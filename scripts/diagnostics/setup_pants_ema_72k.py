"""Reuse admitted PanTS metadata, qualify EMA recovery, then freeze one launch receipt."""
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

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training import experiment_config as E
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require
from scripts.train_full_segmenter import preflight,session_config,tree_bytes
SETUP=Path('E:/PROWL/readiness/pants-ema-72k-20261013-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/pants-ema-qualification-20261013')
NAME='pants_only_ema_72k_20261013'
SPEC=ROOT/'docs/capstone/operations/PANTS-EMA-72K-20261013.md'

def pins():
    paths=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+[SPEC]
    return {str(p):E.sha256(p) for p in paths}

def configuration():
    cfg=E.load_experiment(SETUP/'experiment.yaml');cfg['paths']['output_dir']=cfg['full_segmenter']['output_dir']
    return cfg

def prepare():
    parent=Path('E:/PROWL/readiness/pants-course-reference-20261011-a01/experiment.yaml')
    spec=yaml.safe_load(parent.read_text());cohort=spec['cohort']
    original_review=Path(cohort['review']);review=json.loads(original_review.read_text())
    dev=Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01/development.txt')
    train=E.ids(Path(cohort['train_ids']));names=E.ids(dev)
    require(len(train)==1333 and len(names)==70,'Wrong frozen cohort')
    excluded=set(E.ids(Path(cohort['development_ids'])))-set(names)
    require(excluded=={'PanTS_00000922','PanTS_00005105','PanTS_00005370','PanTS_00007299','PanTS_00007523'},'Unexpected development exclusions')
    SETUP.mkdir(parents=True,exist_ok=False)
    (SETUP/'development.txt').write_bytes(dev.read_bytes());cohort['development_ids']=str(SETUP/'development.txt')
    selected=set(train+names)
    review['target_states']={k:v for k,v in review['target_states'].items() if k in selected}
    review['prepared_cache']['members']={k:v for k,v in review['prepared_cache']['members'].items() if k in selected}
    review['input_sha256']['development_ids']=E.sha256(SETUP/'development.txt')
    review['long_schedule_amendment']=dict(parent_review=str(original_review),parent_sha256=E.sha256(original_review),
        excluded_development=sorted(excluded),reason='Reuse approved matched 70; no source/cache requalification',specification=str(SPEC))
    cohort['review']=str(SETUP/'cohort-review.json');(SETUP/'cohort-review.json').write_bytes(canonical(review))
    spec['name']=NAME;full=spec['recipe']['full_segmenter'];full['output_dir']='E:/PROWL/artifacts/'+NAME
    full['session']['lr_horizon_steps']=72000
    spec['run'].update(max_updates=72000,max_seconds=259200,retain_steps=[24000,36000,48000,60000,72000])
    (SETUP/'experiment.yaml').write_text(yaml.safe_dump(spec,sort_keys=False))
    cfg=configuration();report=preflight(cfg,inspect=True);require(report['ready'],str(report))
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    provider=PreparedInputs(cfg,full['geometry'])
    (SETUP/'setup.json').write_bytes(canonical(dict(parent_configuration=str(parent),parent_sha256=E.sha256(parent),
        file_sha256=pins(),preflight=report,control_sha256=provider.pin,scientific_training_launched=False)))
    print(json.dumps(report),flush=True)

def worker(cold):
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_ema_v1 import EMASession
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from src.training.segmenter_native_case_v1 import native_case
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.operations.full_training_platform import durable_replace
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    cfg=configuration();output=SETUP/'cuda-profile';torch.set_num_threads(2);started=time.monotonic()
    torch.cuda.reset_peak_memory_stats();provider=PreparedInputs(cfg,cfg['full_segmenter']['geometry'])
    if cold:
        saved=torch.load(BACKUP/'saved.pt',map_location='cpu',weights_only=True)['session']
        expected=torch.load(output/'expected.pt',map_location='cpu',weights_only=True)['session']
        session=EMASession.restore(saved,saved['identity']);compare(session.state(),saved,exact=True)
        update=session.update(provider);maxima=[];compare(session.state(),expected,maxima=maxima)
        report=dict(full_state_restore_exact=True,next_state_close=True,max_absolute_difference=max(maxima,default=0),
            rtol=1.3e-6,atol=1e-5,optimizer_updates=1,update=update)
    else:
        config=dict(session_config(cfg),max_steps=4,warmup_steps=1,lr_horizon_steps=4)
        session=EMASession(Session(config,provider.control,device='cuda',initialization=cfg['_experiment']['initialization']),start_step=2)
        updates=[session.update(provider) for _ in range(3)]
        atomic_checkpoint(output/'saved.pt',session,best_score=None,history_bytes=0)
        temp=BACKUP/'saved.partial'
        with (output/'saved.pt').open('rb') as src,temp.open('xb') as dest:
            shutil.copyfileobj(src,dest);dest.flush();os.fsync(dest.fileno())
        require(E.sha256(temp)==E.sha256(output/'saved.pt'),'Backup mismatch');durable_replace(temp,BACKUP/'saved.pt')
        updates.append(session.update(provider));atomic_checkpoint(output/'expected.pt',session,best_score=None,history_bytes=0)
        selected=[next(n for n in provider.control['validation'] if provider.control['target_states'][n]==state)
            for state in ('positive','reference_empty')]
        evaluations=[]
        for variant in ('raw','ema'):
            with session.weights(variant):
                for name in selected:evaluations.append(dict(variant=variant,**native_case(session.raw,provider,name)))
        report=dict(optimizer_updates=4,updates=updates,native_evaluations=evaluations,backup_sha256=E.sha256(BACKUP/'saved.pt'))
    torch.cuda.synchronize()
    report.update(seconds=time.monotonic()-started,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_reserved_bytes=torch.cuda.max_memory_reserved(),nonpromotable=True,control_sha256=provider.pin)
    (output/('cold.json' if cold else 'producer.json')).write_bytes(canonical(report))

