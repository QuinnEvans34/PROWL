"""DUR-06 fake metadata guard qualification; no models, payloads or array generation."""
from copy import deepcopy
from pathlib import Path
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import segmenter_duration_executor_v1 as engine
from scripts.diagnostics import segmenter_duration_launch as launch


@pytest.fixture(autouse=True)
def deny_model_work(monkeypatch):
    def denied(*a,**k):raise AssertionError('Model/payload work outside DUR-06 unit scope')
    for name in ('Session','scratch','make_identity','restore_payload'):monkeypatch.setattr(launch.core,name,denied)
    monkeypatch.setattr(torch.nn.Module,'_call_impl',denied)
    monkeypatch.setattr(torch.optim.AdamW,'step',denied)
    monkeypatch.setattr(torch,'load',denied)


@pytest.fixture
def evidence(monkeypatch):
    from src.operations import segmenter_duration_readiness_v1 as reconcile
    from scripts.diagnostics import segmenter_training_qualification as qualification
    # Invented dictionaries isolate new admission semantics; producing hashes are checked separately.
    prior={f'src/fake_{n}.py':'a'*64 for n in range(398)}
    amended=['scripts/diagnostics/segmenter_duration_launch.py','src/training/segmenter_duration_executor_v1.py']
    prior.update({n:'a'*64 for n in amended});pins=prior|{n:'b'*64 for n in amended}
    runtime={'fixture':'no model runtime'};ids=[f'invented-{n}' for n in range(7)]
    origin=dict(source_pins=deepcopy(prior),pins=dict(request_sha256='575603717131190f97ea7496e4ef0d4c0311ae5f9be0599658dad1c0671fd70b'),targets=dict(cases=[dict(study_id=n) for n in ids]));origin['source_pins'].pop('src/fake_397.py')
    a=dict(state='qualified_duration_inference_v1',source_pins=pins,runtime=runtime,completed_steps=192,
        primary_reads_blocked=True,training_resume_qualified=False,next_update_exact=False,
        continuation_status='failed_bit_exact_deferred',all_native_exports_exact=True,cold_original_reads=0,
        model_calls=engine.call_limits('scientific'),producer_sha256='a1930dd30180be300a07dd9a6aaa1e57650d4e0b1c8d93dc1c73864999151e3b',
        recovery_sha256='c'*64,tests_sha256='d'*64,lineage_sha256='e'*64,checkpoints=[0,48,96,144,192],
        probe_checks=[dict(step=n,max_absolute_difference=0.) for n in [0,48,96,144,192]],
        native_checks=[dict(step=s,study_id=n,prediction_exact=True,view_validated=True) for s in [48,96,144,192] for n in (ids if s==192 else ids[:6])],view_checks=25,origin_request_sha256=origin['pins']['request_sha256'])
    r=dict(kind='scientific',source_pins=pins,runtime=runtime,extension_allowed=False,
        readiness={k:a[k] for k in ('producer_sha256','recovery_sha256','tests_sha256','lineage_sha256','training_resume_qualified')}|dict(kind=a['state'],acceptance_sha256='f'*64),
        recovery_policy=dict(primary_denied=True,original_target_reads=0,original_ct_reads=0,real_optimizer_calls=0,automatic_restart=False))
    lineage=dict(state='reviewed_DUR06_function_scope',source_pins=pins,prior_source_pins=prior,origin_source_pins=origin['source_pins'],amended=amended,outside_approved_regions_identical=True,numerical_recipe_unchanged=True,original_replay_assertion_unchanged=True)
    tests=dict(state='qualified_model_free_DUR06',source_pins=pins,passed=1,model_forwards=0,optimizer_calls=0,actual_arrays=0)
    recovery={k:deepcopy(a[k]) for k in ('source_pins','runtime','producer_sha256','origin_request_sha256','lineage_sha256','tests_sha256','primary_reads_blocked','training_resume_qualified','checkpoints','probe_checks','native_checks','view_checks')}
    recovery.update(state='passed_duration_inference_v1',attempt='DUR_INFERENCE_20261007_I02',model_calls=dict(forwards=30,optimizer_calls=0),original_arrays=0,third_party_weights=0,scientific_launch=False,payload_member_bytes=100,seconds=1.)
    rows={'SEGMENTER-DURATION-INFERENCE-READINESS.json':a,'frozen-manifest.json':origin,'protected-pins-post-repair.json':prior,'source-lineage.json':lineage,'unit-qualification.json':tests,'result.json':recovery}
    def read(path,pin,*args):
        name=Path(path).name
        if name=='SEGMENTER-DURATION-NATIVE-READINESS.json':raise ValueError('No full native certificate')
        return canonical(rows[name])
    monkeypatch.setattr(launch,'read_control',read)
    monkeypatch.setattr(qualification,'runtime',lambda:runtime)
    monkeypatch.setenv('PYTORCH_ENABLE_MPS_FALLBACK','0')
    monkeypatch.setattr(reconcile,'reconcile',lambda *a:None)
    from scripts.diagnostics import segmenter_lowrate_native_qualification as old
    monkeypatch.setattr(launch,'metadata_result',lambda path,pin:dict(state='qualified',gate=dict(passed=True)) if pin==old.CPU_PIN else dict(state='qualified_native_mechanics_not_real_training',producer=dict(state='passed'),recovery=dict(state='passed')))
    return r,rows


