import hashlib
from pathlib import Path
import pytest
from scripts.prepare_week5_model_handoff import bound, export_control, ROOT


def test_bound_bytes_reject_tamper_and_symlink(tmp_path):
    p=tmp_path/'weights';p.write_bytes(b'invented')
    pin=hashlib.sha256(p.read_bytes()).hexdigest()
    assert bound(p,pin)==b'invented'
    with pytest.raises(ValueError,match='SHA256'):bound(p,'0'*64)
    with pytest.raises(ValueError,match='bounded'):bound(p,pin,limit=1)
    link=tmp_path/'link';link.symlink_to(p)
    with pytest.raises(ValueError,match='bounded'):bound(link,pin)


def test_export_refuses_repo_existing_or_wrong_selection(tmp_path):
    with pytest.raises(ValueError,match='20000'):export_control({'step':24000},tmp_path/'new')
    with pytest.raises(ValueError,match='outside checkout'):export_control({'step':20000},ROOT/'private-weights')
    with pytest.raises(FileExistsError):export_control({'step':20000},tmp_path)


def test_backup_mismatch_refused_before_loading(tmp_path):
    p=tmp_path/'source';p.write_bytes(b'not-pickle')
    b=tmp_path/'backup';b.write_bytes(b'changed')
    req=dict(step=20000,checkpoint=str(p),backup=str(b),checkpoint_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    with pytest.raises(ValueError,match='SHA256'):export_control(req,tmp_path/'new')
    assert not (tmp_path/'new').exists()
