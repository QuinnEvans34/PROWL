import pytest
from scripts.diagnostics.compare_rsuper_pilot import paired_summary


def test_erratum_negative_and_missed_lesion_retained():
    old=[dict(case_id='positive',lesion_voxels=100,prediction_voxels=50,recall=.5),
         dict(case_id='PanTS_00003059',lesion_voxels=12,prediction_voxels=10,recall=0.)]
    new=[dict(case_id='positive',lesion_voxels=100,prediction_voxels=0,recall=0.),
         dict(case_id='PanTS_00003059',lesion_voxels=12,prediction_voxels=5,recall=0.)]
    result=paired_summary(old,new)
    assert result['positive_cases']==1 and result['negative_cases']==1
    assert result['summary']['baseline']['positive_macro_dice']==pytest.approx(2/3)
    assert result['summary']['candidate']['positive_cases_missed']==1
    assert result['summary']['baseline']['negative_false_positive_voxels']==10
    assert result['summary']['candidate']['negative_false_positive_voxels']==5
    with pytest.raises(ValueError):paired_summary(old,new[::-1])
    new[0]['lesion_voxels']=99
    with pytest.raises(ValueError):paired_summary(old,new)
