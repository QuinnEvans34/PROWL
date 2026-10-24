"""Fixed-case EMA extent/blending diagnosis, never a training launcher."""
import itertools
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.audit_mac_teacher_inputs import extract
from src.training.teacher_medformer_v1 import FrozenTeacher,sha
from src.data.manifest_records import canonical,digest
from src.operations.full_training_platform import training_guard,require_ac
OUT=BASE/'extent-blend-probe-01';CASE='PanTS_00002720'


def upstream_scope():
    import torch
    import torch.nn.functional as F
    from types import SimpleNamespace
    source=BASE/'teacher/source/rsuper_train'
    # Empty environment prevents unrequested upstream TTA modes in synthetic tests.
    s=dict(torch=torch,F=F,_os=SimpleNamespace(environ={}))
    extract(source/'inference/utils.py',['split_idx'],s)
    extract(source/'inference/inference3d.py',
            ['make_gaussian_kernel','classification_to_3D','inference_sliding_window_one_pass'],s)
    return s


def accumulate(values,forward,scope,*,window=128,tick=lambda r:None):
    """Same model windows feed three accumulators; no padding or duplicate windows.

    Reject cases whose upstream window order differs from the candidate. This
    deliberately bounds this diagnostic instead of generalizing the executor.
    """
    import numpy as np
    import torch
    from src.data.segmenter_teacher_geometry_v1 import plan
    if values.dtype!=np.float32 or not np.isfinite(values).all():raise ValueError('Input')
    p=plan(values.shape,window=window,stride=window//2,max_voxels=256000000,max_tiles=200)
    if p['padded']!=list(values.shape):raise ValueError('Padding outside this probe')
    axes=[[scope['split_idx'](window//2,n,i)[0] for i in range(n//(window//2))] for n in values.shape]
    origins=list(itertools.product(*axes))
    if origins!=p['origins']:raise ValueError('Upstream window multiplicity/order differs')
    axis=np.exp(-.5*((np.arange(window,dtype=np.float32)-(window-1)/2)/(window*.25))**2)
    candidate=axis[:,None,None]*axis[None,:,None]*axis[None,None,:]
    upstream=scope['make_gaussian_kernel'](window,window,window)[0,0]
    weights=[candidate,upstream.numpy()]
    sums=[np.zeros(values.shape,np.float32) for _ in weights]
    counts=[np.zeros(values.shape,np.float32) for _ in weights]
    low_sum=torch.zeros(values.shape,dtype=torch.bfloat16)
    low_count=torch.zeros_like(low_sum);low_weight=upstream.to(torch.bfloat16)
    for index,origin in enumerate(origins):
        sl=tuple(slice(o,o+window) for o in origin)
        q=forward(torch.from_numpy(np.ascontiguousarray(values[sl]))[None,None]).detach().cpu()
        if q.shape!=(1,window,window,window) or q.dtype!=torch.float32 or not torch.isfinite(q).all() or q.min()<0 or q.max()>1:raise ValueError('Output')
        for acc,count,w in zip(sums,counts,weights):
            acc[sl]+=q[0].numpy()*w;count[sl]+=w
        low_sum[sl]+=q[0].to(torch.bfloat16)*low_weight
        low_count[sl]+=low_weight
        tick(dict(tile=index+1,total=len(origins)))
    result={}
    for name,acc,count in zip(['candidate_float32','upstream_kernel_float32'],sums,counts):
        if np.any(count<=0):raise ValueError('Coverage gap')
        np.divide(acc,count,out=acc);np.clip(acc,0,1,out=acc);result[name]=acc
    if (low_count<=0).any():raise ValueError('Coverage gap')
    # Exact upstream accumulation/division order, reduced to the lesion channel.
    low_sum/=(low_count+1e-6)
    result['upstream_bfloat16']=low_sum.float().numpy()
    return result,len(origins)


def synthetic_check():
    import numpy as np
    import torch
    from types import SimpleNamespace
    from src.data.segmenter_teacher_geometry_v1 import predict
    torch.set_num_threads(2);s=upstream_scope()
    # Nonconstant tile-local logits make blending differences observable.
    class Net(torch.nn.Module):
        def forward(self,x):
            ramp=torch.linspace(-2,2,x.shape[-1]).reshape(1,1,1,1,-1)
            return {'segmentation':x*.3+ramp}
    net=Net();values=np.random.default_rng(42).normal(size=(49,51,53)).astype(np.float32)
    forward=lambda x:net(x)['segmentation'][:,0].sigmoid()
    outputs,tiles=accumulate(values,forward,s,window=32)
    expected,_=predict(values,forward,max_voxels=200000,max_tiles=200,window=32,stride=16)
    assert np.array_equal(outputs['candidate_float32'],expected)
    expected,_=s['inference_sliding_window_one_pass'](net,torch.from_numpy(values)[None,None],
        SimpleNamespace(window_size=[32]*3,classes=1,epai_stage_2=False),gaussian=True)
    assert np.array_equal(outputs['upstream_bfloat16'],expected[0,0].float().numpy())
    try:accumulate(np.zeros((64,51,53),np.float32),forward,s,window=32)
    except ValueError as exc:assert 'multiplicity' in str(exc)
    else:raise AssertionError('Duplicate windows not rejected')
    return dict(candidate_exact=True,upstream_bfloat16_exact=True,duplicate_windows_rejected=True,tiles=tiles)


def worker():
    if os.environ.get('PROWL_BLEND_PROBE')!='1':raise ValueError('Supervisor required')
    import numpy as np
    import torch
    import nibabel as nib
    import SimpleITK as sitk
    from src.data.segmenter_teacher_geometry_v1 import preprocess,reconstruct,grid
    from src.data.segmenter_native_windows_v1 import orient
    from src.data.segmenter_content_v1 import target_content
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():assert sha(p)==h,p
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    teacher=FrozenTeacher(request['teacher'],digest(canonical(request['teacher'])),device='mps')
    before={k:v.detach().cpu().clone() for k,v in teacher.model.state_dict().items()}
    b=next(r for r in json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot'] if r['case_id']==CASE)
    for f in b['files'].values():assert sha(f['path'])==f['sha256']
    meta=json.loads((BASE/f'metadata-received-01/native-region/members/{CASE}.json').read_text())
    image=sitk.ReadImage(b['files']['ct']['path'])
    assert list(image.GetSize())==meta['parent_geometry']['source_shape']
    assert np.allclose(np.asarray(grid(image)['affine'])@np.eye(4)[:,[2,1,0,3]],meta['parent_geometry']['source_affine'],rtol=0,atol=1e-4)
    values,g,processing=preprocess(image,max_voxels=256000000)
    # Establish common native support BEFORE expensive model execution.
    _,coverage=reconstruct(np.zeros(values.shape,np.float32),g,meta['geometry'],max_voxels=256000000)
    def tick(r):
        torch.mps.synchronize();require_ac()
        if torch.mps.driver_allocated_memory()>12*1024**3:raise ValueError('MPS budget')
        if r['tile']%25==0 or r['tile']==r['total']:print(r,flush=True)
    probabilities,tiles=accumulate(values,teacher.lesion_probability,upstream_scope(),tick=tick)
    del values,image
    m=nib.load(b['files']['lesion']['path'])
    assert list(m.shape)==meta['parent_geometry']['source_shape'] and np.allclose(m.affine,meta['parent_geometry']['source_affine'],rtol=0,atol=1e-4)
    mask,_=target_content(m.dataobj.get_unscaled(),dict(slope=float(m.dataobj.slope),intercept=float(m.dataobj.inter)))
    sl=tuple(slice(l,h) for l,h in zip(meta['region_low'],meta['region_high']))
    target=orient(mask,meta['parent_geometry'])[sl]!=0;assert int(target.sum())==meta['lesion_voxels']
    cached=BASE/f'patient-pilot-02/{CASE}-probability.npz'
    with np.load(cached) as z:baseline=z['probability'].astype(np.float32)/65535
    def metrics(q):
        p=q>.5;inter=int((p&target).sum());n=int(target.sum());v=int(p.sum())
        return dict(dice=2*inter/(n+v),recall=inter/n,predicted_voxels=v,reference_voxels=n,
            false_positive_voxels=int((p&~target).sum()),high_confidence_false_voxels=int(((q>=.9)&~target).sum()))
    results={'saved_revised_candidate':metrics(baseline)};native_arrays={}
    for name,q in probabilities.items():
        native,mapping=reconstruct(q,g,meta['geometry'],max_voxels=256000000)
        results[name]=metrics(native);native_arrays[name]=native
    comparisons={name:dict(max_abs=float(abs(a-native_arrays['candidate_float32']).max()),
        threshold_disagreements=int(((a>.5)!=(native_arrays['candidate_float32']>.5)).sum())) for name,a in native_arrays.items()}
    for k,v in teacher.model.state_dict().items():assert torch.equal(v.cpu(),before[k])
    with (OUT/'native-probabilities.npz').open('xb') as f:np.savez_compressed(f,**native_arrays)
    write(OUT/'result.json',dict(case_id=CASE,metrics=results,blend_comparisons=comparisons,
        processing=processing,coverage=coverage,tiles=tiles,frozen_state_exact=True,scientific_updates=0,
        quality_accepted=False,limitation='One exposed case. CPU normalization/MPS forward/native world reconstruction; not complete upstream CUDA executor parity. Saved baseline is quantized.'))


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    elif '--synthetic' in sys.argv:print(json.dumps(synthetic_check()))
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();require_ac()
        checks=synthetic_check()
        original=json.loads((BASE/'patient-pilot-02/request.json').read_text());pins=dict(original['pins'])
        for p,h in pins.items():assert sha(p)==h,p
        for p in [Path(__file__).resolve(),ROOT/'scripts/diagnostics/audit_mac_teacher_inputs.py',
                  BASE/f'patient-pilot-02/{CASE}-probability.npz',BASE/'teacher/source/rsuper_train/inference/inference3d.py',
                  BASE/'teacher/source/rsuper_train/inference/utils.py']:
            pins[str(p)]=sha(p)
        assert original['teacher']['variant']=='ema'
        OUT.mkdir(exist_ok=False)
        write(OUT/'request.json',dict(case_id=CASE,teacher=original['teacher'],pins=pins,seconds=1200,
            rss_bytes=12*1024**3,output_bytes=128*1024**2,synthetic_checks=checks,scientific_updates=0,
            stopping_rule='One case and fixed three accumulators; no threshold tuning, case expansion or automatic retry.'))
        env={**os.environ,'PROWL_BLEND_PROBE':'1','PYTORCH_ENABLE_MPS_FALLBACK':'0','OMP_NUM_THREADS':'2'}
        def guard():
            if sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())>128*1024**2:raise ValueError('Output budget')
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            ok=run(['caffeinate','-i',sys.executable,__file__,'--worker'],OUT,seconds=1200,rss_bytes=12*1024**3,tick=guard,env=env)
        raise SystemExit(0 if ok else 1)
