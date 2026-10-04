"""D-323 exact cache artifact capability on unchanged registered APFS storage."""
import json,os
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
from scripts.diagnostics.storage_setup import disk_info
from src.data.manifest_records import digest
from src.data.source_inventory_records import require
from src.operations.artifact_store import directory
from src.operations.localizer_run_storage import CappedStore,tree_bytes

REPO=Path(__file__).resolve().parents[2]


def cache_store(registry_path,capability,*,trusted_capability_sha256,artifact_id,create=False):
    require(digest(capability)==trusted_capability_sha256,'Unreviewed cache capability')
    c=json.loads(capability)
    require(set(c)=={'schema_version','approval','operation','area','artifact_id','max_new_bytes','registry_sha256','volume_uuid','source_writes','model_updates_allowed'},'Cache capability fields differ')
    require(c['schema_version']=='1.0.0' and c['approval']=='D-323' and c['operation']=='qualified_segmenter_cache_build_resolve' and c['area']=='segmenter-input-cache' and c['artifact_id']==artifact_id and c['max_new_bytes']==512*1024**2 and c['source_writes'] is False and c['model_updates_allowed'] is False,'Unsupported cache capability')
    registry_path=Path(registry_path);require(registry_path.resolve(strict=True)==registry_path,'Unsafe registry')
    raw=registry_path.read_bytes();require(digest(raw)==c['registry_sha256'],'Registry changed')
    reg=yaml.safe_load(raw);Draft202012Validator(json.loads((REPO/'configs/local/roots.schema.json').read_bytes())).validate(reg)
    r=reg['roots']['prowl_artifacts'];domain=reg['failure_domains'][r['failure_domain']];root=Path(r['path'])
    require(r['role']=='artifact' and r['access']=='setup_only' and domain['volume_uuid']==c['volume_uuid'],'Wrong storage role/domain')
    def guard():
        require(digest(registry_path.read_bytes())==c['registry_sha256'],'Registry changed during cache operation')
        mount=Path(domain['mount_path']);info=disk_info(mount)
        require(mount.is_mount() and info.get('FilesystemType')=='apfs' and info.get('VolumeUUID')==c['volume_uuid'] and info.get('MountPoint')==str(mount) and info.get('WritableVolume') is True,'Unavailable/wrong APFS cache volume')
        fd=directory(root);os.close(fd);require(root.stat().st_dev==mount.stat().st_dev,'Cache root on unexpected device')
    guard();path=root/c['area']
    if create:
        fd=directory(root)
        try:
            try:os.mkdir(c['area'],0o700,dir_fd=fd);os.fsync(fd)
            except FileExistsError:pass
        finally:os.close(fd)
    fd=directory(path);os.close(fd)
    baseline=tree_bytes(path);total=os.statvfs(root).f_blocks*os.statvfs(root).f_frsize
    store=CappedStore(path,check_root=guard,max_bytes=512*1024**2,minimum_free_bytes=max(100*1024**3,total//10),quota_root=path,quota_bytes=baseline+c['max_new_bytes'])
    return ExactCacheStore(store,artifact_id)


class ExactCacheStore:
    def __init__(self,store,artifact_id):self.store=store;self.artifact_id=artifact_id;self.root=store.root
    def publish(self,artifact_id,**kwargs):
        require(artifact_id==self.artifact_id,'Cache capability exact artifact only');return self.store.publish(artifact_id,**kwargs)
    def resolve(self,artifact_id,**kwargs):
        require(artifact_id==self.artifact_id,'Cache capability exact artifact only');return self.store.resolve(artifact_id,**kwargs)
