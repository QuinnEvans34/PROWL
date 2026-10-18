"""Opt-in, local-only question planner. Never retrieves, measures, generates or persists.

Keyword routing is an engineering foundation, not semantic scope/privacy qualification.
Even literature candidates require scope review; no plan authorizes execution. Existing
guided endpoints and the frozen query policy are unchanged.
"""
import re
import unicodedata
from uuid import UUID

from .query import classify_scope, normalize_question
from .records import RecordError, identity_digest, validate

REQUEST_VERSION = 'prowl-expert-request-v1'
PLAN_VERSION = 'prowl-expert-route-v1'
POLICY_VERSION = 'scan-question-routing-v1'


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _decision(text):
    # Preserve refusal precedence, including in mixed requests. These examples are
    # not an exhaustive detector, hence every literature path remains unexecuted.
    codes = set(classify_scope(text))
    # The old fixture policy catches the prefix "what disease" even in general
    # literature questions. Narrow that one rule only in this new opt-in policy.
    if (_has(r'^what diseases (can|could|may) (cause|indicate)\b', text)
            and not _has(r'\b(this|my|our|patient|case|scan)\b|\d', text)):
        codes.discard('RF1_diagnosis')
    if codes or _has(
        r'\b(diagnos\w*|prognos\w*|treatment|chemotherapy|biopsy|survival)\b'
        r'|\b(probability|odds|risk|chance)\b.{0,60}\b(cancer|malignan\w*|disease)\b'
        r'|\b(does|is|has)\b.{0,50}\b(this|my|our)\b.{0,50}\b(cancer|malignan\w*|disease)\b'
        r'|\b(reveal|dump|print|show)\b.{0,40}\b(database|db|prompt|secrets?)\b', text
    ):
        return 'refusal', 'refused', ['scope_or_privacy_refusal'], []
    # Do not silently discard negated clauses or interpret absent findings as facts.
    if _has(r"\b(no|not|never|without|instead|exclude)\b|\b(don't|doesn't|isn't|can't)\b", text):
        return 'clarification', 'needs_clarification', ['ambiguous_or_negated_request'], []
    anatomy = _has(r'\b(pancrea\w*|lesions?|tumou?rs?|inflammation)\b', text)
    if not anatomy:
        return 'clarification', 'needs_clarification', ['unrecognized_task'], []
    measurement = _has(r'\b(how (large|big|long|wide)|measure)\b'
                       r'|\b(what (is|are)|give)\b.{0,35}\b(size|dimensions?|diameters?|volumes?)\b', text)
    comparison = _has(r'\b(average|normal|reference|percentile|compare\w*|larger than|smaller than)\b'
                      r'|\bis this pancreas enlarged\b', text)
    disease = _has(r'\b(diseases?|conditions?|indicate|cause\w*|distinguish|differentiat\w*)\b', text)
    location = _has(r'\b(where|locat\w*)\b', text)
    # Preserve compound intent rather than choose one convenient answer path.
    if sum((measurement or location, comparison, disease)) > 1:
        return 'clarification', 'needs_clarification', ['multiple_tasks'], []
    if measurement or location:
        needs = ['validated_measurement'] if measurement else []
        if location:
            needs.append('validated_location')
        if _has(r'\b(head|body|tail)\b', text):
            needs.append('qualified_subregion')
        return 'measurement', 'unavailable', ['measurement_adapter_unavailable'], needs
    if comparison:
        return 'reference_comparison', 'unavailable', ['comparison_adapter_unavailable'], [
            'validated_measurement', 'eligible_reference']
    if disease:
        if _has(r'\b(this|my|our)\b|\b\d|\b(mm|cm|ml)\b', text):
            return 'literature', 'unavailable', ['verified_findings_required'], [
                'verified_findings', 'qualified_literature_retrieval']
        return 'literature', 'needs_scope_review', ['literature_candidate_only'], [
            'qualified_literature_retrieval']
    return 'clarification', 'needs_clarification', ['unrecognized_task'], []


def plan_request(request):
    """Return a deterministic non-executable plan for a closed free-text request.

    Accepts no client-supplied measurements, findings, labels, citations or route hints.
    The future trusted case adapter requires its own version and qualification.
    """
    validate('expert-request-v1', request)
    if str(UUID(request['request_id'])) != request['request_id']:
        raise RecordError('Request ID must be a canonical UUID')
    normalized = normalize_question(request['question'])
    matching = unicodedata.normalize('NFKC', normalized).casefold().replace('’', "'")
    route, status, reasons, needs = _decision(matching)
    plan = dict(schema_version=PLAN_VERSION, policy_version=POLICY_VERSION,
        request_id=request['request_id'], request_sha256=identity_digest(request),
        question_original=request['question'], question_normalized=normalized,
        route=route, status=status, reason_codes=reasons, required_capabilities=needs,
        execution='not_started', answer=None, citations=[])
    plan['content_sha256'] = identity_digest(plan)
    return validate('expert-route-v1', plan)


def verify_plan(plan, *, request):
    """Check both integrity and policy against the caller's original request.

    A recomputed hash cannot authorize an answered state, substituted question or route.
    """
    validate('expert-route-v1', plan)
    if plan != plan_request(request):
        raise RecordError('Routing plan does not match request and policy')
    return plan
