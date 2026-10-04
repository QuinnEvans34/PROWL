"""V5 stores never create or enlarge an allowance without exact storage approval."""
"""D-333 scoped training qualification checkpoint/keeper roots; registry stays unchanged."""
from contextlib import contextmanager
import json
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import yaml
from jsonschema import Draft202012Validator
from scripts.diagnostics.storage_setup import disk_info
from src.data.manifest_records import digest
from src.data.source_inventory_records import require
from src.operations.artifact_store import ArtifactStore,directory

REPO=Path(__file__).resolve().parents[2]


from src.operations.localizer_run_storage import CappedStore,tree_bytes,mounted_apfs



def validate_storage_authority(capability,approval,trusted_pin):
    require(isinstance(approval,bytes) and isinstance(trusted_pin,str) and digest(approval)==trusted_pin,'Missing exact storage-capacity approval; proposal is inactive')
    a=json.loads(approval);c=json.loads(capability)
    require(set(a)=={'kind','decision','author','user_instruction','capability_sha256','phase','delete_old_evidence','real_launch_authorized'} and a['kind']=='exact_segmenter_v5_storage' and isinstance(a['decision'],str) and a['decision'].startswith('D-') and a['decision']!='D-333' and a['author']=='Quinton Evans' and isinstance(a['user_instruction'],str) and bool(a['user_instruction'].strip()) and a['capability_sha256']==digest(capability) and a['phase']==c['phase'] and a['delete_old_evidence'] is False and a['real_launch_authorized'] is False,'Storage approval differs; capacity approval never grants real training')
    return a

def validate_capability(capability):
    cap=json.loads(capability)
    require(set(cap)=={'schema_version','approval','operation','primary_area','backup_area','restore_area','max_new_bytes_per_domain','real_optimizer_updates_allowed','phase','launch_approval_required','registry_sha256','primary_volume_uuid','backup_volume_uuid','backup_baseline_bytes','absolute_backup_ceiling','primary_ceiling'},'Capability inventory differs')
    phase=cap['phase'];require(phase in ('rehearsal','real'),'Unknown storage phase')
    suffix='rehearsal' if phase=='rehearsal' else 'runs'
    require(cap['schema_version']=='1.0.0' and cap['approval']=='D-333' and
        cap['operation']=='segmenter_v5_executor_preparation' and
        cap['primary_area']=='segmenter-v5-'+suffix and
        cap['backup_area']=='segmenter-v5-'+suffix+'-keepers' and
        cap['restore_area']=='segmenter-v5-'+suffix+'-restores' and cap['max_new_bytes_per_domain']==2*1024**3 and
        cap['real_optimizer_updates_allowed'] is (phase=='real') and cap['launch_approval_required'] is (phase=='real'),
        'Unsupported v5 storage capability; separate storage and real launch approvals required')
    require(all(type(cap[k]) is int and cap[k]>0 for k in ('backup_baseline_bytes','absolute_backup_ceiling','primary_ceiling')) and cap['primary_ceiling']==2*1024**3 and cap['absolute_backup_ceiling']==cap['backup_baseline_bytes']+2*1024**3 and cap['absolute_backup_ceiling']<=20*1024**3,'Wrong fixed absolute v5 capacity')
    return cap

def v5_stores(registry_path,capability,*,trusted_capability_sha256,storage_approval=None,trusted_storage_approval_sha256=None,create=False,recovery_only=False):
    require(digest(capability)==trusted_capability_sha256,'Unreviewed run capability')
    cap=json.loads(capability)
    validate_storage_authority(capability,storage_approval,trusted_storage_approval_sha256)
    validate_capability(capability)
    registry_path=Path(registry_path);require(registry_path.resolve(strict=True)==registry_path,'Unsafe registry')
    raw=registry_path.read_bytes();require(digest(raw)==cap['registry_sha256'],'Registry changed')
    reg=yaml.safe_load(raw);Draft202012Validator(json.loads((REPO/'configs/local/roots.schema.json').read_bytes())).validate(reg)
    primary=reg['roots']['prowl_artifacts'];backup=reg['roots']['prowl_backup']
    require(primary['role']=='artifact' and primary['access']=='setup_only' and backup['role']=='backup' and
            backup['access']=='selected_controls_and_keepers','Wrong root roles')
    roots=[Path(primary['path']),Path(backup['path'])]
    domains=[reg['failure_domains'][r['failure_domain']] for r in (primary,backup)]
    require(domains[0]['volume_uuid']==cap['primary_volume_uuid'] and domains[1]['volume_uuid']==cap['backup_volume_uuid'] and
            domains[0]['volume_uuid']!=domains[1]['volume_uuid'],'Failure domains differ from capability')
    for root in roots[1:] if recovery_only else roots:
        fd=directory(root);os.close(fd)
    if not recovery_only:require(roots[0].stat().st_dev!=roots[1].stat().st_dev,'Backup shares primary device')
    baseline=[tree_bytes(roots[0]/cap['primary_area']) if not recovery_only and (roots[0]/cap['primary_area']).exists() else 0,tree_bytes(roots[1])]
    def check(index):
        require(digest(registry_path.read_bytes())==cap['registry_sha256'],'Registry changed during run')
        root=roots[index];domain=domains[index];mount=Path(domain['mount_path']);info=disk_info(mount)
        mounted=mount.is_mount()
        if not mounted and index==1 and info.get('Internal') is True:
            mounted=mounted_apfs(info,mount,subprocess.check_output(['/sbin/mount'],text=True,timeout=5))
        require(mounted and info.get('VolumeUUID')==domain['volume_uuid'] and
                info.get('FilesystemType')=='apfs' and info.get('MountPoint')==str(mount) and
                info.get('WritableVolume') is True,'Wrong or unavailable APFS failure domain')
        fd=directory(root);os.close(fd)
        require(root.stat().st_dev==mount.stat().st_dev,'Root on unexpected device')
    # Independent readers validate only their own medium, so restore works with primary absent.
    for i in ([1] if recovery_only else [0,1]):check(i)
    require(cap['absolute_backup_ceiling']<=backup['cap_bytes'] and cap['backup_baseline_bytes']<=baseline[1]<=cap['absolute_backup_ceiling'],'Reviewed absolute backup ceiling exceeded')
    stores=[]
    for i,area in ((0,cap['primary_area']),(1,cap['backup_area']),(1,cap['restore_area'])):
        if recovery_only and i==0:
            stores.append(None);continue
        if create:
            fd=directory(roots[i])
            try:
                try:os.mkdir(area,0o700,dir_fd=fd);os.fsync(fd)
                except FileExistsError:pass
            finally:os.close(fd)
        path=roots[i]/area;fd=directory(path);os.close(fd)
        total=os.statvfs(roots[i]).f_blocks*os.statvfs(roots[i]).f_frsize
        stores.append(CappedStore(path,check_root=lambda i=i:check(i),max_bytes=192*1024**2,
            minimum_free_bytes=max(100*1024**3,total//10) if i==0 else backup['minimum_free_bytes'],
            quota_root=path if i==0 else roots[1],
            quota_bytes=cap['primary_ceiling'] if i==0 else cap['absolute_backup_ceiling']))
    return tuple(stores)
