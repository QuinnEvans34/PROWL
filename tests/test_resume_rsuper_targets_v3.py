import json
import sys
from contextlib import nullcontext
import numpy as np
import pytest
from src.data.segmenter_teacher_cache_v1 import sha
from scripts.diagnostics import resume_rsuper_targets_v3 as resume
from src.operations import full_training_platform as platform, mac_teacher_supervision_v2 as supervision


@pytest.mark.parametrize('output_cap', [10000, 31*1024**3])
def test_continuation_preserves_recipe_and_tightens_only_large_output_cap(tmp_path, monkeypatch, output_cap):
    previous = tmp_path/'previous'; previous.mkdir()
    payload=previous/'A.npz'; np.savez_compressed(payload,probability=np.zeros((2,3,4),np.uint16))
    row=dict(case_id='A',payload_sha256=sha(payload),bytes=payload.stat().st_size,native_geometry={'shape':[2,3,4]})
    (previous/'A.json').write_text(json.dumps(row))
    request=dict(train=['A','B'],teacher={'fixed':'teacher'},preprocessing_policy={'fixed':'policy'},
                 pins={},limits=dict(seconds=100,output_bytes=output_cap,rss_bytes=1000000))
    (previous/'request.json').write_text(json.dumps(request))
    (previous/'resources.json').write_text(json.dumps(dict(workers_reaped=True,success=False,
        error="InterruptedError('Supervisor signal 15')",seconds=12.5)))
    receipt=tmp_path/'pause.json'
    receipt.write_text(json.dumps(dict(stopped=True,directory=str(previous),
        request_sha256=sha(previous/'request.json'),resources_sha256=sha(previous/'resources.json'))))
    output=tmp_path/'next'; captured=[]
    monkeypatch.setattr(resume,'BASE',tmp_path)
    monkeypatch.setattr(resume,'storage_preflight',lambda:None)
    monkeypatch.setattr(platform,'require_ac',lambda:None)
    monkeypatch.setattr(platform,'training_guard',lambda _:nullcontext())
    monkeypatch.setattr(supervision,'run',lambda command,directory,**kwargs:captured.append((command,directory,kwargs)) or True)
    monkeypatch.setattr(sys,'argv',['resume','--previous',str(previous),'--output',str(output),'--pause-receipt',str(receipt)])
    resume.main()
    prepared=json.loads((output/'request.json').read_text())
    assert prepared['teacher']==request['teacher'] and prepared['preprocessing_policy']==request['preprocessing_policy']
    assert prepared['train']==request['train'] and prepared['reused_completed']=={'A':row}
    assert prepared['limits']==dict(seconds=87,output_bytes=min(output_cap,30*1024**3),rss_bytes=1000000)
    assert captured[0][2]['seconds']==87 and '--worker' in captured[0][0]
    assert sha(previous/'request.json')==json.loads(receipt.read_text())['request_sha256']
    assert all(sha(path)==pin for path,pin in prepared['pins'].items())
