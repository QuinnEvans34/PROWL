"""D-324 one-shot step0 cache inference and independent native recovery."""
import argparse,fcntl,gc,json,os,shutil,signal,subprocess,sys,time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
import torch
from src.training import segmenter_inference_v1 as core
from src.data import segmenter_cache_v1 as cache,segmenter_geometry_v1 as geometry,segmenter_geometry_loader_v1 as loader
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require,content_hash
from src.operations.segmenter_inference_storage_v1 import inference_stores
from src.operations.segmenter_inference_backup_v1 import backup_checkpoint,restore_backup
from scripts.diagnostics import segmenter_cache_qualification as old,segmenter_source_verification as source,segmenter_content_pilot as prior
from scripts.diagnostics.localizer_context_profile import power
REPO=source.REPO;ROOT=REPO/'outputs/prowl'
PROFILE=ROOT/'SEGMENTER-INFERENCE-SYNTHETIC-20261002';DEST=ROOT/'SEGMENTER-INFERENCE-REAL-20261002';RECOVERY=ROOT/'SEGMENTER-INFERENCE-RECOVERY-20261002';BUDGET=ROOT/'SEGMENTER-INFERENCE-BUDGET-20261002.json'
CAP=REPO/'docs/capstone/operations/SEGMENTER-INFERENCE-STORAGE-CAPABILITY-2026-10-02.json'
CAP_PIN='35ccc397c163b91b5e4f4accedf85653519d53534a996b24b81f3e29c702731f'
ACCEPT=ROOT/'SEGMENTER-CACHE-REVIEW-20261002/accepted-cache.json';ACCEPT_PIN='8b21315b14e38a6f582964a274d430ce768af9fb8348c8858c9ece62221125f3'
COMPLETION='90b8cc94fec1dd68dc70ed03e6037635e566481bd8d2f4918d7d2cc3827983a6';BINDING='cdd7c7071cc70663d6f2779b1e9b68890995f85d60d1a9bd561b61918ec275b6';OLD_REQ='d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364'
LIMITS=dict(seconds=1200,rss_bytes=12*1024**3,driver_bytes=12*1024**3,output_bytes=1024**3,free_bytes=100*1024**3)
CODE=['src/training/segmenter_inference_v1.py','src/operations/segmenter_inference_storage_v1.py','src/operations/segmenter_inference_backup_v1.py','scripts/diagnostics/segmenter_inference_qualification.py','tests/test_segmenter_inference.py','tests/test_segmenter_inference_transaction.py',str(CAP.relative_to(REPO))]


def pins():
    require(digest(CAP.read_bytes())==CAP_PIN,'Inference capability changed')
    require(digest(ACCEPT.read_bytes())==ACCEPT_PIN,'Cache acceptance changed')
    accepted=json.loads(ACCEPT.read_bytes());fixed=accepted['source_pins'];require(all(digest((REPO/n).read_bytes())==h for n,h in fixed.items()),'D-319–323 producing source changed')
    return fixed|{n:digest((REPO/n).read_bytes()) for n in CODE}


def runtime():return old.runtime()|dict(torch=torch.__version__,monai=__import__('monai').__version__,mps_fallback='0')


def stores(create=False,recovery=False,ceilings=None):
    sts=inference_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=create,recovery_only=recovery)
    if ceilings:
        for i,s in enumerate(sts):
            if s:s.quota_bytes=min(s.quota_bytes,ceilings[i])
    return sts


def budget():
    value=json.loads(BUDGET.read_bytes());require(value['capability_sha256']==CAP_PIN and value['decision']=='D-324','Wrong frozen storage budget');return value['ceilings']


def context(ancestry):return dict(source=pins(),environment=runtime(),ancestry=ancestry)


