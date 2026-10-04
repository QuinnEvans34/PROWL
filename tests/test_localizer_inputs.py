from copy import deepcopy
import gzip
from pathlib import Path
import nibabel as nib
import numpy as np
import pytest
from src.data.binary_label_policy import APPROVED_POLICY
from src.data.cohort_registry import COHORT_ID,MEMBERS
from src.data.localizer_inputs import SourceBinding,LocalizerDataset
from scripts.diagnostics.localizer_content_verify import signature
from src.data.manifest_records import digest


def fixture(tmp_path,*,units='mm',mask_value=1,mask_shift=0):
    image=np.zeros((8,8,8),np.float32);mask=np.zeros_like(image);mask[2:4,2:4,2:4]=mask_value
    refs={};rows=[]
    for kind,arr in [('ct',image),('pancreas',mask)]:
        a=np.eye(4)
        if kind=='pancreas':a[0,3]=mask_shift
        im=nib.Nifti1Image(arr,a);im.header.set_xyzt_units(units if kind=='ct' else 'unknown')
        payload=gzip.compress(im.to_bytes());p=tmp_path/(kind+'.nii.gz');p.write_bytes(payload)
        refs[kind]=dict(root_alias='followup_source',uri=p.name,bytes=len(payload),content_sha256=digest(payload))
        observation=signature(p.stat());observation.pop('bytes')
        rows.append(dict(uri=p.name,study_id=MEMBERS[0],kind=kind,protected_role='train',bytes=len(payload),
                         expected_content_sha256=digest(payload),observation=observation))
    d=dict(study_id=MEMBERS[0],cohort_id=COHORT_ID,image=refs['ct'],target=refs['pancreas'],
        mapping=dict(policy_id=APPROVED_POLICY),geometry=dict(shape_xyz=[8]*3,spacing_mm_xyz=[1]*3,affine_ras=np.eye(4).ravel().tolist()))
    return LocalizerDataset([d],SourceBinding(tmp_path,rows,lambda:None),{}),refs,rows


def test_only_ct_and_binary_pancreas_read(tmp_path):
    dataset,refs,rows=fixture(tmp_path)
    (tmp_path/'lesion.nii.gz').write_bytes(b'not even a valid image')
    image,target,affine,decoded=dataset.load_native(0)
    assert target.sum()==8 and image.shape==(8,8,8) and decoded['policy']==APPROVED_POLICY


@pytest.mark.parametrize('fault',['held_member','wrong_cohort','unknown_units','nonbinary','misaligned','hash','symlink','wrong_kind','wrong_role'])
def test_rejects_unsupported_inputs(tmp_path,fault):
    ds,refs,rows=fixture(tmp_path,units='unknown' if fault=='unknown_units' else 'mm',
        mask_value=2 if fault=='nonbinary' else 1,mask_shift=1 if fault=='misaligned' else 0)
    if fault=='held_member':ds.descriptors[0]['study_id']='pants:study:PanTS_00000078'
    if fault=='wrong_cohort':ds.descriptors[0]['cohort_id']='cohort:arbitrary:v1'
    if fault=='hash':
        p=tmp_path/refs['ct']['uri'];p.write_bytes(b'bad')
    if fault=='symlink':
        p=tmp_path/refs['ct']['uri'];p.rename(tmp_path/'elsewhere');p.symlink_to(tmp_path/'elsewhere')
    if fault=='wrong_kind':rows[0]['kind']='pancreatic_lesion'
    if fault=='wrong_role':rows[0]['protected_role']='validation'
    with pytest.raises((ValueError,OSError)):ds.load_native(0)


def test_changed_bytes_even_when_size_stat_are_refreshed(tmp_path):
    ds,refs,rows=fixture(tmp_path);p=tmp_path/'ct.nii.gz';data=bytearray(p.read_bytes());data[-1]^=1;p.write_bytes(data)
    sig=signature(p.stat());sig.pop('bytes');rows[0]['observation']=sig
    with pytest.raises(ValueError,match='source bytes'):ds.load_native(0)


def test_dataset_tensor_path_cold_repeat_and_provenance_isolation(tmp_path):
    import torch
    from test_localizer_preprocessing import recipe
    ds,refs,rows=fixture(tmp_path);ds.recipe=recipe()
    first=ds[0];second=ds[0]
    assert first['image'].shape[0]==1 and set(torch.unique(first['label']).tolist())=={0.,1.}
    assert torch.equal(first['image'],second['image']) and torch.equal(first['label'],second['label'])
    assert first['transform_record']==second['transform_record']
    first['provenance']['image']['content_sha256']='0'*64
    assert ds.descriptors[0]['image']['content_sha256']==refs['ct']['content_sha256']


def test_factory_rejects_failed_cohort_before_any_array(monkeypatch):
    import src.data.localizer_inputs as module
    from scripts.diagnostics.localizer_preprocessing_check import REPO,CAP,CAP_PIN,RECIPE,RECIPE_PIN
    monkeypatch.setattr(module,'cohort_store',lambda *a,**k:object())
    def refused(*a,**kw):raise ValueError('held cohort')
    monkeypatch.setattr(module,'resolve_inputs',refused)
    def unexpected(*a,**kw):raise AssertionError('source arrays opened before qualification')
    monkeypatch.setattr(module.SourceBinding,'image',unexpected)
    with pytest.raises(ValueError,match='held cohort'):
        module.open_localizer_dataset(repo=REPO,capability_path=CAP,trusted_capability_sha256=CAP_PIN,
                                      recipe_path=RECIPE,trusted_recipe_sha256=RECIPE_PIN)


def test_factory_rejects_unreviewed_recipe_before_cohort(monkeypatch,tmp_path):
    import src.data.localizer_inputs as module
    from scripts.diagnostics.localizer_preprocessing_check import REPO,CAP,CAP_PIN,RECIPE,RECIPE_PIN
    other=tmp_path/'recipe.json';other.write_bytes(RECIPE.read_bytes()+b' ')
    def unexpected(*a,**kw):raise AssertionError('cohort accessed before recipe pin check')
    monkeypatch.setattr(module,'cohort_store',unexpected)
    with pytest.raises(ValueError,match='Recipe changed'):
        module.open_localizer_dataset(repo=REPO,capability_path=CAP,trusted_capability_sha256=CAP_PIN,
                                      recipe_path=other,trusted_recipe_sha256=RECIPE_PIN)
