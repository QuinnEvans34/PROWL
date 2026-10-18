import json
import pytest
from jsonschema import ValidationError
from src.retrieval.section_search import SectionSearch, MODEL, MODEL_SHA


def fixture():
    bundle=dict(work=dict(work_id='w'),citation=dict(title='Synthetic study'),
        representation=dict(work_id='w',text='Invented source text. More text.',sections=[
            dict(section_id='a',title='Methods',start=0,end=21),
            dict(section_id='b',title='Results',start=22,end=32)]))
    records=[dict(text='Invented source text.',citation=bundle['citation'],passage=dict(
        work_id='w',passage_id='a',ordinal=0,section_id='a')),
        dict(text='More text.',citation=bundle['citation'],passage=dict(
        work_id='w',passage_id='b',ordinal=1,section_id='b'))]
    return SectionSearch([bundle],records),records


def provider(papers=None,sections=None,digest=MODEL_SHA):
    calls=[]
    def call(path,payload=None):
        calls.append((path,payload))
        if path=='tags':return dict(models=[dict(name=MODEL,digest=digest)])
        data=dict(papers=['D1'] if papers is None else papers) if len(calls)==2 else dict(sections=['S2','S1'] if sections is None else sections)
        return dict(model=MODEL,done=True,done_reason='stop',prompt_eval_count=100,
                    message=dict(content=json.dumps(data)))
    return call,calls


def test_selected_sections_return_original_records_and_order():
    search,records=fixture();call,calls=provider()
    result=search.search('Pancreas question',call)
    assert [h['record'] for h in result['hits']]==[records[1],records[0]]
    assert result['hits'][0]['record'] is records[1]
    assert len(calls)==3
    assert json.loads(calls[1][1]['messages'][1]['content'])['question']=='Pancreas question'


@pytest.mark.parametrize('papers',[['foreign'],['D1','D1'],[]])
def test_foreign_duplicate_empty_papers_stop_before_section_call(papers):
    search,_=fixture();call,calls=provider(papers=papers)
    with pytest.raises(ValidationError):search.search('Pancreas',call)
    assert len(calls)==2


@pytest.mark.parametrize('sections',[['foreign'],['S1','S1'],[]])
def test_invalid_sections_never_invent_evidence(sections):
    search,_=fixture();call,_=provider(sections=sections)
    with pytest.raises(ValidationError):search.search('Pancreas',call)


def test_wrong_model_blocks_selection():
    search,_=fixture();call,calls=provider(digest='wrong')
    with pytest.raises(OSError):search.search('Pancreas',call)
    assert len(calls)==1


def test_large_evidence_is_not_silently_clipped():
    search,records=fixture();records[0]['text']='x'*24001;call,_=provider()
    with pytest.raises(ValueError,match='evidence exceeds'):search.search('Pancreas',call)


def test_oversized_provider_context_rejected():
    search,_=fixture();call,calls=provider()
    def oversize(path,payload=None):
        response=call(path,payload)
        if path=='chat':response['prompt_eval_count']=16000
        return response
    with pytest.raises(ValueError,match='oversized'):search.search('Pancreas',oversize)
    assert len(calls)==2
