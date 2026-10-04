"""D-288 bounded CPU source-grid comparison of retained CAP-EXP-005/006 exports."""
import argparse
import gc
import gzip
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_smoke_run import capture,put,sha
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
PLAN=REPO/'docs/capstone/operations/CAP-EXP-006-COVERAGE-INSPECTION-PLAN-2026-09-29.md'
RUNS={
 'CAP-EXP-005':('expanded-execution-0cb02ead-2908-40f5-a56a-a4077250b4d9','13ebf8e9423d60d62ef105f65eef088331268cff9df9c656d8650216849ef2ed'),
 'CAP-EXP-006':('expanded-execution-943d4c6d-29b8-4d85-a2e5-fce579116f59','900c05364910507ba4f927733f1bf3225a900c85fabc4a99a6bcba306c0c9567')}
SELECTION=ROOT/'localizer-candidates-f1f88917-7aa0-4cd5-a4e7-e8a84897421c'
SELECTION_PIN='3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1'
FROZEN=ROOT/'expanded-launch-request-bb413397-e1a1-463d-8aba-1edf0887129c'


def verify_runs():
    results={}
    for experiment,(name,pin) in RUNS.items():
        p=ROOT/name;raw=(p/'receipt.json').read_bytes();require(sha(raw)==pin,'Changed original receipt')
        for n,r in json.loads(raw).items():
            require(Path(n).name==n and sha((p/n).read_bytes())==r['sha256'],'Changed original evidence')
        r=json.loads((p/'result.json').read_bytes());require(r['state']=='complete' and len(r['exports'])==27,'Incomplete original run')
        results[experiment]=r
    raw=(SELECTION/'receipt.json').read_bytes();require(sha(raw)==SELECTION_PIN,'Changed selection receipt')
    receipt=json.loads(raw)
    # Candidate receipts include top-level state alongside a file map.
    inventory=receipt.get('files',receipt)
    r=inventory['selection.json'];require(sha((SELECTION/'selection.json').read_bytes())==(r['sha256'] if isinstance(r,dict) else r),'Changed selection')
    return results


def prepare():
    verify_runs();source,env=capture();dest=ROOT/('coverage-inspection-request-'+str(uuid4()));dest.mkdir()
    files={'source.json':source,'environment.json':env,'design.md':PLAN.read_bytes(),'capability.json':(FROZEN/'capability.json').read_bytes(),'recipe.json':(FROZEN/'recipe.json').read_bytes()}
    for n,b in files.items():put(dest/n,b)
    put(dest/'request.json',canonical(dict(approval='D-288',runs=RUNS,files={n:sha(b) for n,b in files.items()},seconds=1200,rss=16*1024**3,output_bytes=256*1024**2,optimizer_updates=0)))
    print(dest);print('request_sha256='+sha((dest/'request.json').read_bytes()))


def checked(request,pin):
    require(request.parent==ROOT and request.resolve(strict=True)==request,'Unsafe request root')
    raw=(request/'request.json').read_bytes();require(sha(raw)==pin,'Changed request');r=json.loads(raw)
    require(r['approval']=='D-288' and r['runs']=={k:list(v) for k,v in RUNS.items()} and r['optimizer_updates']==0 and r['seconds']==1200 and r['rss']==16*1024**3 and r['output_bytes']==256*1024**2,'Wrong diagnostic scope')
    require(set(r['files'])=={'source.json','environment.json','design.md','capability.json','recipe.json'},'Wrong request files')
    for n,h in r['files'].items():require(sha((request/n).read_bytes())==h,'Changed frozen control')
    require(capture()==((request/'source.json').read_bytes(),(request/'environment.json').read_bytes()),'Diagnostic source/environment changed')
    require(PLAN.read_bytes()==(request/'design.md').read_bytes(),'Diagnostic plan changed')
    return r


