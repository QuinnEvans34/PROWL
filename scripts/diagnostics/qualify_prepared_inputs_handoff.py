"""Read-only saved preparation handoff; input references are explicit path/SHA256 pairs."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.operations.prepared_inputs_workflow_v1 import definition
from src.operations.workflow_contracts_v1 import execute_registered,registry_for
from src.operations.workflow_execution_v1 import Executor


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['plan','run','resume','inspect'])
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--inputs',type=Path)
    p.add_argument('--resume-of');p.add_argument('--run-id')
    a=p.parse_args()
    if a.command=='inspect' and not a.run_id:p.error('--run-id required')
    if a.command!='inspect' and not a.inputs:p.error('--inputs required')
    if a.command=='resume' and not a.resume_of:p.error('--resume-of required')
    try:
        def check():
            if not a.root.is_dir():raise OSError('Dedicated existing output root required')
        e=Executor(a.root,check_root=check,sensitivity='research-local')
        if a.command=='inspect':result=e.inspect(a.run_id)
        else:
            s,h,v=definition(json.loads(a.inputs.read_bytes()))
            registry_for('prepared-inputs',s)
            if a.command=='plan':result=e.preview(s,v,resume_of=a.resume_of)
            else:
                a.run_id=a.run_id or str(uuid.uuid4())
                result=execute_registered(e,'prepared-inputs',s,h,v,identity=a.run_id,resume_of=a.resume_of)
        print(json.dumps(result));return 0
    except Exception as error:
        print(json.dumps({'error':str(error),'run_id':a.run_id,'training_authorized':False}),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
