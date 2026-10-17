"""Real loopback requests over synthetic evidence; no database or model service."""
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from tests.retrieval.test_research_workflow import inputs, store_at, request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from serve_research_workflow import workflow_handler, LocalFixtureServer


@pytest.fixture
def service(tmp_path, inputs):
    calls=[]
    def generate(*_):
        calls.append('select')
        return (dict(inputs[1],validation='generation_rejected') if len(calls)==1 else inputs[1])
    store=store_at(tmp_path,inputs,generate)
    server=LocalFixtureServer(('127.0.0.1',0),workflow_handler(store))
    thread=Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}',calls
    finally:server.shutdown();server.server_close();thread.join(2)


def fetch(url,payload=None,origin='http://127.0.0.1:5180'):
    with urlopen(Request(url,data=json.dumps(payload).encode() if payload is not None else None,
                headers={'Content-Type':'application/json','Origin':origin}),timeout=3) as reply:
        return json.load(reply)


def test_failure_then_linked_retry_and_download(service):
    url,calls=service;r=request();failed=fetch(url+'/research-workflow/runs',r)
    assert failed['state']=='failed'
    assert fetch(url+'/research-workflow/runs',r)==failed and calls==['select']
    with pytest.raises(HTTPError) as exc:fetch(url+'/research-workflow/responses/'+r['request_id'])
    assert exc.value.code==404
    saved=fetch(url+'/research-workflow/runs',request(resume_of=r['request_id']))
    assert saved['state']=='completed' and calls==['select','select']
    assert saved['stages'][0]['state']=='reused'
    assert fetch(url+'/research-workflow/runs/'+r['request_id'])==failed
    assert fetch(url+'/research-workflow/responses/'+saved['run_id'])==saved['response']
    assert fetch(url+'/research-workflow/health')['mode']=='research-workflow'


@pytest.mark.parametrize('kind,code',[('origin',403),('extra',400),('conflict',409),('unknown',404)])
def test_api_guards(service,kind,code):
    url,calls=service;r=request()
    if kind=='conflict':fetch(url+'/research-workflow/runs',r);r['question_id']='eus'
    if kind=='extra':r['patient_id']='rejected'
    with pytest.raises(HTTPError) as exc:
        fetch(url+('/unknown' if kind=='unknown' else '/research-workflow/runs'),r,
              'https://foreign.example' if kind=='origin' else 'http://127.0.0.1:5180')
    assert exc.value.code==code
    assert len(calls)==(1 if kind=='conflict' else 0)
