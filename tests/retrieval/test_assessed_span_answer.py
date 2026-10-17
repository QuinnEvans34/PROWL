import copy
import json
import pytest
from src.retrieval import assessed_span_answer as a, evidence_spans, span_answer


@pytest.fixture
def passages():
    return [dict(record=dict(passage=dict(passage_id=f'p{i}'), text=text)) for i, text in enumerate([
        'Handcrafted image measurements are computed after outlining the region of interest. The fitted model is evaluated using separate images.',
        'A different study examined ultrasound images and measured treatment response. Its result does not describe feature extraction.'
    ])]


def selection():
    return dict(intent='explanation', assessments={
        'P1':dict(reason='Explains measurement extraction.', support='direct'),
        'P2':dict(reason='Different empirical task.', support='none')},
        status='excerpts', span_ids=['P1:1-2'])


def api_for(value, calls, **envelope):
    def api(path, payload=None):
        calls.append((path,payload))
        if path == 'tags':return dict(models=[dict(name=a.MODEL,digest=span_answer.MODELS[a.MODEL])])
        return dict(done=True, done_reason='stop', message=dict(content=json.dumps(value)), **envelope)
    return api


def test_complete_assessment_materializes_only_exact_spans(passages):
    calls=[]
    result=a.generate_answer('Explain feature extraction',passages,call_api=api_for(selection(),calls))
    assert result['validation']=='exact_quotes_verified'
    assert result['answer']['extracts']==[dict(passage_id='p0',quote=passages[0]['record']['text'])]
    payload=calls[1][1]
    assert payload['think'] is False and payload['options']['num_predict']==1200
    assert set(json.loads(payload['messages'][1]['content']))=={'question','sources'}
    assert payload['format']['properties']['assessments']['required']==['P1','P2']
    assert result['selection']==selection()


@pytest.mark.parametrize('kind',['missing','foreign','excluded','contradiction','bad-intent','bad-reason','foreign-span','extra','too-many'])
def test_inconsistent_or_malformed_output_is_not_published(passages,kind):
    value=selection()
    if kind=='missing':del value['assessments']['P2']
    if kind=='foreign':value['assessments']['P9']=value['assessments'].pop('P2')
    if kind=='excluded':value['span_ids']=['P2:1-1']
    if kind=='contradiction':value.update(status='insufficient_evidence',span_ids=[])
    if kind=='bad-intent':value['intent']='diagnosis'
    if kind=='bad-reason':value['assessments']['P1']['reason']=' '*241
    if kind=='foreign-span':value['span_ids']=['P8:1-1']
    if kind=='extra':value['medical_advice']='invented'
    if kind=='too-many':value['span_ids']=['P1:1-1']*4
    result=a.generate_answer('Question',passages,call_api=api_for(value,[]))
    assert result['validation']=='generation_rejected' and not result['answer']['extracts']


def test_fresh_abstention_is_valid_and_empty_input_never_calls_model(passages):
    value=selection();value.update(status='insufficient_evidence',span_ids=[])
    value['assessments']['P1']['support']='context'
    calls=[]
    assert a.generate_answer('Absent trial?',passages,call_api=api_for(value,calls))['validation']=='exact_quotes_verified'
    assert [c[0] for c in calls]==['tags','chat']
    result=a.generate_answer('Question',[],call_api=lambda *_:pytest.fail('No call'))
    assert result['validation']=='no_passages' and result['model_called'] is False


def test_pin_mismatch_and_incomplete_generation_are_not_evidence(passages):
    with pytest.raises(OSError):a.generate_answer('Question',passages,call_api=lambda *_:dict(models=[]))
    def api(path,payload=None):
        return dict(models=[dict(name=a.MODEL,digest=span_answer.MODELS[a.MODEL])]) if path=='tags' else dict(done=True,done_reason='length',message=dict(content='{}'))
    assert a.generate_answer('Question',passages,call_api=api)['validation']=='generation_rejected'
    with pytest.raises(ValueError):a.generate_answer('Question',passages,reasoning=True)
    with pytest.raises(ValueError):a.generate_answer('Question',passages,model='qwen3:8b')


def test_runner_assessment_uses_retrieval_without_old_generation_or_gold(tmp_path,monkeypatch,passages):
    from scripts.retrieval import compare_scope_evaluator as runner
    from scripts.retrieval.evaluate_answers import checked_read
    suite=json.loads((runner.ROOT/'configs/evidence/evaluation/development-v1.json').read_text())
    monkeypatch.setattr(runner,'frozen_inputs',lambda *_:({}, {c['id']:dict(passages=passages) for c in suite['cases']}))
    calls=[];monkeypatch.setattr(a,'api',api_for(selection(),calls))
    monkeypatch.setattr('sys.argv',['compare','--selection',str(tmp_path/'unused'),'--output',str(tmp_path/'run'),
                                   '--policy','assessed-spans','--evaluator',a.MODEL])
    assert runner.main()==0
    manifest=checked_read(tmp_path/'run'/'manifest.json')
    assert manifest['generation_mode']=='assessed-spans' and manifest['reused_selection_manifest_sha256'] is None
    assert manifest['policy']==a.POLICY and 'src/retrieval/assessed_span_answer.py' in manifest['source_sha256']
    requests=[p for path,p in calls if path=='chat'];assert len(requests)==10
    for case,payload in zip(suite['cases'],requests):
        user=json.loads(payload['messages'][1]['content'])
        assert user==dict(question=case['question'],sources=evidence_spans.catalog(passages)[0])
