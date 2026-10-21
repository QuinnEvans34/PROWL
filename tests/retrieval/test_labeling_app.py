from copy import deepcopy
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request,urlopen

import pytest

from src.retrieval.labeling_app import ReviewError,ReviewSession,SOURCES,digest,server,validate_output


def output():
    return dict(meaning='The fictional indoor trial used seven-day checks; outdoor applicability is unproven.',
        answerability='answerable',concepts=['Indoor interval and its scope'],sources=[
            dict(source_id=s['id'],judgment='direct' if i==0 else 'not_relevant',rationale='Invented test judgment.',
                 spans=[dict(quote=s['text'],grade='direct',concept_ids=['c1'])] if i==0 else []) for i,s in enumerate(SOURCES)])


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


@pytest.mark.parametrize('problem',['invented_quote','duplicate_source','model_offset','unknown_concept','uncertain','missing'])
def test_bad_or_unresolved_evidence_not_accepted(problem):
    raw=output()
    if problem=='invented_quote':raw['sources'][0]['spans'][0]['quote']='SECRET fabricated quote'
    if problem=='duplicate_source':raw['sources'][1]=deepcopy(raw['sources'][0])
    if problem=='model_offset':raw['sources'][0]['spans'][0]['start']=0
    if problem=='unknown_concept':raw['sources'][0]['spans'][0]['concept_ids']=['c8']
    if problem=='uncertain':raw['sources'][0]['judgment']='uncertain'
    if problem=='missing':raw['sources'][0].update(judgment='not_relevant',spans=[])
    s=ReviewSession(lambda *args:(raw,{'model':'invented'}))
    with pytest.raises(ReviewError) as e:
        c=s.propose(request());s.decide(decision(c))
    assert 'SECRET' not in str(e.value)
    assert not any(e['kind']=='accept' for e in s.events)


def test_gap_review_does_not_invent_support_or_release_evaluation():
    raw=output();raw['answerability']='insufficient_evidence';raw['meaning']='The fictional sources do not give a humidity threshold.'
    for row in raw['sources']:row.update(judgment='not_relevant',spans=[])
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
