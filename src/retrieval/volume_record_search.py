"""Isolated, conservative volume-record selection. Not enabled in the live API."""
from collections import Counter
from copy import deepcopy
import math
import re
import unicodedata

from .fact_records import FactCatalog
from .question_interpretation import interpret_question

POLICY = 'source-linked-volume-search-v1'
NGT = 'normal_glucose_tolerance_comparison'
T2DM = 'well_controlled_type2_metformin'


def route_volume_question(question):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ValueError('Invalid question')
    text = interpret_question(question)['matching_text']
    has = lambda pattern: re.search(pattern, text) is not None
    def result(status, reason, populations=()):
        return dict(status=status, reason=reason, intents=[
            dict(object='pancreas', extent='whole_organ', quantity='volume', population=p,
                 method='MRI', uncertainty_kind='SEM', use='literature_example') for p in populations])

    if has(r"\b(this|my|our|patient|case|current|scan|diagnos\w*|treat\w*|biopsy|risk|odds|probability|survival)\b"):
        return result('unmatched', 'individual_or_clinical_request')
    if has(r"\b(no|not|never|without|except|exclude|ignore|instead|prompt|database|secret\w*)\b"
           r"|\b(don't|doesn't|isn't|can't)\b"):
        return result('unmatched', 'negated_or_instruction_request')
    # The 2 in type 2 diabetes is a population label, not a supplied measurement.
    without_type2 = re.sub(r'\b(type[\s-]*2|t2dm)\b', 'type two', text)
    if re.search(r'\d', without_type2):
        return result('unmatched', 'supplied_number_or_unrepresented_population')
    if not has(r'\b(pancreas|pancreatic)\b'):
        return result('unmatched', 'pancreatic_topic_required')
    if has(r'\b(head|body|tail|lesion\w*|tumou?r\w*|cancer|pdac|pancreatitis|liver|kidney|spleen)\b'):
        return result('unmatched', 'unrepresented_object_or_disease')
    if has(r'\b(ct|computed tomography|ultrasound|us|eus|pet)\b'):
        return result('unmatched', 'unrepresented_method')
    if has(r'\b(healthy|children|child|pediatric|paediatric|infant\w*|adolescent\w*|obes\w*|'
           r'pregnan\w*|gestational|elderly|men|women|male|female|type one|type i)\b'):
        return result('unmatched', 'unrepresented_population')
    if has(r'\b(range|percentile\w*|threshold|cutoff|cut-off|standard deviation|sd|median|'
           r'minimum|maximum|length|width|diameter|weight|mass)\b'):
        return result('unmatched', 'unrepresented_quantity_or_statistic')
    if not has(r'\bvolume\b'):
        return result('clarification', 'specify_volume_or_linear_size') if has(
            r'\b(size|large|big|long|wide)\b') else result('unmatched', 'volume_topic_required')
    if has(r'\b(normal|abnormal|reference|enlarged)\b') and not has(r'\bnormal glucose tolerance\b'):
        return result('unmatched', 'normality_reference_unavailable')
    diabetes = has(r'\b(diabetes|diabetic|t2dm)\b')
    type2 = has(r'\b(type[\s-]*(2|two)|t2dm)\b')
    if diabetes and not type2:
        return result('clarification', 'diabetes_population_unspecified')
    comparison = has(r'\b(compar\w*|versus|vs|differ\w*)\b')
    if type2 and has(r'\bnormal glucose tolerance\b') and not comparison:
        return result('clarification', 'comparison_relationship_unspecified')
    if comparison and not (type2 and has(r'\bnormal glucose tolerance\b')):
        return result('clarification', 'comparison_groups_unspecified')
    if not has(r'\b(average|mean|study|studies|report\w*|mri|magnetic resonance)\b'):
        return result('clarification', 'study_mean_scope_required')
    populations = (NGT, T2DM) if comparison else (T2DM,) if type2 else (NGT,)
    return result('candidate', 'selected_study_examples_not_reference_ranges', populations)


def _terms(text):
    return re.findall(r'[a-z]+', unicodedata.normalize('NFKC', text).casefold())


class VolumeRecordSearchIndex:
    """Source-derived lexical ranking followed by exact existing fact/source admission."""
    def __init__(self, catalog, review, canonical):
        self.engine = FactCatalog(catalog, review, canonical)
        self.records = deepcopy(catalog['records'])
        self.canonical = {s['passage_id']: deepcopy(s['record']) for s in canonical.values()}
        self.documents = {
            r['id']: Counter(_terms(' '.join(
                [str(f['value']) for f in r['fields'].values()]
                + [self.canonical[p]['text'] for p in r['retrieval_anchors']])))
            for r in self.records
        }
        self.df = Counter(t for doc in self.documents.values() for t in doc)

    def search(self, question):
        route = route_volume_question(question)
        ranked = []
        query = set(_terms(question))
        for record in self.records:
            fields = {k: f['value'] for k, f in record['fields'].items()}
            intent = next((i for i in route['intents'] if all(
                i[k] == fields[k] for k in ('object', 'extent', 'quantity', 'population',
                                          'method', 'uncertainty_kind'))), None)
            if intent is None:
                continue
            doc = self.documents[record['id']]
            score = sum(math.log(1+len(self.documents)/(1+self.df[t]))*(1+math.log(doc[t]))
                        for t in query.intersection(doc))
            if score <= 0:
                continue
            anchors = [self.canonical[p] for p in record['retrieval_anchors']]
            if record['id'] not in self.engine.select(anchors, intent)['record_ids']:
                raise ValueError('Selected volume record failed admission')
            answer = self.engine.render(record['id'])
            self.engine.verify_answer(answer, record_id=record['id'])
            ranked.append(dict(record_id=record['id'], population=fields['population'], score=score,
                               evidence_passage_ids=[c['passage_id'] for c in answer['citations']]))
        ranked.sort(key=lambda r: (-r['score'], r['record_id']))
        hits = []
        seen = set()
        for record in ranked:
            for pid in record['evidence_passage_ids']:
                if pid not in seen:
                    hits.append(dict(record=deepcopy(self.canonical[pid]), score=record['score']))
                    seen.add(pid)
        if len(hits) > 20:
            raise ValueError('Volume evidence budget exceeded')
        return dict(policy=POLICY, route=route, matches=ranked, hits=hits)
