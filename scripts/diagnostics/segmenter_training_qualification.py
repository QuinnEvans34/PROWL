"""D-326 CPU/MPS transaction qualification and cold independent recovery; zero real updates."""
import argparse,gc,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','0');os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as data,segmenter_cache_v1 as cache
from src.training import segmenter_training_session_v1 as core,segmenter_training_probe_v1 as probes
from src.operations.segmenter_training_storage_v1 import run_stores
from src.operations.segmenter_training_backup_v1 import backup_checkpoint,restore_backup
from src.operations.segmenter_primary_read_guard_v1 import install as block_primary
from scripts.diagnostics import segmenter_source_verification as source,segmenter_content_pilot as prior,segmenter_checkpoint_inventory as inventory
from scripts.diagnostics.localizer_context_profile import power
REPO=source.REPO;ROOT=REPO/'outputs/prowl';BUDGET=ROOT/'SEGMENTER-TRAINING-READINESS-BUDGET-20261002.json'
CAP=REPO/'docs/capstone/operations/SEGMENTER-TRAINING-READINESS-STORAGE-CAPABILITY-2026-10-02.json';CAP_PIN='744265148211cd499898ea6ff9f7d8a60024030859ec7d2daec241e91f02a420'
INVENTORY_PIN='edef069e1017ba6a7c5d3ff667844f12684b246712cb0c9ec6a35c87a3e30689'
BASELINE=ROOT/'SEGMENTER-NATIVE-SCORE-REVIEW-20261002/accepted-native-baseline.json';BASELINE_PIN='f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2'
CODE=['src/data/segmenter_training_inputs_v1.py','src/training/segmenter_training_session_v1.py','src/training/segmenter_training_probe_v1.py','src/operations/segmenter_training_storage_v1.py','src/operations/segmenter_training_backup_v1.py','scripts/diagnostics/segmenter_checkpoint_inventory.py','scripts/diagnostics/segmenter_training_qualification.py','tests/test_segmenter_training_transaction.py','tests/test_segmenter_checkpoint_inventory.py','tests/test_segmenter_training_probe.py','tests/test_segmenter_training_backup.py',str(CAP.relative_to(REPO))]
CPU=dict(seconds=600,rss_bytes=6*1024**3,driver_bytes=0,output_bytes=64*1024**2,free_bytes=100*1024**3)
MPS=dict(seconds=1200,rss_bytes=12*1024**3,driver_bytes=12*1024**3,output_bytes=64*1024**2,free_bytes=100*1024**3)


def dest(stage):require(stage in ('cpu','mps','bridge'),'Unknown qualification stage');return ROOT/('SEGMENTER-TRAINING-'+stage.upper()+'-20261002')
def pins():
    raw=BASELINE.read_bytes();require(digest(raw)==BASELINE_PIN,'Accepted native baseline changed');fixed=json.loads(raw)['source_pins'];require(all(digest((REPO/n).read_bytes())==h for n,h in fixed.items()),'D-319–325 producing source changed');require(digest(CAP.read_bytes())==CAP_PIN,'Qualification cap changed');return fixed|{n:digest((REPO/n).read_bytes()) for n in CODE}
def runtime():return source.runtime()|dict(torch=torch.__version__,monai=__import__('monai').__version__,scipy=__import__('scipy').__version__,threads=2,mps_fallback='0')
def context():
    inv=source.verify_package(inventory.DEST,INVENTORY_PIN);require(inv['state']=='complete_byte_inventory_no_model_decode' and len(inv['files'])==203 and inv['model_deserializations']==0,'Historical inventory incomplete')
    return {'source.json':canonical(pins()),'environment.json':canonical(runtime()),'geometry.json':canonical(dict(baseline_sha256=BASELINE_PIN,geometry='provided_pancreas_ROI_zero_jitter',qualification_domain='invented_arrays_only')),'lineage.json':canonical(dict(checkpoint_inventory_sha256=INVENTORY_PIN,checkpoint_count=203,known_import_sha256=sorted({r['sha256'] for r in inv['files']}),weight_imports_allowed=False,teacher_models=[],selected_import_sha256=None))}
