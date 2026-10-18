"""Invented relation fixtures: test provenance and qualifier retention, not clinical truth."""
from copy import deepcopy
import hashlib
import pytest
from src.retrieval.disease_fact_records import DiseaseFactCatalog, POLICY, record_digest


@pytest.fixture
def fixture():
    canonical = {}; spans = {}
    for i in range(8):
        text=f'Invented source relation {i}. No clinical claim.';pid=f'p{i}'
        record=dict(text=text,passage=dict(passage_id=pid,work_id='synthetic',ordinal=i,section_id='s'),
                    citation=dict(title='Invented fixture',url='https://example.invalid'))
        canonical['synthetic',i]=dict(passage_id=pid,text=text,record=record)
        spans[f's{i}']=dict(passage_id=pid,work_id='synthetic',ordinal=i,start=0,end=len(text),
                           text_sha256=hashlib.sha256(text.encode()).hexdigest())
    def f(role,relation,i,method=None,phase=None):
        return dict(role=role,subject=f'Fixture subject {i}',relation=relation,object=f'fixture feature {i}',
                    method=method,phase=phase,evidence=[f's{i}'])
    limits=[f('overlap','can_mimic',3),f('single_feature_limit','cannot_reliably_distinguish',4),
            f('combination_limit','depends_on',5)]
    def r(rid,pair,topic,facts,anchor):
        return dict(id=rid,work_id='synthetic',organ='pancreas',comparison=pair,topic=topic,
                    facts=facts,retrieval_anchors=[anchor])
    records=[r('head',['MFCP','PDAC'],'focal_head_mass',[f('finding','occasionally_shows',0),*limits],'p0'),
             r('duct',['MFCP','PDAC'],'imaging_differentiation',
               [f('finding','favors',1),f('method','best_seen',2,'MRCP'),*deepcopy(limits)],'p1'),
             r('aip',['focal_AIP','PDAC'],'imaging_differentiation',
               [f('finding','usually_shows',6,'CT','portal-venous'),f('overlap','can_mimic',3)],'p6')]
    catalog=dict(version=POLICY,manifest={'path':'synthetic','sha256':'invented'},records=records,spans=spans)
    review=dict(catalog_version=POLICY,manifest=catalog['manifest'],status='engineering_reviewed',
                records={r['id']:record_digest(r,spans) for r in records})
    return catalog,review,canonical


def intent(pair=None,topic='imaging_differentiation'):
    return dict(organ='pancreas',comparison=pair or ['MFCP','PDAC'],topic=topic,use='literature_comparison')


def repin(c,r):
    r['records']={record['id']:record_digest(record,c['spans']) for record in c['records']}


@pytest.mark.parametrize('rid,pid,requested', [('head',0,intent(topic='focal_head_mass')),
    ('duct',1,intent()),('aip',6,intent(['focal_AIP','PDAC']))])
def test_selection_expands_complete_qualified_record(fixture,rid,pid,requested):
    engine=DiseaseFactCatalog(*fixture)
    assert engine.select([fixture[2]['synthetic',pid]['record']],requested)['record_ids']==[rid]
    answer=engine.render(rid);assert engine.verify_answer(answer,record_id=rid)
    assert len(answer['citations'])>1
    assert all(s['span_ids'] and s['citations'] for s in answer['statements'] if s['kind']=='source_fact')
    limit=answer['statements'][-1]
    assert limit['kind']=='application_limit' and not limit['citations']
    assert 'individual diagnosis' in limit['text'] and 'size threshold' in limit['text']


@pytest.mark.parametrize('field,value',[('organ','lesion'),('comparison',['pancreatitis','all_tumors']),
    ('comparison',['PDAC','MFCP']),('topic','numerical_head_size'),('use','patient_diagnosis'),
    ('use','treatment'),('use','patient_measurement')])
def test_mismatch_never_reuses_comparison(fixture,field,value):
    e=DiseaseFactCatalog(*fixture);i=intent();i[field]=value
    assert not e.select([s['record'] for s in fixture[2].values()],i)['record_ids']


def test_no_hit_and_context_only_do_not_select(fixture):
    e=DiseaseFactCatalog(*fixture)
    assert not e.select([],intent())['record_ids']
    assert not e.select([fixture[2]['synthetic',3]['record']],intent())['record_ids']
    assert not e.select([fixture[2]['synthetic',1]['record']],intent(['focal_AIP','PDAC']))['record_ids']


