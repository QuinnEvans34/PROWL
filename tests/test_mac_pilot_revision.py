import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import numpy as np
import SimpleITK as sitk
import pytest
from src.data.segmenter_teacher_geometry_v2 import covering_size,preprocess,reconstruct


def test_covering_size_preserves_legacy_extent_and_source_centres():
    assert covering_size((441,301,177),(.7421879768371582,.7421879768371582,1.25),(1,1,1))==(328,224,221)
    assert covering_size((512,355,61),(.878906,.878906,5),(1,1,1))[2]==305
    with pytest.raises(ValueError):covering_size((1,2,3),(0,1,1),(1,1,1))


def test_corrected_synthetic_reconstruction_covers_original_grid():
    a=np.indices((17,31,41),dtype=np.float32).sum(axis=0)
    image=sitk.GetImageFromArray(a);image.SetSpacing((.7421879768,.7421879768,1.25))
    values,g,info=preprocess(image,max_voxels=100000)
    source=info['source_grid']
    q,r=reconstruct(np.full(values.shape,.75,np.float32),g,source,max_voxels=100000)
    assert q.shape==a.shape and np.all(q==.75) and r['out_of_field_voxels']==0


def wait_file(path,timeout=15):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists():return json.loads(path.read_text())
        time.sleep(.05)
    raise AssertionError('Missing '+str(path))


@pytest.mark.parametrize('mode',['normal','failure','term','kill'])
def test_supervisor_lifecycle(tmp_path,mode):
    duration='.5' if mode in ('normal','failure') else '60'
    code=f'import time,subprocess,sys;from pathlib import Path;c=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]);Path({str(tmp_path / "child.pid")!r}).write_text(str(c.pid));time.sleep({duration});raise SystemExit({7 if mode=="failure" else 0})'
    outer='from src.operations.mac_pilot_supervision_v1 import run;import sys;run([sys.executable,"-c",'+repr(code)+'], '+repr(str(tmp_path))+', seconds=5,rss_bytes=512*1024**2)'
    p=subprocess.Popen([sys.executable,'-c',outer],start_new_session=True)
    try:
        info=wait_file(tmp_path/'process.json');wait_file(tmp_path/'guardian-ready.json')
        if mode in ('term','kill'):os.kill(p.pid,signal.SIGTERM if mode=='term' else signal.SIGKILL)
        p.wait(timeout=15)
        result=wait_file(tmp_path/('guardian-failure.json' if mode=='kill' else 'resources.json'))
        assert result['success']==(mode=='normal')
        if mode=='kill':assert result['supervisor_lost']
        # An orphan may briefly be a zombie waiting for launchd; it must not execute.
        end=time.monotonic()+5
        while time.monotonic()<end:
            status=subprocess.run(['ps','-p',str(info['worker']),'-o','stat='],capture_output=True,text=True).stdout.strip()
            if not status or status.startswith('Z'):break
            time.sleep(.05)
        assert not status or status.startswith('Z')
        child=int((tmp_path/'child.pid').read_text())
        status=subprocess.run(['ps','-p',str(child),'-o','stat='],capture_output=True,text=True).stdout.strip()
        assert not status or status.startswith('Z')
    finally:
        if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()


def test_corrected_metadata_predicts_actual_oblique_geometry():
    from src.data.segmenter_teacher_geometry_v2 import metadata_grid,grid
    image=sitk.GetImageFromArray(np.indices((17,31,41),dtype=np.float32).sum(axis=0))
    image.SetSpacing((.7421879768,.7421879768,1.25));c,s=np.cos(.2),np.sin(.2)
    image.SetDirection((c,-s,0,s,c,0,0,0,1));image.SetOrigin((31,-27,17))
    original=grid(image)
    parent=dict(source_shape=list(image.GetSize()),source_affine=(np.asarray(original['affine'])@np.eye(4)[:,[2,1,0,3]]).tolist())
    _,actual,_=preprocess(image,max_voxels=100000)
    expected=metadata_grid(parent)
    assert actual['shape']==expected['shape']
    np.testing.assert_allclose(actual['affine'],expected['affine'],atol=1e-10,rtol=0)
