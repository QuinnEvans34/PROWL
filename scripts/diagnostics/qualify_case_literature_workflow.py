#!/usr/bin/env python3
"""Link an explicitly pinned offline answer capture; never call search or a model."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.operations.case_literature_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor
from src.operations.workflow_contracts_v1 import execute_registered, registry_for


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['plan','run','resume','inspect','status'])
    for flag in ('root','source','capture'):p.add_argument('--'+flag,type=Path,required=flag=='root')
    for flag in ('manifest-sha256','capture-sha256','resume-of','run-id'):p.add_argument('--'+flag)
    p.add_argument('--node',help='Explicit verified Node runtime; default uses PATH')
    a=p.parse_args()
    if a.command in ('inspect','status'):
        if not a.run_id:p.error('--run-id required')
    elif not all((a.source,a.capture,a.manifest_sha256,a.capture_sha256)):
        p.error('Explicit source/capture paths and both SHA256 pins required')
    if a.command=='resume' and not a.resume_of:p.error('--resume-of required')
    try:
        def admit():
            if not a.root.is_dir():raise OSError('Dedicated root must exist')
        e=Executor(a.root,check_root=admit,sensitivity='research-local')
        if a.command in ('inspect','status'):r=e.inspect(a.run_id)
        else:
            s,h,v=definition(a.source,a.manifest_sha256,a.capture,a.capture_sha256,node=a.node)
            if a.command=='plan':
                registry_for('case-literature',s)
                r=e.preview(s,v,resume_of=a.resume_of)
            else:
                a.run_id=a.run_id or str(uuid.uuid4());r=execute_registered(e,'case-literature',s,h,v,resume_of=a.resume_of,identity=a.run_id)
        print(json.dumps(r,sort_keys=True));return 0
    except Exception as error:
        print(json.dumps({'error':str(error),'run_id':a.run_id,'automatic_retry':False}),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
