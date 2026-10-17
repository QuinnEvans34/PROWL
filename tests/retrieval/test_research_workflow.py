import copy
import json
from pathlib import Path
from threading import Event, Thread
from uuid import uuid4

import pytest
from src.retrieval import grounded_answer as g
from src.retrieval.direct_ingestion import source_bundle, source_passages
from src.retrieval.research_workflow import ResearchWorkflow, checked, exclusive, publish
from tests.retrieval.test_direct_ingestion import XML


def request(**kw):
    return dict(request_id=str(uuid4()), question_id='radiomics', **kw)


@pytest.fixture
def inputs(tmp_path):
    path = tmp_path/'synthetic.xml'
    path.write_text(XML)
    rows = list(source_passages(source_bundle(path)))
    passages = [dict(record=rows[1], score=1.0)]
    generation = dict(answer=dict(status='excerpts', extracts=[dict(
        passage_id=rows[1]['passage']['passage_id'], quote=rows[1]['text'])]),
        validation='exact_quotes_verified', provenance=dict(model='fixture'))
    return passages, generation


def store_at(tmp_path, inputs, generate=None, retrieve=None, **kw):
    passages, generation = inputs
    return ResearchWorkflow(tmp_path/'runs', retrieve or (lambda _: copy.deepcopy(passages)),
        'research-v1', 'fixture-encoder', 'fixture-corpus',
        generate or (lambda *_: copy.deepcopy(generation)), dict(model='fixture'), **kw)


def test_failed_generation_explicit_retry_reuses_retrieval_across_restart(tmp_path, inputs):
    calls = []
    bad = copy.deepcopy(inputs[1]);bad.update(validation='generation_rejected', answer=dict(status='insufficient_evidence', extracts=[]))
    store = store_at(tmp_path, inputs, lambda *_: bad, lambda _: calls.append('retrieve') or inputs[0])
    original = request();failed = store.save(original)
    assert failed['state'] == 'failed' and failed['stages'][2]['reason'] == 'invalid_generation'
    assert 'response' not in failed
    assert store.save(original) == failed and calls == ['retrieve']
    before = {p.name:p.read_bytes() for p in (store.directory/original['request_id']).glob('*.json')}
    restart = store_at(tmp_path, inputs, lambda *_: calls.append('select') or inputs[1],
                       lambda _: pytest.fail('Retrieval must be reused'))
    recovery = request(resume_of=original['request_id'])
    saved = restart.save(recovery)
    assert saved['state'] == 'completed'
    assert [s['state'] for s in saved['stages']] == ['reused','completed','completed','completed']
    assert calls == ['retrieve','select']
    assert restart.save(recovery) == saved
    assert before == {p.name:p.read_bytes() for p in (store.directory/original['request_id']).glob('*.json')}
    assert saved['response']['generation'] == inputs[1]


def test_real_generator_rejection_and_valid_abstention_are_distinct(tmp_path, inputs, monkeypatch):
    responses = iter([dict(done=True, done_reason='length', message=dict(content='')),
        dict(done=True, done_reason='stop', message=dict(content=json.dumps(dict(status='insufficient_evidence',extracts=[]))))])
    monkeypatch.setattr(g,'api',lambda path,payload=None: dict(models=[dict(name=g.MODEL,digest=g.MODEL_SHA)]) if path=='tags' else next(responses))
    store = ResearchWorkflow(tmp_path/'runs',lambda _:inputs[0],'research-v1','fixture','fixture')
    failed = store.save(request())
    assert failed['state']=='failed' and failed['stages'][2]['reason']=='invalid_generation'
    saved = store.save(request(resume_of=failed['run_id']))
    assert saved['state']=='completed' and saved['response']['generation']['answer']['status']=='insufficient_evidence'
    assert saved['response']['generation']['validation']=='exact_quotes_verified'


