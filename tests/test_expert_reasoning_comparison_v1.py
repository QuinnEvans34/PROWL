import pytest
from scripts.retrieval.compare_expert_reasoning_v1 import configured_call

@pytest.mark.parametrize('arm,expected',[('baseline',[True,True]),('fast_select',[False,True])])
def test_only_selection_thinking_changes(arm,expected):
    calls=[];f=configured_call(lambda path,payload:calls.append((path,payload)),arm)
    f('tags');original={'think':True,'messages':['evidence'],'format':{'schema':1}}
    f('chat',original);f('chat',original)
    assert [p['think'] for name,p in calls if name=='chat']==expected
    assert original['think'] is True
    assert all(p['messages']==['evidence'] and p['format']=={'schema':1} for n,p in calls if n=='chat')
    with pytest.raises(ValueError):f('chat',original)
