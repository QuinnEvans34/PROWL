import numpy as np
import pytest
from src.inference.reference_boundary import audit_faces


def test_shared_ct_and_crop_edge_is_not_double_counted():
    p=np.zeros((5,6,7),np.uint8);r=p.copy();p[0,0,0]=1;r[0,0,0]=1;p[1,1,0]=2
    a=audit_faces(p,r,[[0,0,0],[4,5,6]])
    for surface in ['ct','crop']:
        c=a['surfaces'][surface]['unique_contact']
        assert c==dict(prediction_union_voxels=2,reference_voxels=1,union_reference_overlap=1,lesion_voxels=1)
    face=a['surfaces']['crop']['faces']['2_low']
    assert face['coincides_with_ct_face'] and face['inward_planes'][0]['union_outside_reference']==1
    assert face['inward_planes'][1]['prediction_union_voxels']==0
    assert not a['release_qualified']


def test_internal_face_is_distinguished():
    p=np.zeros((8,8,8),np.uint8);r=p.copy();p[2,3,3]=1;r[2,3,3]=1;r[3,3,3]=1
    a=audit_faces(p,r,[[2,2,2],[6,6,6]])
    face=a['surfaces']['crop']['faces']['0_low']
    assert not face['coincides_with_ct_face']
    assert face['inward_planes'][1]['reference_missed']==1
    assert a['surfaces']['ct']['unique_contact']['prediction_union_voxels']==0


@pytest.mark.parametrize('roi',[[[0.,0.,0.],[3.,3.,3.]], [[-1,0,0],[3,3,3]],[[0,0,0],[4,3,3]],[[1,1,1],[1,2,2]]])
def test_bad_roi(roi):
    a=np.zeros((3,3,3),np.uint8)
    with pytest.raises(ValueError):audit_faces(a,a,roi)


def test_bad_labels_and_grid():
    a=np.zeros((3,3,3),np.uint8);a[0,0,0]=3
    with pytest.raises(ValueError):audit_faces(a,a,[[0,0,0],[3,3,3]])
    with pytest.raises(ValueError):audit_faces(a[:2],a,[[0,0,0],[2,3,3]])
