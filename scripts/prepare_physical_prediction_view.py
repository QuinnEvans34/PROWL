"""Package retained four-case Windows CT-only output without rewriting producer evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import nibabel as nib
import numpy as np
from scripts.prepare_saved_prediction_view import sha

REQUEST = 'f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd'
CASES = ['PanTS_00002028','PanTS_00000909','PanTS_00004681','PanTS_00006755']
SCHEMA = 'physical-prediction-view-v1'


def read_record(path):
    if path.is_symlink() or not 0 < path.stat().st_size <= 1024**2:
        raise ValueError('Bounded regular provenance file required')
    raw = path.read_bytes()
    return raw, json.loads(raw)


def native_region(result, shape, affine):
    e = result['evidence']; p = e['parent_geometry']
    if (p['source_shape'] != shape or not np.allclose(p['source_affine'], affine, atol=1e-5, rtol=0)
            or e.get('component') != 'predicted-physical-region-v1'
            or e.get('reference_inputs_used') is not False or e.get('localizer_policy') != 'all_support'
            or e['reconstruction'].get('gap_voxels') != 0
            or e['reconstruction'].get('output_decision') != 'native_center_probability_blend_then_argmax'):
        raise ValueError('Physical inference source or reconstruction differs')
    forward = np.asarray(p['forward'])
    if (forward.shape != (3,2) or sorted(forward[:,0].tolist()) != [0,1,2]
            or not np.isin(forward[:,1],[-1,1]).all()):
        raise ValueError('Invalid lossless orientation')
    expected_shape = np.asarray(shape)[np.argsort(forward[:,0].astype(int))].tolist()
    expected_affine = affine @ nib.orientations.inv_ornt_aff(forward, shape)
    if p['shape'] != expected_shape or not np.allclose(p['affine'], expected_affine, atol=1e-5, rtol=0):
        raise ValueError('Physical parent orientation differs')
    low, high = e['region_low'], e['region_high']
    if (len(low) != 3 or len(high) != 3 or any(type(v) is not int for v in low+high)
            or any(not 0 <= l < h <= n for l,h,n in zip(low,high,expected_shape))):
        raise ValueError('Invalid physical inference region')
    box = [[],[]]
    for i, (axis, sign) in enumerate(forward):
        j = int(axis)
        box[0].append(low[j] if sign == 1 else shape[i]-high[j])
        box[1].append(high[j] if sign == 1 else shape[i]-low[j])
    return box


def prepare(ct_path, prediction_path, result_path, request_path, output):
    ct_path, prediction_path, result_path, request_path, output = map(Path,
        (ct_path, prediction_path, result_path, request_path, output))
    request_bytes, request = read_record(request_path)
    result_bytes, result = read_record(result_path)
    if hashlib.sha256(request_bytes).hexdigest() != REQUEST:
        raise ValueError('Only the frozen four-case request is admitted')
    if (request.get('version') != 'four-case-exception-1'
            or [r['case_id'] for r in request['cases']] != CASES
            or request.get('probability_equivalence') != 'UNQUALIFIED'
            or result.get('status') != 'COMPLETED' or result.get('arm') != 'autonomous'
            or result.get('reference_inputs_used') is not False
            or result.get('optimizer_updates') != 0 or result.get('request_sha256') != REQUEST):
        raise ValueError('Requires the completed frozen CT-only exploratory result')
    case = next((r for r in request['cases'] if r['case_id'] == result['case_id']), None)
    if not case: raise ValueError('Result case is outside the fixed request')
    identity = case['identity']['source_sha256']
    for path, expected in [(ct_path, identity['ct']), (prediction_path, result['artifacts']['prediction.nii.gz'])]:
        if path.is_symlink() or not 0 < path.stat().st_size <= 64*1024**2 or sha(path) != expected:
            raise ValueError('CT/prediction hash or compressed size differs')
    ct, pred = nib.load(ct_path), nib.load(prediction_path)
    shape = list(ct.shape); affine = ct.affine
    if (len(shape) != 3 or np.prod(shape) > 32000000
            or ct.shape != pred.shape or not np.isfinite(affine).all()
            or abs(np.linalg.det(affine[:3,:3])) < 1e-10
            or not np.allclose(affine, pred.affine, atol=1e-5, rtol=0)
            or result['source_shape'] != shape
            or not np.allclose(result['source_affine'], affine, atol=1e-5, rtol=0)
            or case['header']['ct']['shape'] != shape
            or not np.allclose(case['header']['ct']['affine'], affine, atol=1e-5, rtol=0)
            or result['units'] != 'mm' or case['header']['ct']['units'] != 'mm'
            or any(n.header.get_xyzt_units()[0] != 'mm' for n in (ct,pred))
            or any(n.header.get_data_dtype().itemsize*np.prod(shape)+352 > 128*1024**2 for n in (ct,pred))):
        raise ValueError('Native geometry or bounded measurement allocation differs')
    box = native_region(result, shape, affine)
    if not np.isin(np.asanyarray(pred.dataobj), [0,1,2]).all():
        raise ValueError('Invalid native prediction labels')
    models = {k:request['models'][k]['sha256'] for k in ('localizer','segmenter')}
    if not all(re.fullmatch('[a-f0-9]{64}',h) for h in models.values()):
        raise ValueError('Invalid model identity')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(ct_path, output/'ct.nii.gz')
    shutil.copyfile(prediction_path, output/'prediction.nii.gz')
    (output/'result.json').write_bytes(result_bytes)
    # This is the exact original request, not a fabricated old-style inference record.
    (output/'evidence.json').write_bytes(request_bytes)
    def ref(n):
        p = output/n
        return dict(uri=n, bytes=p.stat().st_size, content_sha256=sha(p))
    files = {k:ref(n) for k,n in [('ct','ct.nii.gz'),('pred','prediction.nii.gz'),('result','result.json'),('evidence','evidence.json')]}
    if (files['ct']['content_sha256'] != identity['ct']
            or files['pred']['content_sha256'] != result['artifacts']['prediction.nii.gz']
            or files['result']['content_sha256'] != hashlib.sha256(result_bytes).hexdigest()
            or files['evidence']['content_sha256'] != REQUEST):
        raise ValueError('Source changed during packaging; incomplete attempt retained')
    manifest = dict(schema_version=SCHEMA, case_id=result['case_id'], prediction_mode='autonomous',
        status='completed_with_warnings', files=files, geometry=dict(shape=shape,affine=affine.tolist(),units='mm'),
        model_sha256=models, result_sha256=files['result']['content_sha256'], inference_evidence_sha256=REQUEST,
        request_identity=REQUEST, evaluation_scope='four-case-exploratory-20261102', case_role='exposed_development',
        probability_equivalence='UNQUALIFIED', native_region=box, ct_window=[-100,300],
        labels={'0':'background','1':'pancreas','2':'lesion'}, reference_inputs_used=False,
        warnings=['Exposed development case; predictions require human review.',
                  'Cross-device probability equivalence remains unqualified; the four-case exception applies.',
                  'Mask volumes do not establish anatomical completeness, a normal range, or a diagnosis.'])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('ct','prediction','result','request','output'): p.add_argument('--'+key,required=True)
    a=p.parse_args();m=prepare(a.ct,a.prediction,a.result,a.request,a.output)
    print(json.dumps(dict(case_id=m['case_id'],files=m['files'],native_region=m['native_region'])))
