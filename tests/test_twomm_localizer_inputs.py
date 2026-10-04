"""Synthetic role/resource/geometry checks for D-297; no real source reads."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from monai.transforms import SpatialResample
from monai.data import MetaTensor
from src.data.twomm_localizer_inputs import ExpandedDataset,ReadBudget,validate_bundle,descriptors
from src.data.localizer_preprocessing_v4 import preprocess,restore_to_source,plan_geometry
from test_expanded_localizer_inputs import fixture


def recipe():
    r=json.loads(Path('configs/capstone/localizer-preprocessing-v4.json').read_text())
    r.update(spacing_mm=[1.,1.,1.],minimum_shape=[8,8,8],max_output_voxels=100000)
    return r


def scoped(tmp_path,operation='optimizer'):
    d,target,root=fixture(tmp_path,operation)
    for row in d['rows'].values():row['expanded_bytes']=2352 if row['kind']=='ct' else 1352
    return d,target,root


@pytest.mark.parametrize('op',['optimizer','evaluator'])
def test_role_scoped_native_source_and_no_repeat(tmp_path,op):
    d,target,root=scoped(tmp_path,op);budget=ReadBudget([d]);dataset=ExpandedDataset([d],root,lambda:None,recipe(),budget,op)
    with pytest.raises(ValueError,match='operation/role'):dataset.load(0,operation='evaluator' if op=='optimizer' else 'optimizer')
    x=dataset.load(0,operation=op);back=restore_to_source(x['label'],x['transform_record'],discrete=True)
    np.testing.assert_array_equal(back[0].numpy(),target)
    assert budget.files==2 and budget.expanded==3704
    with pytest.raises(ValueError,match='repeated'):dataset.load(0,operation=op)


@pytest.mark.parametrize('fault',['uri','bytes','expanded','hash','descriptor','recipe'])
def test_scoped_input_mutations_refused(tmp_path,fault):
    d,_,root=scoped(tmp_path);budget=ReadBudget([d]);ds=ExpandedDataset([d],root,lambda:None,recipe(),budget,'optimizer')
    if fault=='uri':ds._items[0]['rows']['ct']['uri']='other.nii.gz'
    elif fault=='bytes':budget.expected['ct.nii.gz']['bytes']+=1
    elif fault=='expanded':budget.expected['ct.nii.gz']['expanded_bytes']-=1
    elif fault=='hash':ds._items[0]['image']['content_sha256']='0'*64
    elif fault=='descriptor':ds._items[0]['operation']='evaluator'
    else:ds._recipe['spacing_mm']=[2]*3
    with pytest.raises(ValueError):ds.load_native(0,operation='optimizer')


def test_large_geometry_refused_before_allocation_and_v2_unchanged():
    from src.data.localizer_preprocessing_v2 import plan_geometry as prior
    r=recipe();r.update(spacing_mm=[3]*3,max_output_voxels=8000000)
    assert plan_geometry([480,400,500],np.diag([.8,.8,1.2,1.]),r)['source_voxels']==96000000
    with pytest.raises(ValueError):plan_geometry([480,400,501],np.eye(4),r)
    old=json.loads(Path('configs/capstone/localizer-preprocessing-v2.json').read_text())
    with pytest.raises(ValueError):prior([480,400,500],np.eye(4),old)
    with pytest.raises(ValueError):preprocess(np.broadcast_to(np.zeros(1),(10000,10000,10000)),np.eye(4),r)


@pytest.mark.parametrize('discrete',[True,False])
@pytest.mark.parametrize('oblique',[True,False])
def test_slab_restore_matches_full_resample(discrete,oblique):
    r=recipe();r.update(spacing_mm=[2,2,2]);a=np.diag([1.,1.,1.,1.]);a[:3,3]=[-12,4,6]
    if oblique:
        angle=.23;a[:2,:2]=[[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]
    image=np.arange(18*20*41,dtype=np.float32).reshape(18,20,41)%400-100
    target=np.zeros(image.shape,np.uint8);target[3:14,5:15,8:35]=1
    x=preprocess(image,a,r,target=target);values=x['label'] if discrete else x['image']
    expected=SpatialResample(mode='nearest' if discrete else 'bilinear',padding_mode='zeros',align_corners=False)(MetaTensor(values.as_tensor().clone(),affine=x['transform_record']['processed_affine']),dst_affine=a,spatial_size=list(image.shape))
    actual=restore_to_source(values,x['transform_record'],discrete=discrete)
    if discrete:assert torch.equal(actual,expected)
    else:assert torch.allclose(actual,expected,atol=2e-5,rtol=0)
    np.testing.assert_allclose(actual.affine,a)


def test_v2_image_transform_parity_and_tiny_target_loss():
    from src.data.localizer_preprocessing_v2 import preprocess as old
    r=recipe();image=np.zeros((8,8,20),np.float32);target=np.ones(image.shape,np.uint8)
    x=preprocess(image,np.eye(4),r,target=target);infer=preprocess(image,np.eye(4),r)
    prior=deepcopy(r);prior.update(schema_version='2.0.0',component='pancreas-localizer-preprocessing-v2',max_source_voxels=64000000)
    y=old(image,np.eye(4),prior,target=target)
    assert torch.equal(x['image'],infer['image']) and torch.equal(x['image'],y['image']) and torch.equal(x['label'],y['label'])
    r['spacing_mm']=[3]*3;target[:]=0;target[1,1,1]=1
    with pytest.raises(ValueError,match='lost the entire'):preprocess(image,np.eye(4),r,target=target)


def test_published_bundle_pins_cannot_be_supplied_by_untrusted_bytes():
    with pytest.raises(ValueError):validate_bundle({'inputs.json':b'{}','derived.json':b'{}'})
    with pytest.raises(ValueError):validate_bundle({'inputs.json':b'{}'})


@pytest.mark.parametrize('fault',['held','permission','purpose','accounting','pin'])
def test_descriptor_refuses_unqualified_or_wrong_role_records(fault):
    from test_localizer_expansion import inputs
    from src.data.localizer_expansion import derive,freeze_records
    args=inputs();m,q,e=derive(**args);expected={r:[c['study_id'] for c in args['selection']['candidates'][r]] for r in ('train','validation')}
    _,children=freeze_records(m,q,e,None,expected_members=expected)
    d=dict(manifest=m,qualifications=q,cohorts=children,accounting={'executable_ids':expected})
    val=next(x for x in q if x['protected_role']=='validation')
    if fault=='held':val['outcome']='held'
    elif fault=='permission':next(a for a in m['annotations'] if a['annotation_id']==val['annotation_id'])['allowed_uses']=['training_target']
    elif fault=='purpose':val['purpose']='pancreas_localizer_training'
    elif fault=='pin':next(c for c in children if c['protected_role']=='validation')['members'][0]['qualification']['sha256']='0'*64
    else:d['accounting']['executable_ids']['validation']=[]
    with pytest.raises(ValueError):descriptors(d,{'selection_files':{'selection.json':json.dumps(args['selection'])}},'evaluator')


def test_exact_batch_plan_covers_each_member_once():
    cap=json.loads(Path('docs/capstone/data/TWOMM-LOCALIZER-INPUT-CAPABILITY-2026-09-30.json').read_text())
    ids=[sid for b in cap['batches'] for sid in b['study_ids']]
    assert len(ids)==len(set(ids))==153
    assert set(ids)==set(cap['members']['optimizer']+cap['members']['evaluator'])
    assert [len(b['study_ids']) for b in cap['batches']]==[4]+[16]*9+[1]*5


def test_resource_receipt_cannot_claim_readiness_without_rehearsal():
    from scripts.diagnostics.twomm_localizer_preprocessing import verify_resource
    with pytest.raises(ValueError,match='Resource receipt'):verify_resource(b'{}','0'*64)


def test_pinned_bundle_callback_returns_the_retained_validation_report(monkeypatch):
    import src.data.twomm_localizer_inputs as module
    from src.data.manifest_records import digest
    files={'inputs.json':b'synthetic inputs','derived.json':b'synthetic derived'}
    monkeypatch.setattr(module,'INPUTS',digest(files['inputs.json']));monkeypatch.setattr(module,'DERIVED',digest(files['derived.json']))
    report=module.validate_bundle(files)
    assert report==dict(bundle_id=module.BUNDLE_ID,manifest_sha256=module.MANIFEST,qualified_count=153,held_count=23,
        executable_counts={'train':113,'validation':40},protected_counts={'train':7200,'validation':1800,'test':901},
        prior_issues_preserved=23,source_arrays_opened=False)
    files['derived.json']+=b'changed'
    with pytest.raises(ValueError):module.validate_bundle(files)


def test_candidate_envelope_is_versioned_and_old_limit_unchanged():
    from src.data.localizer_preprocessing_v3 import plan_geometry as old_plan
    old=json.loads(Path('configs/capstone/localizer-preprocessing-v3.json').read_text());old['spacing_mm']=[2.,2.,2.]
    new=json.loads(Path('configs/capstone/localizer-preprocessing-v4.json').read_text())
    shape=[480,400,500];affine=np.diag([1.08,1.08,1.08,1.])
    with pytest.raises(ValueError,match='budget'):old_plan(shape,affine,old)
    p=plan_geometry(shape,affine,new);assert 15000000<p['conservative_output_voxels']<=16000000
    too_large=np.diag([1.2,1.2,1.2,1.])
    with pytest.raises(ValueError,match='budget'):plan_geometry(shape,too_large,new)


def test_candidate_does_not_raise_source_cap():
    r=json.loads(Path('configs/capstone/localizer-preprocessing-v4.json').read_text())
    with pytest.raises(ValueError,match='Source voxel cap'):plan_geometry([480,400,501],np.eye(4),r)
