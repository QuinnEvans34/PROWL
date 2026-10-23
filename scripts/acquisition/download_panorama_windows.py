"""Windows PANORAMA CT acquisition; pinned sizes/MD5, local SHA256, no extraction.

Preserves partials and failures. Does not qualify a training source or acquire labels.
The historical Mac acquisition implementation remains unchanged.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.operations.full_training_platform import training_guard, require_ac

CHUNK = 1024 * 1024
FLOOR = 512 * 1024**3


def retry_delay(exc, retry):
    if isinstance(exc, HTTPError):
        if exc.code not in (408, 429, 500, 502, 503, 504):
            return None
    elif not isinstance(exc, (TimeoutError, ConnectionError, URLError, http.client.IncompleteRead)):
        return None
    delay = min(300, 5 * 2 ** min(retry, 6))
    if isinstance(exc, HTTPError):
        value = exc.headers.get('Retry-After', '') if exc.headers else ''
        if value.isdigit():
            delay = max(delay, int(value))
    return delay


def transfer_with_retries(item, directory, check, record, max_retries=100, sleep=time.sleep):
    for attempt in range(max_retries + 1):
        try:
            return transfer(item, directory, check, record)
        except Exception as exc:
            delay = retry_delay(exc, attempt)
            if delay is None or attempt == max_retries:
                raise
            check()  # Never retry across a power, storage or volume failure.
            record('retry_wait', name=item['name'], retry=attempt + 1,
                   wait_seconds=delay, error=repr(exc), partials_retained=True)
            # Keep safety checks responsive during backoff.
            while delay > 0:
                interval = min(5, delay)
                sleep(interval); check(); delay -= interval


def volume_id(root):
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel.GetVolumeNameForVolumeMountPointW
    fn.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    fn.restype = wintypes.BOOL
    buf = ctypes.create_unicode_buffer(1024)
    if not fn(str(root), buf, len(buf)):
        raise ctypes.WinError(ctypes.get_last_error())
    return buf.value


def validate_response(status, headers, offset, expected):
    if status != (206 if offset else 200):
        raise ValueError('Server did not honor transfer/resume mode')
    if offset and headers.get('Content-Range') != f'bytes {offset}-{expected-1}/{expected}':
        raise ValueError('Unexpected Content-Range')
    if headers.get('Content-Length') is not None and int(headers['Content-Length']) != expected-offset:
        raise ValueError('Unexpected Content-Length')
    if headers.get('Content-Encoding', 'identity') != 'identity':
        raise ValueError('Unexpected content encoding')


def verify(path, item):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != item['bytes']:
        raise ValueError('Payload type/size mismatch; retain evidence')
    md5 = hashlib.md5(usedforsecurity=False); sha = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b''):
            md5.update(chunk); sha.update(chunk)
    if md5.hexdigest() != item['publisher_md5']:
        raise ValueError('Publisher MD5 mismatch; retain evidence')
    return dict(md5=md5.hexdigest(), sha256=sha.hexdigest())


def transfer(item, directory, check, record):
    name = item['name']
    if Path(name).name != name or '/' in name or '\\' in name or ':' in name:
        raise ValueError('Unsafe destination name')
    final = directory / name; partial = directory / (name + '.part')
    for path in (final, partial):
        if path.is_symlink() or path.is_junction():
            raise ValueError('Linked payload refused')
    check()
    if final.exists():
        record('verified_existing', name=name, **verify(final, item)); return
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > item['bytes']:
        raise ValueError('Oversize partial retained')
    check(item['bytes'] - offset)
    record('starting', name=name, resume_bytes=offset, expected_bytes=item['bytes'])
    if offset < item['bytes']:
        headers = {'User-Agent': 'PROWL-research-acquisition/1.0', 'Accept-Encoding': 'identity'}
        if offset: headers['Range'] = f'bytes={offset}-'
        url = f'https://zenodo.org/records/{item["record_id"]}/files/{name}?download=1'
        with urlopen(Request(url, headers=headers), timeout=60) as response:
            validate_response(response.status, response.headers, offset, item['bytes'])
            check()
            with partial.open('ab' if partial.exists() else 'xb') as output:
                count = offset; last = time.monotonic()
                try:
                    for chunk in iter(lambda: response.read1(CHUNK), b''):
                        if count + len(chunk) > item['bytes']:
                            raise ValueError('Transfer exceeds pinned size')
                        check(len(chunk))
                        output.write(chunk); count += len(chunk)
                        if time.monotonic() - last >= 30:
                            output.flush()
                            record('progress', name=name, bytes=count, expected_bytes=item['bytes'])
                            last = time.monotonic()
                finally:
                    output.flush(); os.fsync(output.fileno())
        if count != item['bytes']:
            raise ConnectionError('Short transfer retained for explicit resume')
    check()
    hashes = verify(partial, item)
    if final.exists(): raise FileExistsError('Refusing replacement')
    partial.rename(final)
    record('verified_download', name=name, bytes=item['bytes'], **hashes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drive', required=True, type=Path)
    parser.add_argument('--volume-id', required=True)
    parser.add_argument('--max-retries', type=int, default=100)
    args = parser.parse_args()
    if not 0 <= args.max_retries <= 1000:
        raise ValueError('Retry limit must be between 0 and 1000')
    mount = args.drive.resolve()
    if os.name != 'nt' or str(mount) != mount.anchor:
        raise ValueError('An explicit Windows volume root is required')
    def check(needed=0):
        if volume_id(mount) != args.volume_id:
            raise RuntimeError('Destination volume changed or disappeared')
        require_ac()
        if shutil.disk_usage(mount).free < FLOOR + needed:
            raise RuntimeError('512 GiB acquisition free-space reserve would be crossed')
    check()
    directory = mount
    for part in ('PROWL', 'sources', 'panorama', 'acquisition-20261008'):
        directory = directory / part
        if directory.is_symlink() or directory.is_junction():
            raise ValueError('Linked destination refused')
        directory.mkdir(exist_ok=True)
    inventory = ROOT / 'docs/capstone/data/acquisition-2026-09-19.json'
    raw = inventory.read_bytes(); queue = json.loads(raw)['panorama']['ct_archives']
    # Entire queue reservation is deliberately conservative, including existing bytes.
    check(sum(item['bytes'] for item in queue))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with training_guard(directory / '.download.lock'), (directory / f'attempt-{stamp}.jsonl').open('x') as log:
        def record(event, **fields):
            line = json.dumps(dict(at=datetime.now(timezone.utc).isoformat(), event=event, **fields))
            log.write(line + '\n'); log.flush(); os.fsync(log.fileno()); print(line, flush=True)
        record('attempt_started', volume_id=args.volume_id, destination=str(directory),
               inventory_sha256=hashlib.sha256(raw).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               ct_archives_only=True, extraction=False, reserve_bytes=FLOOR,
               max_retries_per_archive=args.max_retries)
        try:
            for item in queue:
                transfer_with_retries(item, directory, check, record, args.max_retries)
            record('ct_queue_complete', labels_qualified=False, training_source_qualified=False)
        except BaseException as exc:
            record('failed', error=repr(exc), partials_retained=True)
            raise


if __name__ == '__main__':
    main()
