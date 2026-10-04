"""D-304 original-reference scoring, one single-use label-only pass in8+145 cases."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_smoke_run import capture,put
from scripts.diagnostics.localizer_context_profile import power
from scripts.diagnostics.twomm_inference_pilot import BINDING,BINDING_PIN,REPO,ROOT
from scripts.diagnostics.twomm_inference_continuation import PILOT,PILOT_PIN
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require

CAP=REPO/'docs/capstone/data/NATIVE-REFERENCE-CAPABILITY-2026-09-30.json'
CAP_PIN='90967ebe492234a0dabcfaaf6c1daf8c3d54ab25fc15c559d787b4b18e0c8e70'
RECIPE=REPO/'configs/capstone/localizer-preprocessing-v4.json'
FULL=ROOT/'twomm-session-continuation-1e8f209b-a692-4d26-9ff7-3470ead10427'
FULL_PIN='e72ebedd2b318b629282f389adfb03b0bae9bc4b4af6212bafcb5e0cd00fcd64'
WEIGHTS='365306b1aec77681bd651a1e87ca7902b10efffef38607f1618303220d20954e'
LIMITS=dict(seconds=1200,rss_bytes=16*1024**3,output_bytes=128*1024**2,free_bytes=100*1024**3)
NAMES={'source.json','environment.json','binding.json','capability.json','recipe.json'}


def checked_package(path,pin):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe package')
    raw=(path/'receipt.json').read_bytes();require(digest(raw)==pin,'Completion changed');r=json.loads(raw)
    require(r['state']=='complete','Incomplete package')
    for n,v in r['files'].items():
        require(Path(n).name==n,'Unsafe package member');p=path/n
        require(p.is_file() and not p.is_symlink(),'Missing package member')
        b=p.read_bytes();require(len(b)==v['bytes'] and digest(b)==v['sha256'],'Package member changed')
    return r


def prediction_index():
    out={}
    for path,pin in ((PILOT,PILOT_PIN),(FULL,FULL_PIN)):
        checked_package(path,pin);p=json.loads((path/'profile.json').read_bytes())
        require(p['weights_sha256']==WEIGHTS and p['completed_step']==p['real_updates']==0,'Wrong initialized predictions')
        for row in p['cases']:
            sid=row['study_id'];require(sid not in out,'Duplicate prediction')
            out[sid]=(path,row,pin)
    require(len(out)==153,'Incomplete predictions');return out


def expected_ids(cap,batch):
    require(batch in ('pilot','remainder'),'Unknown score batch')
    ids=next(b['study_ids'] for b in cap['batches'] if b['batch_id']==batch)
    require(len(ids)==(8 if batch=='pilot' else 145) and len(set(ids))==len(ids),'Wrong batch membership')
    return ids


def checked_request(path,pin,*,current=True):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe request')
    raw=(path/'request.json').read_bytes();require(digest(raw)==pin,'Request changed');r=json.loads(raw)
    require(set(r)=={'schema_version','approval','batch','limits','files','prior'} and r['schema_version']=='native-score-1' and
            r['approval']=='D-304' and r['limits']==LIMITS and set(r['files'])==NAMES,'Wrong scoring scope')
    for n,h in r['files'].items():require(digest((path/n).read_bytes())==h,'Control changed')
    require(r['files']['binding.json']==BINDING_PIN and r['files']['capability.json']==CAP_PIN,'Wrong source controls')
    cap=json.loads((path/'capability.json').read_bytes());expected_ids(cap,r['batch'])
    require(r['files']['recipe.json']==cap['recipe_sha256'],'Recipe changed')
    if current:
        source,env=capture();require(source==(path/'source.json').read_bytes() and env==(path/'environment.json').read_bytes(),'Source/environment drift')
    if r['batch']=='pilot':require(r['prior'] is None,'Pilot cannot import prior score')
    else:
        prior=r['prior'];require(isinstance(prior,dict) and set(prior)=={'path','pin'},'Missing pilot result');checked_package(Path(prior['path']),prior['pin']);p=json.loads((Path(prior['path'])/'results.json').read_bytes())
        require(p['batch']=='pilot' and p['state']=='passed' and p['capability_sha256']==CAP_PIN and p['binding_sha256']==BINDING_PIN,'Wrong prior score')
        require({row['study_id'] for row in p['cases']}==set(expected_ids(cap,'pilot')),'Incomplete pilot scores')
    return r


def prepare(batch,prior):
    require(digest(CAP.read_bytes())==CAP_PIN and digest(BINDING.read_bytes())==BINDING_PIN,'Pinned controls changed')
    prediction_index();source,env=capture();p=ROOT/('native-score-'+str(uuid4()));p.mkdir()
    files={'source.json':source,'environment.json':env,'binding.json':BINDING.read_bytes(),
        'capability.json':CAP.read_bytes(),'recipe.json':RECIPE.read_bytes()}
    for n,b in files.items():put(p/n,b)
    r=dict(schema_version='native-score-1',approval='D-304',batch=batch,limits=LIMITS,
           files={n:digest(b) for n,b in files.items()},prior=prior)
    put(p/'request.json',canonical(r));pin=digest(canonical(r));checked_request(p,pin)
    print(p,flush=True);print(pin,flush=True)


def summarize(rows):
    out={}
    for role in ('optimizer','evaluator'):
        rr=[r['metrics'] for r in rows if r['role']==role];require(rr,'Missing scored role')
        out[role]=dict(count=len(rr),mean_dice=sum(r['dice'] for r in rr)/len(rr),mean_recall=sum(r['recall'] for r in rr)/len(rr),
            mean_volume_ratio=sum(r['volume_ratio'] for r in rr)/len(rr),roi_diagnostic_pass=sum(r['roi_diagnostic_pass'] for r in rr),
            empty_predictions=sum(r['predicted_voxels']==0 for r in rr),
            mean_box_reference_coverage_empty_as_zero=sum(r['box_reference_coverage'] or 0 for r in rr)/len(rr))
    return out


def worker(path,pin):
    import nibabel as nib
    import numpy as np
    import torch
    from src.data.native_localizer_references import open_native_references
    from src.training.native_localizer_metrics import measure
    from src.training.twomm_inference_export import verify_export
    torch.set_num_threads(2);r=checked_request(path,pin)
    require(json.loads((path/'consumed.json').read_bytes())['request_sha256']==pin,'Missing consumed request')
    put(path/'worker-started.json',canonical(dict(request_sha256=pin)))
    predictions=prediction_index();binding=json.loads((path/'binding.json').read_bytes());started=time.monotonic()
    def check():
        require(time.monotonic()-started<LIMITS['seconds'] and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Scoring time/free cap')
    datasets,budget=open_native_references(repo=REPO,capability_bytes=(path/'capability.json').read_bytes(),
        trusted_capability_sha256=CAP_PIN,recipe_bytes=(path/'recipe.json').read_bytes(),trusted_recipe_sha256=r['files']['recipe.json'],
        batch_id=r['batch'],tick=check)
    rows=[]
    for role,ds in datasets.items():
        original={e['descriptor']['study_id']:e for e in binding['roles'][role]}
        for i in range(len(ds)):
            start=time.monotonic();d=ds.descriptor(i);sid=d['study_id'];entry=original[sid]
            require(entry['descriptor']==d,'Reference/cache qualification differs')
            folder,pred,receipt_pin=predictions[sid]
            require(pred['role']==role and pred['transform_sha256']==entry['transform_record']['record_sha256'],'Prediction role/geometry differs')
            prediction_path=folder/(sid.split(':')[-1]+'.nii.gz')
            verify_export(prediction_path,entry['transform_record'],expected_sha256=pred['export']['sha256'],expected_foreground=pred['export']['foreground'])
            # Read only this label; the inherited factory verifies original cohort/annotation qualifications.
            target,affine,provenance=ds.load(i,operation=role)
            raw=prediction_path.read_bytes();require(digest(raw)==pred['export']['sha256'],'Prediction changed before scoring')
            im=nib.Nifti1Image.from_bytes(gzip.decompress(raw));prediction=np.asanyarray(im.dataobj)
            require(list(im.shape)==entry['transform_record']['source_shape'] and
                np.array_equal(im.affine,np.asarray(entry['transform_record']['source_affine'],dtype=np.float32).astype(float)),
                'Scored prediction geometry differs')
            metrics=measure(prediction,target,affine)
            row=dict(study_id=sid,role=role,metrics=metrics,reference=provenance,
                prediction_sha256=pred['export']['sha256'],prediction_receipt_sha256=receipt_pin,
                transform_sha256=entry['transform_record']['record_sha256'],weights_sha256=WEIGHTS,seconds=time.monotonic()-start)
            put(path/(sid.split(':')[-1]+'.json'),canonical(row));rows.append(row)
            print(json.dumps(dict(study_id=sid,role=role,seconds=row['seconds'],dice=metrics['dice'],recall=metrics['recall'])),flush=True)
            del target,prediction,im;check()
    require(budget.files==len(budget.expected) and budget.pending is None and budget.compressed==budget.compressed_cap and budget.expanded==budget.expanded_cap,'Incomplete reference reads')
    cap=json.loads((path/'capability.json').read_bytes());require({x['study_id'] for x in rows}==set(expected_ids(cap,r['batch'])),'Scoring membership differs')
    put(path/'results.json',canonical(dict(state='passed',batch=r['batch'],cases=rows,summary=summarize(rows),
        capability_sha256=CAP_PIN,binding_sha256=BINDING_PIN,reference_files=budget.files,
        compressed_bytes=budget.compressed,expanded_bytes=budget.expanded,ct_files=0,model_forwards=0,optimizer_updates=0,
        weights_sha256=WEIGHTS,elapsed_seconds=time.monotonic()-started)))


def run(path,pin):
    r=checked_request(path,pin);ac,_=power();require(ac and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Power/free preflight')
    lock=os.open(ROOT/'.native-score.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        put(ROOT/('native-score-claim-'+CAP_PIN+'-'+r['batch']+'.json'),canonical(dict(request=str(path),request_sha256=pin)))
        put(path/'consumed.json',canonical(dict(request_sha256=pin)));start=time.monotonic();peak=0;reason=None
        with (path/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.native_localizer_scoring','--worker',str(path),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            try:
                next_power=0
                while proc.poll() is None:
                    elapsed=time.monotonic()-start
                    if elapsed>=next_power:ac,_=power();next_power=elapsed+10
                    require(ac and elapsed<LIMITS['seconds'],'Power/time cap')
                    require(shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Free floor')
                    require(sum(p.stat().st_size for p in path.iterdir() if p.is_file())<=LIMITS['output_bytes'],'Output cap')
                    obs=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                    if obs.returncode==0 and obs.stdout.strip():peak=max(peak,int(obs.stdout.strip())*1024)
                    elif proc.poll() is None:raise RuntimeError('Memory monitoring failed')
                    require(peak<=LIMITS['rss_bytes'],'RSS cap');time.sleep(.25)
                require(proc.returncode==0,'Worker failed')
            except BaseException as exc:reason=str(exc);raise
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                put(path/'supervisor.json',canonical(dict(exit_code=proc.returncode,reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))
        checked_request(path,pin)
        result=json.loads((path/'results.json').read_bytes());require(result['state']=='passed','No passing result')
        require(sum(p.stat().st_size for p in path.iterdir() if p.is_file())<LIMITS['output_bytes']-1024**2,'Output cap')
        put(path/'receipt.json',canonical(dict(state='complete',request_sha256=pin,files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in path.iterdir() if p.is_file()})))
        print(path,flush=True);print('receipt_sha256='+digest((path/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)


def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',choices=('pilot','remainder'));p.add_argument('--prior',type=Path);p.add_argument('--prior-pin')
    p.add_argument('--run',type=Path);p.add_argument('--worker',type=Path);p.add_argument('--pin');a=p.parse_args()
    if a.prepare:return prepare(a.prepare,None if not a.prior else dict(path=str(a.prior),pin=a.prior_pin))
    if a.worker:return worker(a.worker,a.pin)
    require(a.run is not None and a.pin is not None,'Explicit request required');run(a.run,a.pin)

if __name__=='__main__':main()
