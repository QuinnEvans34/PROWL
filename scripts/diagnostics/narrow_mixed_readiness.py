"""Disposable mixed-source engineering evidence; never scientific cohort admission."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BASE = Path('E:/PROWL/readiness/data-setup-20261010-a01')
OUT = Path('E:/PROWL/readiness/panorama-narrow-readiness-20261011-a01')
BACKUP = Path('C:/Users/quinn/PROWL-Backups/narrow-mixed-20261011-a01')
from src.training.experiment_config import sha256


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)


def ledger(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines()]


def reconcile():
    rows = ledger(BASE/'panorama-candidates.jsonl')
    audit = {r['study_id']: r for r in ledger(BASE/'panorama-ct-union-a01/cases.jsonl')}
    assert len(rows) == len(audit) == 2238
    imports = [r for r in rows if r['reference_standard'] in ('MSD_dataset', 'NIH_dataset')]
    counts = dict(Counter(r['reference_standard'] for r in imports))
    assert counts == {'MSD_dataset': 194, 'NIH_dataset': 80}
    assert all(r['disposition'] == 'excluded_declared_import' and not r['training_ready'] and
               audit[r['study_id']]['status'] == 'retained_prior_hold_or_exclusion' for r in imports)
    save(OUT/'exclusions.json', dict(counts=counts, ids=[r['study_id'] for r in imports],
        ct_payload_reads=0, prior_audit_sha256=sha256(BASE/'panorama-ct-union-a01/cases.jsonl')))
    qualification = read(BASE/'qualification.json')
    assert qualification['workers_reaped'] and qualification['exact_restore']
    assert qualification['pants_cache_cases'] == 1408 and qualification['pants_cache_failures'] == 0
    save(OUT/'pants-reuse.json', dict(qualification=qualification,
        qualification_sha256=sha256(BASE/'qualification.json'), machine_qualification_repeated=False,
        cache_rebuilt=False, full_evaluation_repeated=False))
    eligible = [r for r in rows if r['disposition'].startswith('expert_pdac') and
                audit[r['study_id']]['status'] == 'ct_content_pass_not_admitted']
    ordered = sorted(eligible, key=lambda r: audit[r['study_id']]['tensor_lesion_voxels'])
    selected = [ordered[i] for i in (0, len(ordered)//4, len(ordered)//2, 3*len(ordered)//4, len(ordered)-1)]
    save(OUT/'selection.json', dict(selection_rule='Five expert-PDAC tensor-lesion-size quantiles; focused engineering review only',
        eligible_before_QC_and_overlap=len(eligible), rows=selected, scientific_admission=False))


def prepare():
    import nibabel as nib
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.data.panorama_geometry import preprocess
    from src.data.segmenter_geometry_v2 import recipe
    from scripts.diagnostics.audit_panorama_setup import observation
    audit = {r['study_id']: r for r in ledger(BASE/'panorama-ct-union-a01/cases.jsonl')}
    results = []
    for row in read(OUT/'selection.json')['rows']:
        paths = [Path(row[k]['path']) for k in ('ct', 'label')]
        before = [observation(p) for p in paths]
        assert all(sha256(p) == row[k]['expected_sha256'] for k, p in zip(('ct', 'label'), paths))
        ct, mask = [nib.load(p) for p in paths]
        assert ct.shape == mask.shape and np.allclose(ct.affine, mask.affine, atol=1e-5, rtol=0)
        result = preprocess(ct.get_fdata(dtype=np.float32), mask.dataobj.get_unscaled(), ct.affine,
            recipe(tensor_shape=(144, 144, 144)),
            source_identity=dict(study_id=row['study_id'], ct_sha256=row['ct']['expected_sha256']), diagnosis='PDAC')
        assert result['mechanical_survival_pass'] and not result['lost_component_ids']
        assert result['geometry_sha256'] == audit[row['study_id']]['geometry_sha256']
        assert before == [observation(p) for p in paths]
        name = row['publisher_study_id']; target = result['target']; image = result['image']
        np.savez_compressed(OUT/(name+'.npz'), image=image[None].astype(np.float32), target=target)
        # The shared sampler outputs physical RAS, isotropic tensor grid, with explicit padding.
        # Show maximum lesion area on each axis and a second plane at the pancreas center.
        fig, axes = plt.subplots(2, 3, figsize=(12, 8))
        slices = []
        for j, code in enumerate((2, 1)):
            support = target == code
            for axis in range(3):
                plane = int(np.argmax(support.sum(axis=tuple(k for k in range(3) if k != axis))))
                sl = [slice(None)]*3; sl[axis] = plane; sl = tuple(sl); slices.append([code, axis, plane])
                ax = axes[j, axis]; ax.imshow(image[sl].T, origin='lower', cmap='gray', vmin=0, vmax=1, aspect='equal')
                for value, color in ((1, 'lime'), (2, 'red')):
                    field = target[sl].T == value
                    if field.any(): ax.contour(field, levels=[.5], colors=[color], linewidths=.7)
                ax.set_title(f'RAS axis {axis}, slice {plane}'); ax.axis('off')
        spacing = result['geometry']['transform']['effective_spacing_mm']
        fig.suptitle(f'{name}: actual optimizer crop, RAS isotropic {spacing[0]:.3f} mm\ngreen=machine pancreas; red=expert PDAC; not clinical QC')
        fig.tight_layout(); fig.savefig(OUT/(name+'.png'), dpi=110); plt.close(fig)
        record = dict(study_id=row['study_id'], subject_id=row['subject_id'], cache=str(OUT/(name+'.npz')),
            cache_sha256=sha256(OUT/(name+'.npz')), geometry=result['geometry'], geometry_sha256=result['geometry_sha256'],
            source=row, mechanical_survival_pass=True, lost_component_ids=[],
            tensor_lesion_voxels=int((target == 2).sum()), tensor_pancreas_voxels=int((target == 1).sum()),
            slices=slices, visual_review='pending', scientific_admission=False)
        results.append(record); save(OUT/(name+'.json'), record)
        print(json.dumps(dict(prepared=name, count=len(results))), flush=True)
    save(OUT/'prepared.json', results)


class MixedSmokeInputs:
    """Explicitly non-promotable adapter around checked PanTS and diagnostic PANORAMA batches."""
    def __init__(self, cfg, out=OUT):
        from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
        from src.data.manifest_records import canonical, digest
        self.pants = PreparedInputs(cfg, cfg['full_segmenter']['geometry'])
        self.out = out
        self.control = read(out/'smoke-control.json')
        assert self.control['domain'] == 'disposable_mixed_engineering_only'
        assert self.control['pants_control'] == self.pants.control
        self.pin = digest(canonical(self.control))

    def get(self, name, *, role, operation):
        import numpy as np
        from src.data import segmenter_full_batch_v1 as B
        if role not in ('train', 'validation') or operation != ('optimizer' if role == 'train' else 'evaluator'):
            raise ValueError('Protected smoke role/operation')
        if name not in self.control['train' if role == 'train' else 'validation']:
            raise ValueError('Outside frozen smoke members')
        if name in self.control['panorama']:
            if role != 'train': raise ValueError('PANORAMA cannot evaluate')
            r = self.control['panorama'][name]
            assert sha256(r['cache']) == r['cache_sha256']
            with np.load(r['cache'], allow_pickle=False) as data: x, y = data['image'], data['target']
        else:
            batch = self.pants.get(name, role=role, operation=operation)
            x, y = batch.checked(self.pants.pin, operation, name)
        return B.Batch(B._TOKEN, study_id=name, role=role, operation=operation,
            image=x, target=y, control_sha256=self.pin)


def smoke(cold=False):
    import torch
    from src.training import experiment_config as E
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from scripts.train_full_segmenter import session_config
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    from src.operations.full_training_platform import durable_replace
    cfg = E.load_experiment(str(BASE/'pants-admitted/smoke.yaml'))
    torch.set_num_threads(2)
    provider = MixedSmokeInputs(cfg)
    started = time.monotonic()
    if cold:
        state = torch.load(BACKUP/'saved.pt', map_location='cpu', weights_only=True)['session']
        expected = torch.load(OUT/'smoke/expected.pt', map_location='cpu', weights_only=True)['session']
        session = Session.restore(state, state['identity']); compare(session.state(), state, exact=True)
        row = session.update(provider); maxima = []; compare(session.state(), expected, maxima=maxima)
        report = dict(updates=[row], exact_restore=True, next_state_close=True, max_absolute_difference=max(maxima, default=0))
    else:
        c = session_config(cfg); c.update(max_steps=9, lr_horizon_steps=9)
        session = Session(c, provider.control, device='cuda', initialization=cfg['_experiment']['initialization'])
        rows = [session.update(provider) for _ in provider.control['train']]
        assert {r['member_id'] for r in rows} == set(provider.control['train'])
        atomic_checkpoint(OUT/'smoke/saved.pt', session, best_score=None, history_bytes=0)
        temp = BACKUP/'saved.partial'
        with (OUT/'smoke/saved.pt').open('rb') as src, temp.open('xb') as dst:
            shutil.copyfileobj(src, dst); dst.flush(); os.fsync(dst.fileno())
        assert sha256(temp) == sha256(OUT/'smoke/saved.pt')
        durable_replace(temp, BACKUP/'saved.pt')
        rows.append(session.update(provider))
        atomic_checkpoint(OUT/'smoke/expected.pt', session, best_score=None, history_bytes=0)
        # One unchanged development member exercises the mixed adapter, not a repeated 75-case qualification.
        evaluation = session.evaluate_case(provider, provider.control['validation'][0])
        report = dict(updates=rows, exposure=session.exposure, evaluation=evaluation,
            checkpoint_sha256=sha256(BACKUP/'saved.pt'), checkpoint_step=len(provider.control['train']))
    torch.cuda.synchronize()
    report.update(seconds=time.monotonic()-started, scientific_admission=False, promotable_model=False)
    save(OUT/'smoke'/('cold.json' if cold else 'producer.json'), report)


def freeze_smoke():
    from src.training import experiment_config as E
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    cfg = E.load_experiment(str(BASE/'pants-admitted/smoke.yaml'))
    pants = PreparedInputs(cfg, cfg['full_segmenter']['geometry'])
    reviews = read(OUT/'visual-review.json')
    records = read(OUT/'prepared.json')
    assert reviews['scope'] == 'engineering_only' and len(reviews['accepted_ids']) >= 2
    accepted = [r for r in records if r['study_id'] in reviews['accepted_ids']][:2]
    assert len(accepted) == 2
    assert len({r['subject_id'] for r in accepted}) == 2
    assert all(r['mechanical_survival_pass'] and not r['lost_component_ids'] and
        r['source']['disposition'].startswith('expert_pdac') for r in accepted)
    states = pants.control['target_states']
    names = [next(n for n in pants.control['train'] if states[n] == s) for s in ('positive', 'reference_empty')]
    panorama = {r['study_id']: r for r in accepted}
    names += list(panorama)
    save(OUT/'smoke-control.json', dict(domain='disposable_mixed_engineering_only', train=names,
        validation=pants.control['validation'][:1], pants_control=pants.control, panorama=panorama,
        target_states={**{n: states[n] for n in names if n in states}, **{n:'positive' for n in panorama}},
        scientific_admission=False, review_sha256=sha256(OUT/'visual-review.json')))


def main():
    p = argparse.ArgumentParser(); p.add_argument('stage', choices=['reconcile','prepare','freeze','producer','cold']); p.add_argument('--worker', action='store_true'); a=p.parse_args()
    if a.stage == 'reconcile': return reconcile()
    if a.stage == 'freeze': return freeze_smoke()
    if a.worker: return prepare() if a.stage == 'prepare' else smoke(a.stage == 'cold')
    from src.operations.full_training_platform import training_guard, watch_windows, require_ac
    from scripts.train_full_segmenter import tree_bytes
    if a.stage == 'producer':
        (OUT/'smoke').mkdir(); BACKUP.mkdir()
        assert OUT.stat().st_dev != BACKUP.stat().st_dev
    controls = [Path(__file__), ROOT/'src/data/panorama_geometry.py', ROOT/'src/data/panorama_setup.py', BASE/'panorama-candidates.jsonl']
    if a.stage != 'prepare':
        controls += [OUT/'smoke-control.json', OUT/'visual-review.json', BASE/'pants-admitted/smoke.yaml',
            ROOT/'src/training/segmenter_full_session_v1.py', ROOT/'src/data/segmenter_prepared_inputs_v1.py']
    pins = {str(path):sha256(path) for path in controls}
    save(OUT/(a.stage+'-request.json'),dict(pins=pins, scientific_admission=False, seconds=1800, rss_bytes=12*1024**3))
    last = [0.]
    def tick():
        if time.monotonic()-last[0]<10:return
        require_ac()
        for path in (OUT, Path('C:/Users/quinn/PROWL-Backups')):
            if shutil.disk_usage(path).free < 100*1024**3: raise RuntimeError('Storage floor')
        if tree_bytes(OUT)>4*1024**3: raise RuntimeError('Output cap')
        if BACKUP.exists() and tree_bytes(BACKUP)>1024**3: raise RuntimeError('Independent smoke backup cap')
        if any(sha256(path)!=value for path,value in pins.items()): raise RuntimeError('Producing code changed')
        last[0]=time.monotonic()
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        tick()
        with (OUT/(a.stage+'.log')).open('x') as log:
            child = subprocess.Popen([sys.executable, __file__, a.stage, '--worker'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2'))
            try: watch_windows(child, seconds=1800, rss_bytes=12*1024**3, tick=tick)
            finally: save(OUT/(a.stage+'-resources.json'), getattr(child,'duration_resources',{}))


if __name__ == '__main__': main()
