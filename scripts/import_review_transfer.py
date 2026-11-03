"""Verify and import one bounded private review tar; no inference or app registration."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

MAX_ARCHIVE = 256 * 1024**2
MAX_TOTAL = 512 * 1024**2
MAX_FILES = 128
HASH = re.compile(r'[a-f0-9]{64}')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def name(value):
    p = PurePosixPath(value)
    if (not value or '\\' in value or p.is_absolute() or ':' in value
            or any(v in ('', '.', '..') for v in value.split('/'))
            or len(value) > 240 or any(ord(c) < 32 for c in value)):
        raise ValueError('Unsafe transfer member path')
    return value


def import_archive(archive, output, *, expected_sha256):
    archive, output = Path(archive), Path(output)
    if not HASH.fullmatch(expected_sha256):
        raise ValueError('Explicit archive SHA256 required')
    if archive.is_symlink() or not 0 < archive.stat().st_size <= MAX_ARCHIVE:
        raise ValueError('Archive exceeds transfer limit or is a link')
    if output.exists() or output.is_symlink() or output.parent.resolve() != output.parent.absolute():
        raise ValueError('Fresh destination under a real directory required')
    if sha(archive) != expected_sha256:
        raise ValueError('Archive SHA256 mismatch')
    # Validate the complete inventory before creating a destination. Never extractall.
    with tarfile.open(archive, 'r:*') as tar:
        members = []
        total = 0
        for m in tar:
            if len(members) >= MAX_FILES + 1:
                raise ValueError('Too many transfer members')
            name(m.name)
            if not m.isfile() or m.size < 0:
                raise ValueError('Only regular transfer files are permitted')
            total += m.size
            if total > MAX_TOTAL:
                raise ValueError('Expanded transfer exceeds limit')
            members.append(m)
        names = [m.name for m in members]
        if len(set(v.casefold() for v in names)) != len(names):
            raise ValueError('Duplicate transfer paths')
        for v in names:
            if any(v.startswith(other + '/') for other in names if other != v):
                raise ValueError('File/directory path conflict')
        by_name = {m.name: m for m in members}
        meta = by_name.get('transfer-manifest.json')
        if not meta or not 0 < meta.size <= 1024**2:
            raise ValueError('Missing or oversized transfer manifest')
        with tar.extractfile(meta) as stream:
            manifest_bytes = stream.read(1024**2 + 1)
        manifest = json.loads(manifest_bytes)
        records = manifest.get('files')
        if manifest.get('schema') != 'prowl-review-transfer-v1' or not isinstance(records, list) or len(records) > MAX_FILES:
            raise ValueError('Unsupported transfer manifest')
        declared = {}
        for row in records:
            path = name(row['path'])
            if (path in declared or path in ('transfer-manifest.json', 'import-receipt.json')
                    or type(row['bytes']) is not int or row['bytes'] < 0
                    or not isinstance(row['sha256'], str) or not HASH.fullmatch(row['sha256'])):
                raise ValueError('Invalid member declaration')
            declared[path] = row
        if set(declared) != set(names) - {'transfer-manifest.json'}:
            raise ValueError('Transfer inventory mismatch')
        for path, row in declared.items():
            if by_name[path].size != row['bytes']:
                raise ValueError('Declared member size differs')
            h = hashlib.sha256()
            with tar.extractfile(by_name[path]) as stream:
                for block in iter(lambda: stream.read(1024**2), b''):
                    h.update(block)
            if h.hexdigest() != row['sha256']:
                raise ValueError('Transfer member SHA256 mismatch')
        # All failures after this point retain an incomplete attempt without a receipt.
        output.mkdir(mode=0o700)
        for m in members:
            target = output / m.name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tar.extractfile(m) as source, target.open('xb') as dest:
                for block in iter(lambda: source.read(1024**2), b''):
                    dest.write(block)
            expected = hashlib.sha256(manifest_bytes).hexdigest() if m.name == meta.name else declared[m.name]['sha256']
            if sha(target) != expected:
                raise ValueError('Member changed during import')
    if sha(archive) != expected_sha256:
        raise ValueError('Archive changed during import')
    receipt = dict(schema='prowl-review-import-v1', archive_sha256=expected_sha256,
                   manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(), files=records,
                   scope='transport-integrity-only; inference and geometry not qualified')
    with (output/'import-receipt.json').open('x') as f:
        json.dump(receipt, f, indent=2)
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(json.dumps(import_archive(a.archive, a.output, expected_sha256=a.sha256)))
