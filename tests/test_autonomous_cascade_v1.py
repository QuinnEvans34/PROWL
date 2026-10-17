"""Synthetic models exercise actual CT-only inference; not trained-model quality tests."""
import builtins
import io
import json
from hashlib import sha256
from pathlib import Path
import nibabel as nib
import numpy as np
import pytest
import torch
from src.inference.autonomous_cascade_v1 import run_case


class Localizer(torch.nn.Module):
    def forward(self,x):
        return torch.cat((.4-x,x-.4),dim=1)


class Segmenter(torch.nn.Module):
    def forward(self,x):
        return torch.cat((.2-x,torch.zeros_like(x),x-.2),dim=1)


def options():
    return dict(localizer=Localizer(),segmenter=Segmenter(),localizer_sha256='b'*64,
        segmenter_sha256='c'*64,patch_size=(16,16,16),tensor_shape=(24,24,24),device='cpu',
        localizer_recipe=dict(schema_version='4.0.0',component='pancreas-localizer-preprocessing-v4',
        orientation='RAS',image_interpolation='bilinear',target_interpolation='nearest',
        padding_mode='constant_zero',crop='none',augmentation='none',cache='none',workers=0,
        spacing_mm=[2.,2.,2.],hu_window=[-100.,300.],minimum_shape=[16,16,16],
        max_source_voxels=96_000_000,max_output_voxels=16_000_000))


def ct_file(root,empty=False):
    root.mkdir();ct=np.full((32,32,32),-100,np.float32)
    if not empty:ct[10:22,10:22,10:22]=150
    a=np.eye(4);a[0,1]=.1;a[:3,3]=[4,-8,12]
    img=nib.Nifti1Image(ct,a);img.header.set_xyzt_units('mm')
    p=root/'ct.nii.gz';nib.save(img,p);return p


@pytest.mark.parametrize("policy",["all_support","largest_component_26"])
def test_masks_absent_changed_removed_never_read(tmp_path,monkeypatch,policy):
    ct=ct_file(tmp_path/'inputs');pin=sha256(ct.read_bytes()).hexdigest()
    # A hard read guard fails if inference tries to open any file in the reference directory.
    refs=tmp_path/'references';refs.mkdir();mask=refs/'pancreas.nii.gz'
    real_builtin=builtins.open;real_io=io.open;observed=[]
    def guard(original):
        def opened(file,*args,**kwargs):
            if isinstance(file,(str,bytes,Path)):
                p=Path(file).resolve();assert not p.is_relative_to(refs.resolve()),'Reference access'
                observed.append(p)
            return original(file,*args,**kwargs)
        return opened
    with monkeypatch.context() as m:
        m.setattr(builtins,'open',guard(real_builtin));m.setattr(io,'open',guard(real_io))
        first=run_case(ct,tmp_path/'absent',case_id='synthetic',expected_ct_sha256=pin,**dict(options(),region_policy=policy))
    mask.write_bytes(b'wrong reference');(ct.parent/'pancreas.nii.gz').write_bytes(b'also wrong')
    with monkeypatch.context() as m:
        m.setattr(builtins,'open',guard(real_builtin));m.setattr(io,'open',guard(real_io))
        second=run_case(ct,tmp_path/'changed',case_id='synthetic',expected_ct_sha256=pin,**dict(options(),region_policy=policy))
    assert ct.parent/'pancreas.nii.gz' not in observed
    mask.unlink();refs.rmdir();(ct.parent/'pancreas.nii.gz').unlink()
    third=run_case(ct,tmp_path/'removed',case_id='synthetic',expected_ct_sha256=pin,**dict(options(),region_policy=policy))
    assert first['prediction_array_sha256']==second['prediction_array_sha256']==third['prediction_array_sha256']
    output=nib.load(tmp_path/'absent/prediction.nii.gz');source=nib.load(ct)
    assert output.shape==source.shape and np.array_equal(output.affine,source.affine)
    assert 2 in np.unique(np.asarray(output.dataobj))
    assert first['evidence']['region_plan']['transform']['roi_origin']=='predicted_region'


def test_empty_localization_persists_failure_without_reference_fallback(tmp_path):
    ct=ct_file(tmp_path/'inputs',empty=True)
    with pytest.raises(ValueError,match='empty_localization'):
        run_case(ct,tmp_path/'result',case_id='empty',expected_ct_sha256=sha256(ct.read_bytes()).hexdigest(),**options())
    r=json.loads((tmp_path/'result/result.json').read_text())
    assert r['status']=='failed' and not (tmp_path/'result/prediction.nii.gz').exists()


def test_wrong_ct_and_reference_argument_rejected(tmp_path):
    ct=ct_file(tmp_path/'inputs')
    with pytest.raises(ValueError,match='CT bytes'):
        run_case(ct,tmp_path/'wrong',case_id='wrong',expected_ct_sha256='0'*64,**options())
    with pytest.raises(TypeError):
        run_case(ct,tmp_path/'oracle',case_id='wrong',expected_ct_sha256=sha256(ct.read_bytes()).hexdigest(),
                 reference_mask=np.ones((32,32,32)),**options())


def test_unknown_units_review_persists_without_editing_ct(tmp_path):
    ct=ct_file(tmp_path/'inputs');im=nib.load(ct)
    im.header.set_xyzt_units('unknown');nib.save(im,ct)
    pin=sha256(ct.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='source review'):
        run_case(ct,tmp_path/'no_review',case_id='synthetic',expected_ct_sha256=pin,**options())
    review=dict(ct_sha256=pin,interpreted_units='mm',basis='ct_acquisition_metadata',
                evidence='Invented test fixture generated with millimeter coordinates',reviewer='test fixture')
    r=run_case(ct,tmp_path/'reviewed',case_id='synthetic',expected_ct_sha256=pin,
               spatial_units_review=review,**options())
    assert r['spatial_units']['header_units']=='unknown' and r['spatial_units']['review']==review
    assert sha256(ct.read_bytes()).hexdigest()==pin
    assert nib.load(tmp_path/'reviewed/prediction.nii.gz').header.get_xyzt_units()[0]=='mm'


def test_larger_localizer_cap_keeps_numerics_and_enforces_ceiling():
    from src.data import localizer_preprocessing_v4 as geometry
    recipe=options()['localizer_recipe'];image=np.zeros((20,20,20),np.float32)
    before=geometry.preprocess(image,np.eye(4),recipe)['image'].as_tensor()
    larger=dict(recipe,max_output_voxels=64_000_000)
    after=geometry.preprocess(image,np.eye(4),larger)['image'].as_tensor()
    assert torch.equal(before,after)
    with pytest.raises(ValueError,match='budget'):
        geometry.plan_geometry([300]*3,np.diag([2.,2.,2.,1.]),recipe)
    assert geometry.plan_geometry([300]*3,np.diag([2.,2.,2.,1.]),larger)['conservative_output_voxels']>16_000_000
    with pytest.raises(ValueError,match='cap'):
        geometry.validate_recipe(dict(recipe,max_output_voxels=64_000_001))
