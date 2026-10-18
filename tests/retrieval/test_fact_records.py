"""Mutation/selection tests use invented study values, never evaluation answers."""
from copy import deepcopy
import hashlib
import pytest
from src.retrieval.fact_records import FactCatalog, POLICY, LIMITS, record_digest, _literal


@pytest.fixture
def fixture():
    texts = [
        'The total pancreas volume in cm3 was measured.',
        'A control group of 12 normal glucose tolerance subjects matched for age, weight and sex.',
        'The method was magnetic resonance imaging.',
        'Data are expressed as mean±SEM.', '71.2', '3.4',
    ]
    canonical = {}; spans = {}
    for i,t in enumerate(texts):
        pid=f'passage:{i}'; sid=f's{i}'
        record=dict(text=t, passage=dict(passage_id=pid,work_id='work:synthetic',ordinal=i,section_id='s'),
                    citation=dict(title='Invented study',url='https://example.invalid',authors=['Fixture']))
        canonical[('work:synthetic',i)]=dict(passage_id=pid,text=t,record=record)
        spans[sid]=dict(passage_id=pid,work_id='work:synthetic',ordinal=i,start=0,end=len(t),
                        text_sha256=hashlib.sha256(t.encode()).hexdigest())
    def f(value,ref): return dict(value=value,evidence=[ref])
    fields=dict(object=f('pancreas','s0'),extent=f('whole_organ','s0'),quantity=f('volume','s0'),unit=f('cm3','s0'),
        population=f('normal_glucose_tolerance_comparison','s1'),sample_size=f(12,'s1'),method=f('MRI','s2'),
        statistic=f('mean','s3'),mean=f('71.2','s4'),uncertainty=f('3.4','s5'),uncertainty_kind=f('SEM','s3'),
        matching=f(['age','weight','sex'],'s1'))
    record=dict(id='fact:synthetic',work_id='work:synthetic',fields=fields,limitations=LIMITS.copy(),
                retrieval_anchors=['passage:4'])
    catalog=dict(version=POLICY,manifest={'path':'synthetic','sha256':'invented'},spans=spans,records=[record])
    review=dict(catalog_version=POLICY,manifest=catalog['manifest'],status='engineering_reviewed',
                records={record['id']:record_digest(record,spans)})
    return catalog,review,canonical


def intent():
    return dict(object='pancreas',extent='whole_organ',quantity='volume',population='normal_glucose_tolerance_comparison',
                method='MRI',uncertainty_kind='SEM',use='literature_example')


def test_complete_assembly_and_result_anchor_expand_missing_context(fixture):
    catalog,review,canonical=fixture; engine=FactCatalog(*fixture)
    selected=engine.select([canonical[('work:synthetic',4)]['record']],intent())
    assert selected==dict(status='selected',record_ids=['fact:synthetic'])
    answer=engine.render(selected['record_ids'][0]); text=' '.join(s['text'] for s in answer['statements'])
    for required in ['MRI','whole-pancreas','71.2 cm³','12 people','normal glucose tolerance','±3.4 cm³',
                     'standard error of the mean','age, weight and sex','selected study group',
                     'not a universal average','CT reference range','cannot determine']:
        assert required in text
    assert len(answer['citations'])==6  # All context is expanded from only one retrieved result hit.
    assert {s['kind'] for s in answer['statements']}=={'source_fact','source_fact_with_statistical_glossary','interpretation_limit'}
    assert engine.verify_answer(answer,record_id='fact:synthetic')


@pytest.mark.parametrize('field,value', [('object','lesion'),('extent','head'),('quantity','diameter'),
    ('population','healthy_adults'),('method','CT'),('uncertainty_kind','SD'),('use','patient_normality')])
def test_mismatched_intents_never_reuse_volume_record(fixture,field,value):
    engine=FactCatalog(*fixture); requested=intent();requested[field]=value
    assert engine.select([fixture[2][('work:synthetic',4)]['record']],requested)['record_ids']==[]


