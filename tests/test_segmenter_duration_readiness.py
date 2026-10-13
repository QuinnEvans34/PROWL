"""Portable DUR-03 source and metadata refusal checks; no local receipts or jobs."""
import json
import os
from pathlib import Path
import pytest
from src.data.manifest_records import digest
from src.operations import segmenter_duration_readiness_v1 as repair
from src.operations.segmenter_duration_dispatch_v1 import verify_code

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name',sorted(repair.PROVENANCE))
def test_provenance_byte_forgery_refused(tmp_path,name):
    p=tmp_path/name;p.parent.mkdir(parents=True);p.write_bytes(b'forged metadata')
    with pytest.raises(ValueError,match='hash differs'):repair.read_pinned(tmp_path,name,repair.PROVENANCE[name])


# Reviewed metadata-only inventory from the historical DUR-03 receipt; no output lookup.
_SCRIPT_BYTES = (ROOT/'tests/fixtures/duration_readiness_script_paths.json').read_bytes()
assert digest(_SCRIPT_BYTES) == '53ec2b70bb7bdd646a4fbe26e2760a826652b30a550a247a963866c82780cf45'
SCRIPT_PATHS = tuple(json.loads(_SCRIPT_BYTES))


@pytest.mark.parametrize('name',SCRIPT_PATHS)
def test_script_path_exact_known_script_verifies(name):
    verify_code(dict(source_pins={name:digest((ROOT/name).read_bytes())}))


@pytest.mark.parametrize('name',SCRIPT_PATHS)
def test_script_path_hash_substitution_refuses(name):
    with pytest.raises(ValueError,match='identity changed'):verify_code(dict(source_pins={name:'a'*64}))


@pytest.mark.parametrize('name',['scripts/diagnostics/unapproved.py','scripts/unapproved.py','scripts/diagnostics/segmenter_duration_launch.py.npy','scripts/diagnostics/segmenter_duration_launch.py/../segmenter_duration_launch.py','/scripts/diagnostics/segmenter_duration_launch.py','outputs/patient.json','src/patient.nii.gz','tests/state.pt','configs/cache.npy'])
def test_script_path_unapproved_or_payload_refuses_before_open(name,monkeypatch):
    from src.operations import segmenter_duration_dispatch_v1 as dispatcher
    def denied(*a,**k):raise AssertionError('Disallowed source was opened')
    monkeypatch.setattr(dispatcher,'read_control',denied)
    with pytest.raises(ValueError,match='Code pin cannot'):verify_code(dict(source_pins={name:'a'*64}))


@pytest.mark.parametrize('unsafe',['symlink','hardlink','oversize'])
def test_script_path_safe_file_guards_retained(tmp_path,monkeypatch,unsafe):
    from src.operations import segmenter_duration_dispatch_v1 as dispatcher
    monkeypatch.setattr(dispatcher,'REPO',tmp_path);name='scripts/diagnostics/segmenter_duration_launch.py';path=tmp_path/name;path.parent.mkdir(parents=True);raw=b'no executable fixture calls'
    if unsafe=='symlink':
        other=tmp_path/'fixture.py';other.write_bytes(raw);path.symlink_to(other)
    elif unsafe=='hardlink':
        path.write_bytes(raw);os.link(path,tmp_path/'linked.py')
    else:raw=b'0'*(4*1024**2+1);path.write_bytes(raw)
    with pytest.raises(ValueError):verify_code(dict(source_pins={name:digest(raw)}))


def test_read_pinned_symlink_refused(tmp_path):
    p=tmp_path/'real.json';p.write_bytes(b'{}');(tmp_path/'link.json').symlink_to(p)
    with pytest.raises(ValueError,match='Unsafe'):repair.read_pinned(tmp_path,'link.json',digest(b'{}'))


def test_read_pinned_multiple_links_refused(tmp_path):
    p=tmp_path/'real.json';p.write_bytes(b'{}');os.link(p,tmp_path/'link.json')
    with pytest.raises(ValueError,match='type/size'):repair.read_pinned(tmp_path,'link.json',digest(b'{}'))


def test_read_pinned_size_refused(tmp_path):
    p=tmp_path/'large.json';p.write_bytes(b'0'*(4*1024**2+1))
    with pytest.raises(ValueError,match='type/size'):repair.read_pinned(tmp_path,'large.json',digest(p.read_bytes()))
