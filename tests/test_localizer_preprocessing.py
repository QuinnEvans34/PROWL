import json
from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest
import torch
from src.data.localizer_preprocessing import preprocess,restore_to_source


def recipe():
    r=json.loads(Path('configs/capstone/localizer-preprocessing-v1.json').read_bytes())
    r.update(spacing_mm=[1,1,1],minimum_shape=[8,8,8],max_output_voxels=100000)
    return r


@pytest.mark.parametrize('affine',[
    np.diag([1,1,1,1]),
    np.array([[-1,0,0,7],[0,-1,0,7],[0,0,1,0],[0,0,0,1]]),
    np.array([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]])])
def test_orientation_landmark_restores_exactly(affine):
    label=np.zeros((8,8,8),np.uint8);label[2:5,3,1:4]=1
    image=label.astype('float32')*400-100
    result=preprocess(image,affine,recipe(),target=label)
    back=restore_to_source(result['label'],result['transform_record'],discrete=True)
    np.testing.assert_array_equal(back[0].numpy(),label)
    assert np.allclose(back.affine,affine)


def test_anisotropic_oblique_grid_and_single_channel():
    theta=.2;rot=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1.]])
    a=np.eye(4);a[:3,:3]=rot@np.diag([1,2,4]);a[:3,3]=[13,-7,21]
    label=np.zeros((9,9,9),np.uint8);label[3:6,3:6,3:6]=1
    x=preprocess(label*300.,a,recipe(),target=label)
    back=restore_to_source(x['label'],x['transform_record'],discrete=True)
    assert back.shape==(1,9,9,9) and np.allclose(back.affine,a)
    assert set(torch.unique(x['label']).tolist())<={0,1}
    assert float(back.sum())>0


def test_inference_image_identical_and_no_target_crop_or_mutation():
    image=np.arange(1000,dtype=np.float32).reshape(10,10,10)-500;before=image.copy()
    mask=np.zeros_like(image,dtype=np.uint8);mask[2:4,2:4,2:4]=1
    r=recipe();train=preprocess(image,np.eye(4),r,target=mask)
    infer=preprocess(image,np.eye(4),r)
    other=preprocess(image,np.eye(4),r,target=1-mask)
    assert torch.equal(train['image'],infer['image']) and torch.equal(train['image'],other['image'])
    np.testing.assert_array_equal(image,before)
    assert train['image'].min()==0 and train['image'].max()==1
    assert 'label' not in infer


def test_fractional_probabilities_are_not_nearest_labels():
    r=recipe();r['spacing_mm']=[2,2,2]
    x=preprocess(np.zeros((9,9,9)),np.eye(4),r)
    v=torch.zeros_like(x['image']);v[:,:,4:,:]=1
    back=restore_to_source(v,x['transform_record'],discrete=False)
    assert torch.any((back>0)&(back<1))


@pytest.mark.parametrize('fault',['labels','geometry','nan','cache','crop','budget','record'])
def test_invalid_inputs_and_trace_refused(fault):
    r=recipe();image=np.zeros((8,8,8));target=np.zeros_like(image);a=np.eye(4)
    if fault=='labels':target[0,0,0]=2
    if fault=='geometry':a[0,0]=0
    if fault=='nan':image[0,0,0]=np.nan
    if fault=='cache':r['cache']='disk'
    if fault=='crop':r['crop']='pancreas'
    if fault=='budget':r['spacing_mm']=[.001]*3
    if fault=='record':
        x=preprocess(image,a,r);record=deepcopy(x['transform_record']);record['source_affine'][0][3]=5
        with pytest.raises(ValueError,match='record changed'):restore_to_source(x['image'],record,discrete=False)
        return
    with pytest.raises(ValueError):preprocess(image,a,r,target=target)


def test_disappearing_thin_target_requires_recipe_review():
    r=recipe();r['spacing_mm']=[3,3,3]
    target=np.zeros((8,8,8));target[1,1,1]=1
    with pytest.raises(ValueError,match='lost the entire'):
        preprocess(np.zeros_like(target),np.eye(4),r,target=target)
