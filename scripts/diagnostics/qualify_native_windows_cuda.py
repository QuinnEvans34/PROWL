"""Four nonpromotable updates, independent backup, one cold update; no long run."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_native_intake import OUT, provider, verify
from scripts.diagnostics.setup_pants_augmentation import configuration, environment
from scripts.train_full_segmenter import session_config, tree_bytes
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard, watch_windows, require_ac, durable_replace
BACKUP = Path('C:/Users/quinn/PROWL-Backups/native-intake-qualification-20261018-a02')
KIND='native'
COHORT='cohort-complete'


def configure(kind):
    global OUT,provider,verify,BACKUP,KIND,COHORT
    KIND=kind
    if kind=='physical':
        from scripts.diagnostics import qualify_physical_intake as physical
        OUT,provider,verify=physical.OUT,physical.provider,physical.verify
        BACKUP=Path('C:/Users/quinn/PROWL-Backups/physical-intake-qualification-20261018-a01')
        COHORT='cohort'


def journal(path, record):
    with Path(path).open('ab') as f:
        f.write(canonical(record));f.flush();os.fsync(f.fileno())


def checked():
    verify()
    r = json.loads((OUT/'cuda-request.json').read_text())
    if any(sha256(p) != h for p,h in r['pins'].items()): raise ValueError('CUDA pins changed')
    if environment() != r['environment']: raise ValueError('CUDA environment changed')
    return r


def worker(cold):
    import torch
    import numpy as np
    from src.training.segmenter_full_session_v1 import Session, identity_for
    if KIND=='physical':
        from src.training.segmenter_physical_windows_session_v1 import PhysicalSession as WindowSession,predict_native
        from src.data.segmenter_physical_windows_v1 import POLICY
        identity_version='physical-detail-session-1'
    else:
        from src.training.segmenter_native_windows_session_v1 import WindowSession,predict_native
        from src.data.segmenter_native_windows_v1 import POLICY
        identity_version='native-window-session-1'
    from src.training.segmenter_augmentation_v1 import augmentation_identity
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from src.training.pants_native_evaluation import native_metrics
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    request=checked(); cfg=configuration(); p=provider(); output=OUT/'cuda'
    config=dict(session_config(cfg),max_steps=4,warmup_steps=1,lr_horizon_steps=4)
    torch.set_num_threads(2); torch.cuda.reset_peak_memory_stats(); started=time.monotonic()
    if cold:
        saved=torch.load(BACKUP/'saved.pt',map_location='cpu',weights_only=True)['session']
        expected=torch.load(output/'expected.pt',map_location='cpu',weights_only=True)['session']
        identity=dict(version=identity_version,raw=identity_for(config,p.control,'cuda',cfg['_experiment']['initialization']),
                      policy=POLICY,augmentation=augmentation_identity())
        session=WindowSession.restore(saved,identity); compare(session.state(),saved,exact=True)
        update=session.update(p); journal(output/'cold-updates.jsonl',update)
        maxima=[]; compare(session.state(),expected,maxima=maxima)
        original=json.loads((output/'producer.json').read_text())['updates'][-1]
        if update['input_view'] != original['input_view'] or update['batch_sha256'] != original['batch_sha256']:
            raise ValueError('Cold window or augmentation mismatch')
        report=dict(exact_restore=True,next_update_close=True,exact_input_view=True,
                    max_absolute_difference=max(maxima,default=0),updates=[update])
    else:
        session=WindowSession(Session(config,p.control,device='cuda',initialization=cfg['_experiment']['initialization']))
        updates=[]
        for _ in range(3):
            t=time.monotonic(); r=session.update(p); r['seconds']=time.monotonic()-t; updates.append(r)
            journal(output/'producer-updates.jsonl',r)
            print(json.dumps(dict(qualification_update=r['step'],loss=r['loss'],seconds=r['seconds'])),flush=True)
        atomic_checkpoint(output/'saved.pt',session,best_score=None,history_bytes=0)
        temp=BACKUP/'saved.partial'
        with (output/'saved.pt').open('rb') as source,temp.open('xb') as dest:
            shutil.copyfileobj(source,dest);dest.flush();os.fsync(dest.fileno())
        if sha256(temp) != sha256(output/'saved.pt'): raise ValueError('Backup mismatch')
        durable_replace(temp,BACKUP/'saved.pt')
        t=time.monotonic(); r=session.update(p); r['seconds']=time.monotonic()-t; updates.append(r)
        journal(output/'producer-updates.jsonl',r)
        print(json.dumps(dict(qualification_update=r['step'],loss=r['loss'],seconds=r['seconds'])),flush=True)
        atomic_checkpoint(output/'expected.pt',session,best_score=None,history_bytes=0)
        evaluations=[]
        # Largest positive/empty native grids, chosen by geometry before predictions.
        # This stresses full-volume reconstruction memory, not only a small example.
        for selected in request['native_cases']:
            name,role=selected['case_id'],selected['role']
            t=time.monotonic(); c=p.load(name,role=role,operation='evaluator')
            codes,evidence=predict_native(session.raw,c['image'],c['geometry'],
                progress=lambda done,total: print(json.dumps(dict(case=name,tiles_done=done,total=total)),flush=True) if done%25==0 or done==total else None)
            metrics=native_metrics(codes,c['original_pancreas'],c['original_lesion'],np.array(c['geometry']['source_affine']))
            evaluations.append(dict(case_id=name,scope='nonpromotable_'+role+'_native_full_CT',metrics=metrics,
                                    reconstruction=evidence,seconds=time.monotonic()-t))
            journal(output/'native-evaluations.jsonl',evaluations[-1])
        report=dict(updates=updates,evaluations=evaluations,backup_sha256=sha256(BACKUP/'saved.pt'))
    torch.cuda.synchronize()
    report.update(nonpromotable=True,seconds=time.monotonic()-started,
                  peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
    (output/('cold.json' if cold else 'producer.json')).write_bytes(canonical(report))


def run():
    verify()
    if not json.loads((OUT/COHORT/'results.json').read_text())['completed']: raise ValueError('Intake incomplete')
    from scripts.diagnostics.qualify_native_intake import read_journal
    import math
    records=read_journal(OUT/COHORT/'cases.jsonl')
    largest=[max((r for r in records if r['positive']==positive),key=lambda r:math.prod(r['native_shape']))
             for positive in (True,False)]
    native_cases=[dict(case_id=r['case_id'],role=r['role'],voxels=math.prod(r['native_shape']),
                       tiles=r['full_field_tile_count'],selection='largest native grid within target state; no prediction-based selection') for r in largest]
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    files += [OUT/'request.json',OUT/COHORT/'results.json',OUT/COHORT/'cases.jsonl',OUT/COHORT/'resources.json',
              OUT/'pilot/visual-review.json',ROOT/'docs/capstone/operations/PANTS-COVERAGE-INTAKE-FIX-20261018.md']
    if (OUT/'parser-amendment.json').is_file():files.append(OUT/'parser-amendment.json')
    if KIND=='physical':files.append(ROOT/'docs/capstone/operations/PANTS-PHYSICAL-DETAIL-INTAKE-20261018.json')
    files += list((ROOT/'configs').rglob('*.yaml'))
    from scripts.diagnostics.qualify_native_intake import SETUP
    files += [SETUP/'experiment.yaml']
    with (OUT/'cuda-request.json').open('xb') as f:
        f.write(canonical(dict(pins={str(p):sha256(p) for p in files},environment=environment(),
                              updates=4,cold_updates=1,nonpromotable=True,native_cases=native_cases,kind=KIND)))
    output=OUT/'cuda';output.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
    if output.stat().st_dev==BACKUP.stat().st_dev: raise ValueError('Backup not independent')
    cfg=configuration()
    def tick():
        require_ac()
        if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')): raise ValueError('Free space floor')
        if tree_bytes(cfg['full_segmenter']['backup_dir'])+512*1024**2>cfg['full_segmenter']['backup_cap_bytes']:
            raise ValueError('Backup cap')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        for stage in ('producer','cold'):
            tick()
            with (output/(stage+'.log')).open('x') as log:
                process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--kind',KIND,'--worker',stage],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                try:watch_windows(process,seconds=1800,rss_bytes=12*1024**3,tick=tick)
                finally:(output/(stage+'-resources.json')).write_bytes(canonical(getattr(process,'duration_resources',{})))
            print(stage+' passed; worker reaped',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['native','physical'],default='native');ap.add_argument('--run',action='store_true');ap.add_argument('--worker',choices=['producer','cold']);a=ap.parse_args()
    configure(a.kind)
    if a.run:run()
    elif a.worker:worker(a.worker=='cold')
