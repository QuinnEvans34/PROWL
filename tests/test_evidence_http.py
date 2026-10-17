"""Exercise Origin checks through the shared HTTP handler without models or a database."""
import importlib.util
import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest

from src.retrieval.guided_fixture import ResponseStore

spec = importlib.util.spec_from_file_location(
    'evidence_http', Path(__file__).resolve().parents[1] / 'scripts/serve_evidence_fixture.py')
http = importlib.util.module_from_spec(spec)
spec.loader.exec_module(http)


@pytest.fixture
def service(tmp_path):
    store = ResponseStore(tmp_path)
    server = http.LocalFixtureServer(('127.0.0.1', 0), http.handler_for(store))
    thread = Thread(target=server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', tmp_path
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize('origin', ['http://127.0.0.1:5180', 'http://127.0.0.1:5179', 'http://localhost:5173'])
def test_local_ui_can_save_and_retry(service, origin):
    url, directory = service
    request = {'request_id': str(uuid4()), 'question_id': 'workflow'}
    def post():
        with urlopen(Request(url + http.PREFIX, data=json.dumps(request).encode(),
                headers={'Content-Type': 'application/json', 'Origin': origin}), timeout=3) as reply:
            assert reply.status == 200
            return json.load(reply)
    first = post()
    assert post() == first
    assert len(list(directory.glob('*.json'))) == 1


@pytest.mark.parametrize('origin', ['https://unrelated.example', 'http://127.0.0.1:5181', 'null'])
def test_foreign_origin_cannot_publish(service, origin):
    url, directory = service
    with pytest.raises(HTTPError) as error:
        urlopen(Request(url + http.PREFIX,
            data=json.dumps({'request_id': str(uuid4()), 'question_id': 'workflow'}).encode(),
            headers={'Content-Type': 'application/json', 'Origin': origin}), timeout=3)
    assert error.value.code == 403
    assert not list(directory.iterdir())
