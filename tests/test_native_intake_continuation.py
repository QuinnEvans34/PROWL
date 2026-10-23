import json
from types import SimpleNamespace
import pytest
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from scripts.diagnostics import continue_native_intake as c


def fixture(tmp_path,monkeypatch,*,wrong_order=False):
    (tmp_path/'cohort').mkdir();(tmp_path/'pilot').mkdir()
    def record(name,role='train'):
        return dict(case_id=name,role=role,exact_target_roundtrip=True,annotated_field_exposure_18_visits=1.)
    (tmp_path/'cohort/cases.jsonl').write_bytes(canonical(record('b' if wrong_order else 'a')))
    (tmp_path/'pilot/cases.jsonl').write_bytes(canonical(record('b'))+b'\n')
    (tmp_path/'cohort/resources.json').write_bytes(canonical(dict(workers_reaped=True,seconds=10,peak_owned_rss_bytes=100)))
    (tmp_path/'pilot/visual-review.json').write_text('{}')
    (tmp_path/'request.json').write_text('{}')
    (tmp_path/'parser-amendment.json').write_bytes(canonical(dict(reused_pilot_sha256=sha256(tmp_path/'pilot/cases.jsonl'))))
    monkeypatch.setattr(c,'OUT',tmp_path);monkeypatch.setattr(c,'DEST',tmp_path/'cohort-complete')
    monkeypatch.setattr(c,'provider',lambda:SimpleNamespace(control=dict(train=['a','b','c'],validation=['d'])))
    monkeypatch.setattr(c,'verify',lambda:dict(cohort_seconds=100,worker_rss_bytes=1000))


def test_preserves_exact_prefix_and_reuses_future_pilot_without_replay(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch);c.prepare()
    r=json.loads((c.DEST/'request.json').read_text())
    assert r['reused_cases']==2
    assert r['remaining']==[['c','train'],['d','validation']]
    assert r['seconds_remaining']==90
    assert r['rss_bytes']==1000
    c.prepared()


def test_wrong_prefix_fails_before_continuation(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch,wrong_order=True)
    with pytest.raises(ValueError,match='exact ordered prefix'):c.prepare()


def test_changed_pilot_refuses_reuse(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch)
    with (tmp_path/'pilot/cases.jsonl').open('ab') as f:f.write(b'\n')
    with pytest.raises(ValueError,match='Pilot changed'):c.prepare()
