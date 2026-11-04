"""Approved continuation: fixed70 denominator, six unit failures, one capacity failure."""
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import prepare_autonomous_baseline_v3_20261103 as old
q=old.q
PARENT_SHA='7db98398be4da35bf775976ef81ec73e848e0258e56e760307817a4e5ec48364'
PARENT_OUT=old.OUT
OUT=Path('E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a03')
RUN=Path('E:/PROWL/artifacts/week05-autonomous70-20261103-a03')
SOURCES=old.SOURCES
UNIT_IDS=['PanTS_00006011','PanTS_00005780','PanTS_00001823','PanTS_00002935','PanTS_00006901','PanTS_00006115']
FAILURES=UNIT_IDS+['PanTS_00005592']
POLICY=dict(unit_failure_ids=UNIT_IDS,resource_failure_ids=['PanTS_00005592'],denominator=70,excluded=False,raise_capacity=False,infer_units=False,score=None)
def failure_status(c):return 'SOURCE_UNIT_ADMISSION_FAILURE' if c['case_id'] in UNIT_IDS else 'PREFLIGHT_RESOURCE_LIMIT'
def validate_policy(r):
    if r.get('failure_policy')!=POLICY or r.get('unresolved_preflight') or r['localizer_recipe']['max_output_voxels']!=16000000:raise ValueError('Failure policy/cap mismatch')
    cs=r['cases'];failed=[c for c in cs if c.get('preflight_failure')]
    if len(cs)!=70 or len({c['case_id'] for c in cs})!=70 or {c['case_id'] for c in failed}!=set(FAILURES):raise ValueError('Fixed70 seven failures required')
    for c in failed:
        if c['reuse'] is not None:raise ValueError('Failed case cannot reuse')
        f=c['preflight_failure']
        if c['case_id'] in UNIT_IDS:
            if f!=dict(case_id=c['case_id'],reason='Unresolved CT spatial units',header_units='unknown',ct_sha256=c['identity']['source_sha256']['ct'],excluded=False):raise ValueError('Unit evidence mismatch')
        elif f!=dict(case_id=c['case_id'],reason='Projected resampling budget exceeded',conservative_shape=[235,215,398],required_voxels=20108950,existing_cap=16000000,excluded=False):raise ValueError('Capacity evidence mismatch')
    if sum(c['reuse'] is not None for c in cs)!=5 or sum(c['reuse'] is None and not c['preflight_failure'] for c in cs)!=58:raise ValueError('Five reuse58 new required')
    budget=r['budget']
    if budget['remaining_evaluation_seconds']!=r['limits']['total_evaluation_seconds']-budget['prior_admission_seconds'] or not 0<budget['remaining_evaluation_seconds']<=42000:raise ValueError('Remaining budget invalid')

def prepare():
    import nibabel as nib
    old.inspect(PARENT_SHA)
    if OUT.exists():raise FileExistsError('Already prepared')
    r=copy.deepcopy(json.loads((PARENT_OUT/'request.json').read_text()))
    restore=json.loads((SOURCES/'restoration.json').read_text());resources=json.loads((PARENT_OUT/'restore.resources.json').read_text());failure=json.loads((PARENT_OUT/'handoff-failure.json').read_text())
    if not resources['success'] or not resources['workers_reaped'] or resources['exit_code']!=0 or restore['request_sha256']!=PARENT_SHA or len(restore['cases'])!=64:raise ValueError('Original restore not verified')
    if failure['request_sha256']!=PARENT_SHA:raise ValueError('Failure lineage')
    observed=[]
    for c in r['cases']:
        if c['preflight_failure']:continue
        p=c['files']['ct'];n=nib.load(p);u=n.header.get_xyzt_units()[0]
        if u!='mm':
            if u!='unknown' or c['case_id'] not in UNIT_IDS:raise ValueError('Unexpected source-unit issue')
            if q.sha(p)!=c['identity']['source_sha256']['ct']:raise ValueError('Unit failure CT identity changed')
            observed.append(c['case_id']);c['preflight_failure']=dict(case_id=c['case_id'],reason='Unresolved CT spatial units',header_units=u,ct_sha256=c['identity']['source_sha256']['ct'],excluded=False)
        if c['needs_restoration'] and restore['cases'].get(c['case_id'])!=c['identity']['source_sha256']['ct']:raise ValueError('Restoration identity differs')
    if set(observed)!=set(UNIT_IDS):raise ValueError('Exact unit failure set differs')
    prior=json.loads((PARENT_OUT/'handoff-admit.resources.json').read_text())
    if prior['success'] or not prior['workers_reaped'] or prior['exit_code']!=1:raise ValueError('Prior admission cleanup changed')
    r.update(version='autonomous70-unit-failure-continuation-3',parent_request_sha256=PARENT_SHA,status='APPROVED_CONTINUATION_SOURCE_ADMISSION_PENDING',failure_policy=POLICY,output=str(RUN),backup='C:/Users/quinn/PROWL-Backups/week05-autonomous70-20261103-a03',
        execution_counts=dict(denominator=70,reuse=5,new_inference=58,declared_unit_failures=6,declared_resource_failure=1,ct_restoration=0),
        budget=dict(original_evaluation_seconds=42000,prior_admission_seconds=prior['seconds'],remaining_evaluation_seconds=42000-prior['seconds'],restoration_reused_seconds=resources['seconds'],new_restoration_allowed=False))
    r['admission_required']=[]
    files=[PARENT_OUT/'request.json',PARENT_OUT/'handoff-failure.json',PARENT_OUT/'handoff-admit.resources.json',PARENT_OUT/'source-admission.resources.json',PARENT_OUT/'source-admission.log',PARENT_OUT/'restore.resources.json',SOURCES/'restoration.json',Path(__file__),ROOT/'scripts/diagnostics/execute_autonomous_baseline_v3_20261103.py',ROOT/'scripts/diagnostics/handoff_autonomous70_v2_20261103.py',ROOT/'tests/test_week05_unit_continuation_20261103.py']
    for p in files:r['pins'][str(p)]=q.sha(p)
    validate_policy(r);OUT.mkdir();q.write(OUT/'request.json',r);pin=q.sha(OUT/'request.json')
    q.write(OUT/'human-approval.json',dict(request_sha256=pin,source_thread='01a14176-ad79-7470-aad5-951d0dea22fc',human_quote='Great, lets get the other laptop working then.',relayed_scope='70 exposed-development autonomous cases: six unit failures plus5592 capacity failure;5reuse/58new; unchanged model/settings and64GiB combined backups',limits=r['limits'],failure_policy=POLICY,automatic_retry=False,training=False))
    q.write(OUT/'admission.json',dict(approved_request_sha256=pin,scope='autonomous70',limits=r['limits'],output_policy='retain_float32_probabilities',numerical_exception='approved_only_for_this_scope',failure_policy=POLICY))
    pins={str(p):q.sha(p) for p in [OUT/'request.json',OUT/'admission.json',OUT/'human-approval.json',ROOT/'scripts/diagnostics/handoff_autonomous70_v2_20261103.py']}
    q.write(OUT/'handoff-request.json',dict(request_sha256=pin,pins=pins,stages=['source-admission','evaluate'],automatic_retry=False))
    print(json.dumps(dict(request_sha256=pin,handoff_sha256=q.sha(OUT/'handoff-request.json'),counts=r['execution_counts'],budget=r['budget'])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true',required=True);p.parse_args();prepare()
