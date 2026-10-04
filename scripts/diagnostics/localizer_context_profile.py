"""D-298 synthetic context profiler; production 96-cube guard stays unchanged."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
from uuid import uuid4

REPO=Path(__file__).resolve().parents[2]
GIB=1024**3
LIMITS=dict(seconds=600,rss_bytes=16*GIB,driver_bytes=16*GIB,output_bytes=256*1024**2,free_bytes=100*GIB)
SHAPES=((192,160,192),)

def profile_size(value):
    if type(value)!=int or value not in (96,144):raise ValueError("Only frozen 96/144 profile sizes")
    return value

def profile_config(size):
    return dict(patch_size=[profile_size(size)]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=40,loss_id="balanced_ce_dice_v1")

def patch_batch(image,target,config,*,step,member_id):
    # Synthetic centre crop only: this does not qualify the production sampler.
    n=profile_size(config["patch_size"][0]);slices=tuple(slice((s-n)//2,(s+n)//2) for s in image.shape[1:])
    return image[(slice(None),)+slices][None].clone(),target[(slice(None),)+slices][None].long().clone(),dict(member_id=member_id,step=step,policy="synthetic_center_only",physical_span_mm=n*2)

def profile_session(config):
    from types import SimpleNamespace
    from src.training.localizer import LocalizerSession
    # Reuse exact production architecture initialization; never widen its public config guard.
    base=LocalizerSession(dict(config,patch_size=[96]*3))
    return SimpleNamespace(model=base.model,optimizer=base.optimizer,scheduler=base.scheduler,step=0)


def sha(data):return hashlib.sha256(data).hexdigest()


def encode(value):return json.dumps(value,sort_keys=True,allow_nan=False).encode()


def write(dest,name,value):
    payload=encode(value)
    if Path(name).name!=name:raise ValueError('Invalid evidence member')
    if sum(p.stat().st_size for p in dest.iterdir() if p.is_file())+len(payload)>LIMITS['output_bytes']:raise ValueError('Output cap')
    with (dest/name).open('xb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())


def summary(values):
    if not values or any(not isinstance(x,(int,float)) or not 0<x<float('inf') for x in values):raise ValueError('Invalid timing samples')
    return dict(samples_seconds=values,median_seconds=statistics.median(values),min_seconds=min(values),max_seconds=max(values))


def stop_reason(elapsed,rss,output,free,ac):
    if elapsed>=LIMITS['seconds']:return 'time_cap'
    if rss>LIMITS['rss_bytes']:return 'rss_cap'
    if output>LIMITS['output_bytes']:return 'output_cap'
    if free<LIMITS['free_bytes']:return 'free_space_floor'
    if not ac:return 'AC_power_lost'
    return None


def power():
    result=subprocess.run(['/usr/bin/pmset','-g','batt'],capture_output=True,text=True,check=True,timeout=5)
    return 'AC Power' in result.stdout,result.stdout


def worker(dest,size):
    size=profile_size(size)
    if dest.parent!=REPO/'outputs/prowl' or dest.resolve(strict=True)!=dest:raise ValueError('Wrong destination')
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0':raise ValueError('Fallback must be disabled before import')
    import importlib.metadata
    import platform
    import torch
    from monai.inferers import sliding_window_inference
    from src.training.localizer import configured_loss
    if not torch.backends.mps.is_available():raise RuntimeError('MPS unavailable; no fallback')
    torch.set_num_threads(2)
    recommended=torch.mps.recommended_max_memory()
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/recommended))
    environment=dict(python=sys.version,platform=platform.platform(),machine=platform.machine(),
        packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
        mps_available=True,mps_fallback='0',recommended_max_memory=recommended,threads=2,
        config=profile_config(size))
    write(dest,'environment.json',environment)
    config=environment['config'];session=profile_session(config);session.model.to('mps')
    session.optimizer=torch.optim.AdamW(session.model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
    session.scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(session.optimizer,T_max=config['max_steps'])
    def synthetic(shape):
        y=torch.zeros((1,*shape),dtype=torch.float32)
        y[(slice(None),)+tuple(slice(s//3,2*s//3) for s in shape)]=1
        return y*.8+.1,y
    image,target=synthetic(SHAPES[0]);samples=[];memories=[];updates=[]
    def memory(stage):
        torch.mps.synchronize()
        row=dict(stage=stage,allocated_bytes=torch.mps.current_allocated_memory(),driver_bytes=torch.mps.driver_allocated_memory())
        if row['driver_bytes']>LIMITS['driver_bytes']:raise MemoryError('MPS driver cap')
        memories.append(row)
    def update(current,step):
        torch.mps.synchronize();start=time.monotonic()
        x,y,trace=patch_batch(image,target,config,step=step,member_id='invented-volume')
        x=x.to('mps');y=y.to('mps');current.model.train();current.optimizer.zero_grad(set_to_none=True)
        loss=configured_loss(current.model(x),y,config)
        if not torch.isfinite(loss).item():raise ValueError('Nonfinite loss')
        loss.backward()
        if not all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in current.model.parameters()):raise ValueError('Invalid gradients')
        current.optimizer.step();current.scheduler.step();current.step=step+1
        if not all(torch.isfinite(p).all().item() for p in current.model.parameters()):raise ValueError('Nonfinite parameters')
        torch.mps.synchronize();elapsed=time.monotonic()-start
        memory('update-'+str(step+1))
        return dict(step=step+1,seconds=elapsed,loss=loss.item(),sampler=trace)
    for step in range(8):
        row=update(session,step);updates.append(row)
        print(json.dumps(dict(stage='update',step=step+1,seconds=row['seconds'])),flush=True)
        if step>=2:samples.append(row['seconds'])
    session.model.eval();inference=[]
    with torch.no_grad():
        for shape in SHAPES:
            volume,_=synthetic(shape);times=[]
            for repeat in range(2):
                torch.mps.synchronize();start=time.monotonic()
                prediction=sliding_window_inference(volume[None],[size]*3,1,session.model,overlap=.25,
                    mode='constant',padding_mode='constant',sw_device='mps',device='cpu')
                torch.mps.synchronize();times.append(time.monotonic()-start)
                if prediction.device.type!='cpu' or prediction.shape!=(1,2,*shape) or not torch.isfinite(prediction).all():raise ValueError('Invalid CPU-stitched prediction')
                memory('inference-'+str(shape)+'-'+str(repeat))
                print(json.dumps(dict(stage='inference',shape=shape,repeat=repeat,seconds=times[-1])),flush=True)
            inference.append(dict(shape=shape,timing=summary(times)))
        fixed,_y,_=patch_batch(image,target,config,step=0,member_id='reload-probe')
        before=session.model(fixed.to('mps')).softmax(1).cpu()
    def cpu_tree(value):
        if isinstance(value,torch.Tensor):return value.detach().cpu().clone()
        if isinstance(value,dict):return {k:cpu_tree(v) for k,v in value.items()}
        if isinstance(value,list):return [cpu_tree(v) for v in value]
        if isinstance(value,tuple):return tuple(cpu_tree(v) for v in value)
        return value
    torch.mps.synchronize();start=time.monotonic()
    state=cpu_tree(dict(model=session.model.state_dict(),optimizer=session.optimizer.state_dict(),
        scheduler=session.scheduler.state_dict(),step=session.step,config=config))
    transfer_seconds=time.monotonic()-start
    path=dest/'profile-state.pt';start=time.monotonic()
    with path.open('xb') as stream:torch.save(state,stream);stream.flush();os.fsync(stream.fileno())
    write_seconds=time.monotonic()-start;pin=sha(path.read_bytes())
    del state,session
    torch.mps.empty_cache();start=time.monotonic()
    if sha(path.read_bytes())!=pin:raise ValueError('Changed checkpoint')
    state=torch.load(path,map_location='cpu',weights_only=True);read_seconds=time.monotonic()-start
    start=time.monotonic();fresh=profile_session(config);fresh.model.load_state_dict(state['model'],strict=True);fresh.model.to('mps')
    fresh.optimizer=torch.optim.AdamW(fresh.model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
    fresh.scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(fresh.optimizer,T_max=config['max_steps'])
    fresh.optimizer.load_state_dict(state['optimizer']);fresh.scheduler.load_state_dict(state['scheduler']);fresh.step=state['step']
    torch.mps.synchronize();restore_seconds=time.monotonic()-start;del state
    fresh.model.eval()
    with torch.no_grad():after=fresh.model(fixed.to('mps')).softmax(1).cpu()
    difference=(before-after).abs().max().item()
    if not torch.allclose(before,after,atol=1e-5,rtol=0):raise ValueError('MPS reload mismatch')
    memory('reload');resumed=update(fresh,8)
    report=dict(state='passed',synthetic_only=True,model_parameters=sum(p.numel() for p in fresh.model.parameters()),
        warmup_updates=2,timed_updates=6,updates=updates,training=summary(samples),inference=inference,
        checkpoint=dict(bytes=path.stat().st_size,sha256=pin,transfer_to_cpu_seconds=transfer_seconds,
            write_fsync_seconds=write_seconds,hash_and_read_seconds=read_seconds,restore_mps_seconds=restore_seconds,
            max_reload_probability_difference=difference,tolerance_atol=1e-5,resumed_update=resumed),
        memory_samples=memories,automatic_cpu_fallback=False,production_checkpoint=False)
    write(dest,'report.json',report)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=Path);parser.add_argument('--run',action='store_true');parser.add_argument('--size',type=int,required=True);args=parser.parse_args();profile_size(args.size)
    if args.worker:return worker(args.worker,args.size)
    if not args.run:parser.error('--run required')
    ac,power_text=power()
    if not ac or shutil.disk_usage(REPO).free<LIMITS['free_bytes']:raise RuntimeError('Power/free-space preflight failed')
    root=REPO/'outputs/prowl'
    lock=os.open(root/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dest=root/('context-resource-'+str(uuid4()));dest.mkdir()
        sources=['scripts/diagnostics/localizer_context_profile.py','src/training/localizer.py','src/models/segresnet.py']
        request=dict(patch_size=args.size,spacing_mm=2,production_sampler_qualified=False,limits=LIMITS,shapes=SHAPES,power=power_text,source={n:(REPO/n).read_text() for n in sources},
            git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            git_status=subprocess.check_output(['git','--no-optional-locks','status','--short'],cwd=REPO,text=True),
            plan=(REPO/'docs/capstone/operations/LOCALIZER-CONTEXT-PROFILE-PLAN-2026-09-30.md').read_text(),
            promotion_eligible=False,hardware=subprocess.check_output(['/usr/sbin/sysctl','-n','hw.memsize','hw.model'],text=True))
        write(dest,'request.json',request);print(dest,flush=True)
        env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1')
        start=time.monotonic();peak=0;reason=None
        with (dest/'worker.log').open('xb') as log:
            process=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_context_profile','--worker',str(dest),'--size',str(args.size)],
                cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                next_power=0
                while process.poll() is None:
                    elapsed=time.monotonic()-start
                    if elapsed>=next_power:ac,_=power();next_power=elapsed+10
                    observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(process.pid)],capture_output=True,text=True,timeout=5)
                    if observed.returncode==0 and observed.stdout.strip():peak=max(peak,int(observed.stdout.strip())*1024)
                    elif process.poll() is None:raise RuntimeError('Memory monitor failed')
                    size=sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
                    reason=stop_reason(elapsed,peak,size,shutil.disk_usage(REPO).free,ac)
                    if reason:raise RuntimeError(reason)
                    time.sleep(.25)
                if process.returncode:reason='worker_failed';raise RuntimeError(reason)
            except BaseException as error:
                reason=reason or type(error).__name__;raise
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
                # Preserve failure controls even when an output cap was crossed.
                with (dest/'supervisor.json').open('xb') as stream:stream.write(encode(dict(
                    exit_code=process.returncode,stop_reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))
        report=json.loads((dest/'report.json').read_bytes())
        if report['state']!='passed':raise ValueError('No passing worker report')
        inventory={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir() if p.is_file()}
        write(dest,'receipt.json',dict(state='complete',files=inventory,synthetic_only=True))
        print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)


if __name__=='__main__':main()
