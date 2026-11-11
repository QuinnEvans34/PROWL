from io import BytesIO
import json
import tarfile

import pytest

from scripts.diagnostics import evaluate_native_small_lesion_outliner_20261111 as replay
from scripts.diagnostics.import_mac_stunet_32k_packet_20261111 import import_packet, sha


def make_packet(path, entries):
    with tarfile.open(path,'w') as tar:
        for name, data in entries:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member,BytesIO(data))


def test_private_packet_import_verifies_transport_and_members(tmp_path, monkeypatch):
    import hashlib
    model = b'synthetic mock weights'
    report = json.dumps(dict(step=32000,cases=[{} for _ in range(70)])).encode()
    digest = hashlib.sha256(report).hexdigest()
    monkeypatch.setattr(replay,'REPORT_SHA',digest)
    manifest = dict(step=32000,source_checkpoint_sha256=replay.CHECKPOINT_SHA,
                    independent_checkpoint_sha256=replay.CHECKPOINT_SHA,tensor_equality=True,
                    report_sha256=digest,model_sha256=hashlib.sha256(model).hexdigest())
    archive = tmp_path/'test.tar'
    make_packet(archive,[('model-only.pt',model),('native-32000.json',report),
                         ('manifest.json',json.dumps(manifest).encode())])
    out = tmp_path/'received'
    result = import_packet(archive,out,sha(archive))
    assert result['member_sha256']['native-32000.json'] == digest
    assert (out/'import-receipt.json').is_file()


def test_unapproved_packet_member_fails_before_extraction(tmp_path):
    archive = tmp_path/'unexpected.tar'
    make_packet(archive,[('model-only.pt',b'weights'),('../not-authorized',b'data')])
    output = tmp_path/'received'
    with pytest.raises(ValueError,match='Unexpected transfer member'):
        import_packet(archive,output,sha(archive))
    assert not output.exists()
