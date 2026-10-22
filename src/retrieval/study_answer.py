"""CT visibility and study limits using the existing source-bound record contract."""
from copy import deepcopy
import re

from .development_search import search_scope
from .direct_ingestion import digest
from .measurement_interpretation import MeasurementCatalog, MeasurementComposer, MeasurementIndex
from .question_interpretation import interpret_question
from .record_answer import SYSTEM as BASE_SYSTEM, PLAN_SCHEMA
from .record_search import RecordAwareSearch

POLICY = 'source-linked-study-search-v1'
ANSWER_POLICY = 'source-study-answer-v1'
SCHEMA = 'prowl-study-answer-response-v1'
SYSTEM = BASE_SYSTEM.replace('These are named literature comparisons, not patient diagnoses.',
    'These are explanations of CT visibility and limitations of one named study, not patient diagnoses.')
PROMPT_SHA = digest(dict(system=SYSTEM, schema=PLAN_SCHEMA))


def route_study_question(question):
    intent = interpret_question(question); q = intent['matching_text']
    has = lambda p: re.search(p, q) is not None
    def no(reason): return dict(status='unmatched', reason=reason, topic=None)
    if intent['subject'] != 'pancreas' or intent['context'] != 'literature' or intent['negated']:
        return no('unresolved_subject_context_or_negation')
    if has(r'\b(this|my|our|your|patient|case|diagnos\w*|treat\w*|biopsy|stage|staging|prognos\w*|survival|risk|probability|odds|chance|prompt|database|secret\w*|ignore|cysts?|ipmn|neuroendocrine|kidney|liver|lung)\b|\d'):
        return no('individual_or_unrepresented_request')
    if any(m != 'CT' for m in intent['modalities']) or intent['task'] == 'contour_review':
        return no('unrepresented_modality_or_task')
    iso = has(r'\bisoattenuat\w*\b')
    appearance = iso or has(r'\b(blend\w*|similar|same|like|resembl\w*)\b.{0,70}\b(tissue|density|intensity|pancreas)\b')
    tumor = has(r'\b(tumou?rs?|cancer|carcinomas?|pdac)\b')
    if not tumor or not appearance:
        return no('specific_ct_visibility_topic_required')
    if intent['task'] == 'study_limitations' and has(r'\b(study|research|paper)\b'):
        return dict(status='candidate', reason='selected_ct_study_limits', topic='ct_isoattenuating_study_limits')
    if (iso or 'CT' in intent['modalities']) and has(r'\b(why|how|explain|difficult|hard|challeng\w*)\b'):
        return dict(status='candidate', reason='selected_ct_visibility', topic='ct_isoattenuating_visibility')
    return no('specific_ct_visibility_topic_required')


class StudyCatalog(MeasurementCatalog):
    version = 'reviewed-ct-study-facts-v1'
    topics = {'ct_isoattenuating_visibility': ['definition', 'context', 'scope_limit'],
              'ct_isoattenuating_study_limits': ['design', 'selection', 'reference_limit', 'scope_limit']}


class StudyIndex(MeasurementIndex):
    def __init__(self, catalog, review, canonical):
        self.engine = StudyCatalog(catalog, review, canonical)
        self.canonical = {s['passage_id']: deepcopy(s['record']) for s in canonical.values()}

    def search(self, question):
        route = route_study_question(question); matches = []; hits = []
        for rid, record in self.engine.records.items():
            if route['status'] != 'candidate' or route['topic'] != record['topic']:
                continue
            rendered = self.engine.render(rid)
            pids = [c['passage_id'] for c in rendered['citations']]
            terms = set(re.findall('[a-z]+', question.casefold()))
            source_terms = set(re.findall('[a-z]+', ' '.join(self.canonical[p]['text'] for p in pids).casefold()))
            score = float(len(terms & source_terms))
            if score <= 0: continue
            matches.append(dict(record_id=rid, topic=record['topic'], score=score,
                anchor_passage_ids=record['retrieval_anchors'], evidence_passage_ids=pids))
            hits.extend(dict(record=deepcopy(self.canonical[p]), score=score) for p in dict.fromkeys(record['retrieval_anchors']+pids))
        return dict(route=route, matches=matches, hits=hits)


class StudySearch(RecordAwareSearch):
    policy = POLICY


class StudyComposer(MeasurementComposer):
    policy = ANSWER_POLICY
    system = SYSTEM
    prompt_sha = PROMPT_SHA
    wording_version = 'reviewed-ct-study-wording-v1'
