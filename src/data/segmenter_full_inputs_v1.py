"""On-demand full-cohort inputs through the capstone physical-geometry pipeline."""
import csv
import hashlib
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np

from src.data import segmenter_geometry_v2 as geometry
from src.data import segmenter_content_v1 as content
from src.data import segmenter_training_inputs_v1 as boundary
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.training.experiment_config import ids, resolve, sha256


class Inputs:
    def __init__(self, cfg, recipe, *, cache_dir=None, audit_only=False):
        spec = cfg['_experiment']; cohort = spec['cohort']
        self.audit_only = audit_only
        review = {} if audit_only else json.loads(resolve(cohort['review']).read_text())
        self.recipe = recipe; geometry.validate_recipe(recipe)
        with resolve(cohort['manifest']).open(newline='') as stream:
            records = list(csv.DictReader(stream))
        self.rows = {r['case_id']: r for r in records}
        require(len(records) == len(self.rows), 'Duplicate manifest rows')
        train, dev = ids(resolve(cohort['train_ids'])), ids(resolve(cohort['development_ids']))
        selected = train + dev
        self.states = ({name: 'positive' if self.rows[name]['historical_has_lesion']=='True'
                       else 'reference_empty' for name in selected} if audit_only else review.get('target_states', {}))
        require(set(self.states) == set(selected) and all(v in ('positive', 'verified_negative')
                or (audit_only and v=='reference_empty') for v in self.states.values()),
                'Full cohort needs explicit reviewed target states; empty is not negative')
        self.observations = {}
        for name in selected:
            self.observations[name] = {}
            for kind in ('ct', 'pancreas', 'lesion'):
                p = Path(self.rows[name][kind + '_path'])
                require(p.is_absolute() and p.is_file() and not p.is_symlink(), 'Missing/unsafe input file')
                self.observations[name][kind] = self.observe(p)
        self.control = dict(version='segmenter-full-inputs-1', domain='candidate_audit_only' if audit_only else 'reviewed_full_cohort',
            train=train, validation=dev, target_states=self.states,
            manifest_sha256=sha256(resolve(cohort['manifest'])), review_sha256=None if audit_only else sha256(resolve(cohort['review'])),
            geometry=recipe, observations=self.observations)
        self.pin = digest(canonical(self.control))
        self.cache = Path(cache_dir) / self.pin if cache_dir else None
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=False)
            (self.cache/'control.json').write_bytes(canonical(self.control))

    @staticmethod
    def observe(path):
        s = path.stat()
        return dict(bytes=s.st_size, modified_ns=s.st_mtime_ns, inode=s.st_ino, device=s.st_dev)

    def _unchanged(self, name):
        for kind, expected in self.observations[name].items():
            require(self.observe(Path(self.rows[name][kind+'_path'])) == expected, 'Source file changed during run')

    def prepare(self, name):
        arrays, affines, hashes = {}, {}, {}
        self._unchanged(name)
        for kind in ('ct', 'pancreas', 'lesion'):
            path = Path(self.rows[name][kind+'_path'])
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024**2), b''): h.update(chunk)
            hashes[kind] = h.hexdigest()
            obj = nib.load(str(path))
            geometry.canonical_geometry(list(obj.shape), obj.affine, self.recipe)
            affines[kind] = obj.affine
            if kind == 'ct': arrays[kind] = obj.get_fdata(dtype=np.float32)
            else:
                proxy = obj.dataobj
                arrays[kind], _ = content.target_content(proxy.get_unscaled(),
                    dict(slope=float(proxy.slope), intercept=float(proxy.inter)))
        self._unchanged(name)
        require(all(a.shape == arrays['ct'].shape for a in arrays.values()) and
            all(np.allclose(a, affines['ct'], atol=1e-5, rtol=0) for a in affines.values()),
            'CT/label grids do not match')
        require(np.isfinite(arrays['ct']).all(), 'Nonfinite CT')
        result = geometry.preprocess(arrays['ct'], arrays['pancreas'], arrays['lesion'], affines['ct'],
            self.recipe, source_identity=dict(study_id=name, ct_sha256=hashes['ct']),
            lesion_target_state=self.states[name])
        require(result['fidelity']['mechanical_survival_pass'], 'Geometry loses lesion component/pancreas support')
        metadata = dict(case_id=name, source_sha256=hashes, transform=result['transform'],
            transform_sha256=result['transform_sha256'], fidelity=result['fidelity'], control_sha256=self.pin)
        return result['image'][None].astype(np.float32), result['target'].astype(np.uint8), metadata

    def get(self, name, *, role, operation):
        require(not self.audit_only or operation=='evaluator', 'Candidate audit cannot supply optimizer inputs')
        require(role in ('train', 'validation') and operation in ('optimizer', 'evaluator')
            and name in self.control['train' if role == 'train' else 'validation']
            and (operation != 'optimizer' or role == 'train'), 'Protected input role violation')
        self._unchanged(name)
        path = self.cache / (name + '.npz') if self.cache else None
        if path and path.exists():
            meta = json.loads(path.with_suffix('.json').read_text())
            require(meta['control_sha256'] == self.pin and meta['case_id'] == name and
                sha256(path) == meta['cache_sha256'], 'Derived cache identity mismatch')
            with np.load(path, allow_pickle=False) as data: x, y = data['image'], data['target']
        else:
            x, y, meta = self.prepare(name)
            if path:
                temporary = path.with_suffix('.tmp')
                with temporary.open('xb') as stream:
                    np.savez(stream, image=x, target=y); stream.flush(); os.fsync(stream.fileno())
                os.replace(temporary, path)
                meta['cache_sha256'] = sha256(path)
                path.with_suffix('.json').write_bytes(canonical(meta))
        return boundary.Batch(boundary._TOKEN, study_id=name, role=role, operation=operation,
                              image=x, target=y, control_sha256=self.pin)
