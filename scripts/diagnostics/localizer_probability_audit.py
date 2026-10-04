"""D-290 single-use, inference-only terminal probability diagnostic."""
import argparse
import ast
import gc
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_smoke_run import capture,put,sha
from scripts.diagnostics.localizer_coverage_inspection import verify_runs,FROZEN,RUNS
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
PLAN=REPO/'docs/capstone/operations/CAP-EXP-006-PROBABILITY-AUDIT-PLAN-2026-09-29.md'
RUN=ROOT/RUNS['CAP-EXP-006'][0]


def compatibility():
    verify_runs()
    old=json.loads((RUN/'source.json').read_bytes())['files']
    changed=[]
    for name,content in old.items():
        current=(REPO/name).read_text()
        if current!=content:
            require(name=='src/training/expanded_executor.py','Changed inference dependency: '+name)
            for function in ('metrics','validate_checkpoint','validate_controls'):
                def definition(text):
                    return ast.dump(next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==function))
                require(definition(current)==definition(content),'Changed checkpoint or baseline metric function')
            changed.append(name)
    return dict(changed_original_files=changed,reason='Executor adds source-crop reporting in evaluate; audit uses unchanged predict/restore and verified metric/checkpoint functions.')


def prepare():
    runs=verify_runs();compat=compatibility();source,env=capture()
    dest=ROOT/('probability-audit-request-'+str(uuid4()));dest.mkdir()
    files={'source.json':source,'environment.json':env,'design.md':PLAN.read_bytes(),
           'capability.json':(FROZEN/'capability.json').read_bytes(),'recipe.json':(FROZEN/'recipe.json').read_bytes()}
    for n,b in files.items():put(dest/n,b)
    put(dest/'request.json',canonical(dict(decision='D-290',files={n:sha(b) for n,b in files.items()},
        checkpoint=runs['CAP-EXP-006']['checkpoints'][-1],compatibility=compat,seconds=1200,rss=16*1024**3,
        output_bytes=256*1024**2,thresholds=[.01,.05,.10,.25,.50],hard_mask_tolerance=0,optimizer_updates=0)))
    print(dest);print('request_sha256='+sha((dest/'request.json').read_bytes()))


def checked(request,pin):
    require(request.parent==ROOT and request.resolve(strict=True)==request,'Unsafe request')
    raw=(request/'request.json').read_bytes();require(sha(raw)==pin,'Changed request');r=json.loads(raw)
    require(r['decision']=='D-290' and r['seconds']==1200 and r['rss']==16*1024**3 and r['output_bytes']==256*1024**2 and r['optimizer_updates']==0 and r['hard_mask_tolerance']==0 and r['thresholds']==[.01,.05,.10,.25,.50],'Wrong audit scope')
    require(set(r['files'])=={'source.json','environment.json','design.md','capability.json','recipe.json'},'Wrong controls')
    for n,h in r['files'].items():require(sha((request/n).read_bytes())==h,'Changed frozen control')
    require(capture()==((request/'source.json').read_bytes(),(request/'environment.json').read_bytes()),'Source/environment changed')
    require(PLAN.read_bytes()==(request/'design.md').read_bytes(),'Plan changed')
    require(compatibility()==r['compatibility'],'Compatibility changed')
    require(verify_runs()['CAP-EXP-006']['checkpoints'][-1]==r['checkpoint'],'Terminal reference changed')
    return r


