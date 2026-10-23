import json
import pytest
from src.retrieval.general_fallback import generate, MODEL, MODEL_SHA

EVIDENCE=[dict(rank=1,record=dict(text='The invented organ releases digestive enzymes.',citation=dict(title='Invented source')))]

def provider(*,empty=False,repair=False,bad=False):
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        schema=payload['format']['properties']
        if 'claims' in schema:
            value=dict(claims=[] if empty and len(calls)==1 else [dict(text='The invented organ releases digestive enzymes.',citations=[dict(source='P1')])])
        elif 'checks' in schema:
            n=payload['format']['properties']['checks']['minItems']
            value=dict(checks=[dict(claim=i,decision='unsupported' if bad else 'supported',reason='The source directly states this fact.') for i in range(1,n+1)],scope=dict(decision='pass',reason='No clinical or private content.'))
        elif 'missing' in schema:
            body=json.loads(payload['messages'][1]['content'])
            assert body['sources'][0]['text']==EVIDENCE[0]['record']['text']
            missing=not body['claims']
            value=dict(decision='revise' if missing else 'pass',reason='The source provides the requested function.',missing=['Include the supported function.'] if missing else [])
        else:value=dict(decision='pass',reason='The answer is concise and clear.')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(value)))
    return call,calls


def test_supported_answer_binds_exact_source():
    call,calls=provider();r=generate('What does the invented organ do?',EVIDENCE,call)
    assert r['status']=='summarized' and r['revisions']==0
    assert r['claims'][0]['citations']==[dict(rank=1,quote=EVIDENCE[0]['record']['text'])]
    assert len(calls)==4


def test_empty_draft_is_repaired_from_evidence_not_accepted_as_gap():
    call,calls=provider(empty=True);r=generate('What does the invented organ do?',EVIDENCE,call)
    assert r['status']=='summarized' and r['revisions']==1 and len(calls)==8
    feedback=json.loads(calls[4]['messages'][1]['content'])['feedback']
    assert any(x['criterion']=='completeness' for x in feedback)


def test_persistently_unsupported_draft_never_returns():
    call,calls=provider(bad=True)
    with pytest.raises(ValueError,match='failed separate checks'):generate('What does it do?',EVIDENCE,call)
    assert len(calls)==8


def test_budget_rejects_before_model():
    def unexpected(*args):raise AssertionError('No model call')
    with pytest.raises(ValueError):generate('What does it do?',EVIDENCE*6,unexpected)
