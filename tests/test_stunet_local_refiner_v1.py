import numpy as np
import torch
from src.training.stunet_local_refiner_v1 import Refiner,channels,crop,crop_record,objective,restore,valid_support


def test_native_affine_and_boundary_roundtrip():
    a=np.array([[.8,.3,0,11],[0,.7,0,-5],[0,0,2.5,6],[0,0,0,1]])
    source=np.arange(8*12*8).reshape(8,12,8)
    r=crop_record(source.shape,a,[1,3,7],8)
    p=np.array(r['patch_affine'])
    np.testing.assert_allclose(p@[4,4,4,1],a@[1,3,7,1])
    patch=crop(source,r,padding=-1)
    np.testing.assert_equal(patch[~valid_support(r)],-1)
    out=restore(patch,r)
    region=tuple(slice(l,h) for l,h in zip(r['source_low'],r['source_high']))
    np.testing.assert_equal(out[region],source[region])


def test_cpu_update_and_background_loss():
    torch.set_num_threads(2)
    model=Refiner()
    x=torch.zeros(1,2,16,16,16)
    valid=torch.ones(1,1,16,16,16,dtype=torch.bool)
    y=torch.zeros_like(valid,dtype=torch.float32)
    l=objective(model(x),y,valid)
    l.backward()
    assert torch.isfinite(l) and torch.count_nonzero(model.head.bias.grad)
    y[:,:,7:9,7:9,7:9]=1
    opt=torch.optim.AdamW(model.parameters(),lr=.001)
    opt.zero_grad()
    l=objective(model(x),y,valid)
    l.backward()
    opt.step()
    assert torch.isfinite(l) and model(x).shape==y.shape
    a=channels(np.zeros((16,)*3,np.float32),valid[0,0].numpy())
    assert a.shape==(2,16,16,16) and a[1,8,8,8]==1
