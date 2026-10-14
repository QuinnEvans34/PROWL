"""Bounded real-data CUDA fit, independent backup and cold continuation qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))


def compare(left,right,*,exact=False,maxima=None):
    import torch
    if isinstance(left,torch.Tensor):
        assert left.shape==right.shape and left.dtype==right.dtype
        if exact or not left.is_floating_point(): assert torch.equal(left,right)
        else:
            torch.testing.assert_close(left,right,rtol=1.3e-6,atol=1e-5)
            if maxima is not None:maxima.append(float((left-right).abs().max()))
    elif isinstance(left,dict):
        assert left.keys()==right.keys()
        for k in left:compare(left[k],right[k],exact=exact,maxima=maxima)
    elif isinstance(left,(list,tuple)):
        assert len(left)==len(right)
        for a,b in zip(left,right):compare(a,b,exact=exact,maxima=maxima)
    else:assert left==right


def worker(experiment,output,backup,cold,validation_limit=None):
    import torch
    from src.training import experiment_config as E
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.operations.full_training_platform import durable_replace
    from scripts.train_full_segmenter import session_config
    cfg=E.load_experiment(experiment);full=cfg['full_segmenter']
    torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats();started=time.monotonic()
    provider=PreparedInputs(cfg,full['geometry'])
    if cold:
        saved=torch.load(backup/'saved.pt',map_location='cpu',weights_only=True)['session']
        expected=torch.load(output/'expected.pt',map_location='cpu',weights_only=True)['session']
        session=Session.restore(saved,saved['identity']);compare(session.state(),saved,exact=True)
        row=session.update(provider);maxima=[];compare(session.state(),expected,maxima=maxima)
        report=dict(stage='cold',optimizer_updates=1,full_state_restore_exact=True,next_state_close=True,
            rtol=1.3e-6,atol=1e-5,max_absolute_difference=max(maxima,default=0),update=row)
    else:
        session=Session(session_config(cfg),provider.control,device='cuda',initialization=cfg['_experiment']['initialization'])
        rows=[]
        for _ in range(2):
            at=time.monotonic();row=session.update(provider);row['wall_seconds']=time.monotonic()-at;rows.append(row)
        path=output/'saved.pt';atomic_checkpoint(path,session,best_score=None,history_bytes=0)
        temp=backup/'saved.partial'
        with path.open('rb') as src,temp.open('xb') as dst:
            shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        assert E.sha256(path)==E.sha256(temp)
        durable_replace(temp,backup/'saved.pt')
        rows.append(session.update(provider))
        atomic_checkpoint(output/'expected.pt',session,best_score=None,history_bytes=0)
        at=time.monotonic()
        names=session.control['validation'][:validation_limit] if validation_limit else session.control['validation']
        evaluations=[session.evaluate_case(provider,name) for name in names]
        report=dict(stage='producer',optimizer_updates=3,forwards=3+len(evaluations),updates=rows,
            validation_seconds=time.monotonic()-at,evaluations=evaluations,backup_sha256=E.sha256(backup/'saved.pt'))
    torch.cuda.synchronize()
    report.update(seconds=time.monotonic()-started,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_reserved_bytes=torch.cuda.max_memory_reserved(),precision='float32_tf32_disabled',
        development_only=True,training_run=False)
    (output/('cold.json' if cold else 'producer.json')).write_text(json.dumps(report,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--backup',type=Path,required=True);p.add_argument('--worker',action='store_true');p.add_argument('--cold',action='store_true')
    p.add_argument('--validation-limit',type=int, help='Bounded changed-recipe qualification; does not alter cohort identity')
    a=p.parse_args()
    if a.validation_limit is not None and a.validation_limit < 1:raise ValueError('Positive validation limit required')
    if a.worker:return worker(a.experiment,a.output,a.backup,a.cold,a.validation_limit)
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    from scripts.train_full_segmenter import preflight
    from src.training import experiment_config as E
    cfg=E.load_experiment(a.experiment);cfg['paths']['output_dir']=cfg['full_segmenter']['output_dir']
    report=preflight(cfg,inspect=True)
    if not report['ready']:raise ValueError(report)
    a.output.mkdir(parents=True,exist_ok=False);a.backup.mkdir(parents=True,exist_ok=False)
    assert a.output.stat().st_dev!=a.backup.stat().st_dev
    def tick():
        require_ac()
        for path in (a.output,a.backup):
            if shutil.disk_usage(path).free<100*1024**3:raise RuntimeError('Storage floor')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        for stage in ('producer','cold'):
            command=[sys.executable,str(Path(__file__).resolve()),'--experiment',a.experiment,
                '--output',str(a.output),'--backup',str(a.backup),'--worker']+(['--cold'] if stage=='cold' else [])
            if a.validation_limit:command+=['--validation-limit',str(a.validation_limit)]
            with (a.output/f'{stage}.log').open('x') as log:
                process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
                try:watch_windows(process,seconds=900,rss_bytes=12*1024**3,tick=tick)
                finally:
                    (a.output/f'{stage}-resources.json').write_text(json.dumps(getattr(process,'duration_resources',{}),indent=2)+'\n')
            r=json.loads((a.output/f'{stage}.json').read_text())
            print(json.dumps({k:v for k,v in r.items() if k not in ('evaluations','updates','update')}),flush=True)


if __name__=='__main__':main()
