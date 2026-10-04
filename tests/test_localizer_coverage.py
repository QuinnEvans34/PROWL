from copy import deepcopy
import numpy as np
import pytest
from src.training.localizer_coverage import inspect_coverage


def fixture():
    y=np.zeros((64,64,64),np.uint8);y[20:40,20:40,20:40]=1
    return y


def test_exact_and_empty():
    y=fixture();r=inspect_coverage(y,y,np.eye(4))
    assert r['dice']==r['recall']==r['precision']==r['box_coverage']==1 and r['center_offset_mm']==0
    r=inspect_coverage(np.zeros_like(y),y,np.eye(4))
    assert r['dice']==r['recall']==0 and r['box'] is None and not r['roi_diagnostic_pass']


def test_missing_extent_faces_anisotropic_flipped_axes():
    y=fixture();p=np.zeros_like(y);p[20:25,20:40,20:40]=1
    a=np.diag([-2.,3.,5.,1.]);a[:3,3]=[100,-50,90]
    r=inspect_coverage(p,y,a)
    assert r['recall']==.25 and r['box_coverage']==.5
    assert r['outside_faces']['upper']==[.5,0.,0.] and r['outside_faces']['lower']==[0.,0.,0.]
    assert r['realized_unclipped_margin_mm']==[10.,12.,10.] and r['center_offset_mm']==15.
    assert r['reference_volume_ml']==pytest.approx(240.)


def test_distant_false_component_inflates_box_without_improving_recall():
    y=fixture();p=y.copy();p[1:3,1:3,1:3]=1
    r=inspect_coverage(p,y,np.eye(4));base=inspect_coverage(y,y,np.eye(4))
    assert r['components']==2 and r['fp_only_components']==1 and r['fp_only_component_voxels']==8
    assert r['recall']==1 and r['scan_fraction']>base['scan_fraction']
    assert r['largest_component_fraction']==pytest.approx(8000/8008)


def test_no_input_mutation_and_centroid_translation_invariance():
    y=fixture();p=y.copy();a=np.eye(4);before=deepcopy((p,y,a))
    r=inspect_coverage(p,y,a);a2=a.copy();a2[:3,3]=[100,2,-9]
    assert inspect_coverage(p,y,a2)['center_offset_mm']==r['center_offset_mm']
    assert all(np.array_equal(x,b) for x,b in zip((p,y,a),before))


@pytest.mark.parametrize('fault',['nonbinary','shape','empty_reference','nan_affine','shear','zero_axis'])
def test_refusals(fault):
    y=fixture();p=y.copy();a=np.eye(4)
    if fault=='nonbinary':p[0,0,0]=2
    if fault=='shape':p=p[:3]
    if fault=='empty_reference':y.fill(0)
    if fault=='nan_affine':a[0,0]=np.nan
    if fault=='shear':a[0,1]=.2
    if fault=='zero_axis':a[0,0]=0
    with pytest.raises(ValueError):inspect_coverage(p,y,a)


def test_pinned_request_refuses_changed_scope_and_files(tmp_path,monkeypatch):
    import json
    from scripts.diagnostics import localizer_coverage_inspection as job
    from src.data.manifest_records import canonical,digest
    monkeypatch.setattr(job,'ROOT',tmp_path)
    request=tmp_path/'request';request.mkdir();plan=tmp_path/'plan.md';plan.write_bytes(b'audit')
    monkeypatch.setattr(job,'PLAN',plan);monkeypatch.setattr(job,'capture',lambda:(b'source',b'env'))
    files={'source.json':b'source','environment.json':b'env','design.md':b'audit','capability.json':b'cap','recipe.json':b'recipe'}
    for n,b in files.items():(request/n).write_bytes(b)
    r=dict(approval='D-288',runs=job.RUNS,files={n:digest(b) for n,b in files.items()},seconds=1200,rss=16*1024**3,output_bytes=256*1024**2,optimizer_updates=0)
    raw=canonical(r);(request/'request.json').write_bytes(raw)
    assert job.checked(request,digest(raw))['optimizer_updates']==0
    (request/'recipe.json').write_bytes(b'changed')
    with pytest.raises(ValueError,match='control'):job.checked(request,digest(raw))
    (request/'recipe.json').write_bytes(b'recipe');r['optimizer_updates']=1;raw=canonical(r);(request/'request.json').write_bytes(raw)
    with pytest.raises(ValueError,match='scope'):job.checked(request,digest(raw))


def test_original_receipt_tampering_refused(tmp_path,monkeypatch):
    from scripts.diagnostics import localizer_coverage_inspection as job
    monkeypatch.setattr(job,'ROOT',tmp_path)
    name=next(iter(job.RUNS.values()))[0];p=tmp_path/name;p.mkdir();(p/'receipt.json').write_bytes(b'{}')
    with pytest.raises(ValueError,match='original receipt'):job.verify_runs()


def test_native_overlay_invented_data():
    from io import BytesIO
    from PIL import Image
    from scripts.diagnostics.localizer_coverage_inspection import overlay
    y=fixture();p=y.copy();p[:30]=0
    data=overlay(y.astype(float)*200,y,p,[1,2,3],[25,30,30],'synthetic')
    with Image.open(BytesIO(data)) as img:
        assert img.size==(960,660);img.verify()


def test_source_fraction_excludes_padding_without_changing_region():
    from src.training.localizer_coverage import mapped_source_box
    pa=np.eye(4);pa[:3,3]=-16
    r=mapped_source_box([[32]*3,[64]*3],processed_shape=[96]*3,processed_affine=pa,source_shape=[64]*3,source_affine=np.eye(4))
    assert r['box']==[[16]*3,[48]*3] and r['scan_fraction']==.125
    assert r['padded_tensor_fraction']==pytest.approx(1/27)


def test_source_box_flip_anisotropy_and_clipping():
    from src.training.localizer_coverage import mapped_source_box
    sa=np.diag([-2.,1.,1.,1.]);sa[0,3]=18
    r=mapped_source_box([[0]*3,[10]*3],processed_shape=[10]*3,processed_affine=np.eye(4),source_shape=[10]*3,source_affine=sa)
    assert r['box']==[[4,0,0],[10,10,10]] and r['scan_fraction']==.6
    r=mapped_source_box(None,processed_shape=[10]*3,processed_affine=np.eye(4),source_shape=[10]*3,source_affine=sa)
    assert r['scan_fraction'] is None


@pytest.mark.parametrize('fault',['outside','fractional','shear','singular'])
def test_source_box_refuses_unsupported_geometry(fault):
    from src.training.localizer_coverage import mapped_source_box
    box=[[0]*3,[8]*3];a=np.eye(4)
    if fault=='outside':box[1][0]=11
    if fault=='fractional':box[0][0]=.5
    if fault=='shear':a[0,1]=.5
    if fault=='singular':a[0,0]=0
    with pytest.raises(ValueError):mapped_source_box(box,processed_shape=[10]*3,processed_affine=a,source_shape=[10]*3,source_affine=np.eye(4))



def test_box_wholly_in_padding_has_zero_acquired_volume():
    from src.training.localizer_coverage import mapped_source_box
    pa=np.eye(4);pa[:3,3]=-32
    r=mapped_source_box([[0]*3,[8]*3],processed_shape=[96]*3,processed_affine=pa,source_shape=[32]*3,source_affine=np.eye(4))
    assert r['scan_fraction']==0 and r['box']==[[0]*3,[0]*3]
