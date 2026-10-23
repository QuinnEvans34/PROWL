from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import pytest

from src.training.native_error_review_v1 import (POLICY,validate_report,case_error,summarize,compare,paired_stat,
    select_complete_series,final_decision,small_components,component_table,REGION_SCOPE)
from scripts.diagnostics.compare_native_distillation import fixed_recipe,run as final_run

IDS=['positive-small','positive-large','empty-a','empty-b']


def case(name,n,p,tp,step=2000):
    m=dict(lesion=dict(target_voxels=n,predicted_voxels=p,true_positive=tp,dice=None if n+p==0 else 2*tp/(n+p)),
        pancreas=dict(target_voxels=10,predicted_voxels=10,true_positive=8,dice=.8),voxel_mm3=1.,
        target_volume_mm3=float(n),predicted_volume_mm3=float(p),reference_positive=n>0,case_detected=tp>0,
        false_alarm_any=n==0 and p>0,case_alert_50mm3=p>=50,reference_components=int(n>0),detected_components=int(tp>0),
        predicted_components=int(p>0),size_band='empty' if not n else 'small' if n<1000 else 'medium' if n<=10000 else 'large')
    return dict(case_id=name,step=step,scope=REGION_SCOPE,metrics=m,
        reconstruction=dict(gap_voxels=0,lesion_guided_region=False,assistance='provided_pancreas_mask'))


def report(step=2000):
    return dict(step=step,scope=REGION_SCOPE,cases=[case(IDS[0],100,80,60,step),case(IDS[1],20000,10000,6000,step),
        case(IDS[2],0,100,0,step),case(IDS[3],0,0,0,step)])


def test_known_precision_recall_false_positive_false_negative_and_volumes():
    e=case_error(report()['cases'][0])
    assert (e['false_negative'],e['false_positive'],e['voxel_recall'],e['voxel_precision'])==(40,20,.6,.75)
    assert e['error_pattern']=='missed_voxel_dominant' and e['target_mL']==.1
    s=summarize(report(),IDS,positive_cases=2)
    assert s['positive_macro_dice']==pytest.approx((120/180+12000/30000)/2)
    assert s['positive_macro_recall']==pytest.approx(.45) and s['negative_alarms']==1
    assert s['negative_predicted_mL']==.1 and s['bands']['medium']['cases']==0


@pytest.mark.parametrize('n,p,tp,kind',[(100,0,0,'complete_miss_no_prediction'),(100,10,0,'complete_miss_with_off_target_prediction'),
    (100,100,100,'exact_voxel_match'),(100,150,80,'extra_voxel_dominant'),(100,100,50,'balanced_mixed_error'),
    (0,0,0,'negative_clean'),(0,3,0,'negative_false_positive')])
def test_error_patterns(n,p,tp,kind):assert case_error(case('A',n,p,tp))['error_pattern']==kind


def test_overlapping_error_flags_and_undefined_precision_are_not_perfect_scores():
    e=case_error(case('A',100,250,25))
    assert e['flags']['more_than_half_annotation_missed'] and e['flags']['more_than_half_prediction_extra'] and e['flags']['at_least_double_target_volume']
    r=report();r['cases'][0]=case(IDS[0],100,0,0);s=summarize(r,IDS,positive_cases=2)
    assert s['precision_defined_positive_cases']==1 and s['complete_misses']==1
    assert s['positive_macro_recall']==.15


@pytest.mark.parametrize('change',['missing','duplicate','tp','dice','boolean','volume','band','scope','step','gap','lesion_crop','nan'])
def test_malformed_or_incomplete_reports_fail(change):
    r=report();m=r['cases'][0]['metrics']
    if change=='missing':r['cases'].pop()
    elif change=='duplicate':r['cases'][-1]=deepcopy(r['cases'][0])
    elif change=='tp':m['lesion']['true_positive']=1000
    elif change=='dice':m['lesion']['dice']=.99
    elif change=='boolean':m['case_detected']=False
    elif change=='volume':m['target_volume_mm3']=101
    elif change=='band':m['size_band']='large'
    elif change=='scope':r['scope']='test'
    elif change=='step':r['cases'][0]['step']=4000
    elif change=='gap':r['cases'][0]['reconstruction']['gap_voxels']=1
    elif change=='lesion_crop':r['cases'][0]['reconstruction']['lesion_guided_region']=True
    else:m['voxel_mm3']=float('nan')
    with pytest.raises(ValueError):validate_report(r,IDS,positive_cases=2)


def test_case_reordering_exact_pairing_and_zero_difference_intervals():
    a=report();b=deepcopy(a);b['cases'].reverse()
    c=compare(a,b,IDS,positive_cases=2,replicates=100)
    assert c['metrics']['dice']['estimate']==0 and c['metrics']['dice']['ci95']==[0,0]
    assert c['hypothesis_decision'] is None and c['practical_decision'] is None
    assert c['guards']['small_component_recall']['passed'] is None