def test_empty_retrieval_skips_model_and_saves(tmp_path):
    store = ResearchWorkflow(tmp_path/'runs',lambda _:[],'research-v1','fixture','fixture')
    saved=store.save(request())
    assert saved['state']=='completed' and saved['response']['generation']['model_called'] is False


def test_service_failure_keeps_retrieval_for_new_run(tmp_path,inputs):
    def fail(*_):raise OSError('private detail not for UI')
    failed=store_at(tmp_path,inputs,fail).save(request())
    assert failed['stages'][1]['reason']=='service_unavailable'
    assert 'private detail' not in json.dumps(failed)
    recovered=store_at(tmp_path,inputs).save(request(resume_of=failed['run_id']))
    assert recovered['stages'][0]['state']=='reused'


def test_interrupted_select_is_visible_and_recovers(tmp_path,inputs):
    def interrupt(*_):raise KeyboardInterrupt
    store=store_at(tmp_path,inputs,interrupt);r=request()
    with pytest.raises(KeyboardInterrupt):store.save(r)
    assert store.read(r['request_id'])['state']=='interrupted'
    saved=store_at(tmp_path,inputs).save(request(resume_of=r['request_id']))
    assert saved['state']=='completed' and saved['stages'][0]['state']=='reused'


def test_running_status_and_cross_instance_lock(tmp_path,inputs):
    started,finish=Event(),Event()
    def slow(*_):
        started.set();assert finish.wait(5);return inputs[1]
    store=store_at(tmp_path,inputs,slow);r=request();results=[]
    worker=Thread(target=lambda:results.append(store.save(r)));worker.start()
    try:
        assert started.wait(5)
        other=store_at(tmp_path,inputs)
        assert other.read(r['request_id'])['state']=='running'
        assert other.save(r)['state']=='running'
        with pytest.raises(OSError,match='busy'):other.save(request())
    finally:
        finish.set();worker.join(5)
    assert results[0]['state']=='completed'


@pytest.mark.parametrize('target',['retrieve.json','select.json','event-0001.json','request.json'])
def test_corrupt_parent_refuses_reuse_before_calls(tmp_path,inputs,target):
    def fail(*_):raise OSError('offline')
    store=store_at(tmp_path,inputs,fail if target!='select.json' else lambda *_:dict(inputs[1],validation='generation_rejected'))
    failed=store.save(request());p=store.directory/failed['run_id']/target
    value=json.loads(p.read_text());value['tampered']=True;p.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='integrity'):
        store_at(tmp_path,inputs,lambda *_:pytest.fail('No inference')).save(request(resume_of=failed['run_id']))


def test_rehashed_artifact_with_wrong_inputs_rejected(tmp_path,inputs):
    def fail(*_):raise OSError('offline')
    store=store_at(tmp_path,inputs,fail);failed=store.save(request())
    path=store.directory/failed['run_id']/'retrieve.json';value=checked(path)
    value['inputs']={'invented':'a'};value.pop('content_sha256');path.unlink();publish(path,value)
    with pytest.raises(ValueError,match='binding'):store.read(failed['run_id'])


def test_conflict_and_changed_config_refuse_recovery(tmp_path,inputs):
    def fail(*_):raise OSError('offline')
    store=store_at(tmp_path,inputs,fail);r=request();store.save(r)
    with pytest.raises(FileExistsError):store.save(dict(r,question_id='eus'))
    changed=store_at(tmp_path,inputs);changed.binding['retrieval_identity']='changed'
    with pytest.raises(ValueError,match='configuration'):changed.save(request(resume_of=r['request_id']))
    with pytest.raises(ValueError,match='configuration'):store.save(dict(request(resume_of=r['request_id']),question_id='eus'))


def test_completed_run_cannot_be_retried(tmp_path,inputs):
    store=store_at(tmp_path,inputs);saved=store.save(request())
    with pytest.raises(ValueError,match='Only failed'):store.save(request(resume_of=saved['run_id']))
    with pytest.raises(ValueError):store.save(dict(request(),patient_id='private'))
    with pytest.raises(ValueError):store.read('../outside')


