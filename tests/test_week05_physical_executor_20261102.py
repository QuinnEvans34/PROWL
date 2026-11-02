import copy
import json
import os
from pathlib import Path
import sys
import numpy as np
import pytest
import torch
from src.inference.physical_cascade_v1 import segment,embed,hard_codes,predict
from src.inference.predicted_physical_region_v1 import prepare
from scripts.diagnostics import qualify_physical_cascade_20261102 as launch


class Constant(torch.nn.Module):
    def forward(self,x):
        return torch.cat((torch.zeros_like(x),torch.ones_like(x),2*torch.ones_like(x)),dim=1)


def test_actual_physical_tiling_probability_native_roundtrip():
    image=np.zeros((9,8,7),np.float32);mask=np.ones(image.shape,np.uint8)
    affine=np.array([[0,-2,0,11],[-1,0,0,13],[0,0,3,-4],[0,0,0,1.]])
    region=prepare(image,mask,affine,base_margin_mm=0,extra_margin_mm=[0]*3,max_region_voxels=1000)
    codes,prob,info=segment(Constant(),region,device='cpu',max_tiles=1)
    assert codes.shape==image.shape and np.all(codes==2)
    assert info['gap_voxels']==0 and info['minimum_blend_weight']>0
    assert np.allclose(prob.sum(0),1,atol=2e-5)
    expected=torch.softmax(torch.tensor([0.,1.,2.]),0).numpy()
    assert np.allclose(prob,expected[:,None,None,None])


def test_existing_control_predictor_equivalence_at_multiple_tile_edges():
    from contextlib import nullcontext
    from types import SimpleNamespace
    from src.training.segmenter_physical_windows_session_v1 import predict_native
    class Varying(torch.nn.Module):
        def forward(self,x):return torch.cat((x,1-x,torch.full_like(x,.6)),1)
    image=np.linspace(-100,250,147*5*7,dtype=np.float32).reshape(147,5,7)
    r=prepare(image,np.ones(image.shape,np.uint8),np.eye(4),base_margin_mm=0,
        extra_margin_mm=[0]*3,max_region_voxels=image.size)
    model=Varying();s=SimpleNamespace(model=model,device='cpu',_clean=lambda:None,rng_scope=nullcontext)
    old,old_info=predict_native(s,r['image'],r['geometry'])
    new,prob,info=segment(model,r,device='cpu',max_tiles=2)
    assert np.array_equal(new,embed(old,r))
    for key in ('tiles','minimum_blend_weight','gap_voxels'):assert old_info[key]==info[key]


def test_hard_decision_ties_and_invalid_probabilities():
    p=np.ones((3,2,3,4),np.float32)/3
    assert not hard_codes(p).any()
    p[0,0,0,0]=np.nan
    with pytest.raises(ValueError):hard_codes(p)
    with pytest.raises(ValueError):hard_codes(np.zeros((3,2,3,4)))


def test_budget_and_cancellation_before_forward():
    r=prepare(np.zeros((5,6,7)),np.ones((5,6,7)),np.eye(4),base_margin_mm=0,extra_margin_mm=[0]*3,max_region_voxels=1000)
    with pytest.raises(ValueError,match='tile budget'):segment(Constant(),r,device='cpu',max_tiles=0)
    def cancel(*args):raise KeyboardInterrupt('cancelled')
    with pytest.raises(KeyboardInterrupt):segment(Constant(),r,device='cpu',max_tiles=1,progress=cancel)
    with pytest.raises(ValueError):embed(np.zeros((1,1,1)),r)


def test_nonfinite_model_rejected():
    class Bad(Constant):
        def forward(self,x):return super().forward(x)*float('nan')
    r=prepare(np.zeros((5,6,7)),np.ones((5,6,7)),np.eye(4),base_margin_mm=0,extra_margin_mm=[0]*3,max_region_voxels=1000)
    with pytest.raises(ValueError,match='logits'):segment(Bad(),r,device='cpu',max_tiles=1)