def test_reference_mismatch_and_inference_scope_mismatch_fail():
    a=report();b=report();b['cases'][0]=case(IDS[0],101,80,60)
    with pytest.raises(ValueError,match='target semantics|targets'):compare(a,b,IDS,positive_cases=2)
    b=deepcopy(a);b['scope']='native_development_provided_pancreas'
    for row in b['cases']:row['scope']=b['scope']
    with pytest.raises(ValueError,match='inference scopes'):compare(a,b,IDS,positive_cases=2)


def test_exact_legacy_top_and_row_scope_pair_is_descriptive_only():
    old=report();old['scope']='native_provided_pancreas_development'
    for row in old['cases']:row['scope']='native_development_provided_pancreas'
    assert summarize(old,IDS,positive_cases=2)['detected']==2
    with pytest.raises(ValueError,match='inference scopes'):compare(old,report(),IDS,positive_cases=2)
    old['cases'][0]['scope']='test'
    with pytest.raises(ValueError,match='scope'):summarize(old,IDS,positive_cases=2)


def test_bootstrap_determinism_sign_total_and_empty():
    assert paired_stat([.1,.2,.3],replicates=100)==paired_stat([.1,.2,.3],replicates=100)
    assert paired_stat([2,3],replicates=100,total=True)['estimate']==5
    assert paired_stat([],replicates=100)['ci95'] is None
    with pytest.raises(ValueError):paired_stat([np.nan],replicates=100)


def test_full_horizon_required_earliest_tie_and_terminal_separate():
    all_reports=[report(step=s) for s in range(2000,24001,2000)]
    best,terminal=select_complete_series(list(reversed(all_reports)),IDS,positive_cases=2)
    assert best['step']==2000 and terminal['step']==24000
    for invalid in (all_reports[:-1],all_reports+[report()],all_reports[:-1]+[report(2000)]):
        with pytest.raises(ValueError):select_complete_series(invalid,IDS,positive_cases=2)


def sidecar(r,pin):
    cases=[]
    for row in r['cases']:
        n=row['metrics']['lesion']['target_voxels']
        cases.append(dict(case_id=row['case_id'],target_sha256='a'*64,geometry_sha256='b'*64,
            components=[] if not n else [dict(component_id=1,voxels=n,volume_mm3=float(n),detected=row['metrics']['case_detected'])]))
    return dict(version='native-components-1',report_sha256=pin,matching=POLICY['component_matching'],cases=cases)


def test_small_component_guard_requires_all_components_and_patient_cluster_bootstrap():
    a,b=report(),report();a['cases'][0]=case(IDS[0],100,0,0)
    x,y=sidecar(a,'c'*64),sidecar(b,'d'*64)
    result=small_components(a,b,x,y,control_sha256='c'*64,treatment_sha256='d'*64,replicates=1000)
    assert result['estimate']==1 and result['ci95']==[1,1] and result['components']==1
    assert result['zero_denominator_draws']>0 and 'patient_cluster' in result['bootstrap_unit']
    x['cases'][0]['components'][0]['volume_mm3']=1000
    with pytest.raises(ValueError):component_table(x,a,'c'*64)


def test_missing_small_components_never_pass_and_case_size_is_not_substitute():
    c=compare(report(),report(),IDS,positive_cases=2,replicates=100)
    c['metrics']['dice']=dict(estimate=.05,ci95=[.02,.08])
    decision=final_decision(c)
    assert decision['hypothesis_decision']=='reject_H0' and decision['practical_decision']=='not_evaluable_missing_required_guard'
    c['guards']['small_component_recall']['passed']=True
    assert final_decision(c)['practical_decision']=='accept'
    c['guards']['alarm']['passed']=False
    assert final_decision(c)['practical_decision']=='reject'


@pytest.mark.parametrize('delta,ci,expected',[(-.02,[-.04,0],'reject'),(.01,[-.02,.03],'inconclusive'),(.02,[.001,.05],'accept')])
def test_practical_policy_and_not_accepting_null(delta,ci,expected):
    c=compare(report(),report(),IDS,positive_cases=2,replicates=100)
    c['metrics']['dice']=dict(estimate=delta,ci95=ci);c['guards']['small_component_recall']['passed']=True
    assert final_decision(c)['practical_decision']==expected
    assert final_decision(c)['hypothesis_decision']==('reject_H0' if ci[0]>0 else 'fail_to_reject_H0')


def test_configuration_changes_and_unbound_manifest_fail_before_output(tmp_path):
    config=dict(session={},initialization={},region_policy={},training_view_policy={},throughput_policy='same',
        _experiment=dict(name='a',run=dict(checkpoint_every=500,max_updates=24000,validate_every=2000)))
    b=deepcopy(config);b['_experiment']['name']='b';b['distillation']={'weight':.1}
    assert fixed_recipe(config)==fixed_recipe(b)
    b['unexpected_intervention']=True
    with pytest.raises(ValueError):fixed_recipe(b)
    manifest=tmp_path/'unbound.json';manifest.write_text(json.dumps(dict(status='UNBOUND_NOT_READY')))
    with pytest.raises(ValueError,match='Unbound'):final_run(manifest,tmp_path/'output')
    assert not (tmp_path/'output').exists()


