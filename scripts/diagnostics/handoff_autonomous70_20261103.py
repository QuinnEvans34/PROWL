"""One-shot durable handoff for explicitly approved restoration and evaluation."""
import argparse,json,os,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import execute_autonomous_baseline_v2_20261103 as run
q=run.q
PIN='7db98398be4da35bf775976ef81ec73e848e0258e56e760307817a4e5ec48364'
BACKUP=Path('C:/Users/quinn/PROWL-Backups/week05-full-baseline-preparation-20261103-a02')

def verify_resources(path):
    v=json.loads(Path(path).read_text())
    if not v['success'] or not v['workers_reaped'] or v['exit_code']!=0:raise ValueError('Stage did not finish successfully/reap: '+str(path))

def execute_stage(flag,pin,log,seconds,rss,r):
    q.supervise([sys.executable,str(ROOT/'scripts/diagnostics/execute_autonomous_baseline_v2_20261103.py'),flag,pin],log=log,seconds=seconds,rss_bytes=rss,tick=lambda:run.gate(r))
    verify_resources(log.with_suffix('.resources.json'))

def main(receipt_sha):
    out=run.prep.OUT
    if q.sha(out/'handoff-request.json')!=receipt_sha:raise ValueError('Handoff receipt mismatch')
    receipt=json.loads((out/'handoff-request.json').read_text())
    for p,h in receipt['pins'].items():
        if q.sha(p)!=h:raise ValueError('Handoff pin changed: '+p)
    r=run.request(PIN);run.admission(PIN,r);run.gate(r)
    if any(p.exists() for p in [out/'handoff.jsonl',out/'restore.log',run.prep.SOURCES,run.BASE,run.BACKUP]):raise FileExistsError('Owned stage already started; no retry')
    journal=(out/'handoff.jsonl').open('x');started=time.monotonic()
    def event(stage):
        journal.write(json.dumps(dict(stage=stage,seconds=time.monotonic()-started,pid=os.getpid(),utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))+'\n');journal.flush();os.fsync(journal.fileno())
    def backup():
        for p in out.iterdir():
            if not p.is_file() or p.name in ['handoff.jsonl','handoff-console.log','handoff-console-error.log']:continue
            dest=BACKUP/p.name
            if not dest.exists():shutil.copyfile(p,dest)
            if q.sha(p)!=q.sha(dest):raise ValueError('Preparation backup mismatch: '+p.name)
    try:
        backup();event('restoration_start')
        execute_stage('--restore-sha256',PIN,out/'handoff-restore.log',r['limits']['restore_seconds'],r['limits']['restore_rss_bytes'],r)
        verify_resources(out/'restore.resources.json')
        restored=json.loads((run.prep.SOURCES/'restoration.json').read_text())
        wanted={c['case_id']:c['identity']['source_sha256']['ct'] for c in r['cases'] if c['needs_restoration'] and not c['preflight_failure']}
        if restored['request_sha256']!=PIN or restored['cases']!=wanted:raise ValueError('Restored set differs from exact64')
        backup();event('restoration_verified_source_admission_start')
        execute_stage('--admit-sources-sha256',PIN,out/'handoff-admit.log',600,r['limits']['restore_rss_bytes'],r)
        verify_resources(out/'source-admission.resources.json');ready=json.loads((out/'ready.json').read_text())
        if ready['request_sha256']!=PIN or len(ready['evidence'])!=70:raise ValueError('Incomplete source admission denominator')
        backup();event('source_admission_verified_evaluation_start')
        execute_stage('--launch-ready-sha256',q.sha(out/'ready.json'),out/'handoff-evaluate.log',r['limits']['total_evaluation_seconds'],r['limits']['rss_bytes'],r)
        result=json.loads((run.BASE/'completion.json').read_text())
        if result['total_cases']!=70 or result['successful_cases']!=69 or result['failed']!=['PanTS_00005592']:raise ValueError('Final accounting incomplete')
        for p in run.BASE.rglob('*'):
            if p.is_file() and q.sha(p)!=q.sha(run.BACKUP/p.relative_to(run.BASE)):raise ValueError('Final independent backup mismatch')
        backup();event('complete_69_predictions_one_declared_resource_failure')
    except BaseException as e:
        q.write(out/'handoff-failure.json',dict(error=repr(e),automatic_retry=False,request_sha256=PIN));event('failed_no_retry');raise
    finally:
        journal.close();backup();shutil.copyfile(out/'handoff.jsonl',BACKUP/'handoff.jsonl')
        if q.sha(out/'handoff.jsonl')!=q.sha(BACKUP/'handoff.jsonl'):raise ValueError('Final handoff journal backup')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--receipt-sha256',required=True);main(p.parse_args().receipt_sha256)
