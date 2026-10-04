from copy import deepcopy
import numpy as np
import pytest
from src.data import segmenter_geometry_v1 as g
from src.data.source_inventory_records import content_hash

IDENTITY=dict(study_id='invented-only',ct_sha256='a'*64)


def make(shape=(7,9,11),affine=None,r=None,pan=None,les=None,state='positive'):
    ct=np.zeros(shape,np.float32);p=np.ones(shape,np.uint8) if pan is None else pan
    l=np.zeros(shape,np.uint8) if les is None else les
    if les is None:l[2,3,4]=1
    return g.preprocess(ct,p,l,np.eye(4) if affine is None else affine,
        r or g.recipe(tensor_shape=shape,margin_mm=0),source_identity=IDENTITY,lesion_target_state=state)


def test_identity_nonzero_origin_exact_reference_and_probability_roundtrip():
    a=np.eye(4);a[:3,3]=[17,-24,11];r=make(affine=a)
    assert np.array_equal(r['reference_roundtrip'],r['target'])
    assert r['fidelity']['metrics']['lesion']['recall']==1 and r['fidelity']['all_components_survive']
    assert np.array_equal(np.asarray(r['transform']['tensor_affine']),a)
    p=np.stack([r['target']==c for c in range(3)]).astype(np.float32)
    restored=g.restore_probabilities(p,r['transform'],trusted_record_sha256=r['transform_sha256'])
    assert np.array_equal(restored,p) and np.array_equal(restored.argmax(0),r['reference_roundtrip'])


def test_permuted_flipped_axes_have_manual_coordinate_oracle_and_source_parity():
    shape=(4,5,6);a=np.array([[0,0,-3,30],[-2,0,0,8],[0,4,0,-12],[0,0,0,1]],float)
    r=make(shape,a,g.recipe(tensor_shape=(18,8,20),sampling_mm=1.,margin_mm=0))
    record=r['transform'];point=np.array([1,2,4,1])
    # Independent native→RAS index formula for this specifically constructed affine.
    ras=np.array([shape[2]-1-point[2],shape[0]-1-point[0],point[1],1])
    assert np.allclose(np.asarray(record['canonical_affine'])@ras,[18,6,-4,1])
    assert np.allclose(a@point,[18,6,-4,1])
    assert record['canonical_shape']==[6,4,5] and record['sampling_shape']==[18,8,20]
    assert record['uniform_scale']==1 and record['effective_spacing_mm']==[1.,1.,1.]
    assert r['reference_roundtrip'].shape==shape and r['fidelity']['metrics']['lesion']['recall']==1


def test_anisotropic_physical_aspect_and_odd_padding_are_explicit():
    a=np.diag([2.,3.,5.,1.]);a[:3,3]=[10,20,30]
    r=make((8,6,4),a,g.recipe(tensor_shape=(21,21,21),margin_mm=0),les=np.ones((8,6,4),np.uint8))
    t=r['transform'];assert t['roi_physical_extent_mm']==[16.,18.,20.] and t['sampling_shape']==[16,18,20]
    assert t['uniform_scale']==1.05 and t['normalized_shape']==[17,19,21]
    assert t['pad_low']==[2,1,0] and t['pad_high']==[2,1,0]
    assert len(set(t['effective_spacing_mm']))==1
    t=g.plan_geometry([7,9,11],np.eye(4),[[0,0,0],[7,9,11]],g.recipe(tensor_shape=(12,12,12),margin_mm=0),source_identity=IDENTITY,roi_origin='predicted_region')
    assert t['pad_low']==[2,1,0] and t['pad_high']==[2,1,0] # ceil dimensions8/10/12
    t=g.plan_geometry([5,6,7],np.eye(4),[[0,0,0],[5,6,7]],g.recipe(tensor_shape=(10,10,10),margin_mm=0),source_identity=IDENTITY,roi_origin='predicted_region')
    assert t['normalized_shape']==[8,9,10] and t['pad_low']==[1,0,0] and t['pad_high']==[1,1,0]


