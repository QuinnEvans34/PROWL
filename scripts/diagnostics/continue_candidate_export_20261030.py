"""One separately frozen continuation of the 178 unfinished exports; zero updates."""
import argparse,json,os,sys,time,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import export_verifier_candidates_20261027 as old
from scripts.diagnostics import recover_candidate_export_20261030 as recovery
from scripts.acquisition import restore_remaining_cts_20261030 as restore
from src.data.verifier_relocated_inputs_20261030 import RelocatedCandidateInputs
from src.operations.verifier_candidate_archive_v1 import tree_bytes,check_capacity,write_json,backup_file,append_event,process_cases
from src.operations.full_training_platform import require_ac,watch_windows,training_guard
from src.training.experiment_config import sha256
pilot=old.pilot;read=old.read
SETUP=Path('E:/PROWL/readiness/verifier-candidate-continuation-20261030-a01')
OUT=Path('E:/PROWL/artifacts/verifier-candidates-20261030-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/verifier-candidates-20261030-a01')

def provider():
    return RelocatedCandidateInputs(relocation=read(restore.OUT/'restoration.json'),
        partition=read(pilot.BASE/'partitions.json'),partition_sha256=sha256(pilot.BASE/'partitions.json'),
        expected_partition_sha256=pilot.PARTITION_SHA,manifest=pilot.shared.parent.MANIFEST,
        review=pilot.shared.parent.SOURCE_SETUP/'cohort-review.json',train_file=pilot.shared.parent.TRAIN,
        dev_file=pilot.shared.parent.SOURCE_SETUP/'development.txt')

def resources(reserve_e=0,reserve_c=0):
    require_ac()
    check_capacity(used_e=sum(tree_bytes(p) for p in ('E:/PROWL/cache',pilot.OUT,old.OUT,old.SETUP,SETUP,OUT,recovery.OUT)),
        used_c=tree_bytes('C:/Users/quinn/PROWL-Backups'),free_e=shutil.disk_usage('E:/').free,
        free_c=shutil.disk_usage('C:/').free,reserve_e=reserve_e,reserve_c=reserve_c)

def verify_membership(audit,relocation):
    wanted=[c['case_id'] for c in audit['remaining']]
    if len(wanted)!=178 or len(set(wanted))!=178 or len(audit['rows'])!=355:raise ValueError('Recovery counts')
    if set(wanted)&{r['case_id'] for r in audit['rows']}:raise ValueError('Completed case reselected')
    if set(wanted)!=set(relocation['cases']):raise ValueError('Restoration membership')
    if relocation['status']!='BYTE_IDENTICAL_CT_RESTORATION_ONLY':raise ValueError('Restoration incomplete')
    if any(c['reuse'] or c['role']!=relocation['cases'][c['case_id']]['role'] for c in audit['remaining']):raise ValueError('Continuation roles')

