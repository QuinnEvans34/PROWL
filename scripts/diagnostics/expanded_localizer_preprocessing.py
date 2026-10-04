"""D-283 single-use, supervised preprocessing diagnostic for exact frozen inputs."""
import argparse
import gc
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from uuid import uuid4

from scripts.diagnostics.localizer_smoke_run import capture,encoded,put,sha
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
CAP=REPO/'docs/capstone/data/EXPANDED-LOCALIZER-INPUT-CAPABILITY-2026-09-29.json'
RECIPE=REPO/'configs/capstone/localizer-preprocessing-v2.json'
PLAN=REPO/'docs/capstone/data/EXPANDED-LOCALIZER-PREPROCESSING-JOB-2026-09-29.md'
STAGING=ROOT/'expansion-candidate-1e1e331d-c385-410b-97ee-a6e1478a1e70'
PLAN_PIN='3844a5c9fcaa5912dd247d7e28c07d822e62b215d276b045e7e91986b607658d'
LIMITS=dict(seconds=1200,rss=16*1024**3,output_bytes=256*1024**2,internal_free=100*1024**3)


def prepare():
    from src.data.localizer_preprocessing_v2 import plan_geometry
    planraw=(STAGING/'plan.json').read_bytes();require(sha(planraw)==PLAN_PIN,'Changed cohort preparation')
    plan=json.loads(planraw);raw=(STAGING/'derived.json').read_bytes();require(sha(raw)==plan['files']['derived.json'],'Changed derived bytes')
    d=json.loads(raw);recipe=json.loads(RECIPE.read_bytes());projections=[]
    annotations={a['annotation_id']:a for a in d['manifest']['annotations']};studies={s['study_id']:s for s in d['manifest']['studies']}
    for c in d['cohorts']:
        for m in c['members']:
            s=studies[m['study_id']];g=s['geometry'];import numpy as np
            projections.append(dict(study_id=m['study_id'],role=c['protected_role'],**plan_geometry(g['shape_xyz'],np.asarray(g['affine_ras']).reshape(4,4),recipe),
                compressed_bytes=s['image']['bytes']+annotations[m['annotation']['id']]['file']['bytes']))
    require(len(projections)==27 and sum(r['compressed_bytes'] for r in projections)<=1024**3,'Projected scope exceeds cap')
    source,environment=capture();out=ROOT/('expanded-preprocessing-request-'+str(uuid4()));out.mkdir()
    members={'capability.json':CAP.read_bytes(),'recipe.json':RECIPE.read_bytes(),'plan.md':PLAN.read_bytes(),
             'source.json':source,'environment.json':environment,'projections.json':encoded(projections)}
    for n,b in members.items():put(out/n,b)
    request=dict(approval='D-283',operation='read_only_preprocessing',limits=LIMITS,files={n:sha(b) for n,b in members.items()},optimizer_updates=0)
    put(out/'request.json',encoded(request));print(json.dumps(dict(request=str(out),request_sha256=sha((out/'request.json').read_bytes()),cases=27,source_files=54,
        compressed_bytes=sum(r['compressed_bytes'] for r in projections),maximum_projected_voxels=max(r['conservative_output_voxels'] for r in projections)),indent=2))


def checked_request(path,pin):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe request root')
    raw=(path/'request.json').read_bytes();require(sha(raw)==pin,'Independent request pin differs');req=json.loads(raw)
    require(req['approval']=='D-283' and req['limits']==LIMITS and req['optimizer_updates']==0,'Wrong request scope')
    require(set(req['files'])=={'capability.json','recipe.json','plan.md','source.json','environment.json','projections.json'},'Request inventory changed')
    for n,h in req['files'].items():require(sha((path/n).read_bytes())==h,'Changed request member')
    source,environment=capture();require(source==(path/'source.json').read_bytes() and environment==(path/'environment.json').read_bytes(),'Code/environment changed')
    return req


def sheet(image,target,restored,affine,processed,label,record,code):
    import numpy as np
    import nibabel as nib
    from PIL import Image
    from scripts.diagnostics.localizer_alignment_review import render
    orient=nib.orientations.ornt_transform(nib.orientations.io_orientation(affine),nib.orientations.axcodes2ornt(('R','A','S')))
    ca=affine@nib.orientations.inv_ornt_aff(orient,image.shape)
    native=[nib.orientations.apply_orientation(v,orient) for v in (image,target,restored)]
    coords=np.nonzero(native[1]);mid=[int(np.median(v)) for v in coords];views=[(2,mid[2],True),(1,mid[1],True),(0,mid[0],True)]
    top=render(native[0],native[1],nib.affines.voxel_sizes(ca),views,code+' SOURCE reference')
    middle=render(native[0],native[2],nib.affines.voxel_sizes(ca),views,code+' RESTORED reference (same source planes)')
    coords=np.nonzero(label);mid=[int(np.median(v)) for v in coords];views=[(2,mid[2],True),(1,mid[1],True),(0,mid[0],True)]
    bottom=render(processed*400-100,label,nib.affines.voxel_sizes(np.asarray(record['processed_affine'])),views,code+' PROCESSED reference (own median planes)')
    result=Image.new('RGB',(top.width,top.height+middle.height+bottom.height));result.paste(top,(0,0));result.paste(middle,(0,top.height));result.paste(bottom,(0,top.height+middle.height))
    b=io.BytesIO();result.save(b,format='PNG');return b.getvalue()


