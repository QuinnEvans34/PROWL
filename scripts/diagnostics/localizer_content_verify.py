"""Pinned ten-file read-only hash check. No decoding, qualification or source activation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
from uuid import uuid4

import yaml

from scripts.diagnostics.followup_voxel_audit import Package
from scripts.diagnostics.storage_setup import disk_info

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / 'docs/capstone/data/LOCALIZER-CONTENT-VERIFICATION-JOB-2026-09-28.json'
SPEC_SHA = 'd1707a08c36a29980302294cba66b878ec3a819004605e2422def872a2acc1f8'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def peak_rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def check_memory(limit):
    if peak_rss() > limit:
        raise ValueError('Process RSS ceiling exceeded')


def load_spec(path=SPEC, expected_sha=SPEC_SHA):
    payload = path.read_bytes()
    if digest(payload) != expected_sha:
        raise ValueError('Job specification pin changed')
    spec = json.loads(payload)
    for ref in spec['inputs']:
        p = REPO / ref['path']
        if not p.is_relative_to(REPO) or p.resolve(strict=True) != p:
            raise ValueError('Unsafe control path')
        if digest(p.read_bytes()) != ref['sha256']:
            raise ValueError('Retained control changed: ' + ref['path'])
    return spec


def signature(info):
    return dict(device=info.st_dev, inode=info.st_ino, mtime_ns=info.st_mtime_ns,
                ctime_ns=info.st_ctime_ns, bytes=info.st_size)


def open_relative(root, uri):
    """Walk every component with no-follow descriptors, including root ancestors."""
    rel = Path(uri)
    if rel.is_absolute() or not rel.parts or any(p in ('.', '..') for p in uri.split('/')):
        raise ValueError('Unsafe source URI')
    if not root.is_absolute():
        raise ValueError('Root must be absolute')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in root.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        device = os.fstat(directory).st_dev
        for part in rel.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
            if os.fstat(directory).st_dev != device:
                raise ValueError('Source device changed')
        fd = os.open(rel.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_dev != device:
            os.close(fd)
            raise ValueError('Source is not a same-device regular file')
        return fd
    finally:
        os.close(directory)


def hash_file(root, row, *, chunk_bytes, remaining_bytes, memory_limit, tick=lambda: None):
    if row['protected_role'] != 'train' or row['kind'] not in ('ct', 'pancreas'):
        raise ValueError('Wrong role or artifact kind')
    if row['bytes'] > remaining_bytes:
        raise ValueError('Source read cap exceeded')
    expected = dict(row['observation'], bytes=row['bytes'])
    fd = open_relative(root, row['uri'])
    start = time.monotonic()
    try:
        if signature(os.fstat(fd)) != expected:
            raise ValueError('Source stat identity changed')
        sha = hashlib.sha256(); count = 0
        while count < row['bytes']:
            tick(); check_memory(memory_limit)
            data = os.read(fd, min(chunk_bytes, row['bytes'] - count))
            if not data:
                raise ValueError('Truncated source')
            count += len(data); sha.update(data)
        tick()
        if signature(os.fstat(fd)) != expected:
            raise ValueError('Source mutated during read')
        # Reopen the path through no-follow ancestors to reject rename/replacement.
        other = open_relative(root, row['uri'])
        try:
            if signature(os.fstat(other)) != expected:
                raise ValueError('Source path replaced')
        finally:
            os.close(other)
        if sha.hexdigest() != row['expected_content_sha256']:
            raise ValueError('Source content hash changed')
        check_memory(memory_limit)
        return dict(uri=row['uri'], sha256=sha.hexdigest(), bytes=count,
                    elapsed_seconds=time.monotonic()-start, peak_rss_bytes=peak_rss())
    finally:
        os.close(fd)


def supervised_hash(request, timeout, memory_limit):
    """Bound worker wall time and monitor RSS; no third-party process dependency."""
    command = [sys.executable, '-m', 'scripts.diagnostics.localizer_content_verify', '--worker']
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=REPO)
    started = time.monotonic()
    payload = json.dumps(request).encode()
    try:
        while True:
            if time.monotonic()-started >= timeout:
                raise TimeoutError('File/overall deadline exceeded')
            try:
                out, err = proc.communicate(payload, timeout=min(.1, timeout-(time.monotonic()-started)))
                break
            except subprocess.TimeoutExpired:
                payload = None
                if time.monotonic()-started >= timeout:
                    raise TimeoutError('File/overall deadline exceeded')
                if proc.poll() is None:
                    observed = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(proc.pid)],
                                              capture_output=True, text=True, timeout=1)
                    if observed.stdout.strip() and int(observed.stdout.strip())*1024 > memory_limit:
                        raise ValueError('Worker RSS ceiling exceeded')
        if proc.returncode:
            raise ValueError('Worker failed: ' + err.decode(errors='replace')[-2000:])
        if len(out) > 8192:
            raise ValueError('Worker result too large')
        result = json.loads(out)
        if result['peak_rss_bytes'] > memory_limit:
            raise ValueError('Worker peak RSS ceiling exceeded')
        return result
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.communicate()


def execute(spec, root, package, check_mount, deadline, run_worker=supervised_hash):
    limits = spec['limits']; used = 0; results = []
    for index, row in enumerate(spec['files']):
        check_mount(); check_memory(limits['process_rss_bytes'])
        if time.monotonic() >= deadline:
            raise TimeoutError('Overall deadline exceeded')
        if used + row['bytes'] > limits['source_read_bytes']:
            raise ValueError('Source read cap exceeded')
        result = run_worker(dict(root=str(root), row=row, chunk_bytes=limits['chunk_bytes'],
                                 remaining_bytes=limits['source_read_bytes']-used,
                                 memory_limit=limits['process_rss_bytes']),
                            min(limits['per_file_seconds'], deadline-time.monotonic()),
                            limits['process_rss_bytes'])
        if (result['uri'] != row['uri'] or result['bytes'] != row['bytes'] or
                result['sha256'] != row['expected_content_sha256']):
            raise ValueError('Worker evidence does not match request')
        if time.monotonic() >= deadline:
            raise TimeoutError('Overall deadline exceeded')
        used += result['bytes']; results.append(result)
        package.write(f'file-{index:02}.json', result)
    check_mount()
    if used != spec['unique_input_bytes']:
        raise ValueError('Incomplete byte coverage')
    return results


def run():
    started = time.monotonic(); package = None
    def timeout(*_):
        raise TimeoutError('Overall wall-time ceiling')
    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(300)
    try:
        spec = load_spec(); limits = spec['limits']; deadline = started + limits['wall_seconds']
        check_memory(limits['process_rss_bytes'])
        registry_bytes = (REPO/'configs/local/roots.yaml').read_bytes()
        registry = yaml.safe_load(registry_bytes)
        request_ref = next(r for r in spec['inputs'] if r['path'].endswith('/request.json'))
        old_request = json.loads((REPO/request_ref['path']).read_bytes())
        if digest(registry_bytes) != old_request['registry_sha256']:
            raise ValueError('Registry changed since metadata inventory')
        root = Path(old_request['diagnostic_root'])
        primary = registry['failure_domains']['external_primary']; mount = Path(primary['mount_path'])
        acquisition = Path(registry['roots']['pants_source']['acquisition_parent'])
        if root.parent != acquisition or not root.is_relative_to(mount):
            raise ValueError('Source outside registered acquisition root')
        device = None
        def check_mount():
            nonlocal device
            if not mount.is_mount() or mount.resolve(strict=True) != mount:
                raise ValueError('Registered mount absent or noncanonical')
            info = disk_info(mount)
            if info.get('VolumeUUID') != primary['volume_uuid'] or info.get('FilesystemType') != 'apfs':
                raise ValueError('Volume identity changed')
            current = mount.stat().st_dev
            if device is not None and current != device:
                raise ValueError('Mount device changed')
            device = current
        check_mount()
        parent = REPO/'outputs/prowl'
        if shutil.disk_usage(parent).free < limits['internal_free_floor_bytes']:
            raise ValueError('Internal free-space floor')
        package = Package(parent/('localizer-content-'+str(uuid4())), max_bytes=limits['output_bytes'])
        print('Evidence package: '+str(package.path), flush=True)
        package.write('request.json', dict(spec_sha256=SPEC_SHA, spec=spec, registry_sha256=digest(registry_bytes),
                                          root=str(root), eligibility_granted=0))
        code = [Path(__file__), REPO/'scripts/diagnostics/followup_voxel_audit.py',
                REPO/'scripts/diagnostics/storage_setup.py', REPO/'src/data/manifest_records.py']
        package.write('implementation.json', {str(p.relative_to(REPO)):dict(sha256=digest(p.read_bytes()),
                                                                         text=p.read_text()) for p in code})
        # Worker checks mount every chunk via the same pinned configuration.
        worker_volume = dict(mount=str(mount), uuid=primary['volume_uuid'], device=device)
        def dispatch(request, seconds, memory):
            return supervised_hash(dict(request, volume=worker_volume), seconds, memory)
        results = execute(spec, root, package, check_mount, deadline, dispatch)
        package.write('summary.json', dict(status='content_identity_verified', files=len(results),
            source_bytes=sum(r['bytes'] for r in results), elapsed_seconds=time.monotonic()-started,
            eligibility_granted=0, source_modified=False, voxel_decode=False, caching='unknown',
            parent_peak_rss_bytes=peak_rss()))
        for name, sha in package.hashes.items():
            if digest((package.path/name).read_bytes()) != sha:
                raise ValueError('Evidence readback failed')
        check_memory(limits['process_rss_bytes']); check_mount()
        if time.monotonic() >= deadline:
            raise TimeoutError('Overall deadline exceeded')
        package.write('verification.json', dict(status='complete', files=package.hashes.copy(),
                                                eligibility_granted=0, training_started=False))
        print(json.dumps(dict(status='complete', files=len(results), source_bytes=spec['unique_input_bytes'],
                              elapsed_seconds=time.monotonic()-started)), flush=True)
    except BaseException as exc:
        if package is not None and not (package.path/'verification.json').exists():
            try:
                package.write('failure.json', dict(status='failed_not_complete', error_type=type(exc).__name__,
                                                  message=str(exc)))
            except Exception:
                pass  # An incomplete package remains incomplete even if its error receipt cannot be written.
        raise
    finally:
        signal.alarm(0); signal.signal(signal.SIGALRM, previous)


def worker(request):
    volume = request.pop('volume', None); last = -float('inf')
    def tick():
        nonlocal last
        if volume is not None and time.monotonic()-last >= 1:
            mount = Path(volume['mount'])
            if not mount.is_mount() or mount.resolve(strict=True) != mount or mount.stat().st_dev != volume['device']:
                raise ValueError('Worker mount changed')
            info = disk_info(mount)
            if info.get('VolumeUUID') != volume['uuid'] or info.get('FilesystemType') != 'apfs':
                raise ValueError('Worker volume changed')
            last = time.monotonic()
    result = hash_file(Path(request.pop('root')), request.pop('row'), tick=tick, **request)
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run', action='store_true'); group.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker(json.loads(sys.stdin.buffer.read(32768)))
    else:
        run()