def cache_controls():
    req=old.checked_request(OLD_REQ);require(req['binding_sha256']==BINDING,'Wrong accepted cache binding')
    p=json.loads((old.DEST/'result.json').read_bytes());require(p['cache_completion_sha256']==COMPLETION,'Wrong cache receipt')
    entries=[]
    for e,row in zip(req['binding']['entries'],p['cases']):
        d=e['descriptor'];entries.append(dict(study_id=d['study_id'],protected_role=d['protected_role'],transform=e['transform'],transform_sha256=e['transform_sha256'],image_sha256=row['files']['image']['sha256']))
    return req,entries


def build_request(mode,profile_pin=None):
    require(mode in ('profile','real'),'Wrong request mode')
    if mode=='profile':
        t=geometry.plan_geometry([512,402,197],np.diag([.78,.78,1.25,1.]),[[100,110,0],[290,270,90]],geometry.recipe(),source_identity=dict(study_id='invented-largest',ct_sha256=digest(b'invented')),roi_origin='provided_pancreas_reference')
        cases=[dict(study_id='invented-largest',protected_role='train',transform=t,transform_sha256=content_hash(t),image_sha256=digest(core.array_bytes(np.full((1,144,144,144),.5,np.float32))))]
        ancestry=dict(domain='invented_arrays_only')
    else:
        p=source.verify_package(PROFILE,profile_pin);require(budget()==json.loads((PROFILE/'request.json').read_bytes())['storage_ceilings'],'Storage ceilings cannot reset after profile');require(p['state']=='passed' and p['code_pins']==pins() and p['runtime']==runtime() and p['model_updates']==p['source_arrays_read']==0,'Unqualified synthetic profile')
        _,cases=cache_controls();ancestry=dict(cache_completion_sha256=COMPLETION,cache_binding_sha256=BINDING,cache_request_sha256=OLD_REQ,cache_acceptance_sha256=ACCEPT_PIN,cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS)
    identity=core.make_identity(cases,context(ancestry),run_id='D-324-'+mode,domain='invented_profile' if mode=='profile' else 'qualified_cache')
    return dict(schema_version='segmenter-inference-request-1',decision='D-324',mode=mode,identity=identity,profile_receipt_sha256=profile_pin,capability_sha256=CAP_PIN,storage_ceilings=budget(),limits=LIMITS,output=str(PROFILE if mode=='profile' else DEST),model_updates_allowed=False,raw_source_reads_allowed=False,code_pins=pins(),runtime=runtime(),probe_tolerance=1e-6,native_mask_tolerance=0)


def checked(dest,pin):
    require(dest in (PROFILE,DEST) and dest.resolve(strict=True)==dest,'Unsafe inference output')
    raw=(dest/'request.json').read_bytes();require(digest(raw)==pin,'Request transport changed');r=json.loads(raw)
    require(r==build_request(r['mode'],r['profile_receipt_sha256']),'Request/scratch/code/runtime changed');return r


def prepare(mode,profile_pin=None):
    pins()
    if not BUDGET.exists():
        sts=stores(create=True);source.put(BUDGET,dict(decision='D-324',capability_sha256=CAP_PIN,ceilings=[s.quota_bytes for s in sts]))
    req=build_request(mode,profile_pin);dest=Path(req['output']);dest.mkdir();source.put(dest/'request.json',req)
    print(json.dumps(dict(request_sha256=digest((dest/'request.json').read_bytes()),mode=mode,limits=LIMITS)))


