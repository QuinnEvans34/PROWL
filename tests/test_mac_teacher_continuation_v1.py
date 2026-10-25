import json
import numpy as np
import pytest
from src.operations.mac_teacher_continuation_v1 import completed_members, remaining_seconds
from src.data.segmenter_teacher_cache_v1 import sha


def test_reuse_only_complete_records_and_reject_corruption(tmp_path):
    path = tmp_path/'A.npz'; np.savez_compressed(path, probability=np.zeros((2,3,4),np.uint16))
    row = dict(case_id='A', payload_sha256=sha(path), bytes=path.stat().st_size,
               native_geometry={'shape':[2,3,4]})
    (tmp_path/'A.json').write_text(json.dumps(row))
    (tmp_path/'B.npz').write_bytes(b'interrupted payload')
    assert completed_members(tmp_path, {'train':['A','B']}) == {'A':row}
    path.write_bytes(b'corrupted')
    with pytest.raises(ValueError): completed_members(tmp_path, {'train':['A','B']})


def stopped(seconds):
    return dict(workers_reaped=True, success=False,
                error="InterruptedError('Supervisor signal 15')", seconds=seconds)


def test_repeated_pauses_charge_work_but_not_time_in_class():
    remaining = remaining_seconds({'limits':{'seconds':100}}, stopped(12.1))
    assert remaining == 87
    assert remaining_seconds({'limits':{'seconds':remaining}}, stopped(10)) == 77


def test_group_kill_requires_explicit_operator_record_and_reaping():
    r=dict(workers_reaped=True,success=False,error="ValueError('Duration worker failed')",exit_code=-9,seconds=10)
    with pytest.raises(ValueError):remaining_seconds({'limits':{'seconds':100}},r)
    assert remaining_seconds({'limits':{'seconds':100}},r,owned_worker_kill=True)==90
    r['workers_reaped']=False
    with pytest.raises(ValueError):remaining_seconds({'limits':{'seconds':100}},r,owned_worker_kill=True)


@pytest.mark.parametrize('field,value', [('workers_reaped',False),('success',True),
    ('error','resource failure'),('seconds',None),('seconds',float('nan')),('seconds',101)])
def test_unqualified_stops_cannot_resume(field,value):
    resources = stopped(10); resources[field] = value
    with pytest.raises(ValueError): remaining_seconds({'limits':{'seconds':100}},resources)
