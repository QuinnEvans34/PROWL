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
from scripts.diagnostics import qualify_varied_deterministic_v2 as qualification
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,require_ac,durable_replace

SETUP=qualification.SETUP
NAME=setup.varied.NAME
OUT=setup.varied.OUT
BACKUP=setup.varied.BACKUP
SPEC=ROOT/'docs/capstone/operations/PANTS-VARIED-FOCUS-FAST-24K-20261022.json'
AMENDMENT=qualification.SPEC
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
    if (SETUP/'configuration.json').exists():raise ValueError('Preparation already started')
    for name in ('configuration.json','resolved.yaml','parent-comparison.json','dashboard-handoff.json'):
        source=setup.SETUP/name
        with source.open('rb') as a,(SETUP/name).open('xb') as b:shutil.copyfileobj(a,b)
        if sha256(source)!=sha256(SETUP/name):raise ValueError('Prepared evidence copy mismatch')
    write(SETUP/'launch-authority.json',dict(single_run=NAME,authorized=True,
        instruction='User: Work autonomously until we can start training; get training running soon.',
        amendment_sha256=sha256(AMENDMENT),automatic_retry_resume=False,schedules=False))


def successful_stage(root,stage):
    value=read(root/(stage+'-resources.json'))
    if not value.get('success') or value.get('exit_code')!=0 or not value.get('workers_reaped'):
        raise ValueError('Stage did not succeed/reap: '+stage)


def passed_tests(path):
    import xml.etree.ElementTree as ET
    suites=ET.parse(path).getroot().findall('testsuite')
    if not suites or sum(int(s.get('tests',0)) for s in suites)<1 or any(
        int(s.get('failures',0))+int(s.get('errors',0))+int(s.get('skipped',0)) for s in suites):
        raise ValueError('Regression evidence not all passed')


def gates():
    qualification.check();setup.resources()
    for stage in qualification.STAGES:successful_stage(SETUP,stage)
    producer=read(SETUP/'producer.json')
    if not producer['exact_inputs'] or not producer['state_comparison']['passes_original_bound']:
        raise ValueError('Deterministic equivalence not passed')
    for stage in ('cold','production-cold'):
        value=read(SETUP/(stage+'.json'))
        if not value['exact_restore'] or not value['exact_next_input'] or not value['state_comparison']['passes_original_bound']:
            raise ValueError('Cold restore not passed: '+stage)
    if sha256(SETUP/'saved.pt')!=sha256(qualification.BACKUP/'saved.pt'):
        raise ValueError('Independent deterministic backup changed')
    source=setup.SETUP
    for stage in ('pilot','cache-complete'):
        if not read(source/(stage+'-resources.json'))['workers_reaped']:raise ValueError('Old worker not reaped')
    cache=read(source/'cache-complete/result.json')
    if not cache['completed'] or cache['cases']!=1333 or cache['new_exclusions']!=0:
        raise ValueError('Incomplete cache')
    if not read(source/'pilot/result.json')['passed']:raise ValueError('Pilot failed')
    visual=read(source/'visual-review.json')
    if not visual['accepted'] or visual['reviewed_cases']!=12:raise ValueError('Visual qualification missing')
    for row in visual['findings']:
        if sha256(source/'pilot'/row['figure'])!=row['sha256']:raise ValueError('Reviewed image changed')
    native=read(source/'cuda/execution/native-000033.json')
    if len(native['cases'])!=2:raise ValueError('Original production native-path evidence incomplete')
    failed=read(source/'cuda-producer-resources.json')
    if failed['success'] or failed['exit_code']!=1 or not failed['workers_reaped']:
        raise ValueError('Original failed qualification not preserved')
    if read(source/'failure-review.json')['observed_update_speedup']<1.10:
        raise ValueError('Original actual-path speed gate')
    for root,request in [(source,n) for n in ('pilot-request.json','cache-complete-request.json','cuda-request.json')]+[
        (source/'original-repeatability-a01','request.json'),
        (Path('E:/PROWL/readiness/varied-deterministic-20261022-a01'),'request.json')]:
        for path,pin in read(root/request)['pins'].items():
            if sha256(path)!=pin:raise ValueError('Preserved producer changed: '+path)
    for path,pin in read(SETUP/'parent-comparison.json')['pins'].items():
        if sha256(path)!=pin:raise ValueError('Parent comparison changed')
    for path in (source/'tests-final.xml',source/'dashboard-tests.xml',
                 source/'deterministic-adapter-v2-tests.xml',SETUP/'launch-tests.xml'):
        passed_tests(path)
    if not read(SETUP/'launch-authority.json')['authorized']:raise ValueError('No one-run authority')

