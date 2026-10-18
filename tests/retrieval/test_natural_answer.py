import json
from copy import deepcopy
import pytest
from src.retrieval.natural_answer import (MODEL,MODEL_SHA,generate,validate_draft,NaturalAnswerService)
from tests.retrieval.test_development_search import service
from tests.retrieval.test_literature_adapter import setup
from tests.retrieval.test_direct_ingestion import bundle

TEXT='In this artificial study, the pancreas length ranged from 12 to 15 cm in adults.'
EVIDENCE=[dict(rank=1,record=dict(text=TEXT,citation=dict(title='Artificial source')))]
DRAFT=dict(grounding='An artificial adult cohort reports a length range.',claims=[dict(text='The study reported an adult pancreas length of 12–15 cm.',
    citations=[dict(source='P1',quote=TEXT)])])

def wire_draft(draft):
    draft=deepcopy(draft)
    for claim in draft['claims']:
        for citation in claim['citations']:citation.pop('quote',None)
    return draft


def provider(draft=None,review=None):
    calls=[]
    def call(path,payload=None):
        calls.append((path,payload))
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        content=wire_draft(DRAFT if draft is None else draft) if len(calls)==2 else (dict(checks=[dict(claim=i,explanation='Supported by the artificial cohort.',supported=True) for i,_ in enumerate((DRAFT if draft is None else draft)['claims'],1)],safe=True,status_appropriate=True) if review is None else review)
        return dict(model=MODEL,done=True,done_reason='stop',message=dict(content=json.dumps(content)))
    return call,calls

def test_real_protocol_preserves_claim_and_exact_quote():
    call,calls=provider();r=generate('Pancreas size?',EVIDENCE,call)
    assert r['claims'][0]['text']==DRAFT['claims'][0]['text']
    assert r['claims'][0]['citations']==[dict(rank=1,quote=TEXT)]
    assert r['quality']=='development_unvalidated' and len(calls)==3
    assert all('request_id' not in str(p) for _,p in calls)
    assert calls[1][1]['think'] is True and calls[2][1]['think'] is False
    assert calls[2][1]['options']['num_predict']==1536

@pytest.mark.parametrize('kind',['foreign','fabricated','empty','duplicate','no_citation','unknown','too_many','wrong_state'])
def test_invalid_bound_drafts_are_rejected(kind):
    draft=deepcopy(DRAFT);c=draft['claims'][0]
    if kind=='foreign':c['citations'][0]['source']='P9'
    if kind=='fabricated':c['citations'][0]['quote']='This quote does not occur in the source.'
    if kind=='empty':c['text']=' '
    if kind=='duplicate':c['citations']*=2
    if kind=='no_citation':c['citations']=[]
    if kind=='unknown':draft['answer']='hidden'
    if kind=='too_many':draft['claims']*=4
    if kind=='wrong_state':draft['status']='insufficient'
    with pytest.raises(ValueError):validate_draft(draft,[dict(source='P1',text=TEXT)])

@pytest.mark.parametrize('review',[{'acceptable':False},{'acceptable':1},{'acceptable':True,'extra':'x'},{}])
def test_review_rejection_does_not_publish(review):
    call,_=provider(review=review)
    with pytest.raises(ValueError):generate('Pancreas size?',EVIDENCE,call)


@pytest.mark.parametrize('rejection', ['claim', 'safety', 'relevance'])
def test_concise_review_must_approve_every_requirement(rejection):
    review=dict(checks=[dict(claim=1,explanation='Check failed.',supported=True)],safe=True,status_appropriate=True)
    if rejection=='claim':review['checks'][0]['supported']=False
    if rejection=='safety':review['safe']=False
    if rejection=='relevance':review['status_appropriate']=False
    call,calls=provider(review=review)
    with pytest.raises(ValueError,match='review rejected'):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==3

def test_insufficient_is_checked_and_contains_no_claims():
    call,calls=provider(dict(grounding='No direct evidence.',claims=[]))
    assert generate('Pancreas size?',EVIDENCE,call)['status']=='insufficient'
    assert len(calls)==3

def test_missing_model_and_truncation_fail():
    call,calls=provider()
    def wrong(path,payload=None):
        r=call(path,payload)
        if path=='tags':r['models'][0]['digest']='wrong'
        return r
    with pytest.raises(OSError):generate('Pancreas size?',EVIDENCE,wrong)
    assert len(calls)==1
    call,_=provider()
    def truncated(path,payload=None):
        r=call(path,payload)
        if path=='chat':r['done_reason']='length'
        return r
    with pytest.raises(ValueError):generate('Pancreas size?',EVIDENCE,truncated)

def test_scope_failure_and_busy_keep_sources_separate(service):
    s,r,_=service;calls=[]
    def fail(*args):calls.append(args);raise OSError('PRIVATE_MODEL_ERROR')
    a=NaturalAnswerService(s,fail)
    result=a.answer(r)
    assert result['generation']=='unavailable' and result['evidence'] and result['answer'] is None
    assert 'PRIVATE_MODEL_ERROR' not in str(result)
    r['question']='Measure this pancreas'
    assert a.answer(r)['generation']=='not_called' and len(calls)==1
    a.lock.acquire()
    with pytest.raises(OSError):a.answer(r)
    a.lock.release()


