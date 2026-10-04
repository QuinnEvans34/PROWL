"""D-332 conditional invented144 MPS/recovery; no real-input interface or launch."""
import argparse,fcntl,json,os,shutil,signal,subprocess,sys,time
from pathlib import Path
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','0')
import numpy as np
import torch
import yaml
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_geometry_v1 as g
from src.training import segmenter_lowrate_session_v1 as m
from src.operations.localizer_run_storage import tree_bytes,mounted_apfs
from src.operations.segmenter_primary_read_guard_v1 import install
from scripts.diagnostics.storage_setup import disk_info
from scripts.diagnostics.localizer_context_profile import power
from scripts.diagnostics.segmenter_source_verification import put,verify_package
from scripts.diagnostics import segmenter_lowrate_qualification_attempt02 as cpu
REPO=cpu.a.c.REPO;ROOT=cpu.ROOT;DEST=ROOT/'SEGMENTER-LOWRATE-MPS-20261003'
CPU_PIN='64b7ae4df8de1201881d73484839e6dad78a8040bd14b1e4609dabbcde0417ec'
REG_PIN='46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788'
CODE=['scripts/diagnostics/segmenter_lowrate_native_qualification.py','tests/test_segmenter_lowrate_native.py']
LIMITS=dict(seconds=600,rss_bytes=12*1024**3,driver_bytes=12*1024**3,local_bytes=8*1024**2,new_primary_bytes=256*1024**2,new_backup_bytes=320*1024**2,free_bytes=100*1024**3)


def pins():return cpu.pins()|{n:digest((REPO/n).read_bytes()) for n in CODE}


def qualified_cpu():
    r=verify_package(cpu.DEST,CPU_PIN);require(r['state']=='qualified' and r['gate']['passed'] and r['source_pins']==cpu.pins(),'CPU learning has not passed with fixed sources')
    p=ROOT/'SEGMENTER-LOWRATE-CPU-INDEPENDENT-PRESERVATION-20261003.json';proof=json.loads(p.read_bytes())
    require(proof['learning_passed'] and len(proof['cold_checkpoints'])==4 and proof['primary_python_reads_blocked'],'CPU independent preservation missing')
    raw=(Path(proof['destination'])/'manifest.json').read_bytes();require(digest(raw)==proof['manifest_sha256'],'CPU keeper manifest changed')
    return digest(p.read_bytes())


def registry():
    raw=(REPO/'configs/local/roots.yaml').read_bytes();require(digest(raw)==REG_PIN,'Registry changed');return yaml.safe_load(raw)


def domains(reg,recovery=False):
    roots=[Path(reg['roots'][name]['path']) for name in ('prowl_artifacts','prowl_backup')]
    ds=[reg['failure_domains'][name] for name in ('external_primary','internal_backup')]
    require(ds[0]['volume_uuid']=='22750B93-2F3F-499D-87F5-902981BFAB59' and ds[1]['volume_uuid']=='542E8B1F-8D50-4783-9250-752DFDC899CD','Registered domains changed')
    for index in ([1] if recovery else [0,1]):
        root=roots[index];mount=Path(ds[index]['mount_path']);info=disk_info(mount)
        mounted=mount.is_mount() or (index==1 and info.get('Internal') is True and mounted_apfs(info,mount,subprocess.check_output(['/sbin/mount'],text=True,timeout=5)))
        require(mounted and info.get('VolumeUUID')==ds[index]['volume_uuid'] and info.get('FilesystemType')=='apfs' and info.get('WritableVolume') is True and info.get('MountPoint')==str(mount),'Native APFS domain not qualified')
        require(root.resolve(strict=True)==root and root.is_dir() and root.stat().st_dev==mount.stat().st_dev,'Unsafe registered root')
        require(shutil.disk_usage(root).free>=LIMITS['free_bytes'],'Native free-space floor')
    if not recovery:require(roots[0].stat().st_dev!=roots[1].stat().st_dev,'Keeper shares primary physical device')
    return roots


