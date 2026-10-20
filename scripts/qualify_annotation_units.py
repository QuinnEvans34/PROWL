"""Explicit CT-linked unit derivation for hash-bound, exactly aligned NIfTI-1 masks.

Does not resample or edit voxel data. Production input validation stays strict.
"""
import gzip
import hashlib
import json
from pathlib import Path
import nibabel as nib
import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''):
            h.update(b)
    return h.hexdigest()


def derive(ct_path, mask_path, ct_sha, mask_sha, output):
    ct_path, mask_path, output = map(Path, (ct_path, mask_path, output))
    if output.exists() or output == mask_path or output == ct_path:
        raise ValueError('Output must be new')
    for p, expected in ((ct_path, ct_sha), (mask_path, mask_sha)):
        if p.stat().st_size > 64*1024**2 or digest(p) != expected:
            raise ValueError('Source identity or compressed budget')
    ct, mask = nib.load(ct_path), nib.load(mask_path)
    for obj in (ct, mask):
        n = int(np.prod(obj.shape))
        if (not isinstance(obj, nib.Nifti1Image) or len(obj.shape) != 3 or n > 32_000_000
                or n*max(4, obj.get_data_dtype().itemsize)+352 > 128*1024**2
                or not np.isfinite(obj.affine).all() or abs(np.linalg.det(obj.affine[:3,:3])) < 1e-12):
            raise ValueError('Unsupported geometry or decoded budget')
    if (ct.header.get_xyzt_units()[0] != 'mm' or mask.header.get_xyzt_units()[0] != 'unknown'
            or ct.shape != mask.shape or not np.array_equal(ct.affine, mask.affine)):
        raise ValueError('Cannot inherit units: CT/mm or exact grid or unknown-mask requirement')
    source_content, derived_content = hashlib.sha256(), hashlib.sha256()
    total = 0
    with gzip.open(mask_path, 'rb') as source, output.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as target:
            header = source.read(352)
            if len(header) != 352 or header[344:348] != b'n+1\x00' or header[123] & 7:
                raise ValueError('Unsupported NIfTI header')
            changed = bytearray(header)
            changed[123] = (header[123] & ~7) | 2
            source_content.update(header)
            derived_content.update(changed)
            target.write(changed)
            total += len(header)
            for b in iter(lambda: source.read(1024**2), b''):
                total += len(b)
                if total > 128*1024**2:
                    raise ValueError('Expanded stream budget')
                source_content.update(b)
                derived_content.update(b)
                target.write(b)
    check = nib.load(output)
    if check.header.get_xyzt_units()[0] != 'mm' or not np.array_equal(check.affine, mask.affine):
        raise ValueError('Derived geometry verification failed')
    if digest(ct_path) != ct_sha or digest(mask_path) != mask_sha:
        raise ValueError('Source changed during derivation')
    receipt = dict(schema='ct-linked-annotation-units-v1', basis='explicit inheritance from hash-bound exact-grid CT',
                   ct_sha256=ct_sha, source_sha256=mask_sha, derived_sha256=digest(output),
                   source_uncompressed_sha256=source_content.hexdigest(),
                   derived_uncompressed_sha256=derived_content.hexdigest(),
                   changed_byte=123, before=header[123], after=changed[123], uncompressed_bytes=total,
                   shape=list(ct.shape), affine=ct.affine.tolist(), voxel_payload_changed=False)
    output.with_name(output.name+'.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt
