from copy import deepcopy
import json
from pathlib import Path
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.operations.artifact_store import ArtifactStore
from src.operations import segmenter_backup_v1 as backup
from src.operations.segmenter_run_storage_v1 import run_stores
from src.training import segmenter_session_v1 as m
from scripts.diagnostics import segmenter_learning_rehearsal as runner
from test_segmenter_session import identity

@pytest.fixture
def backup_files(identity,tmp_path):
    i,c=identity;root=tmp_path/'primary';root.mkdir();store=ArtifactStore(root,check_root=lambda:None,minimum_free_bytes=0)
    s=m.Session(i,c);s.evaluate();s.synthetic_update();s.evaluate();ref=m.publish_checkpoint(store,s)
    files,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:m.validate_payload(f,i))
    artifact=root/digest(ref['artifact_id'].encode())
    files.update({'primary-complete.json':(artifact/'complete.json').read_bytes(),'primary-events.jsonl':(artifact/'events.jsonl').read_bytes(),
        'catalog.json':canonical(dict(source_reference=ref,source_domain='unit-device-A',destination_domain='unit-device-B',approval='D-322',omissions=[],state='verified_snapshot'))})
    return i,ref,files

@pytest.mark.parametrize('fault',['missing','receipt','events','payload','identity','catalog_ref','domain','approval','omission','source_type'])
def test_backup_rejects_incomplete_or_wrong_lineage(backup_files,fault):
    i,ref,f=deepcopy(backup_files)
    if fault=='missing':f.pop('catalog.json')
    elif fault=='receipt':ref['receipt_sha256']='a'*64
    elif fault=='events':f['primary-events.jsonl']+=b'x'
    elif fault=='payload':f['state.pt']+=b'x'
    elif fault=='identity':i['run_id']='segmenter-synthetic-other'
    elif fault=='source_type':
        r=json.loads(f['primary-complete.json']);r['metadata']['artifact_type']='localizer-checkpoint';f['primary-complete.json']=canonical(r);ref['receipt_sha256']=digest(f['primary-complete.json'])
    else:
        cat=json.loads(f['catalog.json'])
        if fault=='catalog_ref':cat['source_reference']['artifact_id']='other'
        elif fault=='domain':cat['destination_domain']=cat['source_domain']
        elif fault=='approval':cat['approval']='D-273'
        elif fault=='omission':cat['omissions']=['progress.json']
        f['catalog.json']=canonical(cat)
    with pytest.raises((ValueError,RuntimeError)):backup.validate_backup(f,i,ref)


def test_restore_without_primary_api_and_complete_members(backup_files,tmp_path):
    i,primary,f=backup_files;validation=lambda v:backup.validate_backup(v,i,primary)
    roots=[]
    for n in ('backup','restored'):
        p=tmp_path/n;p.mkdir();roots.append(ArtifactStore(p,check_root=lambda:None,minimum_free_bytes=0))
    store,target=roots;derivation=digest(canonical(primary));metadata=dict(artifact_type='segmenter-backup',schema_version='1.0.0',component='unit-fixture',code_sha256=i['source_sha256'],parents=[primary['receipt_sha256']],retention='test',sensitivity='synthetic',run_id=i['run_id'],stage_id='backup')
    pin,_=store.publish('unit-backup',derivation_sha256=derivation,files=f,metadata=metadata,validate=validation)
    payload,ref=backup.restore_backup(store,target,dict(artifact_id='unit-backup',receipt_sha256=pin,derivation_sha256=derivation),primary,i)
    assert set(payload)==set(m.CONTROLS)|{'identity.json','state.pt','progress.json'}
    s=m.restore_payload(payload,i);assert s.step==1 and len(s.evaluations)==2 and s.best is not None
    assert ref['artifact_id'].startswith('restore:')


def test_backup_same_device_or_domain_refused_before_resolve(tmp_path,identity):
    i,_=identity;stores=[]
    for n in ('a','b'):
        p=tmp_path/n;p.mkdir();stores.append(ArtifactStore(p,check_root=lambda:None,minimum_free_bytes=0))
    with pytest.raises(ValueError,match='Independent'):backup.backup_checkpoint(*stores,{},i,source_domain='a',destination_domain='b')
    with pytest.raises(ValueError,match='Independent'):backup.backup_checkpoint(*stores,{},i,source_domain='a',destination_domain='a')

@pytest.mark.parametrize('fault',['pin','approval','operation','primary','backup','restore','real_updates','quota','extra'])
def test_storage_scope_refused_before_registry_access(fault,tmp_path):
    cap=json.loads(runner.CAP.read_bytes());pin=runner.CAP_PIN
    if fault=='pin':pin='a'*64;raw=runner.CAP.read_bytes()
    else:
        k={'approval':'approval','operation':'operation','primary':'primary_area','backup':'backup_area','restore':'restore_area','real_updates':'real_optimizer_updates_allowed','quota':'max_new_bytes_per_domain','extra':'extra'}[fault]
        cap[k]={'real_updates':True,'quota':2*1024**3}.get(fault,'bad');raw=canonical(cap);pin=digest(raw)
    with pytest.raises(ValueError):run_stores(tmp_path/'absent-registry',raw,trusted_capability_sha256=pin)


def report_prediction(kind='exact'):
    rows=[]
    for name in m.NAMES:
        _,y=m.fixture(name);prediction=y.clone()
        if kind=='collapse':prediction.fill_(0)
        if kind=='false_lesion' and name=='verified_negative':prediction.fill_(2)
        rows.append(dict(member_id=name,loss=.1,metrics=m.metrics(prediction,y)))
    return dict(step=120,cases=rows)


def test_learning_gate_catches_collapse_negative_and_stalled_loss():
    initial=report_prediction();initial['cases']=[dict(r,loss=1.) for r in initial['cases']]
    assert runner.gate(initial,report_prediction())['passed']
    assert not runner.gate(initial,report_prediction('collapse'))['passed']
    assert not runner.gate(initial,report_prediction('false_lesion'))['passed']
    assert not runner.gate(report_prediction(),report_prediction())['passed']

@pytest.mark.parametrize('fault',['limits','bars','device','config','real','stage','cap'])
def test_invocation_envelope_cannot_silently_expand(fault):
    inv=dict(stage='cpu',decision='D-322',synthetic_only=True,limits=deepcopy(runner.CPU_LIMITS),bars=deepcopy(runner.BARS),capability_sha256=runner.CAP_PIN,identity=dict(config=m.config(steps=480),device='cpu'))
    runner.envelope(inv)
    if fault=='limits':inv['limits']['seconds']+=1
    elif fault=='bars':inv['bars']['positive_lesion_recall']=.1
    elif fault=='device':inv['identity']['device']='mps'
    elif fault=='config':inv['identity']['config']['max_steps']=481
    elif fault=='real':inv['synthetic_only']=False
    elif fault=='stage':inv['stage']='training'
    elif fault=='cap':inv['capability_sha256']='a'*64
    with pytest.raises(ValueError):runner.envelope(inv)


def test_worker_consumption_is_exclusive_before_update(tmp_path,monkeypatch):
    dest=tmp_path/'evidence';dest.mkdir();seen=[]
    monkeypatch.setattr(runner,'checked',lambda d,p:(dict(stage='cpu'),{}))
    monkeypatch.setattr(runner,'cpu_worker',lambda *a,**k:seen.append('updated'))
    monkeypatch.setattr('sys.argv',['rehearsal','--worker',str(dest),'--stage','cpu','--pin','a'*64])
    runner.main();assert seen==['updated']
    with pytest.raises(FileExistsError):runner.main()
    assert seen==['updated']
