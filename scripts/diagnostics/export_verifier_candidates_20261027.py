"""Approved one-shot 533-case inference archive. No labels, training or resume."""
import argparse,json,os,sys,time,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import pilot_verifier_candidates_20261026 as pilot
from src.operations.verifier_candidate_archive_v1 import tree_bytes,check_capacity,write_json,backup_file,append_event,process_cases
from src.operations.full_training_platform import require_ac,watch_windows,training_guard
from src.training.experiment_config import sha256
from src.data.verifier_candidate_inputs_v1 import partition_roles
SETUP=Path('E:/PROWL/readiness/verifier-candidate-export-20261027-a01')
OUT=Path('E:/PROWL/artifacts/verifier-candidates-20261027-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/verifier-candidates-20261027-a01')
read=pilot.read

def resources(reserve_e=0,reserve_c=0):
    require_ac()
    check_capacity(used_e=tree_bytes('E:/PROWL/cache')+tree_bytes(pilot.OUT)+tree_bytes(OUT)+tree_bytes(SETUP),
        used_c=tree_bytes('C:/Users/quinn/PROWL-Backups'),
        free_e=shutil.disk_usage('E:/').free,free_c=shutil.disk_usage('C:/').free,
        reserve_e=reserve_e,reserve_c=reserve_c)

def pilot_gate():
    r=read(pilot.OUT/'result.json');v=read(pilot.OUT/'visual-review.json');s=read(pilot.OUT/'resources.json')
    if not r['passed'] or not v['passed'] or v['result_sha256']!=sha256(pilot.OUT/'result.json') or not s['success'] or not s['workers_reaped'] or s['exit_code']!=0:
        raise ValueError('Pilot completion/review gate')
    if [x['case_id'] for x in v['cases']]!=[x['case_id'] for x in r['cases']] or len(r['cases'])!=6:
        raise ValueError('Pilot visual membership')
    for a,b in zip(r['cases'],v['cases']):
        if not b['reviewed'] or b['figure_sha256']!=sha256(pilot.OUT/a['figure']) or a['figure_sha256']!=b['figure_sha256']:
            raise ValueError('Visual binding')
        if not a['baseline_exact'] or not a['archive_exact'] or a['gap_voxels'] or a['annotation_outside_region']:
            raise ValueError('Pilot numerical quality')
        if sha256(pilot.OUT/(a['case_id']+'.npz'))!=a['prediction_sha256']:raise ValueError('Pilot archive changed')
    return r

def prepare():
    import xml.etree.ElementTree as ET
    if (SETUP/'request.json').exists() or OUT.exists() or BACKUP.exists():raise ValueError('Stage already prepared/started')
    test=SETUP/'tests.xml';suites=list(ET.parse(test).getroot().iter('testsuite'))
    if not suites or sum(int(s.get('tests','0')) for s in suites)<40 or any(int(s.get(k,'0')) for s in suites for k in ('failures','errors')):
        raise ValueError('Full-export qualification tests missing/failed')
    r=pilot_gate();pilot.check();resources()
    if sha256(pilot.BASE/'partitions.json')!=pilot.PARTITION_SHA or sha256(pilot.RUN/'execution/terminal.pt')!=pilot.CHECKPOINT_SHA:raise ValueError('Parent identity changed')
    closeout=read(pilot.REVIEW)
    if closeout['status']!='CLOSEOUT_PASS_NOT_VERIFIER_EFFICACY':raise ValueError('Parent not complete')
    roles=partition_roles(read(pilot.BASE/'partitions.json'))
    if len(roles)!=533:raise ValueError('Expected full reserved membership')
    reuse={a['case_id']:a for a in r['cases']}
    cases=[dict(case_id=n,role=roles[n],reuse=n in reuse) for n in list(reuse)+sorted(set(roles)-set(reuse))]
    pins=dict(read(pilot.RUN/'ready.json')['pins'])
    pins.update(read(pilot.OUT/'request.json')['pins'])
    files=list((ROOT/'src').rglob('*.py'))+[Path(__file__),test,ROOT/'tests/test_verifier_candidate_archive_v1.py',pilot.OUT/'result.json',pilot.OUT/'resources.json',pilot.OUT/'visual-review.json',pilot.OUT/'request.json',pilot.OUT/'budget-review.json',pilot.REVIEW]
    files+=list(pilot.OUT.glob('*.png'))+list(pilot.OUT.glob('*.npz'))+list(pilot.OUT.glob('PanTS_*.json'))
    files+=[pilot.shared.CACHE/(n+'.json') for n in roles]
    for path in files:
        h=sha256(path)
        if str(path) in pins and pins[str(path)]!=h:raise ValueError('Inherited pin conflict')
        pins[str(path)]=h
    for p,h in pins.items():
        if sha256(p)!=h:raise ValueError('Inherited pin mismatch: '+p)
    request=dict(status='APPROVED_ONE_INFERENCE_STAGE',cases=cases,pins=pins,
        seconds=57600,rss_bytes=12*1024**3,gpu_bytes=6*1024**3,
        e_combined_bytes=64*1024**3,c_backup_combined_bytes=40*1024**3,free_floor=100*1024**3,
        optimizer_updates=0,lesion_label_reads=0,development_cases=0,test_cases=0,
        user_approved_date='2026-10-27',automatic_retry=False,
        environment=pilot.shared.parent.environment())
    write_json(SETUP/'request.json',request);print(sha256(SETUP/'request.json'),flush=True)

