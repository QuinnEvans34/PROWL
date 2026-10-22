"""Human-terminal setup of a small encrypted evaluation image and independent backup.

Passwords are handled directly by macOS hdiutil, never read by Python or put in arguments.
Only a closed, content-free status receipt returns to the repository. No model or evaluation.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

import yaml

ROOT = Path(__file__).resolve().parents[2]
SIZE = 128 * 1024**2
FLOOR = 100 * 1024**3


def native(args):
    # stdin/stderr stay on the user's ordinary Terminal. Password prompts never
    # pass through agent tools, Python input/getpass, shell arguments or a logfile.
    return subprocess.run(args, stdout=subprocess.PIPE, check=True).stdout


def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def copy_verified(source, destination):
    """Exclusive copy, durable close and exact read-back; never overwrite a keeper."""
    with source.open('rb') as incoming, destination.open('xb') as outgoing:
        os.chmod(destination, 0o600)
        shutil.copyfileobj(incoming, outgoing)
        outgoing.flush(); os.fsync(outgoing.fileno())
    if digest_file(source) != digest_file(destination):
        raise ValueError('Copy verification failed')
    return digest_file(destination)


def checked_roots(root):
    registry = yaml.safe_load((root/'configs/local/roots.yaml').read_text())
    dirs = []; info = []
    for alias in ('prowl_artifacts','prowl_backup'):
        entry = registry['roots'][alias]; path = Path(entry['path'])
        domain = registry['failure_domains'][entry['failure_domain']]
        if not path.is_dir() or path.resolve()!=path.absolute():
            raise ValueError('Registered root unavailable')
        volume=Path(domain['mount_path'])
        if not volume.is_dir() or path.stat().st_dev!=volume.stat().st_dev:
            raise ValueError('Root is not on its registered mounted volume')
        meta = plistlib.loads(native(['/usr/sbin/diskutil','info','-plist',str(volume)]))
        if meta['VolumeUUID'].upper()!=domain['volume_uuid'].upper():
            raise ValueError('Registered volume changed')
        if shutil.disk_usage(path).free-2*SIZE < max(FLOOR,entry.get('minimum_free_bytes',0)):
            raise ValueError('Free-space floor would be crossed')
        dirs.append(path); info.append(meta)
    if (info[0]['Internal'] is not False or info[1]['Internal'] is not True
            or dirs[0].stat().st_dev==dirs[1].stat().st_dev):
        raise ValueError('Independent external/internal devices required')
    used = int(native(['/usr/bin/du','-sk',str(dirs[1])]).split()[0])*1024
    if used+2*SIZE > registry['roots']['prowl_backup']['cap_bytes']:
        raise ValueError('Shared backup allocation would be crossed')
    return dirs


def relocate_verified_original(source, expected, identity):
    """Relocate only the still-identical source, after caller verified both images."""
    current=source.lstat()
    if (source.is_symlink() or (current.st_dev,current.st_ino)!=identity
            or digest_file(source)!=expected):
        raise ValueError('Original changed; both copies retained and original preserved')
    source.unlink()


def setup(root=ROOT):
    if not sys.stdin.isatty():
        raise ValueError('Run in the ordinary user Terminal, not an agent terminal')
    source=root/'QUESTIONS.md'
    if (source.is_symlink() or not source.is_file() or source.stat().st_size>2*1024**2
            or source.stat().st_size==0):
        raise ValueError('Expected bounded original reviewed draft')
    # A tracked draft needs separate Git-history remediation; never remove it here.
    tracked=subprocess.run(['git','ls-files','--error-unmatch','QUESTIONS.md'],cwd=root,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if tracked.returncode!=1:
        raise ValueError('Draft is tracked or Git check failed; preserve it and resolve separately')
    primary_root,backup_root=checked_roots(root)
    token=uuid4().hex
    primary_dir=primary_root/('literature-private-'+token)
    backup_dir=backup_root/('literature-private-'+token)
    primary_dir.mkdir(mode=0o700); backup_dir.mkdir(mode=0o700)
    image=primary_dir/'evaluation.dmg'; backup=backup_dir/'evaluation.dmg'
    # macOS refuses this APFS image's mountpoint on the external volume.
    # Mount under the registered internal owner-only directory instead.
    mount=backup_dir/'mount'; mount.mkdir(mode=0o700)
    status=dict(version='prowl-private-storage-setup-v1',state='started',
        recorded_at=datetime.now(timezone.utc).isoformat(),capacity_bytes=SIZE,
        different_registered_devices=True,encrypted_primary_verified=False,
        encrypted_backup_verified=False,backup_restore_verified=False,
        images_detached=False,original_relocated=False,ready_for_evaluation=False)
    receipt_dir=root/'outputs/prowl/independent-preparation-20261022'/('storage-'+token)
    receipt_dir.mkdir(mode=0o700)
    receipt=receipt_dir/'status.json'
    def save():
        receipt.write_text(json.dumps(status,indent=2)+'\n');os.chmod(receipt,0o600)
    mounted=False; stage='create_encrypted_image'
    save()
    try:
        print('macOS will ask you to create an encryption password. Keep it in your password manager.',flush=True)
        native(['/usr/bin/hdiutil','create','-size','128m','-fs','APFS','-volname',
                'PROWL Private Evaluation','-encryption','AES-256',str(image)])
        os.chmod(image,0o600)
        encrypted=plistlib.loads(native(['/usr/bin/hdiutil','isencrypted','-plist',str(image)]))
        if encrypted.get('encrypted') is not True:raise ValueError('Encryption not verified')
        status['encrypted_primary_verified']=True
        stage='copy_original_into_image'
        print('Enter the same password to open the new image.',flush=True)
        native(['/usr/bin/hdiutil','attach','-nobrowse','-mountpoint',str(mount),str(image)])
        mounted=True
        info=source.lstat(); identity=(info.st_dev,info.st_ino)
        original_hash=copy_verified(source,mount/'reviewed-draft.md')
        (mount/'README.txt').write_text('Original reviewed draft is preserved as reviewed-draft.md.\n'
            'Keep transcription, labels and evaluation outputs here. This image is not yet a frozen test set.\n'
            'Eject before backing it up. Changes made after setup require a fresh verified encrypted backup.\n')
        os.chmod(mount/'README.txt',0o600)
        native(['/usr/bin/hdiutil','detach',str(mount)]);mounted=False
        stage='copy_encrypted_backup'
        image_hash=copy_verified(image,backup)
        encrypted=plistlib.loads(native(['/usr/bin/hdiutil','isencrypted','-plist',str(backup)]))
        if encrypted.get('encrypted') is not True:raise ValueError('Backup encryption not verified')
        status['encrypted_backup_verified']=True
        stage='restore_check_backup'
        mount.mkdir(mode=0o700,exist_ok=True)
        print('Enter the same password once more to verify the backup can be opened.',flush=True)
        native(['/usr/bin/hdiutil','attach','-readonly','-nobrowse','-mountpoint',str(mount),str(backup)])
        mounted=True
        if digest_file(mount/'reviewed-draft.md')!=original_hash:
            raise ValueError('Backup original read-back failed')
        native(['/usr/bin/hdiutil','detach',str(mount)]);mounted=False
        if digest_file(backup)!=image_hash or digest_file(image)!=image_hash:
            raise ValueError('Detached image identity changed')
        status.update(backup_restore_verified=True,images_detached=True,
            encrypted_image_sha256=image_hash,independent_encrypted_backup_sha256=image_hash,
            original_draft_sha256=original_hash)
        stage='relocate_verified_original'
        relocate_verified_original(source,original_hash,identity)
        status.update(original_relocated=True,state='workspace_ready_not_evaluation_freeze')
        save()
        print('\nVerified encrypted primary and independent backup; both are ejected. Original relocated without changing its bytes.')
        print('Primary:',image,'\nBackup:',backup)
        print('Save these locations privately. Future edits require a fresh backup before evaluation.')
    except BaseException:
        status.update(state='setup_incomplete',failed_stage=stage)
        raise
    finally:
        if mounted or os.path.ismount(mount):
            try:
                native(['/usr/bin/hdiutil','detach',str(mount)])
                status['images_detached']=True
            except Exception:
                status['images_detached']=False
                print('An owned evaluation image may still be mounted. Eject it in Finder; do not force detach.')
        save()


if __name__=='__main__':
    try:
        import fcntl
        lock_path=ROOT/'outputs/prowl/independent-preparation-20261022/storage-setup.lock'
        with lock_path.open('a') as lock:
            os.chmod(lock_path,0o600)
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            setup()
    except Exception:
        print('Setup did not complete. Existing files and partial images were preserved; do not retry blindly.')
        raise SystemExit(1) from None
