from copy import deepcopy
from io import BytesIO
from pathlib import Path
import json
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.data.cohort_registry import COHORT_ID,MEMBERS
from src.training.localizer import LocalizerSession
from src.training.localizer_run import payload,validate_payload,publish_checkpoint,bind_item,MPSRun
from src.operations.artifact_store import ArtifactStore
from src.operations.localizer_backup import validate_backup,restore_backup,backup_checkpoint
from src.operations.localizer_run_storage import tree_bytes,CappedStore


@pytest.fixture
def bundle():
    torch.set_num_threads(2)
    config=dict(patch_size=[16]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=100)
    controls={'inputs.json':canonical(dict(cohort_id=COHORT_ID,members=[dict(study_id=s,cohort_id=COHORT_ID) for s in MEMBERS],recipe={})),
        'source.json':b'{}','environment.json':b'{}'}
    identity=dict(schema_version='2.0.0',run_id='localizer-bridge-test',purpose='prelaunch-verification',training_data='synthetic',device='mps',config=config,
        inputs_sha256=digest(controls['inputs.json']),source_sha256=digest(controls['source.json']),environment_sha256=digest(controls['environment.json']))
    session=LocalizerSession(config)
    return payload(session,identity,controls),identity


def store(path):
    path.mkdir();return ArtifactStore(path,check_root=lambda:None,minimum_free_bytes=0)


@pytest.mark.parametrize('key',['inputs.json','source.json','environment.json','identity.json'])
def test_control_mutation_rejected(bundle,key):
    files,identity=bundle;files[key]+=b' '
    with pytest.raises(ValueError):validate_payload(files,identity)


def test_mismatched_state_identity(bundle):
    files,identity=bundle;changed=deepcopy(identity);changed['run_id']+='-other';files['identity.json']=canonical(changed)
    with pytest.raises(ValueError,match='identity'):validate_payload(files,changed)


def test_prelaunch_refuses_real_update():
    with pytest.raises(ValueError,match='separately approved'):MPSRun.update(None,None,None,None)


def test_binding_rejects_before_data_read(bundle):
    _,identity=bundle
    class Dataset:
        descriptors=[dict(study_id=s,cohort_id=COHORT_ID) for s in MEMBERS];recipe={'changed':True}
        def __getitem__(self,index):raise AssertionError('payload opened')
    with pytest.raises(ValueError,match='Dataset changed'):bind_item(Dataset(),0,identity)


def test_wrong_member_rejected(bundle):
    files,identity=bundle
    inputs=json.loads(files['inputs.json']);inputs['members'][0]['study_id']='held'
    files['inputs.json']=canonical(inputs);identity['inputs_sha256']=digest(files['inputs.json']);files['identity.json']=canonical(identity)
    with pytest.raises(ValueError,match='membership'):validate_payload(files,identity)


def test_backup_independence_and_restore_without_primary(bundle,tmp_path):
    files,identity=bundle;primary=store(tmp_path/'primary');backup=store(tmp_path/'backup');restore=store(tmp_path/'restored')
    ref=publish_checkpoint(primary,files,identity)
    with pytest.raises(ValueError,match='Independent'):backup_checkpoint(primary,backup,ref,identity,source_domain='a',destination_domain='b')
    # Assemble a synthetic cross-domain receipt fixture; live independent media are tested separately.
    directory=primary.root/digest(ref['artifact_id'].encode())
    snapshot=dict(files,**{'primary-complete.json':(directory/'complete.json').read_bytes(),
        'primary-events.jsonl':(directory/'events.jsonl').read_bytes(),
        'catalog.json':canonical(dict(source_reference=ref,source_domain='a',destination_domain='b',approval='D-273',omissions=[],state='verified_snapshot'))})
    valid=lambda f:validate_backup(f,identity,ref)
    _,original=primary.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:validate_payload(f,identity))
    pin,_=backup.publish('backup-fixture',derivation_sha256='a'*64,files=snapshot,metadata=original['metadata'],validate=valid)
    # Primary reads now fail; restore API never receives it.
    primary.check_root=lambda: (_ for _ in ()).throw(AssertionError('primary read forbidden'))
    restored,new=restore_backup(backup,restore,dict(artifact_id='backup-fixture',receipt_sha256=pin,derivation_sha256='a'*64),ref,identity)
    assert restored==files and new['status']=='published'
    snapshot['state.pt']=b'corrupt'
    with pytest.raises(ValueError):valid(snapshot)


