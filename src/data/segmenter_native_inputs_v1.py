"""Role-bound, on-demand native windows; original caches are provenance only."""
import csv
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_native_windows_v1 import POLICY, geometry, orient, extract, sample_origin, coverage_origins
from src.data.manifest_records import canonical, digest
from src.data import segmenter_full_batch_v1 as boundary
from src.training.experiment_config import sha256


def anchors(mask):
    labels, count = ndimage.label(mask, structure=np.ones((3, 3, 3)))
    result = []
    for i, box in enumerate(ndimage.find_objects(labels), 1):
        points = np.argwhere(labels[box] == i)
        point = points[np.argmin(((points-points.mean(0))**2).sum(1))]
        result.append((point + [s.start for s in box]).tolist())
    return result


class NativeInputs:
    def __init__(self, *, manifest, review, train_file, dev_file):
        paths = dict(manifest=Path(manifest), review=Path(review), train_file=Path(train_file), dev_file=Path(dev_file))
        self.review = json.loads(paths['review'].read_text())
        self.root = Path(self.review['prepared_cache']['root'])
        old = json.loads((self.root/'control.json').read_text())
        self.observations = old['observations']
        train, dev = paths['train_file'].read_text().split(), paths['dev_file'].read_text().split()
        if not train or not dev or len(set(train+dev)) != len(train+dev):
            raise ValueError('Distinct, nonempty roles required')
        if not set(train).issubset(old['train']) or not set(dev).issubset(old['validation']):
            raise ValueError('Protected role change')
        if sha256(paths['manifest']) != old['manifest_sha256']:
            raise ValueError('Manifest changed')
        with paths['manifest'].open(newline='') as f:
            self.rows = {r['case_id']: r for r in csv.DictReader(f) if r['case_id'] in set(train+dev)}
        if set(self.rows) != set(train+dev): raise ValueError('Missing manifest member')
        self.control = dict(version='native-inputs-1', train=train, validation=dev, policy=POLICY,
                            bindings={k: sha256(p) for k, p in paths.items()},
                            source_control_sha256=sha256(self.root/'control.json'))
        self.pin = digest(canonical(self.control))
        self.cache = None

    def check_role(self, name, role, operation):
        if role not in ('train', 'validation') or operation not in ('optimizer', 'evaluator', 'audit'):
            raise ValueError('Unsupported role/operation')
        if operation == 'optimizer' and role != 'train': raise ValueError('Development cannot optimize')
        if name not in self.control['train' if role == 'train' else 'validation']:
            raise ValueError('Case outside bound role')

    def load(self, name, *, role, operation='audit'):
        self.check_role(name, role, operation)
        meta_path = self.root/(name+'.json')
        if sha256(meta_path) != self.review['prepared_cache']['members'][name]['metadata_sha256']:
            raise ValueError('Original metadata changed')
        meta = json.loads(meta_path.read_text())
        row = self.rows[name]
        objects = {}
        for kind in ('ct', 'pancreas', 'lesion'):
            path = Path(row[kind+'_path']); s = path.stat()
            observed = dict(bytes=s.st_size, modified_ns=s.st_mtime_ns, inode=s.st_ino, device=s.st_dev)
            if observed != self.observations[name][kind]:
                raise ValueError(f'Source observation changed: {name}/{kind}')
            # Reuse prior full CT hash and finite audit, tied to unchanged file observations.
            # Labels are small and rechecked byte-for-byte for the new supervision path.
            if kind != 'ct' and sha256(path) != meta['source_sha256'][kind]:
                raise ValueError('Label identity changed')
            objects[kind] = nib.load(path)
        ct = objects['ct']; r = geometry(ct.shape, ct.affine)
        if np.prod(ct.shape, dtype=np.int64) > 256000000: raise ValueError('Source voxel cap')
        if ct.shape != tuple(meta['transform']['source_shape']) or not np.allclose(ct.affine, meta['transform']['source_affine'], atol=1e-5, rtol=0):
            raise ValueError('Original source geometry changed')
        masks = {}
        for kind in ('pancreas', 'lesion'):
            obj = objects[kind]
            if obj.shape != ct.shape or not np.allclose(obj.affine, ct.affine, atol=1e-5, rtol=0):
                raise ValueError('Image-mask geometry mismatch')
            p = obj.dataobj
            masks[kind], _ = target_content(p.get_unscaled(), dict(slope=float(p.slope), intercept=float(p.inter)))
        image = ct.get_fdata(dtype=np.float32, caching='unchanged')
        if not np.isfinite(image).all(): raise ValueError('Nonfinite CT')
        image = orient(image, r)
        np.clip(image, -100, 250, out=image); image += 100; image /= 350
        pancreas = orient(masks['pancreas'], r)
        lesion = orient(masks['lesion'], r)
        if not pancreas.any(): raise ValueError('Empty provided pancreas')
        expected_positive = self.review['target_states'][name] == 'positive'
        if bool(lesion.any()) != expected_positive: raise ValueError('Target state changed')
        target = pancreas.astype(np.uint8); target[lesion != 0] = 2
        support = lesion if expected_positive else pancreas
        centers = anchors(support)
        if not expected_positive: centers = centers[:1]  # Full-organ coverage is provided separately, not deleted.
        coverage = coverage_origins(support)
        return dict(name=name, image=image, target=target, geometry=r, centers=centers, coverage=coverage,
                    positive=expected_positive, original_lesion=masks['lesion'], original_pancreas=masks['pancreas'],
                    source_sha256=meta['source_sha256'], old_transform=meta['transform'],
                    metadata_sha256=sha256(meta_path))

    def window(self, name, *, role, operation, visit, seed):
        self.check_role(name, role, operation)
        if operation != 'optimizer': raise ValueError('Inference must use full-field tiles, never target anchors')
        case = self.load(name, role=role, operation=operation)
        origin, kind = sample_origin(case['target'].shape, case['centers'], visit=visit, seed=seed, case_id=name, coverage=case['coverage'])
        image, transform = extract(case['image'], origin)
        target, _ = extract(case['target'], origin)
        return image[None], target, transform, dict(origin=list(origin), kind=kind, visit=visit,
                                                   geometry=case['geometry'])


class OptimizerWindows:
    """Stateless per-update view. Session checkpoint exposure determines next patch."""
    def __init__(self, provider, session):
        self.provider, self.session, self.control = provider, session, provider.control
        self.trace = None

    def get(self, name, *, role, operation):
        from src.training.segmenter_augmentation_v1 import augment
        image, target, transform, trace = self.provider.window(name, role=role, operation=operation,
            visit=self.session.exposure[name], seed=self.session.config['seed'])
        image, target, augmentation = augment(image, target, transform, seed=self.session.config['seed'],
            update=self.session.step+1, case_id=name)
        self.trace = dict(window=trace, augmentation=augmentation)
        return boundary.Batch(boundary._TOKEN, study_id=name, role=role, operation=operation,
            image=image, target=target, control_sha256=self.provider.pin)
