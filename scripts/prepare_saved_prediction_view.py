"""Package an existing autonomous result for private native-grid display; no inference."""
import argparse
import hashlib
import json
import math
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


def prepare(ct_path, result_path, output, *, measurement_provenance=False):
    ct_path, result_path, output = map(Path, (ct_path, result_path, output))
    if measurement_provenance and result_path.stat().st_size > 1024**2:
        raise ValueError('Native measurement provenance exceeds the preview budget')
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
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
    if (len(ct.shape) != 3 or ct.shape != pred.shape or math.prod(ct.shape) > 96000000
            or list(ct.shape) != transform['source_shape']
            or not np.isfinite(ct.affine).all()
            or not np.allclose(ct.affine, pred.affine, atol=1e-5, rtol=0)
            or not np.allclose(ct.affine, transform['source_affine'], atol=1e-5, rtol=0)):
        raise ValueError('Native CT/prediction geometry mismatch')
    if ct.header.get_xyzt_units()[0] != 'mm' or pred.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('Native display requires explicit millimeter headers')
    if measurement_provenance and (math.prod(ct.shape) > 32000000
            or max(ct_path.stat().st_size, pred_path.stat().st_size) > 64*1024**2
            or max(ct.header.get_data_dtype().itemsize, pred.header.get_data_dtype().itemsize)*math.prod(ct.shape) + 352 > 128*1024**2):
        raise ValueError('Native measurement package exceeds the bounded preview budget')
    labels = np.asanyarray(pred.dataobj)
    if not np.isin(labels, [0, 1, 2]).all():
        raise ValueError('Prediction must use background/pancreas/lesion labels 0/1/2')
    evidence_bytes = json.dumps(evidence, sort_keys=True, separators=(',', ':')).encode()
    if measurement_provenance:
        plan = evidence.get('region_plan', {})
        t = plan.get('transform', {})
        if (evidence.get('component') != 'autonomous-cascade-v1'
                or plan.get('component') != 'segmenter-predicted-roi-v2'
                or t.get('roi_origin') != 'predicted_region'
                or t.get('source_identity') != identity
                or t.get('source_shape') != list(ct.shape)
                or not np.allclose(t.get('source_affine'), ct.affine, atol=1e-5, rtol=0)):
            raise ValueError('Measurement packaging requires matching native inference provenance')
        p = plan.get('prediction_record', {})
        if (p.get('full_volume') is not True or p.get('units') != 'mm'
                or p.get('source_identity') != identity
                or p.get('model_sha256') != evidence['model_sha256'].get('localizer')
                or p.get('native_shape') != list(ct.shape)
                or not np.allclose(p.get('native_affine'), ct.affine, atol=1e-5, rtol=0)):
            raise ValueError('Localizer identity or native geometry differs')
        box = t.get('native_box')
        if (not isinstance(box, list) or len(box) != 2
                or any(not isinstance(row, list) or len(row) != 3 for row in box)
                or any(type(n) is not int for row in box for n in row)
                or any(not (0 <= box[0][i] < box[1][i] <= ct.shape[i]) for i in range(3))):
            raise ValueError('Invalid native inference region')
        if len(evidence_bytes) > 1024**2:
            raise ValueError('Native measurement provenance exceeds the preview budget')
    # A fresh output directory prevents mixing files from separate packages.
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(ct_path, output / 'ct.nii.gz')
    shutil.copyfile(pred_path, output / 'prediction.nii.gz')
    if sha(output/'ct.nii.gz') != identity['ct_sha256'] or sha(output/'prediction.nii.gz') != result['prediction_sha256']:
        raise ValueError('Source changed while copying; incomplete package retained without manifest')
    def ref(path):
        return dict(uri=path.name, content_sha256=sha(path), bytes=path.stat().st_size)
    manifest = dict(schema_version='saved-prediction-view-v1', case_id=result['case_id'],
        prediction_mode='autonomous', status='completed_with_warnings',
        files=dict(ct=ref(output/'ct.nii.gz'), pred=ref(output/'prediction.nii.gz')),
        geometry=dict(shape=list(ct.shape), affine=ct.affine.tolist(), units='mm'),
        model_sha256=evidence['model_sha256'], result_sha256=hashlib.sha256(result_bytes).hexdigest(),
        inference_evidence_sha256=hashlib.sha256(json.dumps(evidence, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        ct_window=[-100, 300], labels={'0':'background','1':'pancreas','2':'lesion'},
        warnings=['Development demonstration. Predictions are unvalidated and require review.',
                  'This selected case does not establish representative performance or a diagnosis.'],
        reference_inputs_used=False)
    if measurement_provenance:
        manifest['schema_version'] = 'saved-prediction-view-v2'
        (output/'result.json').write_bytes(result_bytes)
        (output/'evidence.json').write_bytes(evidence_bytes)
        manifest['files'].update(result=ref(output/'result.json'), evidence=ref(output/'evidence.json'))
        manifest['warnings'].append('Native grid restoration does not certify complete pancreas coverage or segmentation accuracy.')
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ct', required=True)
    p.add_argument('--result', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--measurement-provenance', action='store_true', help='Include hash-bound inference records for native measurements')
    args = p.parse_args()
    manifest = prepare(args.ct, args.result, args.output, measurement_provenance=args.measurement_provenance)
    print(json.dumps({'case_id':manifest['case_id'], 'geometry':manifest['geometry'], 'files':manifest['files']}))
