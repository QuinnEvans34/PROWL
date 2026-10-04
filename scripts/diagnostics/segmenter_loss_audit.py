"""D-329 single-use, training-only zero-update audit of consumed CAP-EXP-013 checkpoints."""
import argparse,gc,json,os,signal,subprocess,sys,time,shutil
from pathlib import Path
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','0')
os.environ.setdefault('OMP_NUM_THREADS','2'); os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_loss_audit_v1 as audit,segmenter_training_session_v1 as core
from scripts.diagnostics import segmenter_short_launch as c

ROOT=c.ROOT; PROFILE=ROOT/'SEGMENTER-LOSS-AUDIT-PROFILE-attempt02-20261003'
DEST=ROOT/'SEGMENTER-LOSS-AUDIT-attempt02-20261003'
PRODUCER_PIN='23cf88bd94122a3fe120eedaf8318aa48967bfd00cb1491f0cbf57c531866926'
REQUEST_PIN='eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9'
TRAIN=[f'pants:study:PanTS_{n:08d}' for n in (3,26,2232,2973,5821,6238)]
STEPS=[0,6,24,48]
LIMITS=dict(seconds=900,rss_bytes=12*1024**3,driver_bytes=12*1024**3,free_bytes=100*1024**3,output_bytes=32*1024**2,
            checkpoint_payload_bytes=4*(96*1024**2+2*1024**2),cache_closure_bytes=128*1024**2,consumed_pair_bytes=96*1024**2)
NEW=['src/training/segmenter_loss_audit_v1.py','scripts/diagnostics/segmenter_loss_audit.py','tests/test_segmenter_loss_audit.py']


def pins():return c.pins()|{n:digest((c.REPO/n).read_bytes()) for n in NEW}


def guard(d,start):
    torch.mps.synchronize()
    require(time.monotonic()-start<LIMITS['seconds'] and c.prior.rss()<=LIMITS['rss_bytes']
            and torch.mps.driver_allocated_memory()<=LIMITS['driver_bytes'],'Audit resource envelope')
    require(shutil.disk_usage(c.REPO).free>=LIMITS['free_bytes']
            and shutil.disk_usage('/Volumes/PROWL-Data').free>=LIMITS['free_bytes'],'Audit free space')
    c.prior.check_output(d,LIMITS['output_bytes'])


def sealed_batch(provider,control,sid):
    require(type(provider) in (c.data.QualifiedInputs,c.data.InventedInputs)
            and canonical(provider.control)==canonical(control) and sid in control['train']
            and sid not in control['validation'],'Audit protected provider/member mismatch')
    b=provider.get(sid,role='train',operation='optimizer')
    require(type(b) is c.data.Batch and b.role=='train','Audit requires sealed train batch')
    x,y=b.checked(digest(canonical(control)),'optimizer',sid)
    require(y is not None,'Audit target absent')
    return b,torch.as_tensor(x)[None],torch.as_tensor(y,dtype=torch.long)[None]


def deny_original_reads():
    def deny(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes)) and os.fsdecode(args[0]).endswith(('.nii','.nii.gz')):
            raise ValueError('Loss audit forbids original CT/target payload opens')
    sys.addaudithook(deny)


def profile():
    PROFILE.mkdir(); c.source.put(PROFILE/'consumed.json',dict(decision='D-329',domain='invented_arrays_only',source_pins=pins(),runtime=c.runtime(),limits=LIMITS))
    signal.alarm(LIMITS['seconds']);start=time.monotonic();torch.set_num_threads(2)
    provider=c.data.InventedInputs(144);model=audit.analysis_clone(core.scratch(core.config()),'mps'); rows=[];peak=0
    # Separate maximum-shape analytic/autograd logit check, one invented voxel-class array.
    _,_,y=sealed_batch(provider,provider.control,provider.control['train'][0]); y=y.to('mps')
    z=torch.zeros(1,3,144,144,144,device='mps',requires_grad=True)
    ce,di,p,gce,gdi,_=audit.terms(z,y);errs=[]
    for loss,g in [(ce,gce),(di,gdi)]:
        actual=torch.autograd.grad(loss,z,retain_graph=True)[0]
        err=float((actual-g).abs().max().detach().cpu());require(err<=1e-7,'MPS analytic gradient parity');errs.append(err)
    del z,y,ce,di,p,gce,gdi,actual,loss,g;gc.collect();torch.mps.empty_cache()
    for sid in provider.control['train']:
        b,x,y=sealed_batch(provider,provider.control,sid)
        row=audit.analyze(model,x.to('mps'),y.to('mps'));rows.append(dict(study_id=sid,**row));guard(PROFILE,start)
        peak=max(peak,torch.mps.driver_allocated_memory());del b,x,y;gc.collect();torch.mps.empty_cache()
    c.source.put(PROFILE/'result.json',dict(state='qualified',decision='D-329',domain='invented_arrays_only',rows=rows,
        seconds=time.monotonic()-start,peak_rss_bytes=c.prior.rss(),sampled_driver_peak_bytes=peak,
        model_forwards=6,head_vjp_queries=12,logit_oracle_vjp_queries=2,optimizer_calls=0,original_arrays=0,
        analytic_gradient_max_abs=errs,source_pins=pins(),runtime=c.runtime(),limits=LIMITS))
    signal.alarm(0);print(c.prior.package(PROFILE))


