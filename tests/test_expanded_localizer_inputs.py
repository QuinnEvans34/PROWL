import json
from copy import deepcopy
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest
import torch
from scripts.diagnostics.localizer_content_verify import signature
from src.data.manifest_records import digest
from src.data.expanded_localizer_inputs import ExpandedDataset,ReadBudget,descriptors,open_expanded_inputs
from src.data.localizer_preprocessing_v2 import preprocess,restore_to_source,plan_geometry
from src.data.source_inventory_records import content_hash


def recipe():
    r=json.loads(Path('configs/capstone/localizer-preprocessing-v2.json').read_bytes())
    r.update(spacing_mm=[1.,1.,1.],minimum_shape=[8,8,8],max_output_voxels=100000)
    return r


def fixture(tmp_path,operation='optimizer'):
    root=tmp_path.resolve();role={'optimizer':'train','evaluator':'validation'}[operation]
    a=np.array([[-1.,0,0,9],[0,-1.,0,9],[0,0,1.,0],[0,0,0,1.]])
    target=np.zeros((10,10,10),np.uint8);target[1:4,2:5,0:3]=1
    refs={};rows={}
    for kind,arr in [('ct',np.arange(1000,dtype=np.int16).reshape(10,10,10)),('pancreas',target)]:
        im=nib.Nifti1Image(arr,a);im.header.set_xyzt_units('mm' if kind=='ct' else 'unknown');p=root/(kind+'.nii.gz');nib.save(im,p)
        stat=signature(p.stat());size=stat.pop('bytes');refs[kind]=dict(root_alias='followup_source',uri=p.name,bytes=size,content_sha256=digest(p.read_bytes()),media_type='application/gzip')
        rows[kind]=dict(study_id='pants:study:PanTS_00000001',protected_role=role,kind=kind,uri=p.name,bytes=size,observation=stat)
    d=dict(study_id='pants:study:PanTS_00000001',protected_role=role,operation=operation,mapping={'policy_id':'pants-semantic-binary-atol1e-6-v1'},
        image=refs['ct'],target=refs['pancreas'],rows=rows,geometry=dict(shape_xyz=[10]*3,affine_ras=a.ravel().tolist(),spacing_mm_xyz=[1.]*3))
    return d,target,root


@pytest.mark.parametrize('operation',['optimizer','evaluator'])
def test_exact_bytes_role_and_restore(tmp_path,operation):
    d,target,root=fixture(tmp_path,operation);budget=ReadBudget();dataset=ExpandedDataset([d],root,lambda:None,recipe(),budget,operation)
    wrong='evaluator' if operation=='optimizer' else 'optimizer'
    with pytest.raises(ValueError,match='operation/role'):dataset.load_native(0,operation=wrong)
    assert budget.files==0
    x=dataset.load(0,operation=operation);back=restore_to_source(x['label'],x['transform_record'],discrete=True)
    np.testing.assert_array_equal(back[0].numpy(),target);assert budget.files==2
    assert x['transform_record']['schema_version']=='2.0.0'


@pytest.mark.parametrize('fault',['stat','hash','symlink','descriptor','budget','recipe'])
def test_refuses_changed_inputs(tmp_path,fault):
    d,_,root=fixture(tmp_path);budget=ReadBudget()
    if fault=='hash':d['image']['content_sha256']='0'*64
    if fault=='stat':d['rows']['ct']['observation']['mtime_ns']-=1
    if fault=='symlink':
        p=root/'ct.nii.gz';p.rename(root/'other.nii.gz');p.symlink_to('other.nii.gz')
    dataset=ExpandedDataset([d],root,lambda:None,recipe(),budget,'optimizer')
    if fault=='descriptor':dataset._items[0]['protected_role']='validation'
    if fault=='recipe':dataset._recipe['spacing_mm']=[2,2,2]
    if fault=='budget':budget.compressed=1024**3
    with pytest.raises((ValueError,OSError)):dataset.load_native(0,operation='optimizer')


def test_header_only_large_projection_and_preallocation_refusal():
    r=recipe();r.update(spacing_mm=[3]*3,max_output_voxels=8000000)
    assert plan_geometry([512,512,200],np.eye(4),r)['source_voxels']==52428800
    with pytest.raises(ValueError,match='Source voxel'):plan_geometry([512,512,300],np.eye(4),r)
    r['spacing_mm']=[.01]*3
    with pytest.raises(ValueError,match='Projected'):plan_geometry([10]*3,np.eye(4),r)
    # A huge broadcast view must be refused before finite-mask or image-copy allocation.
    r=recipe();huge=np.broadcast_to(np.zeros(1),(10000,10000,10000))
    with pytest.raises(ValueError,match='Source voxel'):preprocess(huge,np.eye(4),r)


