"""Explicit local UI preparation; fixed commands only, no ingestion or model download."""
import fcntl
import json
import os
import signal
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
from src.retrieval.direct_ingestion import digest
from src.operations.full_training_platform import require_ac
CONFIG = ROOT/'infra/retrieval/.env.local-expert.json'
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


def ac_power():
    try: require_ac(); return True
    except Exception: return False


def status():
    result = dict(drive=False, database=False, search=False, ollama=False,
                  model=False, gpu_busy=answer_gpu_busy())
    result['ac_power'] = ac_power()
    result['answer_blocker'] = 'ac_power' if not result['ac_power'] else 'gpu_busy' if result['gpu_busy'] else None
    expected = None
    try:
        c = read_config(CONFIG); limits(c); result['drive'] = True
        expected = digest(c)
        with connect(c) as db:
            result['database'] = db.execute('SELECT 1').fetchone()[0] == 1
    except Exception: pass
    try:
        result['search'] = backend_ready(expected)
        if result['search'] and http(8016, 'literature-search/health').get('answer_policy') == 'sources-only' and not result['answer_blocker']:
            result['answer_blocker'] = 'sources_only'
    except Exception: pass
    try:
        models = http(11434, 'api/ps')['models']; result['ollama'] = True
        result['model'] = any(m.get('name') == MODEL and m.get('digest') == MODEL_SHA for m in models)
    except Exception: pass
    return result


def answer_gpu_busy():
    """Candidate owns the exclusive lock while serving; other owners block answers."""
    if not gpu_busy(): return False
    try:
        c = read_config(CONFIG)
        health = http(8016, 'literature-search/health')
        reserved = (health.get('backend') == 'checked'
                    and health.get('storage_identity') == digest(c)
                    and health.get('answer_policy') == 'single-pass-summary-v1'
                    and health.get('answer_gpu_reserved') is True)
        return not reserved
    except Exception:
        return True


def backend_ready(identity):
    if identity is None:return False
    health=http(8016, 'literature-search/health')
    return health.get('backend')=='checked' and health.get('storage_identity')==identity


def listening(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


def start_process(argv, name):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/(name+'.log')).open('ab') as log:
        child = subprocess.Popen(argv, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT)),
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    (OUT/(name+'-owner.json')).write_text(json.dumps(dict(pid=child.pid,argv=argv,identity=process_identity(child.pid))))
    return child


def process_identity(pid):
    try: return command(['ps','-p',str(pid),'-o','lstart=,command=']).decode().strip()
    except subprocess.CalledProcessError: return ''


def record_ready_owner(child):
    # macOS can rewrite Python's executable name during startup. Bind ownership
    # after health admission, when the interpreter has finished that transition.
    owner_path = OUT/'literature-owner.json'
    owner = json.loads(owner_path.read_text())
    identity = process_identity(child.pid)
    if owner['pid'] != child.pid or child.poll() is not None or not identity:
        raise RuntimeError('Search became ready but its process ownership could not be recorded. Inspect services before enabling AI answers.')
    owner['identity'] = identity
    owner_path.write_text(json.dumps(owner))


def stop_owned_sources():
    try:
        owner = json.loads((OUT/'literature-owner.json').read_text())
        expected = [str(ROOT/'.venv-retrieval/bin/python'), str(ROOT/'scripts/serve_single_summary_candidate.py'),
                    '--config',str(CONFIG),'--port','8016','--sources-only']
        if type(owner['pid']) is not int or owner['pid'] <= 0 or owner['argv'] != expected or not owner['identity'] or process_identity(owner['pid']) != owner['identity']:
            raise ValueError('Owner identity differs')
    except (OSError,KeyError,TypeError,ValueError):
        raise RuntimeError('Source search is available, but its ownership could not be verified. No service was stopped; use Find sources and inspect the service before enabling AI answers.') from None
    os.kill(owner['pid'],signal.SIGTERM)
    wait_for(lambda: not listening(8016) and process_identity(owner['pid']) != owner['identity'],5,stage='Stopping the owned source-only service')


def wait_for(check, seconds, *, stage='Local service', process=None):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if process is not None and process.poll() is not None:
            raise RuntimeError(f'{stage} exited before becoming ready. Check local service status and its log; no retry was started.')
        try:
            if check(): return
        except Exception: pass
        time.sleep(1)
    raise RuntimeError(f'{stage} did not become ready within {seconds} seconds. Check local service status and its log before preparing again.')


