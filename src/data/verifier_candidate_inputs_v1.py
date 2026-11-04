"""Inference-only reserved patient access. Lesion labels are a separate fit-only read."""
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from src.data.segmenter_native_inputs_v1 import NativeInputs
from src.data.segmenter_native_windows_v1 import geometry, orient
from src.data.segmenter_pancreas_region_v1 import oriented_box
from src.data.segmenter_content_v1 import target_content
from src.training.experiment_config import sha256

ROLES = ('verifier_fit', 'verifier_tune', 'verifier_calibration')

def partition_roles(partition):
    roles = partition['roles']
    if set(roles) != {'generator_train', *ROLES}:
        raise ValueError('Unknown partition roles')
    all_ids = sum((list(v) for v in roles.values()), []) + list(partition['development'])
    if len(set(all_ids)) != len(all_ids) or any(not v for v in roles.values()):
        raise ValueError('Overlapping or empty roles')
    return {n: role for role in ROLES for n in roles[role]}

class CandidateInputs:
    def __init__(self, *, partition, partition_sha256, expected_partition_sha256, **source):
        if partition_sha256 != expected_partition_sha256:
            raise ValueError('Partition identity mismatch')
        self.roles = partition_roles(partition)
        base = NativeInputs(**source)  # Metadata admission only, no voxel reads.
        if set(base.control['train']) != set(sum(partition['roles'].values(), [])) or set(base.control['validation']) != set(partition['development']):
            raise ValueError('Source partition membership mismatch')
        self.root, self.review = base.root, base.review
        self.rows = {n: base.rows[n] for n in self.roles}
        self.observations = {n: base.observations[n] for n in self.roles}

    def check(self, name, role, *, labels=False):
        if role not in ROLES or self.roles.get(name) != role:
            raise ValueError('Protected or mismatched inference role')
        if labels and role != 'verifier_fit':
            raise ValueError('Only fit labels available during representation preparation')

    def metadata(self, name, role):
        self.check(name, role)
        path = self.root/(name+'.json')
        if sha256(path) != self.review['prepared_cache']['members'][name]['metadata_sha256']:
            raise ValueError('Source metadata changed')
        return json.loads(path.read_text())

    def _object(self, name, kind, meta):
        path = Path(self.rows[name][kind+'_path']); s = path.stat()
        observed = dict(bytes=s.st_size, modified_ns=s.st_mtime_ns, inode=s.st_ino, device=s.st_dev)
        if observed != self.observations[name][kind]:
            raise ValueError('Source observation changed')
        if kind != 'ct' and sha256(path) != meta['source_sha256'][kind]:
            raise ValueError('Mask identity changed')
        return nib.load(path)

    @staticmethod
    def _mask(obj):
        p = obj.dataobj
        return target_content(p.get_unscaled(), dict(slope=float(p.slope), intercept=float(p.inter)))[0]

    def load(self, name, *, role):
        meta = self.metadata(name, role)
        ct = self._object(name, 'ct', meta)
        pancreas = self._object(name, 'pancreas', meta)
        if np.prod(ct.shape, dtype=np.int64) > 256000000:
            raise ValueError('Source voxel cap')
        if ct.shape != tuple(meta['transform']['source_shape']) or not np.allclose(ct.affine, meta['transform']['source_affine'], rtol=0, atol=1e-5):
            raise ValueError('Source geometry changed')
        if pancreas.shape != ct.shape or not np.allclose(pancreas.affine, ct.affine, rtol=0, atol=1e-5):
            raise ValueError('Pancreas alignment')
        mask = self._mask(pancreas)
        if not mask.any():
            raise ValueError('Empty provided pancreas')
        parent = geometry(ct.shape, ct.affine)
        low, high = oriented_box(mask, parent)
        slices = tuple(slice(int(l), int(h)) for l,h in zip(low,high))
        image = ct.get_fdata(dtype=np.float32, caching='unchanged')
        if not np.isfinite(image).all():
            raise ValueError('Nonfinite CT')
        image = orient(image, parent)
        np.clip(image, -100, 250, out=image); image += 100; image /= 350
        affine = np.array(parent['affine']); affine[:3,3] = (affine@[*low,1])[:3]
        local = geometry((high-low).tolist(), affine)
        if local['forward'] != [[0.,1.],[1.,1.],[2.,1.]]:
            raise ValueError('Unexpected region orientation')
        return dict(name=name, role=role, image=np.ascontiguousarray(image[slices]),
            geometry=local, parent_geometry=parent, region_low=low.tolist(), region_high=high.tolist(),
            source_sha256={k:meta['source_sha256'][k] for k in ('ct','pancreas')})

    def fit_truth(self, name, *, role, parent_geometry):
        self.check(name, role, labels=True)
        meta = self.metadata(name, role); obj = self._object(name, 'lesion', meta)
        if obj.shape != tuple(parent_geometry['source_shape']) or not np.allclose(obj.affine,parent_geometry['source_affine'],rtol=0,atol=1e-5):
            raise ValueError('Lesion alignment')
        return self._mask(obj).astype(bool)