def worker(dest,request,pin):
    import numpy as np
    import torch
    from src.data.expanded_localizer_inputs import open_expanded_inputs
    from src.data.localizer_preprocessing_v2 import preprocess,restore_to_source
    from scripts.diagnostics.localizer_content_verify import peak_rss
    req=checked_request(request,pin);torch.set_num_threads(2);start=time.monotonic();reports=[]
    def tick():
        require(time.monotonic()-start<LIMITS['seconds'] and peak_rss()<=LIMITS['rss'],'Time/memory budget')
        require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Internal free floor')
        require(sum(p.stat().st_size for p in dest.iterdir())<=LIMITS['output_bytes'],'Evidence cap')
    datasets,budget=open_expanded_inputs(repo=REPO,capability_bytes=(request/'capability.json').read_bytes(),trusted_capability_sha256=req['files']['capability.json'],
        recipe_bytes=(request/'recipe.json').read_bytes(),trusted_recipe_sha256=req['files']['recipe.json'],tick=tick)
    metadata_seconds=time.monotonic()-start;print(json.dumps(dict(state='bundle_verified',metadata_seconds=metadata_seconds)),flush=True)
    for operation,dataset in datasets.items():
        for index in range(len(dataset)):
            tick();beg=time.monotonic();desc=dataset.descriptor(index);code=desc['study_id'].split(':')[-1]
            image,target,a,provenance=dataset.load_native(index,operation=operation);load_seconds=time.monotonic()-beg
            transform_start=time.monotonic()
            try:
                x=preprocess(image,a,dataset.recipe,target=target);transform_seconds=time.monotonic()-transform_start
                infer=preprocess(image,a,dataset.recipe);require(torch.equal(x['image'],infer['image']),'Target influences image transform');del infer
                require(x['image'].shape[0]==1 and x['image'].min()>=0 and x['image'].max()<=1,'Image channel/range')
                back=restore_to_source(x['label'],x['transform_record'],discrete=True)[0].as_tensor().numpy().astype(np.uint8)
                require(np.isin(back,[0,1]).all() and back.any(),'Restoration lost binary target')
                label=x['label'][0].as_tensor().numpy().astype(np.uint8);processed=x['image'][0].as_tensor().numpy()
                dice=float(2*np.logical_and(target,back).sum()/(int(target.sum())+int(back.sum())))
                report=dict(study_id=desc['study_id'],operation=operation,state='numerical_pass',source_shape=list(image.shape),processed_shape=list(label.shape),
                    source_foreground=int(target.sum()),processed_foreground=int(label.sum()),restored_foreground=int(back.sum()),roundtrip_dice=dice,
                    image_target_independent=True,load_seconds=load_seconds,transform_seconds=transform_seconds,elapsed_seconds=time.monotonic()-beg,
                    provenance=provenance,transform_record=x['transform_record'])
                put(dest/(code+'.png'),sheet(image,target,back,a,processed,label,x['transform_record'],code));del x,back,label,processed
            except ValueError as exc:
                report=dict(study_id=desc['study_id'],operation=operation,state='preprocessing_failed',error=str(exc),source_read_verified=True,provenance=provenance)
            put(dest/(code+'.json'),encoded(report));reports.append(report);print(json.dumps({k:report[k] for k in ('study_id','operation','state')}),flush=True)
            del image,target,a,provenance;gc.collect();tick()
    require(budget.files==54 and len(reports)==27,'Incomplete frozen cohort coverage')
    checked_request(request,pin)
    put(dest/'results.json',encoded(dict(state='numerical_pass_visual_review_pending' if all(r['state']=='numerical_pass' for r in reports) else 'preprocessing_failures_retained',
        counts={op:sum(r['operation']==op for r in reports) for op in datasets},failures=[r['study_id'] for r in reports if r['state']!='numerical_pass'],
        source_files=budget.files,source_bytes=budget.compressed,expanded_bytes=budget.expanded,metadata_seconds=metadata_seconds,
        elapsed_seconds=time.monotonic()-start,peak_rss=peak_rss(),optimizer_updates=0)))


def run(request,pin):
    req=checked_request(request,pin);require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Internal free floor')
    dest=ROOT/('expanded-preprocessing-'+str(uuid4()));dest.mkdir()
    put(ROOT/('expanded-preprocessing-claim-'+pin+'.json'),encoded(dict(result=dest.name,request_sha256=pin)))
    for n in ('request.json',*req['files']):put(dest/n,(request/n).read_bytes())
    start=time.monotonic();peak=0;reason=None;proc=None;print(dest,flush=True)
    try:
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.expanded_localizer_preprocessing','--worker',str(dest),'--request',str(request),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                require(time.monotonic()-start<=LIMITS['seconds'],'Supervisor time cap')
                require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Supervisor free floor')
                require(sum(p.stat().st_size for p in dest.iterdir())<=LIMITS['output_bytes'],'Supervisor output cap')
                p=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                if p.returncode==0 and p.stdout.strip():peak=max(peak,int(p.stdout.strip())*1024);require(peak<=LIMITS['rss'],'Supervisor RSS cap')
                elif proc.poll() is None:raise RuntimeError('Memory monitor unavailable')
                time.sleep(.25)
            require(proc.returncode==0,'Worker failed; inspect retained log')
        checked_request(request,pin)
    except BaseException as exc:reason=str(exc);raise
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        put(dest/'supervisor.json',encoded(dict(exit_code=None if proc is None else proc.returncode,stop_reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))
    put(dest/'receipt.json',encoded(dict(state='complete',files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir()},optimizer_updates=0)))
    print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--pin');p.add_argument('--worker',type=Path);a=p.parse_args()
    if a.prepare:prepare()
    elif a.worker and a.request and a.pin:worker(a.worker,a.request,a.pin)
    elif a.request and a.pin:run(a.request,a.pin)
    else:p.error('Choose prepare or exact request')