def qualify():
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    output=SETUP/'cuda-profile';output.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
    require(output.stat().st_dev!=BACKUP.stat().st_dev,'Independent backup required')
    def tick():
        require_ac()
        for path in (output,BACKUP):require(shutil.disk_usage(path).free>=100*1024**3,'Storage floor')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        for stage in ('producer','cold'):
            with (output/(stage+'.log')).open('x') as log:
                process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--stage',stage],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                try:watch_windows(process,seconds=900,rss_bytes=12*1024**3,tick=tick)
                finally:(output/(stage+'-resources.json')).write_bytes(canonical(getattr(process,'duration_resources',{})))
            print(stage+' passed and worker reaped',flush=True)

def freeze():
    setup=json.loads((SETUP/'setup.json').read_text())
    for path,sha in setup['file_sha256'].items():require(E.sha256(path)==sha,'Producing file changed since qualification setup: '+path)
    suite=ET.parse(SETUP/'tests.xml').getroot()
    suites=list(suite.iter('testsuite'))
    require(suites and all(int(s.get('failures','0'))==int(s.get('errors','0'))==0 for s in suites),'Tests failed')
    require(sum(int(s.get('tests','0')) for s in suites)>=13,'Insufficient tests')
    for stage in ('producer','cold'):
        resource=json.loads((SETUP/'cuda-profile'/f'{stage}-resources.json').read_text())
        require(resource.get('workers_reaped') is True,'Workers not reaped')
    cold=json.loads((SETUP/'cuda-profile/cold.json').read_text());require(cold['full_state_restore_exact'] and cold['next_state_close'],'Recovery failed')
    cfg=configuration();full=cfg['full_segmenter'];report=preflight(cfg,inspect=True);require(report['ready'],str(report))
    reserve=12*(SETUP/'cuda-profile/saved.pt').stat().st_size+256*1024**2
    require(tree_bytes(full['backup_dir'])+reserve<full['backup_cap_bytes'],'Retained-checkpoint allocation insufficient')
    require(tree_bytes(full['cache_dir'])<=full['cache_max_bytes'],'Cache budget')
    for path in (Path('C:/'),Path('E:/')):require(shutil.disk_usage(path).free>100*1024**3+reserve,'Free-space reserve')
    require(not (Path(full['backup_dir'])/NAME).exists(),'Backup already exists')
    filepins=dict(setup['file_sha256'])
    paths=[SETUP/'experiment.yaml',SETUP/'cohort-review.json',SETUP/'development.txt',SETUP/'setup.json',SETUP/'tests.xml']
    paths+=list((SETUP/'cuda-profile').glob('*.json'))
    paths+=[Path(v) for v in cfg['_experiment']['cohort'].values()]+[E.resolve(cfg['_experiment']['base_config'])] if 'base_config' in cfg['_experiment'] else [Path(v) for v in cfg['_experiment']['cohort'].values()]
    paths+=[Path(cfg['_experiment']['initialization']['source_review']),Path(full['cache_dir'])/'control.json']
    for path in paths:filepins[str(path)]=E.sha256(path)
    receipt=dict(configuration=str(SETUP/'experiment.yaml'),title='PanTS only: longer 72k schedule with ordinary and EMA weights',
        ema=dict(alpha=.99,start_step=500),control_sha256=setup['control_sha256'],file_sha256=filepins,
        preflight=report,backup_reserved_bytes=reserve,authority='User explicitly approved launching this single PanTS-only run; no automatic PANORAMA follow-up')
    with (SETUP/'ready.json').open('xb') as stream:stream.write(canonical(receipt))
    print(E.sha256(SETUP/'ready.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['prepare','qualify','producer','cold','freeze'],required=True);a=p.parse_args()
    if a.stage in ('producer','cold'):worker(a.stage=='cold')
    else:globals()[a.stage]()