def test_save_failure_reuses_selection_and_validation(tmp_path,inputs,monkeypatch):
    import src.retrieval.research_workflow as module
    original=module.ResearchStore.save
    monkeypatch.setattr(module.ResearchStore,'save',lambda *_:(_ for _ in ()).throw(OSError('disk')))
    store=store_at(tmp_path,inputs);failed=store.save(request())
    assert failed['stages'][3]['state']=='failed'
    monkeypatch.setattr(module.ResearchStore,'save',original)
    restart=store_at(tmp_path,inputs,lambda *_:pytest.fail('Must reuse selection'))
    saved=restart.save(request(resume_of=failed['run_id']))
    assert [s['state'] for s in saved['stages']]==['reused','reused','reused','completed']


def test_invented_quote_never_saved(tmp_path,inputs):
    bad=copy.deepcopy(inputs[1]);bad['answer']['extracts'][0]['quote']='An invented conclusion which must never appear in a saved answer.'
    store=store_at(tmp_path,inputs,lambda *_:bad);failed=store.save(request())
    assert failed['stages'][2]['reason']=='invalid_generation'
    assert not list((store.directory/'responses').glob('*.json'))
    recovered=store_at(tmp_path,inputs).save(request(resume_of=failed['run_id']))
    assert recovered['state']=='completed' and recovered['stages'][1]['state']=='completed'


def test_process_death_releases_lock_and_recovery_reuses_disk_snapshot(tmp_path,inputs):
    import subprocess
    import sys
    payload=tmp_path/'payload.json';r=request()
    payload.write_text(json.dumps(dict(passages=inputs[0],request=r)))
    script='''
import json,os,sys
from pathlib import Path
from src.retrieval.research_workflow import ResearchWorkflow
p=json.loads(Path(sys.argv[1]).read_text())
s=ResearchWorkflow(sys.argv[2],lambda _:p['passages'],'research-v1','fixture-encoder','fixture-corpus',lambda *_:os._exit(17),dict(model='fixture'))
s.save(p['request'])
'''
    result=subprocess.run([sys.executable,'-c',script,str(payload),str(tmp_path/'runs')],timeout=10)
    assert result.returncode==17
    store=store_at(tmp_path,inputs,retrieve=lambda _:pytest.fail('Must reuse disk snapshot'))
    assert store.read(r['request_id'])['state']=='interrupted'
    recovered=store.save(request(resume_of=r['request_id']))
    assert recovered['state']=='completed' and recovered['stages'][0]['state']=='reused'


def test_interrupt_after_response_publication_reuses_model_output(tmp_path,inputs,monkeypatch):
    import src.retrieval.research_workflow as module
    original=module.ResearchStore.save
    def publish_then_interrupt(self,request):
        original(self,request)
        raise KeyboardInterrupt
    monkeypatch.setattr(module.ResearchStore,'save',publish_then_interrupt)
    store=store_at(tmp_path,inputs);r=request()
    with pytest.raises(KeyboardInterrupt):store.save(r)
    old_response=store.directory/'responses'/f"{r['request_id']}.json"
    old_bytes=old_response.read_bytes()
    assert store.read(r['request_id'])['state']=='interrupted'
    monkeypatch.setattr(module.ResearchStore,'save',original)
    saved=store_at(tmp_path,inputs,lambda *_:pytest.fail('No repeated generation')).save(request(resume_of=r['request_id']))
    assert saved['state']=='completed'
    assert [s['state'] for s in saved['stages']]==['reused','reused','reused','completed']
    assert old_response.read_bytes()==old_bytes


def test_generation_identity_mismatch_is_failed_before_save(tmp_path,inputs):
    bad=dict(inputs[1],provenance=dict(model='other'))
    failed=store_at(tmp_path,inputs,lambda *_:bad).save(request())
    assert failed['state']=='failed' and failed['stages'][1]['reason']=='invalid_generation'
    assert failed['stages'][2]['state']=='pending' and 'response' not in failed
