"""Freeze a qualified verifier; scientific dispatch requires explicit launch flag."""
import argparse,json,os,sys,time,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import build_verifier_views_20261031 as build
from scripts.diagnostics import qualify_verifier_20261031 as qualify
from src.training.experiment_config import sha256
from src.operations.verifier_candidate_archive_v1 import write_json,backup_file
from src.operations.full_training_platform import watch_windows,require_ac,training_guard
BASE=build.BASE;NAME='pants_candidate_verifier_20261031'
OUT=Path('E:/PROWL/artifacts')/NAME;BACKUP=Path('C:/Users/quinn/PROWL-Backups')/NAME
FILES=['src/data/verifier_views_20261031.py','src/training/verifier_session_20261031.py','src/training/verifier_executor_20261031.py',
    'src/training/verifier_decisions_20261031.py','scripts/diagnostics/build_verifier_views_20261031.py',
    'scripts/diagnostics/qualify_verifier_20261031.py','scripts/train_verifier_20261031.py']

def freeze():
    import xml.etree.ElementTree as ET
    if (BASE/'ready.json').exists() or OUT.exists():raise ValueError('Already frozen/started')
    suites=list(ET.parse(BASE/'tests-post-pilot.xml').getroot().iter('testsuite'))+list(ET.parse(BASE/'tests-comparison.xml').getroot().iter('testsuite'))
    suites+=list(ET.parse(BASE/'tests-occupancy.xml').getroot().iter('testsuite'))
    suites+=list(ET.parse(BASE/'tests-tune.xml').getroot().iter('testsuite'))
    if sum(int(s.get('tests','0')) for s in suites)<20 or any(int(s.get(k,'0')) for s in suites for k in ('failures','errors')):raise ValueError('Final tests gate')
    for stage in ('producer','cold'):
        result=build.pilot.read(qualify.OUT/(stage+'.json'));resources=build.pilot.read(qualify.OUT/(stage+'-resources.json'))
        if not result['passed'] or not result['nonpromotable'] or not resources['success'] or not resources['workers_reaped'] or resources['exit_code']!=0:raise ValueError('GPU qualification gate')
    build_status=build.pilot.read(BASE/'build/resources.json')
    if not build_status['success'] or not build_status['workers_reaped']:raise ValueError('Complete intake not clean')
    from src.training.verifier_session_20261031 import Dataset
    manifest=BASE/'build/manifest.json';d=Dataset(manifest,sha256(manifest));design=build.pilot.read(build.DESIGN)
    expected={n:role for role,names in design['patients'].items() for n in names}
    records=d.manifest['patient_records']
    if len(records)!=333 or {r['case_id']:r['role'] for r in records}!=expected or len({r['case_id'] for r in records})!=333:raise ValueError('Patient accounting')
    if len({r['positive'] for r in d.rows if r['role']=='verifier_fit'})!=2:raise ValueError('Insufficient classes')
    for row in d.rows:
        if not row['view_metadata']['complete_component_coverage'] or sha256(row['path'])!=row['sha256'] or sha256(build.BACKUP/Path(row['path']).name)!=row['sha256']:raise ValueError('Intake/independent backup gate')
    coverage=build.pilot.read(BASE/'fit-coverage-reuse.json')
    if not coverage['passed'] or len(coverage['cases'])!=266:raise ValueError('Inherited fitting coverage evidence')
    for row in coverage['cases']:
        if sha256(row['metadata_path'])!=row['metadata_sha256']:raise ValueError('Coverage metadata changed')
    for receipt in (BASE/'pilot/request.json',BASE/'build/request.json'):
        for path,pin in build.pilot.read(receipt)['pins'].items():
            if sha256(path)!=pin:raise ValueError('Prepared intake producer changed: '+path)
    qualification=build.pilot.read(qualify.OUT/'request.json')
    for p,h in qualification['pins'].items():
        if sha256(p)!=h:raise ValueError('Qualified producer changed')
    files=[ROOT/f for f in FILES]+[build.DESIGN,BASE/'tests-post-pilot.xml',BASE/'tracking-readiness.json',BASE/'dashboard/experiments.py',BASE/'dashboard/index.html',BASE/'dashboard/handoff.json',manifest,BASE/'build/resources.json',BASE/'pilot/visual-review.json',qualify.OUT/'request.json',qualify.OUT/'producer.json',qualify.OUT/'cold.json',qualify.OUT/'producer-resources.json',qualify.OUT/'cold-resources.json']
    files += list((ROOT/'src').rglob('*.py'))
    files += [BASE/'fit-coverage-reuse.json',ROOT/'scripts/diagnostics/check_verifier_fit_coverage_20261031.py',BASE/'pilot/request.json',BASE/'tests-tune.xml',BASE/'tests-occupancy.xml',BASE/'tests-comparison.xml',BASE/'build/request.json',build.review.MANIFEST,build.pilot.BASE/'partitions.json']
    pins={str(p):sha256(p) for p in files};pins.update({r['path']:r['sha256'] for r in d.rows});build.resource_check()
    steps=math.ceil(len(d.fit)/design['batch_size'])*design['epochs']
    write_json(BASE/'configuration.json',dict(run=dict(max_updates=steps,validate_every=math.ceil(len(d.fit)/design['batch_size'])),name=NAME,metric_scope='verifier_candidate_classification'))
    pins[str(BASE/'configuration.json')]=sha256(BASE/'configuration.json')
    write_json(BASE/'dashboard-handoff.json',dict(title='Reject false lesion candidates while preserving real lesions',journal=str(OUT/'execution/history.jsonl'),target_steps=steps,
        metric_scope='verifier_candidate_classification',cohort_summary='266 fit / 67 tuning; 200 calibration locked; no development Dice during fitting'))
    write_json(BASE/'ready.json',dict(status='READY_REQUIRES_EXPLICIT_USER_LAUNCH',name=NAME,pins=pins,configuration=design,
        environment=build.pilot.shared.parent.environment(),
        dataset_manifest=str(manifest),dataset_sha256=sha256(manifest),seconds=28800,rss_bytes=12*1024**3,gpu_bytes=6*1024**3,
        nonpromotable_qualification=True,max_updates=steps,scientific_output=str(OUT),automatic_retry=False))
    print(sha256(BASE/'ready.json'),flush=True)

