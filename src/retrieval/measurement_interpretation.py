"""Source-bound CT measurement methods, separate from numeric reference/scan answers.

The closed intent grammar is deliberately narrow. Reviewed facts derive from canonical
paper spans, not evaluation answers. Curation still needs independent semantic review.
"""
from copy import deepcopy
import hashlib
import re
import unicodedata

from .development_search import search_scope
from .direct_ingestion import digest
from .record_answer import RecordComposer, SYSTEM as BASE_SYSTEM, PLAN_SCHEMA
from .record_search import RecordAwareSearch

POLICY = 'source-linked-measurement-search-v1'
ANSWER_POLICY = 'source-measurement-answer-v1'
SCHEMA = 'prowl-measurement-answer-response-v1'
CATALOG_POLICY = 'reviewed-measurement-methods-v1'
SYSTEM = BASE_SYSTEM.replace('These are named literature comparisons, not patient diagnoses.',
    'These are CT study measurement methods, not patient measurements, conversions or prognoses.')
PROMPT_SHA = digest(dict(system=SYSTEM, schema=PLAN_SCHEMA))
TOPIC = 'ct_tumor_diameter_versus_segmented_volume'
REASON = 'selected_ct_measurement_method_not_patient_interpretation'


def route_measurement_question(question):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ValueError('Invalid question')
    q = unicodedata.normalize('NFKC', question).casefold().replace('’', "'")
    def has(pattern): return re.search(pattern, q) is not None
    def no(reason): return dict(status='unmatched', reason=reason)
    if has(r"\b(this|my|our|your|patient|case|current|diagnos\w*|treat\w*|biopsy|prognos\w*|survival|stage|staging|risk|probability|odds|chance|predict\w*|convert\w*|conversion|formula|calculate\w*)\b|\d"):
        return no('individual_quantitative_or_outcome_request')
    if has(r"\b(no|not|never|without|except|exclude|instead|ignore|prompt|database|secret\w*|invent\w*)\b|\b(don't|doesn't|isn't|can't)\b"):
        return no('negated_or_instruction_request')
    if has(r'\b(liver|kidney|renal|spleen|lung|mri|mr|ultrasound|eus|pet|cysts?|cystic|ipmn|neuroendocrine|pnet|normal|average|threshold|range|percentile|head|tail|body)\b'):
        return no('unrepresented_modality_population_or_object')
    if not (has(r'\bpancrea\w*\b') and has(r'\b(tumou?rs?|lesions?|cancer)\b')
            and has(r'\bdiameters?\b') and has(r'\b(volume|volumetric)\b')
            and has(r'\b(differ\w*|compar\w*|versus|vs|distin\w*)\b')):
        return no('measurement_method_comparison_required')
    return dict(status='candidate', reason=REASON)


def measurement_scope(request):
    reason = search_scope(request)
    if reason == 'measurement_unavailable' and route_measurement_question(request['question'])['status'] == 'candidate':
        return None
    return reason


def record_digest(record, spans):
    refs = {sid for fact in record['facts'] for sid in fact['evidence']}
    return digest(dict(record=record, spans={sid: spans[sid] for sid in sorted(refs)}))


