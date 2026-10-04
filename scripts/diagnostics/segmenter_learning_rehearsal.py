"""D-322 bounded synthetic learning/MPS checkpoint transaction and primary-blocked restore."""
import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import sys
import time
from uuid import uuid4
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_session_v1 as module
from src.operations.artifact_store import ArtifactStore
from scripts.diagnostics.localizer_context_profile import power
from scripts.diagnostics import segmenter_source_verification as source

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl';GIB=1024**3
CAP=REPO/'docs/capstone/operations/SEGMENTER-SYNTHETIC-STORAGE-CAPABILITY-2026-10-01.json'
CAP_PIN='a274167129974c73f95150b0fab34e80d2bc1b769dc52d03936e14c2a20ea29c'
ACCEPT='outputs/prowl/SEGMENTER-GEOMETRY-REVIEW-20261001/accepted-geometry.json'
ACCEPT_PIN='b3ff4db94b49f1ea9b44d57afd975c17f16309c9929df35fa3e0d9f7e67e7384'
PRIMARY='22750B93-2F3F-499D-87F5-902981BFAB59';BACKUP='542E8B1F-8D50-4783-9250-752DFDC899CD'
CODE=['src/training/segmenter_session_v1.py','src/operations/segmenter_run_storage_v1.py','src/operations/segmenter_backup_v1.py',
 'scripts/diagnostics/segmenter_learning_rehearsal.py','tests/test_segmenter_session.py','tests/test_segmenter_recovery.py',
 'src/models/segresnet.py','src/operations/artifact_store.py','src/operations/localizer_run_storage.py','scripts/diagnostics/storage_setup.py',
 'configs/local/roots.schema.json',str(CAP.relative_to(REPO))]
CPU_LIMITS=dict(seconds=600,rss_bytes=6*GIB,output_bytes=256*1024**2,free_bytes=100*GIB)
MPS_LIMITS=dict(seconds=1200,rss_bytes=12*GIB,driver_bytes=12*GIB,output_bytes=512*1024**2,free_bytes=100*GIB)
BARS=dict(loss_ratio=.8,positive_lesion_dice=.65,positive_lesion_recall=.8,pancreas_dice=.8,all_components_hit=True,negative_lesion_fraction=.02)


def write(p,x):source.put(p,x)
def raw(p,b):
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def tensor(p,x):
    with p.open('xb') as f:torch.save(x,f);f.flush();os.fsync(f.fileno())
def rss():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

def capture():
    old=json.loads((REPO/'outputs/prowl/SEGMENTER-GEOMETRY-FIDELITY-attempt02-20261001/request.json').read_bytes())['code_pins']
    require(all(source.sha((REPO/n).read_bytes())==h for n,h in old.items()),'D-321 producers changed')
    require(source.sha(CAP.read_bytes())==CAP_PIN,'Storage capability changed')
    src=old|{n:source.sha((REPO/n).read_bytes()) for n in CODE}
    env=dict(python=sys.version,platform=platform.platform(),machine=platform.machine(),executable=str(Path(sys.executable).absolute()),
        executable_sha256=source.sha(Path(sys.executable).read_bytes()),packages={n:importlib.metadata.version(n) for n in ('torch','monai','numpy','scipy','nibabel','Pillow')},threads=2)
    return {'source.json':canonical(src),'environment.json':canonical(env),'geometry.json':canonical(dict(
        domain='synthetic_context_only_not_real_input_permission',acceptance_sha256=ACCEPT_PIN,
        accepted_geometry=json.loads(source.safe_local(ACCEPT,ACCEPT_PIN))))}


def stores(create=False,recovery=False):
    from src.operations.segmenter_run_storage_v1 import run_stores
    return run_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=create,recovery_only=recovery)


def envelope(inv):
    require(inv['stage'] in ('cpu','mps_produce','mps_recover') and inv['decision']=='D-322' and inv['synthetic_only'] is True,'Wrong invocation domain')
    expected=CPU_LIMITS if inv['stage']=='cpu' else MPS_LIMITS
    require(inv['limits']==expected and inv['bars']==BARS and inv['capability_sha256']==CAP_PIN,'Invocation limits/criteria changed')
    require(inv['identity']['config']==module.config(steps=480) if inv['stage']=='cpu' else inv['identity']['config']==module.config(size=144,steps=4,lr=.0003),'Exact synthetic config differs')
    require(inv['identity']['device']==('cpu' if inv['stage']=='cpu' else 'mps'),'Wrong device')


