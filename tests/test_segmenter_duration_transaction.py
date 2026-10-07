from copy import deepcopy
from io import BytesIO
import json
import pytest
import torch
from segmenter_duration_fixtures import request
from src.data.manifest_records import canonical
from src.training import segmenter_duration_session_v1 as core

@pytest.fixture(scope='module')
def setup():return request()

@pytest.fixture(scope='module')
def saved(setup):
    r,p=setup;torch.set_num_threads(2);s=core.Session(r['identity'],{n:v.encode() for n,v in r['controls'].items()})
    counters={'forwards':0,'optimizer_calls':0}
    s.model.register_forward_pre_hook(lambda *a:counters.__setitem__('forwards',counters['forwards']+1))
    s.optimizer.register_step_pre_hook(lambda *a:counters.__setitem__('optimizer_calls',counters['optimizer_calls']+1))
    s.update(p);files=core.payload(s);s.update(p)
    restored=core.restore_payload(files,r['identity'])
    restored.model.register_forward_pre_hook(lambda *a:counters.__setitem__('forwards',counters['forwards']+1))
    restored.optimizer.register_step_pre_hook(lambda *a:counters.__setitem__('optimizer_calls',counters['optimizer_calls']+1))
    restored.update(p)
    assert core.tree_exact(s.model.state_dict(),restored.model.state_dict()) and core.tree_exact(s.optimizer.state_dict(),restored.optimizer.state_dict()) and core.progress(s)==core.progress(restored) and core.tree_exact(s.cpu_rng,restored.cpu_rng)
    x=p.get(p.control['train'][0],role='train',operation='inference').image
    assert (s.predict(x)==restored.predict(x)).all()
    old=restored.optimizer.step
    def interrupt():old();raise RuntimeError('invented interruption after optimizer mutation')
    restored.optimizer.step=interrupt
    with pytest.raises(RuntimeError):restored.update(p)
    assert restored.dirty and restored.step==2
    for f in (lambda:restored.update(p),lambda:core.payload(restored),lambda:restored.predict(x)):
        with pytest.raises(ValueError):f()
    assert counters==dict(forwards=6,optimizer_calls=4)
    print('\nDUR02_TINY_CALLS '+json.dumps(counters))
    return files,r['identity']

def test_uninterrupted_and_interrupted_byte_recovery(saved):
    files,i=saved;assert core.restore_payload(files,i).step==1

@pytest.mark.parametrize('fault',['task','run','step','cursor','exposure','member','lr','init','lineage','extra','optimizer','head','rng','nan'])
def test_complete_state_forgery_refused(saved,fault):
    files,i=deepcopy(saved)
    if fault in ('task','run'):i['task' if fault=='task' else 'run_id']='wrong'
    elif fault=='extra':files['extra']=b'junk'
    elif fault in ('init','lineage'):
        name='initialization.json' if fault=='init' else 'lineage.json';v=json.loads(files[name]);v['weight_imports' if fault=='init' else 'selected_import_sha256']=['not allowed'];files[name]=canonical(v)
    elif fault in ('optimizer','head','rng','nan'):
        v=torch.load(BytesIO(files['state.pt']),weights_only=True)
        if fault=='optimizer':v['optimizer']['state'][0]['step']+=1
        if fault=='head':v['model']['conv_final.2.conv.weight']=v['model']['conv_final.2.conv.weight'][:2]
        if fault=='rng':v['cpu_rng']=torch.zeros(1,dtype=torch.float32)
        if fault=='nan':next(iter(v['model'].values())).view(-1)[0]=float('nan')
        buf=BytesIO();torch.save(v,buf);files['state.pt']=buf.getvalue()
    else:
        v=json.loads(files['progress.json'])
        if fault=='step':v['step']+=1
        if fault=='cursor':v['sampler']['cursor']+=1
        if fault=='exposure':v['exposure']['invented-train-0']+=1
        if fault=='member':v['history'][0]['member_id']='invented-validation'
        if fault=='lr':v['history'][0]['learning_rate']=.003
        files['progress.json']=canonical(v)
    with pytest.raises((ValueError,KeyError)):core.validate_payload(files,i)

def test_192_sampling_is_same_first48_and32_complete_epochs(setup):
    from src.training import segmenter_v5_training_session_v1 as old
    p=setup[1];cfg=core.config();seq=[core.next_member(cfg,p.control,i) for i in range(192)]
    assert seq[:48]==[old.next_member(old.config(size=144,steps=48),p.control,i) for i in range(48)]
    for i in range(0,192,6):assert set(n for n,_ in seq[i:i+6])==set(p.control['train'])
    assert {n:sum(k==n for k,_ in seq) for n in p.control['train']}=={n:32 for n in p.control['train']}

@pytest.mark.parametrize('fault',['rate','head','shape','duration','jitter','selection','schedule'])
def test_recipe_changes_require_new_scope(fault):
    c=core.config()
    if fault=='rate':c['learning_rate']=.003
    if fault=='head':c['architecture']['out_channels']=2
    if fault=='shape':c['tensor_shape']=[24,144,144]
    if fault=='duration':c['max_steps']=193
    if fault=='jitter':c['jitter']='translation'
    if fault=='selection':c['primary_checkpoint']='best_validation'
    if fault=='schedule':c['lr_schedule']='cosine'
    with pytest.raises(ValueError):core.validate_config(c)

def test_no_actual_permit_or_tuple_import(setup):
    r,p=setup;s=core.Session(r['identity'],{n:v.encode() for n,v in r['controls'].items()})
    with pytest.raises(ValueError):core.UpdatePermit(object(),'a'*64,'b'*64)
    with pytest.raises(ValueError):s.update((None,None))
    with pytest.raises(ValueError):s.import_weights({})
    assert s.step==0 and not s.dirty
