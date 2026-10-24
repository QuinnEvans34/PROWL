"""Explicit reader for corrected target derivatives, not a scientific input provider."""
import json
from pathlib import Path
import numpy as np
from src.training.experiment_config import sha256
from src.data.pants_errata_v1 import EXPECTED, VERSION


def load_target(root, case_id, *, role, manifest_sha256, overlay_sha256):
    root = Path(root)
    if role != 'train' or case_id not in EXPECTED:
        raise ValueError('Only corrected training members are admitted')
    manifest = root / 'manifest.json'
    if sha256(manifest) != manifest_sha256:
        raise ValueError('Manifest identity changed')
    data = json.loads(manifest.read_text())
    if (data['version'] != VERSION or data['overlay_sha256'] != overlay_sha256
            or set(data['members']) != set(EXPECTED)):
        raise ValueError('Correction identity or membership changed')
    row = data['members'][case_id]
    array, metadata = root / (case_id + '.npz'), root / (case_id + '.json')
    if sha256(array) != row['target_sha256'] or sha256(metadata) != row['metadata_sha256']:
        raise ValueError('Corrected cache member changed')
    small = json.loads(metadata.read_text())
    if (small['name'] != case_id or small['positive'] is not False
            or small['lesion_voxels'] != 0
            or small['label_revision_sha256'] != overlay_sha256):
        raise ValueError('Corrected metadata mismatch')
    with np.load(array, allow_pickle=False) as payload:
        if payload.files != ['target']:
            raise ValueError('Unexpected target payload')
        target = np.ascontiguousarray(payload['target'])
    if (target.dtype != np.uint8 or target.shape != tuple(small['geometry']['shape'])
            or not np.isin(target, [0, 1]).all()
            or int(target.sum()) != small['pancreas_source_voxels']):
        raise ValueError('Corrected target mismatch')
    return target, small
