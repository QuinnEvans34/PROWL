import numpy as np
import pytest
from copy import deepcopy

from src.data import segmenter_geometry_v2 as g
from src.data import segmenter_geometry_v1 as old
from src.data.source_inventory_records import content_hash

IDENTITY = dict(study_id='invented',ct_sha256='a'*64)


def make(affine,shape=(32,32,32)):
    indices=np.indices(shape).reshape(3,-1)
    world=affine[:3,:3]@indices+affine[:3,3:4]
    ct=(world[0]+2*world[1]+3*world[2]-100).reshape(shape).astype(np.float32)
    p=np.zeros(shape,np.uint8);p[8:24,8:24,8:24]=1
    l=np.zeros_like(p);l[14:18,14:18,14:18]=1
    return ct,p,l


@pytest.mark.parametrize('angle',[0, .03, .4, -.6])
def test_tilted_world_ramp_and_native_return(angle):
    c,s=np.cos(angle),np.sin(angle)
    a=np.array([[c,-s,0,17],[s,c,0,-24],[0,0,1,11],[0,0,0,1.]])
    ct,p,l=make(a)
    out=g.preprocess(ct,p,l,a,g.recipe(tensor_shape=(32,32,32),margin_mm=3),
                     source_identity=IDENTITY,lesion_target_state='positive')
    record=out['transform'];point=np.array([16,16,16,1])
    world=np.asarray(record['tensor_affine'])@point
    expected=(world[0]+2*world[1]+3*world[2])/350
    assert out['image'][16,16,16]==pytest.approx(expected,abs=1e-6)
    restored=g.restore_codes(out['target'],record,trusted_record_sha256=out['transform_sha256'])
    assert (restored[l==1]==2).mean()>.6
    assert out['fidelity']['mechanical_survival_pass']


@pytest.mark.parametrize('flip',[False,True])
def test_axis_aligned_pipeline_matches_preserved_geometry(flip):
    a=np.eye(4)
    if flip:a[0,0]=-1;a[0,3]=31
    ct,p,l=make(a)
    args=dict(source_identity=IDENTITY,lesion_target_state='positive')
    before=old.preprocess(ct,p,l,a,old.recipe(tensor_shape=(32,32,32),margin_mm=3),**args)
    after=g.preprocess(ct,p,l,a,g.recipe(tensor_shape=(32,32,32),margin_mm=3),**args)
    assert np.array_equal(before['target'],after['target'])
    assert np.allclose(before['image'],after['image'],atol=1e-6,rtol=0)


def test_larger_native_shape_admission_and_bound():
    g.canonical_geometry([512,512,800],np.eye(4),g.recipe())
    with pytest.raises(ValueError,match='envelope'):g.canonical_geometry([512,512,1000],np.eye(4),g.recipe())
    a=np.eye(4);a[0,0]=0
    with pytest.raises(ValueError,match='affine'):g.canonical_geometry([32]*3,a,g.recipe())


def test_lesion_cannot_move_roi_and_lost_component_reported():
    a=np.eye(4);ct,p,l=make(a)
    first=g.preprocess(ct,p,l,a,g.recipe(margin_mm=0),source_identity=IDENTITY,lesion_target_state='positive')
    l[0,0,0]=1
    second=g.preprocess(ct,p,l,a,g.recipe(margin_mm=0),source_identity=IDENTITY,lesion_target_state='positive')
    assert first['transform']==second['transform'] and np.array_equal(first['image'],second['image'])
    assert not second['fidelity']['mechanical_survival_pass']
    changed=deepcopy(first['transform']);changed['tensor_affine'][0][3]+=1
    with pytest.raises(ValueError,match='derivation'):g.validate_record(changed,content_hash(changed))


def test_empty_reference_is_not_a_verified_negative_claim():
    ct,p,l=make(np.eye(4));l.fill(0)
    result=g.preprocess(ct,p,l,np.eye(4),g.recipe(),source_identity=IDENTITY,lesion_target_state='reference_empty')
    assert result['fidelity']['lesion_target_state']=='reference_empty'
    assert not result['fidelity']['components']