def native_preflight():
    cpu.native_preflight();require(torch.backends.mps.is_available() and os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0','Native MPS without fallback required')
    ac,_=power();require(ac,'AC power required')


def request(cap):
    validate_cap(cap);preserved=qualified_cpu();context={'source.json':canonical(pins()),'environment.json':canonical(cpu.a.c.runtime()),'geometry.json':canonical(dict(domain='invented_native_probe_only',cpu_receipt_sha256=CPU_PIN))}
    i,controls=m.make_identity(m.config(size=144,steps=4,lr=.0003),context,run_id='segmenter-lowrate-synthetic-D332-MPS',device='mps')
    return dict(decision='D-332',stage='invented_mps_mechanics',identity=i,controls={n:v.decode() for n,v in controls.items()},source_pins=pins(),runtime=cpu.a.c.runtime(),limits=LIMITS,storage=cap,cpu_receipt_sha256=CPU_PIN,cpu_preservation_sha256=preserved,checkpoint_steps=[0,2,4],produce_optimizer_calls=5,recovery_optimizer_calls=1,dirty_calls=1,max_model_forwards=8,real_optimizer_calls=0,original_reads=0,real_inputs_allowed=False,automatic_launch_allowed=False)


def validate_cap(cap):
    reg=registry();p=Path(reg['roots']['prowl_artifacts']['path']);b=Path(reg['roots']['prowl_backup']['path']);proof=json.loads((ROOT/'SEGMENTER-LOWRATE-CPU-INDEPENDENT-PRESERVATION-20261003.json').read_bytes())
    base=proof['whole_root_after_bytes'];expected=dict(decision='D-332',registry_sha256=REG_PIN,primary_area=str(p/'segmenter-lowrate-D332-MPS-20261003'),backup_area=str(b/'segmenter-lowrate-D332-MPS-20261003'),backup_root=str(b),backup_baseline_bytes=base,absolute_backup_ceiling=min(base+LIMITS['new_backup_bytes'],14892449687,reg['roots']['prowl_backup']['cap_bytes']),maximum_new_primary_bytes=LIMITS['new_primary_bytes'],maximum_new_backup_bytes=LIMITS['new_backup_bytes'],primary_uuid='22750B93-2F3F-499D-87F5-902981BFAB59',backup_uuid='542E8B1F-8D50-4783-9250-752DFDC899CD',invented_only=True)
    require(cap==expected,'Native capability differs from registered roots/frozen CPU occupancy/prior ceiling')


def prepare():
    native_preflight();qualified_cpu();reg=registry();primary,backup=domains(reg)
    areas=[primary/'segmenter-lowrate-D332-MPS-20261003',backup/'segmenter-lowrate-D332-MPS-20261003']
    require(not DEST.exists() and all(not p.exists() for p in areas),'Fresh native destinations required')
    base=tree_bytes(backup);ceiling=min(base+LIMITS['new_backup_bytes'],14892449687,reg['roots']['prowl_backup']['cap_bytes'])
    require(ceiling-base>=LIMITS['new_backup_bytes'],'Insufficient preservation room; no cleanup or quota reset')
    cap=dict(decision='D-332',registry_sha256=REG_PIN,primary_area=str(areas[0]),backup_area=str(areas[1]),backup_root=str(backup),backup_baseline_bytes=base,absolute_backup_ceiling=ceiling,maximum_new_primary_bytes=LIMITS['new_primary_bytes'],maximum_new_backup_bytes=LIMITS['new_backup_bytes'],primary_uuid=reg['failure_domains']['external_primary']['volume_uuid'],backup_uuid=reg['failure_domains']['internal_backup']['volume_uuid'],invented_only=True)
    DEST.mkdir();put(DEST/'storage-capability.json',cap);r=request(cap);put(DEST/'request.json',r)
    for n in CODE:raw_write(DEST/('source--'+Path(n).name),(REPO/n).read_bytes())
    print(digest((DEST/'request.json').read_bytes()))


def checked(pin):
    raw=(DEST/'request.json').read_bytes();r=json.loads(raw);require(digest(raw)==pin and r==request(json.loads((DEST/'storage-capability.json').read_bytes())),'Native request/source/runtime/parent drift')
    return r


def raw_write(path,raw):
    require(path.parent.resolve(strict=True)==path.parent and Path(path.name).name==path.name,'Unsafe flat destination')
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())


def tensor_bytes(value):
    from io import BytesIO
    b=BytesIO();torch.save(value,b);return b.getvalue()


def load_tensor(raw):
    from io import BytesIO
    return torch.load(BytesIO(raw),weights_only=True,map_location='cpu')


def verify_flat(area,manifest,pin):
    raw=(area/'manifest.json').read_bytes();require(digest(raw)==pin and json.loads(raw)==manifest,'Native keeper manifest changed')
    require(set(manifest['files'])|{'manifest.json'}=={p.name for p in area.iterdir()},'Native keeper membership differs')
    for name,ref in manifest['files'].items():
        require(Path(name).name==name,'Unsafe keeper member');p=area/name;require(p.is_file() and not p.is_symlink(),'Unsafe keeper file')
        raw=p.read_bytes();require(len(raw)==ref['bytes'] and digest(raw)==ref['sha256'],'Keeper member differs')