def test_capacity_counts_hidden_attempts_and_rejects_symlinks(tmp_path):
    (tmp_path/'.attempt-x').mkdir();(tmp_path/'.attempt-x'/'data').write_bytes(b'123')
    assert tree_bytes(tmp_path)==3
    (tmp_path/'link').symlink_to(tmp_path/'.attempt-x'/'data')
    with pytest.raises(ValueError):tree_bytes(tmp_path)


def test_scoped_quota_fails_without_publishing(tmp_path,bundle):
    files,identity=bundle
    capped=CappedStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0,quota_root=tmp_path,quota_bytes=1)
    with pytest.raises(ValueError,match='quota'):publish_checkpoint(capped,files,identity)
    assert not list(tmp_path.glob('.attempt-*'))


def test_recovery_root_factory_never_requires_primary(tmp_path,monkeypatch):
    import yaml
    import src.operations.localizer_run_storage as module
    reg=yaml.safe_load((module.REPO/'configs/local/roots.example.yaml').read_text())
    internal=tmp_path/'internal';internal.mkdir();backup=internal/'backup';backup.mkdir()
    reg['failure_domains']['external_primary']['mount_path']=str(tmp_path/'ABSENT')
    reg['failure_domains']['internal_backup']['mount_path']=str(internal)
    reg['roots']['prowl_artifacts']['path']=str(tmp_path/'ABSENT'/'artifacts')
    reg['roots']['prowl_backup']['path']=str(backup)
    path=tmp_path/'roots.yaml';path.write_text(yaml.safe_dump(reg))
    cap=json.loads((module.REPO/'docs/capstone/operations/LOCALIZER-RUN-CAPABILITY-2026-09-28.json').read_bytes())
    cap.update(registry_sha256=digest(path.read_bytes()),primary_volume_uuid=reg['failure_domains']['external_primary']['volume_uuid'],
        backup_volume_uuid=reg['failure_domains']['internal_backup']['volume_uuid'])
    def info(p):
        assert p==internal,'Primary accessed during recovery'
        return dict(VolumeUUID=cap['backup_volume_uuid'],FilesystemType='apfs',MountPoint=str(internal),WritableVolume=True)
    monkeypatch.setattr(module,'disk_info',info);monkeypatch.setattr(Path,'is_mount',lambda p:p==internal)
    raw=canonical(cap)
    primary,b,r=module.run_stores(path,raw,trusted_capability_sha256=digest(raw),create=True,recovery_only=True)
    assert primary is None and b.root==backup/'localizer-keepers' and r.root==backup/'localizer-restores'
    monkeypatch.setattr(module,'disk_info',lambda p:dict(info(p),VolumeUUID='changed'))
    with pytest.raises(ValueError,match='APFS'):b.check_root()


@pytest.mark.parametrize('fault',['hash','scope','launch'])
def test_storage_capability_rejected_before_roots(tmp_path,fault):
    import src.operations.localizer_run_storage as module
    cap=json.loads((module.REPO/'docs/capstone/operations/LOCALIZER-RUN-CAPABILITY-2026-09-28.json').read_bytes())
    if fault=='scope':cap['primary_area']='sources'
    if fault=='launch':cap['real_optimizer_updates_allowed']=True
    raw=canonical(cap)
    with pytest.raises(ValueError):module.run_stores(tmp_path/'absent',raw,trusted_capability_sha256='0'*64 if fault=='hash' else digest(raw))


def test_native_apfs_data_mount_identity():
    from src.operations.localizer_run_storage import mounted_apfs
    info={'DeviceNode':'/dev/disk3s5'};mount=Path('/System/Volumes/Data')
    assert mounted_apfs(info,mount,'/dev/disk3s5 on /System/Volumes/Data (apfs, local, journaled)')
    assert not mounted_apfs(info,mount,'/dev/disk4s5 on /System/Volumes/Data (apfs, local)')
    assert not mounted_apfs(info,mount,'/dev/disk3s5 on /System/Volumes/Data-other (apfs, local)')
    assert not mounted_apfs(info,mount,'/dev/disk3s5 on /System/Volumes/Data (exfat, local)')
