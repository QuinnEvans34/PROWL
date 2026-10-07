from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import pytest
from segmenter_duration_fixtures import request
from src.data.manifest_records import canonical,digest
from src.operations import segmenter_duration_storage_v1 as storage,segmenter_duration_dispatch_v1 as dispatcher

@pytest.fixture(scope='module')
def cap():return request('scientific')[0]['storage_capability']

@pytest.mark.parametrize('fault',[None,'absolute','growth','phase','child','free','baseline','domains','delete','float'])
def test_exact_26gib_budget_and_joint_growth_guard(cap,fault):
    c=deepcopy(cap)
    if fault=='absolute':c['absolute_backup_ceiling']=20*storage.GIB
    if fault=='growth':c['maximum_new_backup_bytes']+=1
    if fault=='phase':c['phase_ceiling']=8*storage.GIB
    if fault=='child':c['child_ceiling']=True
    if fault=='free':c['minimum_free_bytes']=1
    if fault=='baseline':c['backup_baseline_bytes']=20*storage.GIB
    if fault=='domains':c['backup_volume_uuid']=c['primary_volume_uuid']
    if fault=='delete':c['delete_old_evidence']=True
    if fault=='float':c['maximum_new_backup_bytes']=float(c['maximum_new_backup_bytes'])
    if fault is None:assert storage.validate_capability(canonical(c))==c
    else:
        with pytest.raises(ValueError):storage.validate_capability(canonical(c))

def test_budget_authority_cannot_grant_training(cap):
    raw=canonical(cap);a=dict(kind='exact_duration_storage_v1',author='Quinton Evans',user_instruction='INVENTED TEST ONLY',capability_sha256=digest(raw),budget_bytes=26*storage.GIB,preserve_old_evidence=True,launch_authorized=False);approval=canonical(a)
    storage.validate_storage_authority(raw,approval,digest(approval))
    a['launch_authorized']=True;approval=canonical(a)
    with pytest.raises(ValueError):storage.validate_storage_authority(raw,approval,digest(approval))

def test_readonly_cache_never_opens_writer(tmp_path):
    store=storage.ReadOnlyStore(tmp_path,check_root=lambda:None,max_bytes=4096,minimum_free_bytes=0)
    with pytest.raises(ValueError):
        with store.writer(None):pass

@pytest.mark.parametrize('fault',['pin','symlink','hardlink','size','relative'])
def test_controls_reject_unsafe_paths_and_changed_bytes(tmp_path,fault):
    path=tmp_path/'control.json';path.write_bytes(b'{}');pin=digest(b'{}');bound=4096
    if fault=='pin':pin='0'*64
    if fault=='symlink':link=tmp_path/'alias';link.symlink_to(path);path=link
    if fault=='hardlink':__import__('os').link(path,tmp_path/'second')
    if fault=='size':bound=1
    if fault=='relative':path=Path('control.json')
    with pytest.raises((ValueError,FileNotFoundError)):dispatcher.read_control(path,pin,bound)

def test_unit_echo_absolute_cli_and_consumed_replay(tmp_path):
    r,p=request();request_path=tmp_path/'request.json';request_path.write_bytes(canonical(r));pin=digest(canonical(r));dest=tmp_path/'job';dest.mkdir()
    result=dispatcher.dispatch(request_path,pin,dest,stage='unit_echo')
    assert result['resources']['workers_reaped'] and json.loads((dest/'unit-worker-result.json').read_bytes())==dict(state='unit_no_model_worker_complete',model_forwards=0,optimizer_calls=0)
    with pytest.raises(FileExistsError):dispatcher.dispatch(request_path,pin,dest,stage='unit_echo')


def test_unit_cannot_launch_native_worker(tmp_path):
    r,p=request();path=tmp_path/'request';path.write_bytes(canonical(r))
    with pytest.raises(ValueError):dispatcher.dispatch(path,digest(canonical(r)),tmp_path,stage='producer')
    assert not (tmp_path/'dispatch-producer-consumed.json').exists()


def test_watchdog_terminates_and_reaps_only_owned_worker():
    process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True)
    with pytest.raises(ValueError,match='resource'):dispatcher.watch(process,seconds=.15,rss_bytes=3*storage.GIB)
    assert process.poll() is not None


def test_watchdog_stops_before_rss_overflow(monkeypatch):
    process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True)
    monkeypatch.setattr(dispatcher,'owned_tree',lambda pid:({pid},1000))
    with pytest.raises(ValueError,match='resource'):dispatcher.watch(process,seconds=2,rss_bytes=100)
    assert process.poll() is not None

