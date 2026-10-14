"""Supervised native development evaluation; never reads test arrays or optimizes weights."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def worker(a):
    import nibabel as nib
    import numpy as np
    import torch
    from src.training import experiment_config as E
    from src.training.segmenter_full_session_v1 import Session, identity_for
    from src.training.pants_native_evaluation import native_metrics
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.data.segmenter_full_inputs_v1 import Inputs
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_geometry_v2 import restore_codes
    from src.data.source_inventory_records import require
    from src.data.manifest_records import canonical
    from scripts.train_full_segmenter import session_config
    cfg = E.load_experiment(a.experiment)
    p = PreparedInputs(cfg, cfg['full_segmenter']['geometry'])
    require(E.sha256(a.checkpoint) == a.sha256, 'Checkpoint hash mismatch')
    saved = torch.load(a.checkpoint, map_location='cpu', weights_only=True)
    identity = identity_for(session_config(cfg), p.control, cfg['device'], cfg['_experiment']['initialization'])
    # Launched runs bind the copied cohort review; it must be byte-identical to the supplied config review.
    s = Session.restore(saved['session'], identity)
    torch.set_num_threads(2)
    records = []
    with (a.output/'cases.jsonl').open('x') as journal:
        names = p.control['validation'][:a.qualification_limit] if a.qualification_limit else p.control['validation']
        for name in names:
            _, x, _ = s._batch(p, name, 'validation', 'evaluator')
            meta = json.loads((p.root/(name+'.json')).read_text())
            with torch.no_grad(), s.rng_scope():
                s.model.eval()
                logits = s.model(x[None].to(s.device))
                require(torch.isfinite(logits).all().item(), 'Nonfinite predictions')
                codes = logits.argmax(1)[0].cpu().numpy().astype(np.uint8)
            restored = restore_codes(codes, meta['transform'], trusted_record_sha256=meta['transform_sha256'])
            labels = {}
            affine = np.asarray(meta['transform']['source_affine'])
            for kind in ('pancreas', 'lesion'):
                path = Path(p.rows[name][kind+'_path'])
                require(E.sha256(path) == meta['source_sha256'][kind], 'Native reference changed')
                obj = nib.load(path)
                require(obj.shape == restored.shape and np.allclose(obj.affine, affine, atol=1e-5, rtol=0), 'Native label geometry mismatch')
                proxy = obj.dataobj
                labels[kind], _ = target_content(proxy.get_unscaled(),
                    dict(slope=float(proxy.slope), intercept=float(proxy.inter)))
                require(Inputs.observe(path) == p.source['observations'][name][kind], 'Reference changed during evaluation')
            row = dict(case_id=name, step=s.step, metrics=native_metrics(restored, labels['pancreas'], labels['lesion'], affine))
            nib.save(nib.Nifti1Image(restored, affine), a.output/(name+'.nii.gz'))
            journal.write(json.dumps(row, allow_nan=False)+'\n'); journal.flush()
            records.append(row)
    (a.output/'report.json').write_bytes(canonical(dict(scope='native_development_provided_pancreas',
        checkpoint_sha256=a.sha256, identity_sha256=s.identity_pin, step=s.step, cases=records,
        complete_development_cohort=len(records)==len(p.control['validation']),
        test_reads=0, optimizer_updates=0, detection_rule='26_connected_reference_component_any_overlap',
        prediction_rule='three_class_argmax_no_postprocessing')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--qualification-limit', type=int)
    a = parser.parse_args()
    if a.qualification_limit is not None and a.qualification_limit < 1: raise ValueError('Positive qualification limit required')
    if a.worker: return worker(a)
    from src.operations.full_training_platform import training_guard, watch_windows, require_ac
    a.output.mkdir(parents=True, exist_ok=False)
    def tick():
        require_ac()
        for drive in (a.output, Path('C:/')):
            if shutil.disk_usage(drive).free < 100*1024**3: raise RuntimeError('Storage floor')
        if sum(f.stat().st_size for f in a.output.rglob('*') if f.is_file()) > 4*1024**3:
            raise RuntimeError('Evaluation output limit')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        with (a.output/'worker.log').open('x') as log:
            p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), *sys.argv[1:], '--worker'],
                                 stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            try: watch_windows(p, seconds=3600, rss_bytes=12*1024**3, tick=tick)
            finally: (a.output/'resources.json').write_text(json.dumps(getattr(p, 'duration_resources', {}), indent=2))


if __name__ == '__main__': main()
