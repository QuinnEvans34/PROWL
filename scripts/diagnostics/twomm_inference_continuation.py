"""D-303 single-use remaining145-case cached inference and native export; zero real updates."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_context_profile import power
from scripts.diagnostics.localizer_smoke_run import capture,put
from scripts.diagnostics.expanded_localizer_launch import stores
from scripts.diagnostics.twomm_session_rehearsal import config,PRIMARY,BACKUP
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl';GIB=1024**3
CACHE=ROOT/'twomm-cache-build-80569d7d-94e0-4c52-91ba-1a128dd076ae/cache'
CACHE_PIN='b61897ed3176fecd9d8ca143285d9700699c1557537ba15b966a487134342bf7'
BINDING=ROOT/'twomm-cache-readiness-20260930/proposed-binding.json'
BINDING_PIN='ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d'
LIMITS=dict(seconds=1200,rss_bytes=16*GIB,driver_bytes=16*GIB,output_bytes=4*GIB,free_bytes=100*GIB)
from scripts.diagnostics import twomm_inference_pilot as pilot
PILOT=ROOT/'twomm-session-pilot-72fa2ebb-0fe4-4ee4-9682-b001335f05b1'
PILOT_PIN='5764b267a2f2cfef95e327804364b5b4228f51c2359274e1c4b18c0e54f3d76f'


def cases(binding):
    require(set(binding['roles'])=={'optimizer','evaluator'},'Wrong roles')
    all_cases=[]
    for role,count in (('optimizer',113),('evaluator',40)):
        entries=binding['roles'][role];require(len(entries)==count,'Incomplete full cohort')
        for i,e in enumerate(entries):
            d=e['descriptor']
            require(d['operation']==role and d['protected_role']==('train' if role=='optimizer' else 'validation'),'Wrong protected role')
            all_cases.append(dict(role=role,index=i,study_id=d['study_id']))
    require(len({c['study_id'] for c in all_cases})==153,'Duplicate member')
    require(all(c in all_cases for c in pilot.CASES),'Pilot ancestry differs')
    selected=[c for c in all_cases if c not in pilot.CASES]
    require(len(selected)==145 and sum(c['role']=='optimizer' for c in selected)==107,'Wrong continuation counts')
    return selected


def check_pilot():
    require(PILOT.resolve(strict=True)==PILOT,'Unsafe pilot path')
    raw=(PILOT/'receipt.json').read_bytes();require(digest(raw)==PILOT_PIN,'Pilot completion changed')
    receipt=json.loads(raw);require(receipt['state']=='complete' and receipt['real_updates']==0,'Pilot not passed')
    for n,r in receipt['files'].items():
        require(Path(n).name==n,'Unsafe pilot member')
        p=PILOT/n;require(p.is_file() and not p.is_symlink(),'Missing pilot evidence')
        b=p.read_bytes();require(len(b)==r['bytes'] and digest(b)==r['sha256'],'Pilot evidence changed')
    return receipt

CONTROL_NAMES={'inputs.json','source.json','environment.json'}


def stop_reason(elapsed,rss,output,free,ac):
    for condition,reason in ((elapsed>=LIMITS['seconds'],'time_cap'),(rss>LIMITS['rss_bytes'],'rss_cap'),
        (output>LIMITS['output_bytes'],'output_cap'),(free<LIMITS['free_bytes'],'free_floor'),(not ac,'AC_lost')):
        if condition:return reason
    return None


def checked_request(dest,pin,*,check_code=True):
    require(dest.parent==ROOT and dest.resolve(strict=True)==dest,'Unsafe continuation destination')
    check_pilot()
    raw=(dest/'request.json').read_bytes();require(digest(raw)==pin,'Request pin differs');r=json.loads(raw)
    require(set(r)=={'schema_version','approval','operation','cache','cache_pin','binding_pin','cases',
        'limits','config','files','storage_ceilings','run_id','pilot_receipt_sha256'} and r['schema_version']=='twomm-continuation-1' and
        r['approval']=='D-303' and r['operation']=='remaining145-zero-update-inference' and
        r['cache']==str(CACHE) and r['cache_pin']==CACHE_PIN and r['binding_pin']==BINDING_PIN and
        r['pilot_receipt_sha256']==PILOT_PIN and r['limits']==LIMITS and r['config']==config() and
        r['run_id']==dest.name and dest.name.startswith('twomm-session-continuation-'),'Continuation request scope differs')
    require(set(r['files'])==CONTROL_NAMES,'Control inventory differs')
    for n,h in r['files'].items():require(digest((dest/n).read_bytes())==h,'Frozen control changed')
    require(r['files']['inputs.json']==BINDING_PIN,'Wrong input control')
    require(len(r['storage_ceilings'])==2 and all(type(n)==int and n>0 for n in r['storage_ceilings']),
            'Missing storage ceilings')
    b=json.loads((dest/'inputs.json').read_bytes())
    require(r['cases']==cases(b),'Continuation membership differs')
    for c in r['cases']:
        d=b['roles'][c['role']][c['index']]['descriptor']
        require(d['study_id']==c['study_id'] and d['operation']==c['role'] and
                d['protected_role']==('train' if c['role']=='optimizer' else 'validation'),'Case role/index differs')
    if check_code:
        source,env=capture()
        require(source==(dest/'source.json').read_bytes() and env==(dest/'environment.json').read_bytes(),'Code/environment drift')
    return r


def claim(dest,pin):
    # Exclusive durable marker: any attempted execution permanently consumes this request.
    put(dest/'consumed.json',canonical(dict(request_sha256=pin,attempt=str(uuid4()),state='consumed')))


def prepare():
    check_pilot();pilot.verify_results(PILOT)
    require(digest(BINDING.read_bytes())==BINDING_PIN and digest((CACHE/'complete.json').read_bytes())==CACHE_PIN,
            'Cache controls changed')
    primary,backup,_=stores()
    for store,reserve in ((primary,128*1024**2),(backup,256*1024**2)):
        with store.opened() as fd:store.space(fd,reserve)
    source,env=capture()
    dest=ROOT/('twomm-session-continuation-'+str(uuid4()));dest.mkdir()
    controls={'inputs.json':BINDING.read_bytes(),'source.json':source,'environment.json':env}
    for n,b in controls.items():put(dest/n,b)
    request=dict(schema_version='twomm-continuation-1',approval='D-303',operation='remaining145-zero-update-inference',
        cache=str(CACHE),cache_pin=CACHE_PIN,binding_pin=BINDING_PIN,cases=cases(json.loads(BINDING.read_bytes())),pilot_receipt_sha256=PILOT_PIN,limits=LIMITS,config=config(),
        files={n:digest(b) for n,b in controls.items()},storage_ceilings=[primary.quota_bytes,backup.quota_bytes],run_id=dest.name)
    put(dest/'request.json',canonical(request));print(dest,flush=True);print(digest(canonical(request)),flush=True)


def identity(request):
    from src.training.twomm_session import POLICY
    return dict(schema_version='twomm-session-1',run_id=request['run_id'],purpose='qualified-cache-inference',
        device='mps',config=request['config'],sampling_policy=POLICY,cache_receipt_sha256=request['cache_pin'],
        inputs_sha256=request['binding_pin'],source_sha256=request['files']['source.json'],
        environment_sha256=request['files']['environment.json'])


def no_raw_reads(event,args):
    if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        path=os.path.abspath(os.fsdecode(args[0]))
        require(not path.startswith('/Volumes/PROWL-Data/PROWL/sources/'),'Raw source reads forbidden')


def worker(dest,pin,stage,reference_pin=None):
    r=checked_request(dest,pin)
    require(json.loads((dest/'consumed.json').read_bytes())['request_sha256']==pin,'Missing consumed request')
    require(stage in ('profile','recover'),'Unsupported worker stage')
    put(dest/(stage+'-started.json'),canonical(dict(request_sha256=pin,stage=stage)))
    sys.addaudithook(no_raw_reads)
    if stage=='recover':
        def primary_block(event,args):
            if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
                require(not os.path.abspath(os.fsdecode(args[0])).startswith('/Volumes/PROWL-Data'), 'Primary reads forbidden')
        sys.addaudithook(primary_block)
    import torch
    from src.training.twomm_cache import DiskRoleCache
    from src.training.twomm_session import (Session,weight_digest,synthetic_item,payload,publish_checkpoint,
                                           validate_payload,restore_payload)
    from src.training.twomm_inference_export import export_prediction
    from src.operations.localizer_backup import backup_checkpoint,restore_backup
    torch.set_num_threads(2)
    require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS required')
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    ident=identity(r)
    def memory():
        torch.mps.synchronize();d=torch.mps.driver_allocated_memory()
        require(d<=LIMITS['driver_bytes'],'Driver memory cap')
        return dict(driver_bytes=d,live_bytes=torch.mps.current_allocated_memory())
    if stage=='profile':
        started=time.monotonic();binding=json.loads((dest/'inputs.json').read_bytes())
        cache=DiskRoleCache(CACHE,CACHE_PIN,binding,BINDING_PIN);open_seconds=time.monotonic()-started
        session=Session(ident);before=weight_digest(session);rows=[]
        for c in r['cases']:
            timing={};p,trace,item=session.predict_cache(cache,c['role'],c['index'],timings=timing)
            require(item['study_id']==c['study_id'],'Returned member differs')
            export=export_prediction(dest/(c['study_id'].split(':')[-1]+'.nii.gz'),p,item['transform_record'])
            require(weight_digest(session)==before and session.step==0 and not session.optimizer.state,'Inference changed model')
            row=dict(**c,**timing,padding=trace,export=export,processed_shape=list(p.shape[1:]),
                transform_sha256=item['transform_record']['record_sha256'],memory=memory(),weights_unchanged=True)
            put(dest/(c['study_id'].split(':')[-1]+'.json'),canonical(row));rows.append(row)
            print(json.dumps(dict(case=c['study_id'],inference_seconds=timing['inference_seconds'],memory=row['memory'])),flush=True)
            del p,item;torch.mps.empty_cache()
        probe,_=session.predict(synthetic_item()['image']);require(weight_digest(session)==before,'Probe changed model')
        with (dest/'probe.pt').open('xb') as f:torch.save(probe,f);f.flush();os.fsync(f.fileno())
        primary,backup,_=stores()
        for k,s in enumerate((primary,backup)):s.quota_bytes=min(s.quota_bytes,r['storage_ceilings'][k])
        files=payload(session,ident,{n:(dest/n).read_bytes() for n in CONTROL_NAMES})
        ref=publish_checkpoint(primary,files,ident)
        back=backup_checkpoint(primary,backup,ref,ident,source_domain=PRIMARY,destination_domain=BACKUP,validator=validate_payload)
        put(dest/'references.json',canonical(dict(primary=ref,backup=back,weights_sha256=before,
                                                probe_sha256=digest((dest/'probe.pt').read_bytes()))))
        put(dest/'profile.json',canonical(dict(state='passed',cache_open_seconds=open_seconds,cases=rows,
            completed_step=session.step,weights_sha256=before,raw_source_reads=0,real_updates=0)))
    else:
        require(digest((dest/'references.json').read_bytes())==reference_pin,'Recovery references changed')
        refs=json.loads((dest/'references.json').read_bytes());_,backup,restore=stores(recovery_only=True)
        for s in (backup,restore):s.quota_bytes=min(s.quota_bytes,r['storage_ceilings'][1])
        files,ref=restore_backup(backup,restore,refs['backup'],refs['primary'],ident,validator=validate_payload)
        session=restore_payload(files,ident);require(weight_digest(session)==refs['weights_sha256'],'Restored model differs')
        require(session.step==0 and not session.optimizer.state,'Unexpected restored updates')
        probe,_=session.predict(synthetic_item()['image'])
        require(digest((dest/'probe.pt').read_bytes())==refs['probe_sha256'],'Probe changed')
        expected=torch.load(dest/'probe.pt',map_location='cpu',weights_only=True)
        delta=float((probe-expected).abs().max());require(delta<=1e-5,'Restored probe differs')
        put(dest/'recover.json',canonical(dict(state='passed',primary_reads_forbidden=True,restored=ref,
            probability_max_difference=delta,weights_sha256=weight_digest(session),completed_step=session.step,memory=memory())))


def supervise(dest,pin,stage,*,deadline,reference_pin=None):
    start=time.monotonic();peak=0;reason=None
    env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1')
    args=[sys.executable,'-m','scripts.diagnostics.twomm_inference_continuation','--worker',str(dest),
          '--pin',pin,'--stage',stage]
    if reference_pin:args+=['--reference-pin',reference_pin]
    with (dest/(stage+'.log')).open('xb') as log:
        process=subprocess.Popen(args,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            next_power=0;ac=True
            while process.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed>=next_power:ac,_=power();next_power=elapsed+10
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(process.pid)],capture_output=True,text=True,timeout=5)
                if observed.returncode==0 and observed.stdout.strip():peak=max(peak,int(observed.stdout.strip())*1024)
                elif process.poll() is None:raise RuntimeError('Memory monitoring failed')
                size=sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
                reason=stop_reason(LIMITS['seconds']-(deadline-time.monotonic()),peak,size,shutil.disk_usage(REPO).free,ac)
                require(reason is None,str(reason));time.sleep(.25)
            require(process.returncode==0,'Worker failed')
        except BaseException as error:
            reason=reason or type(error).__name__;raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            put(dest/(stage+'-supervisor.json'),canonical(dict(exit_code=process.returncode,reason=reason,
                peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))


def run(dest,pin):
    checked_request(dest,pin);ac,_=power()
    require(ac and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Power/free preflight')
    lock=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);claim(dest,pin);deadline=time.monotonic()+LIMITS['seconds']
        supervise(dest,pin,'profile',deadline=deadline)
        supervise(dest,pin,'recover',deadline=deadline,reference_pin=digest((dest/'references.json').read_bytes()))
        checked_request(dest,pin);verify_results(dest);reconcile(dest)
        ac,_=power()
        require(stop_reason(LIMITS['seconds']-(deadline-time.monotonic()),0,0,shutil.disk_usage(REPO).free,ac) is None,
                'Final time/power/free-space check failed')
        inventory={p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in dest.iterdir() if p.is_file()}
        require(sum(x['bytes'] for x in inventory.values())<LIMITS['output_bytes']-1024**2,'Output cap')
        put(dest/'receipt.json',canonical(dict(state='complete',request_sha256=pin,files=inventory,real_updates=0)))
        print(dest,flush=True);print('receipt_sha256='+digest((dest/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)


def verify_results(dest):
    from src.training.twomm_inference_export import verify_export
    profile=json.loads((dest/'profile.json').read_bytes());recovery=json.loads((dest/'recover.json').read_bytes())
    require(profile['state']==recovery['state']=='passed' and profile['completed_step']==recovery['completed_step']==0 and
        profile['real_updates']==0 and profile['raw_source_reads']==0 and recovery['primary_reads_forbidden'] is True and
        recovery['weights_sha256']==profile['weights_sha256'] and
        0<=recovery['probability_max_difference']<=1e-5,'Incomplete readiness results')
    require([{k:row[k] for k in ('role','index','study_id')} for row in profile['cases']]==cases(json.loads((dest/'inputs.json').read_bytes())),'Incomplete continuation membership')
    binding=json.loads((dest/'inputs.json').read_bytes())
    for row in profile['cases']:
        record=binding['roles'][row['role']][row['index']]['transform_record']
        require(row['weights_unchanged'] is True and row['transform_sha256']==record['record_sha256'],'Case validation changed')
        verify_export(dest/(row['study_id'].split(':')[-1]+'.nii.gz'),record,
            expected_sha256=row['export']['sha256'],expected_foreground=row['export']['foreground'])
    for stage in ('profile','recover'):
        s=json.loads((dest/(stage+'-supervisor.json')).read_bytes())
        require(s['exit_code']==0 and s['reason'] is None and s['peak_worker_rss']<=LIMITS['rss_bytes'],'Failed process')



def reconcile(dest):
    check_pilot()
    previous=json.loads((PILOT/'profile.json').read_bytes())
    current=json.loads((dest/'profile.json').read_bytes())
    binding=json.loads((dest/'inputs.json').read_bytes())
    expected=cases(binding)
    require([{k:r[k] for k in ('role','index','study_id')} for r in previous['cases']]==pilot.CASES,'Pilot case evidence differs')
    require([{k:r[k] for k in ('role','index','study_id')} for r in current['cases']]==expected,'Continuation case evidence differs')
    rows=previous['cases']+current['cases']
    require(len(rows)==153 and len({r['study_id'] for r in rows})==153,'Full membership mismatch')
    require(previous['weights_sha256']==current['weights_sha256'],'Initial model differs across batches')
    record=dict(state='reconciled',pilot_receipt_sha256=PILOT_PIN,binding_sha256=BINDING_PIN,
        counts={role:sum(r['role']==role for r in rows) for role in ('optimizer','evaluator')},
        members=[{k:r[k] for k in ('role','index','study_id','transform_sha256')} for r in rows],
        weights_sha256=current['weights_sha256'],real_updates=0,raw_source_reads=0)
    put(dest/'aggregate.json',canonical(record))
    return record

def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--run',type=Path)
    p.add_argument('--worker',type=Path);p.add_argument('--pin');p.add_argument('--stage',choices=('profile','recover'))
    p.add_argument('--reference-pin');a=p.parse_args()
    if a.worker:return worker(a.worker,a.pin,a.stage,a.reference_pin)
    if a.prepare:return prepare()
    require(a.run is not None and a.pin is not None,'Explicit request and pin required');run(a.run,a.pin)

if __name__=='__main__':main()
