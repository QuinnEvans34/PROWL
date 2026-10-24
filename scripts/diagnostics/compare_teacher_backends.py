"""Two fixed exposed lesion-centered windows, CPU/MPS parity diagnostic only."""
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from src.training.teacher_medformer_v1 import bundle_identity,FrozenTeacher,sha
from src.data.manifest_records import canonical,digest
from src.operations.full_training_platform import training_guard,require_ac
OUT=BASE/'teacher-backend-parity-01'
CASES=['PanTS_00002720','PanTS_00006222']


def worker():
    if os.environ.get('PROWL_BACKEND_PARITY')!='1':raise ValueError('Supervisor required')
    import time
    import numpy as np
    import nibabel as nib
    import torch
    import SimpleITK as sitk
    from src.data.segmenter_teacher_geometry_v2 import preprocess
    from src.data.segmenter_content_v1 import target_content
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():assert sha(p)==h,p
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    teacher=FrozenTeacher(request['teacher'],digest(canonical(request['teacher'])),device='cpu')
    before={k:v.detach().cpu().clone() for k,v in teacher.model.state_dict().items()}
    bindings={r['case_id']:r for r in json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot']}
    reports=[]
    for name in CASES:
        b=bindings[name]
        for f in b['files'].values():assert sha(f['path'])==f['sha256']
        values,g,_=preprocess(sitk.ReadImage(b['files']['ct']['path']),max_voxels=256000000)
        obj=nib.load(b['files']['lesion']['path'])
        mask,_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        center=np.argwhere(mask>0).mean(axis=0)
        world=obj.affine@[*center,1]
        point=(np.linalg.inv(np.asarray(g['affine']))@world)[:3]
        origin=np.clip(np.floor(point-64).astype(int),0,np.asarray(values.shape)-128)
        assert (np.asarray(values.shape)>=128).all()
        sl=tuple(slice(int(o),int(o)+128) for o in origin)
        patch=np.ascontiguousarray(values[sl],dtype=np.float32);del values,mask
        x=torch.from_numpy(patch)[None,None]
        outputs={};timings={}
        for device in ['cpu','mps']:
            require_ac();teacher.model.to(device);teacher.device=device
            began=time.monotonic();outputs[device]=teacher.lesion_probability(x).numpy()[0].copy()
            if device=='mps':
                torch.mps.synchronize()
                assert torch.mps.driver_allocated_memory()<=12*1024**3
            timings[device]=time.monotonic()-began
            print(name,device,'forward complete',timings[device],flush=True)
        a,b=outputs['cpu'],outputs['mps'];diff=np.abs(a-b)
        report=dict(case_id=name,origin=origin.tolist(),window_shape=list(patch.shape),
            input_sha256=__import__('hashlib').sha256(patch.tobytes()).hexdigest(),seconds=timings,
            maximum_probability_difference=float(diff.max()),mean_probability_difference=float(diff.mean()),
            voxels_difference_over_001=int((diff>.01).sum()),
            threshold_disagreements=int(((a>.5)!=(b>.5)).sum()),window_voxels=int(a.size),
            cpu_positive_voxels=int((a>.5).sum()),mps_positive_voxels=int((b>.5).sum()))
        with (OUT/(name+'.npz')).open('xb') as f:np.savez_compressed(f,cpu=a,mps=b)
        reports.append(report);print(report,flush=True)
        teacher.model.cpu();teacher.device='cpu';torch.mps.empty_cache()
    assert all(torch.equal(before[k],v.detach().cpu()) for k,v in teacher.model.state_dict().items())
    for p,h in request['pins'].items():assert sha(p)==h,p
    write(OUT/'result.json',dict(success=True,cases=reports,frozen_state_exact=True,
        scope='two_annotation_centered_windows_not_full_volume_accuracy_or_CUDA_parity',
        teacher_qualified=False,scientific_updates=0))


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();require_ac()
        pins=dict(json.loads((BASE/'patient-pilot-02/request.json').read_text())['pins'])
        for p,h in pins.items():assert sha(p)==h,p
        pins[str(Path(__file__).resolve())]=sha(__file__)
        teacher=bundle_identity(BASE/'teacher',BASE/'convert-01/conversion.json')
        OUT.mkdir(exist_ok=False)
        write(OUT/'request.json',dict(cases=CASES,pins=pins,teacher=teacher,seconds=1200,
            rss_bytes=12*1024**3,forwards=4,selection='clamped annotation-centroid window',
            reason='isolate backend with identical weights and inputs; no threshold or quality tuning'))
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            ok=run(['caffeinate','-i',sys.executable,__file__,'--worker'],OUT,seconds=1200,rss_bytes=12*1024**3,
                env={**os.environ,'PROWL_BACKEND_PARITY':'1','PYTORCH_ENABLE_MPS_FALLBACK':'0','OMP_NUM_THREADS':'2'})
        raise SystemExit(0 if ok else 1)
