from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pytest
from src.data.segmenter_native_windows_v1 import geometry
from src.data.segmenter_physical_windows_v1 import physical_geometry, coverage_bank, sample_window
from src.data.segmenter_pancreas_region_v1 import window_origin
from src.data.segmenter_varied_region_v1 import coverage_slots, components, choose, planned_visits


@pytest.mark.parametrize('total', [8, 9, 13, 18])
@pytest.mark.parametrize('required', [1, 2, 4, 6, 8])
def test_every_required_bank_slot_is_reserved(total, required):
    slots = coverage_slots(total, required)
    assert len(set(slots)) == required and min(slots) == 0 and max(slots) < total
    cover = [(i, i, i) for i in range(required)]
    visited = []
    for visit in slots:
        origin, trace = choose(dict(shape=[200]*3), cover, [], step=0,
            focused_visit=visit, total=total, seed=42, name='patient')
        visited.append(origin); assert trace['kind'] == 'reserved_cover'
    assert visited == cover


def test_impossible_schedule_fails_without_exclusion():
    with pytest.raises(ValueError, match='Insufficient'): coverage_slots(7, 8)


def test_permutation_is_identical_to_existing_session():
    from src.training.segmenter_full_session_v1 import Session
    # Use only the existing next_member method, not a network or optimizer.
    raw = object.__new__(Session)
    raw.control = {'train': ['a','b','c','d','e']}; raw.config = {'seed':42,'max_steps':83}
    raw._epoch = None
    counts = dict.fromkeys(raw.control['train'], 0); exposure = counts.copy()
    for step in range(83):
        raw.step = step; name = raw.next_member(); exposure[name] += 1
        if step % 4 != 3: counts[name] += 1
    assert planned_visits(raw.control['train'], 83) == (counts, exposure)


@pytest.mark.parametrize('positive', [False, True])
@pytest.mark.parametrize('factors', [(1,1,1), (2,1,4)])
def test_jitter_retains_anchor_and_component_if_it_fits(positive, factors):
    target = np.zeros((180,100,70), np.uint8)
    target[50:55,40:45,30:35] = 2 if positive else 1
    g = geometry(list(target.shape), np.diag([*factors,1.]))
    record = physical_geometry(g); cover = coverage_bank(target > 0, record)
    parts, actual_positive = components(target, record)
    assert actual_positive == positive
    origins = []
    for visit in range(1,10):
        origin, trace = choose(record, cover, parts, step=visit*4, focused_visit=visit,
                               total=10, seed=42, name='a')
        assert (origin,trace) == choose(record, cover, parts, step=visit*4,
            focused_visit=visit, total=10, seed=42, name='a')
        patch,_ = sample_window(target, record, origin, order=0)
        anchor = tuple(a-o for a,o in zip(trace['anchor'],origin))
        assert patch[anchor] == (2 if positive else 1)
        assert trace['whole_component_fits']
        assert int((patch > 0).sum()) == int((target > 0).sum())*np.prod(factors)
        origins.append(origin)
    assert len(set(origins)) > 1


def test_large_component_not_falsely_claimed_whole_but_bank_unchanged():
    target = np.ones((200,12,12), np.uint8)*2
    record = physical_geometry(geometry(list(target.shape), np.eye(4)))
    cover = coverage_bank(target > 0,record); parts,_ = components(target,record)
    origin,trace = choose(record,cover,parts,step=4,focused_visit=1,total=10,seed=42,name='a')
    assert trace['kind']=='component_jitter' and not trace['whole_component_fits']
    assert len(cover)==2
    assert all(0<=a-o<144 for a,o in zip(trace['anchor'],origin))


def test_tiny_and_border_components_cycle_without_disappearance():
    target = np.zeros((160,24,24), np.uint8); target[0,0,0]=2;target[-1,-1,-1]=2
    record = physical_geometry(geometry(list(target.shape),np.eye(4)))
    cover=coverage_bank(target>0,record);parts,_=components(target,record)
    selected=[]
    for visit in (1,2,3,4):
        origin,trace=choose(record,cover,parts,step=0,focused_visit=visit,total=12,seed=42,name='a')
        patch,_=sample_window(target,record,origin,order=0)
        assert patch[tuple(a-o for a,o in zip(trace['anchor'],origin))]==2
        selected.append(trace['component_index'])
    assert selected[0]!=selected[1] and selected[:2]==selected[2:]


def test_context_is_bit_identical_to_parent_and_does_not_need_components():
    record=dict(shape=[270,100,180]);cover=[(0,0,0)]
    for step in (3,7,991,23999):
        original=window_origin(record,cover,step=step,focused_visit=5,seed=42,name='a')
        origin,trace=choose(record,cover,[],step=step,focused_visit=5,total=12,seed=42,name='a')
        assert (origin,trace['kind'])==original


def test_roles_and_actual_anchor_guard():
    from src.data.segmenter_varied_region_v1 import VariedInputs
    p=object.__new__(VariedInputs);p.control={'train':['a'],'validation':['dev']}
    p.planned_counts={'a':12};p.component_cache={}
    target=np.zeros((170,24,24),np.uint8);target[100:104,10:14,10:14]=2
    case=dict(name='a',target=target,image=target.astype(np.float32)/2,
        geometry=geometry(list(target.shape),np.eye(4)),source_sha256={'test':'immutable'},
        region_low=[0,0,0],region_high=list(target.shape))
    with pytest.raises(ValueError,match='outside bound role'):
        p.from_case(dict(case,name='dev'),step=0,focused_visit=0,seed=42)
    x,y,transform,trace=p.from_case(case,step=4,focused_visit=1,seed=42)
    assert x.shape==(1,144,144,144) and y.shape==(144,144,144)
    assert trace['lesion_voxels']>0 and np.array_equal(x[0]*2,y.astype(np.float32))


def test_new_session_counters_and_identity():
    from src.training.segmenter_varied_region_session_v1 import VariedSession
    raw=SimpleNamespace(control={'train':['a'],'planned_focused_counts':{'a':3}},
        identity={},exposure={'a':4},step=4)
    s=VariedSession(raw);s.focused={'a':3};s.check()
    s.focused={'a':4}
    with pytest.raises(ValueError):s.check()
    s.focused={'a':3};s.identity['policy']['window']=192
    with pytest.raises(ValueError):s.check()


def test_restore_rejects_wrong_policy_before_raw_model_allocation():
    from src.training.segmenter_varied_region_session_v1 import VariedSession
    with pytest.raises(ValueError,match='identity mismatch'):
        VariedSession.restore({'version':1,'identity':{},'identity_sha256':'wrong'}, {})
