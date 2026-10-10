import hashlib
import pytest
from scripts.acquisition.download_panorama_windows import validate_response, verify, transfer


@pytest.mark.parametrize('status,headers,offset,valid', [
    (200, {'Content-Length': '10'}, 0, True),
    (206, {'Content-Length': '6', 'Content-Range': 'bytes 4-9/10'}, 4, True),
    (200, {'Content-Length': '10'}, 4, False),
    (206, {'Content-Range': 'bytes 5-9/10'}, 4, False),
    (200, {'Content-Length': '11'}, 0, False),
    (200, {'Content-Encoding': 'gzip'}, 0, False),
])
def test_response(status, headers, offset, valid):
    if valid: validate_response(status, headers, offset, 10)
    else:
        with pytest.raises(ValueError): validate_response(status, headers, offset, 10)


def test_verified_file_and_failures(tmp_path):
    path = tmp_path / 'batch.zip'; path.write_bytes(b'test')
    item = dict(bytes=4, publisher_md5=hashlib.md5(b'test').hexdigest())
    assert verify(path, item)['sha256'] == hashlib.sha256(b'test').hexdigest()
    with pytest.raises(ValueError): verify(path, dict(item, bytes=5))
    with pytest.raises(ValueError): verify(path, dict(item, publisher_md5='0'*32))
    assert path.read_bytes() == b'test'


def test_complete_partial_verified_without_network(tmp_path):
    (tmp_path / 'batch.zip.part').write_bytes(b'test')
    events = []
    transfer(dict(name='batch.zip', bytes=4, publisher_md5=hashlib.md5(b'test').hexdigest()),
             tmp_path, lambda *a: None, lambda event, **fields: events.append(event))
    assert events == ['starting', 'verified_download']
    assert (tmp_path / 'batch.zip').read_bytes() == b'test'


def test_oversize_preserved(tmp_path):
    path = tmp_path / 'batch.zip.part'; path.write_bytes(b'too large')
    with pytest.raises(ValueError):
        transfer(dict(name='batch.zip', bytes=4), tmp_path, lambda *a: None, lambda *a, **k: None)
    assert path.read_bytes() == b'too large'


@pytest.mark.parametrize('failure', [TimeoutError('read timed out'), ConnectionError('short transfer')])
def test_network_failure_resumes_and_verifies(tmp_path, monkeypatch, failure):
    from scripts.acquisition import download_panorama_windows as D
    calls = []
    class Response:
        def __init__(self, second):
            self.status = 206 if second else 200
            self.headers = {'Content-Length': '2' if second else '4'}
            if second: self.headers['Content-Range'] = 'bytes 2-3/4'
            self.chunks = iter([b'st', b''] if second else [b'te', failure])
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read1(self, size):
            value = next(self.chunks)
            if isinstance(value, Exception): raise value
            return value
    def connect(request, timeout):
        calls.append(request.get_header('Range'))
        return Response(len(calls) == 2)
    monkeypatch.setattr(D, 'urlopen', connect)
    events = []
    D.transfer_with_retries(dict(name='batch.zip', bytes=4, record_id=1,
        publisher_md5=hashlib.md5(b'test').hexdigest()), tmp_path, lambda *a: None,
        lambda event, **kw: events.append(event), sleep=lambda n: None)
    assert calls == [None, 'bytes=2-']
    assert events.count('retry_wait') == 1
    assert events[-1] == 'verified_download'
    assert (tmp_path/'batch.zip').read_bytes() == b'test'


@pytest.mark.parametrize('error', [ValueError('checksum'), RuntimeError('AC'), OSError('disk')])
def test_safety_errors_never_retry(tmp_path, monkeypatch, error):
    from scripts.acquisition import download_panorama_windows as D
    def fail(*args): raise error
    monkeypatch.setattr(D, 'transfer', fail)
    with pytest.raises(type(error)):
        D.transfer_with_retries({}, tmp_path, lambda: None, lambda *a, **k: pytest.fail('retry'),
                                sleep=lambda n: pytest.fail('sleep'))


def test_retry_budget_and_http_policy(tmp_path, monkeypatch):
    from scripts.acquisition import download_panorama_windows as D
    from urllib.error import HTTPError
    assert D.retry_delay(HTTPError('u', 404, '', {}, None), 0) is None
    assert D.retry_delay(HTTPError('u', 429, '', {'Retry-After': '120'}, None), 0) == 120
    calls = []
    def fail(*args):
        calls.append(1)
        raise TimeoutError()
    monkeypatch.setattr(D, 'transfer', fail)
    with pytest.raises(TimeoutError):
        D.transfer_with_retries({'name':'x'}, tmp_path, lambda: None, lambda *a, **kw: None,
                                max_retries=2, sleep=lambda n: None)
    assert len(calls) == 3