def parent():
    prod=c.source.verify_package(c.dest('real'),PRODUCER_PIN)
    r=c.checked('real',REQUEST_PIN)
    require(prod['state']=='producer_complete' and prod['request_sha256']==REQUEST_PIN
            and prod['source_pins']==c.pins(),'Parent producer changed')
    require([p['primary']['step'] for p in prod['transaction']['checkpoints']]==STEPS,'Parent cadence changed')
    control=json.loads(r['controls']['inputs.json'])
    require(control['train']==TRAIN and control['domain']=='qualified_real_cache'
            and control['original_arrays_read']==0 and control['jitter']=='none','Parent cohort control changed')
    return prod,r,control


def expected_request(profile_pin):
    pr=c.source.verify_package(PROFILE,profile_pin)
    require(pr['state']=='qualified' and pr['source_pins']==pins() and pr['runtime']==c.runtime()
            and pr['optimizer_calls']==0 and len(pr['rows'])==6,'Audit not qualified for sources/runtime')
    prod,r,control=parent()
    return dict(schema_version='1.0.0',task=audit.TASK,decision='D-329',source_pins=pins(),runtime=c.runtime(),
        parent_request_sha256=REQUEST_PIN,producer_receipt_sha256=PRODUCER_PIN,profile_receipt_sha256=profile_pin,
        identity=r['identity'],checkpoints=prod['transaction']['checkpoints'],inputs_control=control,
        storage_read_ceilings=r['storage_ceilings'],training_members=TRAIN,checkpoint_steps=STEPS,limits=LIMITS,
        model_forwards=24,head_vjp_queries=48,optimizer_calls=0,original_array_reads=0,
        validation_model_evaluations=0,head_parameters=list(audit.HEAD),loss_id=core.numerical.LOSS_V3,
        analysis_mode='eval_clone_head_only',continuation_allowed=False,output=str(DEST))


def request_pin(path):return digest(Path(path).read_bytes())


def prepare(profile_pin):
    r=expected_request(profile_pin);DEST.mkdir();c.source.put(DEST/'request.json',r);print(request_pin(DEST/'request.json'))


def checked(pin):
    raw=(DEST/'request.json').read_bytes();require(digest(raw)==pin,'Audit request changed');r=json.loads(raw)
    require(r==expected_request(r['profile_receipt_sha256']),'Audit source/runtime/scope drift')
    return r