def worker(dest,request,pin):
    import numpy as np
    import nibabel as nib
    import torch
    from src.data.expanded_localizer_inputs import open_expanded_inputs
    from src.data.localizer_preprocessing_v2 import restore_to_source
    from src.training.expanded_localizer import RoleCache,restore,tensor_pin
    from src.training.expanded_executor import validate_checkpoint,validate_export
    from src.training.localizer_probability_audit import audit_probabilities,require_baseline_parity
    from scripts.diagnostics.expanded_localizer_launch import stores
    from scripts.diagnostics.localizer_content_verify import peak_rss
    require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK','0')=='0','Fallback enabled')
    torch.set_num_threads(2);req=checked(request,pin);start=time.monotonic()
    def tick():
        require(time.monotonic()-start<1200 and peak_rss()<16*1024**3,'Audit resource cap')
        require(shutil.disk_usage(REPO).free>100*1024**3,'Internal free floor')
        require(sum(p.stat().st_size for p in dest.iterdir())<256*1024**2,'Evidence cap')
    primary,_,_=stores();identity=json.loads((RUN/'identity.json').read_bytes());ref=req['checkpoint']
    files,_=primary.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:validate_checkpoint(f,identity))
    session=restore({k:v for k,v in files.items() if k not in {'plan.json','approval.json'}},identity)
    require(session.step==2400,'Wrong checkpoint step')
    def model_pin():return sha(canonical({k:tensor_pin(v.detach().cpu()) for k,v in session.model.state_dict().items()}))
    before=model_pin()
    # Make accidental optimizer use fail loudly in this diagnostic.
    def forbidden(*a,**kw):raise RuntimeError('Optimizer updates forbidden in audit')
    session.optimizer.step=forbidden
    datasets,budget=open_expanded_inputs(repo=REPO,capability_bytes=(request/'capability.json').read_bytes(),trusted_capability_sha256=req['files']['capability.json'],recipe_bytes=(request/'recipe.json').read_bytes(),trusted_recipe_sha256=req['files']['recipe.json'],tick=tick)
    cache=RoleCache(datasets,guard=tick)
    require(sha(canonical(cache.inputs))==identity['inputs_sha256'],'Cache role/input binding differs')
    result=verify_runs()['CAP-EXP-006'];refs={(r['role'],r['study_id']):r['reference'] for r in result['exports']};rows=[]
    session.model.eval()
    for role in ('optimizer','evaluator'):
        for i,sid in enumerate(cache.members(role)):
            tick();item=cache.get(role,i)
            with torch.inference_mode():prob=session.predict(item['image'])
            analysis=audit_probabilities(prob.numpy(),item['label'][0].numpy(),item['transform_record'])
            ref=refs[role,sid]
            export,_=primary.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:validate_export(f,json.loads(f['record.json'])))
            record=json.loads(export['record.json']);require(record['transform']==item['transform_record'],'Transform differs')
            require_baseline_parity(analysis['operating_points']['argmax'],record,role=role,study_id=sid)
            native=restore_to_source(prob.argmax(0,keepdim=True),item['transform_record'],discrete=True)[0].numpy().astype(np.uint8)
            saved=np.asarray(nib.Nifti1Image.from_bytes(gzip.decompress(export['prediction.nii.gz'])).dataobj)
            require(np.array_equal(native,saved),'Native hard-mask parity failed')
            row=dict(role=role,study_id=sid,exact_native_parity=True,**analysis);rows.append(row)
            put(dest/(sid.split(':')[-1]+'.json'),canonical(row));print(sid+' '+role+' parity passed',flush=True)
            del item,prob,analysis,export,record,native,saved;gc.collect();tick()
    require(len(rows)==27 and budget.files==54 and session.step==2400 and model_pin()==before,'Incomplete or mutated audit')
    checked(request,pin)
    put(dest/'results.json',canonical(dict(state='complete',cases=rows,checkpoint=req['checkpoint'],model_sha256_before=before,model_sha256_after=model_pin(),step=2400,optimizer_updates=0,model_inferences=27,source_files=budget.files,cache_bytes=cache.bytes,elapsed_seconds=time.monotonic()-start,policy_selected=False)))


def run(request,pin):
    checked(request,pin);dest=ROOT/('probability-audit-'+str(uuid4()));dest.mkdir();put(ROOT/('probability-audit-claim-'+pin+'.json'),canonical(dict(result=dest.name)))
    put(dest/'invocation.json',canonical(dict(request=str(request),pin=pin)));start=time.monotonic();peak=0;proc=None;reason=None;print(dest,flush=True)
    try:
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_probability_audit','--worker',str(dest),'--request',str(request),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
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
