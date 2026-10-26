#!/usr/bin/env python3
"""CPU-only invented workflow demonstration. No production case or arbitrary command dispatch."""
import argparse
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.operations.case_evidence_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['plan','run','resume','inspect','status'])
    p.add_argument('--root',type=Path,required=True,help='Dedicated existing synthetic evidence directory')
    p.add_argument('--run-id',help='Existing run for inspect/status; new UUID for run/resume')
    p.add_argument('--resume-of',help='Explicit completed/failed/interrupted parent run')
    p.add_argument('--evidence-version',type=int,default=1)
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    def root_check():
        if not args.root.is_dir() or args.root.absolute()!=args.root.resolve():
            raise ValueError('Existing canonical synthetic root required')
    executor=Executor(args.root,check_root=root_check)
    try:
        stages,handlers,validators=definition(evidence_version=args.evidence_version)
        if args.command=='plan':result=executor.preview(stages,validators,resume_of=args.resume_of)
        elif args.command in ('inspect','status'):
            if not args.run_id:p.error('--run-id required')
            result=executor.inspect(args.run_id)
        else:
            args.run_id=args.run_id or str(uuid.uuid4())
            if args.command=='resume' and not args.resume_of:p.error('--resume-of required')
            result=executor.execute(stages,handlers,validators,resume_of=args.resume_of,identity=args.run_id)
        if args.json:print(json.dumps(result,sort_keys=True))
        elif 'decisions' in result:
            for r in result['decisions']:print(f"{r['stage']}: {r['action']} — {r['reason']}")
        else:
            print(f"Run {result['run_id']}: {result['state']}")
            for stage,state in result['stages'].items():print(f'{stage}: {state}')
            for e in result['events']:
                if e['state']=='failed':print(f"Failure: {e['error']}")
            if result['state']!='complete':print('Next: inspect the failure, then explicitly resume with --resume-of. No automatic retry.')
        return 0
    except Exception as exc:
        print(f'{type(exc).__name__}: {exc}',file=sys.stderr)
        if args.run_id:print(f'Run ID: {args.run_id}',file=sys.stderr)
        print('No automatic retry. Inspect the saved attempt before resuming.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
