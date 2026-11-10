"""Count-only synthetic corrected-run contracts; no private image fixtures."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.diagnostics import review_stunet_tuning_20261110 as audit

SOURCE=Path(__file__).resolve().parents[1]/'docs/capstone/coordination/LENOVO-STUNET-COMPLETE-NATIVE-METADATA-20261108.json'


@pytest.fixture
def fixture():
    # Shape-valid synthetic corrected export, derived from public-in-repo old
    # metadata. Never treated as observed corrected-run performance evidence.
    p=json.loads(SOURCE.read_bytes())
    p.update(artifact_id=audit.ARTIFACT,ready_sha256=audit.READY,mlflow_run_id=audit.MLFLOW)
    for report,step in zip(p['reports'],audit.STEPS):
        report['step']=step; report['report_name']=f'native-{step:05d}.json'
        p['source_json_sha256'][report['report_name']]=report['report_sha256']
        report['checkpoint']['name']=f'checkpoint-{step:05d}.pt'
    return p


def run(p):
    raw=json.dumps(p).encode()
    return audit.review(raw,hashlib.sha256(raw).hexdigest())


def test_terminal_and_selected_separate_with_all_six_validations(fixture):
    result=run(fixture)
    assert [r['step'] for r in result['series']]==audit.STEPS
    assert result['terminal_step']==24000
    last=result['series'][-1]
    assert last['summary']['positive_macro_dice']==pytest.approx(.3716332167382889)
    assert last['summary']['reference_empty_case_specificity']==pytest.approx(7/34)
    assert last['summary']['native_voxel_specificity']>.99
    assert last['summary']['detected_positive_cases']==35
    assert result['new_model_calls']==result['new_array_reads']==result['new_training_updates']==0
    assert result['selected_to_terminal']['macro_dice_delta']==0
    assert result==run(fixture)


def test_raw_original_run_is_not_silently_admitted_as_corrected():
    raw=SOURCE.read_bytes()
    with pytest.raises(ValueError,match='experiment identity'):
        audit.review(raw,hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize('mutate,error',[
    (lambda p:p['reports'].pop(),'six full'),
    (lambda p:p['reports'].reverse(),'six full'),
    (lambda p:p.update(ready_sha256='0'*64),'experiment identity'),
    (lambda p:p['reports'][0]['cases_as_saved'].pop(),'cohort'),
    (lambda p:p['reports'][0]['cases_as_saved'].__setitem__(1,copy.deepcopy(p['reports'][0]['cases_as_saved'][0])),'cohort'),
    (lambda p:p['reports'][0].update(independent_report_backup_matches=False),'receipt'),
    (lambda p:p['reports'][0]['checkpoint'].update(name='selected.pt'),'Checkpoint'),
    (lambda p:p['reports'][0]['summary_as_saved'].update(lesion_dice=.99),'summary'),
    (lambda p:p['reports'][0]['cases_as_saved'][0].update(gaps=1),'coverage'),
    (lambda p:p['reports'][0]['cases_as_saved'][0]['metrics']['lesion'].update(true_positive=-1),'overlap'),
    (lambda p:p['case_identities_from_frozen_inputs'][0].update(native_shape=[0,2,3]),'geometry'),
    (lambda p:p['case_identities_from_frozen_inputs'][0]['source_sha256'].update(ct='bad'),'binding'),
])
def test_corrupt_export_refused_even_after_rehash(fixture,mutate,error):
    mutate(fixture)
    with pytest.raises(ValueError,match=error):run(fixture)


def test_changed_reference_refused(fixture):
    m=fixture['reports'][-1]['cases_as_saved'][0]['metrics']['pancreas']
    m['target_voxels']+=1
    m['dice']=2*m['true_positive']/(m['target_voxels']+m['predicted_voxels'])
    with pytest.raises(ValueError,match='References changed'):run(fixture)


def test_hash_and_byte_bounds(fixture):
    raw=json.dumps(fixture).encode()
    with pytest.raises(ValueError,match='SHA256'):audit.review(raw,'0'*64)
    with pytest.raises(ValueError,match='byte limit'):audit.review(b'x'*(audit.MAX_BYTES+1),'0'*64)


def row(n,p,t):return dict(target_voxels=n,predicted_voxels=p,overlap_voxels=t)


def test_oracle_budget_uses_per_case_macro_not_pooled_counts():
    rows=[row(10,20,5),row(100,100,100),row(0,9999,0)]
    assert audit.counterfactual(rows)==pytest.approx(2/3)
    assert audit.counterfactual(rows,fp_removed=1)==pytest.approx(5/6)
    assert audit.counterfactual(rows,fn_recovered=1)==pytest.approx((20/35+1)/2)


def test_zero_tp_loss_requirement_and_unattainable_target():
    rows=[row(10,20,5)]
    fraction=audit.required_fp_fraction(rows)
    assert fraction==pytest.approx(2/3)
    assert audit.counterfactual(rows,fp_removed=fraction)==pytest.approx(.5)
    assert audit.required_fp_fraction([row(10,100,0)]) is None
    assert audit.counterfactual([row(10,100,0)],fp_removed=1)==0
    assert audit.required_fp_fraction([row(10,10,10)])==0