def native_record():
    return g.plan_geometry([512,402,197],np.diag([.78,.78,1.25,1.]),[[100,120,0],[280,260,80]],g.recipe(),source_identity=dict(study_id='invented_D332_native_grid',ct_sha256=digest(b'no_original_CT')),roi_origin='provided_pancreas_reference')


def class_counts(pred,target):
    require(pred.shape==target.shape and pred.dtype==target.dtype==np.uint8 and np.isin(pred,[0,1,2]).all() and np.isin(target,[0,1,2]).all(),'Native invented score input differs')
    rows=[]
    for k in range(3):
        n=int((target==k).sum());v=int((pred==k).sum());tp=int(((pred==k)&(target==k)).sum());rows.append(dict(class_id=k,target_voxels=n,predicted_voxels=v,true_positive=tp,dice=2*tp/(n+v) if n else None,recall=tp/n if n else None))
    return rows


def native_probe(probability,tick):
    t=native_record();pin=digest(canonical(t));native=g.restore_probabilities(probability.numpy(),t,trusted_record_sha256=pin,tick=tick)
    mask=native.argmax(0).astype(np.uint8);prob_hash=digest(memoryview(native).cast('B'));del native
    _,codes=m.fixture('multiple',144);reference=g.restore_codes(codes.numpy().astype(np.uint8),t,trusted_record_sha256=pin,tick=tick)
    scores=class_counts(mask,reference);require(sum(x['predicted_voxels'] for x in scores)==mask.size,'Native class conservation differs')
    return mask,dict(domain='invented_inverse_target_mechanics_not_original_reference_or_learning',transform=t,transform_sha256=pin,probability_sha256=prob_hash,mask_sha256=digest(memoryview(mask).cast('B')),derived_reference_sha256=digest(memoryview(reference).cast('B')),shape=list(mask.shape),dtype='uint8',scores=scores)


def tick(start,r,recovery=False):
    torch.mps.synchronize();require(time.monotonic()-start<LIMITS['seconds'] and cpu.a.c.prior.rss()<=LIMITS['rss_bytes'] and torch.mps.driver_allocated_memory()<=LIMITS['driver_bytes'],'Native time/RSS/driver envelope')
    cap=r['storage'];backup=Path(cap['backup_area']);root=Path(cap['backup_root'])
    require(tree_bytes(root)<=cap['absolute_backup_ceiling'] and (not backup.exists() or tree_bytes(backup)<=cap['maximum_new_backup_bytes']),'Frozen backup capacity exceeded')
    if not recovery:
        area=Path(cap['primary_area']);require(not area.exists() or tree_bytes(area)<=cap['maximum_new_primary_bytes'],'Native primary capacity exceeded')
    require(shutil.disk_usage(REPO).free>=LIMITS['free_bytes'] and shutil.disk_usage(root).free>=LIMITS['free_bytes'],'Native free-space floor')
    require(tree_bytes(DEST)<=LIMITS['local_bytes'],'Local numeric evidence ceiling')


def restore_checkpoint(area,ref,identity):
    require(type(ref['step'])==int and ref['step'] in (0,2,4) and set(ref['payload'])==set(m.CONTROLS)|{'identity.json','progress.json','state.pt'},'Native checkpoint reference inventory differs')
    prefix=f"checkpoint{ref['step']}--";files={n:(area/(prefix+n)).read_bytes() for n in ref['payload']}
    require(all(digest(v)==ref['payload'][n]['sha256'] and len(v)==ref['payload'][n]['bytes'] for n,v in files.items()),'Checkpoint payload drift')
    s=m.restore_payload(files,identity);require(s.step==ref['step'] and m.state_hash(s.model.state_dict())==ref['weights_sha256'],'Recovered weights/step differ');return s


