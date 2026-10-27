"""Synthetic subprocess cancellation of the real registered CPU adapter path."""
import os
from pathlib import Path
import signal
import sys
import time
from src.operations.saved_package_workflow_v1 import definition
from src.operations.workflow_contracts_v1 import execute_registered
from src.operations.workflow_execution_v1 import Executor
from src.operations.case_evidence_workflow_v1 import native_fixture
from src.data.manifest_records import digest

root=Path(sys.argv[1]);identity=sys.argv[2]
source=root/'source';source.mkdir()
for name,data in native_fixture().items():(source/name).write_bytes(data)
e=Executor(root,check_root=lambda:None,minimum_free_bytes=0,sensitivity='research-local')
s,h,v=definition(source,digest((source/'manifest.json').read_bytes()))
original=h['integrity']
def slow(parents,config):
    (root/'ready').write_text('synthetic handler entered')
    deadline=time.monotonic()+5
    while not (root/'release').exists():
        if time.monotonic()>deadline:raise RuntimeError('Fixture release deadline')
        time.sleep(.02)
    return original(parents,config)
h['integrity']=slow
result=execute_registered(e,'saved-package',s,h,v,identity=identity)
assert result['state']=='cancelled'