def checked(dest,pin):
    require(dest.parent==ROOT and dest.resolve(strict=True)==dest,'Wrong evidence destination')
    b=(dest/'invocation.json').read_bytes();require(digest(b)==pin,'Independent invocation pin changed');inv=json.loads(b);envelope(inv)
    context=capture();require(all(inv['controls'][n]==context[n].decode() for n in context),'Source/runtime/geometry context changed')
    controls={n:v.encode() for n,v in inv['controls'].items()};module.validate_controls(inv['identity'],controls);return inv,controls


def gate(initial,final):
    ratio=sum(r['loss'] for r in final['cases'])/sum(r['loss'] for r in initial['cases']);ok=ratio<BARS['loss_ratio']
    for r in final['cases']:
        m=r['metrics'];ok=ok and m['pancreas_parenchyma']['dice']>=BARS['pancreas_dice']
        if m['lesion']['target_voxels']:ok=ok and m['lesion']['dice']>=BARS['positive_lesion_dice'] and m['lesion']['recall']>=BARS['positive_lesion_recall'] and all(c['true_positive']>0 for c in m['components'])
        else:ok=ok and m['lesion_false_positive_fraction']<=BARS['negative_lesion_fraction']
    return dict(passed=bool(ok),loss_ratio=ratio,thresholds=BARS)


def bounded_worker(dest,inv):
    start=time.monotonic();signal.alarm(inv['limits']['seconds'])
    def tick():
        require(time.monotonic()-start<inv['limits']['seconds'] and rss()<=inv['limits']['rss_bytes'],'Worker time/RSS ceiling')
        require(shutil.disk_usage(REPO).free>=inv['limits']['free_bytes'],'Disk-free floor')
        if inv['stage']=='cpu':size=sum(p.stat().st_size for area in (dest,ROOT/(inv['identity']['run_id']+'-checkpoints')) for p in area.rglob('*') if p.is_file())
        else:size=sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
        require(size<=inv['limits']['output_bytes'],'Evidence output ceiling')
        if inv['stage']!='cpu':
            torch.mps.synchronize();require(torch.mps.driver_allocated_memory()<=inv['limits']['driver_bytes'],'MPS driver cap')
    return start,tick


