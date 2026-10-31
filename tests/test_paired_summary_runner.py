import json
import pytest
from scripts.retrieval import compare_single_summary_candidate as m
from test_single_summary_review_runner import sources


def fixture(tmp_path):
    out=tmp_path/'review';manifest=m.prepared(out,sources(tmp_path));return out,manifest


def test_preparation_has_frozen_pair_no_calls(tmp_path,monkeypatch):
    monkeypatch.setattr(m,'api',lambda *a,**k:pytest.fail('No model calls'))
    out,manifest=fixture(tmp_path)
    assert manifest['max_logical_requests']==20
    assert manifest['comparison']['baseline']['request_seconds']==90
    assert 'Pending' in (out/'paired-review.md').read_text() or 'pending' in (out/'paired-review.md').read_text()
    with pytest.raises(FileExistsError):m.prepared(out,tmp_path/'source')


def test_identical_inputs_cold_warm_and_timings(tmp_path):
    out,manifest=fixture(tmp_path);loaded=False;seen=[]
    def transport(path,payload=None,**kw):
        nonlocal loaded
        if path=='generate':loaded=False;return {}
        if path=='ps':return dict(models=[dict(digest=m.candidate.MODEL_SHA)] if loaded else [])
        assert path=='chat';loaded=True
        return dict(total_duration=2_000_000_000,eval_count=7)
    def generate(question,evidence,call):
        seen.append((question,evidence));call('chat',{'model':m.candidate.MODEL})
        return dict(coverage='supported',claims=[dict(text='Invented answer',citations=[dict(rank=1,quote=evidence[0]['record']['text'])])],limitation='')
    results=m.evaluate(out,manifest,transport,generators={'baseline':generate,'candidate':generate})
    assert len(results)==20 and len(seen)==20
    assert all(pair==seen[0] for pair in seen)
    assert all(r['calls'][0]['seconds']['total_duration']==2 for r in results)
    assert all(r['calls'][0]['seconds']['load_duration'] is None for r in results)
    assert [r['arm'] for r in results[:8]]==['baseline','baseline','candidate','candidate','candidate','candidate','baseline','baseline']
    summary=json.loads((out/'timing-summary.json').read_text())
    assert summary['complete_warm_pairs']==5 and summary['promoted'] is False


def test_unload_failure_never_generates(tmp_path):
    out,manifest=fixture(tmp_path)
    def transport(path,*a,**k):return dict(models=[dict(name=m.candidate.MODEL)])
    result=m.evaluate(out,manifest,transport,generators={'baseline':lambda *a:pytest.fail('must not run')})
    assert result==[] and (out/'setup-failure.json').exists()


def test_failures_preserved_without_retry_or_false_warm(tmp_path):
    out,manifest=fixture(tmp_path);calls=[]
    def transport(path,*a,**k):
        if path=='chat':calls.append(path);raise TimeoutError('invented')
        return dict(models=[])
    def generate(q,e,call):return call('chat',{})
    rows=m.evaluate(out,manifest,transport,generators=dict(baseline=generate,candidate=generate))
    assert len(calls)==10 # one cold failure per packet/arm, not retried as warm
    assert all('failure' in r for r in rows)
    assert rows[0]['calls'][0]['failure']=="TimeoutError('invented')"
    assert json.loads((out/'timing-summary.json').read_text())['complete_warm_pairs']==0


def test_total_budget_stops_before_model(tmp_path):
    out,manifest=fixture(tmp_path);times=iter([0,1801])
    assert m.evaluate(out,manifest,lambda *a,**k:pytest.fail('budget'),clock=lambda:next(times))==[]


def test_second_attempt_cannot_overwrite_results(tmp_path):
    out,manifest=fixture(tmp_path)
    def transport(*a,**k):raise OSError('unload failed')
    m.evaluate(out,manifest,transport)
    with pytest.raises(FileExistsError):m.evaluate(out,manifest,transport)
