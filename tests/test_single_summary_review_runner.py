import json
import pytest
from scripts.retrieval import check_single_summary_candidate as runner


def sources(tmp_path):
    source=tmp_path/'source';source.mkdir()
    evidence=[dict(rank=1,record=dict(text='An invented source states that glands release enzymes.',citation=dict(title='Invented source')))]
    for name in runner.NAMES:
        (source/f'{name}.json').write_text(json.dumps(dict(question='What does the invented gland do?',baseline=dict(evidence=evidence))))
    return source


def test_prepare_is_readable_and_never_calls_model(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'generate',lambda *a:pytest.fail('no model during preparation'))
    output=tmp_path/'review';manifest=runner.prepare(output,sources(tmp_path))
    assert len(manifest['packets'])==5
    assert 'Not run' in (output/'review.md').read_text()
    assert 'Invented source' in (output/'review.md').read_text()
    assert json.loads((output/'inputs.json').read_text())==manifest
    with pytest.raises(FileExistsError):runner.prepare(output,tmp_path/'source')


def test_invalid_last_packet_fails_before_output_creation(tmp_path):
    source=sources(tmp_path)
    (source/'gap.json').write_text(json.dumps(dict(question='Gap?',baseline=dict(evidence=[]))))
    with pytest.raises(ValueError,match='Evidence budget'):runner.prepare(tmp_path/'review',source)
    assert not (tmp_path/'review').exists()


def test_review_preserves_failure_and_separate_manual_decision(tmp_path,monkeypatch):
    output=tmp_path/'review';manifest=runner.prepare(output,sources(tmp_path))
    calls=[]
    def generate(question,evidence,call):
        calls.append(question)
        if len(calls)==2:raise TimeoutError('synthetic timeout')
        return dict(coverage='partial',limitation='Other functions are not described.',claims=[dict(text='The gland releases enzymes.',citations=[dict(rank=1,quote=evidence[0]['record']['text'])])])
    monkeypatch.setattr(runner,'generate',generate)
    runner.evaluate(output,manifest,lambda *a,**k:pytest.fail('synthetic only'))
    review=(output/'review.md').read_text()
    assert 'synthetic timeout' in review and 'Other functions are not described.' in review
    assert review.count('Manual review: **Pending**')==5
    assert len(calls)==5
    assert json.loads((output/'function_paraphrase.json').read_text())['promoted'] is False
