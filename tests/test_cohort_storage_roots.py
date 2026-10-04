import json
from pathlib import Path
import pytest
import yaml
import src.operations.storage_roots as roots
from src.data.manifest_records import digest


def fixture(tmp_path,monkeypatch):
    data=yaml.safe_load((roots.REPO/'configs/local/roots.example.yaml').read_text())
    mount=tmp_path/'external';mount.mkdir();artifact=mount/'artifacts';artifact.mkdir()
    data['failure_domains']['external_primary']['mount_path']=str(mount)
    data['roots']['prowl_artifacts']['path']=str(artifact)
    registry=tmp_path/'roots.yaml';registry.write_text(yaml.safe_dump(data))
    cap=dict(schema_version='1.0.0',approval='D-269',root_alias='prowl_artifacts',area='cohorts',
        operation='publish_and_resolve_cohort',scientific_runs_enabled=False,registry_sha256=digest(registry.read_bytes()),
        volume_uuid='EXAMPLE_EXTERNAL_UUID')
    info=dict(VolumeUUID=cap['volume_uuid'],FilesystemType='apfs',MountPoint=str(mount),WritableVolume=True)
    monkeypatch.setattr(roots,'disk_info',lambda p:info)
    monkeypatch.setattr(Path,'is_mount',lambda p:p==mount)
    return registry,cap,info,artifact


def open_store(registry,cap,**kwargs):
    payload=json.dumps(cap).encode()
    return roots.cohort_store(registry,payload,trusted_capability_sha256=digest(payload),**kwargs)


def test_scoped_area_only_and_registry_unchanged(tmp_path,monkeypatch):
    registry,cap,info,artifact=fixture(tmp_path,monkeypatch);before=registry.read_bytes()
    s=open_store(registry,cap,create=True)
    assert s.root==artifact/'cohorts' and registry.read_bytes()==before
    assert yaml.safe_load(before)['scientific_runs_enabled'] is False


@pytest.mark.parametrize('fault',['uuid','filesystem','readonly','alias','area','registry','overlap'])
def test_wrong_volume_or_capability_refused(tmp_path,monkeypatch,fault):
    registry,cap,info,artifact=fixture(tmp_path,monkeypatch)
    if fault=='uuid':info['VolumeUUID']='wrong'
    if fault=='filesystem':info['FilesystemType']='exfat'
    if fault=='readonly':info['WritableVolume']=False
    if fault=='alias':cap['root_alias']='pants_source'
    if fault=='area':cap['area']='models'
    if fault=='registry':registry.write_text(registry.read_text()+'\n')
    if fault=='overlap':
        data=yaml.safe_load(registry.read_text());data['roots']['pants_source']['acquisition_parent']=str(artifact/'source')
        registry.write_text(yaml.safe_dump(data));cap['registry_sha256']=digest(registry.read_bytes())
    with pytest.raises(ValueError):open_store(registry,cap,create=True)
    assert not (artifact/'cohorts').exists()