class MeasurementCatalog:
    def __init__(self, catalog, review, canonical):
        if (set(catalog) != {'version', 'manifest', 'spans', 'records'} or catalog['version'] != CATALOG_POLICY
                or review['catalog_version'] != CATALOG_POLICY or review['manifest'] != catalog['manifest']
                or review['status'] != 'engineering_reviewed'):
            raise ValueError('Unreviewed measurement catalog')
        sources = {s['passage_id']: s for s in canonical.values()}
        self.spans = {}; self.citations = {}; self.records = {}
        for sid, span in catalog['spans'].items():
            if set(span) != {'passage_id', 'work_id', 'ordinal', 'start', 'end', 'text_sha256'}:
                raise ValueError('Invalid measurement source span')
            source = sources[span['passage_id']]; p = source['record']['passage']
            start, end = span['start'], span['end']
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source['text'])
                    or span['work_id'] != p['work_id'] or span['ordinal'] != p['ordinal']
                    or hashlib.sha256(source['text'][start:end].encode()).hexdigest() != span['text_sha256']):
                raise ValueError('Measurement source changed')
            self.spans[sid] = dict(span=deepcopy(span), quote=source['text'][start:end])
            self.citations[span['passage_id']] = dict(passage_id=span['passage_id'], work_id=p['work_id'],
                ordinal=p['ordinal'], section_id=p['section_id'], quote=source['text'], citation=deepcopy(source['record']['citation']))
        if set(review['records']) != {r['id'] for r in catalog['records']}:
            raise ValueError('Review membership differs')
        for r in catalog['records']:
            if (set(r) != {'id', 'work_id', 'topic', 'facts', 'retrieval_anchors'} or r['topic'] != TOPIC
                    or r['id'] in self.records or record_digest(r, catalog['spans']) != review['records'][r['id']]
                    or [f['role'] for f in r['facts']] != ['definition', 'method', 'rationale', 'study_limit']):
                raise ValueError('Unqualified measurement record')
            for f in r['facts']:
                if (set(f) != {'role', 'text', 'evidence'} or not isinstance(f['text'], str) or not f['text'].strip()
                        or not f['evidence'] or any(catalog['spans'][sid]['work_id'] != r['work_id'] for sid in f['evidence'])):
                    raise ValueError('Invalid measurement fact')
            pids = {catalog['spans'][sid]['passage_id'] for f in r['facts'][:2] for sid in f['evidence']}
            if not r['retrieval_anchors'] or not set(r['retrieval_anchors']) <= pids:
                raise ValueError('Anchor must locate measurement method')
            self.records[r['id']] = deepcopy(r)

    def render(self, record_id):
        r = self.records[record_id]
        refs = {sid for f in r['facts'] for sid in f['evidence']}
        pids = {self.spans[sid]['span']['passage_id'] for sid in refs}
        return dict(policy=CATALOG_POLICY, record_id=record_id, statements=[
            dict(text=f['text'], role=f['role'], kind='source_fact', span_ids=f['evidence'],
                 citations=sorted({self.spans[sid]['span']['passage_id'] for sid in f['evidence']})) for f in r['facts']],
            evidence={sid: deepcopy(self.spans[sid]) for sid in sorted(refs)},
            citations=[deepcopy(self.citations[pid]) for pid in sorted(pids)])

    def verify_answer(self, answer, *, record_id):
        if answer != self.render(record_id): raise ValueError('Changed measurement assembly')
        return True


class MeasurementIndex:
    def __init__(self, catalog, review, canonical):
        self.engine = MeasurementCatalog(catalog, review, canonical)
        self.canonical = {s['passage_id']: deepcopy(s['record']) for s in canonical.values()}

    def search(self, question):
        route = route_measurement_question(question); matches = []; hits = []; seen = set()
        if route['status'] == 'candidate':
            # Typed method selection, then lexical overlap with actual source text. No question-key lookup.
            terms = set(re.findall(r'[a-z]+', question.casefold()))
            for rid, record in self.engine.records.items():
                rendered = self.engine.render(rid)
                pids = [c['passage_id'] for c in rendered['citations']]
                source_terms = set(re.findall(r'[a-z]+', ' '.join(self.canonical[p]['text'] for p in pids).casefold()))
                score = float(len(terms & source_terms))
                if score <= 0: continue
                matches.append(dict(record_id=rid, topic=record['topic'], score=score,
                    anchor_passage_ids=record['retrieval_anchors'], evidence_passage_ids=pids))
                for pid in record['retrieval_anchors'] + pids:
                    if pid not in seen:
                        hits.append(dict(record=deepcopy(self.canonical[pid]), score=score)); seen.add(pid)
        if len(hits) > 20: raise ValueError('Evidence budget exceeded')
        return dict(route=route, matches=matches, hits=hits)


class MeasurementSearch(RecordAwareSearch):
    policy = POLICY


class MeasurementComposer(RecordComposer):
    policy = ANSWER_POLICY
    system = SYSTEM
    prompt_sha = PROMPT_SHA
    wording_version = 'reviewed-measurement-wording-v1'
