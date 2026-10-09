"""Verify exact admitted CT bytes against private handoff; never read test payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.operations.full_training_platform import training_guard, require_ac


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--handoff', type=Path, required=True)
    p.add_argument('--ct-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    groups = {key: (args.handoff / path).read_text().split() for key, path in {
        'train': 'splits/admitted/train.txt', 'development': 'splits/admitted/development.txt',
        'original_train': 'splits/original/train.txt', 'original_dev': 'splits/original/val.txt',
        'test': 'splits/original/test.txt'}.items()}
    assert all(len(v) == len(set(v)) for v in groups.values())
    assert set(groups['train']) <= set(groups['original_train'])
    assert set(groups['development']) <= set(groups['original_dev'])
    selected = groups['train'] + groups['development']
    assert len(selected) == len(set(selected)) == 1408
    assert not set(selected) & set(groups['test'])
    inventory = args.handoff / 'metadata/source-file-hashes.json'
    records = [r for r in json.loads(inventory.read_text()) if r['kind'] == 'ct']
    assert len(records) == 1408 and {r['case_id'] for r in records} == set(selected)
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic(); total = 0
    with training_guard(args.output / '.lock'), (args.output / 'ct-verification.jsonl').open('x') as log:
        try:
            for index, row in enumerate(records, 1):
                name = row['case_id']
                assert re.fullmatch(r'PanTS_[0-9]{8}', name)
                assert row['relative_path'] == name + '/ct.nii.gz'
                assert row['role'] == ('train' if name in groups['train'] else 'development')
                path = args.ct_root / row['relative_path']
                require_ac()
                if not path.is_file() or path.is_symlink(): raise ValueError(f'Missing/unsafe CT: {name}')
                before = path.stat(); h = hashlib.sha256()
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(4*1024**2), b''): h.update(chunk)
                after = path.stat()
                assert (before.st_size,before.st_mtime_ns,before.st_ino) == (after.st_size,after.st_mtime_ns,after.st_ino)
                actual = h.hexdigest(); passed = actual == row['sha256']; total += before.st_size
                result = dict(case_id=name, path=str(path), bytes=before.st_size, sha256=actual,
                              expected_sha256=row['sha256'], passed=passed, seconds=time.monotonic()-start)
                log.write(json.dumps(result)+'\n'); log.flush()
                if not passed: raise ValueError(f'CT hash mismatch: {name}; no training/cache admission')
                if index == 1 or index % 25 == 0: print(json.dumps(dict(verified=index,bytes=total,seconds=time.monotonic()-start)),flush=True)
            summary = dict(passed=True,cases=len(records),bytes=total,seconds=time.monotonic()-start,
                           source_inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest())
        except BaseException as exc:
            (args.output / 'failure.json').write_text(json.dumps(dict(error=repr(exc),seconds=time.monotonic()-start),indent=2))
            raise
        (args.output / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary),flush=True)


if __name__ == '__main__': main()
