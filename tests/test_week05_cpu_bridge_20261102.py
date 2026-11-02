import os
import sys
import subprocess
from pathlib import Path
import numpy as np
import pytest
from src.inference.ct_access_policy_windows_v1 import CtAccessPolicy
from src.inference.predicted_physical_region_v1 import prepare
from src.training.verifier_candidate_export_v1 import native_embed


def test_native_geometry_roundtrip_and_all_faces():
    x=np.arange(6*7*8,dtype=np.float32).reshape(6,7,8)
    m=np.zeros_like(x,dtype=np.uint8);m[0,0,0]=m[-1,-1,-1]=1
    a=np.array([[0,-2,0,17],[-1,0,0,23],[0,0,3,-11],[0,0,0,1]],float)
    r=prepare(x,m,a,base_margin_mm=0,extra_margin_mm=[0,0,0],max_region_voxels=1000)
    assert np.array_equal(native_embed(np.ones(r['image'].shape,np.uint8),r),np.ones(m.shape))
    assert np.allclose(native_embed(r['image'],r),(np.clip(x,-100,250)+100)/350)
    assert r['reference_inputs_used'] is False


def test_physical_margin_and_non_resizing():
    x=np.zeros((20,20,20),np.float32);m=np.zeros_like(x);m[10,10,10]=1
    r=prepare(x,m,np.diag([2,1,3,1]),base_margin_mm=3,extra_margin_mm=[0,0,0],max_region_voxels=1000)
    assert r['image'].shape==(5,7,3)
    assert r['region_low']==[8,7,9]


@pytest.mark.parametrize('kind',['empty','fractional','nonfinite','budget'])
def test_invalid_inputs_never_fallback(kind):
    x=np.zeros((4,4,4));m=np.ones_like(x);limit=1000
    if kind=='empty':m[:]=0
    if kind=='fractional':m[0,0,0]=.5
    if kind=='nonfinite':x[0,0,0]=np.nan
    if kind=='budget':limit=1
    with pytest.raises(ValueError):prepare(x,m,np.eye(4),base_margin_mm=0,extra_margin_mm=[0,0,0],max_region_voxels=limit)


def test_reference_absence_and_changes_do_not_enter_bridge(tmp_path):
    x=np.zeros((4,4,4));m=np.ones_like(x)
    before=prepare(x,m,np.eye(4),base_margin_mm=0,extra_margin_mm=[0,0,0],max_region_voxels=1000)
    (tmp_path/'lesion.nii').write_bytes(b'not an input')
    after=prepare(x,m,np.eye(4),base_margin_mm=0,extra_margin_mm=[0,0,0],max_region_voxels=1000)
    assert np.array_equal(before['image'],after['image'])


def test_access_policy_paths_modes_and_windows_null(tmp_path):
    ct=tmp_path/'ct.nii';out=tmp_path/'out';code=tmp_path/'runtime';code.mkdir()
    guard=CtAccessPolicy(ct,out,[code])
    guard('open',(os.fsencode(ct),'rb',0));guard('open',(os.devnull,'wb',os.O_WRONLY))
    guard('open',(str(out/'result.json'),'w',os.O_WRONLY));guard('open',(str(code/'stdlib.py'),'r',0))
    for path,mode,flags in [(ct,'w',os.O_WRONLY),(code/'x','w',os.O_WRONLY),(tmp_path/'lesion.nii','r',0)]:
        with pytest.raises(PermissionError):guard('open',(str(path),mode,flags))
    assert guard.ct_reads==1


def test_actual_subprocess_audit_tripwire(tmp_path):
    ct=tmp_path/'ct.bin';ct.write_bytes(b'CT');ref=tmp_path/'lesion.bin';ref.write_bytes(b'LABEL')
    out=tmp_path/'out';out.mkdir()
    code=f'''import sys,os
from pathlib import Path
from src.inference.ct_access_policy_windows_v1 import CtAccessPolicy
g=CtAccessPolicy({str(ct)!r},{str(out)!r},[])
sys.addaudithook(g)
assert Path({str(ct)!r}).read_bytes()==b'CT'
with open(os.devnull,'wb') as f:f.write(b'x')
try:Path({str(ref)!r}).read_bytes()
except PermissionError:pass
else:raise AssertionError('Reference readable')
Path({str(out/'ok')!r}).write_text('passed')
'''
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert (out/'ok').read_text()=='passed'


def test_bridge_matches_existing_control_source_axis_margin_semantics():
    from src.data.segmenter_pancreas_region_v1 import oriented_box,POLICY
    from src.data.segmenter_native_windows_v1 import geometry
    x=np.zeros((60,70,80),np.float32);m=np.zeros_like(x);m[30:32,35:38,40:42]=1
    a=np.array([[0,-4,0,17],[-3,0,0,23],[0,0,5,-11],[0,0,0,1]],float)
    r=prepare(x,m,a,base_margin_mm=POLICY['base_margin_mm'],extra_margin_mm=POLICY['extra_margin_mm'],max_region_voxels=x.size)
    lo,hi=oriented_box(m,geometry(x.shape,a))
    assert r['region_low']==lo.tolist() and r['region_high']==hi.tolist()
