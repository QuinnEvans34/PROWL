"""D-332 closed synthetic CPU qualification; no real inputs or automatic next-stage launch."""
import argparse,gc,json,os,shutil,signal,subprocess,sys,time
from pathlib import Path
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','0')
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_lowrate_session_v1 as m
from scripts.diagnostics import segmenter_loss_audit as a,segmenter_normalized_qualification as predecessor
from scripts.diagnostics.segmenter_learning_rehearsal import BARS,gate
from scripts.diagnostics.segmenter_source_verification import put,verify_package

ROOT=a.ROOT;DEST=ROOT/'SEGMENTER-LOWRATE-CPU-20261003'
CODE=['src/training/segmenter_lowrate_session_v1.py',
      'scripts/diagnostics/segmenter_lowrate_qualification.py','tests/test_segmenter_lowrate_candidate.py']
LIMITS=dict(trajectory_seconds=180,total_seconds=400,rss_bytes=2*1024**3,output_bytes=256*1024**2,free_bytes=100*1024**3)
AUDIT_PIN='d78be296a0b0f42f462bedc546d002613399847b21b586b37aabfde7cbd12b09'
PREDECESSOR_PIN='5221113806d5e733527a2b7b0cf03d21a40fed0cb3d7617bc7cd10de0ae15574'


def pins():
    result=verify_package(predecessor.DEST,PREDECESSOR_PIN);require(result['source_pins']==predecessor.pins() and result['state']=='learning_failed','D-331 sources changed')
    return predecessor.pins()|{n:digest((a.c.REPO/n).read_bytes()) for n in CODE}


def context():
    result=verify_package(a.DEST,AUDIT_PIN);require(result['source_pins']==a.pins(),'D-329 audit changed')
    return {'source.json':canonical(pins()),'environment.json':canonical(a.c.runtime()),
      'geometry.json':canonical(dict(domain='invented_class_cues_only',audit_receipt_sha256=AUDIT_PIN,real_geometry_or_inputs_allowed=False))}


def request():
    i,controls=m.make_identity(m.config(steps=480),context(),run_id='segmenter-lowrate-synthetic-D332-CPU',device='cpu')
    return dict(schema_version='1.0.0',decision='D-332',stage='synthetic_cpu_class_cues',identity=i,
        controls={n:v.decode() for n,v in controls.items()},source_pins=pins(),runtime=a.c.runtime(),limits=LIMITS,bars=BARS,
        trajectories=['uninterrupted480','interrupted30_plus_restored450'],total_synthetic_optimizer_calls=960,
        real_optimizer_calls=0,real_inputs_allowed=False,weight_imports_allowed=False,automatic_extension_allowed=False,output=str(DEST))


def prepare():
    r=request();DEST.mkdir();put(DEST/'request.json',r)
    for n in CODE:(DEST/('source--'+Path(n).name)).open('xb').write((a.c.REPO/n).read_bytes())
    print(digest((DEST/'request.json').read_bytes()))


def checked(pin):
    raw=(DEST/'request.json').read_bytes();require(DEST.resolve(strict=True)==DEST and digest(raw)==pin,'Exact synthetic request changed')
    r=json.loads(raw);require(r==request(),'Source/runtime/config/criteria drift');return r


def raw_write(p,v):
    with p.open('xb') as f:f.write(v);f.flush();os.fsync(f.fileno())


def save(s,label):
    files=m.payload(s);require(len(files)==8 and len(files['state.pt'])<=96*1024**2,'Synthetic checkpoint inventory/size')
    manifest={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()}
    for n,v in files.items():raw_write(DEST/(label+'--'+n),v)
    put(DEST/(label+'--manifest.json'),dict(identity_sha256=digest(canonical(s.identity)),step=s.step,files=manifest))
    return dict(prefix=label,manifest_sha256=digest((DEST/(label+'--manifest.json')).read_bytes()),step=s.step,weights_sha256=m.state_hash(s.model.state_dict()))


