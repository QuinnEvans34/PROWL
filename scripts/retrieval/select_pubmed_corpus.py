#!/usr/bin/env python3
"""Resumable evaluation, global ranking and verified export of a frozen catalog."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import signal
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.retrieval.resumable_selection import run


def install_signal_handlers():
    def stop(signum, frame):
        raise KeyboardInterrupt(f'User stop signal {signum}')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog', 'mesh-path', 'output', 'receipts', 'packet-path'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--log-path', type=Path, required=True, help='Fresh internal-drive invocation log, outside output')
    parser.add_argument('--mesh-sha256', required=True)
    parser.add_argument('--expected-volume-uuid', required=True)
    parser.add_argument('--cutoff-year', type=int, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--evaluation-only', action='store_true', help='Development stop before ranking/export')
    parser.add_argument('--hours', type=float, default=12)
    parser.add_argument('--max-gib', type=float, default=256)
    parser.add_argument('--free-gib', type=float, default=400)
    parser.add_argument('--cache-mib', type=int, default=32)
    parser.add_argument('--workers', type=int, default=1, help='Ordered CPU evaluation workers (1..12); one SQLite writer')
    args = vars(parser.parse_args())
    log_path = args.pop('log_path').absolute()
    if log_path.exists() or any(p.is_symlink() for p in (log_path, *log_path.parents)):
        parser.error('Invocation log must be a fresh nonsymlink path')
    if log_path.parent.stat().st_dev == args['catalog'].stat().st_dev:
        parser.error('Invocation log must be on a different device from the catalog')
    expected = args.pop('expected_volume_uuid')
    mount = args['catalog'].absolute()
    while not os.path.ismount(mount):
        mount = mount.parent
    info = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', str(mount)]))
    if info.get('VolumeUUID') != expected:
        parser.error('External volume UUID mismatch')
    args['volume_id'] = expected
    install_signal_handlers()
    with log_path.open('x') as log:
        def record(state, **details):
            log.write(json.dumps(dict(state=state, utc_seconds=time.time(), **details))+'\n')
            log.flush(); os.fsync(log.fileno())
        record('started', pid=os.getpid(), output=str(args['output']), resume=args['resume'])
        try:
            result = run(**args)
        except BaseException as exc:
            record('stopped', error_type=type(exc).__name__, error=str(exc))
            raise
        record('finished', stage=result.get('stage'), exit_code=0)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
