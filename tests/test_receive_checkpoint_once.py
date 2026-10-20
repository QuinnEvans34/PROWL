import hashlib
import http.client
import importlib.util
import socket
import ssl
import subprocess
import threading
import time
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('checkpoint_receiver', Path(__file__).resolve().parents[1]/'scripts/receive_checkpoint_once.py')
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)


@pytest.fixture
def intake(tmp_path):
    cert, key = tmp_path/'cert.pem', tmp_path/'key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
                    '-subj','/CN=checkpoint-test','-addext','subjectAltName=IP:127.0.0.1',
                    '-keyout',str(key),'-out',str(cert)], check=True, capture_output=True)
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        port = s.getsockname()[1]
    payload, token = b'artificial checkpoint bytes', 'fixture-token'
    config = dict(bind='127.0.0.1',peer='127.0.0.1',port=port,ttl_seconds=2,
                  bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),
                  token_sha256=hashlib.sha256(token.encode()).hexdigest(),
                  certificate=str(cert),key=str(key),destination=str(tmp_path/'checkpoint'),receipt=str(tmp_path/'receipt.json'))
    return config, payload, token


def start(c):
    result = []
    t = threading.Thread(target=lambda: result.append(receiver.receive(c)))
    t.start()
    for _ in range(100):
        try:
            with socket.create_connection((c['bind'],c['port']),timeout=.1):
                break
        except OSError:
            time.sleep(.01)
    return t, result


def post(c, data, token, path='/checkpoint', length=None):
    context = ssl.create_default_context(cafile=c['certificate'])
    conn = http.client.HTTPSConnection(c['bind'],c['port'],context=context,timeout=3)
    conn.request('POST',path,data,{'Authorization':'Bearer '+token,'Content-Length':str(length or len(data))})
    response = conn.getresponse()
    status = response.status
    response.read()
    conn.close()
    return status


def test_rejects_token_path_length_then_accepts_once(intake):
    c,data,token = intake
    t,result = start(c)
    assert post(c,data,'wrong') == 403
    assert post(c,data,token,path='/other') == 403
    assert post(c,data,token,length=len(data)+1) == 403
    assert post(c,data,token) == 201
    t.join(3)
    assert not t.is_alive() and result[0]['status']=='verified'
    assert Path(c['destination']).read_bytes()==data
    with pytest.raises(OSError):
        socket.create_connection((c['bind'],c['port']),timeout=.2)
    assert token not in Path(c['receipt']).read_text()


def test_bad_digest_never_publishes(intake):
    c,data,token = intake
    t,result = start(c)
    with pytest.raises(http.client.RemoteDisconnected):
        post(c,b'x'*len(data),token)
    t.join(3)
    assert result[0]['status']=='failed'
    assert not Path(c['destination']).exists()
    assert not Path(c['destination']+'.receiving').exists()


def test_wrong_peer_and_expiry(intake):
    c,data,token = intake
    c['peer']='127.0.0.2'
    t,result = start(c)
    with pytest.raises((OSError,ssl.SSLError)):
        post(c,data,token)
    t.join(3)
    assert not t.is_alive() and result[0]['status']=='expired'
    assert not Path(c['destination']).exists()


def test_deadline_closes_stalled_tls(intake):
    c,_,_ = intake
    t,result = start(c)
    with socket.create_connection((c['bind'],c['port']),timeout=1):
        t.join(3)
    assert not t.is_alive() and result[0]['status']=='expired'
    assert result[0]['elapsed_seconds'] < 3


def test_no_overwrite(intake):
    c,_,_ = intake
    Path(c['destination']).write_bytes(b'preserve')
    with pytest.raises(ValueError,match='Fresh'):
        receiver.receive(c)
    assert Path(c['destination']).read_bytes()==b'preserve'
