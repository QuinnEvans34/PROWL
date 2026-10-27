"""Explicit local UI preparation; fixed commands only, no ingestion or model download."""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from retrieval.direct_corpus import read_config, limits, connect
from src.retrieval.search_reformulation import MODEL, MODEL_SHA
CONFIG = ROOT/'infra/retrieval/.env.ingestion.json'
LOCK = ROOT/'outputs/prowl/.mps-profile.lock'
OUT = ROOT/'outputs/prowl/local-expert'


def command(args, timeout=20):
    return subprocess.check_output(args, timeout=timeout, stderr=subprocess.PIPE)


def http(port, path, payload=None, timeout=5):
    req = Request(f'http://127.0.0.1:{port}/{path}',
                  data=None if payload is None else json.dumps(payload).encode(),
                  headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=timeout) as r: return json.load(r)


def gpu_busy():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a+b') as f:
        try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return True
        return False


def status():
    result = dict(drive=False, database=False, search=False, ollama=False,
                  model=False, gpu_busy=gpu_busy())
    try:
        c = read_config(CONFIG); limits(c); result['drive'] = True
        with connect(c) as db:
            result['database'] = db.execute('SELECT 1').fetchone()[0] == 1
    except Exception: pass
    try: result['search'] = http(8016, 'literature-search/health')['backend'] == 'checked'
    except Exception: pass
    try:
        models = http(11434, 'api/ps')['models']; result['ollama'] = True
        result['model'] = any(m.get('name') == MODEL and m.get('digest') == MODEL_SHA for m in models)
    except Exception: pass
    return result


def listening(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


def start_process(argv, name):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/(name+'.log')).open('ab') as log:
        subprocess.Popen(argv, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT)),
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)


def wait_for(check, seconds):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        try:
            if check(): return
        except Exception: pass
        time.sleep(1)
    raise RuntimeError('A service did not become ready. Check the local service logs, then try again.')


def prepare():
    raw = json.loads(CONFIG.read_text())
    if not Path(raw['mount']).is_mount():
        try: command(['diskutil', 'mount', raw['volume_uuid']], 20)
        except Exception:
            raise RuntimeError('Connect or unlock PROWL-Data, then prepare again. No replacement data folder was created.')
    c = read_config(CONFIG); limits(c)
    try: command(['docker', '--context', 'desktop-linux', 'info', '--format', '{{json .}}'])
    except Exception:
        command(['open', '-a', 'Docker'])
        wait_for(lambda: command(['docker', '--context', 'desktop-linux', 'info', '--format', '{{json .}}']), 45)
    info = json.loads(command(['docker', '--context', 'desktop-linux', 'info', '--format', '{{json .}}']))
    if info['MemTotal'] > int(command(['sysctl', '-n', 'hw.memsize']))*.15:
        raise RuntimeError('Docker exceeds the existing memory budget. Review Docker settings before starting.')
    rows = json.loads(command(['docker', '--context', 'desktop-linux', 'inspect', 'prowl-literature-db-1']))
    container = rows[0]
    if not any(m['Source'] == c['data'] and m['Destination'] == '/var/lib/postgresql/data' for m in container['Mounts']):
        raise RuntimeError('Database mount differs from the configured drive; manual review is required.')
    if not container['State']['Running']:
        try:
            command(['docker', '--context', 'desktop-linux', 'start', 'prowl-literature-db-1'], 30)
        except subprocess.CalledProcessError as error:
            if b'invalid mount config' in (error.stderr or b''):
                raise RuntimeError('Docker cannot see the data drive. Restart Docker Desktop to refresh its mount, then prepare again. This button will not interrupt other Docker projects.') from None
            raise RuntimeError('The existing literature database could not start. Inspect its Docker status; no container was replaced.') from None
    def database_ready():
        with connect(c) as db: return db.execute('SELECT 1').fetchone()[0] == 1
    wait_for(database_ready, 20)
    if not listening(8016):
        start_process([str(ROOT/'.venv-retrieval/bin/python'), str(ROOT/'scripts/serve_literature_search.py'),
                       '--study-answers', '--general-extracts'], 'literature')
    wait_for(lambda: http(8016, 'literature-search/health')['backend'] == 'checked', 35)
    if gpu_busy(): return status()
    # Hold the same exclusive lock as training during model preparation.
    with LOCK.open('a+b') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return status()
        if not listening(11434): start_process(['ollama', 'serve'], 'ollama')
        wait_for(lambda: http(11434, 'api/tags'), 10)
        tags = http(11434, 'api/tags')['models']
        if not any(m.get('name') == MODEL and m.get('digest') == MODEL_SHA for m in tags):
            raise RuntimeError('The reviewed local model is missing or changed. No model was downloaded.')
        http(11434, 'api/generate', {'model': MODEL, 'stream': False, 'keep_alive': '10m'}, timeout=60)
    return status()


if __name__ == '__main__':
    try:
        action = sys.argv[1]
        if action not in ('status', 'prepare', 'gpu'): raise ValueError('Unknown action')
        value = {'gpu_busy': gpu_busy()} if action == 'gpu' else prepare() if action == 'prepare' else status()
        print(json.dumps(value))
    except Exception as e:
        print(json.dumps({'error': str(e) if isinstance(e, RuntimeError) else 'Preparation could not finish. Check the drive and local service logs.'}))
