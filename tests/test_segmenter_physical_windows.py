import numpy as np
import pytest
from src.data.segmenter_native_windows_v1 import geometry,orient,tiles
from src.data.segmenter_physical_windows_v1 import physical_geometry,sample_window,PhysicalReconstructor,coverage_bank


@pytest.mark.parametrize('spacing',[(.7,.7,5.),(.8,5.,.8),(1.5,.6,10.),(.5,.5,.5),(1.00000006,1.,2.0000001)])
def test_field_edges_and_physical_spacing(spacing):
    a=np.diag([*spacing,1.]);native=geometry((5,7,9),a);r=physical_geometry(native)
    assert max(r['spacing_mm'])<=1.00001
    for corner in (np.array([-.5]*3),np.array(native['shape'])-.5):
        fine=(corner+.5)*r['factors']-.5
        np.testing.assert_allclose(a @ [*corner,1],np.array(r['affine']) @ [*fine,1],atol=1e-8)
    assert all(f>=1 for f in r['factors'])


@pytest.mark.parametrize('spacing',[(.7,.7,5.),(.8,5.,.8),(1.5,.6,10.),(.5,.5,.5)])
def test_real_tile_oracle_restores_every_native_label_including_corners(spacing):
    native=geometry((7,9,5),np.diag([*spacing,1.]));r=physical_geometry(native)
    target=np.random.default_rng(8).integers(0,3,size=(7,9,5),dtype=np.uint8)
    target[0,0,0]=2;target[-1,-1,-1]=2
    ts=tiles(r['shape'],window=16,stride=8);recon=PhysicalReconstructor(r,window=16)
    for origin in ts:
        patch,_=sample_window(target,r,origin,order=0,window=16)
        recon.add(origin,np.stack([patch==k for k in range(3)]).astype(np.float32))
    np.testing.assert_array_equal(recon.finish(ts).argmax(0),target)


def test_linear_ct_coordinates_and_padding():
    native=geometry((5,6,4),np.diag([.8,2.,3.,1.]));r=physical_geometry(native)
    x=np.indices((5,6,4),dtype=np.float32).sum(0)/20
    patch,t=sample_window(x,r,(0,0,0),order=1,window=16)
    assert t['normalized_shape']==[5,12,12]
    assert np.all(patch[5:]==0) and np.all(patch[:,12:]==0)
    assert 0<=patch.min()<=patch.max()<=1
    # A physical point inside the original field has the expected linear value.
    expected=(2+((5+.5)/2-.5)+((5+.5)/3-.5))/20
    assert patch[2,5,5]==pytest.approx(expected)


def test_coverage_bank_preserves_expanded_annotation_field():
    native=geometry((30,25,20),np.diag([.7,.7,10.,1.]));r=physical_geometry(native)
    mask=np.zeros((30,25,20),bool);mask[3:25,4:20,1:19]=True
    bank=coverage_bank(mask,r)
    assert len(bank)==2
    expanded=np.repeat(mask,10,axis=2);seen=np.zeros(expanded.shape,bool)
    for origin in bank:seen[tuple(slice(o,o+144) for o in origin)]=True
    assert np.all(seen[expanded])
