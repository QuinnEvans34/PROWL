"""Operator-only stop of the named launchd teacher job; never schedules a stop."""
import argparse, json, os, re, signal, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE, write
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.operations.mac_pilot_supervision_v1 import identity
from src.operations.mac_teacher_continuation_v1 import remaining_seconds, completed_members


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--label', required=True)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); directory = a.directory.resolve(strict=True)
    if directory.parent != BASE or not re.fullmatch(r'com\.prowl\.rsuper-targets-[a-z0-9.-]+', a.label):
        raise ValueError('Existing scoped teacher job required')
    if (directory/'resources.json').exists(): raise ValueError('Job already stopped; inspect its resources')
    proc = json.loads((directory/'process.json').read_text())
    target = f'gui/{os.getuid()}/{a.label}'
    description = subprocess.check_output(['launchctl', 'print', target], text=True)
    match = re.search(r'^\s*pid = (\d+)\s*$', description, re.M)
    if match is None or int(match[1]) != proc['supervisor']:
        raise ValueError('Registered supervisor identity differs')
    if identity(proc['worker']) != proc['worker_start']:
        raise ValueError('Worker identity differs')
    parent = subprocess.check_output(['ps', '-p', str(proc['worker']), '-o', 'ppid='], text=True).strip()
    if int(parent) != proc['supervisor']: raise ValueError('Worker ownership differs')
    request = json.loads((directory/'request.json').read_text())
    a.output.mkdir(parents=True, exist_ok=False)
    write(a.output/'request.json', dict(directory=str(directory), label=a.label,
        request_sha256=sha(directory/'request.json'), process=proc, action='explicit_operator_pause'))
    subprocess.run(['launchctl', 'kill', 'SIGTERM', target], check=True)
    grace = time.monotonic()+5
    while not (directory/'resources.json').exists() and time.monotonic() < grace:
        time.sleep(.1)
    killed = False
    if not (directory/'resources.json').exists():
        # Kill only the identity-checked private worker group, leaving its
        # supervisor alive to collect resource/reaping evidence.
        if identity(proc['worker']) != proc['worker_start'] or os.getpgid(proc['worker']) != proc['worker']:
            raise ValueError('Worker group changed; refusing fallback')
        parent = subprocess.check_output(['ps', '-p', str(proc['worker']), '-o', 'ppid='], text=True).strip()
        if int(parent) != proc['supervisor']: raise ValueError('Supervisor ownership changed')
        write(a.output/'kill-request.json', dict(process=proc, action='explicit_owned_worker_group_kill',
            reason='normal stop not observed after five seconds', request_sha256=sha(directory/'request.json')))
        os.killpg(proc['worker'], signal.SIGKILL); killed = True
    deadline = time.monotonic()+20
    while not (directory/'resources.json').exists():
        if time.monotonic() > deadline: raise TimeoutError('Pause cleanup not confirmed; do not disconnect')
        time.sleep(.1)
    resources = json.loads((directory/'resources.json').read_text())
    remaining = remaining_seconds(request, resources, owned_worker_kill=killed)
    # Do not consider a reused PID an owned live worker; never signal it.
    try: live = identity(proc['worker']) == proc['worker_start']
    except subprocess.CalledProcessError: live = False
    if live: raise ValueError('Worker still present; do not disconnect')
    members = completed_members(directory, request)
    write(a.output/'receipt.json', dict(stopped=True, directory=str(directory),
        request_sha256=sha(directory/'request.json'), resources_sha256=sha(directory/'resources.json'),
        completed_cases=len(members), remaining_active_seconds=remaining,
        owned_worker_kill_requested=killed,
        kill_request_sha256=sha(a.output/'kill-request.json') if killed else None,
        current_partial_case='not reused; will be recomputed', automatic_resume=False))
    print(f'Stopped and reaped. {len(members)} completed cases verified. Receipt: {a.output / "receipt.json"}')


if __name__ == '__main__': main()
