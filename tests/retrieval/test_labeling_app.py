from copy import deepcopy
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request,urlopen

import pytest

from src.retrieval.labeling_app import ReviewError,ReviewSession,SOURCES,SENTENCES,digest,server,validate_output


def output():
    return dict(meaning='The fictional indoor trial used seven-day checks; outdoor applicability is unproven.',
        answerability='answerable',concepts=['Indoor interval and its scope'],sources={
            s['id']:dict(judgment='direct' if i==0 else 'not_relevant',rationale='Invented test judgment.',
                 excerpts=[dict(sentence_id=SENTENCES[s['id']][0]['id'],grade='direct',concept_ids=['c1'])] if i==0 else []) for i,s in enumerate(SOURCES)})


def provider(question,correction,previous):
    data=output()
    if correction:data['meaning']='Corrected fictional interpretation: seven days indoors only.'
    return data,dict(model='invented_test_stub',model_sha256='0'*64,seconds=0,provider='test_only')


def request(**updates):
    return dict(dict(question='Invented interval?',correction='',case_id=None,revision=None,author='Invented operator'),**updates)


def decision(case,**updates):
    return dict(dict(case_id=case['id'],revision=case['revision'],proposal_sha256=case['proposal_sha256'],
        reviewer='Invented reviewer',action='accept',meaning_reviewed=True,
        reviewed_sources=[s['id'] for s in SOURCES],note=''),**updates)


def test_full_revision_review_history_and_consistency():
    s=ReviewSession(provider);first=s.propose(request());s.decide(decision(first))
    second=s.propose(request(case_id=first['id'],revision=1,correction='Clarify indoor scope.'))
    assert second['revision']==2 and second['state']=='needs_review' and not second['consistency_reviewed']
    with pytest.raises(ReviewError,match='changed'):s.decide(decision(first))
    s.decide(decision(second));s.decide(decision(second,action='consistency',note='Compared population and interval limits.'))
    export=s.export();assert not export['ready_for_evaluation'] and not export['independent_raters_claimed']
    assert [e['kind'] for e in export['events']]==['proposal_created','accept','proposal_created','accept','consistency']
    assert export['events'][0]['proposal']['meaning']==first['proposal']['meaning']
    assert export['events'][2]['correction']=='Clarify indoor scope.'
    assert export['events'][-1]['actor']=='Invented reviewer'
    for i,event in enumerate(export['events']):
        assert event['sha256']==digest({k:v for k,v in event.items() if k!='sha256'})
        assert event['previous_sha256']==(export['events'][i-1]['sha256'] if i else None)
    assert export['sha256']==digest({k:v for k,v in export.items() if k!='sha256'})
    # Caller cannot mutate retained original evidence.
    export['events'][0]['proposal']['meaning']='changed'
    assert s.export()['events'][0]['proposal']['meaning']==first['proposal']['meaning']


@pytest.mark.parametrize('change',[dict(meaning_reviewed=False),dict(reviewed_sources=[]),dict(reviewer=''),
    dict(reviewed_sources=[SOURCES[0]['id']]*3),dict(proposal_sha256='changed')])
def test_incomplete_or_stale_review_cannot_accept(change):
    s=ReviewSession(provider);c=s.propose(request())
    with pytest.raises(ReviewError):s.decide(decision(c,**change))
    assert len(s.events)==1 and s.cases[c['id']]['state']=='needs_review'


@pytest.mark.parametrize('problem',['invented_sentence','wrong_source','model_offset','unknown_concept','uncertain','missing'])
def test_bad_or_unresolved_evidence_not_accepted(problem):
    raw=output();first=raw['sources']['fiction:indoor']
    if problem=='invented_sentence':first['excerpts'][0]['sentence_id']='SECRET fabricated sentence'
    if problem=='wrong_source':first['excerpts'][0]['sentence_id']='fiction:outdoor:s1'
    if problem=='model_offset':first['excerpts'][0]['start']=0
    if problem=='unknown_concept':first['excerpts'][0]['concept_ids']=['c8']
    if problem=='uncertain':first['judgment']='uncertain'
    if problem=='missing':first.update(judgment='not_relevant',excerpts=[])
    s=ReviewSession(lambda *args:(raw,{'model':'invented'}))
    with pytest.raises(ReviewError) as e:
        c=s.propose(request());s.decide(decision(c))
    assert 'SECRET' not in str(e.value)
    assert not any(e['kind']=='accept' for e in s.events)


def test_gap_review_does_not_invent_support_or_release_evaluation():
    raw=output();raw['answerability']='insufficient_evidence';raw['meaning']='The fictional sources do not give a humidity threshold.'
    for row in raw['sources'].values():row.update(judgment='not_relevant',excerpts=[])
    s=ReviewSession(lambda *args:(raw,{'model':'invented'}));c=s.propose(request(question='Invented humidity threshold?'))
    c=s.decide(decision(c));assert c['state']=='human_accepted_invented' and not c['ready_for_evaluation']


