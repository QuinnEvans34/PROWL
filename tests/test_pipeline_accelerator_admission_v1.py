"""Exercise existing POSIX guard and target admission, using only invented CPU data."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from src.data.manifest_records import canonical,digest
from src.data.segmenter_native_windows_v1 import geometry
from src.data.segmenter_generated_target_admission_v1 import admit
from src.data.segmenter_teacher_cache_v1 import sha,TeacherTargetStore

REPO=Path(__file__).resolve().parents[1]
HELPER=REPO/'tests/helpers/accelerator_lock_fixture.py'


def spawn(lock, mode):
    return subprocess.Popen([sys.executable,str(HELPER),str(lock),mode],cwd=REPO,
        env=dict(os.environ,PYTHONPATH=str(REPO)),stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)


def call(lock,mode):
    child=spawn(lock,mode)
    try:
        out,err=child.communicate(timeout=5)
        return child.returncode,out.strip(),err
    finally:
        if child.poll() is None:child.kill();child.wait(5)


@pytest.mark.skipif(os.name!='posix',reason='Mac POSIX qualification only')
@pytest.mark.parametrize('stop',['release','terminate','kill'])
def test_exclusive_owner_and_recovery_preserve_lock_inode(tmp_path,stop):
    lock=tmp_path/'isolated.lock';owner=spawn(lock,'hold')
    try:
        assert select.select([owner.stdout],[],[],5)[0], 'Owner did not become ready'
        assert owner.stdout.readline().strip()=='admitted'
        inode=lock.stat().st_ino
        for _ in range(2):
            code,out,err=call(lock,'probe');assert (code,out)==(3,'busy'),err
        if stop=='kill':owner.kill()
        elif stop=='terminate':owner.terminate()
        else:owner.stdin.write('\n');owner.stdin.flush()
        owner.communicate(timeout=5)
        assert owner.returncode=={'kill':-9,'terminate':-15,'release':0}[stop]
        code,out,err=call(lock,'probe');assert (code,out)==(0,'admitted'),err
        assert lock.stat().st_ino==inode
    finally:
        if owner.poll() is None:owner.kill();owner.wait(5)
        for stream in (owner.stdin,owner.stdout,owner.stderr):stream.close()


def test_ac_failure_never_enters_body_and_releases_lock(tmp_path):
    lock=tmp_path/'isolated.lock'
    assert call(lock,'no-ac')[:2]==(4,'synthetic AC unavailable')
    assert call(lock,'probe')[:2]==(0,'admitted')


def test_stale_text_is_not_lock_ownership(tmp_path):
    lock=tmp_path/'isolated.lock';lock.write_text('stale owner metadata')
    assert call(lock,'probe')[:2]==(0,'admitted')
    assert lock.read_text()=='stale owner metadata'


def fixture(tmp_path):
    control={'train':['A','B'],'validation':['V']}
    native=geometry((4,4,4),np.eye(4))
    small={'geometry':native,'parent_geometry':native,'region_low':[0]*3,
           'region_high':[4]*3,'source_sha256':{'ct':'a'*64}}
    provider=SimpleNamespace(control=control,pin=digest(canonical(control)),cache_member=lambda name:(None,small))
    rows={}
    for name in control['train']:
        path=tmp_path/(name+'.npz');np.savez_compressed(path,probability=np.zeros((4,4,4),np.uint16))
        rows[name]=dict(case_id=name,native_geometry=small['geometry'],source_ct_sha256='a'*64,
            payload_sha256=sha(path),bytes=path.stat().st_size,reconstruction=dict(
                method='RAS_world_linear_slabbed',native_voxels=64,covered_voxels=64,out_of_field_voxels=0))
    request=dict(train=list(control['train']),teacher=dict(weights={'sha256':'a'*64},config={},labels={}),preprocessing_policy={})
    result=dict(success=True,complete=True,members=rows)
    resources=dict(success=True,workers_reaped=True,exit_code=0)
    return provider,request,result,resources


@pytest.mark.parametrize('fault',['partial','protected','live','exit','provider','order','dtype','shape','inventory','grid','coverage','hash'])
def test_invalid_target_boundary_never_returns_training_manifest(tmp_path,fault):
    p,req,result,resources=fixture(tmp_path)
    if fault=='partial':del result['members']['B']
    if fault=='protected':req['train'].append('V')
    if fault=='live':resources['workers_reaped']=False
    if fault=='exit':resources['exit_code']=1
    if fault=='provider':p.pin='b'*64
    if fault=='order':req['train'].reverse()
    if fault in ('dtype','shape','inventory'):
        values=np.zeros((4,4,4),np.float32) if fault=='dtype' else np.zeros((3,4,4) if fault=='shape' else (4,4,4),np.uint16)
        path=tmp_path/'A.npz';np.savez_compressed(path,**{('extra' if fault=='inventory' else 'probability'):values})
        result['members']['A'].update(payload_sha256=sha(path),bytes=path.stat().st_size)
    if fault=='grid':result['members']['A']['native_geometry']={}
    if fault=='coverage':result['members']['A']['reconstruction']['covered_voxels']=63
    if fault=='hash':result['members']['A']['payload_sha256']='0'*64
    with pytest.raises(ValueError):admit(tmp_path,req,result,resources,p)
    assert not (tmp_path/'manifest.json').exists()


def test_valid_targets_enter_store_partial_qualification_does_not(tmp_path):
    p,req,result,resources=fixture(tmp_path)
    manifest,identity=admit(tmp_path,req,result,resources,p)
    path=tmp_path/'manifest.json';path.write_bytes(canonical(manifest))
    TeacherTargetStore(tmp_path,sha(path),control=p.control,common_identity=identity)
    partial,identity=admit(tmp_path,req,result,{},p,qualification_only=True)
    qualification=tmp_path/'qualification';qualification.mkdir()
    path=qualification/'manifest.json';path.write_bytes(canonical(partial))
    with pytest.raises(ValueError,match='Incomplete'):
        TeacherTargetStore(qualification,sha(path),control=p.control,common_identity=identity)
