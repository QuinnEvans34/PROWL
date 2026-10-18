"""Offline-qualified feedback utilities; not selected by the live answer service.

Collect independent mechanical failures without accepting a partially checked claim.
Review flags remain model judgments; these helpers never turn a rejection into approval.
"""
from copy import deepcopy
from jsonschema import validate
from .natural_answer import AnswerFailure, validate_draft, validate_question_claims
from .conservative_answer import draft_schema, study_guards, source_absence, SCHEMA


def collect_claim_feedback(raw, sources, question):
    validate(raw, draft_schema(sources))
    lookup = {source['source']: source['text'] for source in sources}
    accepted, issues = [], []
    for index, original in enumerate(raw['claims'], 1):
        claim = deepcopy(original)
        for citation in claim['citations']:
            citation['quote'] = lookup[citation['source']]
        bound = dict(grounding='', claims=[claim])
        failures = []
        normalized = None
        try:
            normalized = validate_draft(bound, sources, max_citations=3)
        except ValueError as error:
            failures.append(('citation_and_wording', str(error)))
        # Independent checks still inspect the structurally valid, canonical-bound
        # draft. A failure above cannot suppress useful feedback from these rules.
        for criterion, check in (
            ('question_scope', lambda: validate_question_claims(question, bound)),
            ('study_qualifiers', lambda: study_guards(claim)),
        ):
            try:
                check()
            except ValueError as error:
                failures.append((criterion, str(error)))
        if source_absence(claim['text']):
            failures.append(('source_absence', 'Do not cite source absence; omit this claim'))
        if failures:
            issues.extend(dict(claim=index, criterion=criterion, reason=reason)
                          for criterion, reason in failures)
        else:
            accepted.extend(normalized['claims'])
    # Partial acceptance must never leak supported fragments of a rejected draft.
    return ([] if issues else accepted), issues


def review_feedback(review, claim_count):
    validate(review, SCHEMA)
    if [check['claim'] for check in review['checks']] != list(range(1, claim_count + 1)):
        raise AnswerFailure('support_rejected', 'Review identity mismatch')
    issues = []
    for check in review['checks']:
        if not check['supported']:
            reason = check['explanation'].strip()
            if not reason:
                raise AnswerFailure('support_rejected', 'Rejected support check has no explanation')
            issues.append(dict(claim=check['claim'], criterion='support', reason=reason))
    for criterion in ('safe', 'relevant', 'readable', 'qualified'):
        if not review[criterion]:
            reason = review['feedback'].strip()
            if not reason:
                raise AnswerFailure('support_rejected', 'Rejected '+criterion+' check has no explanation')
            issues.append(dict(claim=None, criterion=criterion, reason=reason))
    return issues
