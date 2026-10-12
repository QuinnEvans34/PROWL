#!/usr/bin/env python3
"""Download-only PubMed snapshot: frozen listings, bounded curl, hashes, file-level resume.

No XML parsing, source promotion, selection, database, or embedding work. Legacy sizing tools
remain unchanged. Downloading these files does not by itself produce a current PubMed corpus.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.retrieval.sizing_v1.listings import parse_listing, parse_md5_file, resolve_baseline

MOUNT = Path('/Volumes/PROWL-Data')
UUID = '22750B93-2F3F-499D-87F5-902981BFAB59'
DEST = MOUNT / 'PROWL/scratch/literature/pubmed-2026-20261009'
CAP = 100 * 1024**3
FLOOR = 400_000_000_000
ORIGIN = 'https://ftp.ncbi.nlm.nih.gov/pubmed/'
PATTERN = re.compile(r'pubmed26n(\d{4})\.xml\.gz')


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def make_manifest(packet):
    files, listings = [], {}
    for kind, directory in [('baseline', 'baseline'), ('update', 'updatefiles')]:
        raw = (packet / f'{kind}-listing.html').read_bytes()
        entries = parse_listing(raw)
        listings[kind] = hashlib.sha256(raw).hexdigest()
        if kind == 'baseline':
            resolve_baseline(entries)
        seen = {}
        for name, _, upper in entries:
            if name in seen:
                raise ValueError('Duplicate listing entry')
            seen[name] = upper
            if name.startswith('pubmed26n') and not (
                PATTERN.fullmatch(name) or re.fullmatch(r'pubmed26n\d{4}\.xml\.gz\.md5', name)
                or re.fullmatch(r'pubmed26n\d{4}_stats\.html', name)
            ):
                raise ValueError('Unknown PubMed listing filename')
        data = sorted(name for name in seen if PATTERN.fullmatch(name))
        start = 1 if kind == 'baseline' else 1335
        if not data or [int(PATTERN.fullmatch(n)[1]) for n in data] != list(range(start, start + len(data))):
            raise ValueError('Sequence gap or misplaced file')
        for name in data:
            if name + '.md5' not in seen or not seen[name] or seen[name] > 1024**3:
                raise ValueError('Missing checksum/size or oversized member')
            files.append(dict(name=name, url=ORIGIN + directory + '/' + name, upper_bytes=seen[name]))
    upper = sum(f['upper_bytes'] + 4096 for f in files)
    if upper > CAP - 16 * 1024**2:
        raise ValueError('Frozen listing exceeds acquisition cap')
    return dict(version='pubmed-raw-download-v1', listing_sha256=listings, files=files,
                listed_upper_bytes=upper, cap_bytes=CAP, free_floor_bytes=FLOOR,
                destination=str(DEST), volume_uuid=UUID,
                scope='raw compressed baseline and frozen updates only; not a parsed/current corpus')


class Guard:
    def __init__(self, deadline):
        self.deadline = deadline
        self.device = None

    def check(self, full=False):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('Download time budget reached')
        if not MOUNT.is_mount() or MOUNT.is_symlink():
            raise RuntimeError('Registered drive is not mounted')
        device = MOUNT.stat().st_dev
        if self.device is not None and device != self.device:
            raise RuntimeError('Mounted device changed')
        if full:
            info = plistlib.loads(subprocess.check_output(
                ['/usr/sbin/diskutil', 'info', '-plist', str(MOUNT)], timeout=15))
            if info.get('VolumeUUID') != UUID or info.get('MountPoint') != str(MOUNT) or info.get('FilesystemType') != 'apfs':
                raise RuntimeError('Wrong volume identity')
        if shutil.disk_usage(MOUNT).free < FLOOR + 2 * 1024**3:
            raise RuntimeError('Free-space floor reached')
        self.device = device


def safe_directory(path):
    """Create only beneath the verified mount; refuse symlinks at each component."""
    relative = path.relative_to(MOUNT)
    current = MOUNT
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError('Symlink in destination')
        current.mkdir(exist_ok=True)
        if current.stat().st_dev != MOUNT.stat().st_dev:
            raise ValueError('Destination is on another device')


def download(url, name, limit, root, root_fd, guard):
    if not url.startswith(ORIGIN) or not re.fullmatch(r'pubmed26n\d{4}\.xml\.gz(?:\.md5)?', name):
        raise ValueError('Unexpected download target')
    final = root / name
    partial = name + '.partial'
    if final.is_symlink() or (root / partial).is_symlink():
        raise ValueError('Symlink in file path')
    if final.exists():
        if final.stat().st_size > limit:
            raise ValueError('Existing file exceeds cap')
        return final
    guard.check(full=True)
    fd = os.open(partial, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
    proc = None
    try:
        offset = os.fstat(fd).st_size
        if offset >= limit:
            raise ValueError('Partial exceeds file allowance; retained for inspection')
        os.lseek(fd, 0, os.SEEK_END)
        cmd = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--proto', '=https',
               '--connect-timeout', '30', '--max-time', str(max(1, min(1200, int(guard.deadline-time.monotonic())))),
               '--speed-limit', '1024', '--speed-time', '60', '--max-filesize', str(limit-offset),
               '--user-agent', 'PROWL-capstone-acquisition/1.0']
        if offset:
            cmd += ['--continue-at', str(offset)]
        proc = subprocess.Popen(cmd + [url], stdout=fd, stderr=subprocess.PIPE)
        while proc.poll() is None:
            guard.check()
            if os.fstat(fd).st_size > limit:
                raise ValueError('File size cap exceeded')
            time.sleep(0.25)
        error = proc.stderr.read(8192).decode(errors='replace')
        if proc.returncode:
            raise RuntimeError(f'curl failed ({proc.returncode}): {error.strip()}')
        if os.fstat(fd).st_size > limit:
            raise ValueError('File size cap exceeded')
        os.fsync(fd)
        # Checksum validation occurs before data promotion in the caller.
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            proc.stderr.close()
        os.close(fd)
    return root / partial


def promote(path, name, root, root_fd, guard):
    guard.check(full=True)
    if path.name != name:
        os.link(path.name, name, src_dir_fd=root_fd, dst_dir_fd=root_fd, follow_symlinks=False)
        os.unlink(path.name, dir_fd=root_fd)
        os.fsync(root_fd)


def verify_member(path, expected_md5):
    md5, sha = hashes(path)
    if md5 != expected_md5:
        raise ValueError(f'Publisher checksum mismatch for {path.name}; retained for inspection')
    return sha


def execute(packet, manifest, hours):
    guard = Guard(time.monotonic() + hours * 3600)
    guard.check(full=True)
    safe_directory(DEST)
    root_fd = os.open(DEST, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    lock = os.open('.download.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    completed, byte_count = 0, 0
    started = time.monotonic()
    def status(state, **extra):
        data = dict(state=state, at=now(), verified_files=completed, total_files=len(manifest['files']),
                    verified_bytes=byte_count, elapsed_seconds=round(time.monotonic()-started, 2), **extra)
        temp = packet / 'status.tmp'
        temp.write_bytes(canonical(data))
        os.replace(temp, packet / 'status.json')
        print(json.dumps(data), flush=True)
    try:
        expected = canonical(manifest)
        manifest_path = DEST / 'manifest.json'
        if manifest_path.is_symlink():
            raise ValueError('Symlink manifest')
        if manifest_path.exists():
            if manifest_path.read_bytes() != expected:
                raise ValueError('Existing manifest differs')
        else:
            fd = os.open('manifest.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(expected)
                stream.flush()
                os.fsync(stream.fileno())
        # Unknown payloads would make the cap accounting incomplete. Refuse, never delete.
        allowed = {'manifest.json', '.download.lock', 'receipts.jsonl'}
        for member in manifest['files']:
            allowed.update(member['name'] + suffix for suffix in ('', '.partial', '.md5', '.md5.partial'))
        if any(p.name not in allowed or p.is_symlink() for p in DEST.iterdir()):
            raise ValueError('Unexpected destination member')
        status('running')
        receipt_fd = os.open('receipts.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
        with os.fdopen(receipt_fd, 'a') as receipts:
            for member in manifest['files']:
                name, url, limit = member['name'], member['url'], member['upper_bytes']
                checksum = download(url+'.md5', name+'.md5', 4096, DEST, root_fd, guard)
                expected_md5 = parse_md5_file(checksum.read_bytes(), name)
                promote(checksum, name+'.md5', DEST, root_fd, guard)
                data = download(url, name, limit, DEST, root_fd, guard)
                sha = verify_member(data, expected_md5)
                promote(data, name, DEST, root_fd, guard)
                size = (DEST / name).stat().st_size
                receipts.write(json.dumps(dict(name=name, url=url, bytes=size, md5=expected_md5,
                                               sha256=sha, verified_at=now()))+'\n')
                receipts.flush()
                os.fsync(receipts.fileno())
                completed += 1
                byte_count += size
                if completed <= 3 or completed % 10 == 0:
                    status('running', last_verified=name)
        status('complete', note='Raw downloads verified. Parsing and ordered update replay remain pending.')
    except BaseException as exc:
        status('stopped', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        os.close(lock)
        os.close(root_fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--hours', type=float, default=4)
    args = parser.parse_args()
    if not 0 < args.hours <= 12:
        parser.error('hours must be >0 and <=12')
    manifest = make_manifest(args.packet)
    path = args.packet / 'manifest.json'
    if path.exists() and path.read_bytes() != canonical(manifest):
        raise ValueError('Frozen manifest changed')
    if not path.exists():
        path.write_bytes(canonical(manifest))
    if args.execute:
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('Requested stop')))
        execute(args.packet, manifest, args.hours)
    else:
        print(json.dumps({k: v for k, v in manifest.items() if k != 'files'}, indent=2))
        print(f"Files: {len(manifest['files'])}")


if __name__ == '__main__':
    main()
