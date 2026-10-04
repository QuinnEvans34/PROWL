import json
from pathlib import Path
from copy import deepcopy
import pytest
import torch
from src.data.manifest_records import canonical,digest
from scripts.diagnostics import segmenter_lowrate_qualification_attempt02 as q,segmenter_lowrate_qualification as first


@pytest.fixture
def cli(monkeypatch,tmp_path):
    monkeypatch.setattr(q,'DEST',tmp_path/'attempt02')
    monkeypatch.setattr(q,'native_preflight',lambda:1000)
    monkeypatch.setattr(q.m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    monkeypatch.setattr(q,'pins',lambda:{'source':'a'*64})
    monkeypatch.setattr(q,'context',lambda:{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')})
    monkeypatch.setattr(q.a.c,'runtime',lambda:{'invented':'runtime'})
    return q


def test_preflight_failure_leaves_request_unprepared(cli,monkeypatch):
    def blocked():raise PermissionError('native monitor blocked')
    monkeypatch.setattr(cli,'native_preflight',blocked)
    with pytest.raises(PermissionError):cli.prepare()
    assert not cli.DEST.exists()


def test_preflight_failure_leaves_prepared_request_unconsumed(cli,monkeypatch):
    cli.prepare();pin=digest((cli.DEST/'request.json').read_bytes())
    def blocked():raise PermissionError('native monitor blocked')
    monkeypatch.setattr(cli,'native_preflight',blocked)
    with pytest.raises(PermissionError):cli.run(pin)
    assert not (cli.DEST/'consumed.json').exists()


def test_distinct_request_is_frozen_and_single_use(cli,capsys):
    cli.prepare();pin=capsys.readouterr().out.strip();r=cli.checked(pin)
    assert r['reviewed_fault_receipt_sha256']==cli.PREDECESSOR_PIN
    assert r['identity']['run_id'].endswith('attempt02') and r['identity']['config']['learning_rate']==.001
    assert r['native_preflight_sha256']==digest((cli.DEST/'native-preflight.json').read_bytes())
    with pytest.raises(FileExistsError):cli.prepare()


@pytest.mark.parametrize('field',['native_preflight','reviewed_fault_receipt_sha256','rate'])
def test_changed_preflight_parent_or_rate_refused(cli,field):
    cli.prepare();r=json.loads((cli.DEST/'request.json').read_bytes())
    if field=='native_preflight':
        (cli.DEST/'native-preflight.json').write_bytes(canonical({'substituted':True}))
        pin=digest((cli.DEST/'request.json').read_bytes())
    else:
        if field=='rate':r['identity']['config']['learning_rate']=.003
        else:r[field]='b'*64
        (cli.DEST/'request.json').write_bytes(canonical(r));pin=digest((cli.DEST/'request.json').read_bytes())
    with pytest.raises(ValueError):cli.checked(pin)


@pytest.mark.parametrize('fault',[None,'calls','worker','source','state'])
def test_consumed_fault_must_have_zero_updates_and_fixed_source(monkeypatch,tmp_path,fault):
    assert q.predecessor is first and q.DEST!=first.DEST
    expected={'prior':'a'*64};monkeypatch.setattr(first,'pins',lambda:expected)
    monkeypatch.setattr(q.a.c,'REPO',tmp_path)
    for name in q.CODE:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
    def verify(dest,pin):
        assert dest==first.DEST and pin==q.PREDECESSOR_PIN
        return dict(source_pins={'changed':'b'*64} if fault=='source' else expected,
                    state='qualified' if fault=='state' else 'consumed_incomplete',
                    worker_started=fault=='worker',synthetic_optimizer_calls=int(fault=='calls'))
    monkeypatch.setattr(q,'verify_package',verify)
    if fault:
        with pytest.raises(ValueError):q.pins()
    else:assert q.pins()==expected|{n:digest(n.encode()) for n in q.CODE}