def worker(pin):
    r=checked(pin);require(json.loads((DEST/'consumed.json').read_bytes())['request_sha256']==pin,'Missing single-use consumption')
    deny_original_reads();signal.alarm(LIMITS['seconds']);start=time.monotonic();torch.set_num_threads(2)
    rows=[];payload_bytes=0;consumed_pair_bytes=0;peak=0
    try:
        provider=c.data.resolve_qualified()
        require(canonical(provider.control)==canonical(r['inputs_control']),'Fresh input ancestry/control drift')
        cache_bytes=sum(map(len,provider._files.values()));require(cache_bytes<=LIMITS['cache_closure_bytes'],'Cache closure byte bound')
        ss=c.stores('real',ceilings=r['storage_read_ceilings']);guard(DEST,start)
        for pair in r['checkpoints']:
            ref=pair['primary'];files,receipt=ss[0].resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:core.validate_payload(f,r['identity']))
            payload_bytes+=sum(map(len,files.values()));require(payload_bytes<=LIMITS['checkpoint_payload_bytes'],'Checkpoint byte envelope')
            s=core.decode(files,r['identity']);require(s.step==ref['step'] and core.numerical.state_hash(s.model.state_dict())==pair['weights_sha256'],'Same-run checkpoint mismatch')
            # No optimizer is moved to MPS or called. Only this independent model clone is analyzed.
            state_before=core.numerical.cpu_tree(s.optimizer.state_dict());model=audit.analysis_clone(s.model,'mps')
            original_weights=core.numerical.state_hash(s.model.state_dict())
            for sid in TRAIN:
                b,x,y=sealed_batch(provider,r['inputs_control'],sid)
                n=x.numel()*x.element_size()+y.numel() # persisted target is uint8, not expanded long
                if ref['step']==0:consumed_pair_bytes+=n
                require(consumed_pair_bytes<=LIMITS['consumed_pair_bytes'],'Consumed cache pairs byte bound')
                row=audit.analyze(model,x.to('mps'),y.to('mps'))
                require(row['class_counts']==r['inputs_control']['target_metadata'][sid]['class_counts'],'Target counts changed')
                rows.append(dict(step=ref['step'],study_id=sid,batch_sha256=b.hashes(),weights_sha256=pair['weights_sha256'],**row))
                guard(DEST,start);peak=max(peak,torch.mps.driver_allocated_memory())
                c.source.put(DEST/f'row-{ref["step"]:02d}-{TRAIN.index(sid):02d}.json',rows[-1])
                del b,x,y;gc.collect();torch.mps.empty_cache()
            require(core.tree_exact(state_before,s.optimizer.state_dict()) and original_weights==core.numerical.state_hash(s.model.state_dict())
                    and s.step==ref['step'] and not s.dirty,'Original checkpoint transaction mutated')
            del model,s,files,state_before;gc.collect();torch.mps.empty_cache()
        require(len(rows)==24 and sum(v['model_forwards'] for v in rows)==24 and sum(v['head_vjp_queries'] for v in rows)==48,'Audit coverage/call counts differ')
        checked(pin);guard(DEST,start)
        c.source.put(DEST/'result.json',dict(state='complete',decision='D-329',request_sha256=pin,rows=rows,
            seconds=time.monotonic()-start,peak_rss_bytes=c.prior.rss(),sampled_driver_peak_bytes=peak,
            checkpoint_payload_bytes=payload_bytes,cache_closure_bytes=cache_bytes,consumed_pair_bytes=consumed_pair_bytes,
            model_forwards=24,head_vjp_queries=48,optimizer_calls=0,original_array_reads=0,validation_model_evaluations=0,
            checkpoint_transactions_unchanged=True,source_pins=pins(),runtime=c.runtime()))
    except BaseException as exc:
        c.source.put(DEST/'failure.json',dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),completed_rows=len(rows),seconds=time.monotonic()-start));raise
    finally:signal.alarm(0)


def supervise(pin):
    checked(pin);c.source.put(DEST/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry',authority='Quinton continue; D-329 read-only scope'))
    start=time.monotonic();peak=0
    cmd=[sys.executable,'-m','scripts.diagnostics.segmenter_loss_audit','--worker','--request-sha256',pin]
    with (DEST/'stdout.log').open('xb') as out,(DEST/'stderr.log').open('xb') as err:
        proc=subprocess.Popen(cmd,stdout=out,stderr=err)
        try:
            while proc.poll() is None:
                require(time.monotonic()-start<LIMITS['seconds'],'Supervised audit time cap')
                status=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                if status.stdout.strip():peak=max(peak,int(status.stdout.strip())*1024)
                require(peak<=LIMITS['rss_bytes'],'Supervised audit RSS cap');time.sleep(.5)
        except BaseException:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
        finally:
            c.source.put(DEST/'supervision.json',dict(exit_code=proc.poll(),seconds=time.monotonic()-start,sampled_peak_rss_bytes=peak))
    require(proc.returncode==0,'Audit worker failed; request consumed, inspect logs')
    print(c.prior.package(DEST))


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for n in ('profile','prepare','run','worker'):g.add_argument('--'+n,action='store_true')
    p.add_argument('--profile-sha256');p.add_argument('--request-sha256');a=p.parse_args()
    if a.profile:profile()
    elif a.prepare:prepare(a.profile_sha256)
    elif a.run:supervise(a.request_sha256)
    else:worker(a.request_sha256)
if __name__=='__main__':main()