def test_complete_inference_certificate(evidence):launch.validate_readiness(evidence[0])


@pytest.mark.parametrize('field,value',[('state','qualified_duration_native_v1'),('completed_steps',48),('primary_reads_blocked',False),('training_resume_qualified',True),('next_update_exact',True),('continuation_status','passed'),('cold_original_reads',1),('cold_original_reads',False),('all_native_exports_exact',False),('producer_sha256','a'*64)])
def test_certificate_boundary(evidence,field,value):
    r,rows=evidence;rows['SEGMENTER-DURATION-INFERENCE-READINESS.json'][field]=value
    with pytest.raises((ValueError,KeyError)):launch.validate_readiness(r)


@pytest.mark.parametrize('field', ['source_pins','runtime','recovery_sha256','tests_sha256','lineage_sha256','origin_request_sha256'])
def test_certificate_bindings(evidence,field):
    r,rows=evidence;rows['SEGMENTER-DURATION-INFERENCE-READINESS.json'][field]={} if field in ('source_pins','runtime') else 'a'*64
    with pytest.raises(ValueError):launch.validate_readiness(r)


@pytest.mark.parametrize('field,value',[('state','failed'),('attempt','N02'),('model_calls',dict(forwards=29,optimizer_calls=0)),('model_calls',dict(forwards=30,optimizer_calls=1)),('model_calls',dict(forwards=30,optimizer_calls=False)),('original_arrays',1),('third_party_weights',1),('training_resume_qualified',True),('scientific_launch',True),('payload_member_bytes',2*1024**3+1),('seconds',600),('seconds',float('nan'))])
def test_cold_failed_or_expanded_scope(evidence,field,value):
    r,rows=evidence;rows['result.json'][field]=value
    with pytest.raises(ValueError):launch.validate_readiness(r)


@pytest.mark.parametrize('fault',['checkpoint','probe_missing','probe_duplicate','probe_delta','probe_nan','native_missing','native_wrong_role','native_duplicate','mask','view','view_count'])
def test_complete_ordered_evidence(evidence,fault):
    r,rows=evidence;a=rows['SEGMENTER-DURATION-INFERENCE-READINESS.json']
    if fault=='checkpoint':a['checkpoints'].pop()
    elif fault=='probe_missing':a['probe_checks'].pop()
    elif fault=='probe_duplicate':a['probe_checks'][1]=deepcopy(a['probe_checks'][0])
    elif fault=='probe_delta':a['probe_checks'][0]['max_absolute_difference']=1.00001e-6
    elif fault=='probe_nan':a['probe_checks'][0]['max_absolute_difference']=float('nan')
    elif fault=='native_missing':a['native_checks'].pop()
    elif fault=='native_wrong_role':a['native_checks'][0]['study_id']='invented-6'
    elif fault=='native_duplicate':a['native_checks'][1]=deepcopy(a['native_checks'][0])
    elif fault=='mask':a['native_checks'][0]['prediction_exact']=False
    elif fault=='view':a['native_checks'][0]['view_validated']=False
    else:a['view_checks']=24
    for k in ('checkpoints','probe_checks','native_checks','view_checks'):rows['result.json'][k]=deepcopy(a[k])
    with pytest.raises(ValueError):launch.validate_readiness(r)


