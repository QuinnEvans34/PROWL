from copy import deepcopy
import gzip
import numpy as np
import nibabel as nib
import pytest
from src.data.manifest_records import digest
from src.data.bounded_nifti_audit import signature
from src.data.native_localizer_references import NativeReferences,ReadBudget
from src.data.twomm_training_references import VolumeReboundReferences,mount_observation


def setup_file(tmp_path):
    y=np.zeros((4,4,4),np.uint8);y[1:3,1:3,1:3]=1
    p=tmp_path/'a.nii.gz';raw=gzip.compress(nib.Nifti1Image(y,np.eye(4)).to_bytes());p.write_bytes(raw)
    s=signature(p.stat());size=s.pop('bytes');s['device']+=1
    row=dict(uri=p.name,kind='pancreas',study_id='synthetic-a',protected_role='train',bytes=size,
        expanded_bytes=416,observation=s)
    d=dict(study_id='synthetic-a',operation='optimizer',protected_role='train',
        target_scope='visible_reference_not_whole_organ',rows={'pancreas':row},
        target=dict(uri=p.name,bytes=size,content_sha256=digest(raw)),
        geometry=dict(shape_xyz=[4]*3,affine_ras=np.eye(4).reshape(-1).tolist(),spacing_mm_xyz=[1.]*3))
    return p,d


def test_only_device_rebound_old_reader_remains_strict(tmp_path,monkeypatch):
    p,d=setup_file(tmp_path);original=deepcopy(d)
    monkeypatch.setattr('src.data.native_localizer_references.verify_live_mapping',lambda *a:None)
    old=NativeReferences([d],tmp_path,lambda:None,ReadBudget([d]),'optimizer')
    with pytest.raises(ValueError,match='inventory identity'):old.load(0,operation='optimizer')
    budget=ReadBudget([d]);new=VolumeReboundReferences([d],tmp_path,lambda:None,budget,'optimizer')
    y,a,receipt=new.load(0,operation='optimizer')
    assert y.sum()==8 and budget.files==1 and receipt['descriptor']==original and d==original
    audit=receipt['file']['filesystem_observation']
    assert audit['retained_device']!=audit['live_device'] and audit['live_device']==p.stat().st_dev
    assert receipt['file']['content_sha256']==original['target']['content_sha256']


def test_rebound_cannot_accept_changed_content_hash(tmp_path,monkeypatch):
    p,d=setup_file(tmp_path);d['target']['content_sha256']='f'*64
    monkeypatch.setattr('src.data.native_localizer_references.verify_live_mapping',lambda *a:None)
    reader=VolumeReboundReferences([d],tmp_path,lambda:None,ReadBudget([d]),'optimizer')
    with pytest.raises(ValueError,match='qualified source'):reader.load(0,operation='optimizer')


@pytest.mark.parametrize('field',['inode','mtime_ns','ctime_ns'])
def test_rebound_retains_other_inventory_checks(tmp_path,monkeypatch,field):
    p,d=setup_file(tmp_path);d['rows']['pancreas']['observation'][field]+=1
    monkeypatch.setattr('src.data.native_localizer_references.verify_live_mapping',lambda *a:None)
    reader=VolumeReboundReferences([d],tmp_path,lambda:None,ReadBudget([d]),'optimizer')
    with pytest.raises(ValueError,match='inventory identity'):reader.load(0,operation='optimizer')


def test_rebound_refuses_mid_attempt_mount_change(tmp_path,monkeypatch):
    p,d=setup_file(tmp_path);reader=VolumeReboundReferences([d],tmp_path,lambda:None,ReadBudget([d]),'optimizer')
    reader._device+=1
    with pytest.raises(ValueError,match='mount changed'):reader._read(d['rows']['pancreas'],416)


def test_prelaunch_snapshot_requires_every_nondevice_stat_field(tmp_path,monkeypatch):
    p,d=setup_file(tmp_path);items={'optimizer':[d]}
    monkeypatch.setattr('src.data.twomm_training_references.qualified_items',lambda *a,**k:(items,tmp_path,lambda:None))
    r=mount_observation(tmp_path,{})
    assert r['source_bytes_read']==0 and len(r['rows'])==1 and r['rows'][0]['retained']['device']!=r['rows'][0]['live']['device']
    d['rows']['pancreas']['observation']['mtime_ns']+=1
    with pytest.raises(ValueError,match='Non-device'):mount_observation(tmp_path,{})
