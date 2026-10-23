"""One authorized conditional dispatch after the EXISTING audit, never a retry loop."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import psutil
from scripts.train_pancreas_region import SETUP,COHORT,SPEC,read,write,resource_check
from src.training.experiment_config import sha256
from src.data.manifest_records import canonical


def run(pid):
    audit=psutil.Process(pid)
    if not any('continue_pancreas_region_v2.py' in x for x in audit.cmdline()) or '--run' not in audit.cmdline():raise ValueError('Wrong audit process')
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+[SPEC,SETUP/'tests.xml',SETUP/'visual-review.json',COHORT/'request.json']
    files += list((ROOT/'tests').glob('test_pancreas_region*.py'))
    pins={str(p):sha256(p) for p in files}
    write(SETUP/'pipeline-request.json',dict(audit_pid=pid,audit_created=audit.create_time(),pins=pins,automatic_retry=False,
        authority='User explicitly authorized provided-pancreas coverage/sampling verification then this one fresh scientific run'))
    def event(stage,**data):
        with (SETUP/'pipeline.jsonl').open('ab') as f:f.write(canonical(dict(stage=stage,utc_ms=int(time.time()*1000),**data)));f.flush();os.fsync(f.fileno())
        print(stage,flush=True)
    def check():
        for p,h in pins.items():
            if sha256(p)!=h:raise ValueError('Pipeline producing file changed: '+p)
    def command(*args):
        check();resource_check()
        subprocess.run([sys.executable,str(ROOT/'scripts/train_pancreas_region.py'),*args],cwd=ROOT,check=True)
    try:
        event('waiting_existing_coverage_audit');began=time.monotonic()
        while not (COHORT/'resources.json').exists():
            if not audit.is_running() or time.monotonic()-began>7200:raise ValueError('Existing audit ended without completion or timed out')
            time.sleep(5)
        result=read(COHORT/'result.json');resources=read(COHORT/'resources.json')
        if not result['completed'] or not result['all_pass'] or not resources['workers_reaped']:raise ValueError('Coverage gate failed')
        event('binding_and_schedule_verification');command('--prepare')
        event('cuda_and_cold_restore');command('--qualify')
        event('freezing_readiness');command('--freeze')
        event('scientific_dispatch');command('--launch-sha256',sha256(SETUP/'ready.json'))
        event('completed')
    except BaseException as exc:
        event('failed',error_type=type(exc).__name__,error=str(exc))
        write(SETUP/'pipeline-failure.json',dict(error_type=type(exc).__name__,error=str(exc),automatic_retry=False))
        raise


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--audit-pid',type=int,required=True);a=ap.parse_args();run(a.audit_pid)
