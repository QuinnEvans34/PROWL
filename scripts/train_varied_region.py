"""One gated successor. Additive only: never mutates/restarts the current producer."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import yaml
from scripts import train_pancreas_region as parent
from src.data.manifest_records import canonical, digest
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard, watch_windows, durable_replace, require_ac
from src.data.segmenter_varied_region_v1 import VariedInputs, POLICY, planned_visits, coverage_slots

SPEC=ROOT/'docs/capstone/operations/PANTS-VARIED-FOCUS-24K-20261022.json'
SETUP=Path('E:/PROWL/readiness/varied-focus-20261022-a01')
NAME='pants_varied_focus_24k_20261022'
OUT=Path('E:/PROWL/artifacts')/NAME
BACKUP=parent.BACKUP_ROOT/NAME
read,write,check=parent.read,parent.write,parent.check


def cfg(smoke=False):
    c=deepcopy(parent.cfg());c['_experiment']['name']=NAME
    c['training_view_policy']=deepcopy(POLICY)
    if smoke:c['session'].update(max_steps=5,warmup_steps=1,lr_horizon_steps=5)
    return c


def provider(smoke=False):
    schedule=read(SETUP/'schedule.json')
    p=VariedInputs(planned_counts=schedule['focused_counts'],manifest=parent.MANIFEST,
        review=parent.SOURCE_SETUP/'cohort-review.json',train_file=parent.TRAIN,
        dev_file=parent.SOURCE_SETUP/'development.txt')
    p.control['source_loader_policy']=p.control.pop('policy')
    p.control['policy']=deepcopy(parent.POLICY)
    if smoke:
        p.control['train']=read(SETUP/'pilot-selection.json')['cuda_train']
        p.control['qualification_only']=True
    p.pin=digest(canonical(p.control))
    return p


def resource_check():
    parent.resource_check()  # Same budget, storage caps and AC requirement.
    if read(SPEC)['resources']!=read(parent.SPEC)['resources']:raise ValueError('Resource budget changed')


def parent_pins():
    if sha256(parent.SETUP/'ready.json')!=read(SPEC)['parent_receipt_sha256']:raise ValueError('Parent receipt changed')
    check(read(parent.SETUP/'ready.json'))


def prepare():
    parent_pins();resource_check();p=parent.provider()
    if p.pin!=read(parent.SETUP/'ready.json')['control_sha256']:raise ValueError('Parent input control changed')
    rows=[json.loads(s) for s in (parent.COHORT/'cases.jsonl').read_text().splitlines() if s.strip()]
    result=read(parent.COHORT/'result.json')
    if not result['completed'] or not result['all_pass'] or len(rows)!=1403 or not read(parent.COHORT/'resources.json')['workers_reaped']:
        raise ValueError('Reused coverage qualification invalid')
    by_name={r['case_id']:r for r in rows}
    if len(by_name)!=1403 or set(by_name)!=set(p.control['train']+p.control['validation']):raise ValueError('Cohort accounting')
    focused,exposure=planned_visits(p.control['train'])
    old=read(parent.SETUP/'schedule.json')
    if focused!=old['focused_counts'] or exposure!=old['exposure']:raise ValueError('Patient exposure changed')
    reservations={n:list(coverage_slots(focused[n],by_name[n]['cover_windows'])) for n in focused}
    reserved=sum(len(v) for v in reservations.values())
    # Budget conservatively for retained states, qualification copies and replacement temporaries.
    checkpoint_estimate=(parent.OUT/'execution/last.pt').stat().st_size+2*1024**2
    projected_backup=parent.tree_bytes(parent.BACKUP_ROOT)+22*checkpoint_estimate
    if projected_backup>read(SPEC)['resources']['backup_cap_bytes']:raise ValueError('Projected successor backup exceeds cap')
    schedule=dict(total_updates=24000,focused_updates=sum(focused.values()),context_updates=6000,
        focused_counts=focused,exposure=exposure,reservations=reservations,
        reserved_updates=reserved,jitter_updates=sum(focused.values())-reserved,
        all1333_banks_complete=True,zero_new_source_CT_reads=True,
        projected_backup_bytes=projected_backup,checkpoint_estimate_bytes=checkpoint_estimate)
    train=[by_name[n] for n in p.control['train']];positive=[r for r in train if r['positive']]
    empty=[r for r in train if not r['positive']]
    source_rows=[json.loads(s) for s in Path('E:/PROWL/readiness/native-intake-20261018-a02/cohort-complete/cases.jsonl').read_text().splitlines() if s.strip()]
    source={r['case_id']:r for r in source_rows};chosen=[];reasons={}
    def add(name,reason):
        if name not in chosen:chosen.append(name)
        reasons.setdefault(name,[]).append(reason)
    add('PanTS_00002720','Previously severely clipped; retained and corrected')
    for group,label in [(positive,'positive'),(empty,'empty')]:
        add(max(group,key=lambda r:r['cover_windows'])['case_id'],label+' largest coverage bank')
    add(min(positive,key=lambda r:r['lesion_total'])['case_id'],'smallest positive lesion volume in voxels')
    add(max(positive,key=lambda r:r['lesion_total'])['case_id'],'largest positive lesion volume in voxels')
    add(max(positive,key=lambda r:source[r['case_id']]['components'])['case_id'],'most lesion components')
    for row in read(parent.SETUP/'pilot/result.json')['cases']:
        if len(chosen)>=12:break
        add(row['case_id'],'previous difficult training pilot')
    if len(chosen)!=12 or not set(chosen)<=set(p.control['train']):raise ValueError('Training pilot selection')
    cuda_train=[min(group,key=lambda r:(r['cover_windows'],r['inference_tiles']))['case_id'] for group in (positive,empty)]
    validation=[max((r for r in rows if r['role']=='validation' and r['positive']==positive_value),
        key=lambda r:r['inference_tiles'])['case_id'] for positive_value in (True,False)]
    SETUP.mkdir(exist_ok=False)
    write(SETUP/'schedule.json',schedule)
    write(SETUP/'pilot-selection.json',dict(cases=chosen,reasons=reasons,cuda_train=cuda_train,validation=validation))
    with (SETUP/'resolved.yaml').open('x') as f:yaml.safe_dump(cfg(),f)
    candidate=provider();unchanged=deepcopy(candidate.control)
    for key in ('training_view_policy','planned_focused_counts'):unchanged.pop(key)
    unchanged['version']=p.control['version']
    if unchanged!=p.control:raise ValueError('Unexpected input-control change outside sampler')
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'configs').rglob('*.yaml'))
    files+=list((ROOT/'tests').glob('test_varied_region*.py'))
    files += [SPEC,SPEC.with_suffix('.md'),SETUP/'schedule.json',SETUP/'pilot-selection.json',SETUP/'resolved.yaml',
        parent.SETUP/'ready.json',parent.SETUP/'schedule.json',parent.COHORT/'cases.jsonl',parent.COHORT/'result.json',parent.COHORT/'resources.json']
    pins={**read(parent.SETUP/'ready.json')['pins'],**{str(f):sha256(f) for f in files}}
    write(SETUP/'setup.json',dict(pins=pins,environment=parent.environment(),control_sha256=candidate.pin,
        status='PREPARED_WAITING_PARENT',scientific_launch_authorized=True,
        authority='User approved one successor after current run finishes and qualification passes',automatic_retry=False))
    print(json.dumps(dict(status='PREPARED_WAITING_PARENT',reserved_updates=reserved,jitter_updates=schedule['jitter_updates'],
        all_training_banks_complete=True,parent_pins_unchanged=True)),flush=True)


def completion_evidence(root,setup,names):
    """Pure file checks, independently testable. Normal completion only, never stopped/failed."""
    root,setup=Path(root),Path(setup)
    if (root/'operator-stop.json').exists() or (setup/'pipeline-failure.json').exists():raise ValueError('Parent stopped or failed')
    result=read(root/'result.json');resources=read(setup/'scientific-resources.json')
    if result['completed_updates']!=24000 or not resources['workers_reaped']:raise ValueError('Parent incomplete or workers active')
    history=[json.loads(s) for s in (root/'execution/history.jsonl').read_text().splitlines() if s.strip()]
    if [r['step'] for r in history if r['event']=='update']!=list(range(1,24001)):raise ValueError('Parent update accounting')
    if not history or history[-1]['event']!='completed' or any(r['event']=='failed' for r in history):raise ValueError('Parent not normally completed')
    if [r['step'] for r in history if r['event']=='native_completed']!=list(range(2000,24001,2000)):raise ValueError('Parent validation cadence')
    reports=[]
    for step in range(2000,24001,2000):
        report=read(root/f'execution/native-{step:06d}.json')
        if report['step']!=step or len(report['cases'])!=len(names) or {r['case_id'] for r in report['cases']}!=set(names):raise ValueError('Incomplete parent native report')
        if report['scope']!='native_provided_pancreas_region_development' or any(r['step']!=step for r in report['cases']):raise ValueError('Parent metric scope/step changed')
        positives=[r['metrics']['lesion']['dice'] for r in report['cases'] if r['metrics']['lesion']['target_voxels']]
        if len(positives)!=36 or abs(sum(positives)/36-report['lesion_positive_macro_dice'])>1e-12:raise ValueError('Parent score mismatch')
        reports.append(report)
    best=max(reports,key=lambda r:r['lesion_positive_macro_dice'])
    selected=read(root/'execution/native-selected.json');terminal=read(root/'execution/native-terminal.json')
    if selected['step']!=best['step'] or selected['cases']!=best['cases'] or terminal['step']!=24000 or terminal['cases']!=reports[-1]['cases']:
        raise ValueError('Parent endpoint selection changed')
    return dict(selected_step=best['step'],selected_dice=best['lesion_positive_macro_dice'],
        terminal_dice=terminal['lesion_positive_macro_dice'],complete_evaluations=12,completed_updates=24000)


def bind_parent():
    from mlflow import MlflowClient
    check(read(SETUP/'setup.json'));parent_pins()
    summary=completion_evidence(parent.OUT,parent.SETUP,parent.provider().control['validation'])
    client=MlflowClient(tracking_uri=parent.URI)
    if client.get_run(read(SPEC)['parent_mlflow_run_id']).info.status!='FINISHED':raise ValueError('Parent MLflow not finalized')
    checkpoints=list((parent.OUT/'execution').glob('*.pt'))
    if len(checkpoints)!=15:raise ValueError('Parent checkpoint inventory')
    for f in checkpoints:
        if sha256(f)!=sha256(parent.BACKUP/f.name):raise ValueError('Parent independent backup mismatch')
    files=[parent.OUT/'result.json',parent.OUT/'execution/history.jsonl',parent.OUT/'execution/native-selected.json',
        parent.OUT/'execution/native-terminal.json',parent.SETUP/'scientific-resources.json']
    files+=list((parent.OUT/'execution').glob('native-*.json'))+checkpoints+[parent.BACKUP/f.name for f in checkpoints]
    write(SETUP/'parent-comparison.json',dict(summary,pins={str(f):sha256(f) for f in files},
        parent_mlflow_status='FINISHED',workers_reaped=True))


def verify_parent_binding():
    for f,h in read(SETUP/'parent-comparison.json')['pins'].items():
        if sha256(f)!=h:raise ValueError('Bound parent evidence changed: '+f)


def copy_backup(path,root):
    resource_check();dest=root/path.name;temporary=dest.with_suffix(dest.suffix+'.partial')
    if parent.tree_bytes(parent.BACKUP_ROOT)+path.stat().st_size>read(SPEC)['resources']['backup_cap_bytes']:raise ValueError('Backup capacity')
    with path.open('rb') as source,temporary.open('xb') as target:
        shutil.copyfileobj(source,target);target.flush();os.fsync(target.fileno())
    if sha256(path)!=sha256(temporary):raise ValueError('Backup mismatch')
    durable_replace(temporary,dest)


def supervise(stage,rid=None):
    command=[sys.executable,str(Path(__file__).resolve()),'--worker',stage]
    if rid:command+=['--mlflow-run',rid]
    last=[0.]
    def tick():
        if time.monotonic()-last[0]>30:resource_check();last[0]=time.monotonic()
    with (SETUP/(stage+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,PROWL_VARIED_SUPERVISED='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2'))
        try:watch_windows(process,seconds=read(SPEC)['max_seconds'] if stage=='scientific' else 3600,
                          rss_bytes=read(SPEC)['resources']['rss_bytes'],tick=tick)
        finally:write(SETUP/(stage+'-resources.json'),getattr(process,'duration_resources',{}))


def qualify():
    check(read(SETUP/'setup.json'));verify_parent_binding();resource_check()
    pilot=read(SETUP/'pilot/result.json');visual=read(SETUP/'visual-review.json')
    if not pilot['passed'] or len(pilot['cases'])!=12 or not visual['accepted'] or visual['reviewed_cases']!=12:
        raise ValueError('Pilot or visual review incomplete')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        (SETUP/'cuda').mkdir(exist_ok=False)
        (parent.BACKUP_ROOT/(NAME+'-qualification')).mkdir(exist_ok=False)
        supervise('producer');supervise('cold')


def qualification_worker(cold):
    import torch
    from src.training.segmenter_full_session_v1 import Session,identity_for
    from src.training.segmenter_varied_region_session_v1 import VariedSession
    from src.training.segmenter_pancreas_region_executor_v1 import execute
    from src.training.segmenter_augmentation_v1 import augmentation_identity
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    check(read(SETUP/'setup.json'));p=provider(True);config=cfg(True);root=SETUP/'cuda'
    backup=parent.BACKUP_ROOT/(NAME+'-qualification')
    if backup.stat().st_dev==root.stat().st_dev:raise ValueError('Independent backup required')
    torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats();began=time.monotonic()
    if cold:
        saved=torch.load(backup/'saved.pt',map_location='cpu',weights_only=True)['session']
        expected=torch.load(root/'expected.pt',map_location='cpu',weights_only=True)['session']
        identity=dict(version='varied-region-session-1',raw=identity_for(config['session'],p.control,'cuda',config['initialization']),
            policy=POLICY,augmentation=augmentation_identity())
        s=VariedSession.restore(saved,identity);compare(s.state(),saved,exact=True)
        update=s.update(p);maxima=[];compare(s.state(),expected,maxima=maxima)
        original=read(root/'producer.json')['updates'][-1]
        if update['input_view']!=original['input_view'] or update['batch_sha256']!=original['batch_sha256']:raise ValueError('Cold input mismatch')
        report=dict(exact_restore=True,exact_next_input=True,next_update_close=True,max_difference=max(maxima,default=0))
    else:
        s=VariedSession(Session(config['session'],p.control,device='cuda',initialization=config['initialization']))
        def hook(path):
            if path.name=='last.pt' and s.step in (4,5):
                target=root/('saved.pt' if s.step==4 else 'expected.pt');shutil.copyfile(path,target)
                if s.step==4:copy_backup(target,backup)
        result=execute(s,p,root/'execution',validate_every=5,checkpoint_every=1,
            checkpoint_hook=hook,validation_names=read(SETUP/'pilot-selection.json')['validation'])
        rows=[json.loads(x) for x in (root/'execution/history.jsonl').read_text().splitlines() if x.strip()]
        updates=[r for r in rows if r['event']=='update'];evaluations=[r for r in rows if r['event']=='native_case']
        kinds=[u['input_view']['window']['kind'] for u in updates]
        if not {'reserved_cover','component_jitter','region_context'}<=set(kinds) or kinds[3]!='region_context':raise ValueError('Actual sampler paths untested')
        if kinds[-1]!='component_jitter':raise ValueError('Cold replay must exercise changed jitter path')
        if result['completed_updates']!=5 or len(evaluations)!=2:raise ValueError('Actual executor incomplete')
        report=dict(updates=updates,evaluations=evaluations,executor_result=result,backup_sha256=sha256(backup/'saved.pt'))
    report.update(nonpromotable=True,seconds=time.monotonic()-began,peak_gpu_reserved=torch.cuda.max_memory_reserved())
    write(root/('cold.json' if cold else 'producer.json'),report)


def freeze():
    import xml.etree.ElementTree as ET
    receipt=read(SETUP/'setup.json');check(receipt);verify_parent_binding()
    for stage in ('pilot','producer','cold'):
        if not read(SETUP/(stage+'-resources.json'))['workers_reaped']:raise ValueError('Qualification worker active')
    if not read(SETUP/'cuda/cold.json')['exact_next_input'] or not read(SETUP/'pilot/result.json')['passed']:raise ValueError('Qualification failed')
    visual=read(SETUP/'visual-review.json')
    if not visual['accepted'] or visual['reviewed_cases']!=12:raise ValueError('Visual review incomplete')
    suites=ET.parse(SETUP/'tests.xml').getroot().findall('testsuite')
    if not suites or any(int(s.get('failures',0))+int(s.get('errors',0))+int(s.get('skipped',0)) for s in suites):raise ValueError('Tests failed or skipped')
    files=[SETUP/'parent-comparison.json',SETUP/'tests.xml',SETUP/'visual-review.json']
    files+=list((SETUP/'pilot').glob('*'))+list((SETUP/'cuda').glob('*.json'))+list((SETUP/'cuda').glob('*.pt'))
    files+=list(SETUP.glob('*-resources.json'))+[SETUP/'cuda/execution/history.jsonl',parent.BACKUP_ROOT/(NAME+'-qualification')/'saved.pt']
    receipt['pins'].update({str(f):sha256(f) for f in files if f.is_file()})
    write(SETUP/'ready.json',dict(receipt,status='READY'))
    print(sha256(SETUP/'ready.json'),flush=True)


def scientific_worker(rid):
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_varied_region_session_v1 import VariedSession
    from src.training.segmenter_pancreas_region_executor_v1 import execute
    from src.training.segmenter_live_tracking_v1 import Tracker
    receipt=read(SETUP/'ready.json');check(receipt);p=provider();c=cfg()
    if not rid or read(SETUP/'live-tracking.json')['run_id']!=rid or read(SETUP/'dispatch.json')['receipt_sha256']!=sha256(SETUP/'ready.json'):
        raise ValueError('Scientific dispatch binding')
    if p.pin!=receipt['control_sha256']:raise ValueError('Input control changed')
    OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
    if OUT.stat().st_dev==BACKUP.stat().st_dev:raise ValueError('Independent backup required')
    for name in ('resolved.yaml','ready.json','parent-comparison.json'):
        shutil.copyfile(SETUP/name,OUT/name);copy_backup(OUT/name,BACKUP)
    (OUT/'splits').mkdir()
    for role,filename in [('train','train_ids.txt'),('validation','development_ids.txt')]:
        with (OUT/'splits'/filename).open('x') as f:f.write('\n'.join(p.control[role])+'\n')
        copy_backup(OUT/'splits'/filename,BACKUP)
    write(OUT/'input-control.json',p.control);write(OUT/'tracking.json',dict(run_id=rid,tracking_uri=parent.URI))
    torch.set_num_threads(2);session=VariedSession(Session(c['session'],p.control,device='cuda',initialization=c['initialization']))
    last=[0.]
    def tick():
        if time.monotonic()-last[0]>30:resource_check();last[0]=time.monotonic()
    def hook(path):copy_backup(path,BACKUP);copy_backup(path.parent/'history.jsonl',BACKUP)
    result=execute(session,p,OUT/'execution',tick=tick,checkpoint_hook=hook,track=Tracker(rid,OUT))
    write(OUT/'result.json',result);copy_backup(OUT/'result.json',BACKUP)


def launch(pin):
    from mlflow import MlflowClient
    from mlflow.entities import Param
    if sha256(SETUP/'ready.json')!=pin:raise ValueError('Receipt mismatch')
    receipt=read(SETUP/'ready.json')
    if receipt['status']!='READY' or not receipt['scientific_launch_authorized']:raise ValueError('Not ready or authorized')
    check(receipt);verify_parent_binding();resource_check()
    if OUT.exists() or BACKUP.exists() or (SETUP/'dispatch.json').exists():raise ValueError('No retry or resume')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        write(SETUP/'dispatch.json',dict(receipt_sha256=pin,utc_ms=int(time.time()*1000)))
        client=MlflowClient(tracking_uri=parent.URI);experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
        if experiment is None:raise ValueError('Missing existing MLflow experiment')
        run=client.create_run(experiment.experiment_id,tags={'mlflow.runName':read(SPEC)['title'],
            'scope':'provided_pancreas_assisted_native_development','receipt_sha256':pin,
            'parent_run_id':read(SPEC)['parent_mlflow_run_id'],'changed_factor':'focused_training_windows_only'})
        rid=run.info.run_id;write(SETUP/'live-tracking.json',dict(run_id=rid,tracking_uri=parent.URI))
        try:
            client.log_batch(rid,params=[Param(k,str(v)) for k,v in dict(cfg()['session'],
                input_policy=POLICY['version'],pancreas_assistance=True,lesion_guided_development_crop=False,
                train_cases=1333,development_cases=70,validate_every=2000,checkpoint_every=500).items()])
            for f in [SPEC,SETUP/'ready.json',SETUP/'parent-comparison.json']:client.log_artifact(rid,str(f),'provenance')
            supervise('scientific',rid)
            client.set_tag(rid,'tracking_health','degraded_requires_journal_backfill' if (OUT/'tracking-warning.json').exists() else 'healthy')
            for f in [OUT/'result.json',OUT/'execution/history.jsonl',OUT/'execution/native-selected.json',OUT/'execution/native-terminal.json']:
                client.log_artifact(rid,str(f),'results')
            client.set_terminated(rid,'FINISHED')
        except BaseException:client.set_terminated(rid,'FAILED');raise


if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    for flag in ('prepare','bind-parent','pilot','qualify','freeze'):g.add_argument('--'+flag,action='store_true')
    g.add_argument('--launch-sha256');g.add_argument('--worker',choices=['pilot','producer','cold','scientific'])
    ap.add_argument('--mlflow-run');args=ap.parse_args()
    if args.worker and os.environ.get('PROWL_VARIED_SUPERVISED')!='1':raise ValueError('Use supervised entry')
    if args.prepare:prepare()
    elif args.bind_parent:bind_parent()
    elif args.pilot:
        check(read(SETUP/'setup.json'));verify_parent_binding();resource_check();supervise('pilot')
    elif args.qualify:qualify()
    elif args.freeze:freeze()
    elif args.launch_sha256:launch(args.launch_sha256)
    elif args.worker=='scientific':scientific_worker(args.mlflow_run)
    elif args.worker=='pilot':
        from scripts.diagnostics.qualify_varied_region import run
        run()
    else:qualification_worker(args.worker=='cold')