def test_target_independence_boundary_and_v1_compatibility():
    from src.data.localizer_preprocessing import preprocess as old
    r=recipe();image=np.arange(1000,dtype=np.float32).reshape(10,10,10)-200
    target=np.zeros(image.shape,np.uint8);target[:3,2:5,2:5]=1
    trained=preprocess(image,np.eye(4),r,target=target);inferred=preprocess(image,np.eye(4),r)
    other=preprocess(image,np.eye(4),r,target=1-target)
    assert torch.equal(trained['image'],inferred['image']) and torch.equal(inferred['image'],other['image'])
    v1={k:v for k,v in r.items() if k!='max_source_voxels'};v1.update(schema_version='1.0.0',component='pancreas-localizer-preprocessing-v1')
    previous=old(image,np.eye(4),v1,target=target)
    assert torch.equal(previous['image'],trained['image']) and torch.equal(previous['label'],trained['label'])
    assert trained['label'].sum()>0
    with pytest.raises(ValueError):old(image,np.eye(4),r)


def test_small_target_loss_and_changed_restoration_refused():
    r=recipe();r['spacing_mm']=[3]*3;target=np.zeros((8,8,8));target[1,1,1]=1
    with pytest.raises(ValueError,match='lost the entire'):preprocess(np.zeros_like(target),np.eye(4),r,target=target)
    x=preprocess(np.zeros_like(target),np.eye(4),recipe());record=deepcopy(x['transform_record']);record['source_shape']=[99999]*3
    with pytest.raises(ValueError,match='record changed'):restore_to_source(x['image'],record,discrete=False)


def test_capability_is_checked_before_storage_access(tmp_path):
    with pytest.raises(ValueError,match='Unreviewed'):
        open_expanded_inputs(repo=tmp_path,capability_bytes=b'{}',trusted_capability_sha256='0'*64,recipe_bytes=b'{}',trusted_recipe_sha256='0'*64)


def test_descriptor_refuses_held_and_wrong_permissions():
    from test_localizer_expansion import inputs
    from src.data.localizer_expansion import derive,freeze_records
    args=inputs();m,q,e=derive(**args);expected={r:[c['study_id'] for c in args['selection']['candidates'][r]] for r in ('train','validation')}
    parents,children=freeze_records(m,q,e,None,expected_members=expected)
    d=dict(manifest=m,qualifications=q,cohorts=children,accounting={'executable_ids':expected})
    # This refusal happens before touching source rows, which are intentionally only minimal fixtures.
    for mutation in ('held','permission'):
        broken=deepcopy(d)
        if mutation=='held':broken['qualifications'][1]['outcome']='held'
        else:
            aid=q[1]['annotation_id'];next(a for a in broken['manifest']['annotations'] if a['annotation_id']==aid)['allowed_uses']=['training_target']
        with pytest.raises(ValueError):descriptors(broken,{'content':{'selection.json':json.dumps(args['selection'])}},'evaluator')


def test_review_sheet_accepts_serialized_affine_and_canonicalizes_source():
    from scripts.diagnostics.expanded_localizer_preprocessing import sheet
    from PIL import Image
    import io
    a=np.diag([-1.,-1.,1.,1.]);image=np.zeros((8,8,8),np.float32);mask=np.zeros_like(image,np.uint8);mask[2:5,2:5,2:5]=1
    x=preprocess(image,a,recipe(),target=mask);back=restore_to_source(x['label'],x['transform_record'],discrete=True)[0].numpy().astype(np.uint8)
    data=sheet(image,mask,back,a,x['image'][0].numpy(),x['label'][0].numpy().astype(np.uint8),x['transform_record'],'invented case')
    im=Image.open(io.BytesIO(data));assert im.size==(1600,1080)


def test_live_decoder_must_match_qualified_implementation():
    from src.data.expanded_localizer_inputs import verify_live_mapping
    item={'mapping':{'policy_id':'pants-semantic-binary-atol1e-6-v1','policy_sha256':digest(b'approved fixture')}}
    verify_live_mapping([item],b'approved fixture')
    with pytest.raises(ValueError,match='Live binary'):verify_live_mapping([item],b'changed fixture')