def overlay(ct,reference,prediction,spacing,center,title):
    import numpy as np
    from PIL import Image,ImageDraw
    centers=[center,np.median(np.column_stack(np.nonzero(reference)),axis=0).astype(int).tolist()]
    canvas=Image.new('RGB',(960,660),'#151515');draw=ImageDraw.Draw(canvas)
    draw.text((10,8),title+' | native array axes; green=reference red=prediction yellow=overlap',fill='white')
    for row,c in enumerate(centers):
        for axis in range(3):
            grey=np.rint(np.clip((np.take(ct,c[axis],axis=axis).T+100)/400,0,1)*255).astype('uint8')
            y=np.take(reference,c[axis],axis=axis).T.astype(bool);p=np.take(prediction,c[axis],axis=axis).T.astype(bool)
            rgb=np.repeat(grey[...,None],3,axis=2);rgb[y&~p]=[0,220,0];rgb[p&~y]=[230,30,30];rgb[y&p]=[255,220,0]
            img=Image.fromarray(rgb);axes=[i for i in range(3) if i!=axis];w=grey.shape[1]*spacing[axes[0]];h=grey.shape[0]*spacing[axes[1]];scale=min(310/w,270/h)
            img=img.resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.NEAREST)
            canvas.paste(img,(axis*320+(320-img.width)//2,45+row*310));draw.text((axis*320+8,30+row*310),f'{"Missed-ref" if row==0 else "Ref"} median; axis{axis} index{c[axis]}',fill='white')
    out=BytesIO();canvas.save(out,format='PNG');return out.getvalue()


def worker(dest,request,pin):
    import numpy as np
    import nibabel as nib
    import torch
    from src.data.expanded_localizer_inputs import open_expanded_inputs
    from src.training.localizer_coverage import inspect_coverage
    from src.training.expanded_executor import validate_export
    from scripts.diagnostics.expanded_localizer_launch import stores
    from scripts.diagnostics.localizer_content_verify import peak_rss
    torch.set_num_threads(2);req=checked(request,pin);runs=verify_runs();start=time.monotonic();rows=[]
    def tick():
        require(time.monotonic()-start<1200 and peak_rss()<16*1024**3,'Worker resource cap')
        require(shutil.disk_usage(REPO).free>100*1024**3,'Internal free floor')
        require(sum(f.stat().st_size for f in dest.iterdir() if f.is_file())<256*1024**2,'Evidence cap')
    datasets,budget=open_expanded_inputs(repo=REPO,capability_bytes=(request/'capability.json').read_bytes(),trusted_capability_sha256=req['files']['capability.json'],recipe_bytes=(request/'recipe.json').read_bytes(),trusted_recipe_sha256=req['files']['recipe.json'],tick=tick)
    primary,_,_=stores();selection=json.loads((SELECTION/'selection.json').read_bytes());strata={c['study_id']:c['descriptive_stratum'] for group in selection['candidates'].values() for c in group}
    refs={experiment:{(row['role'],row['study_id']):row['reference'] for row in result['exports']} for experiment,result in runs.items()}
    for role,ds in datasets.items():
        for index in range(len(ds)):
            tick();d=ds.descriptor(index);sid=d['study_id'];code=sid.split(':')[-1]
            ct,target,affine,provenance=ds.load_native(index,operation=role)
            result=dict(study_id=sid,role=role,stratum=strata[sid],source_shape=list(target.shape),provenance=provenance,experiments={})
            for experiment in RUNS:
                ref=refs[experiment][role,sid]
                files,_=primary.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:validate_export(f,json.loads(f['record.json'])))
                record=json.loads(files['record.json']);require(record['study_id']==sid and record['role']==role and record['step']==runs[experiment]['completed_steps'],'Export member/role/step differs')
                raw=gzip.decompress(files['prediction.nii.gz']);im=nib.Nifti1Image.from_bytes(raw);pred=np.asarray(im.dataobj)
                require(pred.shape==target.shape and np.allclose(im.affine,affine,rtol=0,atol=1e-5) and im.header.get_xyzt_units()[0]=='mm','Native geometry differs')
                require(record['transform']['source_shape']==list(target.shape) and np.allclose(record['transform']['source_affine'],affine,rtol=0,atol=1e-5),'Transform/source binding differs')
                m=inspect_coverage(pred,target,affine);require(m['predicted_voxels']==record['native_foreground'],'Native foreground differs')
                result['experiments'][experiment]=dict(native=m,processed=record['metrics'],geometry_verified=True,reference=ref)
                if experiment=='CAP-EXP-006':put(dest/(code+'.png'),overlay(ct,target,pred,m['spacing_mm'],m['missing_review_center'],code+' '+role))
                del files,record,raw,im,pred;gc.collect();tick()
            put(dest/(code+'.json'),canonical(result));rows.append(result);print(json.dumps(dict(case=code,role=role,recall006=result['experiments']['CAP-EXP-006']['native']['recall'])),flush=True)
            del ct,target,affine,provenance,result;gc.collect()
    require(budget.files==54 and len(rows)==27,'Incomplete audit');checked(request,pin);verify_runs()
    put(dest/'results.json',canonical(dict(state='complete',cases=rows,source_files=budget.files,source_compressed_bytes=budget.compressed,source_expanded_bytes=budget.expanded,elapsed_seconds=time.monotonic()-start,optimizer_updates=0,model_inferences=0)))


def run(request,pin):
    checked(request,pin);dest=ROOT/('coverage-inspection-'+str(uuid4()));dest.mkdir();put(ROOT/('coverage-inspection-claim-'+pin+'.json'),canonical(dict(result=dest.name)))
    put(dest/'invocation.json',canonical(dict(request=str(request),pin=pin)));start=time.monotonic();peak=0;proc=None;reason=None;print(dest,flush=True)
    try:
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_coverage_inspection','--worker',str(dest),'--request',str(request),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                require(time.monotonic()-start<1200 and shutil.disk_usage(REPO).free>100*1024**3,'Supervisor time/free floor')
                require(sum(f.stat().st_size for f in dest.iterdir())<256*1024**2,'Supervisor evidence cap')
                p=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                if p.returncode==0 and p.stdout.strip():peak=max(peak,int(p.stdout.strip())*1024);require(peak<16*1024**3,'Supervisor RSS cap')
                elif proc.poll() is None:raise RuntimeError('Memory monitor unavailable')
                time.sleep(.25)
            require(proc.returncode==0,'Audit failed; retained evidence, no automatic retry')
    except BaseException as exc:reason=str(exc);raise
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        put(dest/'supervisor.json',canonical(dict(exit_code=None if proc is None else proc.returncode,stop_reason=reason,peak_rss=peak,elapsed_seconds=time.monotonic()-start)))
    checked(request,pin);put(dest/'receipt.json',canonical({f.name:dict(bytes=f.stat().st_size,sha256=sha(f.read_bytes())) for f in dest.iterdir()}));print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--pin');p.add_argument('--worker',type=Path);a=p.parse_args()
    if a.prepare:prepare()
    elif a.worker and a.request and a.pin:worker(a.worker,a.request,a.pin)
    elif a.request and a.pin:run(a.request,a.pin)
    else:p.error('Choose prepare or pinned run')