def check(pin):
    if sha256(BASE/'ready.json')!=pin:raise ValueError('Ready receipt identity')
    r=build.pilot.read(BASE/'ready.json')
    if r['status']!='READY_REQUIRES_EXPLICIT_USER_LAUNCH':raise ValueError('Readiness status')
    if r['environment']!=build.pilot.shared.parent.environment():raise ValueError('Qualified environment changed')
    for p,h in r['pins'].items():
        if sha256(p)!=h:raise ValueError('Frozen input changed: '+p)
    return r

def worker(pin):
    import torch
    from mlflow.tracking import MlflowClient
    from src.training.verifier_session_20261031 import Dataset,Session
    from src.training.verifier_executor_20261031 import execute
    from scripts.diagnostics.backfill_full_runs_mlflow import URI
    if os.environ.get('PROWL_VERIFIER_SCIENCE_SHA')!=pin or build.pilot.read(BASE/'scientific-dispatch.json')['ready_sha256']!=pin:raise ValueError('Scientific supervisor required')
    r=check(pin);qualify.configure();OUT.mkdir();BACKUP.mkdir()
    write_json(OUT/'resolved.yaml',dict(_experiment=build.pilot.read(BASE/'configuration.json')))
    (OUT/'splits').mkdir()
    (OUT/'splits/train_ids.txt').write_text('\n'.join(r['configuration']['patients']['verifier_fit'])+'\n')
    def backup(path):return backup_file(path,BACKUP/Path(path).name,reserve=lambda _:build.resource_check())
    for path in (BASE/'ready.json',BASE/'configuration.json'):backup(path)
    client=MlflowClient(tracking_uri=URI);name='PROWL candidate verification';exp=client.get_experiment_by_name(name)
    expid=exp.experiment_id if exp else client.create_experiment(name)
    run=client.create_run(expid,tags={'mlflow.runName':'Reject false lesion candidates while preserving real lesions','machine':'Windows training laptop','scope':'design-informed/exploratory','generator':'pants_reserved_verifier_generator_24k_20261025','generator_checkpoint_sha256':build.pilot.CHECKPOINT_SHA,'candidate_manifest_sha256':build.review.MANIFEST_SHA,'ready_sha256':pin})
    runid=run.info.run_id;write_json(OUT/'mlflow.json',dict(run_id=runid,tracking_uri=URI));backup(OUT/'mlflow.json')
    start=time.monotonic();last=[0.]
    def tick():
        require_ac()
        if time.monotonic()-last[0]>15:build.resource_check();last[0]=time.monotonic()
        if time.monotonic()-start>r['seconds'] or torch.cuda.max_memory_reserved()>r['gpu_bytes']:raise ValueError('Scientific resource cap')
    def track(row):
        if row['event']=='update':client.log_metric(runid,'train/loss',row['loss'],timestamp=row['utc_ms'],step=row['step'])
        elif row['event']=='verifier_tune':client.log_metric(runid,'tune/patient_balanced_bce',row['patient_balanced_bce'],timestamp=row['utc_ms'],step=row['step'])
    try:
        dataset=Dataset(r['dataset_manifest'],r['dataset_sha256']);c=r['configuration'];session=Session(dataset,seed=c['seed'],batch_size=c['batch_size'],lr=c['learning_rate'])
        result=execute(session,OUT/'execution',epochs=c['epochs'],tick=tick,backup=backup,track=track)
        write_json(OUT/'result.json',result);client.log_artifact(runid,str(OUT/'result.json'));client.set_terminated(runid,'FINISHED')
    except BaseException:
        client.set_terminated(runid,'FAILED');raise

def run(pin,explicit=False):
    if not explicit:raise ValueError('Explicit scientific launch approval required')
    if OUT.exists() or BACKUP.exists() or (BASE/'scientific-dispatch.json').exists():raise ValueError('Already started; no automatic retry')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        r=check(pin);build.resource_check();write_json(BASE/'scientific-dispatch.json',dict(ready_sha256=pin,utc_ms=int(time.time()*1000)))
        with (BASE/'scientific-worker.log').open('x') as log:
            env=dict(os.environ,CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_VERIFIER_SCIENCE_SHA=pin);env.pop('CUDA_VISIBLE_DEVICES',None)
            p=subprocess.Popen([sys.executable,__file__,'--worker',pin],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            success=False
            try:watch_windows(p,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=require_ac);success=True
            finally:write_json(BASE/'scientific-resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--freeze',action='store_true');g.add_argument('--launch-sha256');g.add_argument('--worker');ap.add_argument('--explicit-user-launch',action='store_true');a=ap.parse_args()
    if a.freeze:freeze()
    elif a.worker:worker(a.worker)
    else:run(a.launch_sha256,a.explicit_user_launch)