def check(pin=None):
    if pin is not None and sha256(SETUP/'request.json')!=pin:raise ValueError('Request hash mismatch')
    r=read(SETUP/'request.json')
    if r['status']!='APPROVED_ONE_INFERENCE_STAGE':raise ValueError('Not authorized')
    pilot.shared.parent.check(r)
    return r

def admission(pin):
    if OUT.exists() or BACKUP.exists() or (SETUP/'dispatch.json').exists() or (SETUP/'worker.log').exists():
        raise ValueError('No duplicate/retry/resume')
    r=check(pin);pilot_gate();resources();return r

def worker():
    import numpy as np,torch
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.verifier_candidate_export_v1 import predict,native_embed
    from src.training.candidate_verifier_v1 import candidates
    from src.training.verifier_candidate_provenance_v1 import validate_records
    r=check();dispatch=read(SETUP/'dispatch.json')
    if dispatch['request_sha256']!=sha256(SETUP/'request.json'):raise ValueError('Dispatch mismatch')
    OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
    def backup(path):return backup_file(path,BACKUP/Path(path).name,reserve=lambda n:resources(reserve_c=n))
    backup(SETUP/'request.json')
    start=time.monotonic();last=[0.]
    def tick(done=0,total=0):
        if time.monotonic()-start>r['seconds']:raise ValueError('Time cap')
        if torch.cuda.is_initialized() and torch.cuda.max_memory_reserved()>r['gpu_bytes']:raise ValueError('GPU cap')
        if time.monotonic()-last[0]>15:resources();last[0]=time.monotonic()
    torch.set_num_threads(2)
    fraction=min(1.,r['gpu_bytes']/torch.cuda.get_device_properties(0).total_memory)
    torch.cuda.set_per_process_memory_fraction(fraction)
    state=torch.load(pilot.RUN/'execution/terminal.pt',map_location='cpu',weights_only=True)
    with (pilot.RUN/'execution/history.jsonl').open() as f:identity=json.loads(f.readline())['identity']
    session=FastVariedSession.restore(state['session'],identity)
    if session.step!=24000 or state['best_score'] is not None or set(session.raw.exposure.values())!={30}:raise ValueError('Wrong generator checkpoint')
    session.raw.model.requires_grad_(False);provider=pilot.provider()
    generator_receipt=sha256(pilot.RUN/'ready.json')
    def make_row(n,role,codes,prob,geometry,source,path,info,reused,seconds):
        if codes.dtype!=np.uint8 or prob.dtype!=np.float32 or prob.shape!=codes.shape or not np.isfinite(prob).all() or prob.min()<0 or prob.max()>1 or not np.isin(codes,[0,1,2]).all():raise ValueError('Invalid archive arrays')
        native=native_embed(codes,geometry);labels,parts=candidates(native==2)
        return dict(case_id=n,role=role,checkpoint_sha256=pilot.CHECKPOINT_SHA,generator_receipt_sha256=generator_receipt,
            prediction_sha256=sha256(path),prediction_path=str(path),ct_sha256=source['ct'],pancreas_sha256=source['pancreas'],
            gap_voxels=info['gap_voxels'],tiles=info['tiles'],candidate_count=len(parts),components=parts,
            geometry=geometry,artifact_bytes=path.stat().st_size,reused_pilot=reused,seconds=seconds,
            label_access='none',optimizer_updates=0)
    def reuse(c):
        n=c['case_id'];old=read(pilot.OUT/(n+'.json'));path=pilot.OUT/(n+'.npz')
        meta=provider.metadata(n,c['role'])
        for kind in ('ct','pancreas'):
            provider._object(n,kind,meta)  # Verify observations/headers, no CT voxel read.
            if meta['source_sha256'][kind]!=old[kind+'_sha256']:raise ValueError('Reused source identity mismatch')
        with np.load(path,allow_pickle=False) as a:
            row=make_row(n,c['role'],a['codes'],a['lesion_probability'],old['geometry'],
                dict(ct=old['ct_sha256'],pancreas=old['pancreas_sha256']),path,old,True,0.)
        return row,path
    def produce(c):
        began=time.monotonic();n,role=c['case_id'],c['role'];case=provider.load(n,role=role)
        meta=read(pilot.shared.CACHE/(n+'.json'))
        geometry={k:case[k] for k in ('geometry','parent_geometry','region_low','region_high')}
        if any(geometry[k]!=meta[k] for k in geometry):raise ValueError('Qualified region geometry mismatch')
        tick();codes,prob,info=predict(session.raw,case['image'],case['geometry'],progress=tick)
        if info['gap_voxels']:raise ValueError('Reconstruction gaps')
        reservation=int(codes.size*5*1.01)+1024**2
        resources(reserve_e=reservation,reserve_c=reservation)
        path=OUT/(n+'.npz')
        with path.open('xb') as f:np.savez_compressed(f,codes=codes,lesion_probability=prob);f.flush();os.fsync(f.fileno())
        with np.load(path,allow_pickle=False) as a:
            if not np.array_equal(a['codes'],codes) or not np.array_equal(a['lesion_probability'],prob):raise ValueError('Archive roundtrip')
        row=make_row(n,role,codes,prob,geometry,case['source_sha256'],path,info,False,time.monotonic()-began)
        return row,path
    def record(row):
        path=OUT/(row['case_id']+'.json');write_json(path,row);return path
    journal=OUT/'progress.jsonl'
    append_event(journal,dict(event='started',total=533,reuse=6,request_sha256=sha256(SETUP/'request.json')))
    try:
        rows=process_cases(r['cases'],produce=produce,reuse=reuse,backup=backup,record=record,journal=journal,tick=tick)
        validate_records(rows,read(pilot.BASE/'partitions.json'),checkpoint_sha256=pilot.CHECKPOINT_SHA,
            receipt_sha256=generator_receipt,actual_generator_ids=list(session.raw.exposure),required_ids=[c['case_id'] for c in r['cases']])
        manifest=dict(status='COMPLETE_PREDICTIONS_ONLY',cases=rows,patients=533,reused=6,new_inference=527,
            seconds=time.monotonic()-start,peak_gpu_reserved=torch.cuda.max_memory_reserved(),
            request_sha256=sha256(SETUP/'request.json'),optimizer_updates=0,lesion_label_reads=0)
        write_json(OUT/'manifest.json',manifest);backup(OUT/'manifest.json')
        append_event(journal,dict(event='completed',patients=533,seconds=manifest['seconds']))
        backup(journal);resources()
    except BaseException as exc:
        append_event(journal,dict(event='failed',error_type=type(exc).__name__,message=str(exc)))
        raise

def run(pin):
    r=admission(pin)
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        admission(pin)
        write_json(SETUP/'dispatch.json',dict(request_sha256=pin,utc_ms=int(time.time()*1000),explicit_user_approval=True))
        with (SETUP/'worker.log').open('x') as log:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_FULL_CANDIDATE_EXPORT='1');env.pop('CUDA_VISIBLE_DEVICES',None)
            process=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            success=False
            try:watch_windows(process,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=require_ac);success=True
            finally:write_json(SETUP/'resources.json',dict(getattr(process,'duration_resources',{}),success=success,exit_code=process.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run-sha256');g.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.prepare:prepare()
    elif a.run_sha256:run(a.run_sha256)
    elif os.environ.get('PROWL_FULL_CANDIDATE_EXPORT')=='1':worker()
    else:raise ValueError('Supervisor required')
