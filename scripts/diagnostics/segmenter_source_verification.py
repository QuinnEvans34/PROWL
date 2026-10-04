"""D-316 one-shot metadata then compressed identity/header checks; never arrays or permission."""
import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import plistlib
import resource
import signal
import stat
import subprocess
import sys
import time
import zlib

REPO = Path(__file__).resolve().parents[2]
INVENTORY = 'outputs/prowl/STAGE2-METADATA-20261001/inventory.json'
DERIVED = 'outputs/prowl/expansion-v2-candidate-6bc5c245-47b4-45ab-9616-cd75da986b74/derived.json'
REGISTRY = 'configs/local/roots.yaml'
PINS = {INVENTORY: '2f38464f4fd6efe8235b5471bf2f46466ab7ce13d17e1c7ccff2c7876997aab4',
        DERIVED: 'b0f1c625728603ce87841d5c0ce7ad5397574da04dd5e7ca4814c5ef462ca29f',
        REGISTRY: '46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788'}
STAGES = {'metadata': 'SEGMENTER-SOURCE-M1-attempt02-20261001', 'identity': 'SEGMENTER-SOURCE-M2-20261001'}
MAX_HEADER = 65536


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def put(path, value):
    with Path(path).open('xb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def safe_local(name, pin):
    p = REPO / name
    require(p.is_file() and p.resolve(strict=True) == p and p.stat().st_size <= 32 * 1024**2,
            'Unsafe/oversized retained input')
    raw = p.read_bytes()
    require(sha(raw) == pin, 'Retained input changed: ' + name)
    return raw


def member_name(name):
    rel = PurePosixPath(name)
    require(isinstance(name, str) and str(rel) == name and rel.parts and
            not rel.is_absolute() and not any(x in ('.', '..') for x in rel.parts), 'Unsafe member')
    return rel


@contextmanager
def directory(path):
    """Walk from / using directory descriptors and O_NOFOLLOW at every component."""
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'Unsafe root')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        yield fd
    finally:
        os.close(fd)