@pytest.mark.parametrize('empty',[False,True])
def test_full_ct_only_chain_and_empty_localization(empty):
    class Locator(torch.nn.Module):
        def forward(self,x):
            return torch.cat((torch.ones_like(x) if empty else torch.zeros_like(x),
                              torch.zeros_like(x) if empty else torch.ones_like(x)),1)
    recipe=dict(schema_version='4.0.0',component='pancreas-localizer-preprocessing-v4',orientation='RAS',
        image_interpolation='bilinear',target_interpolation='nearest',padding_mode='constant_zero',
        crop='none',augmentation='none',cache='none',workers=0,spacing_mm=[2.,2.,2.],hu_window=[-100.,300.],
        minimum_shape=[96]*3,max_source_voxels=96_000_000,max_output_voxels=16_000_000)
    kwargs=dict(localizer=Locator(),segmenter=Constant(),localizer_recipe=recipe,device='cpu',
                max_region_voxels=1000,max_tiles=1)
    image=np.zeros((5,6,7),np.float32)
    if empty:
        with pytest.raises(ValueError,match='Nonempty binary'):predict(image,np.eye(4),**kwargs)
    else:
        codes,mask,prob,info=predict(image,np.eye(4),**kwargs)
        assert codes.shape==mask.shape==image.shape and np.all(codes==2) and np.all(mask==1)
        assert info['localizer_policy']=='all_support' and not info['reference_inputs_used']


def request():
    return dict(version='physical-cascade-qualification-1',case_id='PanTS_00001070',ct_path='ct.nii.gz',
        ct_sha256=launch.CT_SHA,source_shape=[1,2,3],source_affine=np.eye(4).tolist(),units='mm',
        models={k:dict(path=k+'.pt',sha256=v) for k,v in launch.MODEL_SHA.items()},localizer_recipe={},
        policy='all_support',limits=copy.deepcopy(launch.LIMITS),comparison=copy.deepcopy(launch.COMPARISON),
        output=str(launch.BASE/'output'),backup=str(launch.BACKUP),pins={},environment={})


@pytest.mark.parametrize('field,value',[('case_id','PanTS_00000001'),('policy','largest_component_26'),
    ('units','unknown'),('limits',{}),('comparison',{}),('models',{}),('reference_path','lesion.nii')])
def test_request_rejects_changes_and_reference_paths(field,value):
    r=request();launch.validate_request(r);r[field]=value
    with pytest.raises(ValueError):launch.validate_request(r)


def test_request_hash_binding(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'BASE',tmp_path)
    (tmp_path/'request.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'):launch.check_request('0'*64)


@pytest.mark.skipif(os.name!='nt',reason='Windows Job Object lifecycle')
@pytest.mark.parametrize('action',['normal','timeout','cancel','failed'])
def test_real_owned_supervisor_cleanup(tmp_path,action):
    code="import time; time.sleep(10)" if action in ('timeout','cancel') else ('raise RuntimeError("expected")' if action=='failed' else 'print("ok")')
    def tick():
        if action=='cancel':raise KeyboardInterrupt('cancel')
    kwargs=dict(log=tmp_path/(action+'.log'),seconds=.5 if action=='timeout' else 20,rss_bytes=1024**3,tick=tick)
    if action=='normal':launch.supervise([sys.executable,'-c',code],**kwargs)
    else:
        with pytest.raises((RuntimeError,KeyboardInterrupt)):launch.supervise([sys.executable,'-c',code],**kwargs)
    r=json.loads((tmp_path/(action+'.resources.json')).read_text())
    assert r['workers_reaped'] and r['success']==(action=='normal')


def test_duplicate_dispatch_refused(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'BASE',tmp_path)
    monkeypatch.setattr(launch,'check_request',lambda pin:request())
    (tmp_path/'worker.log').write_text('previous attempt')
    with pytest.raises(FileExistsError):launch.run('pin')
