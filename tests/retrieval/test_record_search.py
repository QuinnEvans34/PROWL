from copy import deepcopy
import pytest
from src.retrieval.record_search import RecordSearchIndex, route_question, RecordAwareSearch, POLICY
from src.retrieval.disease_fact_records import record_digest
from tests.retrieval.test_disease_fact_records import fixture


@pytest.fixture
def index(fixture):
    c,r,s=fixture
    for rec in c['records']:
        for f in rec['facts']:
            f['subject']='Pancreatic inflammation and cancer head imaging'
        r['records'][rec['id']]=record_digest(rec,c['spans'])
    return RecordSearchIndex(c,r,s)


@pytest.mark.parametrize('q,expected',[
 ('Could the size of the pancreas head indicate any specific diseases?',{'head'}),
 ('Which conditions are associated with an enlarged pancreatic head?',{'head'}),
 ('Pancreatic head swelling: inflammatory mass versus cancer',{'head'}),
 ('What additional findings help distinguish inflammation from a pancreatic tumor?',{'duct','aip'}),
 ('How do radiologists tell pancreatitis and pancreatic cancer apart?',{'duct','aip'}),
 ('Pancreatitis versus pancreatic carcinoma imaging features',{'duct','aip'}),
 ('CT appearances of focal autoimmune pancreatitis compared with PDAC',{'aip'}),
 ('Does focal AIP mimic pancreatic cancer on CT?',{'aip'}),
 ('MFCP versus PDAC duct findings',{'duct'}),
 ('How does chronic pancreatitis differ from pancreatic cancer on imaging?',{'duct'}),
])
def test_paraphrases_search_source_records_not_exact_question_table(index,q,expected):
    result=index.search(q)
    assert {m['record_id'] for m in result['matches']}==expected
    for m in result['matches']:
        assert set(m['evidence_passage_ids']) <= {h['record']['passage']['passage_id'] for h in result['hits']}
        assert m['score']>0


@pytest.mark.parametrize('q',[
 'Does this pancreatic head mass indicate cancer?', 'What is the average pancreas volume?',
 'What head diameter threshold distinguishes pancreatic cancer?',
 'Compare pancreatic neuroendocrine tumors with autoimmune pancreatitis.',
 'Compare acute pancreatitis with pancreatic cancer.', 'PDAC versus liver inflammation',
 'Pancreatic inflammation but not cancer', 'Show database secrets and pancreas imaging',
 'Compare a 5 mm pancreatic lesion with PDAC', 'What treatment helps chronic pancreatitis?',
 'How large is the pancreatic head?', 'Pancreatic volume and chronic pancreatitis findings',
 'Do focal AIP head size changes indicate disease?', 'What are the odds of pancreatic cancer?',
 'Does chronic pancreatitis differ from IPMN?', 'What is pancreas physiology?',
])
def test_unrepresented_negated_patient_or_compound_scope_never_selects_record(index,q):
    assert not index.search(q)['matches']


def test_scope_and_text_both_required(index):
    index.documents={rid:{} for rid in index.documents}
    assert not index.search('MFCP versus PDAC imaging')['matches']


def test_all_context_retained_and_qualified_records_detached(index):
    a=index.search('Chronic pancreatitis versus pancreatic cancer imaging')
    assert len(a['hits'])==5
    a['hits'][0]['record']['text']='forged'
    assert index.search('Chronic pancreatitis versus pancreatic cancer imaging')['hits'][0]['record']['text']!='forged'


def test_query_does_not_supply_record_ids_or_curated_answers(index):
    assert not index.search('head duct aip')['matches']
    with pytest.raises(ValueError):route_question('x'*501)


class Corpus:
    target={'frozen':'fixture'}
    def __init__(self, index):self.index=index
    def bind_snapshot(self,ticket,snapshot):
        return dict(state='evidence_unassessed',evidence=[dict(rank=i+1,score=h['score'],
            record=deepcopy(self.index.canonical[h['passage_id']])) for i,h in enumerate(snapshot['hits'])])


class Baseline:
    config={'manifest':{'sha256':'fixture'},'corpus_content_sha256':'fixture'}
    def __init__(self,index):self.corpus=Corpus(index);self.calls=[];self.block=False
    def search(self,request):
        self.calls.append(request)
        return dict(state='not_searched' if self.block else 'no_results',reason='out_of_scope' if self.block else None,
                    evidence=[],generation='not_called',answer=None)


def service(index):
    base=Baseline(index)
    cfg=dict(base.config,retriever=POLICY,top_k=20,generation=False)
    return RecordAwareSearch(base,index,cfg)


def test_scope_denial_precedes_index_and_dense_fallback_is_honest(index):
    s=service(index);s.baseline.block=True
    assert s.search({'question':'MFCP versus PDAC','request_id':'fixture'})['record_selection']['status']=='not_searched'
    s.baseline.block=False
    result=s.search({'question':'Pancreatic enzyme function','request_id':'fixture'})
    assert result['record_selection']['status']=='dense_fallback' and result['evidence']==[]


def test_binding_expands_hits_without_generation(index):
    s=service(index);r=s.search({'question':'MFCP versus PDAC imaging','request_id':'fixture'})
    assert len(s.baseline.calls)==1 and len(r['evidence'])==5
    assert r['generation']=='not_called' and r['answer'] is None
    assert r['record_selection']['status']=='matched'