def freeze():
    gates();p=setup.provider(prefetch=False)
    try:
        if len(p.control['train'])!=1333 or len(p.control['validation'])!=70 or p.control.get('qualification_only'):
            raise ValueError('Scientific roles not restored')
        if cfg()!=read(SETUP/'configuration.json'):raise ValueError('Configuration changed')
        # Recheck cache members without reading CT or rerunning a cohort audit.
        for name in p.control['train']:p.cache_member(name)
        files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'configs').rglob('*.yaml'))
        files+=list((ROOT/'tests').glob('test_fast_varied*.py'))+list((ROOT/'tests').glob('test_varied_qualified*.py'))+[SPEC,setup.varied.SPEC,AMENDMENT]
        files+=list(SETUP.glob('*.json'))+list(SETUP.glob('*.yaml'))+list(SETUP.glob('*.xml'))
        files+=list(SETUP.glob('*.pt'))+list(SETUP.glob('*-updates.jsonl'))
        files+=list(setup.SETUP.glob('*.json'))+list(setup.SETUP.glob('*.xml'))
        files+=list((setup.SETUP/'original-repeatability-a01').glob('*.json'))
        files+=[setup.SETUP/'cuda/execution/history.jsonl',setup.SETUP/'cuda/execution/native-000033.json',
                setup.SETUP/'pilot/result.json',setup.SETUP/'cache-complete/result.json',qualification.BACKUP/'saved.pt']
        for request in (SETUP/'request.json',setup.SETUP/'cuda-request.json',
                        Path('E:/PROWL/readiness/varied-deterministic-20261022-a01/request.json')):
            files.extend(Path(p) for p in read(request)['pins'])
        files+=list(setup.CACHE.glob('*.json'))+list(setup.CACHE.glob('*.npz'))
        pins={**read(setup.varied.SETUP/'setup.json')['pins'],**{str(f):sha256(f) for f in files}}
        write(SETUP/'ready.json',dict(status='READY_AUTHORIZED_ONE_RUN',scientific_launch_authorized=True,
            requires_explicit_user_launch=True,pins=pins,environment=setup.parent.environment(),control_sha256=p.pin,
            configuration_sha256=sha256(SETUP/'configuration.json'),scientific_updates=0))
        print(sha256(SETUP/'ready.json'))
    finally:p.close()


def check_ready(pin,*,user_launch=False):
    if sha256(SETUP/'ready.json')!=pin:raise ValueError('Receipt mismatch')
    receipt=read(SETUP/'ready.json')
    if receipt['status']!='READY_AUTHORIZED_ONE_RUN' or not user_launch:raise ValueError('Explicit subsequent user launch required')
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
        if torch.are_deterministic_algorithms_enabled() or torch.backends.cudnn.deterministic:
            raise ValueError('Scientific numerical settings must remain original')
        if sum(isinstance(m,torch.nn.Upsample) for m in s.raw.model.modules())!=3:
            raise ValueError('Qualification adapter must NOT enter scientific model')
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
            'changed_factor':'focused_training_windows_only','throughput':'equivalent_inputs_controlled_numerics_and_production_cold_qualified',
            'qualification_note':'Paired deterministic CUDA with native CPU trilinear adjoint; production unchanged',
            'ordinary_gpu_reproducibility':'known_nondeterministic_trilinear_backward'})
        rid=run.info.run_id;write(SETUP/'live-tracking.json',dict(run_id=rid,tracking_uri=setup.parent.URI))
        try:
            client.log_batch(rid,params=[Param(k,str(v)) for k,v in dict(cfg()['session'],
                input_policy=read(SPEC)['throughput_policy'],train_cases=1333,development_cases=70,
                validate_every=2000,pancreas_assistance=True,lesion_guided_development_crop=False).items()])
            for f in (SPEC,setup.varied.SPEC,AMENDMENT,SETUP/'ready.json',SETUP/'parent-comparison.json'):
                client.log_artifact(rid,str(f),'provenance')
            with (SETUP/'scientific.log').open('x') as log:
                env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_FAST_SCIENTIFIC='1');env.pop('CUDA_VISIBLE_DEVICES',None);env.pop('CUBLAS_WORKSPACE_CONFIG',None)
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


