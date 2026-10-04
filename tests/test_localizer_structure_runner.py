import json
from pathlib import Path
import pytest
from scripts.diagnostics.localizer_structure_audit import checked, safe_path, consume, validate_selection, TRAIN_CODES


@pytest.mark.parametrize('relative', ['../secret', '/tmp/secret', ''])
def test_unsafe_paths_refused(tmp_path, relative):
    with pytest.raises(ValueError): safe_path(tmp_path, relative)


def test_changed_retained_bytes_and_symlink_refused(tmp_path):
    import hashlib
    p=tmp_path/'record.json'; p.write_bytes(b'original')
    pin=dict(bytes=8, sha256=hashlib.sha256(b'original').hexdigest())
    assert checked(tmp_path, p.name, pin) == p
    p.write_bytes(b'changed!')
    with pytest.raises(ValueError, match='changed'): checked(tmp_path, p.name, pin)
    p.unlink(); p.symlink_to(tmp_path/'missing')
    with pytest.raises(ValueError, match='Unsafe'): checked(tmp_path, p.name, pin)


def test_request_consumed_once_and_original_marker_preserved(tmp_path):
    consume(tmp_path, 'a'*64); original=(tmp_path/'started.json').read_bytes()
    with pytest.raises(FileExistsError): consume(tmp_path, 'b'*64)
    assert (tmp_path/'started.json').read_bytes() == original


@pytest.mark.parametrize('fault', ['duplicate', 'missing', 'wrong_train', 'wrong_stage', 'wrong_role'])
def test_incorrect_selection_refused(fault):
    rows=[dict(role='evaluator',study_id=f'pants:study:PanTS_{i:08}',step=300) for i in range(40)]
    rows += [dict(role='optimizer',study_id=f'pants:study:PanTS_{i:08}',step=300) for i in TRAIN_CODES]
    validate_selection(rows)
    if fault == 'duplicate': rows[0]=rows[1].copy()
    if fault == 'missing': rows.pop()
    if fault == 'wrong_train': rows[-1]['study_id']='pants:study:PanTS_00009999'
    if fault == 'wrong_stage': rows[0]['step']=150
    if fault == 'wrong_role': rows[0]['role']='optimizer'
    with pytest.raises(ValueError): validate_selection(rows)
