"""Explicit one-stage engineering dispatch; no retries or scientific launch."""
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path
from src.data.manifest_records import canonical, digest
from src.data.segmenter_teacher_cache_v1 import sha
from src.data.teacher_target_publication_v1 import read_bound

def runtime():
    return dict(python=sys.version, executable=sys.executable,
                packages={name:version(name) for name in ('torch','monai','numpy','scipy','nibabel')})


STAGES = ('reference', 'zero', 'producer', 'cold')
LIMITS = dict(seconds=1200, rss_bytes=12*1024**3, mps_bytes=12*1024**3,
              output_bytes=2*1024**3, backup_bytes=4*1024**3)


def write(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())


def check_pins(pins):
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError(f'Qualification pin changed: {path}')


def prepare(preparation, preparation_sha256, output, backup, positive, empty, code_pins):
    prepared = read_bound(preparation, preparation_sha256)
    if prepared['status'] != 'PREPARED_NOT_GPU_QUALIFIED' or prepared['scientific_ready'] is not False:
        raise ValueError('Qualification preparation required')
    check_pins(prepared['pins']); check_pins(code_pins)
    control = json.loads((Path(prepared['admitted_targets'])/'provider-control.json').read_text())
    if positive == empty or not {positive, empty} <= set(control['validation']):
        raise ValueError('Two distinct development members required')
    output = Path(output).resolve(); backup = Path(backup).resolve()
    if output.exists() or backup.exists():
        raise FileExistsError('Use fresh qualification and backup directories')
    if output == backup or output in backup.parents or backup in output.parents:
        raise ValueError('Separate output and backup required')
    request = dict(version='full-provider-mps-qualification-1',
        preparation=str(Path(preparation).resolve()), preparation_sha256=preparation_sha256,
        backup=str(backup), development=dict(positive=positive, empty=empty),
        limits=LIMITS, stages=list(STAGES), engineering_updates=dict(reference=4, zero=4, producer=4, cold=1),
        scientific_updates=0, scientific_ready=False, code_pins=code_pins, runtime=runtime())
    output.mkdir(); write(output/'request.json', request)
    return request


def validate_request(root, request_sha256):
    request = read_bound(Path(root)/'request.json', request_sha256)
    if (request.get('version') != 'full-provider-mps-qualification-1'
            or request['limits'] != LIMITS or request['stages'] != list(STAGES)
            or request['engineering_updates'] != dict(reference=4, zero=4, producer=4, cold=1)
            or request['scientific_ready'] is not False or request['scientific_updates'] != 0):
        raise ValueError('Unsupported qualification request')
    if request.get('runtime') != runtime():
        raise ValueError('Qualification runtime changed')
    check_pins(request['code_pins'])
    prepared = read_bound(request['preparation'], request['preparation_sha256'])
    check_pins(prepared['pins'])
    return request, prepared


def prerequisites(root, stage, request_sha256):
    if stage not in STAGES:
        raise ValueError('Unknown engineering stage')
    parents = {}
    for name in STAGES[:STAGES.index(stage)]:
        path = Path(root)/name/'receipt.json'
        receipt = json.loads(path.read_text())
        if receipt['stage'] != name or receipt['request_sha256'] != request_sha256 or receipt['success'] is not True:
            raise ValueError('Qualified predecessor required')
        check_pins(receipt['artifacts'])
        parents[name] = sha(path)
    return parents


def dispatch(root, stage, request_sha256, *, guard, preflight, supervise, command, env=None):
    """Dependencies are injectable for synthetic tests, never CLI-configurable commands."""
    root = Path(root)
    request, _ = validate_request(root, request_sha256)
    parents = prerequisites(root, stage, request_sha256)
    destination = root/stage
    if destination.exists():
        raise FileExistsError('Stage already attempted; preserve it')
    with guard():
        preflight(request)
        destination.mkdir()
        write(destination/'dispatch.json', dict(stage=stage, request_sha256=request_sha256,
              parents=parents, supervisor=os.getpid()))
        success = supervise(command(stage), destination, seconds=LIMITS['seconds'],
                            rss_bytes=LIMITS['rss_bytes'], tick=lambda: preflight(request), env=env)
        resources = json.loads((destination/'resources.json').read_text())
        if (not success or resources.get('success') is not True
                or resources.get('workers_reaped') is not True
                or type(resources.get('exit_code')) is not int or resources['exit_code'] != 0):
            raise ValueError('Worker failed or was not reaped; no retry')
        result = json.loads((destination/'result.json').read_text())
        if (result.get('stage') != stage or result.get('success') is not True
                or result.get('scientific_updates') != 0
                or result.get('engineering_updates') != request['engineering_updates'][stage]):
            raise ValueError('Engineering stage result mismatch')
        # The final checkpoint/result may be written after the last monitor tick.
        # Recheck capacity and output caps while still holding exclusive ownership.
        preflight(request)
        check_pins(result['evidence'])
        validate_request(root, request_sha256)
        if parents != prerequisites(root, stage, request_sha256):
            raise ValueError('Predecessor changed during stage')
        artifacts = {str(p.resolve()):sha(p) for p in destination.rglob('*') if p.is_file()}
        artifacts.update(result['evidence'])
        receipt = dict(stage=stage, success=True, request_sha256=request_sha256,
                       parents=parents, artifacts=artifacts, scientific_ready=False)
        write(destination/'receipt.json', receipt)
        return receipt