def stores(create=False,recovery=False,ceilings=None):
    ss=run_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=create,recovery_only=recovery)
    if ceilings:
        for s,c in zip(ss,ceilings):
            if s:s.quota_bytes=min(s.quota_bytes,c)
    return ss

def prepare(stage):
    require(stage in ('cpu','mps','bridge'),'Wrong stage');pins()
    if not BUDGET.exists():ss=stores(create=True);source.put(BUDGET,dict(decision='D-326',capability_sha256=CAP_PIN,ceilings=[s.quota_bytes for s in ss]))
    b=json.loads(BUDGET.read_bytes());require(b['decision']=='D-326' and b['capability_sha256']==CAP_PIN,'Frozen budget changed')
    r=dict(decision='D-326',stage=stage,source_pins=pins(),runtime=runtime(),limits=MPS if stage=='mps' else CPU,storage_capability_sha256=CAP_PIN,storage_ceilings=b['ceilings'],original_arrays_allowed=False,real_updates_allowed=False,output=str(dest(stage)))
    if stage!='bridge':
        provider=data.InventedInputs(24 if stage=='cpu' else 144);i,controls=core.make_identity(core.config(size=provider.size,steps=6 if stage=='cpu' else 4),provider,context(),run_id='segmenter-training-'+stage+'-D326',device=stage if stage=='cpu' else 'mps');r|=dict(identity=i,controls={n:v.decode() for n,v in controls.items()})
    d=dest(stage);d.mkdir();(d/'request.json').open('xb').write(canonical(r));print(digest(canonical(r)))

def checked(stage,pin):
    d=dest(stage);raw=(d/'request.json').read_bytes();require(digest(raw)==pin,'Qualification request changed');r=json.loads(raw);require(r['decision']=='D-326' and r['stage']==stage and r['source_pins']==pins() and r['runtime']==runtime() and r['limits']==(MPS if stage=='mps' else CPU) and r['storage_ceilings']==json.loads(BUDGET.read_bytes())['ceilings'] and r['storage_capability_sha256']==CAP_PIN and r['original_arrays_allowed'] is False and r['real_updates_allowed'] is False and r['output']==str(d),'Qualification/code/runtime envelope drift')
    if stage!='bridge':
        controls={n:v.encode() for n,v in r['controls'].items()};require(all(controls[n]==v for n,v in context().items()),'Lineage context changed');core.validate_controls(r['identity'],controls)
    return r

def guard(d,start,limits):
    require(time.monotonic()-start<limits['seconds'] and prior.rss()<=limits['rss_bytes'] and shutil.disk_usage(REPO).free>=limits['free_bytes'],'Worker resources/free space');prior.check_output(d,limits['output_bytes'])
    if limits['driver_bytes']:
        torch.mps.synchronize();require(torch.mps.driver_allocated_memory()<=limits['driver_bytes'] and power()[0],'MPS driver/power ceiling')

