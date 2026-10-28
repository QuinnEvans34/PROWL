import json,plistlib
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.retrieval import direct_corpus as dc
from scripts.retrieval import prepare_local_expert as prep

def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(dc,'ROOT',tmp_path)
    data=tmp_path/'outputs/prowl/literature-internal/data';data.mkdir(parents=True)
    password=tmp_path/'secret';password.write_text('invented');password.chmod(0o600)
    c=dict(storage='internal',project='prowl-literature-internal',port=55435,host='127.0.0.1',database='prowl_literature',user='prowl_literature',data=str(data),password_file=str(password),model_dir=str(tmp_path/'encoder'),encoder_descriptor=str(tmp_path/'descriptor'),mount='/System/Volumes/Data',volume_uuid='internal-id')
    calls=[]
    def info(args,**kw):calls.append(args);return plistlib.dumps(dict(VolumeUUID='internal-id'))
    monkeypatch.setattr(dc.subprocess,'check_output',info)
    p=tmp_path/'config.json';p.write_text(json.dumps(c));return c,p,calls

def test_internal_does_not_require_external_drive(tmp_path,monkeypatch):
    c,p,calls=fixture(tmp_path,monkeypatch)
    assert dc.read_config(p)==c
    assert all('/Volumes/PROWL-Data' not in a for a in calls)
    def usage(path):
        assert str(path)=='/System/Volumes/Data'
        return SimpleNamespace(free=60_000_000_000)
    monkeypatch.setattr(dc.shutil,'disk_usage',usage);dc.limits(c)

@pytest.mark.parametrize('field,value',[('volume_uuid','wrong'),('project','other'),('port',55433),('storage','unknown'),('data','/tmp'),('mount','/Volumes/PROWL-Data')])
def test_wrong_internal_identity_rejected(tmp_path,monkeypatch,field,value):
    c,p,_=fixture(tmp_path,monkeypatch);c[field]=value;p.write_text(json.dumps(c))
    with pytest.raises(ValueError):dc.read_config(p)

def test_internal_reserve_retained(tmp_path,monkeypatch):
    c,_,_=fixture(tmp_path,monkeypatch);monkeypatch.setattr(dc.shutil,'disk_usage',lambda _:SimpleNamespace(free=49_999_999_999))
    with pytest.raises(OSError,match='50 GB'):dc.limits(c)

def test_old_backend_cannot_be_mistaken_for_new(monkeypatch):
    monkeypatch.setattr(prep,'http',lambda *a:{'backend':'checked','storage_identity':'old'})
    assert not prep.backend_ready('new')
    assert prep.backend_ready('old')
    assert not prep.backend_ready(None)
