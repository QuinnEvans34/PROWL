from copy import deepcopy
from io import BytesIO
import json
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import segmenter_lowrate_session_v1 as m,segmenter_session_v1 as old
from src.training.segmenter_normalized_loss_v1 import objective,LOSS

@pytest.fixture
def identity(monkeypatch):
    torch.set_num_threads(2);monkeypatch.setattr(m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    return m.make_identity(m.config(steps=10),{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')},run_id='segmenter-lowrate-synthetic-test',device='cpu')

@pytest.mark.parametrize('fault',['old_loss','v4_loss','old_task','old_schema','real_mode','shape','steps','nonfinite_rate','bool_steps','warm_init'])
def test_identity_isolation(identity,fault):
    i,c=deepcopy(identity)
    if fault=='old_loss':i['config']['loss_id']=old.LOSS_V3
    elif fault=='v4_loss':i['config']['loss_id']='voxel_ce_pancreas64_lesion256_present_foreground_dice_v4'
    elif fault=='old_task':i['task']=old.TASK
    elif fault=='old_schema':i['schema_version']='segmenter-synthetic-session-1'
    elif fault=='real_mode':i['data_mode']='qualified_real_cache'
    elif fault=='shape':i['config']['tensor_shape']=[192]*3
    elif fault=='steps':i['config']['max_steps']=481
    elif fault=='nonfinite_rate':i['config']['learning_rate']=float('nan')
    elif fault=='bool_steps':i['config']['max_steps']=True
    else:
        init=json.loads(c['initialization.json']);init['mode']='old_project';c['initialization.json']=canonical(init);i['initialization_sha256']=digest(c['initialization.json'])
    with pytest.raises(ValueError):m.Session(i,c)


def test_exact_restart_and_old_codec_isolation(identity):
    i,c=identity;s=m.Session(i,c);s.evaluate();s.synthetic_update();files=m.payload(s);r=m.restore_payload(files,i)
    assert s.synthetic_update()==r.synthetic_update()
    assert m.state_hash(s.model.state_dict())==m.state_hash(r.model.state_dict())
    assert m.progress(s)==m.progress(r)
    with pytest.raises(ValueError):old.decode(files,i)
    oldi,oldc=old.make_identity(old.config(steps=10),{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')},run_id='segmenter-synthetic-legacy-test',device='cpu')
    oldmodel=old.Session(oldi,oldc);legacy=old.payload(oldmodel)
    assert old.decode(legacy,oldi).step==0
    with pytest.raises(ValueError):m.decode(legacy,oldi)
    for call in (lambda:s.update(m.fixture('sparse')),lambda:s.import_weights(b'weights')):
        with pytest.raises(ValueError):call()


def test_dirty_step_and_checkpoint_refusal(identity,monkeypatch):
    i,c=identity;s=m.Session(i,c);before=m.payload(s);step=s.optimizer.step
    def fail():step();raise RuntimeError('injected post-mutation')
    monkeypatch.setattr(s.optimizer,'step',fail)
    with pytest.raises(RuntimeError):s.synthetic_update()
    assert s.dirty and s.step==0
    for f in (s.synthetic_update,lambda:m.payload(s),lambda:s.predict(m.fixture('sparse')[0])):
        with pytest.raises(ValueError):f()
    assert m.restore_payload(before,i).synthetic_update()['completed_step']==1

@pytest.mark.parametrize('fault',['optimizer_step','rng','target_role','state_identity','variance','extra_payload'])
def test_checkpoint_faults_refused(identity,fault):
    i,c=identity;s=m.Session(i,c);s.synthetic_update();files=m.payload(s)
    if fault=='extra_payload':files['external.pt']=b'extra'
    elif fault=='target_role':files['inputs.json']=canonical({'evaluator':'optimizer'})
    else:
        state=torch.load(BytesIO(files['state.pt']),weights_only=True)
        if fault=='optimizer_step':next(iter(state['optimizer']['state'].values()))['step']+=1
        elif fault=='variance':next(iter(state['optimizer']['state'].values()))['exp_avg_sq'].fill_(-1)
        elif fault=='rng':state['cpu_rng']=torch.zeros(3,dtype=torch.uint8)
        elif fault=='state_identity':state['identity_sha256']='a'*64
        b=BytesIO();torch.save(state,b);files['state.pt']=b.getvalue()
    with pytest.raises((ValueError,RuntimeError)):m.decode(files,i)

@pytest.fixture
def cli(monkeypatch,tmp_path):
    from scripts.diagnostics import segmenter_lowrate_qualification as q
    monkeypatch.setattr(m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    monkeypatch.setattr(q,'DEST',tmp_path/'diagnostic')
    monkeypatch.setattr(q,'context',lambda:{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')})
    monkeypatch.setattr(q,'pins',lambda:{'code':'a'*64})
    monkeypatch.setattr(q.a.c,'runtime',lambda:{'invented':'runtime'})
    return q


def test_request_persisted_pin_and_exclusive_creation(cli,capsys):
    cli.prepare();pin=capsys.readouterr().out.strip()
    assert pin==digest((cli.DEST/'request.json').read_bytes())
    assert cli.checked(pin)['total_synthetic_optimizer_calls']==960
    with pytest.raises(FileExistsError):cli.prepare()

@pytest.mark.parametrize('field',['bars','limits','loss','real','code','calls'])
def test_request_envelope_tampering(cli,field):
    cli.DEST.mkdir();r=cli.request()
    if field=='bars':r['bars']=dict(r['bars'],positive_lesion_dice=0)
    elif field=='limits':r['limits']=dict(r['limits'],trajectory_seconds=1000)
    elif field=='loss':r['identity']['config']['loss_id']=old.LOSS_V3
    elif field=='real':r['real_inputs_allowed']=True
    elif field=='code':r['source_pins']={'code':'b'*64}
    else:r['total_synthetic_optimizer_calls']=961
    from scripts.diagnostics.segmenter_source_verification import put
    put(cli.DEST/'request.json',r)
    with pytest.raises(ValueError):cli.checked(digest((cli.DEST/'request.json').read_bytes()))


def test_saved_payload_refuses_changed_bytes(cli):
    cli.DEST.mkdir();r=cli.request();s=m.Session(r['identity'],{n:v.encode() for n,v in r['controls'].items()});s.synthetic_update()
    ref=cli.save(s,'test');assert cli.load(ref,r['identity']).step==1
    p=cli.DEST/'test--state.pt';raw=p.read_bytes();p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    with pytest.raises(ValueError):cli.load(ref,r['identity'])


@pytest.mark.parametrize('rate',[.003,.0003,.0011,0,True])
def test_closed_cpu_rate_policy(rate):
    with pytest.raises(ValueError):m.validate_config(m.config(steps=480,lr=rate))


def test_old_v5_same_loss_checkpoint_is_not_lowrate(identity):
    from src.training import segmenter_normalized_session_v1 as previous
    i,c=identity;s=m.Session(i,c);files=m.payload(s)
    with pytest.raises(ValueError):previous.decode(files,i)
    oi,oc=previous.make_identity(previous.config(steps=10),{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')},run_id='segmenter-normalized-synthetic-before',device='cpu')
    legacy=previous.payload(previous.Session(oi,oc))
    assert previous.decode(legacy,oi).step==0
    with pytest.raises(ValueError):m.decode(legacy,oi)


def test_changed_optimizer_lr_is_refused(identity):
    i,c=identity;s=m.Session(i,c);s.synthetic_update();files=m.payload(s)
    state=torch.load(BytesIO(files['state.pt']),weights_only=True);state['optimizer']['param_groups'][0]['lr']=.003
    b=BytesIO();torch.save(state,b);files['state.pt']=b.getvalue()
    with pytest.raises(ValueError):m.decode(files,i)


def test_altered_identity_lr_is_refused(identity):
    i,c=identity;s=m.Session(i,c);files=m.payload(s);other=deepcopy(i);other['config']['learning_rate']=.003
    with pytest.raises(ValueError):m.decode(files,other)


def test_consumed_run_cannot_update_again(cli,monkeypatch):
    from scripts.diagnostics.segmenter_source_verification import put
    cli.prepare();pin=digest((cli.DEST/'request.json').read_bytes());put(cli.DEST/'consumed.json',{'already':'consumed'})
    monkeypatch.setattr(cli,'supervise',lambda *a,**k:pytest.fail('Consumption must fail before any worker'))
    with pytest.raises(FileExistsError):cli.run(pin)


def test_worker_requires_dispatch_and_cannot_start_twice(cli,monkeypatch):
    from scripts.diagnostics.segmenter_source_verification import put
    cli.prepare();pin=digest((cli.DEST/'request.json').read_bytes())
    with pytest.raises(FileNotFoundError):cli.worker('baseline',pin)
    put(cli.DEST/'baseline-consumed.json',dict(request_sha256=pin,state='consumed_no_retry',stage='baseline'))
    put(cli.DEST/'baseline-worker-started.json',dict(request_sha256=pin,state='single_use_worker_started',stage='baseline'))
    monkeypatch.setattr(m,'Session',lambda *a,**k:pytest.fail('Repeated worker must fail before model'))
    with pytest.raises(FileExistsError):cli.worker('baseline',pin)


@pytest.mark.parametrize('fault',[None,'parent_state','parent_sources'])
def test_predecessor_is_the_closed_d331_producer(monkeypatch,tmp_path,fault):
    from scripts.diagnostics import segmenter_lowrate_qualification as q,segmenter_normalized_qualification as previous
    assert q.predecessor is previous
    expected={'accepted':'a'*64}
    monkeypatch.setattr(previous,'pins',lambda:expected)
    monkeypatch.setattr(q.a.c,'REPO',tmp_path)
    for name in q.CODE:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
    def verify(dest,pin):
        assert dest==previous.DEST and pin==q.PREDECESSOR_PIN
        return dict(source_pins={'changed':'b'*64} if fault=='parent_sources' else expected,state='qualified' if fault=='parent_state' else 'learning_failed')
    monkeypatch.setattr(q,'verify_package',verify)
    if fault:
        with pytest.raises(ValueError):q.pins()
    else:assert q.pins()==expected|{n:digest(n.encode()) for n in q.CODE}
