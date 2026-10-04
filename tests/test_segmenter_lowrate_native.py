import json
from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest
import torch
from src.data.manifest_records import canonical,digest
from scripts.diagnostics import segmenter_lowrate_native_qualification as q


@pytest.fixture
def parent(monkeypatch,tmp_path):
    monkeypatch.setattr(q,'ROOT',tmp_path)
    monkeypatch.setattr(q,'REPO',tmp_path)
    registry=canonical(dict(roots=dict(prowl_artifacts=dict(path=str(tmp_path/'primary')),prowl_backup=dict(path=str(tmp_path/'backup'),cap_bytes=20*1024**3))))
    config=tmp_path/'configs/local';config.mkdir(parents=True);(config/'roots.yaml').write_bytes(registry)
    monkeypatch.setattr(q,'REG_PIN',digest(registry))
    monkeypatch.setattr(q.cpu,'pins',lambda:{'accepted':'a'*64})
    area=tmp_path/'independent';area.mkdir();raw=canonical({'retained':'manifest'});(area/'manifest.json').write_bytes(raw)
    proof=dict(learning_passed=True,cold_checkpoints=[{}]*4,primary_python_reads_blocked=True,destination=str(area),manifest_sha256=digest(raw),whole_root_after_bytes=14479045461)
    (tmp_path/'SEGMENTER-LOWRATE-CPU-INDEPENDENT-PRESERVATION-20261003.json').write_bytes(canonical(proof))
    return tmp_path,proof


@pytest.mark.parametrize('fault',[None,'gate','state','sources'])
def test_cpu_learning_required_before_native(parent,monkeypatch,fault):
    def verified(dest,pin):
        assert dest==q.cpu.DEST and pin==q.CPU_PIN
        return dict(state='learning_failed' if fault=='state' else 'qualified',gate={'passed':fault!='gate'},source_pins={'changed':'b'*64} if fault=='sources' else q.cpu.pins())
    monkeypatch.setattr(q,'verify_package',verified)
    if fault:
        with pytest.raises(ValueError):q.qualified_cpu()
    else:assert len(q.qualified_cpu())==64


def cap_for(reg,proof):
    base=proof['whole_root_after_bytes']
    return dict(decision='D-332',registry_sha256=q.REG_PIN,primary_area=str(Path(reg['roots']['prowl_artifacts']['path'])/'segmenter-lowrate-D332-MPS-20261003'),backup_area=str(Path(reg['roots']['prowl_backup']['path'])/'segmenter-lowrate-D332-MPS-20261003'),backup_root=reg['roots']['prowl_backup']['path'],backup_baseline_bytes=base,absolute_backup_ceiling=min(base+q.LIMITS['new_backup_bytes'],14892449687,reg['roots']['prowl_backup']['cap_bytes']),maximum_new_primary_bytes=q.LIMITS['new_primary_bytes'],maximum_new_backup_bytes=q.LIMITS['new_backup_bytes'],primary_uuid='22750B93-2F3F-499D-87F5-902981BFAB59',backup_uuid='542E8B1F-8D50-4783-9250-752DFDC899CD',invented_only=True)


@pytest.mark.parametrize('fault',[None,'path','ceiling','reset','real'])
def test_native_storage_bound_to_registry_and_prior_occupancy(parent,monkeypatch,fault):
    _,proof=parent;reg=q.registry();cap=cap_for(reg,proof)
    if fault=='path':cap['backup_area']='/tmp/other'
    if fault=='ceiling':cap['absolute_backup_ceiling']+=1
    if fault=='reset':cap['backup_baseline_bytes']=0
    if fault=='real':cap['invented_only']=False
    if fault:
        with pytest.raises(ValueError):q.validate_cap(cap)
    else:q.validate_cap(cap)


def test_exact_native_request_counts_fresh_scratch(parent,monkeypatch):
    _,proof=parent;cap=cap_for(q.registry(),proof)
    monkeypatch.setattr(q,'qualified_cpu',lambda:'a'*64)
    monkeypatch.setattr(q,'pins',lambda:{'accepted':'a'*64})
    monkeypatch.setattr(q.cpu.a.c,'runtime',lambda:{'native':'test'})
    monkeypatch.setattr(q.m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    r=q.request(cap);assert r['checkpoint_steps']==[0,2,4]
    assert r['produce_optimizer_calls']==5 and r['recovery_optimizer_calls']==r['dirty_calls']==1 and r['max_model_forwards']==8
    assert r['identity']['config']['tensor_shape']==[144]*3 and r['identity']['config']['learning_rate']==.0003
    assert json.loads(r['controls']['initialization.json'])['weight_imports']==[]
    assert not r['real_inputs_allowed'] and not r['automatic_launch_allowed']


@pytest.mark.parametrize('fault',['step','member'])
def test_checkpoint_reference_refused_before_any_open(tmp_path,fault):
    ref=dict(step=3 if fault=='step' else 2,payload={'../../wrong.pt':{}} if fault=='member' else {n:{} for n in set(q.m.CONTROLS)|{'identity.json','progress.json','state.pt'}})
    with pytest.raises(ValueError):q.restore_checkpoint(tmp_path,ref,{})


def test_native_class_counts_independent_integer_oracle():
    y=np.array([0,0,0,0,1,1,2,2],np.uint8).reshape(2,2,2);p=np.array([0,0,1,2,1,2,2,0],np.uint8).reshape(2,2,2)
    rows=q.class_counts(p,y)
    assert [(r['target_voxels'],r['predicted_voxels'],r['true_positive']) for r in rows]==[(4,3,2),(2,2,1),(2,3,1)]
    assert [r['dice'] for r in rows]==[4/7,.5,2/5] and [r['recall'] for r in rows]==[.5,.5,.5]
    with pytest.raises(ValueError):q.class_counts(p.astype(float),y)


def test_keeper_changed_or_extra_member_refused(tmp_path):
    raw=b'protected';(tmp_path/'state.pt').write_bytes(raw);manifest={'files':{'state.pt':dict(bytes=len(raw),sha256=digest(raw))}}
    encoded=canonical(manifest);(tmp_path/'manifest.json').write_bytes(encoded);q.verify_flat(tmp_path,manifest,digest(encoded))
    (tmp_path/'unbound').write_bytes(b'extra')
    with pytest.raises(ValueError):q.verify_flat(tmp_path,manifest,digest(encoded))


def test_native_worker_without_dispatch_refused(parent,monkeypatch,tmp_path):
    monkeypatch.setattr(q,'DEST',tmp_path/'unprepared');q.DEST.mkdir()
    monkeypatch.setattr(q,'checked',lambda pin:{})
    monkeypatch.setattr(q,'native_preflight',lambda:None)
    monkeypatch.setattr(q,'domains',lambda *a,**k:None)
    with pytest.raises(FileNotFoundError):q.worker('produce','a'*64)
    assert not (q.DEST/'produce-worker-started.json').exists()
