"""Qualified equivalent-throughput successor; explicit one-shot launch only."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import yaml
from scripts.diagnostics import setup_fast_varied as setup
from scripts.diagnostics import qualify_fast_varied as qualification
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,require_ac,durable_replace

SETUP=setup.SETUP
NAME=setup.varied.NAME
OUT=setup.varied.OUT
BACKUP=setup.varied.BACKUP
SPEC=qualification.SPEC
read,write=setup.read,setup.write


def cfg():
    value=deepcopy(setup.varied.cfg());value['throughput_policy']=read(SPEC)['throughput_policy']
    return value


def parent_binding():
    setup.check_pins()
    p=setup.varied.parent.provider()
    summary=setup.varied.completion_evidence(setup.parent.OUT,setup.parent.SETUP,p.control['validation'])
    con=sqlite3.connect('file:C:/Users/quinn/PROWL-Tracking/mlflow.db?mode=ro',uri=True)
    status=con.execute('SELECT status FROM runs WHERE run_uuid=?',('1edf56ad4b7b48a5a5baa0e729e46a5c',)).fetchone();con.close()
    if status!=('FINISHED',):raise ValueError('Parent tracking not FINISHED')
    files=list((setup.parent.OUT/'execution').glob('*.pt'))+list((setup.parent.OUT/'execution').glob('native-*.json'))
    files += [setup.parent.OUT/'execution/history.jsonl',setup.parent.OUT/'result.json']
    if len(list((setup.parent.OUT/'execution').glob('*.pt')))!=15:raise ValueError('Parent checkpoint inventory')
    for f in files:
        if sha256(f)!=sha256(setup.parent.BACKUP/f.name):raise ValueError('Parent backup differs: '+f.name)
    pins={str(f):sha256(f) for f in files+[setup.parent.SETUP/'scientific-resources.json']}
    write(SETUP/'parent-comparison.json',dict(summary,pins=pins,parent_mlflow_status='FINISHED',independent_backups_match=True))


def prepare():
    setup.check_pins();setup.resources()
    if (SETUP/'configuration.json').exists() or (SETUP/'parent-comparison.json').exists():raise ValueError('Preparation already started')
    original=setup.varied.cfg();candidate=cfg()
    if {k:v for k,v in candidate.items() if k!='throughput_policy'}!=original:raise ValueError('Scientific configuration changed')
    parent_binding()
    write(SETUP/'configuration.json',candidate)
    with (SETUP/'resolved.yaml').open('x') as f:yaml.safe_dump(candidate,f)
    monitor=Path('C:/Users/quinn/PROWL-Monitor');registry=read(monitor/'experiments.json')
    current=registry['pending_run'];registry['runs']=[current]+[r for r in registry['runs'] if r['id']!=current['id']]
    registry['pending_run']=dict(id='varied-lesion-focus',title=read(SPEC)['title'],root=str(OUT),
        preparation_root=str(SETUP),metric_scope='native_pancreas_assisted',
        native_files=[dict(label='Selected',path='execution/native-selected.json'),dict(label='Final',path='execution/native-terminal.json')])
    active=dict(title=read(SPEC)['title'],cohort_summary='SuPreM + DiceFocal | 1,333 training / 70 development | 24k | Varied lesion-focused views with complete coverage | Equivalent faster inputs',
        metric_scope='native_pancreas_assisted',preparation_kind='pancreas_region',target_steps=24000,journal=str(OUT/'execution/history.jsonl'))
    write(SETUP/'dashboard-handoff.json',dict(status='PREPARED_NOT_APPLIED',
        existing_pins={str(monitor/n):sha256(monitor/n) for n in ('active-run.json','experiments.json')},
        experiments=registry,active_run=active,retain_private_access=True,journal_derived_hours=True))


def gates():
    setup.check_pins();setup.resources()
    for stage in ('pilot','cache-complete','cuda-reference','cuda-producer','cuda-cold'):
        resource=read(SETUP/(stage+'-resources.json'))
        if not resource['workers_reaped']:raise ValueError('Unreaped stage: '+stage)
        if stage.startswith('cuda-') and (not resource.get('success') or resource.get('exit_code')!=0):
            raise ValueError('Failed qualification stage: '+stage)
    if not read(SETUP/'pilot/result.json')['passed'] or not read(SETUP/'cache-complete/result.json')['completed']:
        raise ValueError('Incomplete input qualification')
    if not read(SETUP/'cuda/producer.json')['speed_gate_passed'] or not read(SETUP/'cuda/cold.json')['exact_next_input']:
        raise ValueError('CUDA qualification failed')
    visual=read(SETUP/'visual-review.json')
    if not visual['accepted'] or visual['reviewed_cases']!=12:raise ValueError('Visual qualification missing')
    for row in visual['findings']:
        if sha256(SETUP/'pilot'/row['figure'])!=row['sha256']:raise ValueError('Reviewed image changed')
    for file,pin in read(SETUP/'parent-comparison.json')['pins'].items():
        if sha256(file)!=pin:raise ValueError('Parent comparison changed')
    for request in ('pilot-request.json','cache-complete-request.json','cuda-request.json'):
        for file,pin in read(SETUP/request)['pins'].items():
            if sha256(file)!=pin:raise ValueError('Qualified producer changed: '+file)
    import xml.etree.ElementTree as ET
    suites=ET.parse(SETUP/'tests-final.xml').getroot().findall('testsuite')
    if not suites or any(int(s.get('failures',0))+int(s.get('errors',0))+int(s.get('skipped',0)) for s in suites):
        raise ValueError('Regression tests not all passed')


def freeze():
    gates();p=setup.provider(prefetch=False)
    try:
        if len(p.control['train'])!=1333 or len(p.control['validation'])!=70 or p.control.get('qualification_only'):
            raise ValueError('Scientific roles not restored')
        if cfg()!=read(SETUP/'configuration.json'):raise ValueError('Configuration changed')
        # Recheck cache members without reading CT or rerunning a cohort audit.
        for name in p.control['train']:p.cache_member(name)
        files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'configs').rglob('*.yaml'))
        files+=list((ROOT/'tests').glob('test_fast_varied*.py'))+[SPEC,setup.varied.SPEC]
        files+=list(SETUP.glob('*.json'))+list(SETUP.glob('*.yaml'))+list(SETUP.glob('*.xml'))
        files+=list((SETUP/'cuda').glob('*.json'))+list((SETUP/'cuda').glob('*.pt'))
        files+=[SETUP/'cuda/execution/history.jsonl',SETUP/'pilot/result.json',SETUP/'cache-complete/result.json',qualification.BACKUP/'saved.pt']
        files+=list(setup.CACHE.glob('*.json'))+list(setup.CACHE.glob('*.npz'))
        pins={**read(setup.varied.SETUP/'setup.json')['pins'],**{str(f):sha256(f) for f in files}}
        write(SETUP/'ready.json',dict(status='READY_AWAITING_USER_LAUNCH',scientific_launch_authorized=False,
            requires_explicit_user_launch=True,pins=pins,environment=setup.parent.environment(),control_sha256=p.pin,
            configuration_sha256=sha256(SETUP/'configuration.json'),scientific_updates=0))
        print(sha256(SETUP/'ready.json'))
    finally:p.close()


def check_ready(pin,*,user_launch=False):
    if sha256(SETUP/'ready.json')!=pin:raise ValueError('Receipt mismatch')
    receipt=read(SETUP/'ready.json')
    if receipt['status']!='READY_AWAITING_USER_LAUNCH' or not user_launch:raise ValueError('Explicit subsequent user launch required')
    setup.parent.check(receipt);gates()
    if OUT.exists() or BACKUP.exists() or (SETUP/'dispatch.json').exists():raise ValueError('No duplicate, retry or resume')
    return receipt


def copy_backup(path):
    setup.resources();destination=BACKUP/path.name;temporary=destination.with_suffix(destination.suffix+'.partial')
    if setup.parent.tree_bytes(setup.parent.BACKUP_ROOT)+path.stat().st_size>27917287424:raise ValueError('Backup cap')
    with path.open('rb') as a,temporary.open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
    if sha256(path)!=sha256(temporary):raise ValueError('Backup hash mismatch')
    durable_replace(temporary,destination)


def scientific_worker(rid):
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.segmenter_pancreas_region_executor_v1 import execute
    from src.training.segmenter_live_tracking_v1 import Tracker
    receipt=read(SETUP/'ready.json');setup.parent.check(receipt)
    if read(SETUP/'live-tracking.json')['run_id']!=rid or read(SETUP/'dispatch.json')['receipt_sha256']!=sha256(SETUP/'ready.json'):
        raise ValueError('Scientific dispatch binding')
    p=setup.provider()
    try:
        if p.pin!=receipt['control_sha256']:raise ValueError('Input control changed')
        OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
        if OUT.stat().st_dev==BACKUP.stat().st_dev:raise ValueError('Independent backups required')
        for name in ('resolved.yaml','ready.json','parent-comparison.json'):
            shutil.copyfile(SETUP/name,OUT/name);copy_backup(OUT/name)
        (OUT/'splits').mkdir()
        for role,name in (('train','train_ids.txt'),('validation','development_ids.txt')):
            path=OUT/'splits'/name
            with path.open('x') as f:f.write('\n'.join(p.control[role])+'\n')
            copy_backup(path)
        write(OUT/'input-control.json',p.control);write(OUT/'tracking.json',dict(run_id=rid,tracking_uri=setup.parent.URI))
        c=cfg();torch.set_num_threads(2)
        s=FastVariedSession(Session(c['session'],p.control,device='cuda',initialization=c['initialization']))
        last=[0.]
        def tick():
            if time.monotonic()-last[0]>30:setup.resources();last[0]=time.monotonic()
        def hook(path):copy_backup(path);copy_backup(path.parent/'history.jsonl')
        result=execute(s,p,OUT/'execution',tick=tick,checkpoint_hook=hook,track=Tracker(rid,OUT))
        p.close()  # All owned input work is drained before final closeout.
        write(OUT/'result.json',result);copy_backup(OUT/'result.json')
        copy_backup(OUT/'execution/history.jsonl')  # Includes final completion events.
    finally:p.close()


def launch(pin,*,user_launch=False):
    check_ready(pin,user_launch=user_launch)
    from mlflow import MlflowClient
    from mlflow.entities import Param
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        write(SETUP/'dispatch.json',dict(receipt_sha256=pin,explicit_user_launch=True,utc_ms=int(time.time()*1000)))
        client=MlflowClient(tracking_uri=setup.parent.URI)
        experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
        if experiment is None:raise ValueError('Existing MLflow experiment missing')
        run=client.create_run(experiment.experiment_id,tags={'mlflow.runName':read(SPEC)['title'],
            'scope':'provided_pancreas_assisted_native_development','receipt_sha256':pin,
            'parent_run_id':read(setup.varied.SPEC)['parent_mlflow_run_id'],
            'changed_factor':'focused_training_windows_only','throughput':'qualified_exact_equivalent_target_cache_prefetch'})
        rid=run.info.run_id;write(SETUP/'live-tracking.json',dict(run_id=rid,tracking_uri=setup.parent.URI))
        try:
            client.log_batch(rid,params=[Param(k,str(v)) for k,v in dict(cfg()['session'],
                input_policy=read(SPEC)['throughput_policy'],train_cases=1333,development_cases=70,
                validate_every=2000,pancreas_assistance=True,lesion_guided_development_crop=False).items()])
            for f in (SPEC,setup.varied.SPEC,SETUP/'ready.json',SETUP/'parent-comparison.json'):
                client.log_artifact(rid,str(f),'provenance')
            with (SETUP/'scientific.log').open('x') as log:
                env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_FAST_SCIENTIFIC='1');env.pop('CUDA_VISIBLE_DEVICES',None)
                process=subprocess.Popen([sys.executable,__file__,'--worker',rid],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=env)
                try:watch_windows(process,seconds=345600,rss_bytes=12*1024**3,tick=require_ac)
                finally:write(SETUP/'scientific-resources.json',getattr(process,'duration_resources',{}))
            client.set_tag(rid,'tracking_health','degraded_requires_journal_backfill' if (OUT/'tracking-warning.json').exists() else 'healthy')
            for f in (OUT/'result.json',OUT/'execution/history.jsonl',OUT/'execution/native-selected.json',OUT/'execution/native-terminal.json'):
                client.log_artifact(rid,str(f),'results')
            client.set_terminated(rid,'FINISHED')
        except BaseException:client.set_terminated(rid,'FAILED');raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--freeze',action='store_true')
    g.add_argument('--launch-sha256');g.add_argument('--worker');parser.add_argument('--explicit-user-launch',action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.freeze:freeze()
    elif args.launch_sha256:launch(args.launch_sha256,user_launch=args.explicit_user_launch)
    else:
        if os.environ.get('PROWL_FAST_SCIENTIFIC')!='1':raise ValueError('Supervisor required')
        scientific_worker(args.worker)
