"""D-284 single-use forward-only real profile and separate synthetic MPS recovery."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_smoke_run import capture as base_capture,encoded,put,sha
from scripts.diagnostics.expanded_localizer_preprocessing import CAP,RECIPE,LIMITS
from src.data.source_inventory_records import require
REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
PLAN=REPO/'docs/capstone/operations/EXPANDED-RUNNER-PLAN-2026-09-29.md'


def capture():
    source,env=base_capture();env=json.loads(env);env['cache']='bounded_processed_ram_512MiB';return source,encoded(env)


def prepare():
    source,env=capture();dest=ROOT/('expanded-profile-request-'+str(uuid4()));dest.mkdir()
    files={'source.json':source,'environment.json':env,'capability.json':CAP.read_bytes(),'recipe.json':RECIPE.read_bytes(),'plan.md':PLAN.read_bytes()}
    for n,b in files.items():put(dest/n,b)
    req=dict(approval='D-284',operation='expanded_forward_profile',real_updates=0,limits=LIMITS,files={n:sha(b) for n,b in files.items()})
    put(dest/'request.json',encoded(req));print(dest);print(sha((dest/'request.json').read_bytes()))


def checked_request(path,pin):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe request')
    raw=(path/'request.json').read_bytes();require(sha(raw)==pin,'Request pin differs');req=json.loads(raw)
    require(req['approval']=='D-284' and req['operation']=='expanded_forward_profile' and req['real_updates']==0 and req['limits']==LIMITS,'Wrong profile scope')
    require(set(req['files'])=={'source.json','environment.json','capability.json','recipe.json','plan.md'},'Wrong request inventory')
    for n,h in req['files'].items():require(sha((path/n).read_bytes())==h,'Changed control')
    source,env=capture();require(source==(path/'source.json').read_bytes() and env==(path/'environment.json').read_bytes(),'Changed code/environment')
    return req


def worker(dest,request,pin):
    import gc
    import torch
    from src.data.expanded_localizer_inputs import open_expanded_inputs
    from src.data.manifest_records import canonical,digest
    from src.training.expanded_localizer import RoleCache,evaluate_role,checkpoint,restore
    from src.training.localizer_run import MPSRun
    from scripts.diagnostics.localizer_content_verify import peak_rss
    torch.set_num_threads(2);req=checked_request(request,pin);start=time.monotonic()
    def guard():
        require(time.monotonic()-start<LIMITS['seconds'] and peak_rss()<LIMITS['rss'],'Profile resource cap')
        require(shutil.disk_usage(REPO).free>LIMITS['internal_free'],'Free-space floor')
    datasets,budget=open_expanded_inputs(repo=REPO,capability_bytes=(request/'capability.json').read_bytes(),trusted_capability_sha256=req['files']['capability.json'],
        recipe_bytes=(request/'recipe.json').read_bytes(),trusted_recipe_sha256=req['files']['recipe.json'],tick=guard)
    print('frozen bundle verified',flush=True);cache=RoleCache(datasets,guard=guard);load_seconds=time.monotonic()-start
    require(budget.files==54 and len(cache.members('optimizer'))==16 and len(cache.members('evaluator'))==11,'Incomplete input scope')
    print(json.dumps(dict(cache_bytes=cache.bytes,load_seconds=load_seconds)),flush=True)
    config=dict(patch_size=[96]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=300,loss_id='balanced_ce_dice_v1')
    identity=dict(schema_version='1.0.0',purpose='qualified-expanded-forward-profile',run_id='expanded-'+dest.name,device='mps',config=config,
        inputs_sha256=digest(canonical(cache.inputs)),source_sha256=req['files']['source.json'],environment_sha256=req['files']['environment.json'])
    session=MPSRun(config);timings={};metrics={}
    for role in ('optimizer','evaluator'):
        began=time.monotonic();metrics[role]=evaluate_role(session,cache,identity,role,guard=guard);torch.mps.synchronize();timings[role]=time.monotonic()-began
        print(json.dumps(dict(role=role,seconds=timings[role],cases=len(metrics[role]['cases']))),flush=True)
    probe=torch.full((1,96,96,96),.25);before=session.predict(probe)
    files=checkpoint(session,cache,identity,[])
    restored=restore(files,identity);after=restored.predict(probe);delta=float((before-after).abs().max())
    require(delta==0,'Step-zero checkpoint probe differs')
    cp=dest/'checkpoint';cp.mkdir()
    for n,b in files.items():put(cp/n,b)
    import io
    stream=io.BytesIO();torch.save(before,stream);put(cp/'probe.pt',stream.getvalue())
    manifest={n:sha((cp/n).read_bytes()) for n in (*files,'probe.pt')};put(cp/'receipt.json',encoded(manifest))
    checked_request(request,pin);guard()
    put(dest/'results.json',encoded(dict(state='complete',real_updates=session.step,source_files=budget.files,cache_bytes=cache.bytes,load_seconds=load_seconds,
        full_volume_seconds=timings,metrics=metrics,checkpoint_probe_max_difference=delta,checkpoint_receipt_sha256=sha((cp/'receipt.json').read_bytes()),peak_rss=peak_rss(),elapsed_seconds=time.monotonic()-start)))


def recover(path,pin):
    import torch
    from src.training.expanded_localizer import restore
    require(sha((path/'receipt.json').read_bytes())==pin,'Recovery receipt differs');manifest=json.loads((path/'receipt.json').read_bytes())
    require(set(manifest)=={'identity.json','inputs.json','progress.json','state.pt','probe.pt'},'Recovery inventory differs')
    for n,h in manifest.items():require(sha((path/n).read_bytes())==h,'Corrupt checkpoint member')
    torch.set_num_threads(2);identity=json.loads((path/'identity.json').read_bytes())
    files={n:(path/n).read_bytes() for n in manifest if n!='probe.pt'};session=restore(files,identity)
    expected=torch.load(path/'probe.pt',map_location='cpu',weights_only=True)
    actual=session.predict(torch.full((1,*identity['config']['patch_size']),.25));delta=float((actual-expected).abs().max())
    require(delta==0,'Fresh-process recovery probe differs')
    print(json.dumps(dict(state='fresh_process_recovery_pass',step=session.step,max_difference=delta,receipt_sha256=pin)))


def synthetic():
    import io
    import numpy as np
    import torch
    from src.data.localizer_preprocessing_v2 import preprocess
    from src.data.manifest_records import canonical,digest
    from src.training.expanded_localizer import RoleCache,synthetic_update,checkpoint,restore
    from src.training.localizer_run import MPSRun
    from scripts.diagnostics.localizer_content_verify import peak_rss
    torch.set_num_threads(2);start=time.monotonic()
    class Fixture:
        def __init__(self,role):
            self.role=role;self.recipe=json.loads(RECIPE.read_bytes())
            self.recipe.update(spacing_mm=[1.]*3)
        def __len__(self):return 16 if self.role=='optimizer' else 11
        def descriptor(self,i):return dict(study_id=f'synthetic-{self.role}-{i}',operation=self.role,protected_role='train' if self.role=='optimizer' else 'validation')
        def load(self,i,*,operation):
            require(operation==self.role,'Wrong fixture role')
            y=np.zeros((24,24,24),np.uint8);y[5:15,6:16,4:14]=1
            x=preprocess(y.astype(np.float32)*300-100,np.eye(4),self.recipe,target=y)
            x['provenance']={'descriptor':self.descriptor(i)};return x
    cache=RoleCache({r:Fixture(r) for r in ('optimizer','evaluator')})
    source,env=capture();config=dict(patch_size=[96]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=4,loss_id='balanced_ce_dice_v1')
    identity=dict(schema_version='1.0.0',purpose='synthetic-expanded-verification',run_id='expanded-synthetic-'+str(uuid4()),device='mps',config=config,
        inputs_sha256=digest(canonical(cache.inputs)),source_sha256=sha(source),environment_sha256=sha(env))
    session=MPSRun(config);history=[];times=[]
    for _ in range(2):
        begin=time.monotonic();history.append(synthetic_update(session,cache,identity));torch.mps.synchronize();times.append(time.monotonic()-begin)
    files=checkpoint(session,cache,identity,history);resumed=restore(files,identity)
    a=synthetic_update(session,cache,identity);b=synthetic_update(resumed,cache,identity)
    require(a==b,'MPS resumed update trace/loss differs')
    parameter_delta=max(float((x.detach()-y.detach()).abs().max()) for x,y in zip(session.model.parameters(),resumed.model.parameters()))
    print(json.dumps(dict(resumed_parameter_max_difference=parameter_delta)),flush=True)
    require(parameter_delta<=1e-6,'MPS resumed weights exceed float32 continuation tolerance')
    history.append(a);files=checkpoint(session,cache,identity,history)
    probe=session.predict(torch.full((1,96,96,96),.25));stream=io.BytesIO();torch.save(probe,stream)
    dest=ROOT/('expanded-synthetic-'+str(uuid4()));dest.mkdir()
    for n,data in dict(files,**{'probe.pt':stream.getvalue()}).items():put(dest/n,data)
    put(dest/'receipt.json',encoded({n:sha((dest/n).read_bytes()) for n in (*files,'probe.pt')}))
    put(dest/'results.json',encoded(dict(state='synthetic_recovery_pass',completed_steps=session.step,actual_synthetic_updates=4,real_updates=0,
        resumed_parameter_max_difference=parameter_delta,continuation_tolerance=1e-6,update_seconds=times,resumed_next_member=a['sampling']['member_id'],cache_bytes=cache.bytes,peak_rss=peak_rss(),elapsed_seconds=time.monotonic()-start)))
    print(dest);print('checkpoint_receipt_sha256='+sha((dest/'receipt.json').read_bytes()))


def run(request,pin):
    req=checked_request(request,pin);dest=ROOT/('expanded-profile-'+str(uuid4()));dest.mkdir()
    put(ROOT/('expanded-profile-claim-'+pin+'.json'),encoded(dict(result=dest.name,request_sha256=pin)))
    for n in ('request.json',*req['files']):put(dest/n,(request/n).read_bytes())
    start=time.monotonic();peak=0;reason=None;proc=None;print(dest,flush=True)
    try:
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.expanded_localizer_profile','--worker',str(dest),'--request',str(request),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                require(time.monotonic()-start<LIMITS['seconds'],'Supervisor time cap')
                require(shutil.disk_usage(REPO).free>LIMITS['internal_free'],'Supervisor free floor')
                require(sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())<LIMITS['output_bytes'],'Supervisor output cap')
                p=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                if p.returncode==0 and p.stdout.strip():peak=max(peak,int(p.stdout.strip())*1024);require(peak<LIMITS['rss'],'Supervisor RSS cap')
                elif proc.poll() is None:raise RuntimeError('Memory monitor unavailable')
                time.sleep(.25)
            require(proc.returncode==0,'Worker failed; retained evidence')
        checked_request(request,pin)
    except BaseException as exc:reason=str(exc);raise
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        put(dest/'supervisor.json',encoded(dict(exit_code=None if proc is None else proc.returncode,stop_reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))
    put(dest/'receipt.json',encoded({str(p.relative_to(dest)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.rglob('*') if p.is_file()}))
    print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--synthetic',action='store_true');p.add_argument('--prepare',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--pin');p.add_argument('--worker',type=Path);p.add_argument('--recover',type=Path);a=p.parse_args()
    if a.synthetic:synthetic()
    elif a.prepare:prepare()
    elif a.recover and a.pin:recover(a.recover,a.pin)
    elif a.worker and a.request and a.pin:worker(a.worker,a.request,a.pin)
    elif a.request and a.pin:run(a.request,a.pin)
    else:p.error('Choose prepare, recover or exact request')
