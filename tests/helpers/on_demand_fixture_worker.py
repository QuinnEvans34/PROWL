"""Artificial native-package producer for job/transport tests; never loads a model."""
import json
from pathlib import Path
import shutil
import sys
import time
from src.inference.on_demand import canonical, sha

request = json.loads(Path(sys.argv[1]).read_bytes())
case = request['case']
if case['case_id'] == 'slow':
    time.sleep(20)
out = Path(sys.argv[2]); out.mkdir()
for key, name in [('ct', 'ct.nii.gz'), ('pancreas', 'prediction.nii.gz')]:
    shutil.copyfile(case[key]['path'], out/name)
e = dict(component='assisted-native-inference-v1', reference_inputs_used=True,
         request_identity=request['request_identity'], prediction_id=request['job_id'],
         recipe_sha256=request['recipe_sha256'], model_sha256={'segmenter':request['checkpoint']['sha256']},
         source_identity={'study_id':case['case_id'], 'ct_sha256':case['ct']['sha256']},
         assistance=dict(kind='provided_pancreas', sha256=case['pancreas']['sha256'], lesion_reference_used_for_prediction=False),
         transform=dict(source_shape=[4,4,4], source_affine=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], units='mm', native_box=[[0,0,0],[4,4,4]]),
         reconstruction=dict(uncovered_region_voxels=0, outside_region='background'))
(out/'evidence.json').write_bytes(canonical(e))
(out/'result.json').write_bytes(canonical(dict(status='complete', case_id=case['case_id'], reference_inputs_used=True, prediction_sha256=sha(out/'prediction.nii.gz'), evidence=e)))
files={key:dict(uri=name,bytes=(out/name).stat().st_size,content_sha256=sha(out/name)) for key,name in [('ct','ct.nii.gz'),('pred','prediction.nii.gz'),('result','result.json'),('evidence','evidence.json')]}
m=dict(schema_version='assisted-prediction-view-v1', status='completed_with_warnings', case_id=case['case_id'],
       prediction_mode='pancreas_assisted',reference_inputs_used=True, request_identity=request['request_identity'],
       prediction_id=request['job_id'], model_sha256=e['model_sha256'], recipe_sha256=e['recipe_sha256'],
       assistance_sha256=case['pancreas']['sha256'],files=files, result_sha256=files['result']['content_sha256'],
       inference_evidence_sha256=files['evidence']['content_sha256'], geometry=dict(shape=[4,4,4],affine=e['transform']['source_affine'],units='mm'),
       ct_window=[-100,300], labels={'0':'background','1':'pancreas','2':'lesion'},warnings=['Artificial test fixture; not a model prediction.'])
if case['case_id'] == 'wrong': m['request_identity']='0'*64
(out/'manifest.json').write_bytes(canonical(m))
