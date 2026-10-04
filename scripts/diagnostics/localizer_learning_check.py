"""Retained CPU synthetic learning + subprocess interruption diagnostic; no raw inputs."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import time
from uuid import uuid4
import torch
from src.data.manifest_records import canonical,digest
from src.operations.artifact_store import ArtifactStore
from src.training.localizer import LocalizerSession,loss_value,foreground_dice
from src.training.localizer_checkpoint import save,resume


def fixture():
    target=torch.zeros(1,16,16,16);target[:,4:12,4:12,4:12]=1
    return target*.8+.1,target


def write(path,value):
    with path.open('xb') as stream:
        stream.write(canonical(value));stream.flush();os.fsync(stream.fileno())


def run(root,child=False):
    torch.set_num_threads(2)
    identity=json.loads((root/'identity.json').read_bytes())
    store=ArtifactStore(root/'checkpoints',check_root=lambda:None)
    image,target=fixture()
    if child:
        session=LocalizerSession(identity['config']);history=[]
        for _ in range(4):history.append(session.update(image,target,'invented-cube'))
        reference=save(store,session,identity)
        write(root/'interrupted-attempt.json',dict(attempt_id=str(uuid4()),history=history,checkpoint=reference,
            next_action='intentional SIGTERM after completed checkpoint'))
        os.kill(os.getpid(),signal.SIGTERM)
        raise RuntimeError('SIGTERM did not terminate worker')
    start=time.monotonic()
    command=[sys.executable,'-m','scripts.diagnostics.localizer_learning_check','--child',str(root)]
    with (root/'worker.log').open('xb') as log:
        worker=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=False)
    assert worker.returncode==-signal.SIGTERM, worker.returncode
    interrupted=json.loads((root/'interrupted-attempt.json').read_bytes())
    recovered=resume(store,interrupted['checkpoint'],identity)
    # New independent scratch trajectory is the exact continuation oracle.
    baseline=LocalizerSession(identity['config'])
    with torch.no_grad():initial=loss_value(baseline.model(image[None]),target[None].long()).item()
    before=baseline.predict(image).argmax(0,keepdim=True)
    baseline_rows=[baseline.update(image,target,'invented-cube') for _ in range(20)]
    resumed_rows=[recovered.update(image,target,'invented-cube') for _ in range(16)]
    assert resumed_rows==baseline_rows[4:]
    assert all(torch.equal(v,recovered.model.state_dict()[k]) for k,v in baseline.model.state_dict().items())
    final_reference=save(store,recovered,identity)
    fresh=resume(store,final_reference,identity)
    probabilities=fresh.predict(image)
    assert torch.equal(probabilities,baseline.predict(image))
    with torch.no_grad():final=loss_value(fresh.model(image[None]),target[None].long()).item()
    assert final<initial*.8
    report=dict(state='passed',synthetic_only=True,initial_loss=initial,final_loss=final,
        initial_metric=foreground_dice(before,target),final_metric=foreground_dice(probabilities.argmax(0,keepdim=True),target),
        completed_steps=20,total_optimizer_updates=40,interruption_exit_code=worker.returncode,
        exact_cpu_continuation=True,exact_reload_prediction=True,checkpoint=final_reference,
        resumed_attempt_id=str(uuid4()),resumed_from=interrupted['checkpoint'],history=resumed_rows,
        elapsed_seconds=time.monotonic()-start,peak_parent_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        peak_children_rss=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        rss_units='bytes on macOS, KiB on Linux',model_parameters=sum(p.numel() for p in fresh.model.parameters()))
    write(root/'report.json',report)
    members={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes()))
        for p in root.rglob('*') if p.is_file() and p.name!='.writer.lock'}
    write(root/'receipt.json',dict(schema_version='1.0.0',state='complete',run_id=identity['run_id'],members=members))
    print(json.dumps(dict(package=str(root),receipt_sha256=digest((root/'receipt.json').read_bytes()),
                         initial_loss=initial,final_loss=final,elapsed_seconds=report['elapsed_seconds'])))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');parser.add_argument('--child',type=Path)
    args=parser.parse_args()
    if args.child:return run(args.child,child=True)
    if not args.run:parser.error('--run required')
    signal.alarm(600)
    root=Path.cwd()/'outputs/prowl'/('localizer-learning-'+str(uuid4()));root.mkdir();(root/'checkpoints').mkdir()
    code_paths=['src/training/localizer.py','src/training/localizer_checkpoint.py','src/models/segresnet.py',
        'src/operations/artifact_store.py','src/data/manifest_records.py','src/data/source_inventory_records.py',
        'scripts/diagnostics/localizer_learning_check.py']
    source={p:Path(p).read_text() for p in code_paths}
    write(root/'source.json',source)
    environment=dict(python=sys.version,platform=platform.platform(),machine=platform.machine(),
        packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
        torch_threads=2,device='cpu',precision='float32',workers=0,cache='none')
    write(root/'environment.json',environment)
    config=dict(patch_size=[16]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=40)
    identity=dict(schema_version='1.0.0',run_id='localizer-synthetic-'+str(uuid4()),run_class='diagnostic',data_mode='synthetic',
        config=config,code_sha256=digest(canonical(source)),environment_sha256=digest(canonical(environment)),
        cohort_sha256=digest(b'invented-cube-16-center-4:12-v1'),preprocessing_sha256=digest(b'invented-binary-times-.8-plus-.1-v1'),
        device='cpu',precision='float32',workers=0,cache='none')
    write(root/'identity.json',identity)
    write(root/'plan.json',dict(maximum_total_updates=40,wall_time_seconds=600,threads=2,
        artifacts_max_bytes=256*1024**2,acceptance='final loss < 0.8 initial; exact CPU restart and predictions',
        real_data=False,tracking='canonical local records; no service',promotion_eligible=False))
    try:run(root)
    except BaseException as error:
        write(root/'failure.json',dict(state='failed',error_type=type(error).__name__,message=str(error)))
        raise


if __name__=='__main__':main()
