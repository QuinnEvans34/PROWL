from contextlib import contextmanager, nullcontext
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from src.operations.kd_gpu_qualification_v1 import prepare,dispatch,write,LIMITS
from src.data.segmenter_teacher_cache_v1 import sha


def fixture(tmp_path):
    admitted=tmp_path/'admitted';admitted.mkdir()
    write(admitted/'provider-control.json',dict(validation=['positive','empty']))
    prep=tmp_path/'preparation.json'
    write(prep,dict(status='PREPARED_NOT_GPU_QUALIFIED',scientific_ready=False,
          admitted_targets=str(admitted),pins={str(admitted/'provider-control.json'):sha(admitted/'provider-control.json')}))
    code=tmp_path/'code.txt';code.write_text('synthetic')
    root=tmp_path/'run'
    prepare(prep,sha(prep),root,tmp_path/'backup','positive','empty',{str(code):sha(code)})
    return root,sha(root/'request.json')


def supervisor(command,destination,**kwargs):
    stage=command[0]
    write(destination/'evidence.json',dict(synthetic=True))
    write(destination/'result.json',dict(success=True,stage=stage,scientific_updates=0,
          engineering_updates=1 if stage=='cold' else 4,
          evidence={str(destination/'evidence.json'):sha(destination/'evidence.json')}))
    write(destination/'resources.json',dict(success=True,workers_reaped=True,exit_code=0))
    return True


def run(root,pin,stage='reference',**kw):
    args=dict(guard=nullcontext,preflight=lambda r:None,supervise=supervisor,command=lambda s:[s])
    args.update(kw)
    return dispatch(root,stage,pin,**args)


def test_stage_chain_and_no_duplicate_dispatch(tmp_path):
    root,pin=fixture(tmp_path)
    for stage in ('reference','zero','producer','cold'):
        receipt=run(root,pin,stage)
        assert receipt['success'] and receipt['scientific_ready'] is False
        with pytest.raises(FileExistsError):run(root,pin,stage)
    assert len(json.loads((root/'cold/receipt.json').read_text())['parents'])==3


@pytest.mark.parametrize('fault',['pin','predecessor','lock','preflight'])
def test_reject_before_worker_and_output(tmp_path,fault):
    root,pin=fixture(tmp_path);stage='reference';kwargs={}
    def fail(*args):raise RuntimeError('synthetic gate')
    if fault=='pin':(tmp_path/'code.txt').write_text('changed')
    elif fault=='predecessor':stage='zero'
    elif fault=='lock':kwargs['guard']=fail
    else:kwargs['preflight']=fail
    kwargs['supervise']=lambda *a,**k:pytest.fail('worker must not start')
    with pytest.raises((ValueError,FileNotFoundError,RuntimeError)):run(root,pin,stage,**kwargs)
    assert not (root/stage).exists()


def test_tampered_predecessor_rejected(tmp_path):
    root,pin=fixture(tmp_path);run(root,pin)
    (root/'reference/evidence.json').write_text('bad')
    with pytest.raises(ValueError):run(root,pin,'zero')
    assert not (root/'zero').exists()


@pytest.mark.parametrize('kind',['nonzero','timeout','success'])
def test_real_supervisor_reaps_synthetic_worker(tmp_path,kind):
    from src.operations.mac_teacher_supervision_v2 import run as owned
    root,pin=fixture(tmp_path)
    if kind=='success':
        # Avoid importing any training code in the subprocess.
        code="""import json,pathlib,hashlib,time
p=pathlib.Path(__import__('sys').argv[1]);time.sleep(.15)
e=p/'evidence.json';e.write_text('{}')
(p/'result.json').write_text(json.dumps(dict(success=True,stage='reference',scientific_updates=0,engineering_updates=4,evidence={str(e):hashlib.sha256(e.read_bytes()).hexdigest()})))
"""
    else:code="import time;time.sleep(.15);raise SystemExit(7)" if kind=='nonzero' else 'import time;time.sleep(20)'
    def supervised(command,dest,**kwargs):
        kwargs['seconds']=.2 if kind=='timeout' else 10
        return owned(command,dest,**kwargs)
    kwargs=dict(supervise=supervised,command=lambda s:[sys.executable,'-c',code,str(root/s)])
    if kind=='success':run(root,pin,**kwargs)
    else:
        with pytest.raises(ValueError):run(root,pin,**kwargs)
        assert not (root/'reference/receipt.json').exists()
    resource=json.loads((root/'reference/resources.json').read_text())
    assert resource['workers_reaped'] is True
    process=json.loads((root/'reference/process.json').read_text())
    with pytest.raises(ProcessLookupError):os.kill(process['worker'],0)


def test_cli_requires_explicit_stage_authorization(tmp_path):
    result=subprocess.run([sys.executable,'scripts/diagnostics/qualify_full_provider_mps.py',
        '--root',str(tmp_path/'absent'),'--stage','reference','--request-sha256','0'*64],
        capture_output=True,text=True,timeout=30)
    assert result.returncode!=0 and 'Explicit engineering run selection required' in result.stderr
    assert not (tmp_path/'absent').exists()


def test_runtime_drift_rejects_before_dispatch(tmp_path, monkeypatch):
    root,pin=fixture(tmp_path)
    monkeypatch.setattr('src.operations.kd_gpu_qualification_v1.runtime',lambda: {'changed':True})
    with pytest.raises(ValueError,match='runtime changed'):
        run(root,pin,supervise=lambda *a,**k:pytest.fail('worker must not start'))
    assert not (root/'reference').exists()


@pytest.mark.parametrize('failure',['output_cap','storage_loss'])
def test_final_resource_failure_preserves_successful_worker_without_receipt(tmp_path,failure):
    root,pin=fixture(tmp_path)
    def final_gate(request):
        # Inject a change after the supervised worker's last tick/exit.
        if (root/'reference/result.json').exists():
            raise RuntimeError(failure)
    with pytest.raises(RuntimeError,match=failure):
        run(root,pin,preflight=final_gate)
    assert json.loads((root/'reference/resources.json').read_text())['workers_reaped'] is True
    assert (root/'reference/result.json').exists()
    assert not (root/'reference/receipt.json').exists()
    with pytest.raises(FileExistsError):run(root,pin)
    with pytest.raises(FileNotFoundError):run(root,pin,'zero')
