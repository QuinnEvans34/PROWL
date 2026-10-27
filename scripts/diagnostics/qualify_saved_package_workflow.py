#!/usr/bin/env python3
"""Read-only integrity/handoff workflow for an explicitly pinned saved package."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.operations.saved_package_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor
from src.operations.workflow_contracts_v1 import execute_registered, registry_for


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['plan','run','resume','inspect','status'])
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--source',type=Path)
    p.add_argument('--manifest-sha256')
    p.add_argument('--resume-of')
    p.add_argument('--run-id')
    a=p.parse_args()
    if a.command not in ('inspect','status') and (not a.source or not a.manifest_sha256):
        p.error('--source and --manifest-sha256 required')
    if a.command in ('inspect','status') and not a.run_id:p.error('--run-id required')
    if a.command=='resume' and not a.resume_of:p.error('--resume-of required')
    def root_check():
        if not a.root.is_dir():raise OSError('Dedicated workflow root must exist')
    try:
        e=Executor(a.root,check_root=root_check,sensitivity='research-local')
        if a.command in ('inspect','status'):result=e.inspect(a.run_id)
        else:
            s,h,v=definition(a.source,a.manifest_sha256)
            if a.command=='plan':
                registry_for('saved-package',s)
                result=e.preview(s,v,resume_of=a.resume_of)
            else:
                a.run_id=a.run_id or str(uuid.uuid4())
                result=execute_registered(e,'saved-package',s,h,v,resume_of=a.resume_of,identity=a.run_id)
        print(json.dumps(result,sort_keys=True));return 0
    except Exception as exc:
        print(json.dumps({'error':str(exc),'type':type(exc).__name__,'run_id':a.run_id,
                          'automatic_retry':False}),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
