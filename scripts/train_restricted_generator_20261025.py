"""One qualified restricted-cohort generator. No auto-launch, retry or resume."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import qualify_restricted_generator as qual
from scripts.diagnostics import setup_fast_varied as shared
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,durable_replace,require_ac
read,write=shared.read,shared.write
SETUP=Path('E:/PROWL/readiness/verifier-generator-launch-20261025-a01')
NAME='pants_reserved_verifier_generator_24k_20261025'
TITLE='Candidate generator with reserved verifier patients'
OUT=Path('E:/PROWL/artifacts')/NAME
BACKUP=Path('C:/Users/quinn/PROWL-Backups')/NAME
MONITOR=Path('C:/Users/quinn/PROWL-Monitor')
URI='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db'


def configuration():
    c=deepcopy(read(qual.PARENT_SETUP/'configuration.json'))
    c['_experiment']=dict(name=NAME,run=dict(max_updates=24000,checkpoint_every=500,validate_every=None))
    c['restricted_generator']=dict(train_cases=800,reserved_cases=533,development_cases=70,
        selection='fixed_terminal_no_heldout_selection',evaluation_enabled=False,
        scope='design-informed exploratory pancreas-assisted generator; unknown SuPreM pretraining membership')
    return c


def qualification_gate():
    qual.check();qual.parent_gate()
    for stage in ('producer','cold'):
        r=read(qual.OUT/(stage+'-resources.json'))
        if not r.get('success') or r.get('exit_code')!=0 or not r.get('workers_reaped'):
            raise ValueError('Qualification not successful/reaped: '+stage)
        if not read(qual.OUT/(stage+'.json'))['passed']:raise ValueError('Qualification quality failure')
    cold=read(qual.OUT/'cold.json');producer=read(qual.OUT/'producer.json')
    if not cold['exact_restore'] or not cold['exact_next_input'] or not cold['comparison']['passes_original_bound']:
        raise ValueError('Cold replay gate')
    if sha256(qual.BACKUP/'saved-four.pt')!=producer['saved_four_sha256']:
        raise ValueError('Qualification independent backup changed')
    if sha256(qual.OUT/'execution/terminal.pt')!=producer['expected_terminal_sha256']:
        raise ValueError('Qualification expected state changed')


def dashboard_configs(active,registry):
    registry=deepcopy(registry)
    previous=registry.get('pending_run')
    if previous and previous['root']!=str(OUT):
        if not any(r['root']==previous['root'] for r in registry['runs']):registry['runs'].insert(0,previous)
    registry['pending_run']=dict(id=NAME,title=TITLE,root=str(OUT),native_files=[],
        metric_scope='generator_no_development_selection',preparation_root=str(SETUP))
    current=dict(title=TITLE,journal=str(OUT/'execution/history.jsonl'),target_steps=24000,
        metric_scope='generator_no_development_selection',
        cohort_summary='800 generator training / 533 reserved | 24k | Fixed terminal checkpoint; no development Dice selection')
    return current,registry


def prepare():
    if SETUP.exists():raise ValueError('Launch preparation exists; no overwrite')
    qualification_gate();shared.resources()
    p=qual.provider()
    try:
        if len(p.control['train'])!=800 or len(p.control['validation'])!=70:raise ValueError('Role counts')
        SETUP.mkdir()
        write(SETUP/'configuration.json',configuration())
        write(SETUP/'input-control.json',p.control)
        active=read(MONITOR/'active-run.json');registry=read(MONITOR/'experiments.json')
        a,r=dashboard_configs(active,registry)
        write(SETUP/'dashboard-handoff.json',dict(before_hashes={str(MONITOR/n):sha256(MONITOR/n) for n in ('active-run.json','experiments.json')},active=a,registry=r))
        write(SETUP/'preparation.json',dict(status='PREPARED_NOT_FROZEN',control_sha256=p.pin,
              qualification_request_sha256=sha256(qual.OUT/'request.json'),scientific_updates=0))
    finally:p.close()


def freeze():
    if (SETUP/'ready.json').exists():raise ValueError('Already frozen')
    qualification_gate();shared.resources()
    if read(SETUP/'configuration.json')!=configuration():raise ValueError('Scientific recipe changed')
    import xml.etree.ElementTree as ET
    suite=ET.parse(SETUP/'tests-verified.xml').getroot()
    suites=list(suite.iter('testsuite'))
    if not suites or any(int(s.get(k,'0')) for s in suites for k in ('failures','errors')) or sum(int(s.get('tests','0')) for s in suites)<10:
        raise ValueError('Passing launch tests required')
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    files += [ROOT/'tests/test_restricted_generator_launch_20261025.py',SETUP/'tests-verified.xml',
              MONITOR/'experiments.py',MONITOR/'index.html']
    files += list(MONITOR.glob('test_*.py'))
    files += list(SETUP.glob('*.json'))+list(qual.OUT.glob('*.json'))
    files += [qual.OUT/'execution/history.jsonl',qual.OUT/'execution/terminal.pt',qual.BACKUP/'saved-four.pt',
              ROOT/'docs/capstone/operations/PANTS-VERIFIER-GENERATOR-20261023.md']
    pins=dict(read(qual.PARENT_SETUP/'ready.json')['pins'])
    pins.update(read(qual.OUT/'request.json')['pins'])
    for path in files:
        value=sha256(path)
        if str(path) in pins and pins[str(path)]!=value:raise ValueError('Conflicting inherited pin')
        pins[str(path)]=value
    write(SETUP/'ready.json',dict(status='READY_REQUIRES_EXPLICIT_USER_LAUNCH',pins=pins,
        environment=shared.parent.environment(),control_sha256=read(SETUP/'preparation.json')['control_sha256'],
        configuration_sha256=sha256(SETUP/'configuration.json'),scientific_updates=0,
        automatic_dispatch=False,seconds=345600,rss_bytes=12*1024**3))
    print(sha256(SETUP/'ready.json'))


def admission(pin,approved):
    if not approved:raise ValueError('Explicit scientific launch approval required')
    if sha256(SETUP/'ready.json')!=pin:raise ValueError('Ready receipt hash mismatch')
    r=read(SETUP/'ready.json')
    if r['status']!='READY_REQUIRES_EXPLICIT_USER_LAUNCH':raise ValueError('Invalid readiness state')
    if OUT.exists() or BACKUP.exists() or (SETUP/'dispatch.json').exists():raise ValueError('No duplicate/retry/resume')
    shared.parent.check(r);qualification_gate();shared.resources()
    return r


def copy_backup(path):
    shared.resources();destination=BACKUP/path.name;temporary=destination.with_suffix(destination.suffix+'.partial')
    if path.stat().st_dev==BACKUP.stat().st_dev:raise ValueError('Independent backup required')
    if shared.parent.tree_bytes(shared.parent.BACKUP_ROOT)+path.stat().st_size>27917287424:raise ValueError('Backup cap')
    with path.open('rb') as a,temporary.open('xb') as b:
        shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
    if sha256(path)!=sha256(temporary):raise ValueError('Backup mismatch')
    durable_replace(temporary,destination)


def run_session(session,provider,output,tracker,backup,tick):
    from src.training.verifier_generator_executor_v1 import execute
    def hook(path):backup(path);backup(path.parent/'history.jsonl')
    return execute(session,provider,output,checkpoint_every=500,track=tracker,checkpoint_hook=hook,tick=tick)


def worker(rid):
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.segmenter_live_tracking_v1 import Tracker
    receipt=read(SETUP/'ready.json');shared.parent.check(receipt)
    if read(SETUP/'live-tracking.json')['run_id']!=rid or read(SETUP/'dispatch.json')['receipt_sha256']!=sha256(SETUP/'ready.json'):
        raise ValueError('Dispatch identity mismatch')
    p=qual.provider()
    try:
        if p.pin!=receipt['control_sha256']:raise ValueError('Provider identity')
        p.enable_prefetch();OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
        for name in ('configuration.json','input-control.json','ready.json'):
            shutil.copyfile(SETUP/name,OUT/name);copy_backup(OUT/name)
        with (OUT/'resolved.yaml').open('x') as f:yaml.safe_dump(read(SETUP/'configuration.json'),f,sort_keys=True)
        copy_backup(OUT/'resolved.yaml')
        (OUT/'splits').mkdir()
        with (OUT/'splits/train_ids.txt').open('x') as f:f.write('\n'.join(p.control['train'])+'\n')
        copy_backup(OUT/'splits/train_ids.txt')
        write(OUT/'tracking.json',dict(run_id=rid,tracking_uri=URI));copy_backup(OUT/'tracking.json')
        c=read(SETUP/'configuration.json');torch.set_num_threads(2)
        s=FastVariedSession(Session(c['session'],p.control,device='cuda',initialization=c['initialization']))
        if torch.are_deterministic_algorithms_enabled() or torch.backends.cudnn.deterministic or sum(isinstance(m,torch.nn.Upsample) for m in s.raw.model.modules())!=3:
            raise ValueError('Production numerical mode/architecture changed')
        tracker=Tracker(rid,OUT);last=[0.]
        def tick():
            if time.monotonic()-last[0]>30:shared.resources();last[0]=time.monotonic()
        result=run_session(s,p,OUT/'execution',tracker,copy_backup,tick)
        write(OUT/'result.json',result);copy_backup(OUT/'result.json');copy_backup(OUT/'execution/history.jsonl')
    finally:p.close()


def launch(pin,approved=False):
    r=admission(pin,approved)
    from mlflow import MlflowClient
    from mlflow.entities import Param
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        admission(pin,approved)
        write(SETUP/'dispatch.json',dict(receipt_sha256=pin,explicit_user_launch=True,utc_ms=int(time.time()*1000)))
        client=MlflowClient(tracking_uri=URI)
        experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
        if experiment is None:raise ValueError('Existing MLflow experiment missing')
        run=client.create_run(experiment.experiment_id,tags={'mlflow.runName':TITLE,
            'scope':'restricted_generator_design_informed_exploratory','receipt_sha256':pin,
            'selection':'fixed_terminal_24000_no_development_evaluation','purpose':'generate_candidates_for_reserved_verifier_patients'})
        rid=run.info.run_id;write(SETUP/'live-tracking.json',dict(run_id=rid,tracking_uri=URI))
        try:
            values=dict(read(SETUP/'configuration.json')['session'],train_cases=800,reserved_cases=533,development_evaluated=0)
            client.log_batch(rid,params=[Param(k,str(v)) for k,v in values.items()])
            for f in ('ready.json','configuration.json','input-control.json'):client.log_artifact(rid,str(SETUP/f),'provenance')
            with (SETUP/'scientific.log').open('x') as log:
                env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_RESTRICTED_SCIENTIFIC='1')
                env.pop('CUDA_VISIBLE_DEVICES',None);env.pop('CUBLAS_WORKSPACE_CONFIG',None)
                process=subprocess.Popen([sys.executable,__file__,'--worker',rid],cwd=ROOT,env=env,
                    stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                success=False
                try:watch_windows(process,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=require_ac);success=True
                finally:write(SETUP/'scientific-resources.json',dict(getattr(process,'duration_resources',{}),success=success,exit_code=process.returncode))
            result=read(OUT/'result.json')
            if result['completed_updates']!=24000 or result['development_cases_evaluated']!=0:raise ValueError('Scientific completion accounting')
            for f in (OUT/'result.json',OUT/'execution/history.jsonl'):client.log_artifact(rid,str(f),'results')
            client.set_tag(rid,'tracking_health','degraded_requires_journal_backfill' if (OUT/'tracking-warning.json').exists() else 'healthy')
            client.set_terminated(rid,'FINISHED')
        except BaseException:client.set_terminated(rid,'FAILED');raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--freeze',action='store_true')
    g.add_argument('--launch-sha256');g.add_argument('--worker');parser.add_argument('--explicit-user-launch',action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.freeze:freeze()
    elif args.launch_sha256:launch(args.launch_sha256,args.explicit_user_launch)
    else:
        if os.environ.get('PROWL_RESTRICTED_SCIENTIFIC')!='1':raise ValueError('Supervisor required')
        worker(args.worker)
