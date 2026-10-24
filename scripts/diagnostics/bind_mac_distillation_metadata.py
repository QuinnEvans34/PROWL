"""Verify the private handoff and bind only its fixed training pilot to Mac files.

Reads compressed source bytes for hashes, never decodes CTs or launches models.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ARCHIVE_SHA = '04d5b0521407c19a5fb4d8f664cc43c3b77be2ba7346246041713f00f24761c5'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(archive, source, output):
    if output.exists():
        raise ValueError('Output exists; preserve previous evidence')
    if archive.stat().st_size != 4057125 or sha(archive) != ARCHIVE_SHA:
        raise ValueError('Unexpected handoff archive')
    with zipfile.ZipFile(archive) as z:
        handoff = json.loads(z.read('HANDOFF.json'))
        for name, pin in handoff['files'].items():
            data = z.read(name)
            if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
                raise ValueError('Handoff member mismatch: ' + name)
        train = z.read('membership/train.txt').decode().splitlines()
        dev = z.read('membership/development.txt').decode().splitlines()
        pilot = json.loads(z.read('pilot-order.json'))
        if len(set(train)) != 1333 or len(set(dev)) != 70 or set(train) & set(dev):
            raise ValueError('Membership mismatch')
        if len(pilot) != 12 or len(set(pilot)) != 12 or not set(pilot) <= set(train):
            raise ValueError('Pilot membership mismatch')
        rows = []
        for case in pilot:
            number = int(case.removeprefix('PanTS_'))
            low = ((number-1)//1000)*1000+1
            image_dir = source/f'PanTSMini_ImageTr_{low:08d}_{low+999:08d}'/case
            label_dir = source/'PanTSMini_Label'/case/'segmentations'
            paths = dict(ct=image_dir/'ct.nii.gz', pancreas=label_dir/'pancreas.nii.gz',
                         lesion=label_dir/'pancreatic_lesion.nii.gz')
            expected = json.loads(z.read(f'source/cached-metadata/{case}.json'))['source_sha256']
            files = {}
            for role, path in paths.items():
                if not path.is_file():
                    files[role] = dict(path=str(path), status='missing')
                    continue
                before = path.stat(); actual = sha(path); after = path.stat()
                stable = (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
                files[role] = dict(path=str(path), sha256=actual, expected_sha256=expected.get(role),
                                   bytes=after.st_size, inode=after.st_ino, device=after.st_dev,
                                   mtime_ns=after.st_mtime_ns,
                                   status='match' if stable and actual == expected.get(role) else 'mismatch')
            rows.append(dict(case_id=case, protected_role='train', files=files))
            print(case, {k:v['status'] for k,v in files.items()}, flush=True)
    success = all(f['status']=='match' for row in rows for f in row['files'].values())
    result = dict(archive_sha256=ARCHIVE_SHA, verified_metadata_files=len(handoff['files']),
                  train_count=len(train), development_count=len(dev), pilot=rows,
                  all_pilot_sources_match=success, scientific_launch_authorized=False,
                  decoded_voxel_reads=0, note='Windows coverage reused; no repeat cohort audit')
    with output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    return success


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if bind(a.archive, a.source, a.output) else 1)
