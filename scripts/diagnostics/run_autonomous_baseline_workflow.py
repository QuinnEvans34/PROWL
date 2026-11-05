"""Plan/run/explicitly resume saved baseline review; no inference or scheduling."""
import argparse
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.operations.autonomous_baseline_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor
from src.operations.workflow_contracts_v1 import execute_registered, registry_for


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['plan', 'run', 'resume', 'inspect', 'status'])
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--source', type=Path)
    for key in ['export-sha256', 'request-sha256', 'ready-sha256', 'run-id', 'resume-of']:
        p.add_argument('--'+key)
    a = p.parse_args()
    if a.command in ('inspect', 'status') and not a.run_id:
        p.error('--run-id required')
    if a.command not in ('inspect', 'status') and not all([a.source, a.export_sha256, a.request_sha256, a.ready_sha256]):
        p.error('Explicit source/export/request/ready identities required')
    if a.command == 'resume' and not a.resume_of:
        p.error('--resume-of required')
    try:
        def check_root():
            if not a.root.is_dir():raise OSError('Dedicated workflow output root must exist')
        executor = Executor(a.root, check_root=check_root, sensitivity='research-local')
        if a.command in ('inspect', 'status'):
            result = executor.inspect(a.run_id)
        else:
            stages, handlers, validators = definition(a.source, a.export_sha256, a.request_sha256, a.ready_sha256)
            if a.command == 'plan':
                registry_for('autonomous-baseline', stages)
                result = executor.preview(stages, validators, resume_of=a.resume_of)
            else:
                a.run_id = a.run_id or str(uuid.uuid4())
                result = execute_registered(executor, 'autonomous-baseline', stages, handlers, validators,
                                            identity=a.run_id, resume_of=a.resume_of)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(dict(error=str(exc), type=type(exc).__name__, run_id=a.run_id, automatic_retry=False)), file=sys.stderr)
        return 1


if __name__ == '__main__':raise SystemExit(main())
