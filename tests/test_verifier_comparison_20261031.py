from src.training.verifier_comparison_20261031 import compare

def data():
    p=dict(case_id='p',role='development',annotated_voxels=10,gt_components=[dict(component_id=1,volume_ml=.01)],candidates=[dict(component_id=1,voxels=10,overlap_voxels=10,gt_hits=[1])])
    n=[dict(case_id='n'+str(i),role='development',annotated_voxels=0,gt_components=[],candidates=[dict(component_id=1,voxels=1,overlap_voxels=0,gt_hits=[])]) for i in range(34)]
    return [p]+n,{**{(r['case_id'],1):.1 for r in n},('p',1):.8}

def test_useful_rejection_requires_guards():
    p,s=data();r=compare(p,s,.8)
    assert r['hypothesis']=='REJECT_H0' and r['status']=='PRACTICAL_SUPPORT'
    assert r['alarm_reduction_ci95']==[1.,1.]

def test_false_alarm_improvement_does_not_override_harm():
    p,s=data();s[('p',1)]=.1;r=compare(p,s,.8)
    assert r['hypothesis']=='REJECT_H0' and r['status']=='PRACTICAL_REJECTION'

def test_baseline_not_acceptance_of_null():
    p,s=data();r=compare(p,s,0)
    assert r['hypothesis']=='FAIL_TO_REJECT_H0' and r['status']=='PRACTICAL_REJECTION'

def test_missing_small_group_is_not_a_pass():
    p,s=data();p[0]['gt_components'][0]['volume_ml']=2
    assert compare(p,s,.8)['status']=='INCONCLUSIVE'