def test_range_cannot_be_called_average_even_with_exact_quote():
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The average pancreas is 12–15 cm long.'
    call,calls=provider(draft)
    with pytest.raises(ValueError,match='average'):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==2


def test_number_requires_its_own_cited_quote():
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The pancreas was 33% smaller in that cohort.'
    call,calls=provider(draft)
    with pytest.raises(ValueError,match='Number'):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==2


@pytest.mark.parametrize('marker', ['[P1]', '(P1)'])
def test_bound_inline_reference_is_not_a_factual_number(marker):
    draft=deepcopy(DRAFT)
    draft['claims'][0]['text']=draft['claims'][0]['text'][:-1]+' '+marker+'.'
    original=deepcopy(draft)
    call,calls=provider(draft)
    result=generate('Pancreas size?',EVIDENCE,call)
    assert result['claims'][0]['text']==DRAFT['claims'][0]['text']
    reviewed=json.loads(calls[2][1]['messages'][1]['content'])
    assert reviewed['claims'][0]['text']==result['claims'][0]['text']
    assert draft==original  # The raw producing evidence stays intact.


@pytest.mark.parametrize('text', ['A size of 33 cm [P1].', 'A finding [P9].', '[P1]',
                                'A finding [P1, P9].', 'A size of [33] cm [P1].'])
def test_normalization_does_not_hide_invalid_facts_or_unbound_sources(text):
    draft=deepcopy(DRAFT);draft['claims'][0]['text']=text
    call,calls=provider(draft)
    with pytest.raises(ValueError):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==2


def test_shared_deadline_stops_before_review(monkeypatch):
    import src.retrieval.natural_answer as module
    now=[100.0]
    monkeypatch.setattr(module,'monotonic',lambda:now[0])
    call,calls=provider()
    def slow(path,payload=None):
        result=call(path,payload)
        now[0]+=5 if path=='tags' else 56
        return result
    with pytest.raises(TimeoutError):generate('Pancreas size?',EVIDENCE,slow)
    assert len(calls)==2


def test_default_transport_uses_one_deadline(monkeypatch):
    import src.retrieval.natural_answer as module
    call,calls=provider();deadlines=[]
    def transport(path,payload=None,*,deadline):
        deadlines.append(deadline)
        return call(path,payload)
    monkeypatch.setattr(module,'api',transport)
    generate('Pancreas size?',EVIDENCE)
    assert len(deadlines)==3 and len(set(deadlines))==1


def test_unicode_evidence_is_presented_as_text_not_escape_sequences():
    text='The artificial β-cell measurement ranged from 12 to 15 cm.'
    draft=deepcopy(DRAFT);draft['claims'][0]['citations'][0]['quote']=text
    call,calls=provider(draft)
    generate('Pancreas size?', [dict(rank=1,record=dict(text=text,citation=dict(title='Artificial')))], call)
    for _,payload in calls[1:]:
        content=payload['messages'][1]['content']
        assert 'β-cell' in content and '\\u03b2' not in content


def test_generation_schema_binds_each_quote_to_its_actual_source():
    from src.retrieval.natural_answer import bind_draft
    from jsonschema import ValidationError
    sources=[dict(source='P1',text=TEXT),dict(source='P2',text='A second artificial source has different evidence.')]
    wire=wire_draft(DRAFT)
    assert bind_draft(wire,sources)==DRAFT
    wrong=deepcopy(wire);wrong['claims'][0]['citations'][0]['source']='P9'
    with pytest.raises(ValidationError):bind_draft(wrong,sources)
    wrong=deepcopy(wire);wrong['claims'][0]['citations'][0]['quote']='Invented quote'
    with pytest.raises(ValidationError):bind_draft(wrong,sources)
    assert 'quote' not in wire['claims'][0]['citations'][0]


@pytest.mark.parametrize('error,code', [(TimeoutError('private'),'timeout'),
    (OSError('private'),'model_unavailable'), (ValueError('private'),'validation_failed')])
def test_failure_category_preserves_sources_and_does_not_leak(service,error,code):
    s,r,_=service
    def fail(*args):raise error
    a=NaturalAnswerService(s,fail)
    result=a.answer(r)
    assert result['generation_failure']==code and result['answer'] is None and result['evidence']
    assert 'private' not in str(result) and not a.lock.locked()


def test_transport_deadline_closes_a_stalled_local_response(monkeypatch):
    import src.retrieval.natural_answer as module
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread, Event
    from time import monotonic
    release=Event()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Length','100')
            self.end_headers()
            self.wfile.write(b'{');self.wfile.flush()
            release.wait(2)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    real_connection=module.HTTPConnection
    monkeypatch.setattr(module,'HTTPConnection',lambda host,port,timeout:
        real_connection('127.0.0.1',server.server_port,timeout=timeout))
    start=monotonic()
    try:
        with pytest.raises(TimeoutError):module.api('tags',deadline=start+.15)
        assert monotonic()-start<1
    finally:
        release.set();server.shutdown();server.server_close();thread.join(2)
