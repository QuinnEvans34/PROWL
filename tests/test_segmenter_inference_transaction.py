from copy import deepcopy
import json
import os
from pathlib import Path
import pytest
from src.operations.artifact_store import ArtifactStore
from src.operations import segmenter_inference_backup_v1 as b,segmenter_inference_storage_v1 as storage
from src.data.manifest_records import canonical,digest
from scripts.diagnostics import segmenter_inference_qualification as cli

@pytest.mark.parametrize('event',['open','os.listdir','os.scandir'])
def test_primary_guard(event):
    with pytest.raises(ValueError):cli.audit_primary(event,('/Volumes/PROWL-Data/artifacts/cache',))
    cli.audit_primary(event,('/private/tmp/independent',))

@pytest.mark.parametrize('fault',['approval','area','operation','updates','registry'])
def test_capability_no_broadening(tmp_path,fault):
    cap=json.loads(cli.CAP.read_bytes())
    if fault=='approval':cap['approval']='D-322'
    if fault=='area':cap['primary_area']='segmenter-runs'
    if fault=='operation':cap['operation']='training'
    if fault=='updates':cap['real_optimizer_updates_allowed']=True
    if fault=='registry':cap['registry_sha256']='0'*64
    raw=canonical(cap)
    registry=tmp_path/'invented-registry.json';registry.write_bytes(b'invented registry')
    with pytest.raises(ValueError):storage.inference_stores(registry,raw,trusted_capability_sha256=digest(raw))

def test_backup_requires_task_and_semantic_receipt():
    payload={'invented':b'x'};ref=dict(artifact_id='test',receipt_sha256='x',derivation_sha256='y')
    # Old/synthetic artifact types must fail before accepting an arbitrary validator.
    receipt=dict(state='complete',artifact_id='test',derivation_sha256='y',metadata={'artifact_type':'segmenter-checkpoint'})
    raw=canonical(receipt);ref['receipt_sha256']=digest(raw)
    files=dict(payload,**{'primary-complete.json':raw,'primary-events.jsonl':b'','catalog.json':b'{}'})
    with pytest.raises(ValueError):b.validate_backup(files,{},ref,lambda *_:{})

def test_completion_last_failure_and_no_reuse(tmp_path):
    store=ArtifactStore(tmp_path,check_root=lambda:None,max_bytes=1024**2,minimum_free_bytes=0)
    meta=dict(artifact_type='invented',schema_version='1.0.0',component='test',code_sha256='0'*64,parents=[],retention='test',sensitivity='synthetic',run_id='test',stage_id='test')
    def fail(_):raise ValueError('semantic failure')
    with pytest.raises(ValueError):store.publish('fault',derivation_sha256='0'*64,files={'x':b'x'},metadata=meta,validate=fail)
    assert not list(tmp_path.rglob('complete.json'))

def test_recovery_interface_has_no_primary_parameter():
    import inspect
    assert 'primary' not in inspect.signature(b.restore_backup).parameters
