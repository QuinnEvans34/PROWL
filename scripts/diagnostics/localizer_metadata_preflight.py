"""One bounded metadata-only PanTS inventory; not a production writer or source activation."""
import argparse
import json
from pathlib import Path
import shutil
import signal
import time
from uuid import uuid4

import yaml

from scripts.diagnostics.storage_setup import disk_info
from scripts.diagnostics.followup_voxel_audit import Package
from src.data.manifest_records import canonical, digest
from src.data.protected_identity import accepted_pants_members, validate_role_assignments
from src.data.source_metadata_inventory import MetadataInventory

REPO=Path(__file__).resolve().parents[2]
SCOPE=REPO/'docs/capstone/data/SOURCE-VERIFICATION-SCOPE-2026-09-28.json'


def prepare():
    scope=json.loads(SCOPE.read_bytes())
    for ref in scope['input_pins']:
        path=REPO/ref['path']
        if not path.is_relative_to(REPO) or path.resolve(strict=True)!=path:
            raise ValueError('Unsafe control path')
        payload=path.read_bytes()
        if len(payload)!=ref['bytes'] or digest(payload)!=ref['sha256']:
            raise ValueError('Retained control pin changed: '+ref['path'])
    roles={};assignments=[]
    for role,filename in [('train','train.txt'),('validation','val.txt'),('test','test.txt')]:
        identities=accepted_pants_members((REPO/'outputs/splits'/filename).read_bytes(),role)
        assignments.extend((i,role) for i in identities)
        roles.update({i.study_id.removeprefix('pants:study:'):role for i in identities})
    if validate_role_assignments(assignments)!=scope['original_membership_counts']:
        raise ValueError('Protected membership changed')
    registry_bytes=(REPO/'configs/local/roots.yaml').read_bytes();registry=yaml.safe_load(registry_bytes)
    primary=registry['failure_domains']['external_primary'];mount=Path(primary['mount_path'])
    acquisition=Path(registry['roots']['pants_source']['acquisition_parent'])
    if not acquisition.is_relative_to(mount):raise ValueError('Source root outside registered mount')
    inv=json.loads((REPO/'outputs/prowl/inventory-2026-09-27/full-v4.json').read_bytes())
    images=next(s for s in inv['sources'] if s['source']=='pants-images')
    labels=next(s for s in inv['sources'] if s['source']=='pants-labels')
    roots=[Path(p) for p in images['roots']+labels['roots']]
    parents={p.parent for p in roots}
    if len(parents)!=1:raise ValueError('Expected one retained extraction parent')
    root=parents.pop()
    if root.parent!=acquisition:raise ValueError('Retained extraction parent not registered')
    expected_destinations={r['destination'] for r in scope['retained_extraction_receipts']}
    if len(roots)!=10 or {p.name for p in roots}!=expected_destinations:
        raise ValueError('Source directories differ from extraction receipts')
    shards={}
    for ref in scope['training_archive_controls']:
        name=ref['name'].removesuffix('.tar.gz');start,end=map(int,name.rsplit('_',2)[-2:])
        shards[name]=[f'PanTS_{n:08}' for n in range(start,end+1)]
    limits=scope['proposed_metadata_preflight']
    return dict(scope=scope,registry=registry,mount=mount,primary=primary,root=root,shards=shards,
                labels=Path(labels['roots'][0]).name,roles=roles,limits=limits,
                registry_sha256=digest(registry_bytes),scope_sha256=digest(SCOPE.read_bytes()))


def run():
    started=time.monotonic();prepared=prepare();mount=prepared['mount'];primary=prepared['primary']
    device=None
    def check_mount():
        nonlocal device
        if mount.is_symlink() or not mount.is_mount() or mount.resolve(strict=True)!=mount:
            raise ValueError('Registered mount absent or noncanonical')
        info=disk_info(mount)
        if info.get('VolumeUUID')!=primary['volume_uuid'] or info.get('FilesystemType')!='apfs':
            raise ValueError('Registered volume identity mismatch')
        current=mount.stat().st_dev
        if device is not None and current!=device:raise ValueError('Mount device changed')
        device=current
    check_mount()
    root=prepared['root']
    if root.resolve(strict=True)!=root:raise ValueError('Source path changed or contains symlink')
    output_parent=REPO/'outputs/prowl'
    if shutil.disk_usage(output_parent).free<100*1024**3:raise ValueError('Internal free-space floor')
    package=Package(output_parent/('localizer-metadata-'+str(uuid4())),max_bytes=64*1024**2)
    print('Evidence package: '+str(package.path),flush=True)
    limits=prepared['limits']
    def timeout(*_):raise TimeoutError('Metadata preflight wall-time ceiling')
    previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(limits['maximum_seconds'])
    try:
        package.write('request.json',dict(scope_sha256=prepared['scope_sha256'],registry_sha256=prepared['registry_sha256'],
            diagnostic_root=str(root),root_activation=False,limits=limits,
            scientific_runs_enabled=prepared['registry']['scientific_runs_enabled'],
            original_membership_counts=prepared['scope']['original_membership_counts']))
        code=[Path(__file__),REPO/'src/data/source_metadata_inventory.py',REPO/'scripts/diagnostics/storage_setup.py',
              REPO/'scripts/diagnostics/followup_voxel_audit.py',REPO/'src/data/protected_identity.py']
        package.write('implementation.json',{p.relative_to(REPO).as_posix():dict(sha256=digest(p.read_bytes()),text=p.read_text()) for p in code})
        inventory=MetadataInventory(root,check_mount=check_mount,seconds=limits['maximum_seconds'],
            max_entries=limits['maximum_directory_entries'],max_memory=limits['maximum_resident_bytes'],
            max_output=limits['maximum_output_bytes']-1024**2)
        payload,summary=inventory.run(prepared['shards'],prepared['labels'],prepared['roles'])
        package.write('files.json',[json.loads(line) for line in payload.splitlines()])
        package.write('summary.json',summary)
        check_mount()
        package.write('verification.json',dict(status='metadata_observation_complete',files=package.hashes.copy(),
            elapsed_seconds=time.monotonic()-started,source_content_read=False,source_modified=False,
            eligibility_granted=0,training_started=False))
        for name,sha in package.hashes.items():
            if digest((package.path/name).read_bytes())!=sha:raise ValueError('Evidence readback mismatch')
        print(json.dumps(summary,sort_keys=True),flush=True)
        print('Evidence readback passed',flush=True)
    except Exception as exc:
        package.write('failure.json',dict(status='failed_not_complete',error_type=type(exc).__name__,message=str(exc)))
        raise
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run:parser.error('Explicit --run required')
    run()