def load(ref,i):
    label=ref['prefix'];raw=(DEST/(label+'--manifest.json')).read_bytes();require(digest(raw)==ref['manifest_sha256'],'Local checkpoint manifest changed')
    manifest=json.loads(raw);require(manifest['identity_sha256']==digest(canonical(i)) and manifest['step']==ref['step'],'Checkpoint identity changed')
    files={n:(DEST/(label+'--'+n)).read_bytes() for n in manifest['files']}
    require(all(len(v)==manifest['files'][n]['bytes'] and digest(v)==manifest['files'][n]['sha256'] for n,v in files.items()),'Checkpoint bytes changed')
    s=m.restore_payload(files,i);require(s.step==ref['step'] and m.state_hash(s.model.state_dict())==ref['weights_sha256'],'Checkpoint model/step changed');return s


def tick(start):
    require(time.monotonic()-start<LIMITS['trajectory_seconds'] and a.c.prior.rss()<=LIMITS['rss_bytes'],'CPU time/RSS envelope')
    require(shutil.disk_usage(a.c.REPO).free>=LIMITS['free_bytes'],'CPU free-space floor')
    a.c.prior.check_output(DEST,LIMITS['output_bytes'])


def block_real():
    def deny(event,args):
        if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            path=os.fsdecode(args[0]);require(not path.startswith('/Volumes/PROWL-Data') and not path.endswith(('.nii','.nii.gz')),'Invented CPU qualification forbids primary/original reads')
    sys.addaudithook(deny)


def worker(stage,pin):
    r=checked(pin);require(stage in ('baseline','interrupt','resume'),'Unknown synthetic trajectory')
    permit=json.loads((DEST/(stage+'-consumed.json')).read_bytes());require(permit==dict(request_sha256=pin,state='consumed_no_retry',stage=stage),'Missing stage dispatch')
    put(DEST/(stage+'-worker-started.json'),dict(request_sha256=pin,state='single_use_worker_started',stage=stage))
    block_real();torch.set_num_threads(2);signal.alarm(LIMITS['trajectory_seconds']);start=time.monotonic()
    i=r['identity'];controls={n:v.encode() for n,v in r['controls'].items()}
    try:
        if stage in ('baseline','interrupt'):
            s=m.Session(i,controls);initial=s.evaluate()
            if stage=='interrupt':zero=save(s,'restart-step0')
            for k in range(480 if stage=='baseline' else 30):
                s.synthetic_update();tick(start)
                if k==29:s.evaluate()
            if stage=='interrupt':
                ref=save(s,'restart-step30');put(DEST/'interruption.json',dict(state='planned_interruption_after_committed30',checkpoint=ref,zero=zero,initial=initial,seconds=time.monotonic()-start))
                os.kill(os.getpid(),signal.SIGTERM);raise RuntimeError('SIGTERM failed')
            final=s.evaluate();ref=save(s,'baseline-step480');verdict=gate(initial,final)
            put(DEST/'baseline.json',dict(state='trajectory_complete',checkpoint=ref,initial=initial,final=final,gate=verdict,
                optimizer_calls=480,seconds=time.monotonic()-start,peak_rss_bytes=a.c.prior.rss()))
        else:
            prior=json.loads((DEST/'interruption.json').read_bytes());s=load(prior['checkpoint'],i)
            for k in range(450):s.synthetic_update();tick(start)
            final=s.evaluate();ref=save(s,'restored-step480');baseline=json.loads((DEST/'baseline.json').read_bytes());other=load(baseline['checkpoint'],i)
            require(m.progress(s)==m.progress(other) and m.state_hash(s.model.state_dict())==m.state_hash(other.model.state_dict()),'Restart weights/progress differ')
            from src.training.segmenter_training_session_v1 import tree_exact
            require(tree_exact(s.optimizer.state_dict(),other.optimizer.state_dict()) and torch.equal(s.cpu_rng,other.cpu_rng),'Restart optimizer/RNG differs')
            require(torch.equal(s.predict(m.fixture('multiple')[0]),other.predict(m.fixture('multiple')[0])),'Restart prediction differs')
            verdict=gate(prior['initial'],final);require(verdict==baseline['gate'] and final==baseline['final'],'Independent trajectory scores differ')
            put(DEST/'resume.json',dict(state='trajectory_complete',checkpoint=ref,initial=prior['initial'],final=final,gate=verdict,
                optimizer_calls=450,seconds=time.monotonic()-start,peak_rss_bytes=a.c.prior.rss(),exact_restart_model_optimizer_rng_progress=True,exact_reload_prediction=True))
        tick(start);checked(pin)
    except BaseException as exc:
        put(DEST/(stage+'-failure.json'),dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),seconds=time.monotonic()-start,committed_step=s.step if 's' in locals() else None));raise
    finally:signal.alarm(0)


