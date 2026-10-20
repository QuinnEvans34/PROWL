#!/usr/bin/env python3
"""Audit a retained assisted package without inference, mutation or measurement promotion."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inference.boundary_audit import audit_boundary


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit_package(package, assistance):
    manifest = json.loads((package / 'manifest.json').read_text())
    if manifest.get('schema_version') != 'assisted-prediction-view-v1':
        raise ValueError('Expected an assisted native package')
    for key, filename in [('ct', 'ct.nii.gz'), ('pred', 'prediction.nii.gz'),
                          ('evidence', 'evidence.json'), ('result', 'result.json')]:
        pin = manifest['files'][key]
        p = package / filename
        if pin['uri'] != filename or p.stat().st_size != pin['bytes'] or digest(p) != pin['content_sha256']:
            raise ValueError(f'Package hash/size mismatch: {key}')
    if digest(assistance) != manifest['assistance_sha256']:
        raise ValueError('Assistance hash mismatch')
    evidence = json.loads((package / 'evidence.json').read_text())
    if (evidence['assistance']['sha256'] != manifest['assistance_sha256']
            or evidence['prediction_id'] != manifest['prediction_id']
            or evidence['model_sha256'] != manifest['model_sha256']
            or evidence['source_identity']['ct_sha256'] != manifest['files']['ct']['content_sha256']):
        raise ValueError('Evidence identity mismatch')
    pred = nib.load(package / 'prediction.nii.gz')
    ref = nib.load(assistance)
    ct = nib.load(package / 'ct.nii.gz')  # Header only; no CT array needed.
    g = manifest['geometry']
    for img in (pred, ref, ct):
        if (len(img.shape) != 3 or np.prod(img.shape) > 32_000_000
                or list(img.shape) != g['shape'] or img.header.get_xyzt_units()[0] != 'mm'
                or not np.allclose(img.affine, g['affine'], atol=1e-5, rtol=0)):
            raise ValueError('Geometry/units mismatch')
    result = audit_boundary(np.asanyarray(pred.dataobj), np.asanyarray(ref.dataobj),
                            pred.affine, evidence['reconstruction']['native_box'])
    result['identity'] = {k: manifest[k] for k in ('prediction_id', 'request_identity', 'model_sha256', 'assistance_sha256')}
    result['identity']['package_files'] = manifest['files']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--assistance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit_package(args.package, args.assistance)
    with args.output.open('x') as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write('\n')
    print(json.dumps({name: {c: {k: v for k, v in r.items() if k != 'components'}
                           for c, r in t['connectivity'].items()}
                      for name, t in result['targets'].items()}, indent=2))
