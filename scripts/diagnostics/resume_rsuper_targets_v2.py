"""Explicit continuation after a recorded pause; unchanged frozen v2 worker.
Uses the qualified teacher watchdog with bounded process-monitor timeout recovery.

Run under the existing one-shot launchd launcher, only after the previous job has
stopped and resources prove reaping. No auto resume, scientific training or retry.
"""
import argparse, json, math, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.diagnostics import build_rsuper_full_targets_v2 as frozen
from scripts.diagnostics.qualify_distillation_mac import BASE, write, storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.operations.mac_teacher_continuation_v1 import completed_members, remaining_seconds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pause-receipt', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    previous = args.previous.resolve(strict=True); output = args.output.resolve()
    if previous.parent != BASE or output.parent != BASE or previous == output:
        raise ValueError('Distinct generation directories under the existing artifact root required')
    if args.worker:
        request = json.loads((output/'request.json').read_text())
        frozen.OLD = previous; frozen.OUT = output; frozen.LIMITS = request['limits']
        frozen.worker()
        return
    from src.operations.full_training_platform import training_guard, require_ac
    from src.operations.mac_teacher_supervision_v2 import run
    require_ac(); storage_preflight()
    request = json.loads((previous/'request.json').read_text())
    resources = json.loads((previous/'resources.json').read_text())
    receipt = json.loads(args.pause_receipt.read_text())
    if (receipt.get('stopped') is not True or receipt['directory'] != str(previous)
            or receipt['request_sha256'] != sha(previous/'request.json')
            or receipt['resources_sha256'] != sha(previous/'resources.json')):
        raise ValueError('Recorded pause identity differs')
    for path, pin in request['pins'].items():
        if sha(Path(path)) != pin: raise ValueError('Previous producing pin changed: '+path)
    killed = receipt.get('owned_worker_kill_requested', False)
    if killed and sha(args.pause_receipt.parent/'kill-request.json') != receipt['kill_request_sha256']:
        raise ValueError('Operator worker-stop record changed')
    remaining = remaining_seconds(request, resources, owned_worker_kill=killed)
    members = completed_members(previous, request)
    request['reused_completed'] = members
    request['limits'] = dict(request['limits'], seconds=remaining)
    request['continuation'] = dict(previous_request_sha256=sha(previous/'request.json'),
        previous_resources_sha256=sha(previous/'resources.json'),
        pause_receipt_sha256=sha(args.pause_receipt), previous_completed=len(members),
        prior_stage_seconds_charged=math.ceil(resources['seconds']),
        original_wall_budget_seconds=96*3600, no_automatic_retry=True)
    files = [Path(__file__).resolve(), ROOT/'src/operations/mac_teacher_continuation_v1.py',
             previous/'request.json', previous/'resources.json', args.pause_receipt]
    if killed: files.append(args.pause_receipt.parent/'kill-request.json')
    files += [ROOT/'src/operations/mac_teacher_watch_v2.py', ROOT/'src/operations/mac_teacher_supervision_v2.py']
    files += [previous/(name+suffix) for name in members for suffix in ('.json', '.npz')]
    request['pins'].update({str(p.resolve()): sha(p) for p in files})
    existing = sum(p.stat().st_size for p in BASE.rglob('*.npz'))
    if existing + request['limits']['output_bytes'] > 32*1024**3:
        raise ValueError('Combined cache budget needs review before continuation')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        output.mkdir(exist_ok=False); write(output/'request.json', request)
        def tick():
            if sum(p.stat().st_size for p in output.iterdir() if p.is_file()) > request['limits']['output_bytes']:
                raise ValueError('Output budget')
        command = ['caffeinate', '-i', sys.executable, __file__, '--worker',
                   '--previous', str(previous), '--output', str(output),
                   '--pause-receipt', str(args.pause_receipt.resolve())]
        if not run(command, output, seconds=remaining, rss_bytes=request['limits']['rss_bytes'],
                   tick=tick, env=dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK='0', OMP_NUM_THREADS='2')):
            raise SystemExit(1)


if __name__ == '__main__': main()