def save(primary,backup,s):
    ref=core.publish_checkpoint(primary,s);cap=json.loads(CAP.read_bytes());back=backup_checkpoint(primary,backup,ref,s.identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid']);return dict(primary=ref,backup=back)

def publish_probes(primary,backup,files,identity):
    probes.validate(files,identity);aid=identity['run_id']+':probes';derivation=digest(canonical(dict(identity=identity,stage='transaction_probes')));meta=dict(artifact_type='segmenter-training-probes',schema_version='1.0.0',component=core.TASK,code_sha256=identity['source_sha256'],parents=[identity['inputs_sha256']],retention='required_transaction_probe_keeper',sensitivity='synthetic',run_id=identity['run_id'],stage_id='probe')
    pin,status=primary.publish(aid,derivation_sha256=derivation,files=files,metadata=meta,validate=lambda f:probes.validate(f,identity));ref=dict(artifact_id=aid,receipt_sha256=pin,derivation_sha256=derivation);cap=json.loads(CAP.read_bytes());back=backup_checkpoint(primary,backup,ref,identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid'],validator=probes.validate);return dict(primary=ref,backup=back,bytes=sum(map(len,files.values())),members=len(files))

def worker(stage,pin):
    r=checked(stage,pin);d=dest(stage);source.put(d/'worker-consumed.json',dict(request_sha256=pin));start=time.monotonic();signal.alarm(r['limits']['seconds']);tick=lambda:guard(d,start,r['limits']);torch.set_num_threads(2);calls=0;memory=[]
    try:
        if stage=='bridge':
            provider=data.resolve_qualified();tick();rows=[]
            for role,key in [('train','train'),('validation','validation')]:
                for name in provider.control[key]:
                    op='optimizer' if role=='train' else 'evaluator';b=provider.get(name,role=role,operation=op);x,y=b.checked(digest(canonical(provider.control)),op,name);inf=provider.get(name,role=role,operation='inference');require(inf.target is None and np.array_equal(inf.image,x),'Train/inference image parity');rows.append(dict(study_id=name,role=role,operation=op,hashes=b.hashes(),target_counts=np.bincount(y.ravel(),minlength=3).tolist()));tick()
            ctx=context();ctx['geometry.json']=canonical(dict(baseline_sha256=BASELINE_PIN,geometry_acceptance_sha256=provider.control['geometry_acceptance_sha256'],roi_source='provided_pancreas_reference',jitter='none'));identity,ctrl=core.make_identity(core.config(),provider,ctx,run_id='segmenter-training-real-ready-D326',device='cpu');s=core.Session(identity,ctrl)
            try:s.update(provider);raise AssertionError('Real update gate open')
            except ValueError:pass
            require(s.step==0 and not s.dirty and core.numerical.state_hash(s.model.state_dict())==core.INITIAL,'Real readiness mutated scratch');source.put(d/'result.json',dict(state='qualified_cache_optimizer_boundary_no_updates',decision='D-326',cases=rows,control=provider.control,identity=identity,initial_weights_sha256=core.INITIAL,real_updates_denied=True,source_arrays_read=0,model_forwards=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),source_pins=pins(),runtime=runtime()));return
        provider=data.InventedInputs(24 if stage=='cpu' else 144);identity=r['identity'];controls={n:v.encode() for n,v in r['controls'].items()};s=core.Session(identity,controls);ss=stores(ceilings=r['storage_ceilings']);refs=[];prob={};probe_x=provider.get('invented-train-1',role='train',operation='inference').image;steps=[0,2,3,6] if stage=='cpu' else [0,2,3];dur=[]
        if stage=='mps':torch.mps.set_per_process_memory_fraction(min(1.,MPS['driver_bytes']/torch.mps.recommended_max_memory()))
        def measure(name):
            tick();memory.append(dict(stage=name,rss_bytes=prior.rss(),driver_bytes=torch.mps.driver_allocated_memory() if stage=='mps' else 0))
        def checkpoint():refs.append(save(ss[0],ss[1],s));prob[s.step]=s.predict(probe_x);measure('checkpoint_'+str(s.step))
        s.evaluate(provider);checkpoint()
        for _ in range(2):
            before=time.monotonic();s.update(provider);calls+=1;dur.append(time.monotonic()-before);measure('update_'+str(s.step))
        s.evaluate(provider);checkpoint();s.update(provider);calls+=1;next_weights=probes.encode_weights(s.model);next_weight_hash=core.numerical.state_hash(s.model.state_dict());checkpoint();saved=core.payload(s);old=s.optimizer.step
        def fail():old();raise RuntimeError('injected after optimizer mutation')
        s.optimizer.step=fail
        try:s.update(provider);raise AssertionError('Fault did not occur')
        except RuntimeError:calls+=1
        require(s.dirty and s.step==3,'Dirty update committed');denied=0
        for f in (lambda:s.update(provider),lambda:core.payload(s),lambda:s.predict(probe_x)):
            try:f()
            except ValueError:denied+=1
        require(denied==3,'Dirty state reused');s=core.resume(ss[0],refs[-1]['primary'],identity);measure('dirty_reload')
        if stage=='cpu':
            while s.step<6:s.update(provider);calls+=1
            s.evaluate(provider);checkpoint();clean=core.Session(identity,controls);clean.evaluate(provider)
            for _ in range(6):
                clean.update(provider);calls+=1
                if clean.step in (2,6):clean.evaluate(provider)
            require(core.progress(s)==core.progress(clean) and core.numerical.state_hash(s.model.state_dict())==core.numerical.state_hash(clean.model.state_dict()) and torch.equal(s.cpu_rng,clean.cpu_rng) and core.tree_exact(s.optimizer.state_dict(),clean.optimizer.state_dict()),'CPU interrupted/uninterrupted replay differs');del clean
        else:require(calls==4,'MPS optimizer-call envelope')
        probe_files={'image.npy':cache.encode(probe_x),'next-weights.pt':next_weights}|{f'prob-{n}.npy':cache.encode(prob[n]) for n in steps};case=None;score=None
        if stage=='mps':case=probes.native_case(probe_x);mask,report=probes.inverse.export(prob[2],case,tick=tick);probe_files['native-2.npy']=cache.encode(mask);score=probes.native_score(mask);del mask;measure('native_reference_score')
        manifest=dict(task=core.TASK,identity_sha256=digest(canonical(identity)),steps=steps,checkpoints=refs,next_weights_sha256=next_weight_hash,native_case=case,native_score=score);probe_files['manifest.json']=canonical(manifest);pr=publish_probes(ss[0],ss[1],probe_files,identity);measure('protected_probes')
        source.put(d/'result.json',dict(state='synthetic_transaction_qualified',decision='D-326',stage=stage,request_sha256=pin,checkpoints=refs,probes=pr,committed_steps=s.step,optimizer_calls=calls,dirty_transaction_refused=True,cpu_uninterrupted_exact=stage=='cpu',update_seconds=dur,exposure=core.progress(s)['exposure'],memory=memory,source_arrays_read=0,real_model_updates=0,initial_weights_sha256=core.INITIAL,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),source_pins=pins(),runtime=runtime()));signal.alarm(0)
    except BaseException as e:source.put(d/'worker-failure.json',dict(state='consumed_incomplete',error=str(e),optimizer_calls=calls,source_arrays_read=0,real_model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss()));raise
    finally:signal.alarm(0)

