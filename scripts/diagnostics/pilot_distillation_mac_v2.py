"""Bounded, fixed-cohort Mac teacher diagnostic. Never a scientific launcher."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import ARCHIVE_SHA,sha
from src.operations.full_training_platform import training_guard,require_ac
from src.operations.segmenter_duration_dispatch_v1 import watch
from src.data.manifest_records import canonical,digest
OUT=BASE/'patient-pilot-02'
LIMITS=dict(seconds=5400,rss_bytes=12*1024**3,mps_driver_bytes=12*1024**3,
            output_bytes=2*1024**3,max_voxels=256000000,max_case_tiles=1500,max_total_tiles=10000)


def check_geometry(shape,affine,expected):
    import numpy as np
    if list(shape)!=expected['source_shape'] or not np.allclose(affine,expected['source_affine'],rtol=0,atol=1e-4):
        raise ValueError('Source world geometry mismatch')


def worker():
    if os.environ.get('PROWL_MAC_TEACHER_PILOT')!='1':raise ValueError('Supervisor required')
    import numpy as np
    import nibabel as nib
    import SimpleITK as sitk
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.training.teacher_medformer_v1 import FrozenTeacher
    from src.data.segmenter_teacher_geometry_v2 import preprocess,predict,reconstruct,grid,checked_shape
    from src.data.segmenter_native_windows_v1 import orient
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_fast_varied_v1 import normalize_region
    request=json.loads((OUT/'request.json').read_text())
    for p,pin in request['pins'].items():
        if sha(Path(p))!=pin:raise ValueError('Pilot input/code changed: '+p)
    bindings=json.loads((BASE/'pilot-local-bindings-01.json').read_text())
    if not bindings['all_pilot_sources_match']:raise ValueError('Unbound pilot')
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    teacher=FrozenTeacher(request['teacher'],digest(canonical(request['teacher'])),device='mps')
    before={k:v.detach().cpu().clone() for k,v in teacher.model.state_dict().items()}
    reports=[];total=0
    with zipfile.ZipFile(BASE/'mac-kd-metadata-20261023-a01.zip') as z:
        for row in bindings['pilot']:
            name=row['case_id'];began=time.monotonic();storage_preflight();require_ac()
            small=json.loads(z.read('native-region/members/'+name+'.json'))
            parent=small['parent_geometry']
            for role,f in row['files'].items():
                if sha(Path(f['path']))!=f['sha256']:raise ValueError('Pilot source changed')
            checked_shape(parent['source_shape'],LIMITS['max_voxels'])
            image=sitk.ReadImage(row['files']['ct']['path'])
            check_geometry(image.GetSize(),np.asarray(grid(image)['affine'])@np.eye(4)[:,[2,1,0,3]],parent)
            values,tgrid,processing=preprocess(image,max_voxels=LIMITS['max_voxels'])
            expected=request['geometry_preflight'][name]['teacher_grid']
            if tgrid['shape']!=expected['shape'] or not np.allclose(tgrid['affine'],expected['affine'],rtol=0,atol=1e-4):
                raise ValueError('Actual preprocessed geometry differs from preflight')
            def tick(progress):
                torch.mps.synchronize()
                if torch.mps.driver_allocated_memory()>LIMITS['mps_driver_bytes']:raise ValueError('MPS allocation budget')
                if progress['tile']%25==0 or progress['tile']==progress['total']:
                    with (OUT/'progress.jsonl').open('ab') as f:f.write(canonical(dict(case_id=name,**progress)))
            probability,tiling=predict(values,teacher.lesion_probability,max_voxels=LIMITS['max_voxels'],
                max_tiles=min(LIMITS['max_case_tiles'],LIMITS['max_total_tiles']-total),tick=tick)
            total+=tiling['tiles'];del values
            native,mapping=reconstruct(probability,tgrid,small['geometry'],max_voxels=LIMITS['max_voxels']);del probability
            target=None
            slices=tuple(slice(l,h) for l,h in zip(small['region_low'],small['region_high']))
            for role in ('pancreas','lesion'):
                obj=nib.load(row['files'][role]['path']);check_geometry(obj.shape,obj.affine,parent)
                proxy=obj.dataobj
                mask,_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
                region=orient(mask,parent)[slices]
                if role=='pancreas':target=region.astype(np.uint8)
                else:
                    if int(region.sum())!=small['lesion_voxels']:raise ValueError('Lesion target count differs')
                    target[region!=0]=2
                del mask,region,obj
            if target.shape!=native.shape:raise ValueError('Target shape differs')
            lesion=target==2;pred=native>.5;intersection=int((lesion&pred).sum());den=int(lesion.sum()+pred.sum())
            # Diagnostic cache only; cannot be admitted by the training target loader.
            file=OUT/(name+'-probability.npz')
            with file.open('xb') as f:np.savez_compressed(f,probability=np.rint(native*65535).astype(np.uint16))
            display=normalize_region(np.transpose(sitk.GetArrayFromImage(image),(2,1,0)).astype(np.float32),parent,small['region_low'],small['region_high'])
            del image
            support=lesion if lesion.any() else target>0
            fig,axes=plt.subplots(1,3,figsize=(12,4))
            for axis,ax in enumerate(axes):
                anchor=int(np.argmax(support.sum(axis=tuple(j for j in range(3) if j!=axis))))
                plane_axes=[j for j in range(3) if j!=axis]
                spacing=np.linalg.norm(np.asarray(small['geometry']['affine'])[:3,:3],axis=0)
                ax.imshow(np.take(display,anchor,axis=axis).T,cmap='gray',vmin=0,vmax=1,origin='lower',
                          aspect=spacing[plane_axes[1]]/spacing[plane_axes[0]])
                for mask,color in ((target>0,'cyan'),(lesion,'red'),(pred,'yellow')):
                    plane=np.take(mask,anchor,axis=axis).T
                    if plane.any() and not plane.all():ax.contour(plane,levels=[.5],colors=[color],linewidths=.7)
                ax.axis('off');ax.set_title('axis '+str(axis))
            fig.suptitle(name+' TRAIN diagnostic: pancreas cyan / lesion red / teacher yellow')
            fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=110);plt.close(fig)
            report=dict(case_id=name,seconds=time.monotonic()-began,teacher_dice=None if den==0 else 2*intersection/den,
                lesion_voxels=int(lesion.sum()),prediction_voxels=int(pred.sum()),
                recall=None if not lesion.any() else intersection/int(lesion.sum()),
                preprocessing=processing,reconstruction=mapping,tiling=tiling,cache_bytes=file.stat().st_size,
                diagnostic_only=True,quality_accepted=False)
            write(OUT/(name+'.json'),report);reports.append(report)
            del display,target,native,lesion,pred,support
            torch.mps.empty_cache()
    if not all(torch.equal(before[k],v.detach().cpu()) for k,v in teacher.model.state_dict().items()):raise ValueError('Teacher changed')
    write(OUT/'result.json',dict(success=True,cases=reports,total_tiles=total,visual_review_required=True,
                               scientific_updates=0,full_cache_authorized=False,training_ready=False))


def prepare():
    if sys.platform!='darwin':raise ValueError('Mac only')
    require_ac();storage=storage_preflight()
    archive=BASE/'mac-kd-metadata-20261023-a01.zip'
    if sha(archive)!=ARCHIVE_SHA:raise ValueError('Archive changed')
    backup=json.loads((BASE/'backup-cold-01/resources.json').read_text())
    if not backup['success'] or not backup['workers_reaped']:raise ValueError('Backup restore not qualified')
    from src.training.teacher_medformer_v1 import bundle_identity
    teacher=bundle_identity(BASE/'teacher',BASE/'convert-01/conversion.json')
    from src.data.segmenter_teacher_geometry_v2 import metadata_grid,plan,POLICY
    from scripts.diagnostics.review_mac_teacher_failure import coverage
    geometry_preflight={};total_tiles=0
    with zipfile.ZipFile(archive) as z:
        for name in json.loads(z.read('pilot-order.json')):
            small=json.loads(z.read('native-region/members/'+name+'.json'))
            grid=metadata_grid(small['parent_geometry']);check=coverage(grid,small['geometry'])
            if not check['covered']:raise ValueError('Preflight native coverage: '+name)
            tiling=plan(grid['shape'],max_voxels=LIMITS['max_voxels'],max_tiles=LIMITS['max_case_tiles'])
            total_tiles+=tiling['tiles']
            geometry_preflight[name]=dict(teacher_grid=grid,coverage=check,tiles=tiling['tiles'])
    if total_tiles>LIMITS['max_total_tiles']:raise ValueError('Total tile preflight')
    OUT.mkdir(exist_ok=False)
    paths=list((ROOT/'src').rglob('*.py'))+[Path(__file__),ROOT/'scripts/diagnostics/qualify_distillation_mac.py',
        BASE/'pilot-local-bindings-01.json',archive,ROOT/'scripts/diagnostics/review_mac_teacher_failure.py']
    pins={str(p):sha(p) for p in paths}
    write(OUT/'request.json',dict(teacher=teacher,pins=pins,limits=LIMITS,storage=storage,
        scope='Mac MPS teacher-assisted exploratory training-case pilot revision2',
        geometry_preflight=geometry_preflight,estimated_tiles=total_tiles,preprocessing_policy=POLICY,
        scientific_launch_authorized=False))
    # Preserve the producing source in this evidence directory before dispatch.
    with zipfile.ZipFile(OUT/'source.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            if p.is_relative_to(ROOT):z.write(p,str(p.relative_to(ROOT)))
    print(json.dumps(dict(prepared=True,request_sha256=sha(OUT/'request.json'),estimated_tiles=total_tiles,launched=False)))


def launch(request_sha):
    from src.operations.mac_pilot_supervision_v1 import run
    if sys.platform!='darwin':raise ValueError('Mac only')
    require_ac();storage_preflight()
    if sha(OUT/'request.json')!=request_sha:raise ValueError('Request identity mismatch')
    request=json.loads((OUT/'request.json').read_text())
    if request['limits']!=LIMITS:raise ValueError('Limits changed')
    for p,pin in request['pins'].items():
        if sha(Path(p))!=pin:raise ValueError('Prepared input changed: '+p)
    if (OUT/'process.json').exists() or (OUT/'worker.log').exists():raise ValueError('Already attempted; no retry')
    env=dict(os.environ,PROWL_MAC_TEACHER_PILOT='1',PYTHONDONTWRITEBYTECODE='1',PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='2')
    def tick():
        if sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())>LIMITS['output_bytes']:raise ValueError('Pilot output budget')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        success=run(['caffeinate','-i',sys.executable,__file__,'--worker'],OUT,seconds=LIMITS['seconds'],rss_bytes=LIMITS['rss_bytes'],tick=tick,env=env)
    if not success:raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--prepare',action='store_true');p.add_argument('--run-sha256');a=p.parse_args()
    if a.worker:worker()
    elif a.prepare:prepare()
    elif a.run_sha256:launch(a.run_sha256)
    else:p.error('--prepare or --run-sha256 required')
