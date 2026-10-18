"""Bounded paper-focused synthesis with source-locked rendering and model cleanup."""
from time import monotonic
from .conservative_answer import generate_conservative,MODEL,MODEL_SHA,fingerprint as base_fingerprint
from .conservative_render import render_and_check,PROMPT,SCHEMA,CHECK
from .natural_answer import api,remaining
from .direct_ingestion import digest

POLICY='natural-literature-answer-v21'


def fingerprint():
    return digest([base_fingerprint(),PROMPT,SCHEMA,CHECK,'source-locked-render-eight-calls-55s-plus5s-unload-v1'])


def generate_readable(question,evidence,call=None,*,deadline=None):
    deadline=min(monotonic()+60,deadline) if deadline is not None else monotonic()+60
    work_deadline=deadline-5;transport=call;calls=0;provider_started=False
    def bounded(path,payload=None):
        nonlocal calls,provider_started
        remaining(work_deadline)
        if path=='chat':
            calls+=1
            if calls>8:raise ValueError('Generation call budget exceeded')
        provider_started=True
        value=api(path,payload,port=11435,deadline=work_deadline) if transport is None else transport(path,payload)
        remaining(work_deadline)
        return value
    try:
        answer=generate_conservative(question,evidence,bounded,deadline=work_deadline)
        if answer['status']=='summarized':
            sources=[dict(source=f"P{e['rank']}",text=e['record']['text'],title=e['record']['citation']['title']) for e in evidence]
            raw=dict(claims=[dict(text=c['text'],citations=[dict(source=f"P{x['rank']}") for x in c['citations']]) for c in answer['claims']])
            rendered=render_and_check(question,raw,sources,bounded)
            answer=dict(answer,claims=[dict(text=c['text'],citations=[dict(rank=int(x['source'][1:]),quote=x['quote']) for x in c['citations']]) for c in rendered['claims']])
        return dict(answer,policy=POLICY,prompt_sha256=fingerprint(),rendering='source_locked_plain_language_v1',generation_calls=calls)
    finally:
        if provider_started:
            remaining(deadline)
            payload=dict(model=MODEL,keep_alive=0)
            result=api('generate',payload,port=11435,deadline=deadline) if transport is None else transport('generate',payload)
            remaining(deadline)
            if result.get('done') is not True or result.get('model')!=MODEL:
                raise OSError('Candidate model cleanup failed')
