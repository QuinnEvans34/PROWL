"""One authorized cache -> production binding -> smoke -> freeze -> training pipeline.

Stops on any failure without retry. Never scans duplicates or rewrites old evidence.
"""
import argparse
from collections import Counter
from copy import deepcopy
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training import experiment_config as E
from src.data.source_inventory_records import require
from src.data.manifest_records import canonical, digest
from scripts.diagnostics.prepare_panorama_positive_run import OUT, CACHE, BASE, PARENT, EXCLUDED, read, save

NAME='pants_plus_expert_panorama_dicefocal_24k_20261012'
CONFIG=OUT/'experiment.yaml'
SMOKE=OUT/'production-smoke'
SMOKE_BACKUP=Path('C:/Users/quinn/PROWL-Backups/panorama-positive-production-smoke-20261012-a01')
SPEC=ROOT/'docs/capstone/operations/PANORAMA-POSITIVE-EXPERIMENT-20261012.json'


def bind():
    import csv
    import yaml
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.data.segmenter_mixed_inputs_v1 import DOMAIN
    finished=read(OUT/'cache-complete.json');resources=read(OUT/'cache-resources.json')
    require(finished['completed'] and finished['cases']==345 and resources['workers_reaped'] and
        resources['seconds']<=14400 and resources['peak_owned_rss_bytes']<=12*1024**3, 'Cache not complete/reaped within bounds')
    require(finished['selection_sha256']==E.sha256(OUT/'selection.json'), 'Cache selection changed')
    selected=read(OUT/'selection.json')
    for path,pin in read(OUT/'cache-request.json')['pins'].items():
        require(E.sha256(path)==pin, 'Cache producing evidence changed')
    require(set(finished['members'])=={r['study_id'] for r in selected['rows']}, 'Incomplete production membership')
    cfg=E.load_experiment(PARENT);pants=PreparedInputs(cfg,cfg['full_segmenter']['geometry'])
    original=cfg['_experiment']['cohort'];spec=yaml.safe_load(PARENT.read_text())
    spec['name']=NAME;spec['recipe']['full_segmenter']['output_dir']='E:/PROWL/artifacts/'+NAME
    # Both source caches count against one aggregate ceiling.
    spec['recipe']['full_segmenter']['cache_dir']='E:/PROWL/cache'
    cohort=spec['cohort'];cohort['train_ids']=str(OUT/'train.txt');cohort['development_ids']=str(OUT/'development.txt')
    cohort['manifest']=str(OUT/'manifest.csv');cohort['review']=str(OUT/'cohort-review.json')
    train=pants.control['train']+sorted(finished['members']);dev=E.ids(OUT/'development.txt')
    require(len(train)==1678 and len(dev)==70 and not set(EXCLUDED)&set(train+dev), 'Cohort count/hold violation')
    (OUT/'train.txt').write_text('\n'.join(train)+'\n')
    with E.resolve(original['manifest']).open(newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    for row in selected['rows']:
        addition={k:'' for k in fields}
        addition.update(case_id=row['study_id'],ct_path=row['ct']['path'],pancreas_path=row['label']['path'],
            lesion_path=row['label']['path'],historical_has_lesion='True')
        rows.append(addition)
    with (OUT/'manifest.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    states={n:pants.control['target_states'][n] for n in train+dev if n in pants.control['target_states']}
    states.update({n:'positive' for n in finished['members']})
    parent_files=[PARENT]+[E.resolve(v) for v in original.values()]+[E.resolve(cfg['_experiment']['base_config'])]
    evidence=[OUT/'cache-complete.json',OUT/'cache-resources.json',OUT/'parent-reduced-comparison.json',
        ROOT/'docs/capstone/operations/PANORAMA-EXPLORATORY-ADMISSION-20261012.md',
        Path('E:/PROWL/readiness/panorama-narrow-readiness-20261011-a01/visual-review.json')]
    review=dict(domain=DOMAIN,decision='accepted',policy='declared_imports_excluded_five_dev_holds_exploratory',
        user_instruction='Keep the five uncertain CT scans out; document and load the data and run the next experiment.',
        scope='exploratory_development_not_zero_overlap_certification',excluded_development=EXCLUDED,
        empty_reference_policy='annotation_background_not_verified_healthy',target_states=states,
        evidence={str(p):E.sha256(p) for p in evidence},
        input_sha256={k:E.sha256(E.resolve(v)) for k,v in cohort.items() if k!='review'},
        prepared_cache={'root':str(pants.root),'control_sha256':E.sha256(pants.root/'control.json')},
        pants_parent=dict(experiment=str(PARENT),file_sha256={str(p):E.sha256(p) for p in parent_files},control_sha256=pants.pin),
        panorama_cache=dict(root=str(CACHE),members=finished['members'],selection_sha256=finished['selection_sha256']),
        limitations=['Residual undeclared overlap; ambiguous training redundancy not resolved',
            'Source subject grouping does not prove cross-source unique patients',
            'Focused engineering QC plus whole-cohort mechanical checks, not radiologist review',
            'Provided ROI and unverified SuPreM pretraining membership; reused development only'])
    save(OUT/'cohort-review.json',review)
    with CONFIG.open('x') as f:yaml.safe_dump(spec,f,sort_keys=False)
    mixed=PreparedInputs(E.load_experiment(CONFIG),cfg['full_segmenter']['geometry'])
    require(mixed.mixed.pants.pin==pants.pin, 'Parent provider changed')
    # Reuse full PanTS qualification. Check the newly constructed cache hashes, and only
    # four existing PanTS batches for unchanged adapter behavior (not 1,403-case replay).
    for member in finished['members'].values():
        require(E.sha256(member['cache'])==member['cache_sha256'], 'New production cache changed')
    probes=[]
    for role in ('train','validation'):
        probes.extend(next(n for n in pants.control[role] if n not in EXCLUDED and
            pants.control['target_states'][n]==state) for state in ('positive','reference_empty'))
    for name in probes:
        role='train' if name in mixed.control['train'] else 'validation'
        operation='optimizer' if role=='train' else 'evaluator'
        b=mixed.get(name,role=role,operation=operation);x,y=b.checked(mixed.pin,operation,name)
        require(x.shape==(1,144,144,144) and y.shape==(144,144,144), 'Production tensor shape mismatch')
        a=pants.get(name,role=role,operation=operation)
        require(a.hashes()==b.hashes(), 'PanTS numerical batch changed')
    from scripts.train_full_segmenter import preflight
    actual=E.load_experiment(CONFIG);actual['paths']['output_dir']=actual['full_segmenter']['output_dir']
    checked=preflight(actual,inspect=True);require(checked['ready'],str(checked))
    save(OUT/'production-binding.json',dict(preflight=checked,input_control_sha256=mixed.pin,
        train_cases=len(train),development_cases=len(dev),train_target_counts=dict(Counter(states[n] for n in train)),
        development_target_counts=dict(Counter(states[n] for n in dev)),new_cache_integrity_checked=345,
        pants_exact_batch_hash_matches=4,pants_original_control_unchanged=True,
        selection_grouping='345studies_344source_subjects_retained_D030',training_started=False))


class SmokeProvider:
    """Small disposable view of the actual production provider, not a second loader."""
    def __init__(self,cfg):
        from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
        self.full=PreparedInputs(cfg,cfg['full_segmenter']['geometry'])
        c=self.full.control;pan=sorted(c['panorama_members'])
        train=[next(n for n in c['train'] if n.startswith('PanTS_') and c['target_states'][n]==s)
            for s in ('positive','reference_empty')]+[pan[0],pan[-1]]
        dev=[next(n for n in c['validation'] if c['target_states'][n]==s) for s in ('positive','reference_empty')]
        self.control=dict(domain='disposable_production_mixed_smoke',train=train,validation=dev,
            target_states={n:c['target_states'][n] for n in train+dev},production_control=c,production_pin=self.full.pin)
        self.pin=digest(canonical(self.control))

    def get(self,name,*,role,operation):
        from src.data import segmenter_full_batch_v1 as B
        require(name in self.control['train' if role=='train' else 'validation'], 'Outside smoke subset')
        b=self.full.get(name,role=role,operation=operation);x,y=b.checked(self.full.pin,operation,name)
        return B.Batch(B._TOKEN,study_id=name,role=role,operation=operation,image=x,target=y,control_sha256=self.pin)


def smoke_worker(cold):
    import torch
    from src.training.segmenter_full_session_v1 import Session, identity_for
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from src.operations.full_training_platform import durable_replace
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    from scripts.train_full_segmenter import session_config
    cfg=E.load_experiment(CONFIG);provider=SmokeProvider(cfg);torch.set_num_threads(2)
    c=session_config(cfg);c.update(max_steps=9,warmup_steps=1,lr_horizon_steps=9)
    started=time.monotonic()
    if cold:
        state=torch.load(SMOKE_BACKUP/'saved.pt',map_location='cpu',weights_only=True)['session']
        expected=torch.load(SMOKE/'expected.pt',map_location='cpu',weights_only=True)['session']
        identity=identity_for(c,provider.control,'cuda',cfg['_experiment']['initialization'])
        session=Session.restore(state,identity);compare(session.state(),state,exact=True)
        row=session.update(provider);maxima=[];compare(session.state(),expected,maxima=maxima)
        report=dict(exact_restore=True,next_state_close=True,max_absolute_difference=max(maxima,default=0),
            rtol=1.3e-6,atol=1e-5,update=row,optimizer_updates=1)
    else:
        session=Session(c,provider.control,device='cuda',initialization=cfg['_experiment']['initialization'])
        rows=[session.update(provider) for _ in range(4)]
        require({r['member_id'] for r in rows}==set(provider.control['train']), 'Both sources/classes not exercised')
        atomic_checkpoint(SMOKE/'saved.pt',session,best_score=None,history_bytes=0)
        temp=SMOKE_BACKUP/'saved.partial'
        with (SMOKE/'saved.pt').open('rb') as src,temp.open('xb') as dst:
            shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        require(E.sha256(temp)==E.sha256(SMOKE/'saved.pt'), 'Independent backup hash mismatch')
        durable_replace(temp,SMOKE_BACKUP/'saved.pt')
        rows.append(session.update(provider));atomic_checkpoint(SMOKE/'expected.pt',session,best_score=None,history_bytes=0)
        evaluations=[session.evaluate_case(provider,n) for n in provider.control['validation']]
        report=dict(updates=rows,optimizer_updates=5,evaluations=evaluations,checkpoint_step=4,
            checkpoint_sha256=E.sha256(SMOKE_BACKUP/'saved.pt'),production_pin=provider.full.pin)
    torch.cuda.synchronize()
    report.update(seconds=time.monotonic()-started,promotable_model=False,scientific_training=False)
    save(SMOKE/('cold.json' if cold else 'producer.json'),report)


def supervised(stage,seconds):
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    from scripts.train_full_segmenter import tree_bytes
    def tick():
        require_ac()
        require(all(shutil.disk_usage(p).free>=100*1024**3 for p in ('C:/','E:/')), 'Storage floor')
        require(tree_bytes('E:/PROWL/cache')<=32*1024**3, 'Aggregate cache cap')
        require(tree_bytes('C:/Users/quinn/PROWL-Backups')<=27917287424, 'Backup cap')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        tick()
        with (OUT/(stage+'.log')).open('x') as log:
            p=subprocess.Popen([sys.executable,__file__,stage,'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
            try:watch_windows(p,seconds=seconds,rss_bytes=12*1024**3,tick=tick)
            finally:save(OUT/(stage+'-resources.json'),getattr(p,'duration_resources',{}))


def freeze():
    import xml.etree.ElementTree as ET
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from scripts.train_full_segmenter import preflight,tree_bytes
    cfg=E.load_experiment(CONFIG);full=cfg['full_segmenter'];cfg['paths']['output_dir']=full['output_dir']
    checked=preflight(cfg,inspect=True);require(checked['ready'],str(checked))
    p=PreparedInputs(cfg,full['geometry']);binding=read(OUT/'production-binding.json')
    producer,cold=read(SMOKE/'producer.json'),read(SMOKE/'cold.json')
    suites=ET.parse(OUT/'focused-tests.xml').getroot().findall('testsuite')
    require(suites and sum(int(s.attrib['tests']) for s in suites)>=90 and
        all(int(s.attrib['failures'])==int(s.attrib['errors'])==0 for s in suites), 'Focused test evidence missing/failed')
    require(binding['input_control_sha256']==producer['production_pin']==p.pin, 'Qualification identity differs')
    require(producer['optimizer_updates']==5 and cold['exact_restore'] and cold['next_state_close'], 'Smoke failed')
    for stage in ('bind','producer','cold'):
        require(read(OUT/(stage+'-resources.json'))['workers_reaped'], 'Qualification worker remains')
    require(not Path(full['output_dir']).exists() and not (Path(full['backup_dir'])/NAME).exists(), 'Run already exists')
    reserve=(SMOKE/'saved.pt').stat().st_size*7+128*1024**2
    require(tree_bytes(full['backup_dir'])+reserve<=full['backup_cap_bytes'], 'Insufficient independent backup reserve')
    require(all(shutil.disk_usage(p).free>=cfg['_experiment']['run']['min_free_bytes']+reserve for p in ('C:/','E:/')), 'Insufficient free space')
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+[CONFIG,SPEC]
    files += [E.resolve(v) for v in cfg['_experiment']['cohort'].values()]
    files += [E.resolve(cfg['_experiment']['base_config']),E.resolve(cfg['_experiment']['initialization']['source_review'])]
    review=read(OUT/'cohort-review.json')
    files += [Path(p) for p in review['evidence']]+[Path(p) for p in review['pants_parent']['file_sha256']]
    files += [OUT/'pipeline-request.json',OUT/'focused-tests.xml',OUT/'production-binding.json',SMOKE/'producer.json',SMOKE/'cold.json']
    files += [OUT/(s+'-resources.json') for s in ('cache','bind','producer','cold')]
    receipt=dict(status='ready_to_launch_not_started',title=read(SPEC)['title'],experiment_id='CAP-EXP-017',
        configuration=str(CONFIG),configuration_sha256=E.sha256(CONFIG),python=sys.executable,python_version=sys.version,
        packages={n:importlib.metadata.version(n) for n in ('torch','monai','numpy','scipy','nibabel','PyYAML')},
        file_sha256={str(f):E.sha256(f) for f in files},preflight=checked,input_control_sha256=p.pin,
        counts={'train':1678,'positive_train':1016,'reference_empty_train':662,'development':70,'positive_dev':36,'empty_dev':34},
        backup_reserve_bytes=reserve,training_started=False,scheduled_checks=False,
        direct_training_command=[sys.executable,str(ROOT/'scripts/train_full_segmenter.py'),'--experiment',str(CONFIG)],
        limitations=review['limitations'])
    save(OUT/'ready.json',receipt)
    return E.sha256(OUT/'ready.json')


def pipeline():
    from src.operations.full_training_platform import training_guard,require_ac
    controls=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+[SPEC,OUT/'selection.json',OUT/'parent-reduced-comparison.json',OUT/'development.txt']
    pins={str(p):E.sha256(p) for p in controls}
    def unchanged():
        require(all(E.sha256(p)==h for p,h in pins.items()), 'Producing code/spec changed during pipeline')
    with training_guard(ROOT/'outputs/prowl/.panorama-positive-pipeline.lock'):
        save(OUT/'pipeline-request.json',dict(pins=pins,authority='October12 explicit user request to load and run',
            stages=['wait_existing_cache','bind','producer','cold','freeze','single_training_launch'],automatic_retries=False))
        with (OUT/'pipeline.jsonl').open('x') as journal:
            def event(stage,**kw):
                row=dict(stage=stage,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw)
                journal.write(json.dumps(row)+'\n');journal.flush();os.fsync(journal.fileno());print(json.dumps(row),flush=True)
            try:
                event('waiting_existing_cache',cache=str(CACHE))
                started=time.monotonic()
                while not (OUT/'cache-resources.json').exists():
                    require(time.monotonic()-started<14460,'Existing cache wait exceeded bound')
                    require_ac();unchanged();time.sleep(15)
                require(read(OUT/'cache-resources.json')['workers_reaped'] and (OUT/'cache-complete.json').exists(), 'Cache did not complete successfully')
                for stage,seconds in [('bind',1800),('producer',1800),('cold',1800)]:
                    unchanged();event(stage,status='started')
                    if stage=='producer':
                        SMOKE.mkdir(exist_ok=False);SMOKE_BACKUP.mkdir(exist_ok=False)
                        require(SMOKE.stat().st_dev!=SMOKE_BACKUP.stat().st_dev,'Independent backup volume required')
                    supervised(stage,seconds);unchanged();event(stage,status='passed')
                pin=freeze();event('ready',receipt_sha256=pin)
                unchanged();event('training_dispatch',configuration=str(CONFIG))
                subprocess.run([sys.executable,str(ROOT/'scripts/diagnostics/launch_pants_course_reference.py'),
                    '--receipt',str(OUT/'ready.json'),'--sha256',pin,'--launch'],cwd=ROOT,check=True,
                    env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
                event('completed')
            except BaseException as exc:
                event('failed',error_type=type(exc).__name__,error=str(exc));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['pipeline','bind','producer','cold']);parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.stage=='pipeline':pipeline()
    else:
        require(args.worker,'Use the single supervised pipeline')
        if args.stage=='bind':bind()
        else:smoke_worker(args.stage=='cold')
