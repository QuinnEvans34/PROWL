import copy,json,contextlib
from pathlib import Path
import pytest
from scripts.diagnostics import execute_autonomous_baseline_v2_20261103 as run

def cohort():
    names=['PanTS_00005592']+[str(i) for i in range(69)]
    return dict(cases=[dict(case_id=n,reuse={} if i in range(1,6) else None,preflight_failure=dict(case_id=n,reason='Projected resampling budget exceeded',conservative_shape=[235,215,398],required_voxels=20108950,existing_cap=16000000,excluded=False) if i==0 else None) for i,n in enumerate(names)],failure_policy=run.prep.POLICY,unresolved_preflight=[],localizer_recipe=dict(max_output_voxels=16000000),limits=dict(total_evaluation_seconds=42000,rss_bytes=12*1024**3))

def test_denominator_and_capacity_fail_closed():
    r=cohort();run.prep.validate_policy(r)
    for mutate in [lambda x:x['cases'].pop(0),lambda x:x['localizer_recipe'].update(max_output_voxels=20108950),lambda x:x['cases'][0]['preflight_failure'].update(excluded=True),lambda x:x['cases'][1].update(preflight_failure=x['cases'][0]['preflight_failure'])]:
        bad=copy.deepcopy(r);mutate(bad)
        with pytest.raises(ValueError):run.prep.validate_policy(bad)

def test_admission_template_does_not_authorize(tmp_path,monkeypatch):
    monkeypatch.setattr(run.prep,'OUT',tmp_path);r=cohort()
    a=dict(approved_request_sha256='p',scope='autonomous70',limits=r['limits'],output_policy='retain_float32_probabilities',numerical_exception='approved_only_for_this_scope',failure_policy=r['failure_policy'])
    (tmp_path/'admission-template.json').write_text(json.dumps(a))
    with pytest.raises(ValueError,match='NEW HUMAN'):run.admission('p',r)
    (tmp_path/'admission.json').write_text(json.dumps(a));assert run.admission('p',r)==a
    a.pop('failure_policy');(tmp_path/'admission.json').write_text(json.dumps(a))
    with pytest.raises(ValueError,match='failure accounting'):run.admission('p',r)

def test_launch_accounts70_without_forward_or_score_for_failure(tmp_path,monkeypatch):
    r=cohort();out=tmp_path/'prepared';out.mkdir();base=tmp_path/'run';backup=tmp_path/'backup'
    monkeypatch.setattr(run.prep,'OUT',out);monkeypatch.setattr(run,'BASE',base);monkeypatch.setattr(run,'BACKUP',backup)
    monkeypatch.setattr(run,'CASES',[c['case_id'] for c in r['cases']])
    for n,v in [('request.json',r),('admission.json',{}),('ready.json',dict(request_sha256='p',admission_sha256='h',source_pins={})),('source-admission.resources.json',dict(success=True,workers_reaped=True,exit_code=0))]:
        (out/n).write_text(json.dumps(v))
    monkeypatch.setattr(run.q,'sha',lambda p:'h');monkeypatch.setattr(run,'request',lambda *a,**k:r);monkeypatch.setattr(run,'admission',lambda *a:None);monkeypatch.setattr(run,'gate',lambda *a:None)
    monkeypatch.setattr(run.subprocess,'check_output',lambda *a,**k:'');monkeypatch.setattr(run,'training_guard',lambda *a:contextlib.nullcontext())
    backups=[];monkeypatch.setattr(run,'save_backup',lambda p,r:backups.append(p))
    reused=[];calls=[]
    def reuse(c,*a):
        reused.append(c['case_id']);p=base/c['case_id']/'autonomous';p.mkdir(parents=True);(p/'result.json').write_text('{}')
    monkeypatch.setattr(run,'reuse_case',reuse)
    def supervise(args,**kwargs):
        mode,pin,name,arm=args[-4:];calls.append((mode,name));p=base/name/arm;p.mkdir(parents=True,exist_ok=True)
        (p/('score.json' if mode=='--score' else 'result.json')).write_text('{}')
    monkeypatch.setattr(run.q,'supervise',supervise)
    # Reuse dictionaries are truthy in real requests.
    for c in r['cases']:
        if c['reuse'] is not None:c['reuse']={'root':'retained'}
    run.launch('h')
    result=json.loads((base/'completion.json').read_text());failure=json.loads((base/'PanTS_00005592/autonomous/failure.json').read_text())
    assert result['total_cases']==70 and result['successful_cases']==69 and len(result['denominator'])==70
    assert result['failed']==['PanTS_00005592'] and len(reused)==5
    assert sum(m=='--worker' for m,n in calls)==64 and sum(m=='--score' for m,n in calls)==69
    assert all(n!='PanTS_00005592' for m,n in calls)
    assert failure['dice'] is None and failure['source_read'] is False and failure['model_forwards']==0
    assert base/'PanTS_00005592/autonomous/failure.json' in backups

def test_failed_case_direct_worker_and_score_rejected(monkeypatch):
    r=cohort();monkeypatch.setattr(run,'request',lambda *a,**k:r);monkeypatch.setattr(run,'admission',lambda *a:None);monkeypatch.setattr(run,'CASES',[c['case_id'] for c in r['cases']])
    with pytest.raises(ValueError,match='cannot enter inference'):run.worker('p','PanTS_00005592','autonomous')
    with pytest.raises(ValueError,match='no score'):run.scoring('p','PanTS_00005592','autonomous')
