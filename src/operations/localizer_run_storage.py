"""Scoped checkpoint/backup roots; unchanged setup registry and no source activation."""
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


def mounted_apfs(info,mount,table):
    # macOS firmlinks can make pathlib's parent-device heuristic miss the Data mount.
    node=info.get('DeviceNode')
    return isinstance(node,str) and any(line.startswith(f'{node} on {mount} (apfs,') for line in table.splitlines())


def tree_bytes(root):
    """Bounded no-follow inventory includes failed attempts, controls and all backup areas."""
    total=0;count=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            info=(Path(parent)/name).lstat();count+=1
            require(count<=100000 and not stat.S_ISLNK(info.st_mode),'Unsafe or excessive capacity inventory')
            require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),'Unexpected capacity inventory entry')
            if stat.S_ISREG(info.st_mode):total+=info.st_size
    return total


class CappedStore(ArtifactStore):
    def __init__(self,*args,quota_root,quota_bytes,**kwargs):
        super().__init__(*args,**kwargs);self.quota_root=quota_root;self.quota_bytes=quota_bytes
    @contextmanager
    def writer(self,fd):
        quota_fd=directory(self.quota_root)
        lock=os.open('.capacity.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=quota_fd)
        try:
            require(stat.S_ISREG(os.fstat(lock).st_mode) and os.fstat(lock).st_nlink==1,'Unsafe quota lock')
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with super().writer(fd):yield
        finally:os.close(lock);os.close(quota_fd)
    def space(self,fd,remaining):
        super().space(fd,remaining)
        require(tree_bytes(self.quota_root)+remaining<=self.quota_bytes,'Scoped capacity quota exceeded')


def run_stores(registry_path,capability,*,trusted_capability_sha256,create=False,recovery_only=False):
    require(digest(capability)==trusted_capability_sha256,'Unreviewed run capability')
    cap=json.loads(capability)
    require(cap['schema_version']=='1.0.0' and cap['approval']=='D-273' and
        cap['operation']=='localizer_bridge_checkpoint_backup_verification' and
        cap['primary_area']=='localizer-runs' and cap['backup_area']=='localizer-keepers' and
        cap['restore_area']=='localizer-restores' and cap['max_new_bytes_per_domain']==1024**3 and
        cap['real_optimizer_updates_allowed'] is False,'Unsupported run capability')
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
        stores.append(CappedStore(path,check_root=lambda i=i:check(i),max_bytes=96*1024**2,
            minimum_free_bytes=max(100*1024**3,total//10) if i==0 else backup['minimum_free_bytes'],
            quota_root=path if i==0 else roots[1],
            quota_bytes=baseline[0]+1024**3 if i==0 else min(backup['cap_bytes'],baseline[1]+1024**3)))
    return tuple(stores)
