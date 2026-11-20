#!/usr/bin/env python3
"""Prepare one explicitly selected, de-identified local NIfTI CT for review.

The package retains source voxel bytes and physical geometry. This command
does not contact a server, run a model, identify intensity units, or de-identify
the supplied image.
"""
import argparse
import gzip
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from tempfile import TemporaryDirectory

import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inference.on_demand import canonical, sha


MAX_COMPRESSED = 64 * 1024**2
MAX_DECODED = 128 * 1024**2
MAX_VOXELS = 32_000_000
CHUNK = 1024**2


def copy_bounded(source, destination, limit):
    copied = 0
    for chunk in iter(lambda: source.read(CHUNK), b''):
        copied += len(chunk)
        if copied > limit:
            raise ValueError('CT exceeds the local review file budget.')
        destination.write(chunk)
    if not copied:
        raise ValueError('CT file is empty.')


def validate_geometry(path):
    image = nib.load(path)
    shape = tuple(map(int, image.shape))
    if len(shape) != 3 or min(shape) < 2 or math.prod(shape) > MAX_VOXELS:
        raise ValueError('Expected a single CT volume within the review voxel budget.')
    if image.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('The CT header must declare millimeter spatial units.')
    affine = image.affine
    if (image.header['sform_code'] <= 0 and image.header['qform_code'] <= 0
            or not np.isfinite(affine).all()
            or not np.allclose(affine[3], [0, 0, 0, 1], rtol=0, atol=1e-6)
            or abs(np.linalg.det(affine[:3, :3])) < 1e-9):
        raise ValueError('The CT requires a valid three-dimensional spatial transform.')
    if (image.get_data_dtype().kind not in 'iuf' or image.get_data_dtype().itemsize > 8
            or image.dataobj.offset + math.prod(shape) * image.get_data_dtype().itemsize > path.stat().st_size):
        raise ValueError('Unsupported or incomplete scalar CT data.')
    for start in range(0, shape[2], 8):
        with np.errstate(over='ignore', invalid='ignore'):
            values = np.asarray(image.dataobj[..., start:start + 8], dtype=np.float32)
        if not np.isfinite(values).all():
            raise ValueError('The CT contains nonfinite or out-of-range intensities.')
    return {'shape': shape, 'affine': affine.tolist(), 'units': 'mm'}


def prepare(source, output, *, study_id, deidentified):
    if not deidentified:
        raise ValueError('Select only an already de-identified research CT.')
    if not isinstance(study_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', study_id):
        raise ValueError('Use a research study identifier with letters, numbers, dashes, or underscores.')
    source, output = map(Path, (source, output))
    compressed = source.name.endswith('.nii.gz')
    if not compressed and not source.name.endswith('.nii'):
        raise ValueError('Select one local .nii or .nii.gz file.')
    if output.exists() or output.is_symlink():
        raise FileExistsError('Select a new output directory.')

    with TemporaryDirectory(prefix='.prowl-ct-', dir=output.parent) as temp:
        staging = Path(temp)
        plain, packed = staging / 'ct.nii', staging / 'ct.nii.gz'
        selected = packed if compressed else plain
        limit = MAX_COMPRESSED if compressed else MAX_DECODED
        # No device files, FIFOs, or symlink substitution. The producer uses
        # only this chosen source and never discovers adjacent files.
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as original, selected.open('xb') as dest:
            info = os.fstat(original.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
                raise ValueError('Expected a regular CT file within the local review file budget.')
            copy_bounded(original, dest, limit)
            final = os.fstat(original.fileno())
            if (info.st_size, info.st_mtime_ns) != (final.st_size, final.st_mtime_ns):
                raise ValueError('The selected CT changed while it was copied.')
        source_sha = sha(selected)
        if compressed:
            with gzip.open(packed, 'rb') as decoded, plain.open('xb') as dest:
                copy_bounded(decoded, dest, MAX_DECODED)

        geometry = validate_geometry(plain)
        if not compressed:
            with plain.open('rb') as original, packed.open('xb') as dest:
                with gzip.GzipFile(filename='', fileobj=dest, mode='wb', mtime=0) as encoded:
                    copy_bounded(original, encoded, MAX_DECODED)
            if packed.stat().st_size > MAX_COMPRESSED:
                raise ValueError('The packed CT exceeds the local review file budget.')

        manifest = {
            'schema_version': 'local-ct-intake-v1',
            'status': 'ct_ready',
            'study_id': study_id,
            'source': {'format': 'nifti-gzip' if compressed else 'nifti', 'sha256': source_sha},
            'ct': {'uri': 'ct.nii.gz', 'content_sha256': sha(packed), 'bytes': packed.stat().st_size},
            'geometry': geometry,
            'ct_intensity_units': 'unverified',
        }
        (staging / 'manifest.json').write_bytes(canonical(manifest))
        output.mkdir(mode=0o700, exist_ok=False)
        try:
            packed.rename(output / 'ct.nii.gz')
            (staging / 'manifest.json').rename(output / 'manifest.json')
        except OSError:
            (output / 'ct.nii.gz').unlink(missing_ok=True)
            output.rmdir()
            raise
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ct', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--study-id', required=True)
    parser.add_argument('--deidentified', action='store_true', help='Confirm the supplied CT is already de-identified.')
    args = parser.parse_args()
    try:
        manifest = prepare(args.ct, args.output, study_id=args.study_id, deidentified=args.deidentified)
    except (ValueError, OSError, EOFError, nib.filebasedimages.ImageFileError) as error:
        parser.exit(1, f'CT intake failed: {error}\n')
    print(json.dumps(manifest))