def prepare():
    import numpy as np
    import xml.etree.ElementTree as ET
    if (SETUP/'request.json').exists() or (SETUP/'preparation-started.json').exists() or OUT.exists() or BACKUP.exists():raise ValueError('Stage already started')
    SETUP.mkdir(exist_ok=True);write_json(SETUP/'preparation-started.json',dict(utc_ms=int(time.time()*1000)))
    suites=list(ET.parse(SETUP/'tests-final.xml').getroot().iter('testsuite'))
    if sum(int(s.get('tests','0')) for s in suites)<12 or any(int(s.get(k,'0')) for s in suites for k in ('failures','errors')):raise ValueError('Recovery tests missing/failed')
    r=old.check(recovery.OLD_SHA);a=read(recovery.OUT/'audit.json');relocation=read(restore.OUT/'restoration.json')
    if a['status']!='PRIOR_355_INDEPENDENT_BACKUPS_VERIFIED':raise ValueError('Prior backups unverified')
    verify_membership(a,relocation)
    pins=dict(r['pins']);pins.update(a['pins'])
    for p,h in a['pins'].items():
        if sha256(p)!=h:raise ValueError('Prior audit input changed: '+p)
    inputs=provider();checks=[]
    for c in a['remaining']:
        n=c['case_id'];meta=inputs.metadata(n,c['role']);ct=inputs._object(n,'ct',meta);pancreas=inputs._object(n,'pancreas',meta)
        shape=tuple(meta['transform']['source_shape']);affine=meta['transform']['source_affine']
        if ct.shape!=shape or pancreas.shape!=shape or not np.allclose(ct.affine,affine,rtol=0,atol=1e-5) or not np.allclose(ct.affine,pancreas.affine,rtol=0,atol=1e-5):raise ValueError('Restored geometry/alignment')
        pins[relocation['cases'][n]['path']]=meta['source_sha256']['ct']
        checks.append(dict(case_id=n,role=c['role'],ct_sha256=meta['source_sha256']['ct'],pancreas_sha256=meta['source_sha256']['pancreas'],header_alignment=True))
    # Read the formerly failing CT completely once before dispatch, without labels or GPU.
    failed=inputs.load('PanTS_00005914',role=next(c['role'] for c in a['remaining'] if c['case_id']=='PanTS_00005914'))
    qualified=read(pilot.shared.CACHE/'PanTS_00005914.json')
    if any(failed[k]!=qualified[k] for k in ('geometry','parent_geometry','region_low','region_high')):raise ValueError('Recovered failed-case preprocessing differs')
    write_json(SETUP/'source-checks.json',dict(cases=checks,failed_case_full_read=True,lesion_label_reads=0))
    files=[Path(__file__),ROOT/'scripts/diagnostics/handoff_candidate_recovery_20261030.py',ROOT/'src/data/verifier_relocated_inputs_20261030.py',ROOT/'tests/test_verifier_relocated_inputs_20261030.py',ROOT/'tests/test_candidate_continuation_20261030.py',SETUP/'tests-final.xml',SETUP/'source-checks.json',recovery.OUT/'audit.json',restore.OUT/'restoration.json',Path(recovery.__file__),Path(restore.__file__)]
    pins.update({str(p):sha256(p) for p in files});resources()
    write_json(SETUP/'request.json',dict(status='APPROVED_RECOVERY_INFERENCE_ONLY',pins=pins,cases=a['remaining'],
        seconds=a['remaining_seconds'],rss_bytes=r['rss_bytes'],gpu_bytes=r['gpu_bytes'],environment=r['environment'],
        original_request_sha256=recovery.OLD_SHA,completed_reused=355,optimizer_updates=0,lesion_label_reads=0,automatic_retry=False))
    print(sha256(SETUP/'request.json'),flush=True)

def check(pin=None):
    if pin is not None and sha256(SETUP/'request.json')!=pin:raise ValueError('Request identity mismatch')
    r=read(SETUP/'request.json')
    if r['status']!='APPROVED_RECOVERY_INFERENCE_ONLY':raise ValueError('Recovery not authorized')
    pilot.shared.parent.check(r)
    return r

def admission(pin):
    if any(p.exists() for p in (OUT,BACKUP,SETUP/'dispatch.json',SETUP/'worker.log')):raise ValueError('No duplicate/retry')
    r=check(pin);resources();return r

