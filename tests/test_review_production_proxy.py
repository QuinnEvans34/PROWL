"""Real Vite proxy -> isolated review API; no models or production records."""
import json
import os
from pathlib import Path
import selectors
import shutil
import socket
import subprocess
import threading
import uuid
import urllib.error
import urllib.request

import pytest
import uvicorn
from test_review_store import package, store, request
from scripts.serve_reviews import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_production_proxy_preserves_save_and_origin_policy(store, tmp_path):
    node = os.environ.get('PROWL_TEST_NODE') or shutil.which('node')
    if not node or not (ROOT/'ui/node_modules/vite').exists():
        pytest.skip('Node24 and installed UI dependencies required')
    sock = socket.socket(); sock.bind(('127.0.0.1', 0))
    api_port = sock.getsockname()[1]
    from src.review.literature_attachments_v1 import LiteratureAttachments
    attachment_root = tmp_path/'attachments'; attachment_root.mkdir()
    attachments = LiteratureAttachments(attachment_root, store, node=node, minimum_free_bytes=0)
    server = uvicorn.Server(uvicorn.Config(create_app(store, port=api_port, attachments=attachments), log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets':[sock]}, daemon=True)
    thread.start()
    process = None
    try:
        with (tmp_path/'proxy.stderr.log').open('w') as err:
            process = subprocess.Popen([node, str(ROOT/'ui/tests/review-proxy-harness.mjs'),
                f'http://127.0.0.1:{api_port}'], cwd=ROOT/'ui', stdout=subprocess.PIPE,
                stderr=err, text=True)
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=20), 'Proxy startup timed out'
                line = process.stdout.readline()
            assert line, (tmp_path/'proxy.stderr.log').read_text()
            port = json.loads(line)['port']
            def call(path, body=None, *, host='127.0.0.1:5180', origin='http://127.0.0.1:5180', site='same-origin'):
                headers = {'Host':host, 'Origin':origin, 'Sec-Fetch-Site':site}
                data = None if body is None else json.dumps(body).encode()
                if data is not None: headers['Content-Type'] = 'application/json'
                req = urllib.request.Request(f'http://127.0.0.1:{port}/review-records/'+path,
                                             data=data, headers=headers)
                try: response = urllib.request.urlopen(req, timeout=10)
                except urllib.error.HTTPError as error: response = error
                with response:
                    raw = response.read().decode()
                    return response.status, json.loads(raw) if response.headers.get_content_type() == 'application/json' else raw
            body = request(store)
            for invalid in ({'origin':'https://foreign.invalid'}, {'host':'foreign.invalid'}, {'site':'cross-site'}):
                assert call('targets/saved', body, **invalid)[0] == 403
                assert store.target('saved')['history'] == []
            code, saved = call('targets/saved', body)
            assert code == 200
            assert call('targets/saved', body) == (200, saved)  # lost-ack retry
            code, reopened = call('targets/saved', host='localhost:5180', origin='http://localhost:5180')
            assert code == 200 and reopened['history'] == [saved]
            identity = body['manifest_sha256']
            assert call('targets/archive/'+identity)[1]['history'] == [saved]
            assert len(store.target('saved')['history']) == 1
            from test_case_literature_workflow_v1 import capture_fixture
            from src.review.store import encode, digest
            capture = encode(capture_fixture()).decode()
            event = saved['event']['review_event_id']
            route = f'literature/{identity}/{event}'
            attachment_body = dict(capture_text=capture, review_receipt=saved['receipt'])
            assert call(route, attachment_body, origin='https://foreign.invalid')[0] == 403
            assert call(route)[1] == {'attachments':[]}
            wrong_receipt = dict(saved['receipt'], content_sha256='0'*64)
            assert call(route, dict(attachment_body, review_receipt=wrong_receipt))[0] == 400
            assert call(route)[1] == {'attachments':[]}
            code, attached = call(route, attachment_body)
            assert code == 200 and attached['state'] == 'published'
            code, retried = call(route, attachment_body)
            assert code == 200 and retried['receipt_sha256'] == attached['receipt_sha256']
            assert len(call(route)[1]['attachments']) == 1
            newer_body = dict(body, request_id=str(uuid.uuid4()), expected_latest_id=event,
                              action='reject', reason_codes=['missed_lesion'])
            code, newer = call('targets/archive/'+identity, newer_body)
            assert code == 200 and newer['event']['revision'] == 2
            newer_route = f"literature/{identity}/{newer['event']['review_event_id']}"
            assert call(newer_route)[1] == {'attachments':[]}
            artifact = attached['artifact_id'].split(':')[1]
            reopen_route = f"literature-capture/{artifact}/{attached['receipt_sha256']}"
            code, opened = call(reopen_route)
            assert code == 200 and opened['review'] == saved
            assert opened['capture'] == json.loads(capture)
            assert opened['binding']['capture_sha256'] == digest(capture.encode())
            assert call('targets/archive/'+identity)[1]['history'] == [saved, newer]
            assert len(list(attachment_root.glob('ref-*.json'))) == 1
    finally:
        if process is not None:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
            if process.stdout: process.stdout.close()
        server.should_exit = True; thread.join(timeout=10); sock.close()
        assert not thread.is_alive(), 'Isolated API did not stop'
