"""Package an existing autonomous result for private native-grid display; no inference."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import nibabel as nib
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def prepare(ct_path, result_path, output):
    ct_path, result_path, output = map(Path, (ct_path, result_path, output))
    result = json.loads(result_path.read_text())
    evidence = result['evidence']
    identity = evidence['source_identity']
    pred_path = result_path.parent / 'prediction.nii.gz'
    if (result['status'] != 'complete' or result['reference_inputs_used'] is not False
            or evidence['reference_inputs_used'] is not False
            or result['case_id'] != identity['study_id']):
        raise ValueError('Requires a completed CT-only result with matching study identity')
    if sha(ct_path) != identity['ct_sha256'] or sha(pred_path) != result['prediction_sha256']:
        raise ValueError('CT or prediction content hash mismatch')
    ct, pred = nib.load(ct_path), nib.load(pred_path)
    transform = evidence['localizer_transform']
    if (len(ct.shape) != 3 or ct.shape != pred.shape or np.prod(ct.shape) > 96000000
            or list(ct.shape) != transform['source_shape']
            or not np.isfinite(ct.affine).all()
            or not np.allclose(ct.affine, pred.affine, atol=1e-5, rtol=0)
            or not np.allclose(ct.affine, transform['source_affine'], atol=1e-5, rtol=0)):
        raise ValueError('Native CT/prediction geometry mismatch')
    if ct.header.get_xyzt_units()[0] != 'mm' or pred.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('Native display requires explicit millimeter headers')
    labels = np.asanyarray(pred.dataobj)
    if not np.isin(labels, [0, 1, 2]).all():
        raise ValueError('Prediction must use background/pancreas/lesion labels 0/1/2')
    # A fresh output directory prevents mixing files from separate packages.
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(ct_path, output / 'ct.nii.gz')
    shutil.copyfile(pred_path, output / 'prediction.nii.gz')
    def ref(path):
        return dict(uri=path.name, content_sha256=sha(path), bytes=path.stat().st_size)
    manifest = dict(schema_version='saved-prediction-view-v1', case_id=result['case_id'],
        prediction_mode='autonomous', status='completed_with_warnings',
        files=dict(ct=ref(output/'ct.nii.gz'), pred=ref(output/'prediction.nii.gz')),
        geometry=dict(shape=list(ct.shape), affine=ct.affine.tolist(), units='mm'),
        model_sha256=evidence['model_sha256'], result_sha256=sha(result_path),
        inference_evidence_sha256=hashlib.sha256(json.dumps(evidence, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        ct_window=[-100, 300], labels={'0':'background','1':'pancreas','2':'lesion'},
        warnings=['Development demonstration. Predictions are unvalidated and require review.',
                  'This selected case does not establish representative performance or a diagnosis.'],
        reference_inputs_used=False)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ct', required=True)
    p.add_argument('--result', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    manifest = prepare(args.ct, args.result, args.output)
    print(json.dumps({'case_id':manifest['case_id'], 'geometry':manifest['geometry'], 'files':manifest['files']}))