@pytest.mark.parametrize('axis',range(3))
@pytest.mark.parametrize('face',['low','high'])
def test_all_boundary_faces_retain_requested_and_realized_margin(axis,face):
    shape=(10,11,12);p=np.zeros(shape,np.uint8);s=[slice(3,6)]*3;s[axis]=slice(0,2) if face=='low' else slice(shape[axis]-2,shape[axis]);p[tuple(s)]=1
    box,m=g.select_pancreas_box(p,np.diag([1,2,3,1]),g.recipe(margin_mm=10))
    index=0 if face=='low' else 1
    assert m['source_face_contact'][index][axis] and m['realized_margin_mm'][index][axis]==0
    assert box[0][axis]==0 if face=='low' else box[1][axis]==shape[axis]


def test_lesion_perturbations_do_not_change_roi_or_image_and_outside_component_is_counted():
    shape=(12,12,12);p=np.zeros(shape,np.uint8);p[3:9,3:9,3:9]=1
    a=np.zeros_like(p);a[5,5,5]=1;b=a.copy();b[0,0,0]=1
    x=make(shape,r=g.recipe(tensor_shape=(12,12,12),margin_mm=0),pan=p,les=a)
    y=make(shape,r=g.recipe(tensor_shape=(12,12,12),margin_mm=0),pan=p,les=b)
    assert x['transform']==y['transform'] and np.array_equal(x['image'],y['image'])
    assert y['fidelity']['source_component_count']==2 and y['fidelity']['outside_pancreas_voxels']==1
    assert len(y['fidelity']['lost_or_displaced_component_ids'])==1 and not y['fidelity']['mechanical_survival_pass']
    assert sum(c['native_voxels'] for c in y['fidelity']['components'])==2


def test_single_slice_thick_target_all_components_and_class_precedence():
    shape=(9,11,7);p=np.ones(shape,np.uint8);l=np.zeros(shape,np.uint8);l[2:4,4:6,3]=1;l[7,9,0]=1
    r=make(shape,np.diag([1,1,7.5,1]),g.recipe(tensor_shape=(64,64,64),margin_mm=0),pan=p,les=l)
    assert r['fidelity']['source_component_count']==2 and r['fidelity']['all_components_survive']
    assert all(c['roundtrip_recall']==1 for c in r['fidelity']['components'])
    assert set(np.unique(r['target']))=={0,1,2} and not r['fidelity']['recipe_accepted']


def test_reference_negative_requires_verified_semantics_and_unknown_refused():
    z=np.zeros((7,9,11),np.uint8)
    r=make(les=z,state='verified_negative');assert r['fidelity']['source_component_count']==0
    assert r['fidelity']['metrics']['lesion']['dice'] is None and r['fidelity']['lesion_target_state']=='verified_negative'
    for state in ('positive','unknown','held'):
        with pytest.raises(ValueError):make(les=z,state=state)


def test_image_only_same_fixed_box_has_exact_parity_and_outside_probability_background():
    shape=(12,12,12);p=np.zeros(shape,np.uint8);p[3:9,3:9,3:9]=1;l=np.zeros_like(p);l[5,5,5]=1
    r=make(shape,pan=p,les=l,r=g.recipe(tensor_shape=(12,12,12),margin_mm=0))
    image=g.prepare_image(np.zeros(shape,np.float32),r['transform'],trusted_record_sha256=r['transform_sha256'])
    assert np.array_equal(image,r['image'])
    probabilities=np.zeros((3,12,12,12),np.float32);probabilities[2]=1
    restored=g.restore_probabilities(probabilities,r['transform'],trusted_record_sha256=r['transform_sha256'])
    assert restored[0,0,0,0]==1 and restored[1,0,0,0]==restored[2,0,0,0]==0
    assert restored[2,6,6,6]==1 and np.allclose(restored.sum(0),1)


