"""Invented originals and mock device metadata only; no actual protected files."""
from pathlib import Path
import plistlib
from types import SimpleNamespace
import pytest
import yaml
from scripts.retrieval import setup_private_storage as s


def test_copy_exclusive_readback_and_owner_only(tmp_path):
    original=tmp_path/'original';original.write_text('Invented fixture only')
    dest=tmp_path/'copy'
    assert s.copy_verified(original,dest)==s.digest_file(original)
    assert dest.stat().st_mode&0o777==0o600
    with pytest.raises(FileExistsError):s.copy_verified(original,dest)
    assert original.read_text()=='Invented fixture only'


def test_changed_original_never_removed(tmp_path):
    original=tmp_path/'original';original.write_text('Invented original')
    st=original.stat();identity=(st.st_dev,st.st_ino);sha=s.digest_file(original)
    original.write_text('Invented changed')
    with pytest.raises(ValueError):s.relocate_verified_original(original,sha,identity)
    assert original.read_text()=='Invented changed'


def test_symlink_original_never_removed(tmp_path):
    original=tmp_path/'original';original.write_text('Invented')
    st=original.stat();link=tmp_path/'link';link.symlink_to(original)
    with pytest.raises(ValueError):s.relocate_verified_original(link,s.digest_file(original),(st.st_dev,st.st_ino))
    assert original.exists() and link.is_symlink()


def test_noninteractive_setup_refuses_before_draft_access(tmp_path,monkeypatch):
    monkeypatch.setattr(s.sys.stdin,'isatty',lambda:False)
    monkeypatch.setattr(s,'checked_roots',lambda *a:pytest.fail('Storage access reached'))
    with pytest.raises(ValueError,match='ordinary user Terminal'):s.setup(tmp_path)


@pytest.mark.parametrize('failure',['same_physical_kind','wrong_uuid','free_space','backup_cap'])
def test_bad_storage_admission_refused(tmp_path,monkeypatch,failure):
    cfg=tmp_path/'configs/local';cfg.mkdir(parents=True)
    a=tmp_path/'a';a.mkdir();b=tmp_path/'b';b.mkdir()
    reg=dict(roots=dict(prowl_artifacts=dict(path=str(a),failure_domain='a'),
        prowl_backup=dict(path=str(b),failure_domain='b',cap_bytes=4*s.SIZE)),
        failure_domains=dict(a=dict(volume_uuid='AAA',mount_path=str(a)),b=dict(volume_uuid='BBB',mount_path=str(b))))
    (cfg/'roots.yaml').write_text(yaml.safe_dump(reg))
    def native(args):
        if args[0]=='/usr/bin/du':return str(8*s.SIZE//1024).encode()+b'\tunused\n'
        primary=args[-1]==str(a)
        return plistlib.dumps(dict(VolumeUUID=('WRONG' if failure=='wrong_uuid' else ('AAA' if primary else 'BBB')),
            Internal=True if failure=='same_physical_kind' else not primary))
    monkeypatch.setattr(s,'native',native)
    monkeypatch.setattr(s.shutil,'disk_usage',lambda p:SimpleNamespace(free=s.FLOOR if failure=='free_space' else s.FLOOR+10*s.SIZE))
    # Fake separate device identities only for the budget branch; no actual mount operations.
    original_stat=Path.stat
    def fake_stat(p,*args,**kwargs):
        st=original_stat(p,*args,**kwargs)
        if failure=='backup_cap' and p in (a,b):
            fields={k:getattr(st,k) for k in dir(st) if k.startswith('st_')}
            fields['st_dev']=1 if p==a else 2
            return SimpleNamespace(**fields)
        return st
    monkeypatch.setattr(Path,'stat',fake_stat)
    with pytest.raises(ValueError):s.checked_roots(tmp_path)