def test_empty_and_methods_only_hits_do_not_trigger_answer(fixture):
    engine=FactCatalog(*fixture)
    assert engine.select([],intent())['record_ids']==[]
    assert engine.select([fixture[2][('work:synthetic',2)]['record']],intent())['record_ids']==[]


@pytest.mark.parametrize('field,value', [('object','lesion'),('population','well_controlled_type2_metformin'),
    ('sample_size',44),('mean','99.9'),('uncertainty','9.9'),('unit','mm'),('uncertainty_kind','SD')])
def test_changed_interpretation_requires_new_review(fixture,field,value):
    c,r,s=deepcopy(fixture);c['records'][0]['fields'][field]['value']=value
    with pytest.raises(ValueError,match='reviewed version'):FactCatalog(c,r,s)


@pytest.mark.parametrize('missing', ['sample_size','method','uncertainty_kind','matching'])
def test_missing_required_fields_refuse(fixture,missing):
    c,r,s=deepcopy(fixture);del c['records'][0]['fields'][missing]
    with pytest.raises(ValueError,match='qualifications'):FactCatalog(c,r,s)


def test_missing_limit_refuses(fixture):
    c,r,s=deepcopy(fixture);c['records'][0]['limitations'].remove('not_ct_reference')
    with pytest.raises(ValueError,match='qualifications'):FactCatalog(c,r,s)


@pytest.mark.parametrize('change', ['source','offset','cross_paper','field_binding'])
def test_evidence_changes_refuse(fixture,change):
    c,r,s=deepcopy(fixture)
    if change=='source': s[('work:synthetic',0)]['text']='Changed source.'
    if change=='offset': c['spans']['s0']['end']-=1
    if change=='cross_paper':c['spans']['s0']['work_id']='another-paper'
    if change=='field_binding':c['records'][0]['fields']['sample_size']['evidence']=['s4']
    with pytest.raises(ValueError):FactCatalog(c,r,s)


def test_review_does_not_override_missing_literal_field_support(fixture):
    c,r,s=deepcopy(fixture);c['records'][0]['fields']['sample_size']['value']=41
    r['records']['fact:synthetic']=record_digest(c['records'][0],c['spans'])
    with pytest.raises(ValueError,match='Numerical field'):FactCatalog(c,r,s)


def test_forged_retrieval_hit_rejected(fixture):
    engine=FactCatalog(*fixture);hit=deepcopy(fixture[2][('work:synthetic',4)]['record']);hit['text']='99.9'
    with pytest.raises(ValueError,match='Retrieved record'):engine.select([hit],intent())


@pytest.mark.parametrize('change', ['drop','reword','citation','metadata'])
def test_later_rewrite_cannot_drop_or_reassign_qualifiers(fixture,change):
    engine=FactCatalog(*fixture);answer=engine.render('fact:synthetic')
    if change=='drop': answer['statements'].pop()
    if change=='reword': answer['statements'][0]['text']=answer['statements'][0]['text'].replace('12 people','people')
    if change=='citation': answer['statements'][0]['citations']=[]
    if change=='metadata':answer['statements'][1]['text']=answer['statements'][1]['text'].replace('SEM','SD')
    with pytest.raises(ValueError):engine.verify_answer(answer,record_id='fact:synthetic')


def test_catalog_and_outputs_are_detached_snapshots(fixture):
    engine=FactCatalog(*fixture);before=engine.render('fact:synthetic')
    fixture[0]['records'][0]['fields']['mean']['value']='999'
    before['citations'][0]['quote']='Injected';before['evidence'].clear()
    assert '999' not in engine.render('fact:synthetic')['statements'][0]['text']
    assert engine.render('fact:synthetic')['evidence']


def test_literal_correspondence_handles_sentence_punctuation_without_partial_numbers():
    assert _literal('sex','age, weight and sex.')
    assert _literal('4.8','4.8.')
    assert not _literal('4.8','14.8')
    assert not _literal('4.8','4.81')