def test_independent_linear_world_ramp_catches_axis_and_crop_offsets():
    shape=(16,18,20);coords=np.indices(shape);ct=(coords[0]+2*coords[1]+3*coords[2]).astype(np.float32)-100
    p=np.zeros(shape,np.uint8);p[3:13,3:15,3:17]=1;l=np.zeros_like(p);l[8,8,8]=1
    out=g.preprocess(ct,p,l,np.eye(4),g.recipe(tensor_shape=(20,20,20),margin_mm=0),source_identity=IDENTITY,lesion_target_state='positive')
    t=out['transform'];point=np.array([10,10,10,1]);world=np.asarray(t['tensor_affine'])@point
    expected=(world[0]+2*world[1]+3*world[2])/350
    assert out['image'][10,10,10]==pytest.approx(expected,abs=1e-6)
    assert abs(out['image'][10,10,10]-(world[1]+2*world[0]+3*world[2])/350)>1e-4


@pytest.mark.parametrize('field',['tensor_affine','source_affine','box_ras_half_open','pad_low','uniform_scale','orientation_forward','source_identity'])
def test_changed_transform_rejected_even_if_its_local_hash_is_refreshed(field):
    r=make();bad=deepcopy(r['transform'])
    if field in ('source_affine','tensor_affine'):bad[field][0][3]+=1
    elif field=='box_ras_half_open':bad[field][0][0]+=1
    elif field=='pad_low':bad[field][0]+=1
    elif field=='uniform_scale':bad[field]*=2
    elif field=='orientation_forward':bad[field][0][1]*=-1
    else:bad[field]['ct_sha256']='b'*64
    bad['record_sha256']=content_hash({k:v for k,v in bad.items() if k!='record_sha256'})
    with pytest.raises(ValueError):g.validate_record(bad,r['transform_sha256'])
    if field not in ('source_identity',):
        with pytest.raises(ValueError):g.validate_record(bad,content_hash(bad))


@pytest.mark.parametrize('fault',['empty_box','overflow_box','singular','nonfinite','oblique','shear','oversize','sampling_cap','empty_pancreas','nan_ct','bad_label'])
def test_invalid_or_unsupported_inputs_fail_bounded_preflight(fault):
    shape=[7,9,11];a=np.eye(4);box=[[0,0,0],shape.copy()];r=g.recipe()
    if fault=='empty_box':box[1][0]=0
    if fault=='overflow_box':box[1][0]=100
    if fault=='singular':a[0,0]=0
    if fault=='nonfinite':a[1,1]=np.nan
    if fault=='oblique':a[:2,:2]=[[.8,-.6],[.6,.8]]
    if fault=='shear':a[0,1]=.01
    if fault=='oversize':shape=[512,512,512]
    if fault=='sampling_cap':a[0,0]=1e9
    with pytest.raises(ValueError):
        if fault in ('empty_pancreas','nan_ct','bad_label'):
            ct=np.zeros(shape,np.float32);p=np.ones(shape,np.uint8);l=np.zeros(shape,np.uint8);l[2,3,4]=1
            if fault=='empty_pancreas':p[:]=0
            if fault=='nan_ct':ct[0,0,0]=np.nan
            if fault=='bad_label':l[0,0,0]=2
            g.preprocess(ct,p,l,a,r,source_identity=IDENTITY,lesion_target_state='positive')
        else:g.plan_geometry(shape,a,box,r,source_identity=IDENTITY,roi_origin='predicted_region')


@pytest.mark.parametrize('fault',['nan','unnormalized','wrong_grid','negative','extra_class'])
def test_bad_probabilities_refused(fault):
    r=make();p=np.zeros((3,7,9,11),np.float32);p[0]=1
    if fault=='nan':p[0,0,0,0]=np.nan
    if fault=='unnormalized':p[0]=.5
    if fault=='negative':p[1]=-.1
    if fault=='wrong_grid':p=p[:,:,:,:-1]
    if fault=='extra_class':p=np.concatenate([p,p[:1]])
    with pytest.raises(ValueError):g.restore_probabilities(p,r['transform'],trusted_record_sha256=r['transform_sha256'])
