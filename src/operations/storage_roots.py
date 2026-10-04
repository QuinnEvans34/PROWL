"""Narrow cohort-artifact capability over the unchanged setup registry.

The hash-pinned capability is additive approval for one area, not global scientific-run
activation. Production checks are macOS/APFS qualified. No root fallback or source writes.
"""
import json
import os
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
from scripts.diagnostics.storage_setup import disk_info
from src.data.manifest_records import digest
from src.data.source_inventory_records import require
from src.operations.artifact_store import ArtifactStore, directory

REPO=Path(__file__).resolve().parents[2]


def cohort_store(registry_path,capability,*,trusted_capability_sha256,create=False):
    require(digest(capability)==trusted_capability_sha256, 'Unreviewed storage capability')
    cap=json.loads(capability)
    require(cap['schema_version']=='1.0.0' and cap['approval']=='D-269' and
        cap['root_alias']=='prowl_artifacts' and cap['area']=='cohorts' and
        cap['operation']=='publish_and_resolve_cohort' and cap['scientific_runs_enabled'] is False,
        'Unsupported storage capability')
    registry_path=Path(registry_path)
    require(registry_path.resolve(strict=True)==registry_path, 'Unsafe registry path')
    registry_bytes=registry_path.read_bytes()
    require(digest(registry_bytes)==cap['registry_sha256'], 'Registry changed')
    registry=yaml.safe_load(registry_bytes)
    schema=json.loads((REPO/'configs/local/roots.schema.json').read_bytes())
    Draft202012Validator(schema).validate(registry)
    root=registry['roots']['prowl_artifacts'];domain=registry['failure_domains'][root['failure_domain']]
    path=Path(root['path']);mount=Path(domain['mount_path'])
    require(root['role']=='artifact' and root['access']=='setup_only', 'Unexpected root role/access')
    require(path.is_relative_to(mount) and path!=mount and domain['volume_uuid']==cap['volume_uuid'], 'Root/volume capability mismatch')
    for alias,other in registry['roots'].items():
        if alias=='prowl_artifacts':continue
        candidate=other.get('path') or other.get('acquisition_parent')
        if candidate:
            other_path=Path(candidate)
            require(not path.is_relative_to(other_path) and not other_path.is_relative_to(path), 'Overlapping root roles')
    def preflight():
        require(digest(registry_path.read_bytes())==cap['registry_sha256'], 'Registry changed since preflight')
        info=disk_info(mount)
        require(info.get('VolumeUUID')==domain['volume_uuid'] and info.get('FilesystemType')=='apfs'
            and info.get('MountPoint')==str(mount) and info.get('WritableVolume') is True,
            'Wrong or unavailable writable APFS volume')
        require(mount.is_mount() and path.stat().st_dev==mount.stat().st_dev, 'Artifact root is not on registered mount')
        fd=directory(path);os.close(fd)
    preflight()
    if create:
        fd=directory(path)
        try:
            try:os.mkdir('cohorts',0o700,dir_fd=fd);os.fsync(fd)
            except FileExistsError:pass
        finally:os.close(fd)
    area=path/'cohorts';fd=directory(area);os.close(fd)
    total=os.statvfs(path).f_blocks*os.statvfs(path).f_frsize
    return ArtifactStore(area,check_root=preflight,max_bytes=96*1024**2,
                         minimum_free_bytes=max(100*1024**3,total//10))
