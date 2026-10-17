"""Opt-in AI-01 response integrity contract; not wired into a live service.

This checks relationships and exact source locators, never semantic entailment, question
completeness, clinical correctness or whether a claimed response state is justified by evidence.
The frozen source-review rubric must make those judgments separately.
"""
from .direct_ingestion import digest, validate_row
from .query import verify_query
from .records import validate


def validate_response(response, *, query, passages, request_id, identities, generation_model):
    """Validate against trusted caller-owned request/configuration and retrieval snapshots.

    The caller must supply verified published corpus/index provenance and eligible passages;
    a hash alone does not establish that a snapshot was produced by a trusted retriever.
    Local case linkage stays outside this response and must never enter model requests.
    """
    validate('expert-response-v1', response)
    verify_query(query)
    payload = {k: v for k, v in response.items() if k != 'content_sha256'}
    if response['content_sha256'] != digest(payload):
        raise ValueError('Response hash mismatch')
    if (response['request_id'] != request_id or response['query_id'] != query['query_id']
            or response['identities'] != identities or response['retrieval_sha256'] != digest(passages)):
        raise ValueError('Request/query/retrieval/configuration mismatch')
    if response['generation']['model'] != generation_model:
        raise ValueError('Generation model/prompt identity mismatch')
    if query['state'] == 'refused' and passages:
        raise ValueError('Refused query cannot carry retrieved evidence')
    records = {}
    for hit in passages:
        row = validate_row(hit['record'])
        pid = row['passage']['passage_id']
        if pid in records:
            raise ValueError('Duplicate retrieved passage')
        records[pid] = row
    citations = {}
    for citation in response['citations']:
        cid = citation['citation_id']
        if cid in citations or citation['passage_id'] not in records:
            raise ValueError('Duplicate or foreign citation')
        row = records[citation['passage_id']]
        passage = row['passage']
        start, end = citation['start'], citation['end']
        if (citation['work_id'] != passage['work_id']
                or citation['representation_id'] != passage['representation_id']
                or not passage['start'] <= start < end <= passage['end']
                or row['text'][start-passage['start']:end-passage['start']] != citation['quote']):
            raise ValueError('Citation source/offset mismatch')
        citations[cid] = citation
    used, claim_ids = set(), set()
    for claim in response['claims']:
        if claim['claim_id'] in claim_ids or any(c not in citations for c in claim['citation_ids']):
            raise ValueError('Duplicate claim or missing support citation')
        claim_ids.add(claim['claim_id'])
        used.update(claim['citation_ids'])
        if response['mode'] == 'excerpts' and (len(claim['citation_ids']) != 1
                or claim['text'] != citations[claim['citation_ids'][0]]['quote']):
            raise ValueError('Excerpt text must equal its one exact citation')
    if used != set(citations):
        raise ValueError('Unused citation')
    status, generation = response['status'], response['generation']
    reasons = set(response['reason_codes'])
    required_reason = dict(evidence_only='selected_evidence', answered='supported',
        partially_answered='missing_concepts', insufficient_evidence='no_direct_support',
        out_of_scope='query_refused', conflicting_evidence='conflict_unresolved')
    if status in required_reason and reasons != {required_reason[status]}:
        raise ValueError('Status/reason mismatch')
    if status == 'unavailable' and (not reasons or not reasons <= {
            'service_unavailable', 'invalid_generation', 'timeout', 'identity_mismatch'}):
        raise ValueError('Unavailable reason mismatch')
    if (query['state'] == 'refused') != (status == 'out_of_scope'):
        raise ValueError('Query refusal mismatch')
    if generation['state'] in ('rejected', 'unavailable') and status != 'unavailable':
        raise ValueError('Failed generation is not a valid abstention')
    if (generation['state'] == 'rejected') != ('invalid_generation' in reasons):
        raise ValueError('Generation failure reason mismatch')
    if generation['state'] == 'valid' and generation['model'] is None:
        raise ValueError('Valid generation needs model identity')
    if generation['state'] == 'not_called' and generation['model'] is not None:
        raise ValueError('Uncalled generation cannot claim a model')
    if status in ('out_of_scope', 'unavailable', 'insufficient_evidence', 'conflicting_evidence'):
        # v1 refuses unresolved conflict; a cited conflict synthesis needs a future policy version.
        if response['claims'] or response['citations'] or response['mode'] != 'none':
            raise ValueError('Refusal/unavailable cannot contain answer claims')
    elif not response['claims'] or response['mode'] == 'none':
        raise ValueError('Answer/evidence requires claims')
    if status == 'evidence_only' and response['mode'] != 'excerpts':
        raise ValueError('Unqualified evidence cannot be called a summary')
    if status == 'answered' and response['gaps']:
        raise ValueError('Complete answer cannot declare missing concepts')
    if status == 'partially_answered' and not response['gaps']:
        raise ValueError('Partial answer requires explicit gaps')
    if status == 'out_of_scope' and generation['state'] != 'not_called':
        raise ValueError('Refused query cannot call generation')
    return response
