"""Supplemental frozen invented-MPS step0 comparison; no real inputs or updates."""
import argparse,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','0')
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as data
from src.training import segmenter_training_session_v1 as core,segmenter_inference_v1 as old,segmenter_training_probe_v1 as probe
from scripts.diagnostics import segmenter_training_qualification as q,segmenter_source_verification as source,segmenter_content_pilot as prior

DEST=q.ROOT/'SEGMENTER-TRAINING-POLICY-PARITY-20261002'
SELF='scripts/diagnostics/segmenter_training_policy_parity.py'
RECOVERY='f8a75f15ca60045cac67c69c4b0b5633a36a0dd1075db3729631a8cdb17f9bb6'
LIMITS=dict(seconds=180,rss_bytes=8*1024**3,driver_bytes=12*1024**3,free_bytes=100*1024**3,output_bytes=2*1024**2)

def pins():return q.pins()|{SELF:digest((q.REPO/SELF).read_bytes())}
def checked(pin):
    raw=(DEST/'request.json').read_bytes();require(digest(raw)==pin,'Supplemental request changed');r=json.loads(raw)
    require(r==dict(decision='D-326',stage='invented_mps_step0_policy_parity',source_pins=pins(),runtime=q.runtime(),limits=LIMITS,recovery_sha256=RECOVERY,real_inputs_allowed=False,optimizer_calls=0),'Supplemental envelope changed')
    recovery=source.verify_package(q.ROOT/'SEGMENTER-TRAINING-MPS-20261002-RECOVERY',RECOVERY)
    require(recovery['state']=='passed' and recovery['primary_reads_blocked'] and recovery['real_model_updates']==0,'Cold transaction recovery prerequisite')
    return r
def prepare():
    r=dict(decision='D-326',stage='invented_mps_step0_policy_parity',source_pins=pins(),runtime=q.runtime(),limits=LIMITS,recovery_sha256=RECOVERY,real_inputs_allowed=False,optimizer_calls=0)
    DEST.mkdir();(DEST/'request.json').open('xb').write(canonical(r));print(digest(canonical(r)))
def worker(pin):
    checked(pin);source.put(DEST/'worker-consumed.json',dict(request_sha256=pin));torch.set_num_threads(2);start=time.monotonic();signal.alarm(LIMITS['seconds'])
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    def tick():
        torch.mps.synchronize();require(time.monotonic()-start<LIMITS['seconds'] and prior.rss()<=LIMITS['rss_bytes'] and torch.mps.driver_allocated_memory()<=LIMITS['driver_bytes'],'Supplemental resource ceiling')
    p=data.InventedInputs(144);x=p.get('invented-train-1',role='train',operation='inference').image;case=probe.native_case(x)
    identity,controls=core.make_identity(core.config(size=144,steps=4),p,q.context(),run_id='segmenter-training-policy-parity-D326',device='mps');new=core.Session(identity,controls);a=new.predict(x);tick()
    old_identity=old.make_identity([case],dict(source=pins(),environment=q.runtime(),ancestry={'domain':'invented_arrays_only'}),run_id='segmenter-step0-policy-parity-D326',domain='invented_profile')
    prior_session=old.Session(old_identity,device='mps');b=prior_session.predict(dict(image=x,**{k:case[k] for k in ('study_id','protected_role','transform','transform_sha256')}));tick()
    delta=float(np.max(np.abs(a-b)));require(delta==0,'Step0 inference policy changed')
    require(core.numerical.state_hash(new.model.state_dict())==old.state_hash(prior_session.model.state_dict())==core.INITIAL and new.step==0 and not new.history,'Initialization/state drift')
    ma,_=old.export(a,case,tick=tick);mb,_=old.export(b,case,tick=tick);require(np.array_equal(ma,mb),'Native argmax policy changed')
    source.put(DEST/'result.json',dict(state='passed',decision='D-326',scope='invented_MPS_policy_equivalence_not_real_case_reexecution',request_sha256=pin,source_pins=pins(),runtime=q.runtime(),initial_weights_sha256=core.INITIAL,probability_max_difference=delta,probability_sha256=digest(old.array_bytes(a)),native_sha256=digest(old.array_bytes(ma)),native_exact=True,model_forwards=2,optimizer_calls=0,real_inputs=0,source_arrays_read=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),driver_bytes=torch.mps.driver_allocated_memory()));signal.alarm(0)
def run(pin):
    checked(pin);source.put(DEST/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry'));start=time.monotonic();peak=0
    with (DEST/'worker.log').open('xb') as log:
        child=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.segmenter_training_policy_parity','--worker','--request-sha256',pin],cwd=q.REPO,stdout=log,stderr=subprocess.STDOUT)
        try:
            while child.poll() is None:
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(child.pid)],capture_output=True,text=True,timeout=5)
                if child.poll() is None:require(observed.returncode==0 and observed.stdout.strip(),'RSS monitor unavailable');peak=max(peak,int(observed.stdout.strip())*1024)
                require(time.monotonic()-start<LIMITS['seconds'] and peak<=LIMITS['rss_bytes'] and shutil.disk_usage(q.REPO).free>=LIMITS['free_bytes'] and q.power()[0],'Supplemental supervision ceiling');time.sleep(.25)
            require(child.returncode==0,'Supplemental worker failed');checked(pin);source.put(DEST/'supervision.json',dict(seconds=time.monotonic()-start,peak_rss_bytes=peak,exit_code=0));print(prior.package(DEST))
        except BaseException as e:source.put(DEST/'failure.json',dict(error=str(e),seconds=time.monotonic()-start));raise
        finally:
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','worker'):g.add_argument('--'+name,action='store_true')
    p.add_argument('--request-sha256');a=p.parse_args()
    if a.prepare:prepare()
    elif a.worker:worker(a.request_sha256)
    else:run(a.request_sha256)