def prepare_model():
    # Complete warmup before the candidate takes its lifetime reservation.
    # A concurrent trainer winning the lock leaves source search available.
    require_ac()
    with LOCK.open('a+b') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return False
        process = None if listening(11434) else start_process(['ollama', 'serve'], 'ollama')
        wait_for(lambda: http(11434, 'api/tags'), 10,stage='Local model service',process=process)
        tags = http(11434, 'api/tags')['models']
        if not any(m.get('name') == MODEL and m.get('digest') == MODEL_SHA for m in tags):
            raise RuntimeError('The reviewed local model is missing or changed. No model was downloaded.')
        require_ac()
        http(11434, 'api/generate', {'model': MODEL, 'stream': False, 'keep_alive': '10m'}, timeout=60)
        return True


def prepare():
    raw = json.loads(CONFIG.read_text())
    if raw.get('storage','external')=='external' and not Path(raw['mount']).is_mount():
        try: command(['diskutil', 'mount', raw['volume_uuid']], 20)
        except Exception:
            raise RuntimeError('Connect or unlock PROWL-Data, then prepare again. No replacement data folder was created.')
    c = read_config(CONFIG); limits(c)
    try: command(['docker', '--context', 'desktop-linux', 'info', '--format', '{{json .}}'])
    except Exception:
        command(['open', '-a', 'Docker'])
        wait_for(lambda: command(['docker', '--context', 'desktop-linux', 'info', '--format', '{{json .}}']), 45,stage='Docker Desktop')
    info = json.loads(command(['docker', '--context', 'desktop-linux', 'info', '--format', '{{json .}}']))
    if info['MemTotal'] > int(command(['sysctl', '-n', 'hw.memsize']))*.15:
        raise RuntimeError('Docker exceeds the existing memory budget. Review Docker settings before starting.')
    container_name=c.get('project','prowl-literature')+'-db-1'
    rows = json.loads(command(['docker', '--context', 'desktop-linux', 'inspect', container_name]))
    container = rows[0]
    if not any(m['Source'] == c['data'] and m['Destination'] == '/var/lib/postgresql/data' for m in container['Mounts']):
        raise RuntimeError('Database mount differs from the configured drive; manual review is required.')
    if not container['State']['Running']:
        try:
            command(['docker', '--context', 'desktop-linux', 'start', container_name], 30)
        except subprocess.CalledProcessError as error:
            if b'invalid mount config' in (error.stderr or b''):
                raise RuntimeError('Docker cannot see the data drive. Restart Docker Desktop to refresh its mount, then prepare again. This button will not interrupt other Docker projects.') from None
            raise RuntimeError('The existing literature database could not start. Inspect its Docker status; no container was replaced.') from None
    def database_ready():
        with connect(c) as db: return db.execute('SELECT 1').fetchone()[0] == 1
    wait_for(database_ready, 20,stage='Literature database')
    model_prepared = False
    process = None
    def start_search(sources_only):
        argv=[str(ROOT/'.venv-retrieval/bin/python'),str(ROOT/'scripts/serve_single_summary_candidate.py'),
              '--config',str(CONFIG),'--port','8016']
        if sources_only: argv.append('--sources-only')
        return start_process(argv,'literature')
    if not listening(8016):
        if ac_power() and not gpu_busy(): model_prepared = prepare_model()
        # Source search must remain available when training owns the accelerator.
        process = start_search(not ac_power() or gpu_busy() or not model_prepared)
    else:
        try:
            health = http(8016, 'literature-search/health')
        except Exception:
            health = None
        if isinstance(health, dict) and health.get('storage_identity') != digest(c):
            raise RuntimeError('Port 8016 is serving a different or older search configuration. Stop the verified old literature service, then prepare again. No process was stopped automatically.')
        if isinstance(health,dict) and health.get('answer_policy')=='sources-only' and ac_power() and not gpu_busy():
            model_prepared = prepare_model()
            if model_prepared:
                stop_owned_sources()
                process = start_search(not ac_power() or gpu_busy())
    wait_for(lambda: backend_ready(digest(c)), 35,stage='Literature search service',process=process)
    if process is not None: record_ready_owner(process)
    if not ac_power() or gpu_busy(): return status()
    if not model_prepared: prepare_model()
    return status()


if __name__ == '__main__':
    try:
        action = sys.argv[1]
        if action not in ('status', 'prepare', 'gpu'): raise ValueError('Unknown action')
        if action == 'gpu':
            power=ac_power();busy=answer_gpu_busy()
            value={'gpu_busy':busy,'ac_power':power,'answer_blocker':'ac_power' if not power else 'gpu_busy' if busy else None}
        else: value = prepare() if action == 'prepare' else status()
        print(json.dumps(value))
    except Exception as e:
        print(json.dumps({'error': str(e) if isinstance(e, RuntimeError) else 'Preparation could not finish. Check the drive and local service logs.'}))
