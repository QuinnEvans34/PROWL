"""Explicit stages for one qualified pancreas-assisted run; never retries or resumes."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import yaml
from src.data.manifest_records import canonical,digest
from src.training.experiment_config import sha256
from src.operations.full_training_platform import require_ac,watch_windows,training_guard,durable_replace
from scripts.diagnostics.setup_pants_augmentation import configuration,environment
from scripts.train_full_segmenter import session_config,tree_bytes
from scripts.diagnostics.qualify_native_intake import SETUP as SOURCE_SETUP,TRAIN,MANIFEST
from src.data.segmenter_pancreas_region_v1 import RegionInputs,POLICY
from scripts.diagnostics.backfill_full_runs_mlflow import URI

SPEC=ROOT/'docs/capstone/operations/PANTS-PANCREAS-REGION-24K-20261019.json'
SETUP=Path('E:/PROWL/readiness/pancreas-region-20261019-a01')
COHORT=SETUP/'cohort-final'
NAME='pants_pancreas_region_24k_20261019'
OUT=Path('E:/PROWL/artifacts')/NAME
BACKUP_ROOT=Path('C:/Users/quinn/PROWL-Backups')
BACKUP=BACKUP_ROOT/NAME


def read(p):return json.loads(Path(p).read_text())
def write(p,v):
    with Path(p).open('xb') as f:f.write(canonical(v));f.flush();os.fsync(f.fileno())
def provider():
    p=RegionInputs(manifest=MANIFEST,review=SOURCE_SETUP/'cohort-review.json',train_file=TRAIN,dev_file=SOURCE_SETUP/'development.txt')
    # Explicitly distinguish inherited source-reader provenance from final inputs.
    p.control['source_loader_policy']=p.control.pop('policy')
    p.control['policy']=dict(POLICY);p.pin=digest(canonical(p.control))
    return p
def resource_check():
    r=read(SPEC)['resources'];require_ac()
    if any(shutil.disk_usage(d).free<r['minimum_free_bytes'] for d in ('C:/','E:/')):raise ValueError('Disk floor')
    if tree_bytes(BACKUP_ROOT)>r['backup_cap_bytes']:raise ValueError('Backup cap')
    if tree_bytes(configuration()['full_segmenter']['cache_dir'])>r['cache_cap_bytes']:raise ValueError('Cache cap')
def check(receipt):
    for p,h in receipt['pins'].items():
        if sha256(p)!=h:raise ValueError('Pinned input changed: '+p)
    if receipt['environment']!=environment():raise ValueError('Environment changed')
def cfg(smoke=False):
    old=configuration();s=session_config(old)
    if smoke:s=dict(s,max_steps=4,warmup_steps=1,lr_horizon_steps=4)
    return dict(session=s,initialization=old['_experiment']['initialization'],
        _experiment=dict(run=dict(max_updates=24000,validate_every=2000,checkpoint_every=500),
        name=NAME),region_policy=POLICY)
def copy_backup(path,root):
    resource_check();dest=root/path.name;temp=dest.with_suffix(dest.suffix+'.partial')
    if tree_bytes(BACKUP_ROOT)+path.stat().st_size>read(SPEC)['resources']['backup_cap_bytes']:raise ValueError('Backup capacity')
    with path.open('rb') as src,temp.open('xb') as dst:shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
    if sha256(path)!=sha256(temp):raise ValueError('Backup mismatch')
    durable_replace(temp,dest)


def prepare():
    import torch
    import numpy as np
    from src.training.segmenter_full_session_v1 import POLICY as ORDER
    result=read(COHORT/'result.json');resources=read(COHORT/'resources.json')
    if not result['completed'] or not result['all_pass'] or result['cases']!=1403 or not resources['workers_reaped']:raise ValueError('Region cohort not qualified')
    for p,h in read(SETUP/'request.json')['pins'].items():
        if sha256(p)!=h:raise ValueError('Region audit changed')
    from scripts.diagnostics.continue_pancreas_region_v2 import checked
    checked()
    # Retain and verify all previous qualification evidence, not a replacement audit.
    from scripts.train_physical_segmenter import verify_qualification
    verify_qualification();resource_check();p=provider()
    inventory=Path('E:/PROWL/readiness/training-coverage-inventory-20261018-a01/cases.jsonl')
    inventory_rows=[json.loads(s) for s in inventory.read_text().splitlines()]
    if len(inventory_rows)!=671 or {r['case_id'] for r in inventory_rows}!={n for n in p.control['train'] if p.review['target_states'][n]=='positive'}:raise ValueError('Training-only margin cohort')
    required=[]
    for row in inventory_rows:
        path=p.root/(row['case_id']+'.json')
        if sha256(path)!=row['cache_metadata_sha256']:raise ValueError('Margin metadata changed')
        t=read(path)['transform'];plane=1/np.linalg.norm(np.linalg.inv(np.asarray(t['source_affine'])[:3,:3]),axis=1)
        required.append(np.maximum(np.maximum(np.asarray(t['native_box'][0])-row['lesion_box'][0],np.asarray(row['lesion_box'][1])-t['native_box'][1]),0)*plane)
    maximum=np.max(required,axis=0)
    if not np.array_equal(np.ceil(maximum)+1,POLICY['extra_margin_mm']):raise ValueError('Margin derivation mismatch')
    write(SETUP/'margin-derivation.json',dict(training_cases=671,development_cases_used=0,maximum_extra_mm=maximum.tolist(),rounded_plus_safety_mm=POLICY['extra_margin_mm'],inventory_sha256=sha256(inventory)))
    rows=[json.loads(s) for s in (COHORT/'cases.jsonl').read_text().splitlines()]
    if len({r['case_id'] for r in rows})!=1403 or {r['case_id'] for r in rows if r['role']=='train'}!=set(p.control['train']) or {r['case_id'] for r in rows if r['role']=='validation'}!=set(p.control['validation']):raise ValueError('Cohort accounting mismatch')
    counts={n:0 for n in p.control['train']};seen={n:0 for n in counts};mix=[]
    names=list(counts);order=None
    for step in range(24000):
        epoch,cursor=divmod(step,len(names))
        if cursor==0:
            seed=int.from_bytes(hashlib.sha256(f'42:{epoch}:{ORDER}'.encode()).digest()[:8],'little')
            order=torch.randperm(len(names),generator=torch.Generator().manual_seed(seed)).tolist()
        n=names[order[cursor]];seen[n]+=1
        if step%4!=3:counts[n]+=1
        mix.append('context' if step%4==3 else 'focus')
    by_name={r['case_id']:r for r in rows}
    failures=[n for n,c in counts.items() if c<by_name[n]['cover_windows']]
    if failures:raise ValueError('24k schedule does not cover all annotations: '+str(failures))
    schedule=dict(total_updates=24000,focused_updates=sum(counts.values()),context_updates=6000,
        every_four_updates_context=all(mix[i:i+4].count('context')==1 for i in range(0,24000,4)),
        minimum_focused_visits=min(counts.values()),maximum_focused_visits=max(counts.values()),
        all_cases_complete_coverage_bank=True,focused_counts=counts,exposure=seen)
    write(SETUP/'schedule.json',schedule)
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'configs').rglob('*.yaml'))
    files += [SPEC,SETUP/'request.json',COHORT/'request.json',COHORT/'result.json',COHORT/'cases.jsonl',COHORT/'resources.json',
        SETUP/'schedule.json',SETUP/'margin-derivation.json',SOURCE_SETUP/'experiment.yaml',ROOT/'tests/test_pancreas_region.py']
    files += list((ROOT/'tests').glob('test_pancreas_region*.py'))
    pins={**read(SETUP/'request.json')['pins'],**read(COHORT/'request.json')['pins'],**{str(f):sha256(f) for f in files}}
    write(SETUP/'setup.json',dict(pins=pins,environment=environment(),control_sha256=p.pin))
    with (SETUP/'resolved.yaml').open('x') as f:yaml.safe_dump(cfg(),f)


def qualification_worker(cold):
    import torch
    from src.training.segmenter_full_session_v1 import Session,identity_for
    from src.training.segmenter_pancreas_region_session_v1 import RegionSession,evaluate
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    check(read(SETUP/'setup.json'));p=provider();config=cfg(True);root=SETUP/'cuda';backup=BACKUP_ROOT/(NAME+'-qualification')
    torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats();started=time.monotonic()
    if cold:
        saved=torch.load(backup/'saved.pt',map_location='cpu',weights_only=True)['session']
        expected=torch.load(root/'expected.pt',map_location='cpu',weights_only=True)['session']
        from src.training.segmenter_augmentation_v1 import augmentation_identity
        identity=dict(version='pancreas-region-session-1',raw=identity_for(config['session'],p.control,'cuda',config['initialization']),policy=POLICY,augmentation=augmentation_identity())
        s=RegionSession.restore(saved,identity);compare(s.state(),saved,exact=True)
        update=s.update(p);maxima=[];compare(s.state(),expected,maxima=maxima)
        original=read(root/'producer.json')['updates'][-1]
        if update['input_view']!=original['input_view'] or update['batch_sha256']!=original['batch_sha256']:raise ValueError('Cold input mismatch')
        report=dict(exact_restore=True,exact_next_input=True,next_update_close=True,max_difference=max(maxima,default=0))
    else:
        from src.training.segmenter_pancreas_region_executor_v1 import execute
        s=RegionSession(Session(config['session'],p.control,device='cuda',initialization=config['initialization']))
        rows=[json.loads(x) for x in (COHORT/'cases.jsonl').read_text().splitlines()]
        import math
        selected=[max((r for r in rows if r['role']=='validation' and r['positive']==positive),
            key=lambda r:math.prod(h-l for l,h in zip(r['region_low'],r['region_high']))) for positive in (True,False)]
        def checkpoint_hook(path):
            if path.name=='last.pt' and s.step in (3,4):
                target=root/('saved.pt' if s.step==3 else 'expected.pt')
                shutil.copyfile(path,target)
                if s.step==3:copy_backup(target,backup)
        last_check=[0.]
        def tick():
            if time.monotonic()-last_check[0]>30:resource_check();last_check[0]=time.monotonic()
        result=execute(s,p,root/'execution',validate_every=4,checkpoint_every=1,
            checkpoint_hook=checkpoint_hook,tick=tick,validation_names=[r['case_id'] for r in selected])
        history=[json.loads(x) for x in (root/'execution/history.jsonl').read_text().splitlines()]
        updates=[r for r in history if r['event']=='update'];evaluations=[r for r in history if r['event']=='native_case']
        if [u['input_view']['window']['kind'] for u in updates]!=['focused_cover']*3+['region_context']:raise ValueError('Actual global mix')
        if result['completed_updates']!=4 or len(evaluations)!=2:raise ValueError('Actual executor integration incomplete')
        report=dict(updates=updates,evaluations=evaluations,executor_result=result,backup_sha256=sha256(backup/'saved.pt'))
    report.update(nonpromotable=True,seconds=time.monotonic()-started,peak_gpu_reserved=torch.cuda.max_memory_reserved())
    write(root/('cold.json' if cold else 'producer.json'),report)


def supervise(stage,rid=None):
    argv=[sys.executable,str(Path(__file__).resolve()),'--worker',stage]
    if rid:argv+=['--mlflow-run',rid]
    last=[0.]
    def tick():
        if time.monotonic()-last[0]>30:resource_check();last[0]=time.monotonic()
    with (SETUP/(stage+'.log')).open('x') as log:
        p=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,PROWL_REGION_SUPERVISED='1'))
        try:watch_windows(p,seconds=read(SPEC)['max_seconds'] if stage=='scientific' else 3600,rss_bytes=12*1024**3,tick=tick)
        finally:write(SETUP/(stage+'-resources.json'),getattr(p,'duration_resources',{}))


def qualify():
    check(read(SETUP/'setup.json'));resource_check()
    (SETUP/'cuda').mkdir(exist_ok=False);backup=BACKUP_ROOT/(NAME+'-qualification');backup.mkdir(exist_ok=False)
    if backup.stat().st_dev==SETUP.stat().st_dev:raise ValueError('Independent backup required')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        supervise('producer');supervise('cold')


def freeze():
    import xml.etree.ElementTree as ET
    receipt=read(SETUP/'setup.json');check(receipt)
    if not read(SETUP/'cold-resources.json')['workers_reaped'] or not read(SETUP/'producer-resources.json')['workers_reaped']:raise ValueError('Workers active')
    if not read(SETUP/'cuda/cold.json')['exact_next_input']:raise ValueError('Restore failure')
    suites=ET.parse(SETUP/'tests.xml').getroot().findall('testsuite')
    if not suites or any(int(s.get('failures',0))+int(s.get('errors',0))+int(s.get('skipped',0)) for s in suites):raise ValueError('Tests failed or skipped')
    # A reviewed real-case image set and complete actual-path evidence are mandatory.
    visual=read(SETUP/'visual-review.json')
    if visual.get('reviewed_cases')!=12 or not visual.get('accepted'):raise ValueError('Pilot image review missing')
    pilot=read(SETUP/'pilot/result.json')
    if not pilot['completed'] or len(pilot['cases'])!=12:raise ValueError('Incomplete pilot')
    for f in [SETUP/'resolved.yaml',SETUP/'tests.xml',SETUP/'cuda/cold.json',SETUP/'cuda/producer.json',
              SETUP/'cold-resources.json',SETUP/'producer-resources.json',SETUP/'visual-review.json']:
        receipt['pins'][str(f)]=sha256(f)
    for f in [SETUP/'pilot/result.json',*sorted((SETUP/'pilot').glob('*.png'))]:receipt['pins'][str(f)]=sha256(f)
    for f in [SETUP/'cuda/saved.pt',SETUP/'cuda/expected.pt',BACKUP_ROOT/(NAME+'-qualification')/'saved.pt',
              SETUP/'cuda/execution/history.jsonl',SETUP/'cuda/execution/native-selected.json']:
        receipt['pins'][str(f)]=sha256(f)
    write(SETUP/'ready.json',dict(receipt,status='READY',scientific_launch_authorized=True))
    print(sha256(SETUP/'ready.json'),flush=True)


def scientific_worker(rid):
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_pancreas_region_session_v1 import RegionSession
    from src.training.segmenter_pancreas_region_executor_v1 import execute
    from src.training.segmenter_live_tracking_v1 import Tracker
    receipt=read(SETUP/'ready.json');check(receipt);p=provider();c=cfg()
    if not rid or read(SETUP/'live-tracking.json')['run_id']!=rid or read(SETUP/'dispatch.json')['receipt_sha256']!=sha256(SETUP/'ready.json'):raise ValueError('Scientific dispatch binding')
    if p.pin!=receipt['control_sha256']:raise ValueError('Input control changed')
    OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
    if OUT.stat().st_dev==BACKUP.stat().st_dev:raise ValueError('Independent backup required')
    for filename in ('resolved.yaml','ready.json'):shutil.copyfile(SETUP/filename,OUT/filename);copy_backup(OUT/filename,BACKUP)
    (OUT/'splits').mkdir()
    for role,filename in [('train','train_ids.txt'),('validation','development_ids.txt')]:
        with (OUT/'splits'/filename).open('x') as f:f.write('\n'.join(p.control[role])+'\n')
        copy_backup(OUT/'splits'/filename,BACKUP)
    write(OUT/'input-control.json',p.control);write(OUT/'tracking.json',dict(run_id=rid,tracking_uri=URI))
    torch.set_num_threads(2);session=RegionSession(Session(c['session'],p.control,device='cuda',initialization=c['initialization']))
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
    check(receipt);resource_check()
    from scripts.train_physical_segmenter import verify_qualification
    verify_qualification()
    if OUT.exists() or BACKUP.exists():raise ValueError('No retry or resume')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        write(SETUP/'dispatch.json',dict(receipt_sha256=pin,utc_ms=int(time.time()*1000)))
        c=MlflowClient(tracking_uri=URI);e=c.get_experiment_by_name('PROWL capstone lesion outlining')
        if e is None:raise ValueError('Missing existing MLflow experiment')
        run=c.create_run(e.experiment_id,tags={'mlflow.runName':read(SPEC)['title'],'scope':'provided_pancreas_assisted_native_development','receipt_sha256':pin})
        rid=run.info.run_id;write(SETUP/'live-tracking.json',dict(run_id=rid,tracking_uri=URI))
        try:
            c.log_batch(rid,params=[Param(k,str(v)) for k,v in dict(cfg()['session'],input_policy=POLICY['version'],pancreas_assistance=True,lesion_guided_development_crop=False,train_cases=1333,development_cases=70,validate_every=2000,checkpoint_every=500).items()])
            c.log_artifact(rid,str(SPEC),'provenance');c.log_artifact(rid,str(SETUP/'ready.json'),'provenance')
            supervise('scientific',rid)
            c.set_tag(rid,'tracking_health','degraded_requires_journal_backfill' if (OUT/'tracking-warning.json').exists() else 'healthy')
            for f in [OUT/'result.json',OUT/'execution/history.jsonl',OUT/'execution/native-selected.json',OUT/'execution/native-terminal.json']:
                c.log_artifact(rid,str(f),'results')
            c.set_terminated(rid,'FINISHED')
        except BaseException:c.set_terminated(rid,'FAILED');raise


if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    for flag in ('prepare','qualify','freeze'):g.add_argument('--'+flag,action='store_true')
    g.add_argument('--launch-sha256');g.add_argument('--worker',choices=['producer','cold','scientific']);ap.add_argument('--mlflow-run');a=ap.parse_args()
    if a.worker and os.environ.get('PROWL_REGION_SUPERVISED')!='1':raise ValueError('Use supervised stage entry')
    if a.prepare:prepare()
    elif a.qualify:qualify()
    elif a.freeze:freeze()
    elif a.launch_sha256:launch(a.launch_sha256)
    elif a.worker=='scientific':scientific_worker(a.mlflow_run)
    else:qualification_worker(a.worker=='cold')
