import pytest
from src.retrieval import readable_answer as module
from copy import deepcopy
from tests.retrieval.test_natural_answer import EVIDENCE as ORIGINAL
EVIDENCE=deepcopy(ORIGINAL)
for entry in EVIDENCE:
    entry["record"].setdefault("passage", {})["work_id"]="invented:paper"


def test_failed_generation_still_unloads_and_does_not_retry(monkeypatch):
    calls=[]
    def provider(path,payload=None):
        calls.append((path,payload))
        if path=='tags':raise OSError('unavailable')
        return dict(done=True,model=module.MODEL)
    with pytest.raises(OSError):module.generate_readable('Pancreas?',EVIDENCE,provider)
    assert [p for p,_ in calls]==['tags','generate']
    assert calls[-1][1]==dict(model=module.MODEL,keep_alive=0)


def test_expired_budget_never_starts_provider():
    calls=[]
    with pytest.raises(TimeoutError):module.generate_readable('Pancreas?',EVIDENCE,lambda *a:calls.append(a),deadline=0)
    assert not calls


def test_insufficient_skips_renderer_and_unloads(monkeypatch):
    def generate(q,e,call,deadline=None):
        call('tags');return dict(status='insufficient',claims=[],source_scope='top_ranked_paper')
    monkeypatch.setattr(module,'generate_qualified',generate)
    monkeypatch.setattr(module,'render_and_check',lambda *a:pytest.fail('No rendering for insufficient'))
    calls=[]
    def provider(path,payload=None):calls.append(path);return dict(done=True,model=module.MODEL)
    answer=module.generate_readable('Pancreas?',EVIDENCE,provider)
    assert answer['policy']==module.POLICY and answer['status']=='insufficient'
    assert calls==['tags','generate']