def bounded(dest,start):
    require(time.monotonic()-start<LIMITS['seconds'] and prior.rss()<=LIMITS['rss_bytes'],'Inference time/RSS ceiling')
    require(torch.mps.driver_allocated_memory()<=LIMITS['driver_bytes'],'Driver ceiling');require(shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Disk reserve')
    prior.check_output(dest,LIMITS['output_bytes'])


def audit_primary(event,args):
    if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        require(not os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'),'Primary reads forbidden in recovery')


def worker(dest,pin,recovery=False):
    req=checked(dest,pin);out=RECOVERY if recovery and dest==DEST else dest
    if recovery:
        require(json.loads((out/'recovery-consumed.json').read_bytes())['request_sha256']==pin,'No recovery parent claim');source.put(out/'recovery-worker-consumed.json',dict(request_sha256=pin))
        sys.addaudithook(audit_primary)
        # Prove the guard is active before restoring; no primary handle has been opened here.
        try:os.listdir('/Volumes/PROWL-Data');raise AssertionError('Primary audit guard failed')
        except ValueError:pass
    else:
        require(json.loads((dest/'consumed.json').read_bytes())['request_sha256']==pin,'No parent claim');source.put(dest/'worker-consumed.json',dict(request_sha256=pin))
    start=time.monotonic();signal.alarm(1200);torch.set_num_threads(2)
    require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS/fallback disabled required')
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    tick=lambda:bounded(out,start);memory=[]
    def measure(stage):tick();memory.append(dict(stage=stage,rss_bytes=prior.rss(),driver_bytes=torch.mps.driver_allocated_memory(),live_bytes=torch.mps.current_allocated_memory()))
    identity=req['identity'];sts=stores(recovery=recovery,ceilings=req['storage_ceilings'])
    if recovery:
        saved=json.loads((dest/'result.json').read_bytes());files,reference=restore_backup(sts[1],sts[2],saved['backup_reference'],saved['primary_reference'],identity)
        probe=core.recover_probe(files,identity,device='mps',tick=tick);measure('independent_recovered_probe')
        result=dict(state='passed',decision='D-324',mode=req['mode'],request_sha256=pin,restore_reference=reference,restored_members=len(files),restored_bytes=sum(map(len,files.values())),probe=probe,primary_reads_blocked=True,source_arrays_read=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),memory=memory,code_pins=pins(),runtime=runtime())
        source.put(out/('profile-recovery.json' if dest==PROFILE else 'result.json'),result)
    else:
        c=None
        if req['mode']=='real':
            registered=loader.resolve_registered();oldreq,_=cache_controls();require(registered.records==oldreq['binding']['records'],'Fresh registered ancestry differs');measure('registered_replay')
            files,_=old.store().resolve(oldreq['cache_artifact_id'],receipt_sha256=COMPLETION,expected_derivation=OLD_REQ,validate=lambda f:old.validate_production(f,oldreq,OLD_REQ));c=cache.InputCache(files,oldreq['binding'],BINDING);measure('accepted_cache_resolved')
        s=core.Session(identity,device='mps');exports=[];probe_x=None;probe_p=None;rows=[]
        for i,e in enumerate(identity['cases']):
            item=c.get(e['study_id'],role=e['protected_role'],operation='inference') if c else {k:v for k,v in e.items() if k!='image_sha256'}|dict(image=np.full((1,144,144,144),.5,np.float32))
            p=s.predict(item);measure('forward_'+str(i));a,r=core.export(p,e,tick=tick);measure('native_inverse_'+str(i));exports.append((a,r));rows.append(r)
            if i==0:probe_x=item['image'];probe_p=p
            print(json.dumps(dict(case=e['study_id'],native_counts=r['class_counts'])),flush=True);del item,p;gc.collect()
        if req['mode']=='profile':
            # Dense/wrong/empty/fragmented outcomes: no failure-oriented filtering.
            failures=[]
            for pattern in ('empty','dense_wrong','sparse','fragmented'):
                q=np.zeros((3,144,144,144),np.float32);q[0]=1
                if pattern=='dense_wrong':q[0]=0;q[2]=1
                elif pattern=='sparse':q[:,70:72,70:72,70:72]=0;q[2,70:72,70:72,70:72]=1
                elif pattern=='fragmented':q[:,::8,::8,::8]=0;q[2,::8,::8,::8]=1
                aa,rr=core.export(q,identity['cases'][0],tick=tick);failures.append(dict(pattern=pattern,class_counts=rr['class_counts'],native_voxels=aa.size));del aa,q;gc.collect();measure(pattern)
            source.put(dest/'failure-patterns.json',dict(patterns=failures))
        files=core.payload(s,probe_x,probe_p,exports);require(sum(map(len,files.values()))<512*1024**2,'Transaction member budget')
        artifact_id='segmenter-inference:D324:'+req['mode'];metadata=dict(artifact_type='segmenter-inference-checkpoint',schema_version='1.0.0',component=core.TASK,code_sha256=identity['source_sha256'],parents=[content_hash(identity['context']['ancestry'])],retention='required_step0_export_keeper',sensitivity='private_research',run_id=identity['run_id'],stage_id='step0_native_inference')
        receipt,status=sts[0].publish(artifact_id,derivation_sha256=pin,files=files,metadata=metadata,validate=lambda f:core.validate_payload(f,identity))
        reference=dict(artifact_id=artifact_id,receipt_sha256=receipt,derivation_sha256=pin);cap=json.loads(CAP.read_bytes())
        backup=backup_checkpoint(sts[0],sts[1],reference,identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid']);measure('complete_backed_up')
        require(pins()==req['code_pins'] and runtime()==req['runtime'],'End source/runtime drift')
        result=dict(state='passed',decision='D-324',mode=req['mode'],request_sha256=pin,primary_reference=reference,backup_reference=backup,members=len(files),artifact_bytes=sum(map(len,files.values())),cases=rows,initial_weight_sha256=identity['initial_weight_sha256'],terminal_weight_sha256=core.state_hash(s.model.state_dict()),source_arrays_read=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),memory=memory,code_pins=pins(),runtime=runtime())
        source.put(dest/'result.json',result)
    signal.alarm(0)


def supervise(dest,pin,recovery=False):
    req=checked(dest,pin);out=RECOVERY if recovery and dest==DEST else dest
    if recovery and dest==DEST:out.mkdir()
    if not recovery:source.put(dest/'consumed.json',dict(state='consumed_no_retry',request_sha256=pin))
    else:source.put(out/'recovery-consumed.json',dict(state='consumed_no_retry',request_sha256=pin))
    name='recovery' if recovery else 'producer';start=time.monotonic();peak=0
    try:
        with (out/(name+'.log')).open('xb') as log:
            env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1')
            cmd=[sys.executable,'-m','scripts.diagnostics.segmenter_inference_qualification','--worker','--mode',req['mode'],'--request-sha256',pin]+(['--recover'] if recovery else [])
            proc=subprocess.Popen(cmd,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                next_power=0
                while proc.poll() is None:
                    elapsed=time.monotonic()-start
                    if elapsed>=next_power:ac,_=power();require(ac,'AC power lost');next_power=elapsed+10
                    r=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                    if r.returncode==0 and r.stdout.strip():peak=max(peak,int(r.stdout.strip())*1024)
                    elif proc.poll() is None:raise RuntimeError('Memory monitor unavailable')
                    require(elapsed<LIMITS['seconds'] and peak<=LIMITS['rss_bytes'] and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Supervisor resource ceiling');time.sleep(.25)
                require(proc.returncode==0,'Worker exit '+str(proc.returncode))
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        source.put(out/(name+'-supervision.json'),dict(seconds=time.monotonic()-start,peak_rss_bytes=peak,exit_code=proc.returncode))
        if recovery:print(json.dumps(dict(receipt_sha256=prior.package(out),result=json.loads((out/('profile-recovery.json' if dest==PROFILE else 'result.json')).read_bytes()))))
    except BaseException as e:source.put(out/(name+'-failure.json'),dict(state='incomplete_consumed',error=str(e)));raise


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','run','worker'):g.add_argument('--'+n,action='store_true')
    p.add_argument('--mode',choices=('profile','real'),required=True);p.add_argument('--recover',action='store_true');p.add_argument('--profile-sha256');p.add_argument('--request-sha256');a=p.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Inference deadline')))
    torch.set_num_threads(2);dest=PROFILE if a.mode=='profile' else DEST
    if a.worker:worker(dest,a.request_sha256,a.recover);return
    ac,_=power();require(ac,'AC power required');fd=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.prepare:prepare(a.mode,a.profile_sha256)
        else:supervise(dest,a.request_sha256,a.recover)
    finally:os.close(fd)

if __name__=='__main__':main()
