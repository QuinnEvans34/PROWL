"""Bounded local prediction jobs. No model is loaded by the API process.

The operator pins a worker and a small development catalog. A worker receives two
paths: request.json and a fresh output directory, and writes a native package.
This module never guesses a checkpoint or substitutes a stored prediction.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time
import uuid

HASH = re.compile(r'^[a-f0-9]{64}$')
FILES = {'manifest.json', 'ct.nii.gz', 'prediction.nii.gz', 'result.json', 'evidence.json'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


class JobError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


def checked_ref(ref):
    p = Path(ref['path'])
    if not p.is_absolute() or not p.is_file() or not HASH.fullmatch(ref['sha256']):
        raise ValueError('Invalid pinned input')
    if sha(p) != ref['sha256']:
        raise ValueError('Pinned input changed')


class PredictionJobs:
    def __init__(self, root, config=None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.config = copy.deepcopy(config)
        self.lock = threading.RLock()
        self.jobs = {}
        self.closed = False
        if config is None:
            return
        if os.name != 'posix':
            raise ValueError('This supervisor requires POSIX process groups')
        if config['schema'] != 'on-demand-worker-v1' or not Path(config['python']).is_absolute():
            raise ValueError('Invalid worker configuration')
        if config.get('device') not in ('cpu','mps','cuda'):
            raise ValueError('Explicit inference device required')
        if not 1 <= config['timeout_seconds'] <= 600 or not 64 <= config['rss_limit_mib'] <= 12288:
            raise ValueError('Invalid resource budget')
        if not 1 <= len(config['cases']) <= 20 or len({c['case_id'] for c in config['cases']}) != len(config['cases']):
            raise ValueError('Invalid case catalog')
        for c in config['cases']:
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', c['case_id']) or c['role'] != 'exposed_development':
                raise ValueError('Only named exposed development inputs are supported')
            for key in ('ct', 'pancreas'):
                if not HASH.fullmatch(c[key]['sha256']):
                    raise ValueError('Missing input identity')
        if not HASH.fullmatch(config['checkpoint']['sha256']) or not HASH.fullmatch(config['recipe_sha256']):
            raise ValueError('Missing model/recipe identity')
        if not config['code'] or not any(r['path'] == config['worker']['path'] and r['sha256'] == config['worker']['sha256'] for r in config['code']):
            raise ValueError('Worker must be included in code pins')
        self.identity = hashlib.sha256(canonical(config)).hexdigest()

    def catalog(self):
        return {'configured': self.config is not None, 'cases': [
            {'case_id': c['case_id'], 'prediction_mode': 'pancreas_assisted',
             'model_sha256': self.config['checkpoint']['sha256']}
            for c in self.config['cases']] if self.config else []}

    def snapshot(self, job):
        return {k: job[k] for k in ('job_id', 'case_id', 'status', 'request_identity', 'error')}

    def submit(self, case_id):
        with self.lock:
            if self.closed or self.config is None:
                raise JobError(503, 'Current inference worker is not configured.')
            case = next((c for c in self.config['cases'] if c['case_id'] == case_id), None)
            if case is None:
                raise JobError(404, 'Study is not in the inference catalog.')
            # Input hashes are verified inside the supervised worker before and after inference.
            if any(j['thread'].is_alive() for j in self.jobs.values()):
                raise JobError(409, 'Inference is busy. Wait for the active job or cancel it.')
            # Bounded session storage. Explicit deletion frees a slot; never evict a viewed result.
            if len(self.jobs) >= 4:
                raise JobError(409, 'Session result limit reached. Release an earlier result.')
            job_id = uuid.uuid4().hex
            directory = self.root / job_id
            directory.mkdir()
            request = dict(schema='on-demand-request-v1', job_id=job_id, case=case,
                           checkpoint=self.config['checkpoint'], recipe_sha256=self.config['recipe_sha256'],
                           code=self.config['code'], config_identity=self.identity, device=self.config['device'])
            identity = hashlib.sha256(canonical(request)).hexdigest()
            request['request_identity'] = identity
            (directory/'request.json').write_bytes(canonical(request))
            job = dict(job_id=job_id, case_id=case_id, status='queued', error=None,
                       request_identity=identity, directory=directory, request=request,
                       cancel=threading.Event(), thread=None)
            self.jobs[job_id] = job
            job['thread'] = threading.Thread(target=self._run, args=(job,), daemon=True)
            job['thread'].start()
            return self.snapshot(job)

    def get(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise JobError(404, 'Prediction job not found.')
            return self.snapshot(self.jobs[job_id])

    def cancel(self, job_id):
        with self.lock:
            self.get(job_id)
            j = self.jobs[job_id]
            j['cancel'].set()
            if j['status'] in ('queued', 'running'):
                j['status'] = 'cancelling'
            return self.snapshot(j)

    def release(self, job_id):
        # No recursive deletion of an operator-selected directory. Only owned job files.
        import shutil
        with self.lock:
            self.get(job_id)
            j = self.jobs[job_id]
            if j['thread'].is_alive():
                raise JobError(409, 'Cancel the active job and wait before releasing it.')
            shutil.rmtree(j['directory'])
            del self.jobs[job_id]

    def artifact(self, job_id, name):
        with self.lock:
            self.get(job_id)
            j = self.jobs[job_id]
            if j['status'] != 'ready' or name not in FILES:
                raise JobError(404, 'Verified prediction artifact unavailable.')
            p = j['directory']/'package'/name
            expected = j['artifacts'][name]
            if p.is_symlink() or not p.is_file() or p.stat().st_size != expected['bytes'] or sha(p) != expected['sha256']:
                raise JobError(409, 'Prediction artifact changed.')
            return p

    def _verify(self, job):
        folder = job['directory']/'package'
        if folder.is_symlink() or {p.name for p in folder.iterdir()} != FILES:
            raise ValueError('Incomplete worker package')
        for p in folder.iterdir():
            cap = 64*1024**2 if p.name.endswith('.nii.gz') else 1024**2
            if p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= cap:
                raise ValueError('Invalid output file')
        m = json.loads((folder/'manifest.json').read_bytes())
        req = job['request']
        if (m['schema_version'] != 'assisted-prediction-view-v1' or m['case_id'] != job['case_id']
                or m['request_identity'] != job['request_identity'] or m['prediction_id'] != job['job_id']
                or m['prediction_mode'] != 'pancreas_assisted' or m['reference_inputs_used'] is not True
                or m['model_sha256'] != {'segmenter': req['checkpoint']['sha256']}
                or m['recipe_sha256'] != req['recipe_sha256']
                or m['assistance_sha256'] != req['case']['pancreas']['sha256']
                or m['files']['ct']['content_sha256'] != req['case']['ct']['sha256']):
            raise ValueError('Worker output identity differs')
        artifacts = {p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in folder.iterdir()}
        for key, name in [('ct','ct.nii.gz'), ('pred','prediction.nii.gz'), ('result','result.json'), ('evidence','evidence.json')]:
            ref = m['files'][key]
            if ref != dict(uri=name, content_sha256=artifacts[name]['sha256'], bytes=artifacts[name]['bytes']):
                raise ValueError('Worker file identity differs')
        # Client also independently checks provenance, geometry, labels and numerical measurements.
        return artifacts

    def _run(self, job):
        proc = None
        log = None
        started = time.monotonic()
        peak_rss = 0
        failure = None
        outcome = 'failed'
        try:
            with self.lock:
                if job['cancel'].is_set():
                    outcome = 'cancelled'
                    return
                job['status'] = 'running'
            # Launch only pinned local code; no request can specify a command or filesystem path.
            for ref in self.config['code']:
                checked_ref(ref)
            directory = job['directory']
            wrapper = Path(__file__).resolve().parents[2]/'scripts/run_on_demand_worker.py'
            # Private diagnostics are never served through the artifact allowlist.
            log = (directory/'worker.log').open('xb')
            proc = subprocess.Popen([self.config['python'], str(wrapper), self.config['worker']['path'],
                                     str(directory/'request.json'), str(directory/'package')],
                                    stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=log, start_new_session=True)
            while proc.poll() is None:
                if job['cancel'].is_set():
                    raise InterruptedError()
                if time.monotonic()-started > self.config['timeout_seconds']:
                    raise TimeoutError()
                # RSS of the dedicated process group, including worker children.
                rows = subprocess.check_output(['ps','-axo','pgid=,rss='], timeout=3).decode().splitlines()
                rss = sum(int(r.split()[1])*1024 for r in rows if len(r.split()) == 2 and int(r.split()[0]) == proc.pid)
                peak_rss = max(peak_rss, rss)
                if rss > self.config['rss_limit_mib']*1024**2:
                    raise MemoryError()
                if (directory/'worker.log').stat().st_size > 1024**2:
                    raise ValueError('Diagnostic output budget exceeded')
                size = sum(p.lstat().st_size for p in directory.rglob('*') if p.is_file())
                if size > 132*1024**2:
                    raise ValueError('Output budget exceeded')
                job['cancel'].wait(.1)
            if proc.returncode != 0:
                raise ValueError('Worker failed')
            artifacts = self._verify(job)
            with self.lock:
                job['artifacts'] = artifacts
                outcome = 'cancelled' if job['cancel'].is_set() else 'ready'
        except InterruptedError:
            outcome = 'cancelled'
        except Exception as error:
            failure = type(error).__name__
            outcome = 'cancelled' if job['cancel'].is_set() else 'failed'
        finally:
            if proc is not None:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                proc.wait()
            if log is not None:
                log.close()
            try:
                (job['directory']/'execution.json').write_bytes(canonical(dict(
                    elapsed_seconds=time.monotonic()-started, sampled_peak_rss_bytes=peak_rss,
                    returncode=proc.returncode if proc is not None else None,
                    outcome=outcome, failure_type=failure, worker_reaped=proc is None or proc.poll() is not None)))
            except OSError:
                outcome = 'failed'
            with self.lock:
                job['status'] = 'cancelled' if job['cancel'].is_set() else outcome
                job['error'] = 'Prediction failed validation or exceeded its resource budget.' if job['status'] == 'failed' else None

    def close(self):
        with self.lock:
            self.closed = True
            jobs = list(self.jobs.values())
            for j in jobs: j['cancel'].set()
        for j in jobs: j['thread'].join(timeout=10)
