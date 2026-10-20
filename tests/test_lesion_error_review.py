import numpy as np
import pytest
from src.inference.lesion_error_review import review_errors


def test_lesion_priority_and_missed_class_decomposition():
    p=np.array([0,1,2,2,2,0],np.uint8).reshape(1,2,3)
    a=np.array([1,1,1,1,0,0],np.uint8).reshape(p.shape)
    l=np.array([1,1,1,0,0,0],np.uint8).reshape(p.shape)
    r=review_errors(p,a,l,np.diag([2,3,4,1]))
    assert r['confusion_rows_reference_cols_prediction']==[[1,0,1],[0,0,1],[1,1,1]]
    assert r['missed_as_pancreas']==r['missed_as_background']==r['true_positive']==1
    assert r['false_positive_inside_provided_pancreas']==r['false_positive_outside_provided_pancreas']==1
    assert r['voxel_ml']==pytest.approx(.024) and r['lesion_recall']==pytest.approx(1/3)


def test_empty_reference_stays_undefined():
    p=np.ones((2,2,2),np.uint8)*2;r=review_errors(p,p==2,np.zeros_like(p),np.eye(4))
    assert r['lesion_recall'] is None and r['reference_lesion_components']==[] and r['false_positive']==8


@pytest.mark.parametrize('fault',['prediction','reference','shape','affine'])
def test_invalid_inputs(fault):
    p=np.zeros((2,2,2),np.uint8);a=p.copy();l=p.copy();aff=np.eye(4)
    if fault=='prediction':p[0,0,0]=3
    if fault=='reference':l[0,0,0]=2
    if fault=='shape':a=a[:1]
    if fault=='affine':aff[0,0]=0
    with pytest.raises(ValueError):review_errors(p,a,l,aff)
