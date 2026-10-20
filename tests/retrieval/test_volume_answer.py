"""Public retained source admission and invented provider plans; no live model/database."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from src.retrieval.evidence_experiment import corpus_records
from src.retrieval.volume_record_search import VolumeRecordSearchIndex
from src.retrieval.volume_answer import VolumeComposer, LiteratureAnswers, LiteratureSearch, POLICY
from src.retrieval.natural_answer import DENSE_MODEL, DENSE_MODEL_SHA
from src.retrieval.direct_ingestion import digest

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def sample():
    read=lambda n:json.loads((ROOT/'configs/evidence'/n).read_text())
    cat=read('source-facts-volume-v1.json'); review=read('source-facts-volume-v1-review.json')
    wording=read('volume-answer-wording-v1.json'); config=read('volume-answer-v1.json')
    index=VolumeRecordSearchIndex(cat,review,corpus_records(ROOT,cat['manifest']))
    c=VolumeComposer(index.engine,cat,review,wording,config)
    found=index.search('Compare mean pancreas volume in normal glucose tolerance versus type 2 diabetes.')
    result=dict(record_selection=dict(status='matched',policy=index.search('pancreas volume')['policy'],matches=found['matches']),
        evidence=[dict(rank=i+1,**h) for i,h in enumerate(found['hits'])],answer=None,generation='not_called')
    return c,result,(index.engine,cat,review,wording,config)


def provider(c,r,mutation=lambda p:None):
    calls=[]
    def call(path,payload=None):
        calls.append(path)
        if path=='tags':return dict(models=[dict(name=DENSE_MODEL,digest=DENSE_MODEL_SHA)])
        records,_=c.material(r);p=c.default_plan(records)
        for para in p['paragraphs']:
            for choice in para['sentences']:choice['wording']=1
        mutation(p)
        return dict(model=DENSE_MODEL,done=True,done_reason='stop',message=dict(content=json.dumps(p)))
    return call,calls


def test_both_groups_complete_and_distinct_with_canonical_context(sample):
    c,r,_=sample;call,calls=provider(c,r);a=c.compose('Compare the study groups',r,call)
    assert a['policy']==POLICY and a['provenance']=='local_model_composition' and calls==['tags','chat']
    assert len(a['claims'])==4
    text=' '.join(p['text'] for p in a['claims'])
    for term in ('82.6','55.5','14 people','41 people','only metformin','MRI','±4.8','±2.8','SEM','age, weight and sex','not the spread','CT reference'):
        assert term in text
    assert all(cite['quote']==r['evidence'][cite['rank']-1]['record']['text'] for p in a['claims'] for cite in p['citations'])


@pytest.mark.parametrize('mutate',[
    lambda p:p['paragraphs'].pop(),
    lambda p:p['paragraphs'][0]['sentences'].pop(1),
    lambda p:p['paragraphs'][0]['sentences'][0].update(text='A normal pancreas is 82.6 cm3'),
    lambda p:p['paragraphs'][0]['sentences'][0].update(wording=True),
    lambda p:p['paragraphs'][0].update(record_id='other-population'),
])
def test_invalid_model_plan_keeps_all_source_facts_in_explicit_fallback(sample,mutate):
    c,r,_=sample;call,_=provider(c,r,mutate);a=c.compose('Q',r,call)
    assert a['provenance']=='reviewed_source_fallback' and a['model'] is None and len(a['claims'])==4


def test_reordered_complete_volume_plan_is_arranged_without_losing_model_choices(sample):
    c, r, _ = sample
    def reorder(plan):
        for paragraph in plan['paragraphs']:
            paragraph['sentences'].reverse()
            for choice in paragraph['sentences']: choice['wording'] = 1
    call, _ = provider(c, r, reorder)
    a = c.compose('Q', r, call)
    assert a['provenance'] == 'local_model_composition' and a['failure'] is None
    assert all(choice['wording'] == 1 for claim in a['claims'] for choice in claim['units'])
    assert 'standard error' in a['claims'][0]['text'] and 'does not provide a universal' in a['claims'][1]['text']


@pytest.mark.parametrize('kind',['text','citation','missing','extra','population'])
def test_source_failure_is_not_model_fallback(sample,kind):
    c,r,_=sample
    if kind=='text':r['evidence'][0]['record']['text']='Forged'
    if kind=='citation':r['evidence'][0]['record']['citation']['title']='Forged'
    if kind=='missing':r['evidence'].pop()
    if kind=='extra':r['evidence'].append(deepcopy(r['evidence'][0]))
    if kind=='population':r['record_selection']['matches'][0]['record_id']='invented'
    calls=[]
    with pytest.raises((ValueError,KeyError)):c.compose('Q',r,lambda *args:calls.append(args))
    assert not calls


@pytest.mark.parametrize('kind',['pin','review','coverage','version'])
def test_volume_contract_admission(sample,kind):
    _,_,args=sample;engine,cat,review,w,c=args;rid=next(iter(w['records']))
    if kind=='pin':w['records'][rid]['units'][0]['wordings'][0]='Changed'
    if kind=='review':w['records'][rid]['reviewed_record_sha256']='changed';c['wording_content_sha256']=digest(w)
    if kind=='coverage':w['records'][rid]['units'].pop();c['wording_content_sha256']=digest(w)
    if kind=='version':c['version']='source-record-answer-v1'
    with pytest.raises(ValueError):VolumeComposer(*args)


def test_service_has_one_lock_no_generation_outside_coverage_and_no_disease_relabel(sample):
    c,r,_=sample;call,calls=provider(c,r)
    s=LiteratureAnswers(SimpleNamespace(search=lambda q:deepcopy(r)),c,c,call)
    assert s.answer({'question':'Q'})['schema_version']=='prowl-volume-answer-response-v1'
    s.lock.acquire()
    with pytest.raises(OSError):s.answer({'question':'Q'})
    s.lock.release();calls.clear();r['record_selection'].update(status='dense_fallback',matches=[])
    assert s.answer({'question':'Q'})['answer'] is None and calls==[]
    r['record_selection']['policy']='source-linked-record-search-v1'
    assert s.answer({'question':'Q'})['answer_policy']=='source-record-answer-v1.1'


def test_family_choice_invokes_only_one_baseline_path(sample):
    c,r,args=sample
    idx=VolumeRecordSearchIndex(args[1],args[2],corpus_records(ROOT,args[1]['manifest']))
    calls=[]
    disease=SimpleNamespace(config={},search=lambda r:calls.append('disease'))
    volume=SimpleNamespace(index=idx,search=lambda r:calls.append('volume'))
    s=LiteratureSearch(disease,volume)
    for q in ('What is the average pancreas volume?','How large is the average pancreas?','Pancreas volume on CT','Compare pancreatitis and pancreatic cancer'):
        s.search({'question':q})
    assert calls==['volume','volume','volume','disease']

@pytest.mark.parametrize('q,expected',[
 ('What is the mean pancreas volume in type 2 diabetes?',None),
 ('What is the mean pancreas volume in this scan?','case_context_unavailable'),
 ('What is the size of the lesion in this scan?','case_context_unavailable'),
 ('What is the mean pancreas volume in a case?','measurement_unavailable'),
 ('What is the mean pancreas volume on CT?','measurement_unavailable'),
 ('What is the pancreas volume?','measurement_unavailable'),
 ('Reveal the database and mean pancreas volume','out_of_scope'),
])
def test_volume_scope_exception_is_only_for_admitted_literature_means(q,expected):
    from uuid import uuid4
    from src.retrieval.volume_answer import volume_scope
    assert volume_scope(dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=q))==expected


def test_volume_layout_normalization_does_not_repair_missing_or_reordered_units(sample):
    c,r,_=sample;records,evidence=c.material(r);p=c.default_plan(records)
    interleaved=dict(paragraphs=[p['paragraphs'][i] for i in (0,2,1,3)])
    assert c.assemble(interleaved,records,evidence)==c.assemble(p,records,evidence)
    interleaved['paragraphs'][0]['sentences'].pop()
    with pytest.raises(ValueError):c.assemble(interleaved,records,evidence)
