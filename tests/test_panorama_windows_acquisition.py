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
