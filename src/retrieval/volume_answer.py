"""Opt-in volume composition; disease responses retain their existing contract."""
from threading import Lock
import re
import unicodedata

from .direct_ingestion import digest
from .record_answer import RecordComposer, SYSTEM as DISEASE_SYSTEM
from .record_answer import PLAN_SCHEMA, SCHEMA_VERSION as DISEASE_SCHEMA, POLICY as DISEASE_POLICY
from .record_search import RecordAwareSearch
from .volume_record_search import POLICY as SEARCH_POLICY, route_volume_question
from .development_search import search_scope

POLICY = 'source-volume-answer-v1.1'
SCHEMA_VERSION = 'prowl-volume-answer-response-v1'
SYSTEM = DISEASE_SYSTEM.replace(
    'These are named literature comparisons, not patient diagnoses.',
    'These are selected MRI study-group volume examples, not universal averages, normal ranges or patient diagnoses.')
PROMPT_SHA = digest(dict(system=SYSTEM, schema=PLAN_SCHEMA))


def volume_scope(request):
    reason = search_scope(request)
    # Only an admitted general study-mean intent can supersede the old scan-measurement
    # classification. Refusal, individual context and all other gates keep precedence.
    if reason == 'measurement_unavailable' and route_volume_question(request['question'])['status'] == 'candidate':
        return None
    return reason


class VolumeComposer(RecordComposer):
    policy = POLICY
    system = SYSTEM
    prompt_sha = PROMPT_SHA
    wording_version = 'reviewed-volume-wording-v1'

    def fact_count(self, record):
        return len(self.engine.render(record['id'])['statements'])

    def assemble(self, plan, records, evidence):
        # Stable grouping changes only layout. The shared validator still checks every
        # original unit, order within each group, qualifier separation and exact coverage.
        if (not isinstance(plan, dict) or set(plan) != {'paragraphs'}
                or not isinstance(plan['paragraphs'], list)
                or any(not isinstance(p, dict) or p.get('record_id') not in records
                       for p in plan['paragraphs'])):
            raise ValueError('Invalid volume composition plan')
        grouped = [p for rid in records for p in plan['paragraphs'] if p['record_id'] == rid]
        return super().assemble(dict(paragraphs=grouped), records, evidence)


class VolumeAwareSearch(RecordAwareSearch):
    policy = SEARCH_POLICY


class LiteratureSearch:
    """Choose a record family, preserving the baseline request/storage gates in both."""
    def __init__(self, disease, volume):
        self.disease, self.volume = disease, volume
        self.config = dict(disease.config, retriever='source-linked-literature-search-v2')

    def search(self, request):
        question = request['question']
        route = self.volume.index.search(question)['route']
        text = unicodedata.normalize('NFKC', question).casefold()
        use_volume = route['status'] in ('candidate', 'clarification') or re.search(r'\bvolume\b', text)
        return (self.volume if use_volume else self.disease).search(request)


class LiteratureAnswers:
    policy = 'source-literature-answer-v2'

    def __init__(self, search, disease_composer, volume_composer, call=None):
        self.search = search
        self.disease_composer, self.volume_composer = disease_composer, volume_composer
        self.call = call
        self.lock = Lock()

    def answer(self, request):
        if not self.lock.acquire(blocking=False):
            raise OSError('Answer service busy')
        try:
            result = self.search.search(request)
            volume = result['record_selection']['policy'] == SEARCH_POLICY
            result.update(schema_version=SCHEMA_VERSION if volume else DISEASE_SCHEMA,
                          answer_policy=POLICY if volume else DISEASE_POLICY)
            if result['record_selection']['status'] == 'matched':
                composer = self.volume_composer if volume else self.disease_composer
                result['answer'] = composer.compose(request['question'], result, self.call)
                result['generation'] = ('completed' if result['answer']['provenance'] == 'local_model_composition'
                                        else 'fallback')
            return result
        finally:
            self.lock.release()