def recover_worker(stage,pin):
    r=checked(stage,pin);d=ROOT/(dest(stage).name+'-RECOVERY');source.put(d/'worker-consumed.json',dict(request_sha256=pin));block_primary()
    denied=False
    with source.directory('/Volumes') as fd:
        try:os.open('PROWL-Data',os.O_RDONLY|os.O_DIRECTORY,dir_fd=fd)
        except ValueError:denied=True
    require(denied,'Primary component-read guard inactive');start=time.monotonic();signal.alarm(r['limits']['seconds']);torch.set_num_threads(2);tick=lambda:guard(d,start,r['limits']);identity=r['identity'];saved=json.loads((dest(stage)/'result.json').read_bytes());ss=stores(recovery=True,ceilings=r['storage_ceilings']);probe_ref=saved['probes'];pf,pref=restore_backup(ss[1],ss[2],probe_ref['backup'],probe_ref['primary'],identity,validator=probes.validate);probes.validate(pf,identity);size=identity['config']['tensor_shape'][0];image=probes.inverse.decode_array(pf['image.npy'],[1,size,size,size],'float32');restores=[];selected=None;deltas=[]
    for pair in saved['checkpoints']:
        files,ref=restore_backup(ss[1],ss[2],pair['backup'],pair['primary'],identity);s=core.restore_payload(files,identity);p=s.predict(image);expected=probes.inverse.decode_array(pf[f'prob-{s.step}.npy'],[3,size,size,size],'float32');delta=float(np.max(np.abs(p-expected)));require(delta<=(0 if stage=='cpu' else 1e-6),'Cold probability replay differs');deltas.append(delta);restores.append(dict(step=s.step,reference=ref,members=len(files),bytes=sum(map(len,files.values())),validation=core.validate_payload(files,identity)))
        if s.step==2:selected=s
        else:del s
        tick()
    require(selected is not None,'No step2 keeper');p=selected.predict(image)
    if stage=='mps':mask,_=probes.inverse.export(p,probes.native_case(image),tick=tick);require(cache.encode(mask)==pf['native-2.npy'] and probes.native_score(mask)==json.loads(pf['manifest.json'])['native_score'],'Cold native evaluation differs');del mask
    provider=data.InventedInputs(size);row=selected.update(provider);expected=torch.load(probes.BytesIO(pf['next-weights.pt']),map_location='cpu',weights_only=True);wd=max(float((v.detach().cpu()-expected[n]).abs().max()) for n,v in selected.model.state_dict().items());require(wd<=(0 if stage=='cpu' else 1e-6),'Next-update weights differ');tick()
    source.put(d/'result.json',dict(state='passed',decision='D-326',stage=stage,restores=restores,probe_restore=pref,probe_members=len(pf),probe_bytes=sum(map(len,pf.values())),primary_reads_blocked=True,probability_max_difference=max(deltas),next_weight_max_difference=wd,next_member=row['member_id'],native_replay_exact=stage=='mps',source_arrays_read=0,real_model_updates=0,optimizer_calls=1,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),source_pins=pins(),runtime=runtime()));signal.alarm(0)

