"""Array-only96M-voxel resource rehearsal; no source reads or model use."""
import gc
import gzip
import json
import resource
import signal
import time
from uuid import uuid4
import nibabel as nib
import numpy as np
from scripts.diagnostics.localizer_smoke_run import capture,sha,put,encoded
from scripts.diagnostics.localizer_candidate_content_v3 import REPO
from src.data.bounded_nifti_audit import decode_file
from src.data.binary_label_policy import decode_binary,APPROVED_POLICY


def run():
    start=time.monotonic();source,env=capture()
    def guard(*_):
        if time.monotonic()-start>=1200 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>=16*1024**3:raise RuntimeError('Rehearsal resource cap')
    def deadline(*_):raise TimeoutError('Rehearsal time cap')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(1200)
    shape=(480,400,500);affine=np.diag([1.,1.,1.,1.]);images=[]
    for dtype in (np.int16,np.int8):
        a=np.zeros(shape,dtype=dtype);a[100:220,100:250,100:220]=1
        payload=gzip.compress(nib.Nifti1Image(a,affine).to_bytes(),compresslevel=1,mtime=0);del a;gc.collect()
        im,used=decode_file(payload,expanded_cap=512*1024**2,voxel_cap=96_000_000,tick=guard)
        images.append(im);del payload;guard()
    ct=images[0].get_fdata(dtype=np.float32);semantic=images[1].get_fdata(dtype=np.float64)
    unique,count=np.unique(semantic,return_counts=True);mask,receipt=decode_binary(semantic,policy=APPROVED_POLICY)
    coords=np.nonzero(mask);mid=[int(np.median(v)) for v in coords]
    assert ct.shape==shape and np.isfinite(ct).all() and set(unique)=={0.,1.} and mask.sum()==2160000
    guard();assert capture()==(source,env)
    result=dict(state='passed',voxels=96_000_000,source_reads=0,peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,elapsed_seconds=time.monotonic()-start,source_sha256=sha(source),environment_sha256=sha(env),shape=shape,foreground_voxels=int(mask.sum()),median=mid,limitations='Allocation/decode rehearsal; synthetic content is not worst-case real gzip or anatomy.')
    dest=REPO/'outputs/prowl'/('large-content-rehearsal-'+str(uuid4())+'.json');put(dest,encoded(result));signal.alarm(0)
    print(dest);print('sha256='+sha(dest.read_bytes()));print(json.dumps(result))

if __name__=='__main__':run()
