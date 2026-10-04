"""D-300 bounded single-use cache build; no optimizer/model API."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_smoke_run import capture,encoded,put,sha
from scripts.diagnostics.twomm_localizer_preprocessing import verify_resource,supervised_rehearsal
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
CAP=REPO/'docs/capstone/data/TWOMM-CACHE-INPUT-CAPABILITY-2026-09-30.json'
PLAN=REPO/'docs/capstone/operations/TWOMM-CACHE-BUILD-PLAN-2026-09-30.md'
RECIPE=REPO/'configs/capstone/localizer-preprocessing-v4.json'
BINDING=ROOT/'twomm-cache-readiness-20260930/proposed-binding.json'
BINDING_PIN='ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d'
LIMITS=dict(seconds=1200,rss=16*1024**3,output_bytes=4*1024**3+192*1024**2,internal_free=100*1024**3)


def subset(binding,cap,batch):
    result=deepcopy(binding)
    if batch!='assembly':
        ids=next(b['study_ids'] for b in cap['batches'] if b['batch_id']==batch)
        result['roles']={r:[e for e in es if e['descriptor']['study_id'] in ids] for r,es in result['roles'].items()}
    return result


def aggregate_guard(cap_pin):
    total=0
    for claim in ROOT.glob('twomm-cache-build-claim-'+cap_pin+'-*.json'):
        name=json.loads(claim.read_bytes())['result'];require(Path(name).name==name,'Unsafe claim')
        path=ROOT/name;require(path.resolve()==path,'Unsafe aggregate path')
        total+=sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
    require(total<=9*1024**3,'Aggregate cache output cap')
    return total


def result_checked(path,pin):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe result')
    raw=(path/'receipt.json').read_bytes();require(sha(raw)==pin,'Result receipt pin differs');r=json.loads(raw)
    require(r['state']=='complete','Incomplete result')
    for name,ref in r['files'].items():
        p=path/name;require(p.resolve().is_relative_to(path) and not p.is_symlink(),'Unsafe result member')
        b=p.read_bytes();require(len(b)==ref['bytes'] and sha(b)==ref['sha256'],'Result member differs')
    return json.loads((path/'results.json').read_bytes())


def checked_request(path,pin):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe request')
    raw=(path/'request.json').read_bytes();require(sha(raw)==pin,'Request pin differs');r=json.loads(raw)
    require(r['approval']=='D-300' and r['optimizer_updates']==0 and r['limits']==LIMITS and r['batch_id'] in ('pilot','remainder','assembly'),'Wrong request scope')
    require(set(r['files'])=={'source.json','environment.json','binding.json','capability.json','recipe.json','plan.md','resource.json','targets.json'},'Wrong controls')
    for n,p in r['files'].items():require(sha((path/n).read_bytes())==p,'Changed control')
    require(r['files']['binding.json']==BINDING_PIN,'Wrong full binding')
    source,env=capture();require(source==(path/'source.json').read_bytes() and env==(path/'environment.json').read_bytes(),'Code/environment changed')
    verify_resource((path/'resource.json').read_bytes(),r['files']['resource.json'])
    if r['batch_id']=='pilot':require(r['shards']==[],'Pilot cannot reuse shards')
    else:
        require([x['batch_id'] for x in r['shards']]==(['pilot'] if r['batch_id']=='remainder' else ['pilot','remainder']),'Prior evidence missing')
        for s in r['shards']:
            v=result_checked(Path(s['path']),s['pin']);require(v['batch_id']==s['batch_id'] and v['state']=='passed' and v['capability_sha256']==r['files']['capability.json'] and v['full_binding_sha256']==BINDING_PIN,'Prior evidence scope differs')
    return r


def prepare(batch,resource,resource_pin,shards):
    require(batch in ('pilot','remainder','assembly'),'Unknown batch');raw=BINDING.read_bytes();require(sha(raw)==BINDING_PIN,'Binding changed')
    prior=ROOT/'twomm-preprocessing-review-20260930';review=(prior/'receipt.json').read_bytes()
    require(sha(review)=='086fa4216633900a7e100840693803d974aaf05398bfbc80f262ec705d03e657','Prior review differs')
    reports=(prior/'inspection-progress.json').read_bytes();require(sha(reports)==json.loads(review)['files']['inspection-progress.json']['sha256'],'Prior reports differ')
    targets={c['study_id']:c['processed_foreground'] for b in json.loads(reports) for c in b['cases']}
    payload=resource.read_bytes();verify_resource(payload,resource_pin);source,env=capture();p=ROOT/('twomm-cache-request-'+str(uuid4()));p.mkdir()
    files={'source.json':source,'environment.json':env,'binding.json':raw,'capability.json':CAP.read_bytes(),'recipe.json':RECIPE.read_bytes(),'plan.md':PLAN.read_bytes(),'resource.json':payload,'targets.json':encoded(targets)}
    for n,b in files.items():put(p/n,b)
    req=dict(approval='D-300',optimizer_updates=0,batch_id=batch,limits=LIMITS,files={n:sha(b) for n,b in files.items()},shards=shards)
    put(p/'request.json',encoded(req));pin=sha((p/'request.json').read_bytes());checked_request(p,pin)
    print(json.dumps(dict(path=str(p),pin=pin)),flush=True)


def worker(dest,request,pin):
    import torch
    from src.training.twomm_cache import publish,DiskRoleCache
    from src.training.twomm_adapter import pad_image,remove_padding,patch_batch
    from src.data.manifest_records import canonical,digest
    from scripts.diagnostics.localizer_content_verify import peak_rss
    torch.set_num_threads(2);req=checked_request(request,pin);start=time.monotonic()
    def guard():
        aggregate_guard(req['files']['capability.json'])
        require(time.monotonic()-start<LIMITS['seconds'] and peak_rss()<=LIMITS['rss'],'Worker time/RSS cap')
        require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Free-space floor')
    full=json.loads((request/'binding.json').read_bytes());cap=json.loads((request/'capability.json').read_bytes());binding=subset(full,cap,req['batch_id']);bp=digest(canonical(binding));budget=None
    if req['batch_id']!='assembly':
        from src.data.twomm_cache_inputs import open_expanded_inputs
        ds,budget=open_expanded_inputs(repo=REPO,capability_bytes=(request/'capability.json').read_bytes(),trusted_capability_sha256=req['files']['capability.json'],recipe_bytes=(request/'recipe.json').read_bytes(),trusted_recipe_sha256=req['files']['recipe.json'],batch_id=req['batch_id'],tick=guard)
    else:
        caches=[]
        for s in req['shards']:
            path=Path(s['path']);v=result_checked(path,s['pin']);sb=subset(full,cap,s['batch_id']);caches.append(DiskRoleCache(path/'cache',v['cache_receipt_sha256'],sb,digest(canonical(sb))))
        class ShardDataset:
            def __init__(self,role):self.role=role;self.recipe=deepcopy(full['recipe']);self.entries=full['roles'][role]
            def __len__(self):return len(self.entries)
            def descriptor(self,i):return deepcopy(self.entries[i]['descriptor'])
            def load(self,i,*,operation):
                require(operation==self.role,'Wrong assembly role');sid=self.descriptor(i)['study_id']
                matches=[(c,c.members(operation).index(sid)) for c in caches if sid in c.members(operation)];require(len(matches)==1,'Missing/duplicate shard member')
                c,j=matches[0];x=c.get(operation,j);x['provenance']={'descriptor':x['descriptor']};return x
        ds={r:ShardDataset(r) for r in full['roles']}
    print(json.dumps(dict(state='inputs_verified',batch=req['batch_id'])),flush=True)
    cp=dest/'cache';cp.mkdir();beg=time.monotonic();cachepin=publish(cp,ds,binding,bp,guard=guard);build_seconds=time.monotonic()-beg
    if budget:require(budget.files==len(budget.expected) and budget.compressed==budget.compressed_cap and budget.expanded==budget.expanded_cap,'Incomplete source reads')
    beg=time.monotonic();cache=DiskRoleCache(cp,cachepin,binding,bp);open_seconds=time.monotonic()-beg
    config=dict(schema_version='twomm-adapter-1',patch_size=[144]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=4,loss_id='balanced_ce_dice_v1')
    checks=[];timings=[]
    expected_targets=json.loads((request/'targets.json').read_bytes())
    for role in full['roles']:
        for i,sid in enumerate(cache.members(role)):
            item=cache.get(role,i);require(int(item['label'].sum())==expected_targets[sid],'Retained target count differs');guard()
    del item
    print(json.dumps(dict(state='cache_reopened_targets_verified',batch=req['batch_id'])),flush=True)
    # Read one entry per role twice, while full constructor already verifies every array.
    for role in full['roles']:
        for repeat in range(2):
            beg=time.monotonic();item=cache.get(role,0);timings.append(dict(role=role,repeat=repeat,seconds=time.monotonic()-beg))
        padded,trace=pad_image(item['image'],config);require(torch.equal(remove_padding(padded,trace),item['image']),'Padding mismatch')
        if role=='optimizer':
            a,b,t=patch_batch(item,config,step=0);aa,bb,tt=patch_batch(item,config,step=0);require(torch.equal(a,aa) and torch.equal(b,bb) and t==tt,'Crop replay differs')
        else:
            refused=False
            try:patch_batch(item,config,step=0)
            except ValueError:refused=True
            require(refused,'Validation reached sampler')
        checks.append(role);guard()
    if req['batch_id']=='assembly':
        final=json.loads((cp/'complete.json').read_bytes());old={}
        for c in caches:
            for e in c._manifest['entries']:old[e['study_id']]={k:v['sha256'] for k,v in e['files'].items()}
        require(all(old[e['study_id']]=={k:v['sha256'] for k,v in e['files'].items()} for e in final['entries']),'Assembly changed serialized arrays')
    checked_request(request,pin);guard()
    put(dest/'results.json',encoded(dict(state='passed',batch_id=req['batch_id'],full_binding_sha256=BINDING_PIN,capability_sha256=req['files']['capability.json'],cache_receipt_sha256=cachepin,binding_sha256=bp,
        counts={r:len(cache.members(r)) for r in full['roles']},source_files=budget.files if budget else 0,source_bytes=budget.compressed if budget else 0,expanded_bytes=budget.expanded if budget else 0,
        cache_bytes=sum(p.stat().st_size for p in cp.iterdir()),build_seconds=build_seconds,verified_open_seconds=open_seconds,repeat_read_timings=timings,peak_rss=peak_rss(),elapsed_seconds=time.monotonic()-start,optimizer_updates=0)))


def run(request,pin):
    req=checked_request(request,pin);require('AC Power' in subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True),'AC power required');require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Internal free floor')
    dest=ROOT/('twomm-cache-build-'+str(uuid4()));dest.mkdir()
    put(ROOT/('twomm-cache-build-claim-'+req['files']['capability.json']+'-'+req['batch_id']+'.json'),encoded(dict(result=dest.name,request_sha256=pin)))
    for n in ('request.json',*req['files']):put(dest/n,(request/n).read_bytes())
    start=time.monotonic();peak=0;reason=None;proc=None;print(dest,flush=True)
    try:
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.twomm_cache_build','--worker',str(dest),'--request',str(request),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                aggregate_guard(req['files']['capability.json'])
                require('AC Power' in subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True),'AC power lost')
                require(time.monotonic()-start<=LIMITS['seconds'],'Supervisor time cap')
                require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Supervisor free floor')
                require(sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())<=LIMITS['output_bytes'],'Supervisor output cap')
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
    put(dest/'receipt.json',encoded(dict(state='complete',files={str(p.relative_to(dest)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.rglob('*') if p.is_file()},optimizer_updates=0)))
    print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',choices=['pilot','remainder','assembly']);p.add_argument('--resource',type=Path);p.add_argument('--resource-pin');p.add_argument('--shards',type=Path);p.add_argument('--rehearse',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--pin');p.add_argument('--worker',type=Path);a=p.parse_args()
    if a.rehearse:supervised_rehearsal()
    elif a.prepare:prepare(a.prepare,a.resource,a.resource_pin,json.loads(a.shards.read_bytes()) if a.shards else [])
    elif a.worker:worker(a.worker,a.request,a.pin)
    elif a.request and a.pin:run(a.request,a.pin)
    else:p.error('Choose fresh prepare/run or synthetic rehearsal')