def supervise(stage,pin,expected_exit=0):
    put(DEST/(stage+'-consumed.json'),dict(request_sha256=pin,state='consumed_no_retry',stage=stage))
    start=time.monotonic();peak=0
    with (DEST/(stage+'-stdout.log')).open('xb') as out,(DEST/(stage+'-stderr.log')).open('xb') as err:
        p=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.segmenter_lowrate_qualification','--worker',stage,'--request-sha256',pin],stdout=out,stderr=err)
        try:
            while p.poll() is None:
                require(time.monotonic()-start<LIMITS['trajectory_seconds'],'Supervised CPU time envelope')
                status=subprocess.run(['/bin/ps','-o','rss=','-p',str(p.pid)],capture_output=True,text=True,timeout=5)
                if status.stdout.strip():peak=max(peak,int(status.stdout.strip())*1024)
                require(peak<=LIMITS['rss_bytes'],'Supervised CPU RSS envelope');time.sleep(.2)
        except BaseException:
            p.terminate()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();p.wait()
            raise
        finally:put(DEST/(stage+'-supervision.json'),dict(exit_code=p.poll(),seconds=time.monotonic()-start,sampled_peak_rss_bytes=peak,expected_exit=expected_exit))
    require(p.returncode==expected_exit,'CPU trajectory failed; request consumed, inspect retained evidence')
    return time.monotonic()-start


def run(pin):
    r=checked(pin);put(DEST/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry',decision='D-332'))
    start=time.monotonic()
    try:
        t1=supervise('baseline',pin);t2=supervise('interrupt',pin,-signal.SIGTERM);t3=supervise('resume',pin)
        require(t1<=180 and t2+t3<=180 and time.monotonic()-start<=400,'Combined trajectory budget')
        baseline=json.loads((DEST/'baseline.json').read_bytes());resume=json.loads((DEST/'resume.json').read_bytes())
        require(baseline['gate']==resume['gate'] and resume['exact_restart_model_optimizer_rng_progress'],'Trajectory verdict mismatch')
        checked(pin);a.c.prior.check_output(DEST,LIMITS['output_bytes'])
        put(DEST/'result.json',dict(state='qualified' if resume['gate']['passed'] else 'learning_failed',decision='D-332',request_sha256=pin,
            gate=resume['gate'],initial=resume['initial'],final=resume['final'],completed_updates_each=480,
            synthetic_optimizer_calls=960,real_optimizer_calls=0,original_arrays_read=0,source_pins=pins(),runtime=a.c.runtime(),
            exact_restart_model_optimizer_rng_progress=True,exact_reload_prediction=True,seconds=time.monotonic()-start,
            mps_stage_allowed=bool(resume['gate']['passed']),automatic_real_launch_allowed=False))
        print(a.c.prior.package(DEST))
    except BaseException as exc:
        put(DEST/'run-failure.json',dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),seconds=time.monotonic()-start));raise


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--worker',choices=['baseline','interrupt','resume']);p.add_argument('--request-sha256');arg=p.parse_args()
    if arg.prepare:prepare()
    elif arg.run:run(arg.request_sha256)
    else:worker(arg.worker,arg.request_sha256)
if __name__=='__main__':main()
