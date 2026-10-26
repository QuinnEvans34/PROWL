import json
import pytest
from src.data.segmenter_teacher_cache_v1 import sha
from src.operations.mac_teacher_power_continuation_v1 import remaining_after_power_stop

@pytest.mark.parametrize('fault',[None,'unreaped','other_error','changed_log','exhausted'])
def test_only_reviewed_reaped_power_stop_can_continue(tmp_path,fault):
    (tmp_path/'request.json').write_text(json.dumps({'limits':{'seconds':100}}))
    resources=dict(workers_reaped=fault!='unreaped',success=False,exit_code=1,error="ValueError('Duration worker failed')",seconds=101 if fault=='exhausted' else 12.5)
    (tmp_path/'resources.json').write_text(json.dumps(resources))
    (tmp_path/'worker.log').write_text('RuntimeError: '+('other error' if fault=='other_error' else 'AC power required')+'\n')
    review=dict(stopped=True,reason='AC power required',pause_receipt=False)
    for key,name in [('request_sha256','request.json'),('resources_sha256','resources.json'),('worker_log_sha256','worker.log')]:review[key]=sha(tmp_path/name)
    path=tmp_path/'review.json';path.write_text(json.dumps(review))
    if fault=='changed_log':(tmp_path/'worker.log').write_text('changed')
    if fault:
        with pytest.raises(ValueError):remaining_after_power_stop(tmp_path,path)
    else:assert remaining_after_power_stop(tmp_path,path)==87
