"""Offline literature evidence boundary; no search, generation or patient inputs.

A trusted caller supplies a request-specific scope review and ranked snapshot. The
adapter binds them to verified frozen sources and never promotes hits into an answer.
Scope review is procedural, not cryptographic authorization or clinical validation.
"""
from copy import deepcopy
import json
import math
import re

from .corpus_inventory import frozen_inventory, verify_sources
from .direct_ingestion import digest
from .question_routing import verify_plan
from .records import canonical_bytes, sha256_hex


def _closed(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError('Unexpected contract fields')


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Invalid content identity')


class FrozenLiterature:
    """Own an isolated, verified source snapshot. Caller verifies manifest file pins.

    The manifest's expected inventory and exact raw-byte hash are supplied by the
    trusted loader, never taken from a user's request or returned search result.
    """
    def __init__(self, *, batches, bundles, inventory, manifest_sha256):
        _hash(manifest_sha256)
        if frozen_inventory(batches) != inventory:
            raise ValueError('Frozen inventory mismatch')
        verify_sources(batches, bundles)
        self._target = canonical_bytes(dict(manifest_sha256=manifest_sha256, inventory=inventory))
        self._records = {i['record']['passage']['passage_id']: canonical_bytes(i['record'])
                         for b in batches for i in b['items']}

    @property
    def target(self):
        return json.loads(self._target)

    def prepare(self, request, plan, *, scope_review, retriever, limit=5):
        """Make a ticket only after a caller-owned general-literature scope review.

        No code here creates scope decisions. Client requests cannot supply this record.
        Callers must not infer approval from the keyword planner's candidate status.
        """
        verify_plan(plan, request=request)
        if plan['route'] != 'literature' or plan['status'] != 'needs_scope_review':
            raise ValueError('Request is not an eligible literature candidate')
        _closed(scope_review, ('version', 'request_sha256', 'plan_sha256', 'decision', 'reviewer'))
        if (scope_review['version'] != 'prowl-literature-scope-review-v1'
                or scope_review['request_sha256'] != plan['request_sha256']
                or scope_review['plan_sha256'] != plan['content_sha256']
                or scope_review['decision'] != 'general_literature_only'
                or not isinstance(scope_review['reviewer'], str)
                or not re.fullmatch('[a-z0-9][a-z0-9._-]{0,63}', scope_review['reviewer'])):
            raise ValueError('Missing or mismatched scope review')
        _closed(retriever, ('id', 'configuration_sha256'))
        _hash(retriever['configuration_sha256'])
        if (not isinstance(retriever['id'], str)
                or not re.fullmatch('[a-z0-9][a-z0-9._-]{0,63}', retriever['id'])
                or type(limit) is not int or not 1 <= limit <= 50):
            raise ValueError('Invalid retriever identity or limit')
        ticket = dict(version='prowl-literature-ticket-v1', request_id=request['request_id'],
            request_sha256=plan['request_sha256'], plan_sha256=plan['content_sha256'],
            scope_review_sha256=digest(scope_review), question=request['question'],
            target=self.target, retriever=deepcopy(retriever), limit=limit)
        ticket['content_sha256'] = digest(ticket)
        return ticket

    def accept(self, request, plan, *, scope_review, retriever, snapshot, limit=5):
        """Bind a supplied ranking; empty, failed and unassessed evidence are distinct.

        Snapshot hits name canonical records by ID/hash, never supply replacement text.
        The adapter preserves order and scores; it does not rank, select or judge support.
        """
        ticket = self.prepare(request, plan, scope_review=scope_review, retriever=retriever, limit=limit)
        _closed(snapshot, ('version', 'ticket_sha256', 'state', 'failure_code', 'hits'))
        if snapshot['version'] != 'prowl-literature-snapshot-v1' or snapshot['ticket_sha256'] != ticket['content_sha256']:
            raise ValueError('Snapshot request/corpus/configuration mismatch')
        if (snapshot['state'] not in ('complete', 'failed') or not isinstance(snapshot['hits'], list)
                or len(snapshot['hits']) > limit):
            raise ValueError('Invalid snapshot state or count')
        if snapshot['state'] == 'failed':
            if snapshot['hits'] or snapshot['failure_code'] not in ('timeout', 'service_unavailable'):
                raise ValueError('Failed retrieval cannot contain evidence')
        elif snapshot['failure_code'] is not None:
            raise ValueError('Completed retrieval cannot contain a failure')
        evidence, seen = [], set()
        for rank, hit in enumerate(snapshot['hits'], 1):
            _closed(hit, ('passage_id', 'record_sha256', 'score'))
            pid = hit['passage_id']
            if not isinstance(pid, str) or pid not in self._records or pid in seen:
                raise ValueError('Foreign or duplicate passage')
            if hit['record_sha256'] != sha256_hex(self._records[pid]):
                raise ValueError('Canonical evidence identity mismatch')
            try:
                finite_score = type(hit['score']) in (int, float) and math.isfinite(hit['score'])
            except OverflowError:
                finite_score = False
            if not finite_score:
                raise ValueError('Invalid ranking score')
            seen.add(pid)
            evidence.append(dict(rank=rank, score=hit['score'], record=json.loads(self._records[pid])))
        result = dict(version='prowl-literature-evidence-v1', request_id=request['request_id'],
            ticket_sha256=ticket['content_sha256'], snapshot_sha256=digest(snapshot), target=self.target,
            state='retrieval_failed' if snapshot['state'] == 'failed' else
                ('evidence_unassessed' if evidence else 'no_results'),
            failure_code=snapshot['failure_code'], evidence=evidence,
            answer=None, assessment='not_performed', generation='not_called')
        result['content_sha256'] = digest(result)
        return result

    def verify(self, result, request, plan, **kwargs):
        """Verify against trusted original inputs; never trust a rehashed result alone."""
        if canonical_bytes(result) != canonical_bytes(self.accept(request, plan, **kwargs)):
            raise ValueError('Evidence result does not match trusted inputs')
        return result