def worker(stage,pin):
    require(stage in ('produce','recover'),'Unknown native worker')
    if stage=='recover':install()
    r=checked(pin);native_preflight();reg=registry();domains(reg,recovery=stage=='recover')
    require(json.loads((DEST/(stage+'-consumed.json')).read_bytes())==dict(request_sha256=pin,stage=stage,state='consumed_no_retry'),'Native worker not dispatched')
    put(DEST/(stage+'-worker-started.json'),dict(stage=stage,request_sha256=pin,state='single_use_started'))
    torch.set_num_threads(2);torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()));signal.alarm(600);start=time.monotonic();memory=[]
    def measure(label):
        tick(start,r,stage=='recover');memory.append(dict(stage=label,rss_bytes=cpu.a.c.prior.rss(),driver_bytes=torch.mps.driver_allocated_memory(),live_bytes=torch.mps.current_allocated_memory()))
    primary=Path(r['storage']['primary_area']);backup=Path(r['storage']['backup_area']);i=r['identity']
    try:
        if stage=='produce':
            primary.mkdir(mode=0o700);backup.mkdir(mode=0o700);s=m.Session(i,{n:v.encode() for n,v in r['controls'].items()});refs=[];steps=[]
            def save():
                payload=m.payload(s);ref=dict(step=s.step,weights_sha256=m.state_hash(s.model.state_dict()),payload={n:dict(bytes=len(v),sha256=digest(v)) for n,v in payload.items()})
                for n,v in payload.items():raw_write(primary/(f'checkpoint{s.step}--'+n),v)
                refs.append(ref);measure('checkpoint'+str(s.step))
            save()
            for _ in range(2):
                t=time.monotonic();row=s.synthetic_update();measure('update'+str(s.step));steps.append(dict(row,seconds=time.monotonic()-t))
            save();probe=s.predict(m.fixture('multiple',144)[0]);measure('image-only-probe');raw_write(primary/'probe.pt',tensor_bytes(probe))
            mask,native=native_probe(probe,lambda:tick(start,r));raw_write(primary/'native-mask.npy',cpu.a.c.inverse.array_bytes(mask));del mask;measure('native-export-score')
            nextrow=s.synthetic_update();measure('update3');steps.append(nextrow);raw_write(primary/'next-weights.pt',tensor_bytes(m.cpu_tree(s.model.state_dict())))
            saved3=m.payload(s);s.synthetic_update();measure('update4');save();terminal_hash=m.state_hash(s.model.state_dict());del s
            dirty=m.restore_payload(saved3,i);before=m.state_hash(dirty.model.state_dict());method=dirty.optimizer.step
            def fault():method();raise RuntimeError('injected native post-optimizer mutation')
            dirty.optimizer.step=fault
            try:dirty.synthetic_update();raise AssertionError('Dirty fault did not throw')
            except RuntimeError as exc:require(str(exc)=='injected native post-optimizer mutation','Unexpected dirty fault')
            require(dirty.dirty and dirty.step==3 and m.state_hash(dirty.model.state_dict())!=before,'Dirty native optimizer did not mutate/refuse commit')
            denied=0
            for call in (dirty.synthetic_update,lambda:m.payload(dirty),lambda:dirty.predict(m.fixture('multiple',144)[0])):
                try:call()
                except ValueError:denied+=1
            require(denied==3,'Dirty inference/checkpoint/update not refused');del dirty,saved3;measure('dirty-refused')
            refs_record=dict(identity=i,checkpoints=refs,next_update=nextrow,native=native,terminal_weights_sha256=terminal_hash,optimizer_calls=5,committed_steps=4,dirty_optimizer_calls=1,dirty_refusals=denied,updates=steps)
            raw_write(primary/'references.json',canonical(refs_record));raw_write(primary/'request.json',(DEST/'request.json').read_bytes())
            for n in CODE:raw_write(primary/('source--'+Path(n).name),(REPO/n).read_bytes())
            inventory={p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in primary.iterdir()};manifest=dict(decision='D-332',state='complete_invented_native_payload',files=inventory)
            put(primary/'manifest.json',manifest);manifest_pin=digest((primary/'manifest.json').read_bytes())
            for name,ref in inventory.items():
                tick(start,r);raw= (primary/name).read_bytes();require(digest(raw)==ref['sha256'],'Primary changed during backup');raw_write(backup/name,raw)
            raw_write(backup/'manifest.json',(primary/'manifest.json').read_bytes());verify_flat(primary,manifest,manifest_pin);verify_flat(backup,manifest,manifest_pin);measure('independent-copy-verified')
            put(DEST/'produce-result.json',dict(state='passed',stage=stage,manifest_sha256=manifest_pin,files=len(inventory)+1,primary_bytes=tree_bytes(primary),backup_bytes=tree_bytes(backup),checkpoints=[x['step'] for x in refs],optimizer_calls=5,real_optimizer_calls=0,original_reads=0,seconds=time.monotonic()-start,peak_rss_bytes=cpu.a.c.prior.rss(),memory=memory))
        else:
            producer=json.loads((DEST/'produce-result.json').read_bytes());manifest=json.loads((backup/'manifest.json').read_bytes());verify_flat(backup,manifest,producer['manifest_sha256'])
            refs=json.loads((backup/'references.json').read_bytes());require(refs['identity']==i and digest((backup/'request.json').read_bytes())==pin,'Independent identity/request mismatch');decoded=[];selected=None
            for ref in refs['checkpoints']:
                restored=restore_checkpoint(backup,ref,i);decoded.append(dict(step=restored.step,weights_sha256=m.state_hash(restored.model.state_dict()),members=len(ref['payload'])));measure('restore'+str(restored.step))
                if restored.step==2:selected=restored
                else:del restored
            require(selected is not None,'Step2 unavailable');probe=selected.predict(m.fixture('multiple',144)[0]);expected=load_tensor((backup/'probe.pt').read_bytes());delta=float((probe-expected).abs().max());require(delta<=1e-5,'MPS probe replay differs');measure('restored-image-only')
            mask,native=native_probe(probe,lambda:tick(start,r,True));require(native==refs['native'],'Native export/scoring replay differs')
            exported=np.load(backup/'native-mask.npy',allow_pickle=False);require(np.array_equal(mask,exported),'Independent native mask differs');del mask,exported;measure('restored-native-export-score')
            nextrow=selected.synthetic_update();expected=load_tensor((backup/'next-weights.pt').read_bytes());wd=max(float((v.detach().cpu()-expected[n]).abs().max()) for n,v in selected.model.state_dict().items());ld=abs(nextrow['loss']-refs['next_update']['loss'])
            require(nextrow['member_id']==refs['next_update']['member_id'] and nextrow['sampling']==refs['next_update']['sampling'] and wd<=1e-6 and ld<=1e-5,'Restored next update differs');measure('restored-next-update')
            put(DEST/'recover-result.json',dict(state='passed',stage=stage,primary_python_reads_denied=True,restored=decoded,probability_max_difference=delta,next_weight_max_difference=wd,next_loss_difference=ld,native_export_scores_exact=True,optimizer_calls=1,real_optimizer_calls=0,original_reads=0,seconds=time.monotonic()-start,peak_rss_bytes=cpu.a.c.prior.rss(),memory=memory))
        require(checked(pin)==r,'Final native source drift');tick(start,r,stage=='recover')
    except BaseException as exc:put(DEST/(stage+'-failure.json'),dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),seconds=time.monotonic()-start));raise
    finally:signal.alarm(0)


