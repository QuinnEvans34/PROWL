"""Own and reap the isolated Ollama server and single diagnostic worker."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

from retrieval.direct_corpus import read_config, limits
from src.retrieval.natural_answer import api

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'outputs/prowl/evidence-isolation-v1-20261018/supervision'
STORE = Path('/Volumes/PROWL-Data/PROWL/scratch/answer-model-v15-20261017/ollama')


def stop(process):
    if process is None: return
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=10)


def main():
    limits(read_config(str(ROOT/'infra/retrieval/.env.ingestion.json')))
    if not STORE.is_dir() or STORE.resolve() != STORE: raise ValueError('Model store unavailable')
    if json.loads((ROOT/'outputs/prowl/instruction-model-v15-20261017/verification-receipt.json').read_text())['state'] != 'verified':
        raise ValueError('Model provenance unavailable')
    if subprocess.run(['lsof','-t','-iTCP:11435','-sTCP:LISTEN'], capture_output=True).stdout:
        raise ValueError('Candidate port occupied; do not take over')
    OUT.mkdir(exist_ok=False)
    budget = json.loads((ROOT/'configs/evidence/evidence-isolation-v1.json').read_text())['budget']
    server = worker = None; reason = None; peak = samples = 0; started = time.monotonic()
    def interrupted(signum, frame): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with (OUT/'ollama.log').open('x') as serverlog, (OUT/'worker.log').open('x') as workerlog:
            server = subprocess.Popen(['/usr/local/bin/ollama','serve'], cwd=ROOT, start_new_session=True,
                env=dict(os.environ, OLLAMA_HOST='127.0.0.1:11435', OLLAMA_MODELS=str(STORE),
                         OLLAMA_NUM_PARALLEL='1', OLLAMA_MAX_LOADED_MODELS='1'), stdout=serverlog, stderr=subprocess.STDOUT)
            for _ in range(20):
                if server.poll() is not None: raise RuntimeError('Candidate server exited')
                try: api('tags', port=11435, deadline=time.monotonic()+.4); break
                except OSError: time.sleep(.2)
            else: raise RuntimeError('Candidate server unavailable')
            worker = subprocess.Popen([str(ROOT/'.venv-retrieval/bin/python'),
                'scripts/retrieval/run_evidence_isolation.py','run'], cwd=ROOT, start_new_session=True,
                env=dict(os.environ, PYTHONPATH='.:scripts'), stdout=workerlog, stderr=subprocess.STDOUT)
            while worker.poll() is None:
                rows = [tuple(map(int,line.split())) for line in subprocess.check_output(
                    ['ps','-axo','pid=,ppid=,rss='], text=True).splitlines() if line.strip()]
                owned = {server.pid, worker.pid}
                while True:
                    expanded = owned | {p for p,parent,_ in rows if parent in owned}
                    if expanded == owned: break
                    owned = expanded
                rss = sum(k*1024 for p,_,k in rows if p in owned); peak=max(peak,rss); samples+=1
                if rss > budget['peak_owned_gib']*1024**3: reason='memory_budget'
                elif time.monotonic()-started > budget['batch_seconds']: reason='time_budget'
                elif shutil.disk_usage('/').free < budget['internal_floor_gib']*1024**3 or shutil.disk_usage(STORE).free < budget['external_floor_gib']*1024**3: reason='storage_floor'
                elif server.poll() is not None: reason='server_exit'
                if reason: break
                time.sleep(.5)
    finally:
        stop(worker); stop(server)
        result = dict(seconds=time.monotonic()-started, peak_owned_rss_bytes=peak, samples=samples,
            stop_reason=reason, worker_pid=worker.pid if worker else None,
            worker_exit=worker.returncode if worker else None, server_pid=server.pid if server else None,
            server_exit=server.returncode if server else None, reaped=True)
        (OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n'); print(result,flush=True)
    if reason or not worker or worker.returncode: raise SystemExit(1)


if __name__ == '__main__': main()
