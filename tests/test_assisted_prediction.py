import numpy as np
import nibabel as nib
import pytest
from src.inference.assisted_prediction import predict_array, source_box, checked_images
from src.inference.assisted_windows import geometry, orient, tiles, physical_geometry, sample_window, PhysicalReconstructor

@pytest.mark.parametrize('affine',[np.diag([.7,.8,5.,1.]),np.array([[0,-.7,0,4],[.8,0,.1,2],[0,0,-2,9],[0,0,0,1.]])])
def test_reconstruction_on_permuted_flipped_oblique_native_grids(affine):
    shape=(5,6,7);image=np.zeros(shape,np.float32);pancreas=np.ones(shape,np.uint8)
    seen=[]
    def probabilities(patch):
        seen.append(patch.copy());p=np.zeros((3,*patch.shape),np.float32);p[1]=.6;p[2]=.4;return p
    codes,r=predict_array(image,pancreas,affine,probabilities,window=16,stride=8)
    assert codes.shape==shape and np.all(codes==1) and r['uncovered_region_voxels']==0
    assert r['tiles']==len(seen) and r['minimum_blend_weight']>0
    assert all(p.dtype==np.float32 and 0<=p.min()<=p.max()<=1 for p in seen)

def test_normalization_tie_break_and_padding():
    image=np.array([-1000,-100,0,250,1000],np.float32)[:,None,None]*np.ones((1,2,2),np.float32)
    seen=[]
    def probabilities(patch):
        seen.append(patch);return np.full((3,*patch.shape),1/3,dtype=np.float32)
    codes,_=predict_array(image,np.ones(image.shape,np.uint8),np.eye(4),probabilities,window=8,stride=4)
    assert np.all(codes==0);np.testing.assert_allclose(seen[0][:5,0,0],[0,0,100/350,1,1],rtol=1e-6)
    assert np.all(seen[0][5:]==0)

def test_region_reinsertion_uses_prediction_not_assistance():
    shape=(15,15,15);image=np.zeros(shape,np.float32);mask=np.zeros(shape,np.uint8);mask[7,7,7]=1
    affine=np.diag([30.,30.,30.,1.])
    def probs(patch):
        p=np.zeros((3,*patch.shape),np.float32);p[2]=1;return p
    # Large acquired spacing would require many physical tiles: refuse before allocations/callback.
    with pytest.raises(ValueError,match='tile budget'):
        predict_array(image,mask,affine,probs,window=8,stride=4,max_tiles=1)
    lo,hi=source_box(mask,affine)
    assert lo.tolist()==[3,4,3] and hi.tolist()==[12,11,12]

def test_native_oracle_preserves_labels_through_physical_sampling():
    native=geometry((7,9,5),np.diag([.8,2.,3.,1.]));r=physical_geometry(native)
    labels=np.random.default_rng(8).integers(0,3,size=(7,9,5),dtype=np.uint8)
    ts=tiles(r['shape'],16,8);recon=PhysicalReconstructor(r,window=16)
    for origin in ts:
        patch,_=sample_window(labels,r,origin,order=0,window=16)
        recon.add(origin,np.stack([patch==k for k in range(3)]).astype(np.float32))
    np.testing.assert_array_equal(recon.finish(ts).argmax(0),labels)
    with pytest.raises(ValueError,match='Duplicate'):recon.add(ts[0],np.zeros((3,16,16,16),np.float32))

@pytest.mark.parametrize('fault',['units','affine','mask','empty','nan'])
def test_invalid_inputs_are_refused(tmp_path,fault):
    ct=nib.Nifti1Image(np.zeros((4,4,4),np.float32),np.eye(4));ct.header.set_xyzt_units('mm')
    mask=nib.Nifti1Image(np.ones((4,4,4),np.uint8),np.eye(4));mask.header.set_xyzt_units('mm')
    if fault=='units':mask.header.set_xyzt_units('unknown')
    if fault=='affine':mask.affine[0,3]=4
    if fault=='mask':mask.dataobj[:]=2
    if fault=='empty':mask.dataobj[:]=0
    if fault=='nan':ct.dataobj[:]=np.nan
    nib.save(ct,tmp_path/'ct.nii.gz');nib.save(mask,tmp_path/'mask.nii.gz')
    with pytest.raises(ValueError):checked_images(tmp_path/'ct.nii.gz',tmp_path/'mask.nii.gz')

def test_model_loader_uses_only_strict_model_state_without_optimizer(monkeypatch):
    import torch
    from monai.networks.nets import SegResNet
    from src.inference.assisted_prediction import ARCH,load_model
    import copy
    net=SegResNet(spatial_dims=3,in_channels=1,out_channels=3,init_filters=16,norm=('GROUP',{'num_groups':8}),blocks_down=(1,2,2,4),blocks_up=(1,1,1),dropout_prob=None)
    weights=net.state_dict()
    payload={'session':{'version':1,'identity':{'version':'pancreas-region-session-1','raw':{'architecture':ARCH},'policy':{'extra_margin_mm':[81.,43.,71.],'base_margin_mm':10.}},'raw':{'version':2,'identity':{'architecture':ARCH},'model':weights,'optimizer':'must not restore','cpu_rng':'must not restore'}}}
    calls=[]
    def load(path,**kwargs):calls.append(kwargs);return payload
    monkeypatch.setattr(torch,'load',load)
    monkeypatch.setattr(torch.optim,'AdamW',lambda *a,**k: (_ for _ in ()).throw(AssertionError('optimizer constructed')))
    restored=load_model('unused','cpu')
    assert calls==[{'map_location':'cpu','weights_only':True}]
    assert not restored.training
    assert all(torch.equal(v,restored.state_dict()[k]) for k,v in weights.items())
    key=next(iter(weights));original=weights[key]
    for bad in [original.double(),original.flatten()[:1],torch.full_like(original,float('nan'))]:
        weights[key]=bad
        with pytest.raises(ValueError,match='model state'):load_model('unused','cpu')
    weights[key]=original
    payload['session']['identity']['policy']['base_margin_mm']=0
    with pytest.raises(ValueError,match='recipe'):load_model('unused','cpu')

def test_predictions_reinsert_into_source_grid_with_background_outside_roi():
    shape=(190,110,170);image=np.zeros(shape,np.float32);mask=np.zeros(shape,np.uint8);mask[95,55,85]=1
    def probabilities(patch):
        p=np.zeros((3,*patch.shape),np.float32);p[2]=1;return p
    codes,record=predict_array(image,mask,np.eye(4),probabilities)
    lo,hi=record['native_box'];expected=np.zeros(shape,np.uint8)
    expected[tuple(slice(a,b) for a,b in zip(lo,hi))]=2
    np.testing.assert_array_equal(codes,expected)
    assert np.count_nonzero(codes)>np.count_nonzero(mask)
    assert record['tiles']==4 and record['uncovered_region_voxels']==0