def cpu_worker(dest,pin,interruption=False):
    inv,controls=checked(dest,pin);torch.set_num_threads(2)
    # No source-array/external checkpoint reads in either CPU process.
    def audit(event,args):
        if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            require(not os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'),'External primary/source reads forbidden in CPU learning')
    sys.addaudithook(audit)
    start,tick=bounded_worker(dest,inv);identity=inv['identity'];ck=ROOT/(identity['run_id']+'-checkpoints')
    store=ArtifactStore(ck,check_root=lambda:None,minimum_free_bytes=100*GIB)
    if interruption:
        session=module.Session(identity,controls);initial=session.evaluate();zero=module.publish_checkpoint(store,session)
        for _ in range(30):session.synthetic_update();tick()
        session.evaluate();ref=module.publish_checkpoint(store,session)
        write(dest/'interrupted.json',dict(initial=initial,zero=zero,checkpoint=ref,expected_exit=-signal.SIGTERM))
        os.kill(os.getpid(),signal.SIGTERM);raise RuntimeError('SIGTERM failed')
    supervise(dest,'cpu_interrupt',pin,inv['limits'],expected_exit=-signal.SIGTERM)
    refs=json.loads((dest/'interrupted.json').read_bytes());resumed=module.resume(store,refs['checkpoint'],identity)
    baseline=module.Session(identity,controls);baseline.evaluate()
    for k in range(480):
        baseline.synthetic_update()
        if k==29:baseline.evaluate()
        tick()
    baseline.evaluate()
    for _ in range(450):resumed.synthetic_update();tick()
    final=resumed.evaluate();require(module.progress(baseline)==module.progress(resumed),'CPU sampler/evaluation continuation differs')
    require(module.state_hash(baseline.model.state_dict())==module.state_hash(resumed.model.state_dict()),'CPU continued weights differ')
    terminal=module.publish_checkpoint(store,resumed);fresh=module.resume(store,terminal,identity)
    require(torch.equal(fresh.predict(module.fixture('multiple')[0]),baseline.predict(module.fixture('multiple')[0])),'CPU prediction replay differs')
    verdict=gate(refs['initial'],final)
    report=dict(state='passed' if verdict['passed'] else 'learning_failed',synthetic_only=True,initial=refs['initial'],final=final,gate=verdict,
        completed_steps=480,aggregate_updates=960,interruption_exit=-signal.SIGTERM,exact_cpu_continuation=True,exact_reload_prediction=True,
        checkpoints=[refs['zero'],refs['checkpoint'],terminal],seconds=time.monotonic()-start,peak_rss_bytes=rss(),source_arrays_read=0,real_model_updates=0)
    final_context=capture();require(all(inv['controls'][n]==final_context[n].decode() for n in final_context),'Final CPU code/runtime context changed')
    write(dest/'result.json',report);require(verdict['passed'],'Preregistered synthetic learning screen failed');tick();signal.alarm(0)


def native_probe(p,tick):
    from src.data import segmenter_geometry_v1 as g
    t=g.plan_geometry([512,402,197],np.diag([.78,.78,1.25,1.]),[[100,120,0],[280,260,80]],g.recipe(),
        source_identity=dict(study_id='invented_native_grid_probe',ct_sha256=digest(b'invented_no_CT')),roi_origin='provided_pancreas_reference')
    native=g.restore_probabilities(p.numpy(),t,trusted_record_sha256=digest(canonical(t)),tick=tick)
    require(native.shape==(3,512,402,197) and np.isfinite(native).all() and np.allclose(native.sum(0),1,rtol=0,atol=1e-4),'Native inverse probe failed')
    mask=native.argmax(0).astype(np.uint8)
    result=dict(domain='invented_grid_and_model_fixture_no_real_CT',shape=list(native.shape),probability_sha256=source.sha(memoryview(native).cast('B')),
        argmax_sha256=source.sha(memoryview(mask).cast('B')),transform_sha256=digest(canonical(t)),source_grid_exact=True,model_updates=0)
    del native,mask;return result


def mps_worker(dest,pin,recovery=False):
    inv,controls=checked(dest,pin);torch.set_num_threads(2)
    if recovery:
        def audit(event,args):
            if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
                require(not os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'),'Primary reads forbidden in recovery')
        sys.addaudithook(audit)
    require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS required')
    torch.mps.set_per_process_memory_fraction(min(1.,MPS_LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    start,tick=bounded_worker(dest,inv);identity=inv['identity'];memory=[]
    def measure(name):
        tick();memory.append(dict(stage=name,live_bytes=torch.mps.current_allocated_memory(),driver_bytes=torch.mps.driver_allocated_memory(),rss_bytes=rss()))
    from src.operations.segmenter_backup_v1 import backup_checkpoint,restore_backup
    if not recovery:
        primary,backup,_=stores()
        primary.quota_bytes=min(primary.quota_bytes,inv['storage_ceilings'][0]);backup.quota_bytes=min(backup.quota_bytes,inv['storage_ceilings'][1])
        session=module.Session(identity,controls);references=[];rows=[]
        def save():
            ref=module.publish_checkpoint(primary,session);b=backup_checkpoint(primary,backup,ref,identity,source_domain=PRIMARY,destination_domain=BACKUP)
            references.append(dict(primary=ref,backup=b));measure('checkpoint-backup')
        save()
        for _ in range(2):
            then=time.monotonic();row=session.synthetic_update();measure('update');row['seconds']=time.monotonic()-then;rows.append(row)
        session.evaluate();save()
        before=module.state_hash(session.model.state_dict());probe=session.predict(module.fixture('multiple',144)[0]);measure('predict')
        require(before==module.state_hash(session.model.state_dict()),'Inference changed weights');tensor(dest/'probe.pt',probe)
        native=native_probe(probe,tick);measure('native-inverse')
        nextrow=session.synthetic_update();measure('next-update');tensor(dest/'next-weights.pt',module.cpu_tree(session.model.state_dict()))
        # Throw after a real synthetic optimizer step: nothing from that dirty state may publish.
        saved=module.payload(session);old=session.optimizer.step
        def fail():old();raise RuntimeError('injected incomplete optimizer transaction')
        session.optimizer.step=fail
        try:session.synthetic_update();raise AssertionError('Injected partial step unexpectedly committed')
        except RuntimeError:pass
        require(session.dirty and session.step==3,'Partial update was committed')
        denied=0
        for call in (session.synthetic_update,lambda:module.payload(session)):
            try:call()
            except ValueError:denied+=1
        require(denied==2,'Dirty update/checkpoint accepted');session=module.restore_payload(saved,identity);save()
        write(dest/'references.json',dict(identity=identity,checkpoints=references,step2_weights_sha256=before,probe_sha256=source.sha((dest/'probe.pt').read_bytes()),
            next_weights_sha256=source.sha((dest/'next-weights.pt').read_bytes()),next_update=nextrow,native_probe=native,updates=rows,partial_update_refused=True))
        write(dest/'result.json',dict(state='passed',stage='mps_produce',synthetic_only=True,source_arrays_read=0,real_model_updates=0,
            completed_steps=3,aggregate_optimizer_calls=4,dirty_transaction_refused=True,checkpoints=len(references),seconds=time.monotonic()-start,peak_rss_bytes=rss(),memory=memory))
    else:
        require(source.sha((dest/'references.json').read_bytes())==inv['references_sha256'],'Recovery references changed')
        refs=json.loads((dest/'references.json').read_bytes());require(refs['identity']==identity,'Recovery identity differs')
        _,backup,target=stores(recovery=True)
        for st in (backup,target):st.quota_bytes=min(st.quota_bytes,inv['storage_ceilings'][1])
        restored=[];selected=None
        for pair in refs['checkpoints']:
            files,r=restore_backup(backup,target,pair['backup'],pair['primary'],identity)
            session=module.restore_payload(files,identity);measure('restore')
            restored.append(dict(reference=r,step=session.step,members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()}))
            if session.step==2:selected=session
        require(selected is not None and module.state_hash(selected.model.state_dict())==refs['step2_weights_sha256'],'Step2 weights differ')
        probe=selected.predict(module.fixture('multiple',144)[0]);measure('restored-predict')
        require(source.sha((dest/'probe.pt').read_bytes())==refs['probe_sha256'],'Expected probe bytes differ')
        expected=torch.load(dest/'probe.pt',weights_only=True,map_location='cpu');delta=float((probe-expected).abs().max());require(delta<=1e-5,'Prediction replay differs')
        native=native_probe(probe,tick);measure('restored-native-inverse');require(native==refs['native_probe'],'Native inverse replay differs')
        row=selected.synthetic_update();measure('restored-next-update');require(row['sampling']==refs['next_update']['sampling'] and row['member_id']==refs['next_update']['member_id'],'Next exposure differs')
        require(source.sha((dest/'next-weights.pt').read_bytes())==refs['next_weights_sha256'],'Next-weight oracle changed')
        expected=torch.load(dest/'next-weights.pt',weights_only=True,map_location='cpu');wd=max(float((v.detach().cpu()-expected[n]).abs().max()) for n,v in selected.model.state_dict().items())
        ld=abs(row['loss']-refs['next_update']['loss']);require(wd<=1e-6 and ld<=1e-5,'Next update replay differs')
        write(dest/'result.json',dict(state='passed',stage='mps_recover',synthetic_only=True,primary_reads_forbidden=True,source_arrays_read=0,real_model_updates=0,
            restored=restored,probability_max_difference=delta,next_weight_max_difference=wd,next_loss_difference=ld,exact_native_probe=True,
            completed_steps=selected.step,aggregate_optimizer_calls=1,seconds=time.monotonic()-start,peak_rss_bytes=rss(),memory=memory))
    final=capture();require(all(inv['controls'][n]==final[n].decode() for n in final),'Final code/runtime context changed');tick();signal.alarm(0)


def supervise(dest,stage,pin,limits,expected_exit=0):
    started=time.monotonic();peak=0;env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1')
    logname=stage+'.log'
    with (dest/logname).open('xb') as log:
        p=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.segmenter_learning_rehearsal','--worker',str(dest),'--stage',stage,'--pin',pin],cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
        reason=None
        try:
            next_power=0;ac=True
            while p.poll() is None:
                elapsed=time.monotonic()-started
                if stage.startswith('mps') and elapsed>=next_power:ac,_=power();next_power=elapsed+10
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(p.pid)],capture_output=True,text=True,timeout=5)
                if observed.returncode==0 and observed.stdout.strip():peak=max(peak,int(observed.stdout.strip())*1024)
                elif p.poll() is None:raise RuntimeError('Memory monitor unavailable')
                require(elapsed<limits['seconds'] and peak<=limits['rss_bytes'] and ac,'Supervisor time/RSS/power ceiling')
                require(shutil.disk_usage(REPO).free>=limits['free_bytes'],'Supervisor disk-free floor');time.sleep(.25)
            require(p.returncode==expected_exit,'Worker exit differs: '+str(p.returncode))
        except BaseException as e:reason=str(e);raise
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
            write(dest/(stage+'-supervision.json'),dict(exit_code=p.returncode,expected_exit=expected_exit,reason=reason,seconds=time.monotonic()-started,observed_peak_rss_bytes=peak))


def package(dest):
    files={p.name:dict(bytes=p.stat().st_size,sha256=source.sha(p.read_bytes())) for p in dest.iterdir() if p.is_file()}
    write(dest/'receipt.json',dict(state='complete',synthetic_only=True,files=files));return source.sha((dest/'receipt.json').read_bytes())


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--cpu',action='store_true');g.add_argument('--mps',action='store_true');g.add_argument('--worker',type=Path)
    p.add_argument('--stage',choices=('cpu','cpu_interrupt','mps_produce','mps_recover'));p.add_argument('--pin');a=p.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Synthetic deadline')))
    if a.worker:
        inv,_=checked(a.worker,a.pin)
        require((a.stage.startswith('cpu') and inv['stage']=='cpu') or inv['stage']==a.stage,'Worker stage mismatch')
        write(a.worker/(a.stage+'-consumed.json'),dict(invocation_sha256=a.pin,stage=a.stage,state='consumed_no_retry'))
        try:
            if a.stage.startswith('cpu'):return cpu_worker(a.worker,a.pin,interruption=a.stage=='cpu_interrupt')
            return mps_worker(a.worker,a.pin,recovery=a.stage=='mps_recover')
        except BaseException as e:write(a.worker/(a.stage+'-failure.json'),dict(state='failed',error=str(e)));raise
    require(shutil.disk_usage(REPO).free>=100*GIB,'Disk-free floor')
    lock=None
    try:
        if a.mps:
            ac,_=power();require(ac,'AC power required');lock=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            primary,backup,_=stores(create=True);ceilings=[primary.quota_bytes,backup.quota_bytes]
        else:ceilings=[]
        context=capture();c=module.config(size=144,steps=4,lr=.0003) if a.mps else module.config(steps=480)
        i,controls=module.make_identity(c,context,run_id='segmenter-synthetic-'+str(uuid4()),device='mps' if a.mps else 'cpu')
        dest=ROOT/i['run_id'];dest.mkdir()
        if a.cpu:(ROOT/(i['run_id']+'-checkpoints')).mkdir()
        inv=dict(decision='D-322',stage='mps_produce' if a.mps else 'cpu',synthetic_only=True,identity=i,controls={n:v.decode() for n,v in controls.items()},
            limits=MPS_LIMITS if a.mps else CPU_LIMITS,bars=BARS,capability_sha256=CAP_PIN,storage_ceilings=ceilings)
        write(dest/'invocation.json',inv);pin=source.sha((dest/'invocation.json').read_bytes());print(json.dumps(dict(destination=str(dest),invocation_sha256=pin)),flush=True)
        supervise(dest,inv['stage'],pin,inv['limits']);print(json.dumps(dict(receipt_sha256=package(dest),result=json.loads((dest/'result.json').read_bytes()))),flush=True)
        if a.mps:
            recovery=ROOT/(i['run_id']+'-recovery');recovery.mkdir()
            for n in ('references.json','probe.pt','next-weights.pt'):shutil.copyfile(dest/n,recovery/n)
            inv['stage']='mps_recover';inv['references_sha256']=source.sha((recovery/'references.json').read_bytes());write(recovery/'invocation.json',inv)
            supervise(recovery,'mps_recover',source.sha((recovery/'invocation.json').read_bytes()),inv['limits'])
            print(json.dumps(dict(recovery=str(recovery),receipt_sha256=package(recovery),result=json.loads((recovery/'result.json').read_bytes()))),flush=True)
    finally:
        if lock is not None:os.close(lock)


if __name__=='__main__':main()
