"""One requested Lenovo admission sequence and timed run; fail closed, no retries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.full_training_platform import training_guard,watch_windows,require_ac


def audit_gate(handoff,audit,expected_count=1408):
    summary=json.loads((audit/'summary.json').read_text())
    resources=json.loads((audit/'resources.json').read_text())
    if not summary['completed'] or summary['passed']!=expected_count or summary['failed']!=0 or not resources['workers_reaped']:
        raise ValueError('Every original admitted member must pass; no silent cohort shrinkage')
    cache=Path(summary['cache'])
    inventory=json.loads((handoff/'metadata/source-file-hashes.json').read_text())
    expected={}
    for r in inventory:
        member=expected.setdefault(r['case_id'],{})
        if r['kind'] in member:raise ValueError('Duplicate source hash')
        member[r['kind']]=r['sha256']
    if len(expected)!=expected_count or any(set(v)!={'ct','pancreas','lesion'} for v in expected.values()):
        raise ValueError('Incomplete source inventory')
    source=json.loads((audit/'input-control.json').read_text())
    if set(source['train']+source['validation'])!=set(expected):raise ValueError('Source membership changed')
    original_states=json.loads((handoff/'metadata/target-states.json').read_text())
    if source['target_states']!=original_states:raise ValueError('Target states changed')
    for name,hashes in expected.items():
        metadata=json.loads((cache/(name+'.json')).read_text())
        if metadata['source_sha256']!=hashes:raise ValueError(f'Source hash changed during preparation: {name}')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--handoff',type=Path,required=True);p.add_argument('--verification',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--continue-from',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    paths=subprocess.check_output(['git','ls-files','src','scripts','configs'],cwd=ROOT,text=True).splitlines()
    # Include this launcher even before its first commit.
    paths=sorted(set(paths+[str(Path(__file__).relative_to(ROOT)).replace('\\','/')]))
    pins={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths}
    (a.output/'code-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    (a.output/'launch-authority.json').write_text(json.dumps(dict(
        user_intent='Start real PanTS training; target eight elapsed hours; preserve 24000-step LR and final rate',
        train=1333,development=75,exclusions_retained=84,target_seconds=28800,watchdog_seconds=32400,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        automatic_retry=False,scope='one admission sequence and one fresh timed CUDA development run'),indent=2)+'\n')
    def record(stage,**fields):
        row=dict(stage=stage,at=time.time(),**fields)
        with (a.output/'pipeline.jsonl').open('a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
        print(json.dumps(row),flush=True)
    def unchanged():
        for path,pin in pins.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=pin:raise RuntimeError('Code changed: '+path)
    def run(stage,script,args,seconds):
        unchanged();require_ac();record(stage,status='starting')
        command=[sys.executable,str(ROOT/script)]+list(map(str,args))
        env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONUNBUFFERED='1')
        with (a.output/(stage+'.log')).open('x') as log:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:watch_windows(process,seconds=seconds,rss_bytes=16*1024**3,tick=require_ac)
            finally:
                (a.output/(stage+'-resources.json')).write_text(json.dumps(getattr(process,'duration_resources',{}),indent=2)+'\n')
        record(stage,status='passed')
    candidate=a.output/'candidate';audit=a.output/'content-audit';admitted=a.output/'admitted'
    try:
        with training_guard(ROOT/'outputs/prowl/.lenovo-endurance-pipeline.lock'):
            if a.continue_from:
                parent=a.continue_from.resolve()
                events=[json.loads(line) for line in (parent/'pipeline.jsonl').read_text().splitlines()]
                if events[-1].get('status')!='failed' or any(r['stage']=='training' for r in events):
                    raise ValueError('Only stopped pretraining preparation can continue')
                candidate=parent/'candidate'
                (a.output/'continuation-parent.json').write_text(json.dumps(dict(parent=str(parent),
                    pipeline_sha256=hashlib.sha256((parent/'pipeline.jsonl').read_bytes()).hexdigest(),
                    preparation_seconds=14400,automatic_retry=False),indent=2)+'\n')
            else:
                run('bind-inputs','scripts/diagnostics/prepare_lenovo_handoff_config.py',
                    ['--handoff',a.handoff,'--verification',a.verification,'--output',candidate],120)
            extra=(['--resume-audit',a.continue_from/'content-audit','--max-seconds',14400] if a.continue_from else [])
            run('prepare-cache','scripts/prepare_full_segmenter_cache.py',
                ['--experiment',candidate/'candidate.yaml','--output',audit]+extra,14700 if a.continue_from else 7500)
            audit_gate(a.handoff,audit)
            run('compile-cohort','scripts/compile_full_segmenter_cohort.py',
                ['--config',candidate/'candidate.yaml','--audit',audit,'--output',admitted],180)
            for local,old in [('train.txt','train.txt'),('development.txt','development.txt')]:
                if (admitted/local).read_text().split()!=(a.handoff/'splits/admitted'/old).read_text().split():
                    raise ValueError('Ordered admitted membership changed')
            run('real-profile','scripts/diagnostics/profile_lenovo_real_segmenter.py',
                ['--experiment',admitted/'experiment.yaml','--output',a.output/'real-profile',
                 '--backup','C:/Users/quinn/PROWL-Backups/lenovo-8h-profile-01'],1900)
            cold=json.loads((a.output/'real-profile/cold.json').read_text())
            if not cold['full_state_restore_exact'] or not cold['next_state_close']:raise ValueError('Cold recovery failed')
            run('training','scripts/train_full_segmenter.py',['--experiment',admitted/'experiment.yaml'],32520)
            record('finished',status='completed')
    except BaseException as exc:
        record('stopped',status='failed',error=repr(exc),automatic_retry=False)
        raise


if __name__=='__main__':main()