def worker():
    import numpy as np,torch
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.verifier_candidate_export_v1 import predict,native_embed
    from src.training.candidate_verifier_v1 import candidates
    from src.training.verifier_candidate_provenance_v1 import validate_records
    r=check()
    if read(SETUP/'dispatch.json')['request_sha256']!=sha256(SETUP/'request.json'):raise ValueError('Dispatch identity')
    OUT.mkdir();BACKUP.mkdir()
    def backup(p):return backup_file(p,BACKUP/Path(p).name,reserve=lambda n:resources(reserve_c=n))
    backup(SETUP/'request.json');backup(SETUP/'source-checks.json')
    start=time.monotonic();last=[0.]
    def tick(done=0,total=0):
        if time.monotonic()-start>r['seconds']:raise ValueError('Remaining wall budget exceeded')
        if torch.cuda.is_initialized() and torch.cuda.max_memory_reserved()>r['gpu_bytes']:raise ValueError('GPU cap')
        if time.monotonic()-last[0]>15:resources();last[0]=time.monotonic()
    torch.set_num_threads(2);torch.cuda.set_per_process_memory_fraction(min(1.,r['gpu_bytes']/torch.cuda.get_device_properties(0).total_memory))
    state=torch.load(pilot.RUN/'execution/terminal.pt',map_location='cpu',weights_only=True)
    with (pilot.RUN/'execution/history.jsonl').open() as f:identity=json.loads(f.readline())['identity']
    session=FastVariedSession.restore(state['session'],identity)
    if session.step!=24000 or state['best_score'] is not None or set(session.raw.exposure.values())!={30}:raise ValueError('Generator changed')
    session.raw.model.requires_grad_(False);inputs=provider();generator_receipt=sha256(pilot.RUN/'ready.json')
    def produce(c):
        began=time.monotonic();n,role=c['case_id'],c['role'];case=inputs.load(n,role=role)
        geometry={k:case[k] for k in ('geometry','parent_geometry','region_low','region_high')}
        meta=read(pilot.shared.CACHE/(n+'.json'))
        if any(geometry[k]!=meta[k] for k in geometry):raise ValueError('Qualified geometry changed')
        tick();codes,prob,info=predict(session.raw,case['image'],case['geometry'],progress=tick)
        if info['gap_voxels'] or codes.dtype!=np.uint8 or prob.dtype!=np.float32 or prob.shape!=codes.shape or not np.isfinite(prob).all() or prob.min()<0 or prob.max()>1 or not np.isin(codes,[0,1,2]).all():raise ValueError('Invalid prediction')
        reservation=int(codes.size*5*1.01)+1024**2;resources(reserve_e=reservation,reserve_c=reservation)
        path=OUT/(n+'.npz')
        with path.open('xb') as f:np.savez_compressed(f,codes=codes,lesion_probability=prob);f.flush();os.fsync(f.fileno())
        with np.load(path,allow_pickle=False) as a:
            if not np.array_equal(a['codes'],codes) or not np.array_equal(a['lesion_probability'],prob):raise ValueError('Archive roundtrip')
        _,parts=candidates(native_embed(codes,geometry)==2)
        row=dict(case_id=n,role=role,checkpoint_sha256=pilot.CHECKPOINT_SHA,generator_receipt_sha256=generator_receipt,
            prediction_sha256=sha256(path),prediction_path=str(path),ct_sha256=case['source_sha256']['ct'],pancreas_sha256=case['source_sha256']['pancreas'],
            gap_voxels=info['gap_voxels'],tiles=info['tiles'],candidate_count=len(parts),components=parts,geometry=geometry,
            artifact_bytes=path.stat().st_size,reused_pilot=False,seconds=time.monotonic()-began,label_access='none',optimizer_updates=0)
        return row,path
    def record(row):
        path=OUT/(row['case_id']+'.json');write_json(path,row);return path
    def no_reuse(c):raise ValueError('Completed inference must not be redispatched')
    journal=OUT/'progress.jsonl';append_event(journal,dict(event='started',remaining=178,prior_completed=355,request_sha256=sha256(SETUP/'request.json')))
    try:
        new=process_cases(r['cases'],produce=produce,reuse=no_reuse,backup=backup,record=record,journal=journal,tick=tick)
        rows=read(recovery.OUT/'audit.json')['rows']+new
        validate_records(rows,read(pilot.BASE/'partitions.json'),checkpoint_sha256=pilot.CHECKPOINT_SHA,receipt_sha256=generator_receipt,
            actual_generator_ids=list(session.raw.exposure),required_ids=[c['case_id'] for c in read(old.SETUP/'request.json')['cases']])
        manifest=dict(status='COMPLETE_PREDICTIONS_ONLY',cases=rows,patients=533,prior_completed=355,continuation_inference=178,
            seconds=time.monotonic()-start,peak_gpu_reserved=torch.cuda.max_memory_reserved(),request_sha256=sha256(SETUP/'request.json'),
            original_request_sha256=recovery.OLD_SHA,optimizer_updates=0,lesion_label_reads=0)
        write_json(OUT/'manifest.json',manifest);backup(OUT/'manifest.json')
        append_event(journal,dict(event='completed',patients=533,seconds=manifest['seconds']));backup(journal);resources()
    except BaseException as exc:
        append_event(journal,dict(event='failed',error_type=type(exc).__name__,message=str(exc)));raise

def run(pin):
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        r=admission(pin);write_json(SETUP/'dispatch.json',dict(request_sha256=pin,utc_ms=int(time.time()*1000),explicit_user_approval=True))
        with (SETUP/'worker.log').open('x') as log:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_CANDIDATE_RECOVERY='1');env.pop('CUDA_VISIBLE_DEVICES',None)
            p=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            success=False
            try:watch_windows(p,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=require_ac);success=True
            finally:write_json(SETUP/'resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run-sha256');g.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.prepare:prepare()
    elif a.run_sha256:run(a.run_sha256)
    elif os.environ.get('PROWL_CANDIDATE_RECOVERY')=='1':worker()
    else:raise ValueError('Supervisor required')
