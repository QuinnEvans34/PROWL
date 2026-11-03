"""CPU-only successor preserving the frozen70 inventory and declared capacity failure."""
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import prepare_autonomous_baseline_v2_20261103 as old
q=old.q
PARENT_SHA='853faa584b3abc87e5b16b25c186af9cdbd5e1bbe69b08de208d5ecabe083cbc'
OUT=Path('E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a02')
RUN=Path('E:/PROWL/artifacts/week05-autonomous70-20261103-a02')
SOURCES=Path('E:/PROWL/sources/pants/week05-autonomous70-20261103-a02')
POLICY=dict(case_id='PanTS_00005592',status='PREFLIGHT_RESOURCE_LIMIT',denominator=70,excluded=False,raise_capacity=False,score=None)

def validate_policy(r):
    if r.get('failure_policy')!=POLICY or r.get('unresolved_preflight') or r['localizer_recipe']['max_output_voxels']!=16000000:raise ValueError('Failure policy/cap mismatch')
    cases=r['cases'];failed=[c for c in cases if c.get('preflight_failure')]
    if len(cases)!=70 or len({c['case_id'] for c in cases})!=70 or len(failed)!=1 or failed[0]['case_id']!=POLICY['case_id']:raise ValueError('Fixed70 failure denominator')
    f=failed[0]['preflight_failure']
    if f!=dict(case_id=POLICY['case_id'],reason='Projected resampling budget exceeded',conservative_shape=[235,215,398],required_voxels=20108950,existing_cap=16000000,excluded=False):raise ValueError('Failure evidence changed')
    if sum(c['reuse'] is not None for c in cases)!=5 or failed[0]['reuse'] is not None:raise ValueError('Five exact reuses required')

def prepare():
    old.inspect(PARENT_SHA)
    if OUT.exists():raise FileExistsError('Successor already prepared')
    r=copy.deepcopy(json.loads((old.OUT/'request.json').read_text()))
    failure=r['unresolved_preflight'][0]
    if len(r['unresolved_preflight'])!=1:raise ValueError('Unexpected unresolved gate')
    r.update(version='autonomous70-failure-accounting-2',parent_request_sha256=PARENT_SHA,status='PREPARED_REQUIRES_NEW_SCOPE_AND_RESOURCE_ADMISSION',failure_policy=POLICY,unresolved_preflight=[],output=str(RUN),backup='C:/Users/quinn/PROWL-Backups/week05-autonomous70-20261103-a02')
    for c in r['cases']:
        c['preflight_failure']=failure if c['case_id']==POLICY['case_id'] else None
        if c['needs_restoration']:c['files']['ct']=str(SOURCES/(c['case_id']+'.nii.gz'))
    r['execution_counts']=dict(denominator=70,reuse=5,new_inference=64,declared_resource_failure=1,ct_restoration=64)
    r['estimates']['caveat']+='; conservative parent65-case workload estimate retained; successor executes64 new cases'
    r['admission_required']=[x for x in r['admission_required'] if 'Resolve recorded5592' not in x]
    r['admission_required']=[x.replace('65-CT','64-CT') for x in r['admission_required']]+['Approve explicit5592 preflight failure accounting in full70 denominator, no capacity increase or fabricated score']
    for p in [old.OUT/'request.json',Path(__file__),ROOT/'scripts/diagnostics/execute_autonomous_baseline_v2_20261103.py',ROOT/'tests/test_week05_failure_accounting_20261103.py']:
        r['pins'][str(p)]=q.sha(p)
    validate_policy(r);OUT.mkdir();q.write(OUT/'request.json',r)
    pin=q.sha(OUT/'request.json')
    q.write(OUT/'admission-template.json',dict(approved_request_sha256=pin,scope='autonomous70',limits=r['limits'],output_policy='retain_float32_probabilities',numerical_exception='approved_only_for_this_scope',failure_policy=POLICY))
    print(json.dumps(dict(request_sha256=pin,counts=r['execution_counts'],approved=False,restore_started=False,gpu_started=False)))

def inspect(pin):
    if q.sha(OUT/'request.json')!=pin:raise ValueError('Successor request hash')
    r=json.loads((OUT/'request.json').read_text());validate_policy(r)
    for p,h in r['pins'].items():
        if q.sha(p)!=h:raise ValueError('Producing pin changed: '+p)
    print(json.dumps(dict(status=r['status'],request_sha256=pin,counts=r['execution_counts'],admission_present=(OUT/'admission.json').exists())))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--inspect-sha256');a=p.parse_args()
    if a.prepare:prepare()
    else:inspect(a.inspect_sha256)
