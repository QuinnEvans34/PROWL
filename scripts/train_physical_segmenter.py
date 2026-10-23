"""One receipt-gated full-coverage run; separate smoke, no retries or resume."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import durable_replace,require_ac,training_guard,watch_windows
from scripts.diagnostics.qualify_physical_intake import provider,verify as verify_intake
from scripts.diagnostics.setup_pants_augmentation import configuration,environment
from scripts.train_full_segmenter import session_config,tree_bytes
from scripts.diagnostics.backfill_full_runs_mlflow import URI

SPEC=ROOT/'docs/capstone/operations/PANTS-FULL-COVERAGE-24K-20261018.json'
SETUP=Path('E:/PROWL/readiness/pants-full-coverage-24k-20261018-a01')
NAME='pants_full_coverage_physical_24k_20261018'
OUT=Path('E:/PROWL/artifacts')/NAME
BACKUP_ROOT=Path('C:/Users/quinn/PROWL-Backups')
BACKUP=BACKUP_ROOT/NAME


def read(path):return json.loads(Path(path).read_text())
def write_new(path,value):
    with Path(path).open('xb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())


def verify_qualification():
    spec=read(SPEC);p=Path(spec['qualification'])
    if sha256(p)!=spec['qualification_sha256']:raise ValueError('Qualification receipt changed')
    r=read(p)
    for path,pin in {**r['file_sha256'],**r['checkpoint_sha256']}.items():
        if sha256(path)!=pin:raise ValueError('Qualified source/evidence changed: '+path)
    verify_intake()
    inputs=provider()
    if len(inputs.control['train'])!=1333 or len(inputs.control['validation'])!=70:raise ValueError('Wrong cohort')
    for name in inputs.control['train']+inputs.control['validation']:
        for kind in ('ct','pancreas','lesion'):
            s=Path(inputs.rows[name][kind+'_path']).stat()
            if dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)!=inputs.observations[name][kind]:
                raise ValueError('Qualified source observation changed')
    return spec,inputs


def resolved():
    spec=read(SPEC);old=configuration();session=session_config(old)
    session['max_steps']=spec['max_updates']
    return dict(session=session,initialization=old['_experiment']['initialization'],
        _experiment=dict(name=NAME,run=dict(max_updates=spec['max_updates'],validate_every=spec['validate_every'],
            checkpoint_every=spec['checkpoint_every'],max_seconds=spec['max_seconds']),
            cohort=old['_experiment']['cohort']),physical_inputs=read(SPEC)['input_policy'])


def resource_check():
    spec=read(SPEC);r=spec['resources'];require_ac()
    if any(shutil.disk_usage(d).free<r['minimum_free_bytes'] for d in ('C:/','E:/')):raise ValueError('Free-space floor')
    if tree_bytes(BACKUP_ROOT)>r['backup_cap_bytes']:raise ValueError('Backup cap')
    if tree_bytes(configuration()['full_segmenter']['cache_dir'])>r['cache_cap_bytes']:raise ValueError('Existing cache cap')


def pinned_files():
    paths=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    paths += [SPEC,ROOT/'tests/test_physical_executor.py',Path(read(SPEC)['qualification']),
        Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01/experiment.yaml'),
        Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017/execution/native-selected.json'),
        Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017/execution/native-terminal.json')]
    return {str(p):sha256(p) for p in paths}


def check_pins(receipt):
    for p,h in receipt['file_sha256'].items():
        if sha256(p)!=h:raise ValueError('Producing pin changed: '+p)
    if environment()!=receipt['environment']:raise ValueError('Runtime changed')


def prepare():
    spec,p=verify_qualification();resource_check()
    SETUP.mkdir(exist_ok=False)
    write_new(SETUP/'setup.json',dict(file_sha256=pinned_files(),environment=environment(),control_sha256=p.pin))
    with (SETUP/'resolved.yaml').open('x') as f:yaml.safe_dump(resolved(),f,sort_keys=False)
    print('Bound qualified inputs; no scientific training launched',flush=True)


def worker(smoke,run_id):
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_physical_windows_session_v1 import PhysicalSession
    from src.training.segmenter_physical_executor_v1 import execute
    from src.training.segmenter_live_tracking_v1 import Tracker
    receipt=read(SETUP/('setup.json' if smoke else 'ready.json'));check_pins(receipt)
    p=provider();cfg=resolved()
    if p.pin!=receipt['control_sha256']:raise ValueError('Control changed')
    output=SETUP/'smoke' if smoke else OUT
    backup=BACKUP_ROOT/(NAME+'-smoke') if smoke else BACKUP
    output.mkdir(exist_ok=False);backup.mkdir(exist_ok=False)
    if output.stat().st_dev==backup.stat().st_dev:raise ValueError('Independent backup required')
    last_check=[0.]
    def tick():
        if time.monotonic()-last_check[0]>30:resource_check();last_check[0]=time.monotonic()
    def copy(path):
        tick();size=path.stat().st_size
        if tree_bytes(BACKUP_ROOT)+size>read(SPEC)['resources']['backup_cap_bytes']:raise ValueError('Backup capacity')
        dest=backup/path.name;tmp=dest.with_suffix(dest.suffix+'.partial')
        with path.open('rb') as source,tmp.open('xb') as target:
            shutil.copyfileobj(source,target);target.flush();os.fsync(target.fileno())
        if sha256(path)!=sha256(tmp):raise ValueError('Backup verification')
        durable_replace(tmp,dest)
    def checkpoint_hook(path):
        copy(path);copy(path.parent/'history.jsonl')
    for filename in ('resolved.yaml','ready.json' if not smoke else 'setup.json'):
        shutil.copyfile(SETUP/filename,output/filename);copy(output/filename)
    splits=output/'splits';splits.mkdir()
    for role,filename in [('train','train_ids.txt'),('validation','development_ids.txt')]:
        (splits/filename).write_text('\n'.join(p.control[role])+'\n');copy(splits/filename)
    write_new(output/'input-control.json',p.control);copy(output/'input-control.json')
    if not smoke:write_new(output/'tracking.json',dict(run_id=run_id,tracking_uri=URI))
    torch.set_num_threads(2)
    config=cfg['session']
    names=None
    if smoke:
        config=dict(config,max_steps=2,warmup_steps=1,lr_horizon_steps=2)
        # Geometry-only bounded integration check: one positive and one empty dev case.
        records=read(Path(read(SPEC)['qualification']).parent/'summary.json')
        from scripts.diagnostics.qualify_native_intake import read_journal
        rows=read_journal(Path(read(SPEC)['qualification']).parent/'cohort/cases.jsonl')
        names=[min((r for r in rows if r['role']=='validation' and r['positive']==positive),
                   key=lambda r:r['full_field_tile_count'])['case_id'] for positive in (True,False)]
    session=PhysicalSession(Session(config,p.control,device='cuda',initialization=cfg['initialization']))
    result=execute(session,p,output/'execution',validate_every=2 if smoke else read(SPEC)['validate_every'],
        checkpoint_every=1 if smoke else read(SPEC)['checkpoint_every'],tick=tick,
        checkpoint_hook=checkpoint_hook,track=(lambda row:None) if smoke else Tracker(run_id,output),validation_names=names)
    write_new(output/'result.json',dict(result,nonpromotable=smoke));copy(output/'result.json')
    copy(output/'execution/history.jsonl')


def supervise(smoke,run_id=None):
    env=dict(os.environ,PROWL_PHYSICAL_SUPERVISED='1')
    argv=[sys.executable,str(Path(__file__).resolve()),'--worker','smoke' if smoke else 'scientific']
    if run_id:argv+=['--mlflow-run',run_id]
    stem='smoke' if smoke else 'training'
    with (SETUP/(stem+'-worker.log')).open('x') as log:
        process=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=env)
        last=[0.]
        def tick():
            if time.monotonic()-last[0]>30:resource_check();last[0]=time.monotonic()
        try:watch_windows(process,seconds=1800 if smoke else read(SPEC)['max_seconds'],rss_bytes=12*1024**3,tick=tick)
        finally:write_new(SETUP/(stem+'-resources.json'),getattr(process,'duration_resources',{}))


def freeze():
    setup=read(SETUP/'setup.json');check_pins(setup);verify_qualification()
    result=read(SETUP/'smoke/result.json');resources=read(SETUP/'smoke-resources.json')
    if result['completed_updates']!=2 or not result['nonpromotable'] or not resources['workers_reaped']:
        raise ValueError('Integration smoke incomplete')
    if resources['peak_owned_rss_bytes']>12*1024**3:raise ValueError('Smoke memory')
    for name in ('initial.pt','last.pt','best.pt','step-000002.pt'):
        if sha256(SETUP/'smoke/execution'/name)!=sha256(BACKUP_ROOT/(NAME+'-smoke')/name):raise ValueError('Smoke backup changed')
    suites=ET.parse(SETUP/'executor-tests.xml').getroot().findall('testsuite')
    if not suites or any(int(s.get('failures',0))+int(s.get('errors',0))+int(s.get('skipped',0)) for s in suites):
        raise ValueError('Integration tests incomplete')
    files=dict(setup['file_sha256'])
    for path in [SETUP/'resolved.yaml',SETUP/'executor-tests.xml',SETUP/'smoke/result.json',
                 SETUP/'smoke-resources.json',SETUP/'smoke/execution/history.jsonl']:
        files[str(path)]=sha256(path)
    write_new(SETUP/'ready.json',dict(setup,file_sha256=files,status='READY',scientific_launch_authorized=True,
                                    title=read(SPEC)['title']))
    print(json.dumps(dict(ready=str(SETUP/'ready.json'),sha256=sha256(SETUP/'ready.json'))),flush=True)


def launch(expected):
    receipt=read(SETUP/'ready.json')
    if sha256(SETUP/'ready.json')!=expected or not receipt['scientific_launch_authorized']:raise ValueError('Launch receipt mismatch')
    check_pins(receipt);verify_qualification();resource_check()
    if OUT.exists() or BACKUP.exists():raise ValueError('Scientific output already exists; no restart')
    from mlflow import MlflowClient
    from mlflow.entities import Param
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        write_new(SETUP/'dispatch.json',dict(receipt_sha256=expected,utc_ms=int(time.time()*1000)))
        client=MlflowClient(tracking_uri=URI)
        experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
        if experiment is None:raise ValueError('Existing scientific MLflow experiment missing')
        run=client.create_run(experiment.experiment_id,tags={'mlflow.runName':receipt['title'],
            'scope':'exploratory_native_full_CT_development','receipt_sha256':expected,
            'control_run_id':read(SPEC)['control_run_id'],'tracking':'live_local_journal_authoritative'})
        rid=run.info.run_id;write_new(SETUP/'live-tracking.json',dict(run_id=rid,tracking_uri=URI,status='RUNNING'))
        try:
            client.log_batch(rid,params=[Param(k,str(v)) for k,v in dict(resolved()['session'],
                input_policy='physical-detail-windows-1',train_cases=1333,development_cases=70,
                validate_every=2000,checkpoint_every=500,selection='native_full_CT_positive_macro_Dice',
                ema=False,panorama=False).items()])
            client.log_artifact(rid,str(SPEC),'provenance');client.log_artifact(rid,str(SETUP/'ready.json'),'provenance')
            supervise(False,rid)
            client.set_tag(rid,'tracking_health','degraded_requires_backfill' if (OUT/'tracking-warning.json').exists() else 'healthy')
            for path in [OUT/'result.json',OUT/'execution/history.jsonl',OUT/'execution/native-selected.json',OUT/'execution/native-terminal.json']:
                client.log_artifact(rid,str(path),'results')
            client.set_terminated(rid,'FINISHED')
        except BaseException:
            client.set_terminated(rid,'FAILED');raise


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--freeze',action='store_true');ap.add_argument('--launch-sha256');ap.add_argument('--worker',choices=['smoke','scientific']);ap.add_argument('--mlflow-run')
    a=ap.parse_args()
    if sum(bool(v) for v in (a.prepare,a.smoke,a.freeze,a.launch_sha256,a.worker))!=1:ap.error('Choose exactly one operation')
    if a.worker:
        if os.environ.get('PROWL_PHYSICAL_SUPERVISED')!='1' or (a.worker=='scientific' and not a.mlflow_run):raise ValueError('Use supervised entry')
        worker(a.worker=='smoke',a.mlflow_run)
    elif a.prepare:prepare()
    elif a.smoke:
        check_pins(read(SETUP/'setup.json'));resource_check()
        with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):supervise(True)
    elif a.freeze:freeze()
    else:launch(a.launch_sha256)
