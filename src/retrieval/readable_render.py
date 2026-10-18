"""Rewrite claim text without supplying any additional factual context or citation choices."""
from copy import deepcopy
from jsonschema import validate
from .natural_answer import chat,bind_draft
from .qualified_answer import check_draft,isolated_review_body,SCHEMA,CHECK,MODEL

PROMPT="""Rewrite each supplied statement in clear, ordinary English to answer the question.
Use only the facts in that statement. You may leave out details the question does not need; do not
add new facts or merge statements. Preserve quantities, study population, sample size, measurement
method and uncertainty. Replace jargon with ordinary wording or omit unnecessary specialist detail.
Avoid acronyms, cell subtype lists and scan sequence names unless specifically asked. A study example
must remain explicitly study-specific. Aim for one or two short sentences per statement.
Return exactly one text for each ID, in the same order. No citations or source markers in the text."""


def render_schema(claims):
    return dict(type='object',additionalProperties=False,required=['statements'],properties=dict(statements=dict(type='array',minItems=len(claims),maxItems=len(claims),items=dict(type='object',additionalProperties=False,required=['id','text'],properties=dict(id=dict(type='integer'),text=dict(type='string',maxLength=600))))))


def render_payload(question,claims):
    return dict(question=question,statements=[dict(id=i,text=c['text']) for i,c in enumerate(claims,1)])


def render_and_check(question,raw,sources,call):
    schema=render_schema(raw['claims'])
    rendered=chat(call,PROMPT,render_payload(question,raw['claims']),schema,think=None,context_tokens=16384,model=MODEL)
    validate(rendered,schema)
    if [s['id'] for s in rendered['statements']]!=list(range(1,len(raw['claims'])+1)):
        raise ValueError('Rendering changed claim identity')
    rewritten=dict(claims=[dict(text=s['text'],citations=deepcopy(c['citations'])) for s,c in zip(rendered['statements'],raw['claims'])])
    claims,issues=check_draft(rewritten,sources,question)
    if issues:raise ValueError('; '.join(issues))
    review_schema=deepcopy(SCHEMA)
    review_schema['properties']['checks'].update(minItems=len(claims),maxItems=len(claims))
    review=chat(call,CHECK,isolated_review_body(question,claims,sources),review_schema,think=None,context_tokens=16384,model=MODEL)
    validate(review,review_schema)
    if any(review[k] is not True for k in ('safe','relevant','readable','qualified')):
        raise ValueError('Rendered answer review failed')
    if any(c['claim']!=i or c['supported'] is not True for i,c in enumerate(review['checks'],1)):
        raise ValueError('Rendered claim unsupported')
    return dict(claims=claims,review=review)