@contextmanager
def parent(root_fd, uri):
    rel = member_name(uri)
    fd = os.dup(root_fd)
    try:
        for part in rel.parts[:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            if os.fstat(nxt).st_dev != os.fstat(root_fd).st_dev:
                os.close(nxt)
                raise ValueError('Nested source device forbidden')
            os.close(fd)
            fd = nxt
        yield fd, rel.name
    finally:
        os.close(fd)


def observation(s):
    return dict(bytes=s.st_size, device=s.st_dev, inode=s.st_ino,
                mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns, mode=s.st_mode)


def observe(root_fd, row):
    try:
        with parent(root_fd, row['uri']) as (fd, name):
            s = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if not stat.S_ISREG(s.st_mode):
            return dict(state='held', reasons=['not_regular_file'], observation=observation(s))
        reasons = []
        if s.st_dev != os.fstat(root_fd).st_dev:
            reasons.append('wrong_source_device')
        if row['expected_bytes'] is not None and s.st_size != row['expected_bytes']:
            reasons.append('retained_size_changed')
        return dict(state='observed' if not reasons else 'held', reasons=reasons, observation=observation(s))
    except FileNotFoundError:
        return dict(state='held', reasons=['missing_exact_path'], observation=None)
    except OSError as e:
        return dict(state='held', reasons=['unsafe_or_inaccessible_path'], error_type=type(e).__name__, observation=None)


@contextmanager
def source_stream(root_fd, row):
    with parent(root_fd, row['uri']) as (fd, name):
        leaf = os.stat(name, dir_fd=fd, follow_symlinks=False)
        require(stat.S_ISREG(leaf.st_mode) and leaf.st_dev == os.fstat(root_fd).st_dev and observation(leaf) == row['observation'], 'Source changed since M1')
        rawfd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(rawfd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and observation(before) == row['observation'], 'Opened identity differs')
            yield stream
            require(observation(os.fstat(stream.fileno())) == row['observation'] and
                    observation(os.stat(name, dir_fd=fd, follow_symlinks=False)) == row['observation'],
                    'Source changed during read')


def hash_stream(stream, size, counter, guard):
    h = hashlib.sha256()
    left = size
    while left:
        guard()
        raw = stream.read(min(1024**2, left))
        require(raw and len(raw) <= left, 'Truncated or oversized hash input')
        left -= len(raw)
        counter['hash_bytes'] += len(raw)
        h.update(raw)
    return h.hexdigest()


def lesion_header(stream, counter):
    """At most 64 KiB compressed input and exactly 348 decompressed header bytes."""
    import nibabel as nib
    import numpy as np
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    raw = b''
    used = 0
    while len(raw) < 348:
        require(used < MAX_HEADER, 'Compressed header cap')
        chunk = stream.read(min(4096, MAX_HEADER - used))
        require(chunk, 'Truncated header')
        used += len(chunk)
        counter['header_bytes'] += len(chunk)
        raw += decoder.decompress(chunk, 348 - len(raw))
    require(raw[:4] in (b'\x5c\x01\x00\x00', b'\x00\x00\x01\x5c'), 'Not NIfTI-1')
    h = nib.Nifti1Header.from_fileobj(io.BytesIO(raw), check=False)
    require(bytes(h['magic']) == b'n+1\x00', 'Not single-file NIfTI-1')
    shape = tuple(int(x) for x in h.get_data_shape())
    affine = h.get_best_affine()
    zooms = tuple(float(x) for x in h.get_zooms())
    dtype = h.get_data_dtype()
    offset = float(h['vox_offset'])
    slope, intercept = h.get_slope_inter()
    require(len(shape) == 3 and all(x > 0 for x in shape), 'Unsupported 3D grid')
    require(np.isfinite(affine).all() and abs(np.linalg.det(affine[:3, :3])) > 0 and
            all(math.isfinite(z) and z > 0 for z in zooms), 'Invalid physical grid')
    require(dtype.kind in 'iuf' and dtype.itemsize in (1, 2, 4, 8), 'Unsupported label dtype')
    require(math.isfinite(offset) and offset.is_integer() and offset >= 352, 'Invalid payload offset')
    require(slope is None or (math.isfinite(slope) and slope != 0 and math.isfinite(intercept)), 'Invalid effective scaling')
    voxels = math.prod(shape)
    payload = voxels * dtype.itemsize
    require(voxels <= 96_000_000 and offset + payload <= 1024**3, 'Header exceeds next content envelope; retain exception')
    return dict(shape=list(shape), affine=affine.tolist(), spacing=list(zooms), units=list(h.get_xyzt_units()),
                dtype=dtype.str, dtype_itemsize=dtype.itemsize, voxel_count=voxels, vox_offset=int(offset),
                payload_bytes=payload, projected_nifti_bytes=int(offset) + payload,
                stored_slope=None if not math.isfinite(float(h['scl_slope'])) else float(h['scl_slope']),
                stored_intercept=None if not math.isfinite(float(h['scl_inter'])) else float(h['scl_inter']),
                effective_slope=1.0 if slope is None else slope, effective_intercept=0.0 if slope is None else intercept,
                qform_code=int(h['qform_code']), sform_code=int(h['sform_code']),
                decompressed_header_sha256=sha(raw), compressed_header_bytes=used)


def grid_reasons(header, geometry):
    import numpy as np
    reasons = []
    if header['shape'] != geometry['shape_xyz'] or not np.allclose(
            header['affine'], np.array(geometry['affine_ras']).reshape(4, 4), rtol=0, atol=1e-5):
        reasons.append('lesion_ct_grid_mismatch')
    if header['units'][0] not in ('mm', 'unknown'):
        reasons.append('unsupported_lesion_spatial_units')
    return reasons


def verify_package(dest, pin):
    raw = (dest / 'receipt.json').read_bytes()
    require(sha(raw) == pin, 'Receipt changed')
    receipt = json.loads(raw)
    require(receipt['state'] == 'complete', 'Incomplete job')
    require(set(receipt['files']) == {p.name for p in dest.iterdir() if p.name != 'receipt.json'}, 'Package membership changed')
    for name, expected in receipt['files'].items():
        require(Path(name).name == name, 'Unsafe package path')
        p = dest / name
        require(p.is_file() and not p.is_symlink(), 'Unsafe package file')
        b = p.read_bytes()
        require(dict(bytes=len(b), sha256=sha(b)) == expected, 'Package member changed')
    return json.loads((dest / 'result.json').read_bytes())


def runtime():
    import importlib.metadata
    return dict(python=sys.version, executable=str(Path(sys.executable).absolute()),
                executable_sha256=sha(Path(sys.executable).read_bytes()),
                nibabel=importlib.metadata.version('nibabel'), numpy=importlib.metadata.version('numpy'))


def build_request(stage):
    import yaml
    payload = {name: safe_local(name, pin) for name, pin in PINS.items()}
    inv = json.loads(payload[INVENTORY]); d = json.loads(payload[DERIVED]); reg = yaml.safe_load(payload[REGISTRY])
    domain = reg['failure_domains']['external_primary']
    root = str(Path(reg['roots']['pants_source']['acquisition_parent']) / 'extraction-3b1cd6110811-20260922')
    studies = {s['study_id']: s for s in d['manifest']['studies']}
    rows = []
    for candidate in inv['proposed_candidates']:
        sid = candidate['study_id']; role = candidate['protected_role']
        require(role in ('train', 'validation') and candidate['localizer_state'] == 'qualified', 'Wrong candidate role/state')
        s = studies[sid]
        require(candidate['image'] == s['image'] and s['geometry'] is not None, 'Companion reference mismatch')
        for kind, key in [('ct', 'image'), ('pancreas', 'pancreas'), ('lesion', 'expected_lesion')]:
            ref = candidate[key]
            member_name(ref['uri'])
            require(ref['root_alias'] == 'followup_source' and sid.split(':')[-1] in PurePosixPath(ref['uri']).parts, 'Wrong source identity')
            old = candidate['retained_lesion_annotation'] if kind == 'lesion' else None
            rows.append(dict(study_id=sid, protected_role=role, kind=kind, uri=ref['uri'],
                             expected_bytes=ref['bytes'], expected_sha256=ref.get('content_sha256'),
                             retained_lesion_sha256=old['file']['content_sha256'] if old else None,
                             retained_ct_geometry=s['geometry']))
    require(len(rows) == 36 and len({r['uri'] for r in rows}) == 36 and
            sum(r['kind'] == 'lesion' for r in rows) == 12, 'Scope differs')
    request = dict(component='segmenter-source-verification-v1', decision='D-316', stage=stage,
                   capability=dict(root_alias='followup_source', source_root=root, mount=domain['mount_path'],
                                   volume_uuid=domain['volume_uuid'], filesystem=domain['filesystem'],
                                   operations=['stat'] if stage == 'metadata' else ['read_compressed_hash', 'read_lesion_header'],
                                   source_writes=False, global_activation=False),
                   retained_pins=PINS, code_pins={'scripts/diagnostics/segmenter_source_verification.py': sha(Path(__file__).read_bytes())},
                   runtime=runtime(), files=rows, output=str(REPO / 'outputs/prowl' / STAGES[stage]),
                   arrays_allowed=False, qualifications_granted=False,
                   budget=dict(seconds=90 if stage == 'metadata' else 600, rss_bytes=(512 if stage == 'metadata' else 1024)*1024**2,
                               output_bytes=(1 if stage == 'metadata' else 4)*1024**2, observations=36, hash_bytes=0, header_bytes=0))
    if stage == 'identity':
        dest = REPO / 'outputs/prowl' / STAGES['metadata']
        pin = sha((dest / 'receipt.json').read_bytes())
        result = verify_package(dest, pin)
        require(result['stage'] == 'metadata' and len(result['files']) == 36, 'Wrong preceding stage')
        require(all(r['state'] == 'observed' for r in result['files']), 'M1 holds need separate reviewed scope; no refill')
        for row, prior in zip(rows, result['files']):
            require(all(row[k] == prior[k] for k in row), 'M1 source ledger changed')
            row['observation'] = prior['observation']
        request['metadata_receipt_sha256'] = pin
        request['budget']['hash_bytes'] = sum(r['observation']['bytes'] for r in rows)
        request['budget']['header_bytes'] = 12 * MAX_HEADER
    return request


def mount_guard(cap):
    mount = Path(cap['mount']); root = Path(cap['source_root'])
    require(mount.is_mount() and not mount.is_symlink() and mount.resolve(strict=True) == mount and
            root.resolve(strict=True) == root and root.is_relative_to(mount), 'Unsafe/unmounted registered source')
    info = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', str(mount)], timeout=20))
    require(info.get('VolumeUUID') == cap['volume_uuid'] and info.get('MountPoint') == str(mount) and
            info.get('FilesystemType', '').lower() == cap['filesystem'], 'Wrong source volume')
    return dict(mount=str(mount), volume_uuid=info['VolumeUUID'], filesystem=info['FilesystemType'],
                root_device=root.stat().st_dev, root_inode=root.stat().st_ino)


def execute(request_path, request_pin):
    raw = request_path.read_bytes()
    require(sha(raw) == request_pin, 'Request changed')
    req = json.loads(raw)
    require(req == build_request(req['stage']), 'Request scope/code/runtime differs')
    dest = Path(req['output'])
    require(request_path == dest / 'request.json' and dest.resolve(strict=True) == dest, 'Wrong output/request location')
    put(dest / 'consumed.json', dict(request_sha256=request_pin, state='consumed_no_retry'))
    start = time.monotonic(); counter = dict(hash_bytes=0, header_bytes=0); rows = []
    def guard():
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
        require(rss <= req['budget']['rss_bytes'] and time.monotonic()-start <= req['budget']['seconds'], 'Time/RSS budget')
        require(counter['hash_bytes'] <= req['budget']['hash_bytes'] and counter['header_bytes'] <= req['budget']['header_bytes'], 'Source read budget')
    def timeout(*_):
        raise TimeoutError('Source verification time cap')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(req['budget']['seconds'])
    # Metadata may walk directories, but must never open a source payload.
    if req['stage'] == 'metadata':
        def block(event, args):
            if event == 'open' and isinstance(args[0], (str, bytes)):
                require(not os.fsdecode(args[0]).endswith(('.nii', '.nii.gz', '.pt', '.pth')), 'Payload open forbidden in M1')
        sys.addaudithook(block)
    try:
        before = mount_guard(req['capability']); guard()
        with directory(req['capability']['source_root']) as rootfd:
            require(os.fstat(rootfd).st_dev == before['root_device'] and os.fstat(rootfd).st_ino == before['root_inode'], 'Source root replaced')
            for row in req['files']:
                guard()
                if req['stage'] == 'metadata':
                    rows.append(dict(**row, **observe(rootfd, row)))
                    continue
                record = dict(**row, state='verified', reasons=[])
                try:
                    with source_stream(rootfd, row) as stream:
                        identity = hash_stream(stream, row['observation']['bytes'], counter, guard)
                        record['sha256'] = identity
                        if row['expected_sha256'] and identity != row['expected_sha256']:
                            record['reasons'].append('retained_companion_hash_changed')
                        if row['retained_lesion_sha256'] and identity != row['retained_lesion_sha256']:
                            record['reasons'].append('retained_lesion_hash_changed')
                        if row['kind'] == 'lesion':
                            stream.seek(0)
                            record['header'] = lesion_header(stream, counter)
                            record['reasons'] += grid_reasons(record['header'], row['retained_ct_geometry'])
                except (ValueError, OSError, zlib.error) as e:
                    record['reasons'].append('identity_or_header_rejected')
                    record['error'] = str(e)
                record['state'] = 'held' if record['reasons'] else 'verified'
                rows.append(record)
                guard()
        after = mount_guard(req['capability']); require(before == after, 'Source mount/root changed')
        # Companion identity is necessary for any replayed CT geometry/unknown label-unit interpretation.
        if req['stage'] == 'identity':
            for r in rows:
                if r['kind'] == 'lesion':
                    companions = [x for x in rows if x['study_id'] == r['study_id'] and x['kind'] != 'lesion']
                    if any(x['state'] != 'verified' for x in companions):
                        r['state'] = 'held'; r['reasons'].append('paired_companion_not_verified')
                    if r['state'] == 'verified':
                        r['spatial_context'] = 'qualified_mm_ct_exact_matched_grid' if r['header']['units'][0] == 'unknown' else 'declared_mm_exact_matched_grid'
        guard()
        result = dict(stage=req['stage'], decision='D-316', request_sha256=request_pin, files=rows,
                      observed_or_verified=sum(r['state'] in ('observed', 'verified') for r in rows),
                      held=sum(r['state'] == 'held' for r in rows), mount_before=before, mount_after=after,
                      **counter, arrays_read=0, model_updates=0, real_qualifications=0,
                      seconds=time.monotonic()-start,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
        put(dest / 'result.json', result)
        members = {p.name: dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in dest.iterdir()}
        receipt = dict(state='complete', request_sha256=request_pin, files=members)
        require(sum(v['bytes'] for v in members.values())+len(encoded(receipt)) <= req['budget']['output_bytes'], 'Output budget')
        put(dest / 'receipt.json', receipt)
        print(json.dumps({k: result[k] for k in ['stage','observed_or_verified','held','hash_bytes','header_bytes','seconds','peak_rss_bytes']}))
        print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()))
    except BaseException as e:
        put(dest / 'failure.json', dict(state='incomplete_consumed', error=str(e), files=rows, **counter, seconds=time.monotonic()-start))
        raise
    finally:
        signal.alarm(0)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stage', choices=STAGES)
    ap.add_argument('--prepare', action='store_true'); ap.add_argument('--request', type=Path)
    ap.add_argument('--sha256'); ap.add_argument('--verify', type=Path); args = ap.parse_args()
    if args.verify:
        result = verify_package(args.verify, args.sha256)
        req = json.loads((args.verify/'request.json').read_bytes())
        require(req == build_request(req['stage']), 'Source/runtime pins changed after execution')
        require(result['request_sha256'] == sha((args.verify/'request.json').read_bytes()), 'Result/request differs')
        print('Fresh-process package/input/code/runtime verification passed')
    elif args.prepare:
        req = build_request(args.stage); dest = Path(req['output']); dest.mkdir()
        put(dest/'request.json', req); print(dest/'request.json'); print('request_sha256='+sha((dest/'request.json').read_bytes()))
    else:
        require(args.request is not None and args.sha256 is not None, 'Exact request/path hash required')
        execute(args.request.absolute(), args.sha256)


if __name__ == '__main__':
    main()