def supervise(stage,pin,recover=False):
    r=checked(stage,pin);d=dest(stage) if not recover else ROOT/(dest(stage).name+'-RECOVERY')
    if recover:d.mkdir()
    source.put(d/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry'));cmd=[sys.executable,'-m','scripts.diagnostics.segmenter_training_qualification','--recovery-worker' if recover else '--worker','--stage',stage,'--request-sha256',pin];start=time.monotonic();peak=0;p=None
    try:
        with (d/'worker.log').open('xb') as log:
            p=subprocess.Popen(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            while p.poll() is None:
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(p.pid)],capture_output=True,text=True,timeout=5)
                if p.poll() is None:require(observed.returncode==0 and observed.stdout.strip(),'RSS monitor unavailable');peak=max(peak,int(observed.stdout.strip())*1024)
                require(time.monotonic()-start<r['limits']['seconds'] and peak<=r['limits']['rss_bytes'] and shutil.disk_usage(REPO).free>=r['limits']['free_bytes'] and (stage!='mps' or power()[0]),'Supervisor resource/power ceiling');time.sleep(.25)
            require(p.returncode==0,'Qualification worker exit '+str(p.returncode))
        checked(stage,pin);source.put(d/'supervision.json',dict(seconds=time.monotonic()-start,observed_peak_rss_bytes=peak,exit_code=p.returncode));print(prior.package(d))
    except BaseException as e:
        source.put(d/'failure.json',dict(state='consumed_incomplete',error=str(e),seconds=time.monotonic()-start));raise
    finally:
        if p is not None and p.poll() is None:
            p.terminate()
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','run','recover','worker','recovery-worker'):g.add_argument('--'+n,action='store_true')
    p.add_argument('--stage',required=True,choices=['cpu','mps','bridge']);p.add_argument('--request-sha256');a=p.parse_args()
    if a.prepare:prepare(a.stage)
    elif a.worker:worker(a.stage,a.request_sha256)
    elif a.recovery_worker:recover_worker(a.stage,a.request_sha256)
    else:supervise(a.stage,a.request_sha256,recover=a.recover)
