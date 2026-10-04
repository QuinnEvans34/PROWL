from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
import gzip
import io
import json
from pathlib import Path
import nibabel as nib
import numpy as np
import pytest
from scripts.diagnostics.localizer_candidate_headers_v2 import (
    controls,validate_job,CountingReader,read_one,SELECTION)


def fixture_file(tmp_path,content=None):
    p=tmp_path/'ct.nii.gz'
    raw=nib.Nifti1Image(np.zeros((3,4,5),np.int16),np.eye(4)).to_bytes() if content is None else content
    p.write_bytes(gzip.compress(raw));s=p.stat()
    ref=dict(uri=p.name,kind='ct',bytes=s.st_size,observation=dict(device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns))
    return ref


def test_header_only_and_expanded_estimate(tmp_path):
    ref=fixture_file(tmp_path);budget=[0];r=read_one(tmp_path,ref,budget,65536)
    assert r['state']=='header_observed' and r['shape']==[3,4,5]
    assert r['expanded_array_bytes_estimate']==120
    assert r['compressed_bytes_read']==budget[0]<=65536


@pytest.mark.parametrize('fault',['size','inode','role','duplicate','path','substitute'])
def test_job_and_identity_refusals(tmp_path,fault):
    if fault in ('size','inode'):
        ref=fixture_file(tmp_path)
        if fault=='size':ref['bytes']+=1
        else:ref['observation']['inode']+=1
        with pytest.raises(ValueError):read_one(tmp_path,ref,[0],65536)
        return
    saved=retained_metadata();job=deepcopy(saved['header_job']);selection=saved['header_selection']
    if fault=='role':job['cases'][0]['protected_role']='validation'
    if fault=='duplicate':job['cases'][1]=job['cases'][0]
    if fault=='path':job['cases'][0]['inventory_inputs'][0]['uri']='../ct.nii.gz'
    if fault=='substitute':job['cases'][0]['study_id']='pants:study:PanTS_00006350'
    with pytest.raises(ValueError):validate_job(job,selection)


def test_truncated_and_unsupported_header_retained(tmp_path):
    ref=fixture_file(tmp_path,b'x'*40)
    assert read_one(tmp_path,ref,[0],65536)['state']=='header_unresolved'
    raw=nib.Nifti2Image(np.zeros((2,2,2),np.int16),np.eye(4)).to_bytes()
    ref=fixture_file(tmp_path,raw)
    assert read_one(tmp_path,ref,[0],65536)['state']=='header_unresolved'


def test_read_limits_and_failed_reads_counted(tmp_path):
    r=CountingReader(io.BytesIO(b'x'*100),[0],100)
    assert r.read(100)==b'x'*100
    with pytest.raises(RuntimeError):r.read(1)
    r=CountingReader(io.BytesIO(b'x'),[0],1000000)
    with pytest.raises(RuntimeError):r.read(65537)
    ref=fixture_file(tmp_path,b'x'*40);budget=[0]
    assert read_one(tmp_path,ref,budget,65536)['state']=='header_unresolved' and budget[0]>0


def test_parent_symlink_and_escape_refused(tmp_path):
    root=tmp_path/'root';root.mkdir();ref=fixture_file(root)
    link=tmp_path/'link';link.symlink_to(root,target_is_directory=True)
    with pytest.raises(ValueError):read_one(link,ref,[0],65536)
    ref['uri']='../root/ct.nii.gz'
    with pytest.raises(ValueError):read_one(root,ref,[0],65536)
