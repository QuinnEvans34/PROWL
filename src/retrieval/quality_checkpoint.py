"""Observation-only development audit. Expected answers never enter requests."""
import math
from time import monotonic
from uuid import uuid4

from .direct_ingestion import digest


def request_for(case):
    return dict(schema_version='prowl-expert-request-v1', request_id=str(uuid4()),
                question=case['question'])


def verify_response(result, request, *, search, answer, target, records):
    if (result['schema_version'] != 'prowl-development-answer-response-v1'
            or result['request_id'] != request['request_id'] or result['question'] != request['question']
            or result['collection'] != search['collection'] or result['target'] != target
            or result['configuration_sha256'] != digest(search)):
        raise ValueError('Response identity mismatch')
    hits = result['evidence']
    if not isinstance(hits, list) or len(hits) > 5: raise ValueError('Invalid evidence count')
    seen = set()
    for rank, hit in enumerate(hits, 1):
        pid = hit['record']['passage']['passage_id']
        if (hit['rank'] != rank or pid in seen or hit['record'] != records.get(pid)
                or type(hit['score']) not in (int, float) or not math.isfinite(hit['score'])):
            raise ValueError('Invalid canonical evidence')
        seen.add(pid)
    state, generation = result['state'], result['generation']
    if state not in ('not_searched', 'no_results', 'evidence_unassessed'):
        raise ValueError('Invalid search state')
    if bool(hits) != (state == 'evidence_unassessed'): raise ValueError('Evidence state mismatch')
    if generation == 'not_called':
        if hits or result['answer'] is not None: raise ValueError('Invalid no-generation state')
        if state == 'not_searched' and result['reason'] not in (
                'out_of_scope', 'case_context_unavailable', 'measurement_unavailable', 'pancreas_topic_required'):
            raise ValueError('Invalid refusal reason')
    elif generation == 'unavailable':
        if (not hits or result['answer'] is not None or result.get('generation_failure') not in (
                'timeout', 'incomplete', 'support_rejected', 'model_unavailable', 'validation_failed')):
            raise ValueError('Invalid failed generation')
    elif generation == 'completed':
        a = result['answer']
        if (not hits or a['policy'] != answer['version'] or a['model'] != answer['model']
                or a['model_sha256'] != answer['model_sha256'] or a['prompt_sha256'] != answer['prompt_sha256']
                or a['validation'] != 'exact_quotes_and_model_review' or a['quality'] != 'development_unvalidated'
                or a['status'] not in ('summarized', 'insufficient') or not isinstance(a['claims'], list)
                or len(a['claims']) > 3 or bool(a['claims']) != (a['status'] == 'summarized')):
            raise ValueError('Invalid answer binding')
        for claim in a['claims']:
            if (not isinstance(claim['text'], str) or not claim['text'].strip()
                    or not 1 <= len(claim['citations']) <= 2): raise ValueError('Invalid claim')
            ranks = set()
            for citation in claim['citations']:
                rank = citation['rank']
                if (type(rank) is not int or not 1 <= rank <= len(hits) or rank in ranks
                        or citation['quote'] != hits[rank-1]['record']['text']):
                    raise ValueError('Citation is not the bound full passage')
                ranks.add(rank)
    else: raise ValueError('Invalid generation state')
    if state != 'not_searched' and result['reason'] is not None: raise ValueError('Unexpected refusal')
    return result


def observe(case, post, **bindings):
    request = request_for(case)
    start = monotonic()
    receipt = dict(case_id=case['id'], request=request)
    try:
        response = post(request)
        receipt['response'] = response  # Retain invalid output for audit, never score it as accepted.
        verify_response(response, request, **bindings)
        receipt['transport_validation'] = 'passed'
    except Exception as error:
        receipt['transport_validation'] = 'failed'
        receipt['error_type'] = type(error).__name__
    receipt['elapsed_seconds'] = monotonic() - start
    return receipt