def supervise(stage,pin):
    put(DEST/(stage+'-consumed.json'),dict(request_sha256=pin,stage=stage,state='consumed_no_retry'));start=time.monotonic();peak=0
    with (DEST/(stage+'-stdout.log')).open('xb') as out,(DEST/(stage+'-stderr.log')).open('xb') as err:
        p=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.segmenter_lowrate_native_qualification','--worker',stage,'--request-sha256',pin],cwd=REPO,stdout=out,stderr=err)
        try:
            while p.poll() is None:
                require(time.monotonic()-start<600,'Supervisor native deadline');status=subprocess.run(['/bin/ps','-o','rss=','-p',str(p.pid)],capture_output=True,text=True,timeout=5)
                if status.stdout.strip():peak=max(peak,int(status.stdout.strip())*1024)
                require(peak<=LIMITS['rss_bytes'],'Supervisor RSS limit');ac,_=power();require(ac,'AC power lost');time.sleep(.25)
        finally:
            if p.poll() is None:p.terminate();p.wait(timeout=10)
            put(DEST/(stage+'-supervision.json'),dict(exit_code=p.poll(),seconds=time.monotonic()-start,sampled_peak_rss_bytes=peak))
    require(p.returncode==0,'Native worker failed; request consumed, inspect retained evidence')


def run(pin):
    native_preflight();r=checked(pin);put(DEST/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry'));start=time.monotonic()
    lock=os.open(ROOT/'.mps-profile.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);supervise('produce',pin);supervise('recover',pin)
        require(time.monotonic()-start<=600,'Combined native budget exceeded')
        result=dict(state='qualified_native_mechanics_not_real_training',decision='D-332',request_sha256=pin,producer=json.loads((DEST/'produce-result.json').read_bytes()),recovery=json.loads((DEST/'recover-result.json').read_bytes()),source_pins=pins(),seconds=time.monotonic()-start,aggregate_synthetic_optimizer_calls=6,real_optimizer_calls=0,original_reads=0,real_training_authorized=False)
        put(DEST/'result.json',result);print(cpu.a.c.prior.package(DEST))
    except BaseException as exc:put(DEST/'run-failure.json',dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),seconds=time.monotonic()-start));raise
    finally:os.close(lock)


def main():
    p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True);group.add_argument('--prepare',action='store_true');group.add_argument('--run',action='store_true');group.add_argument('--worker',choices=['produce','recover']);p.add_argument('--request-sha256');a=p.parse_args()
    if a.prepare:prepare()
    elif a.run:run(a.request_sha256)
    else:worker(a.worker,a.request_sha256)
if __name__=='__main__':main()
