import hashlib
import io
import json
import tarfile
import pytest
from scripts.import_review_transfer import import_archive, sha


def archive(tmp_path, fault=None):
    path = tmp_path/'packet.tar.gz'
    data = b'Explicitly invented review transport bytes'
    member = 'case/result.json'
    row = dict(path=member, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    if fault == 'hash': row['sha256'] = '0'*64
    if fault == 'size': row['bytes'] += 1
    if fault == 'traversal': member = '../escape'; row['path'] = member
    if fault == 'absolute': member = '/escape'; row['path'] = member
    if fault == 'backslash': member = 'case\\escape'; row['path'] = member
    manifest = json.dumps(dict(schema='prowl-review-transfer-v1', files=[row])).encode()
    with tarfile.open(path, 'w:gz') as tar:
        for n, b in [('transfer-manifest.json', manifest), (member, data)]:
            m = tarfile.TarInfo(n); m.size = len(b)
            if fault == 'link' and n == member:
                m.type = tarfile.SYMTYPE; m.linkname = '/tmp/outside'; m.size = 0
            tar.addfile(m, io.BytesIO(b))
        if fault in ('duplicate', 'casefold', 'unlisted', 'conflict'):
            n = {'duplicate': member, 'casefold': member.upper(), 'unlisted': 'extra', 'conflict': 'case'}[fault]
            m = tarfile.TarInfo(n); m.size = 1; tar.addfile(m, io.BytesIO(b'x'))
    return path


def test_import_preserves_payload_and_creates_receipt(tmp_path):
    source = archive(tmp_path); output = tmp_path/'imported'
    r = import_archive(source, output, expected_sha256=sha(source))
    assert r['archive_sha256'] == sha(source)
    assert (output/'case/result.json').read_bytes().startswith(b'Explicitly invented')
    assert json.loads((output/'import-receipt.json').read_text()) == r
    with pytest.raises(ValueError, match='Fresh'):
        import_archive(source, output, expected_sha256=sha(source))


@pytest.mark.parametrize('fault', ['hash','size','traversal','absolute','backslash','link','duplicate','casefold','unlisted','conflict'])
def test_rejects_entire_bad_inventory_before_creating_destination(tmp_path, fault):
    source = archive(tmp_path, fault); output = tmp_path/'imported'
    with pytest.raises(ValueError): import_archive(source, output, expected_sha256=sha(source))
    assert not output.exists()


def test_bad_archive_pin_and_allocation_limits(tmp_path, monkeypatch):
    source = archive(tmp_path)
    with pytest.raises(ValueError, match='SHA256'): import_archive(source, tmp_path/'a', expected_sha256='0'*64)
    monkeypatch.setattr('scripts.import_review_transfer.MAX_TOTAL', 10)
    with pytest.raises(ValueError, match='Expanded'): import_archive(source, tmp_path/'b', expected_sha256=sha(source))
    assert not (tmp_path/'b').exists()
