"""One fixed exposed case, raw versus saved EMA; no training or cache promotion."""
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from src.training.teacher_medformer_v1 import bundle_identity,FrozenTeacher,sha
from src.data.manifest_records import canonical,digest
from src.operations.full_training_platform import training_guard,require_ac
OUT=BASE/'raw-weight-probe-01';CASE='PanTS_00002720'


def worker():
    if os.environ.get('PROWL_RAW_PROBE')!='1':raise ValueError('Supervisor required')
    import numpy as np
    import torch
    import nibabel as nib
    import SimpleITK as sitk
    from src.data.segmenter_teacher_geometry_v2 import preprocess,predict,reconstruct
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
    image=sitk.ReadImage(b['files']['ct']['path']);values,g,processing=preprocess(image,max_voxels=256000000)
    expected=json.loads((BASE/'patient-pilot-02/request.json').read_text())['geometry_preflight'][CASE]['teacher_grid']
    assert g['shape']==expected['shape'] and np.allclose(g['affine'],expected['affine'],rtol=0,atol=1e-4)
    def tick(r):
        torch.mps.synchronize();require_ac()
        if torch.mps.driver_allocated_memory()>12*1024**3:raise ValueError('MPS budget')
        if r['tile']%25==0 or r['tile']==r['total']:
            print(r,flush=True)
    q,tiling=predict(values,teacher.lesion_probability,max_voxels=256000000,max_tiles=200,tick=tick)
    native,mapping=reconstruct(q,g,meta['geometry'],max_voxels=256000000)
    m=nib.load(b['files']['lesion']['path']);mask,_=target_content(m.dataobj.get_unscaled(),dict(slope=float(m.dataobj.slope),intercept=float(m.dataobj.inter)))
    sl=tuple(slice(l,h) for l,h in zip(meta['region_low'],meta['region_high']))
    target=orient(mask,meta['parent_geometry'])[sl]!=0
    assert int(target.sum())==meta['lesion_voxels']
    cached=BASE/f'patient-pilot-02/{CASE}-probability.npz'
    with np.load(cached) as z:ema=z['probability'].astype(np.float32)/65535
    def metrics(q):
        pred=q>.5;inter=int((pred&target).sum());n=int(target.sum());p=int(pred.sum())
        return dict(dice=2*inter/(n+p),recall=inter/n,predicted_voxels=p,reference_voxels=n,
                    high_confidence_false_voxels=int(((q>=.9)&~target).sum()))
    for k,v in teacher.model.state_dict().items():assert torch.equal(v.cpu(),before[k])
    with (OUT/'probability.npz').open('xb') as f:np.savez_compressed(f,probability=np.rint(native*65535).astype(np.uint16))
    write(OUT/'result.json',dict(case_id=CASE,raw=metrics(native),saved_ema=metrics(ema),
        ema_probability_sha256=sha(cached),mapping=mapping,tiling=tiling,processing=processing,
        frozen_state_exact=True,scientific_updates=0,quality_accepted=False,
        limitation='One exposed case; same candidate pipeline, not full upstream equivalence. EMA comparison uses quantized cache.'))


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();require_ac()
        original=json.loads((BASE/'patient-pilot-02/request.json').read_text())
        pins=dict(original['pins'])
        for p,h in pins.items():assert sha(p)==h,p
        pins[str(Path(__file__).resolve())]=sha(__file__)
        teacher=bundle_identity(BASE/'teacher',BASE/'convert-01/conversion.json',variant='raw')
        OUT.mkdir(exist_ok=False)
        write(OUT/'request.json',dict(case_id=CASE,teacher=teacher,pins=pins,seconds=1200,
              rss_bytes=12*1024**3,model_runs=1,scientific_updates=0))
        env={**os.environ,'PROWL_RAW_PROBE':'1','PYTORCH_ENABLE_MPS_FALLBACK':'0','OMP_NUM_THREADS':'2'}
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            ok=run(['caffeinate','-i',sys.executable,__file__,'--worker'],OUT,seconds=1200,rss_bytes=12*1024**3,env=env)
        raise SystemExit(0 if ok else 1)