def test_model_failure_preserves_accepted_revision_and_releases_busy():
    s=ReviewSession(provider);c=s.propose(request());s.decide(decision(c))
    def failed(*args):raise ReviewError('Local model unavailable.')
    s.provider=failed
    with pytest.raises(ReviewError):s.propose(request(case_id=c['id'],revision=1,correction='Clarify scope'))
    assert not s.busy and len(s.events)==2 and s.cases[c['id']]['state']=='human_accepted_invented'


def test_reject_requires_reason_and_can_be_revised():
    s=ReviewSession(provider);c=s.propose(request())
    with pytest.raises(ReviewError):s.decide(decision(c,action='reject'))
    s.decide(decision(c,action='reject',note='Scope omitted.'))
    c=s.propose(request(case_id=c['id'],revision=1,correction='Include scope.'))
    assert c['state']=='needs_review'
    with pytest.raises(ReviewError):s.decide(decision(c,action='consistency',note='Too early.'))


@pytest.fixture
def running():
    s=ReviewSession(provider);http=server(s,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{http.server_port}'
    def call(path,data=None,headers=None):
        h={'Content-Type':'application/json',**(headers or {})}
        with urlopen(Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h),timeout=3) as r:
            return r.status,r.read(),dict(r.headers)
    yield s,call
    http.shutdown();http.server_close();thread.join()


def test_http_complete_flow_and_export(running):
    s,call=running
    status,page,headers=call('/');assert status==200 and b'Invented-data rehearsal' in page
    assert "frame-ancestors 'none'" in headers['Content-Security-Policy']
    _,raw,_=call('/api/session');token=json.loads(raw)['token'];auth={'X-Review-Token':token}
    _,raw,_=call('/api/propose',request(),auth);c=json.loads(raw)
    call('/api/decision',decision(c),auth)
    _,raw,_=call('/api/propose',request(case_id=c['id'],revision=1,correction='Clarify the scope'),auth);c=json.loads(raw)
    call('/api/decision',decision(c),auth);call('/api/decision',decision(c,action='consistency',note='Checked scope.'),auth)
    _,raw,headers=call('/api/export',{},auth);export=json.loads(raw)
    assert export['cases'][0]['revision']==2 and len(export['events'])==5
    assert headers['Cache-Control']=='no-store' and not export['ready_for_evaluation']


@pytest.mark.parametrize('headers',[{}, {'Origin':'https://external.invalid'}, {'Host':'evil.invalid'}])
def test_cross_origin_or_missing_token_refused(running,headers):
    s,call=running
    with pytest.raises(HTTPError) as e:call('/api/propose',request(),headers)
    assert e.value.code==403 and not s.events


def test_private_import_not_available(running):
    _,call=running
    with pytest.raises(HTTPError) as e:call('/api/private')
    assert e.value.code==404
    _,raw,_=call('/api/session');auth={'X-Review-Token':json.loads(raw)['token']}
    with pytest.raises(HTTPError):call('/api/propose',dict(request(),private_path='/secret'),auth)


def test_local_model_identity_truncation_and_prior_feedback(monkeypatch):
    from src.retrieval.labeling_app import LocalModel,MODEL,MODEL_SHA
    model=LocalModel();calls=[]
    def transport(path,payload=None,timeout=85):
        calls.append((path,payload))
        if path=='tags':return {'models':[{'name':MODEL,'digest':MODEL_SHA}]}
        return dict(done=True,done_reason='stop',message={'content':json.dumps(output())})
    monkeypatch.setattr(model,'request',transport)
    result,identity=model('Invented question?','Clarify scope.','Original meaning.')
    body=json.loads(calls[-1][1]['messages'][1]['content'])
    assert body['previous_meaning']=='Original meaning.' and body['correction']=='Clarify scope.'
    assert identity['model_sha256']==MODEL_SHA and len(calls)==2
    assert body['sources'][0]['sentences'][0]['text'] in SOURCES[0]['text']
    def truncated(path,payload=None,timeout=85):
        if path=='tags':return {'models':[{'name':MODEL,'digest':MODEL_SHA}]}
        return dict(done=True,done_reason='length',message={'content':json.dumps(output())})
    monkeypatch.setattr(model,'request',truncated)
    with pytest.raises(ReviewError,match='finishing'):model('Invented?','')
    monkeypatch.setattr(model,'request',lambda *a,**k:{'models':[{'name':MODEL,'digest':'wrong'}]})
    with pytest.raises(ReviewError,match='identity changed'):model('Invented?','')


def test_busy_session_cannot_duplicate_or_accept_during_revision():
    s=ReviewSession(provider);c=s.propose(request());s.busy=True
    for action in (lambda:s.propose(request()),lambda:s.decide(decision(c)),s.export):
        with pytest.raises(ReviewError):action()
    assert len(s.events)==1