@pytest.mark.parametrize('fault',['origin','prior','amended','regions','numerics','replay','unit_failed','unit_model','unit_source','restart','extension','full_substitution'])
def test_provenance_and_no_restart(evidence,fault):
    r,rows=evidence;l=rows['source-lineage.json'];t=rows['unit-qualification.json']
    if fault=='origin':rows['frozen-manifest.json']['source_pins']['src/fake_0.py']='z'*64
    elif fault=='prior':r['source_pins']['src/fake_1.py']='z'*64
    elif fault=='amended':l['amended']=[]
    elif fault=='regions':l['outside_approved_regions_identical']=False
    elif fault=='numerics':l['numerical_recipe_unchanged']=False
    elif fault=='replay':l['original_replay_assertion_unchanged']=False
    elif fault=='unit_failed':t['state']='failed'
    elif fault=='unit_model':t['model_forwards']=1
    elif fault=='unit_source':t['source_pins']={}
    elif fault=='restart':r['recovery_policy']['automatic_restart']=True
    elif fault=='extension':r['extension_allowed']=True
    else:r['readiness']['kind']='qualified_duration_native_v1'
    with pytest.raises(ValueError):launch.validate_readiness(r)


def test_existing_full_branch_remains(evidence):
    r,rows=evidence;r['readiness']['kind']='qualified_duration_native_v1'
    with pytest.raises(ValueError,match='No full native certificate'):launch.validate_readiness(r)


@pytest.fixture
def scientific_request(evidence,monkeypatch):
    r,rows=evidence
    control=dict(train=[f'invented-{n}' for n in range(6)],validation=['invented-6'])
    monkeypatch.setattr(engine.core,'validate_controls',lambda *a:control)
    monkeypatch.setattr(engine.policy,'validate_policy',lambda *a,**k:None)
    monkeypatch.setattr(engine,'validate_capability',lambda *a:dict(phase='real'))
    monkeypatch.setattr(engine.targets,'validate_scope',lambda *a:None)
    pins={n:'a'*64 for n in engine.REQUIRED_CODE};controls={'source.json':canonical(pins).decode(),'environment.json':'{}','geometry.json':canonical(dict(target_scope_sha256=digest(canonical(dict(domain='original_native_targets'))),stage=engine.targets.STAGE)).decode()}
    q=dict(schema_version='1.0.0',task=engine.TASK,kind='scientific',experiment_id='DURATION-invented',identity=dict(domain='qualified_real_cache',device='mps',config=dict(tensor_shape=[144]*3,max_steps=192)),controls=controls,checkpoint_steps=[0,48,96,144,192],screen_steps=[48,96,144,192],limits=deepcopy(engine.LIMITS),screen_mode='duration_policy',model_calls=engine.call_limits('scientific'),policy=dict(train_case_ids=control['train'],report_case_id=control['validation'][0]),policy_sha256='a'*64,targets=dict(domain='original_native_targets'),source_pins=pins,runtime={},storage_capability={},storage_capability_sha256=digest(canonical(dict(phase='real'))),readiness=deepcopy(r['readiness']),input_cache=dict(area='segmenter-input-cache',acceptance_sha256='8b21315b14e38a6f582964a274d430ce768af9fb8348c8858c9ece62221125f3',request_sha256='d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364',payload_bytes=104509440),imports_allowed=False,extension_allowed=False,recovery_policy=deepcopy(r['recovery_policy']))
    return q


def test_request_admits_distinct_inference_kind(scientific_request):engine.validate_request(scientific_request)


@pytest.mark.parametrize('fault',['resume','lineage_pin','unknown_field','missing_field','unknown_kind','restart','role','calls'])
def test_request_inference_scope_denial(scientific_request,fault):
    request=scientific_request
    if fault=='resume':request['readiness']['training_resume_qualified']=True
    elif fault=='lineage_pin':request['readiness']['lineage_sha256']='bad'
    elif fault=='unknown_field':request['readiness']['automatic_resume']=True
    elif fault=='missing_field':request['readiness'].pop('lineage_sha256')
    elif fault=='unknown_kind':request['readiness']['kind']='qualified_anything'
    elif fault=='restart':request['recovery_policy']['automatic_restart']=True
    elif fault=='role':request['policy']['report_case_id']='invented-0'
    else:request['model_calls']['cold']['optimizer_calls']=1
    with pytest.raises((ValueError,KeyError)):engine.validate_request(request)


def test_i02_result_path(evidence,monkeypatch):
    r,rows=evidence;old=launch.read_control;seen=[]
    def read(path,pin,*args):
        if Path(path).name=='result.json':
            seen.append(str(path))
            assert Path(path).parent.name=='SEGMENTER-DURATION-INFERENCE-I02-20261007'
        return old(path,pin,*args)
    monkeypatch.setattr(launch,'read_control',read)
    launch.validate_readiness(r)
    assert len(seen)==1


def test_retired_i01_not_accepted(evidence):
    r,rows=evidence;rows['result.json']['attempt']='DUR_INFERENCE_20261007_I01'
    with pytest.raises(ValueError,match='Inference cold qualification absent'):launch.validate_readiness(r)
