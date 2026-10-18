import json
import pytest
from tests.retrieval.test_section_search import fixture, provider
from src.retrieval.thinking_section_search import SectionSearch


def test_thinking_policy_stays_bounded_and_binds_original_evidence():
    original,records=fixture();search=SectionSearch(list(original.bundles.values()),records)
    original_call,calls=provider()
    def call(path,payload=None):
        r=original_call(path,payload)
        if path=='chat':
            r['message']['content']=json.dumps(dict(reason='The selected sections address the requested methods and results.',
                **json.loads(r['message']['content'])))
        return r
    result=search.search('Pancreas',call)
    assert [h['record'] for h in result['hits']]==[records[1],records[0]]
    for _,payload in calls[1:]:
        assert payload['think'] is True and payload['options']['num_predict']==2048
    body=json.loads(calls[2][1]['messages'][1]['content'])
    assert body['papers']==[dict(id='D1',title='Synthetic study')]
    assert all('title' not in candidate for candidate in body['candidates'])


def test_timeout_in_selection_never_returns_partial_evidence(monkeypatch):
    original,records=fixture();search=SectionSearch(list(original.bundles.values()),records)
    clock=iter([0,0,61]);monkeypatch.setattr('src.retrieval.thinking_section_search.monotonic',lambda:next(clock))
    call,calls=provider()
    with pytest.raises(TimeoutError):search.search('Pancreas',call)
    assert len(calls)==1