@pytest.mark.parametrize('quota',['child','phase','growth','absolute'])
def test_quota_counts_other_children_and_old_failures(cap,tmp_path,monkeypatch,quota):
    c=deepcopy(cap);backup=tmp_path/'backup';backup.mkdir();root=backup/storage.areas(c)['keeper'];root.mkdir()
    store=storage.PhaseStore(root,cap=c,backup_root=backup,check_root=lambda:None,max_bytes=4096,minimum_free_bytes=0,quota_root=backup,quota_bytes=c['absolute_backup_ceiling'])
    monkeypatch.setattr(storage.CappedStore,'space',lambda *a:None)
    sizes={}
    if quota=='child':sizes[root]=c['child_ceiling']
    if quota=='phase':sizes[backup/storage.areas(c)['controls']]=c['phase_ceiling'];(backup/storage.areas(c)['controls']).mkdir()
    if quota=='growth':sizes[backup]=c['backup_baseline_bytes']+c['maximum_new_backup_bytes']
    if quota=='absolute':sizes[backup]=c['absolute_backup_ceiling']
    monkeypatch.setattr(storage,'tree_bytes',lambda p:sizes.get(p,0))
    with pytest.raises(ValueError,match='quota'):store.space(None,1)


def registry_fixture(tmp_path,cap,monkeypatch):
    import yaml
    c=deepcopy(cap)
    reg=dict(scientific_runs_enabled=False,roots=dict(prowl_artifacts=dict(path='',role='artifact',access='setup_only',failure_domain='external_primary'),prowl_backup=dict(path='',role='backup',access='selected_controls_and_keepers',failure_domain='internal_backup',cap_bytes=c['absolute_backup_ceiling'],minimum_free_bytes=c['minimum_free_bytes'],automatic_deletion=False)),failure_domains=dict(external_primary=dict(mount_path='',volume_uuid='invented-external'),internal_backup=dict(mount_path='',volume_uuid='invented-internal')))
    mounts=[tmp_path/'primary-mount',tmp_path/'backup-mount'];roots=[m/'root' for m in mounts]
    for root in roots:root.mkdir(parents=True)
    for n,root,uuid in zip(('prowl_artifacts','prowl_backup'),roots,('invented-external','invented-internal')):
        reg['roots'][n]['path']=str(root);d=reg['failure_domains'][reg['roots'][n]['failure_domain']];d['mount_path']=str(root.parent);d['volume_uuid']=uuid
    reg['roots']['prowl_backup']['cap_bytes']=c['absolute_backup_ceiling']
    path=tmp_path/'registry.yaml';path.write_text(yaml.safe_dump(reg));c['registry_sha256']=digest(path.read_bytes())
    monkeypatch.setattr(Path,'is_mount',lambda p:p in mounts)
    def probe(m):return dict(VolumeUUID='invented-external' if m==mounts[0] else 'invented-internal',MountPoint=str(m),FilesystemType='apfs',WritableVolume=True,Internal=m==mounts[1])
    monkeypatch.setattr(storage,'disk_info',probe)
    from types import SimpleNamespace
    monkeypatch.setattr(storage.os,'statvfs',lambda p:SimpleNamespace(f_bavail=200*storage.GIB,f_frsize=1))
    return path,c,roots,mounts


def test_current_registry_requires_exact_cap_mount_identity_and_free_floor(tmp_path,cap,monkeypatch):
    path,c,roots,mounts=registry_fixture(tmp_path,cap,monkeypatch)
    got,check=storage.registry_context(path,c);assert got==roots;check(0);check(1)
    monkeypatch.setattr(storage,'disk_info',lambda m:dict(VolumeUUID='wrong',MountPoint=str(m),FilesystemType='apfs',WritableVolume=True))
    with pytest.raises(ValueError):check(0)
    path.write_text(path.read_text()+'\n# mutated registry\n')
    with pytest.raises(ValueError):check(1)


def test_cold_storage_observes_only_internal_volume(tmp_path,cap,monkeypatch):
    path,c,roots,mounts=registry_fixture(tmp_path,cap,monkeypatch)
    for key in ('keeper','restore','controls'):(roots[1]/storage.areas(c)[key]).mkdir()
    probe=storage.disk_info
    monkeypatch.setattr(storage,'disk_info',lambda m:probe(m) if m==mounts[1] else pytest.fail('Cold touched primary'))
    raw=canonical(c);approval=canonical(dict(kind='exact_duration_storage_v1',author='Quinton Evans',user_instruction='INVENTED TEST ONLY',capability_sha256=digest(raw),budget_bytes=c['absolute_backup_ceiling'],preserve_old_evidence=True,launch_authorized=False))
    stores=storage.duration_stores(path,raw,trusted_capability_sha256=digest(raw),approval=approval,trusted_approval_sha256=digest(approval),recovery_only=True)
    assert stores[0] is None and stores[1].root.parent==roots[1] and stores[2].root.parent==roots[1]


