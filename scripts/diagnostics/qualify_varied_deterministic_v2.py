"""Amended equivalence proof plus actual-production cold replay. No science here."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.diagnostics import setup_fast_varied as setup
from scripts.diagnostics import qualify_fast_varied as old
from scripts.diagnostics.control_original_repeatability import compare_states,input_comparison
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,require_ac

SETUP=Path('E:/PROWL/readiness/varied-deterministic-20261022-a02')
SPEC=ROOT/'docs/capstone/operations/PANTS-VARIED-QUALIFICATION-AMENDMENT-20261022.json'
BACKUP=setup.parent.BACKUP_ROOT/'pants-varied-deterministic-qualification-20261022-a02'
STAGES=('reference','producer','cold','production-cold')
read,write=setup.read,setup.write


def check():
    old.check()
    for path,pin in read(SETUP/'request.json')['pins'].items():
        if sha256(path)!=pin: raise ValueError('Amended qualification pin changed: '+path)


def prepare():
    if SETUP.exists(): raise ValueError('Amended qualification already prepared; no duplicate')
    old.check()
    prior=read(setup.SETUP/'original-repeatability-a01/resources.json')
    if not prior['success'] or not prior['workers_reaped']: raise ValueError('Control not complete')
    if read(setup.SETUP/'original-repeatability-a01/result.json')['original_repeat']['passes_original_bound']:
        raise ValueError('Expected demonstrated baseline drift')
    files=[Path(__file__),ROOT/'scripts/diagnostics/deterministic_upsample_probe_v2.py',SPEC,
        ROOT/'tests/test_varied_deterministic_qualification_v2.py',
        setup.SETUP/'deterministic-adapter-v2-tests.xml',setup.SETUP/'cuda-request.json',
        setup.SETUP/'failure-review.json',setup.SETUP/'original-repeatability-a01/result.json',
        setup.SETUP/'original-repeatability-a01/resources.json',setup.SETUP/'cuda/expected.pt',
        old.BACKUP/'saved.pt',setup.SETUP/'cuda/execution/history.jsonl',
        Path('E:/PROWL/readiness/varied-deterministic-20261022-a01/request.json'),
        Path('E:/PROWL/readiness/varied-deterministic-20261022-a01/reference-resources.json')]
    SETUP.mkdir(exist_ok=False)
    write(SETUP/'request.json',dict(pins={str(p):sha256(p) for p in files},scientific=False,
        authority=read(SPEC)['authority'],seconds=1200,rss_bytes=12*1024**3))


def independent_save(path,state):
    old.save(path,state); setup.resources()
    if setup.parent.tree_bytes(setup.parent.BACKUP_ROOT)+path.stat().st_size>27917287424:
        raise ValueError('Backup cap')
    destination=BACKUP/path.name
    with path.open('rb') as a,destination.open('xb') as b:
        shutil.copyfileobj(a,b); b.flush(); os.fsync(b.fileno())
    if sha256(path)!=sha256(destination): raise ValueError('Independent backup mismatch')


def worker(stage):
    import torch
    from scripts.diagnostics import deterministic_upsample_probe_v2 as det
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_varied_region_session_v1 import VariedSession
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.data.manifest_records import canonical,digest
    check(); torch.set_num_threads(2)
    if stage!='production-cold': det.configure()
    elif torch.are_deterministic_algorithms_enabled() or torch.backends.cudnn.deterministic:
        raise ValueError('Production cold replay must use original numerical mode')
    write(SETUP/(stage+'-backend.json'),dict(deterministic=torch.are_deterministic_algorithms_enabled(),
        cudnn_deterministic=torch.backends.cudnn.deterministic,cublas=os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
        cpu_adjoint=stage!='production-cold',scientific=False))
    plan=read(setup.SETUP/'cuda-plan.json'); p=None
    try:
        if stage in ('reference','producer'):
            p=setup.varied.provider() if stage=='reference' else old.provider()
            if stage=='reference':
                p.control['train']=plan['train']; p.control['qualification_only']=True; p.pin=digest(canonical(p.control))
            c=plan['config']; raw=Session(c['session'],p.control,device='cuda',initialization=c['initialization'])
            det.install(raw.model)
            s=VariedSession(raw) if stage=='reference' else FastVariedSession(raw)
            rows=[]; start=time.monotonic(); last_check=start
            reference=read(SETUP/'reference.json')['updates'] if stage=='producer' else None
            with (SETUP/(stage+'-updates.jsonl')).open('xb') as journal:
                for _ in range(33):
                    if time.monotonic()-last_check>30: setup.resources(); last_check=time.monotonic()
                    began=time.monotonic(); row=s.update(p); row['update_seconds']=time.monotonic()-began
                    if reference and any(row[k]!=reference[len(rows)][k] for k in ('step','member_id','batch_sha256','input_view','learning_rate')):
                        raise ValueError('Deterministic actual input mismatch')
                    rows.append(row); journal.write(canonical(row)); journal.flush(); os.fsync(journal.fileno())
                    if stage=='producer' and s.step==32: independent_save(SETUP/'saved.pt',s.state())
            old.save(SETUP/(stage+'-final.pt'),s.state())
            result=dict(updates=rows,seconds=time.monotonic()-start,nonpromotable=True,adapter_modules=3)
            if stage=='producer':
                expected=torch.load(SETUP/'reference-final.pt',map_location='cpu',weights_only=True)
                result.update(input_comparison(reference,rows)); comparison=compare_states(expected,s.state())
                result['state_comparison']=comparison
                if not comparison['passes_original_bound']: raise ValueError('Deterministic equivalence gate failed')
                if {r['input_view']['window']['kind'] for r in rows}!={'reserved_cover','component_jitter','region_context'}:
                    raise ValueError('Missing sampler branch')
            write(SETUP/(stage+'.json'),result)
        else:
            p=old.provider()
            saved_path=BACKUP/'saved.pt' if stage=='cold' else old.BACKUP/'saved.pt'
            expected_path=SETUP/'producer-final.pt' if stage=='cold' else setup.SETUP/'cuda/expected.pt'
            saved=torch.load(saved_path,map_location='cpu',weights_only=True)
            expected=torch.load(expected_path,map_location='cpu',weights_only=True)
            s=FastVariedSession.restore(saved,saved['identity'])
            if stage=='cold': det.install(s.raw.model)
            compare(s.state(),saved,exact=True)
            row=s.update(p)
            reference=(read(SETUP/'producer.json')['updates'][-1] if stage=='cold' else
                [json.loads(x) for x in (setup.SETUP/'cuda/execution/history.jsonl').read_text().splitlines()
                 if json.loads(x)['event']=='update'][-1])
            if any(row[k]!=reference[k] for k in ('step','member_id','batch_sha256','input_view','learning_rate')):
                raise ValueError('Cold input mismatch')
            comparison=compare_states(expected,s.state())
            if not comparison['passes_original_bound']: raise ValueError('Cold numerical gate failed')
            write(SETUP/(stage+'.json'),dict(exact_restore=True,exact_next_input=True,
                state_comparison=comparison,updates=1,nonpromotable=True,backup_sha256=sha256(saved_path)))
    finally:
        if p is not None and hasattr(p,'close'): p.close()


def stage(name):
    check(); log=SETUP/(name+'.log')
    spent=read(Path('E:/PROWL/readiness/varied-deterministic-20261022-a01/reference-resources.json'))['seconds'] if name=='reference' else 0
    if log.exists(): raise ValueError('Stage already started; no duplicate/retry')
    index=STAGES.index(name)
    if index:
        prior=read(SETUP/(STAGES[index-1]+'-resources.json'))
        if not prior['success'] or prior['exit_code']!=0 or not prior['workers_reaped']:
            raise ValueError('Previous stage failed or not reaped')
    if name=='producer': BACKUP.mkdir(exist_ok=False)
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'),log.open('x') as stream:
        env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_DET_QUAL='1')
        env.pop('CUDA_VISIBLE_DEVICES',None)
        if name!='production-cold': env['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
        else: env.pop('CUBLAS_WORKSPACE_CONFIG',None)
        process=subprocess.Popen([sys.executable,__file__,'--worker',name],cwd=ROOT,
            stdout=stream,stderr=subprocess.STDOUT,env=env)
        success=False
        try: watch_windows(process,seconds=1200-spent,rss_bytes=12*1024**3,tick=require_ac); success=True
        finally: write(SETUP/(name+'-resources.json'),dict(getattr(process,'duration_resources',{}),
            success=success,exit_code=process.returncode))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true'); group.add_argument('--stage',choices=STAGES)
    group.add_argument('--worker',choices=STAGES); args=parser.parse_args()
    if args.prepare: prepare()
    elif args.stage: stage(args.stage)
    else:
        if os.environ.get('PROWL_DET_QUAL')!='1': raise ValueError('Supervisor required')
        worker(args.worker)


