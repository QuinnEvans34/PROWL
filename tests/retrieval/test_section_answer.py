from copy import deepcopy
import pytest
from src.retrieval.natural_answer import generate, SECTION_POLICY
from tests.retrieval.test_natural_answer import EVIDENCE, provider


def many_evidence(n):
    result=[]
    for rank in range(1,n+1):
        e=deepcopy(EVIDENCE[0]);e['rank']=rank;result.append(e)
    return result


def test_section_profile_preserves_checks_and_uses_explicit_context_version():
    call,calls=provider()
    result=generate('Pancreas size?',many_evidence(6),call,profile='sections')
    assert result['policy']==SECTION_POLICY
    assert all(payload['options']['num_ctx']==16384 for path,payload in calls if path=='chat')
    assert len([1 for path,_ in calls if path=='chat'])==2


def test_default_profile_still_refuses_larger_package():
    call,calls=provider()
    with pytest.raises(ValueError,match='context budget'):generate('Pancreas',many_evidence(6),call)
    assert not calls


def test_section_profile_bound_before_model_calls():
    call,calls=provider()
    with pytest.raises(ValueError,match='context budget'):generate('Pancreas',many_evidence(51),call,profile='sections')
    assert not calls


def test_expired_request_deadline_blocks_model_calls():
    call,calls=provider()
    with pytest.raises(TimeoutError):generate('Pancreas',EVIDENCE,call,profile='sections',deadline=0)
    assert not calls