def test_new_readonly_reader_preserves_legacy_registry_pins(tmp_path,cap,monkeypatch):
    path,c,roots,mounts=registry_fixture(tmp_path,cap,monkeypatch);(roots[0]/'segmenter-input-cache').mkdir()
    raw=canonical(c);reader=storage.qualified_cache_reader(path,raw,trusted_capability_sha256=digest(raw),cache_area='segmenter-input-cache')
    assert type(reader) is storage.ReadOnlyStore
    with pytest.raises(ValueError):storage.qualified_cache_reader(path,raw,trusted_capability_sha256=digest(raw),cache_area='unapproved-data')
    assert digest(path.read_bytes())==c['registry_sha256']


def test_readonly_cohort_replay_preserves_exact_descriptors(cap,tmp_path,monkeypatch):
    from retained_segmenter_metadata import metadata
    from src.data import segmenter_cohort_bundle_v1 as bundle,segmenter_geometry_loader_v1 as loader
    m=metadata();rows=m['cache_binding']['records'];assert __import__('src.data.source_inventory_records',fromlist=['content_hash']).content_hash(rows)==loader.DESCRIPTORS
    payload={'purpose-derived.json':b'{}','purpose-inputs.json':canonical(dict(membership={})), 'cohorts.json':b'{}'}
    class Reader:
        def resolve(self,aid,*,receipt_sha256,validate):
            assert receipt_sha256==loader.COMPLETION
            return payload,dict(validation=dict(descriptor_sha256=loader.DESCRIPTORS))
    monkeypatch.setattr(storage,'qualified_cache_reader',lambda *a,**kw:Reader())
    monkeypatch.setattr(bundle,'resolve',lambda *a:(None,deepcopy(rows)))
    session=storage.replay_descriptors(tmp_path/'invented-registry',canonical(cap),trusted_capability_sha256=digest(canonical(cap)))
    assert type(session) is loader.ResolvedInputs and session.records==rows
    assert session.select(rows['optimizer'][0]['study_id'],'optimizer')['protected_role']=='train'
    with pytest.raises(ValueError):session.select(rows['evaluator'][0]['study_id'],'optimizer')

@pytest.mark.parametrize('name',['/tmp/control','../secret.env','src/weights.pt','outputs/prowl/array.npy','src/secret.env'])
def test_source_identity_cannot_open_data_weights_secrets(name,monkeypatch):
    monkeypatch.setattr(dispatcher,'read_control',lambda *a:pytest.fail('Forbidden source accessed'))
    with pytest.raises(ValueError):dispatcher.verify_code(dict(source_pins={name:'a'*64}))


def test_metadata_reader_refuses_fifo_without_blocking(tmp_path):
    import os
    path=tmp_path/'fifo';os.mkfifo(path)
    with pytest.raises(ValueError):dispatcher.read_metadata(path)


def test_cold_cannot_adopt_failed_or_different_producer_before_consumption(tmp_path,monkeypatch):
    from segmenter_duration_fixtures import approval
    from src.training import segmenter_duration_executor_v1 as e
    r,p=request('native_rehearsal');path=tmp_path/'request';path.write_bytes(canonical(r));job=tmp_path/'job';job.mkdir();(job/'producer-dispatch-result.json').write_bytes(canonical(dict(state='consumed_failed',request_sha256=digest(canonical(r)),stage='producer')))
    a=tmp_path/'approval';a.write_bytes(approval(r));cap=r['storage_capability'];raw=canonical(cap)
    s=tmp_path/'storage';s.write_bytes(canonical(dict(kind='exact_duration_storage_v1',author='Quinton Evans',user_instruction='INVENTED TEST ONLY',capability_sha256=digest(raw),budget_bytes=cap['absolute_backup_ceiling'],preserve_old_evidence=True,launch_authorized=False)))
    monkeypatch.setattr(dispatcher,'verify_code',lambda *a:None)
    with pytest.raises(ValueError,match='producer'):dispatcher.dispatch(path,digest(path.read_bytes()),job,approval_path=a,approval_pin=digest(a.read_bytes()),storage_path=s,storage_pin=digest(s.read_bytes()),stage='cold')
    assert not (job/'dispatch-cold-consumed.json').exists()


def test_portable_schema_retains20_and_accepts_approved26_without_deletion():
    from jsonschema import Draft202012Validator
    schema=json.loads((Path(__file__).resolve().parents[1]/'configs/local/roots.schema.json').read_bytes())
    validator=Draft202012Validator({'$ref':'#/$defs/backup','$defs':schema['$defs']})
    base=dict(path='/invented/backup',role='backup',access='selected_controls_and_keepers',failure_domain='internal_backup',minimum_free_bytes=100*storage.GIB,automatic_deletion=False)
    for amount in (20,26):validator.validate(base|dict(cap_bytes=amount*storage.GIB))
    assert list(validator.iter_errors(base|dict(cap_bytes=27*storage.GIB)))
    assert list(validator.iter_errors(base|dict(cap_bytes=26*storage.GIB,automatic_deletion=True)))
