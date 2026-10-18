import json
import pytest
from jsonschema import ValidationError
from tests.retrieval.test_section_search import fixture, provider
from src.retrieval.reasoned_section_search import SectionSearch


def setup(reason='The methods and results provide the requested evidence.',sections=None):
    original,records=fixture()
    search=SectionSearch(list(original.bundles.values()),records)
    original_call,calls=provider(sections=sections)
    def call(path,payload=None):
        result=original_call(path,payload)
        if path=='chat':
            value=json.loads(result['message']['content'])
            result['message']['content']=json.dumps(dict(reason=reason,**value))
        return result
    return search,call,calls,records


def test_reason_is_internal_navigation_not_evidence():
    search,call,calls,records=setup()
    result=search.search('Pancreas methods',call)
    assert [h['record'] for h in result['hits']]==[records[1],records[0]]
    assert 'reason' not in result and all('reason' not in h['record'] for h in result['hits'])
    assert list(calls[1][1]['format']['properties'])==['reason','papers']


@pytest.mark.parametrize('reason',['','short','a'*501,None])
def test_missing_or_invalid_reason_fails(reason):
    search,call,calls,_=setup(reason)
    with pytest.raises(ValidationError):search.search('Pancreas',call)
    assert len(calls)==2


def test_plausible_reason_cannot_authorize_foreign_evidence():
    search,call,_,_=setup(sections=['invented'])
    with pytest.raises(ValidationError):search.search('Pancreas',call)
