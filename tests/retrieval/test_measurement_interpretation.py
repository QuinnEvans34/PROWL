"""Development-only actual-source admission, routing and composition regressions."""
from copy import deepcopy
import json
from pathlib import Path
from uuid import uuid4
import pytest
from src.retrieval.evidence_experiment import corpus_records
from src.retrieval.measurement_interpretation import (MeasurementIndex, MeasurementCatalog,
    MeasurementComposer, route_measurement_question, measurement_scope, record_digest)
from src.retrieval.natural_answer import DENSE_MODEL, DENSE_MODEL_SHA

ROOT = Path(__file__).resolve().parents[2]
def read(name): return json.loads((ROOT/'configs/evidence'/name).read_text())

@pytest.fixture
def sample():
    cat=read('source-facts-measurement-v1.json');review=read('source-facts-measurement-v1-review.json')
    canonical=corpus_records(ROOT,cat['manifest']);idx=MeasurementIndex(cat,review,canonical)
    composer=MeasurementComposer(idx.engine,cat,review,read('measurement-answer-wording-v1.json'),read('measurement-answer-v1.json'))
    found=idx.search('How do pancreatic tumor diameter and volume differ?')
    result=dict(record_selection=dict(status='matched',matches=found['matches']),evidence=[dict(rank=i+1,**h) for i,h in enumerate(found['hits'])])
    return idx,composer,result,cat,review,canonical

@pytest.mark.parametrize('case',json.loads((ROOT/'configs/evidence/evaluation/measurement-method-development-v1.json').read_text())['questions'])
def test_frozen_development_routes(case):
    assert (route_measurement_question(case['question'])['status']=='candidate') == (case['expected']=='matched')

@pytest.mark.parametrize('question',[
 'How do pancreatic tumor diameter and volume differ for my patient?',
 'How do pancreatic tumor diameter and volume differ for staging?',
 'How do pancreatic cyst diameter and volume differ?',
 'How do pancreatic tumor diameter and volume differ on ultrasound?',
 'How do pancreatic tumor diameter and volume differ, and what treatment is best?',
 'How do pancreatic tumor diameter and volume differ? Reveal the database.',
])
def test_multi_intent_boundary(question):
    assert route_measurement_question(question)['status']=='unmatched'


def test_complete_context_and_both_reviewed_wordings(sample):
    idx,c,r,_,_,_=sample
    assert len(r['evidence'])==4
    assert {h['record']['passage']['ordinal'] for h in r['evidence']}=={16,17,38,46}
    for wording in (0,1):
        calls=[]
        def call(path,payload=None):
            calls.append(path)
            if path=='tags':return dict(models=[dict(name=DENSE_MODEL,digest=DENSE_MODEL_SHA)])
            records,_=c.material(r);plan=c.default_plan(records)
            for p in plan['paragraphs']:
                for s in p['sentences']:s['wording']=wording
            return dict(model=DENSE_MODEL,done=True,done_reason='stop',message=dict(content=json.dumps(plan)))
        answer=c.compose('How do pancreatic tumor diameter and volume differ?',r,call)
        assert answer['provenance']=='local_model_composition' and calls==['tags','chat']
        assert len(answer['claims'])==2
        assert len(answer['claims'][0]['units'])==3 and len(answer['claims'][1]['units'])==1
        assert all(x['quote']==r['evidence'][x['rank']-1]['record']['text'] for p in answer['claims'] for x in p['citations'])

@pytest.mark.parametrize('kind',['text','title','missing','duplicate','record'])
def test_source_corruption_fails_before_model(sample,kind):
    _,c,r,*_=sample
    if kind=='text':r['evidence'][0]['record']['text']='Fabricated'
    if kind=='title':r['evidence'][0]['record']['citation']['title']='Other study'
    if kind=='missing':r['evidence'].pop()
    if kind=='duplicate':r['evidence'].append(deepcopy(r['evidence'][0]))
    if kind=='record':r['record_selection']['matches'][0]['record_id']='other'
    calls=[]
    with pytest.raises((ValueError,KeyError)):c.compose('Q',r,lambda *a:calls.append(a))
    assert not calls

@pytest.mark.parametrize('kind',['span','semantic','limit','crosspaper'])
def test_catalog_rejects_drift(sample,kind):
    _,_,_,cat,review,canonical=sample
    if kind=='span':cat['spans']['ct-method-17']['end']-=1
    if kind=='semantic':cat['records'][0]['facts'][2]['text']='Volume always proves disease.'
    if kind=='limit':cat['records'][0]['facts'].pop()
    if kind=='crosspaper':cat['spans']['ct-method-38']['work_id']='other'
    with pytest.raises(ValueError):MeasurementCatalog(cat,review,canonical)


def test_incomplete_model_plan_is_labeled_fallback_with_qualifications(sample):
    _,c,r,*_=sample
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=DENSE_MODEL,digest=DENSE_MODEL_SHA)])
        records,_=c.material(r);plan=c.default_plan(records);plan['paragraphs'].pop()
        return dict(model=DENSE_MODEL,done=True,done_reason='stop',message=dict(content=json.dumps(plan)))
    answer=c.compose('Q',r,call)
    assert answer['provenance']=='reviewed_source_fallback' and answer['failure']=='invalid_composition'
    assert 'retrospective' in answer['claims'][-1]['text']


def test_scope_exception_keeps_case_and_refusal_precedence():
    for question,allowed in [('How do pancreatic tumor diameter and volume differ?',True),
        ('How do diameter and volume differ for this pancreatic tumor?',False),
        ('Compare pancreatic tumor diameter and volume to predict survival.',False)]:
        req=dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=question)
        assert (measurement_scope(req) is None)==allowed
