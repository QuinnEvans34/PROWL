"""Kill/restart a real HTTP process after selection; only synthetic data/callbacks."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
from http.client import RemoteDisconnected
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError

import pytest
from tests.retrieval.test_research_workflow import inputs, request
from tests.test_research_workflow_http import fetch
from src.retrieval.research_workflow import checked, publish

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'tests/retrieval/helpers/workflow_interrupt_server.py'


def wait_file(path, process):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        assert process.poll() is None, 'Owned fixture service exited early; inspect retained log'
        if path.exists():
            return checked(path)
        time.sleep(.02)
    pytest.fail(f'Owned service did not publish {path.name}')


@contextmanager
def service(root, mode):
    with (root / f'{mode}.log').open('w') as log:
        process = subprocess.Popen([sys.executable, str(HELPER), '--root', str(root), '--mode', mode],
                                   cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        try:
            ready = wait_file(root / f'{mode}-ready.json', process)
            assert ready['pid'] == process.pid
            yield process, f"http://127.0.0.1:{ready['port']}"
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def snapshot(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.json')}


def test_http_process_kill_after_selection_reuses_without_duplicate_answer(tmp_path, inputs):
    (tmp_path / 'inputs.json').write_text(json.dumps(dict(passages=inputs[0], generation=inputs[1])))
    original = request()
    parent_dir = tmp_path / 'runs' / original['request_id']
    with service(tmp_path, 'interrupt') as (process, url), ThreadPoolExecutor(1) as pool:
        pending = pool.submit(fetch, url + '/research-workflow/runs', original)
        barrier = wait_file(tmp_path / 'barrier.json', process)
        assert barrier['pid'] == process.pid
        running = fetch(url + '/research-workflow/runs/' + original['request_id'])
        assert running['state'] == 'running'
        assert [s['state'] for s in running['stages']] == ['completed', 'completed', 'running', 'pending']
        assert len(running['events']) == 5 and 'response' not in running
        with pytest.raises(HTTPError) as missing:
            fetch(url + '/research-workflow/responses/' + original['request_id'])
        assert missing.value.code == 404
        before = snapshot(parent_dir)
        assert not list((tmp_path / 'runs' / 'responses').glob('*.json'))
        process.kill()  # Exact Popen child only; no process-name or shared-service signals.
        assert process.wait(timeout=3) == -signal.SIGKILL
        with pytest.raises((RemoteDisconnected, ConnectionResetError, URLError)):
            pending.result(timeout=3)

    with service(tmp_path, 'recover') as (restarted, url):
        interrupted = fetch(url + '/research-workflow/runs/' + original['request_id'])
        assert interrupted == dict(running, state='interrupted')
        assert fetch(url + '/research-workflow/runs', original) == interrupted
        assert snapshot(parent_dir) == before
        assert not list((tmp_path / 'runs' / 'responses').glob('*.json'))
        recovery = request(resume_of=original['request_id'])
        saved = fetch(url + '/research-workflow/runs', recovery)
        assert saved['state'] == 'completed'
        assert [s['state'] for s in saved['stages']] == ['reused', 'reused', 'completed', 'completed']
        assert len(saved['events']) == 6
        assert saved['response']['generation'] == inputs[1]
        for event in saved['events'][:2]:
            parent = checked(parent_dir / f"{event['stage']}.json")
            assert event['reused_from'] == dict(run_id=original['request_id'], artifact_sha256=parent['content_sha256'])
        saved_dir = tmp_path / 'runs' / recovery['request_id']
        saved_before = snapshot(saved_dir)
        answer_path = tmp_path / 'runs' / 'responses' / f"{recovery['request_id']}.json"
        answer_before = answer_path.read_bytes()
        assert checked(answer_path) == saved['response']
        assert fetch(url + '/research-workflow/runs', recovery) == saved
        assert fetch(url + '/research-workflow/responses/' + recovery['request_id']) == saved['response']
        assert fetch(url + '/research-workflow/runs/' + original['request_id']) == interrupted
        assert snapshot(parent_dir) == before and snapshot(saved_dir) == saved_before
        assert answer_path.read_bytes() == answer_before
        assert list((tmp_path / 'runs' / 'responses').glob('*.json')) == [answer_path]
        calls = [json.loads(line) for line in (tmp_path / 'calls.jsonl').read_text().splitlines()]
        assert calls == [dict(kind='retrieve', mode='interrupt'), dict(kind='select', mode='interrupt')]
    assert restarted.poll() is not None and process.poll() is not None
    publish(tmp_path / 'verification.json', dict(parent_id=original['request_id'], recovery_id=recovery['request_id'],
        interrupted_state=interrupted['state'], recovery_stages=saved['stages'], parent_sha256=before,
        recovery_sha256=saved_before, response_sha256=saved['response']['content_sha256'],
        response_count=1, synthetic_callbacks=calls, real_model_calls=0,
        same_id_reuse_identical=True, original_history_unchanged=True, workers_reaped=True))