@pytest.mark.parametrize('role',['overlap','single_feature_limit','combination_limit','method'])
def test_missing_qualifier_refuses_even_if_review_rehashed(fixture,role):
    c,r,s=deepcopy(fixture);c['records'][1]['facts']=[f for f in c['records'][1]['facts'] if f['role']!=role]
    repin(c,r)
    with pytest.raises(ValueError,match='qualifications'):DiseaseFactCatalog(c,r,s)


@pytest.mark.parametrize('kind',['method','phase','role_relation','context_anchor'])
def test_structural_qualifiers_cannot_be_reviewed_away(fixture,kind):
    c,r,s=deepcopy(fixture)
    if kind=='method': c['records'][1]['facts'][1]['method']='CT'
    if kind=='phase': c['records'][2]['facts'][0]['phase']=None
    if kind=='role_relation':c['records'][1]['facts'][2]['relation']='usually_shows'
    if kind=='context_anchor':c['records'][1]['retrieval_anchors']=['p3']
    repin(c,r)
    with pytest.raises(ValueError):DiseaseFactCatalog(c,r,s)


@pytest.mark.parametrize('field,value',[('subject','Every inflammatory disease'),('object','any tumor'),
    ('relation','usually_shows'),('method','CT'),('evidence',['s7'])])
def test_semantic_change_requires_new_source_review(fixture,field,value):
    c,r,s=deepcopy(fixture);c['records'][1]['facts'][0][field]=value
    with pytest.raises(ValueError,match='Unreviewed'):DiseaseFactCatalog(c,r,s)


@pytest.mark.parametrize('kind',['source','offset','hash','paper','review_manifest','review_membership'])
def test_source_identity_changes_refuse(fixture,kind):
    c,r,s=deepcopy(fixture)
    if kind=='source':s['synthetic',0]['text']='Altered source'
    if kind=='offset':c['spans']['s0']['end']-=1
    if kind=='hash':c['spans']['s0']['text_sha256']='bad'
    if kind=='paper':c['spans']['s0']['work_id']='wrong'
    if kind=='review_manifest':r['manifest']={'path':'other'}
    if kind=='review_membership':r['records'].pop('aip')
    with pytest.raises(ValueError):DiseaseFactCatalog(c,r,s)


@pytest.mark.parametrize('kind',['text','citation','ordinal','unknown'])
def test_forged_hit_refuses(fixture,kind):
    e=DiseaseFactCatalog(*fixture);hit=deepcopy(fixture[2]['synthetic',1]['record'])
    if kind=='text':hit['text']='Invented claim'
    if kind=='citation':hit['citation']['title']='Other article'
    if kind=='ordinal':hit['passage']['ordinal']=2
    if kind=='unknown':hit['passage']['passage_id']='unknown'
    with pytest.raises(ValueError,match='Noncanonical'):e.select([hit],intent())


@pytest.mark.parametrize('kind',['drop_overlap','drop_combination','drop_single_feature','drop_policy',
    'reword_mrcp','reword_phase','reword_certainty','citation','quote','comparison'])
def test_downstream_rewrites_rejected(fixture,kind):
    e=DiseaseFactCatalog(*fixture);rid='aip' if kind=='reword_phase' else 'duct';a=e.render(rid)
    if kind.startswith('drop_'):
        role={'drop_overlap':'overlap','drop_combination':'combination_limit',
              'drop_single_feature':'single_feature_limit','drop_policy':'scope_limit'}[kind]
        a['statements']=[s for s in a['statements'] if s['role']!=role]
    elif kind=='reword_phase':a['statements'][0]['text']=a['statements'][0]['text'].replace('portal-venous','arterial')
    elif kind=='reword_mrcp':a['statements'][1]['text']='This CT outline establishes the diagnosis.'
    elif kind=='reword_certainty':a['statements'][0]['text']=a['statements'][0]['text'].replace('favors','proves')
    elif kind=='citation':a['statements'][0]['citations']=['p7']
    elif kind=='quote':a['citations'][0]['quote']='Replaced'
    elif kind=='comparison':a['comparison']=['all_inflammation','any_tumor']
    with pytest.raises(ValueError):e.verify_answer(a,record_id=rid)


def test_detached_snapshot_and_return_values(fixture):
    e=DiseaseFactCatalog(*fixture);before=e.render('duct');a=e.render('duct')
    fixture[0]['records'][1]['facts'][0]['object']='Injected'
    a['evidence'].clear();a['citations'][0]['quote']='Injected'
    assert e.render('duct')==before


def test_arbitrary_question_or_patient_fields_are_not_a_router(fixture):
    e=DiseaseFactCatalog(*fixture);i=intent();i['question']='What does this scan mean?'
    with pytest.raises(ValueError,match='structured intent'):e.select([],i)