def completed_fixture(tmp_path,monkeypatch,*,with_components):
    from scripts.diagnostics import compare_native_distillation as cli
    ids=[f'positive-{n:02d}' for n in range(36)]+[f'negative-{n:02d}' for n in range(34)]
    control=dict(train=[f'train-{n}' for n in range(1333)],validation=ids)
    def save(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf-8')
        return dict(path=str(path),sha256=cli.sha(path))
    config=dict(session={'learning_rate':.0001},initialization={'kind':'synthetic'},region_policy={},training_view_policy={},
        throughput_policy='same',_experiment=dict(name='synthetic',run=dict(checkpoint_every=500,max_updates=24000,validate_every=2000)))
    manifest=dict(status='BOUND_FOR_COMPLETED_COMPARISON',scope='teacher_assisted_exploratory',policy=POLICY,
        cohort=save(tmp_path/'cohort.json',dict(role='validation',case_ids=ids)))
    review=dict(approved=True,changed_factor='auxiliary_teacher_loss_only')
    for label,tp in (('control',50),('treatment',70)):
        root=tmp_path/label;execution=root/'execution';execution.mkdir(parents=True)
        cfg=deepcopy(config)
        if label=='treatment':cfg['distillation']={'weight':.1}
        arm=dict(run_directory=str(root),configuration=save(root/'configuration.json',cfg),input_control=save(root/'input-control.json',control),
            result=save(root/'result.json',dict(completed_updates=24000)),resources=save(root/'resources.json',dict(workers_reaped=True)),
            mlflow_run_id=label,components=dict(selected=None,terminal=None))
        arm['receipt']=save(root/'ready.json',dict(configuration_sha256=arm['configuration']['sha256'],control_sha256=arm['input_control']['sha256']))
        save(root/'tracking.json',dict(run_id=label))
        with (execution/'history.jsonl').open('w') as stream:
            for step in range(1,24001):
                stream.write(json.dumps(dict(event='update',step=step))+'\n')
                if step%2000==0:stream.write(json.dumps(dict(event='native_completed',step=step))+'\n')
            stream.write(json.dumps(dict(event='completed',step=24000))+'\n')
        for step in range(2000,24001,2000):
            r=dict(step=step,scope=REGION_SCOPE,cases=[case(n,100,100,tp,step) if n.startswith('positive') else case(n,0,0,0,step) for n in ids])
            pin=save(execution/f'native-{step:06d}.json',r)
            endpoint='selected' if step==2000 else 'terminal' if step==24000 else None
            if endpoint:
                save(execution/f'native-{endpoint}.json',r)
                if with_components:arm['components'][endpoint]=save(root/f'components-{endpoint}.json',sidecar(r,pin['sha256']))
        review[label+'_configuration_sha256']=arm['configuration']['sha256'];manifest[label]=arm
    manifest['matching_review']=save(tmp_path/'review.json',review)
    bound_manifest=save(tmp_path/'manifest.json',manifest)
    class Connection:
        def execute(self,*args):return self
        def fetchone(self):return ('FINISHED',)
        def close(self):pass
    monkeypatch.setattr(cli.sqlite3,'connect',lambda *args,**kwargs:Connection())
    return cli,Path(bound_manifest['path']),manifest


@pytest.mark.parametrize('with_components',[True,False])
def test_completed_cli_end_to_end_and_missing_guard_blocks_acceptance(tmp_path,monkeypatch,with_components):
    from pathlib import Path
    cli,manifest,_=completed_fixture(tmp_path,monkeypatch,with_components=with_components)
    cli.run(manifest,tmp_path/'result')
    result=json.loads((tmp_path/'result/comparison.json').read_text())
    expected='accept' if with_components else 'not_evaluable_missing_required_guard'
    assert result['primary']['practical_decision']==expected and result['secondary']['practical_decision']==expected
    assert result['primary']['control_step']==2000 and result['secondary']['control_step']==24000
    assert result['primary']['metrics']['dice']['estimate']==pytest.approx(.2)
    with pytest.raises(ValueError,match='exists'):cli.run(manifest,tmp_path/'result')


def test_completed_cli_rejects_recipe_not_matching_launch_receipt(tmp_path,monkeypatch):
    cli,manifest,m=completed_fixture(tmp_path,monkeypatch,with_components=True)
    config_path=Path(m['treatment']['configuration']['path']);cfg=json.loads(config_path.read_text())
    cfg['session']['learning_rate']=.005;config_path.write_text(json.dumps(cfg))
    m['treatment']['configuration']['sha256']=cli.sha(config_path)
    review_path=Path(m['matching_review']['path']);review=json.loads(review_path.read_text())
    review['treatment_configuration_sha256']=cli.sha(config_path);review_path.write_text(json.dumps(review))
    m['matching_review']['sha256']=cli.sha(review_path);manifest.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='launched receipt'):cli.run(manifest,tmp_path/'result')
    assert not (tmp_path/'result').exists()
