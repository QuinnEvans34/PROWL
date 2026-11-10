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


PUBLISHED=SOURCE.parent/'STUNET-CORRECTED-FULL-NATIVE-METADATA-20261110.json'
PUBLISHED_SHA='4e2bec89a08dae10856f6da618c9c5be149aa19614471a7573d884be08036787'


def test_actual_published_corrected_endpoint_and_geometry_join():
    r=audit.review_published(PUBLISHED.read_bytes(),PUBLISHED_SHA,SOURCE.read_bytes(),audit.GEOMETRY_SHA)
    assert r['selected_step']==18000 and r['terminal_step']==24000
    terminal=r['series'][-1]
    assert terminal['summary']['positive_macro_dice']==pytest.approx(.41197206677087506)
    assert terminal['summary']['positive_macro_recall']==pytest.approx(.49925030980832513)
    assert terminal['summary']['reference_empty_case_specificity']==pytest.approx(7/34)
    assert terminal['oracle_only']['perfect_fp_removal']==pytest.approx(.6079749013444103)
    assert r['selected_to_terminal']['newly_zero_overlap']==['PanTS_00006755']
    assert r['saved_native_arrays']['retained'] is False
    assert r['source_sha256']==PUBLISHED_SHA


@pytest.mark.parametrize('kind',['input','wrapper','backup','selection'])
def test_published_join_binding_failure(kind):
    p=json.loads(PUBLISHED.read_bytes())
    if kind=='input':
        p['bindings']['pins']['E:\\PROWL\\readiness\\stunet-full-input-binding-20261106-a01\\worker\\inputs.json']='0'*64
    if kind=='wrapper':
        p['bindings']['pins']['C:\\Users\\quinn\\Desktop\\PROWL\\src\\data\\stunet_continuation_inputs_20261108.py']='0'*64
    if kind=='backup':p['completion']['backup_pairs'].pop()
    if kind=='selection':p['selected']['checkpoint']['sha256']='0'*64
    raw=json.dumps(p).encode()
    with pytest.raises(ValueError):
        audit.review_published(raw,hashlib.sha256(raw).hexdigest(),SOURCE.read_bytes(),audit.GEOMETRY_SHA)


def test_cli_published_output_is_reproducible_and_never_overwritten(tmp_path):
    import os,subprocess,sys
    output=tmp_path/'audit.json';root=SOURCE.parents[3]
    args=[sys.executable,str(root/'scripts/diagnostics/review_stunet_tuning_20261110.py'),
        '--export',str(PUBLISHED),'--sha256',PUBLISHED_SHA,'--geometry-export',str(SOURCE),
        '--geometry-sha256',audit.GEOMETRY_SHA,'--output',str(output)]
    env=dict(os.environ,PYTHONPATH=str(root))
    first=subprocess.run(args,capture_output=True,env=env,timeout=10)
    assert first.returncode==0,first.stderr
    raw=output.read_bytes()
    second=subprocess.run(args,capture_output=True,env=env,timeout=10)
    assert second.returncode!=0 and output.read_bytes()==raw


def test_extended_peer_export_independently_reproduces_every_derived_case():
    path=SOURCE.parent/'LENOVO-STUNET-CORRECTED-COMPLETE-NATIVE-METADATA-20261110.json'
    raw=path.read_bytes(); expected='6413c8cecc8a0e3c64cdb3f0c3ee9731113a33de7cb0442fc8b4d8614407423e'
    extended=audit.review(raw,expected)
    joined=audit.review_published(PUBLISHED.read_bytes(),PUBLISHED_SHA,SOURCE.read_bytes(),audit.GEOMETRY_SHA)
    assert extended['series']==joined['series']
    assert extended['selected_to_terminal']==joined['selected_to_terminal']
    p=json.loads(raw);old=json.loads(SOURCE.read_bytes());original=json.loads(PUBLISHED.read_bytes())
    assert p['case_identities_from_frozen_inputs']==old['case_identities_from_frozen_inputs']
    for before,after in zip(original['reports'],p['reports']):
        for a,b in zip(before['report']['cases'],after['cases_as_saved']):
            a=copy.deepcopy(a);a['metrics'].pop('derived_lesion_counts')
            assert a==b
    training=p['training_summary']
    assert len(training['exposure_as_saved'])==1333
    assert sum(training['exposure_as_saved'].values())==24000
    lost=[];positive=0
    for r in training['diagnostics_as_saved']:
        n=[next(c['target_voxels'] for c in s['classes'] if c['class_id']==2) for s in r['diagnostics']['scales']]
        if n[0]:
            positive+=1
            if not n[-1]:lost.append(r['step'])
    assert positive==10 and lost==[19501,22501,23501]
