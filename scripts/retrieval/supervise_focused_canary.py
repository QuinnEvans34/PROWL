"""Own one V15 two-case worker and enforce its external-store/memory/time budget."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import shutil

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/prowl/source-focus-v17-20261018'
STORE=Path('/Volumes/PROWL-Data/PROWL/scratch/answer-model-v15-20261017/ollama')


def main():
    from retrieval.direct_corpus import read_config,limits
    limits(read_config(str(ROOT/'infra/retrieval/.env.ingestion.json')))
    assert json.loads((ROOT/'outputs/prowl/instruction-model-v15-20261017/verification-receipt.json').read_text())['state']=='verified'
    server=int(subprocess.check_output(['lsof','-t','-iTCP:11435','-sTCP:LISTEN'],text=True).strip())
    command=subprocess.check_output(['ps','-p',str(server),'-o','command='],text=True).strip()
    if command!='/usr/local/bin/ollama serve':raise ValueError('Unexpected candidate server owner')
    OUT.mkdir(exist_ok=False)
    log=(OUT/'canary-worker.log').open('x')
    process=subprocess.Popen([str(ROOT/'.venv-retrieval/bin/python'),'scripts/retrieval/check_focused_section_answers.py'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONPATH='.:scripts'))
    start=time.monotonic();peak=0;samples=0;reason=None
    try:
        while process.poll() is None:
            rows=[tuple(map(int,line.split())) for line in subprocess.check_output(['ps','-axo','pid=,ppid=,rss='],text=True).splitlines() if line.strip()]
            owned={server,process.pid}
            while True:
                expanded=owned|{p for p,parent,_ in rows if parent in owned}
                if expanded==owned:break
                owned=expanded
            rss=sum(k*1024 for p,_,k in rows if p in owned);peak=max(peak,rss);samples+=1
            if rss>18*1024**3:reason='memory_budget'
            elif time.monotonic()-start>240:reason='time_budget'
            elif shutil.disk_usage('/').free<104*1024**3 or shutil.disk_usage(STORE).free<100*1024**3:reason='storage_floor'
            if reason:
                process.send_signal(signal.SIGTERM)
                # This isolated listener was verified above and is owned by this experiment.
                os.kill(server,signal.SIGTERM)
                break
            time.sleep(.5)
        process.wait(timeout=10)
    finally:
        if process.poll() is None:process.kill();process.wait()
        log.close()
        result=dict(worker_pid=process.pid,server_pid=server,exit_code=process.returncode,stop_reason=reason,peak_owned_rss_bytes=peak,samples=samples,seconds=time.monotonic()-start,reaped=True)
        (OUT/'supervisor-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
    if process.returncode or reason:raise SystemExit(1)

if __name__=='__main__':main()
