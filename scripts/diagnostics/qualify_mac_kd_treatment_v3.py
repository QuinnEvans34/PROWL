"""Explicit two-worker MPS cold-restore qualification for a stopped continuation.

Three engineering updates, never scientific updates. Does not run validation or
change the scientific horizon. Executor selection/validation ordering is covered
by the separate CPU tests and existing native MPS qualification.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts import resume_mac_kd_treatment_v2 as continuation
from src.operations.kd_gpu_qualification_v1 import write,check_pins
from src.data.teacher_target_publication_v1 import read_bound
from src.data.segmenter_teacher_cache_v1 import sha

STAGES=('producer','cold')
LIMITS=dict(seconds=1200,rss_bytes=12*1024**3,output_bytes=2*1024**3,backup_bytes=512*1024**2)


def prepare(root,pin,out,backup,prior_failed):
    r=continuation.check(root,pin)
    if r['context'] is not None:raise ValueError('Fresh matched treatment required')
    out,backup=Path(out).resolve(),Path(backup).resolve()
    if out.exists() or backup.exists():raise FileExistsError('Fresh qualification destinations required')
    if (Path.home()/'PROWL-Backups').resolve() not in backup.parents:raise ValueError('Internal independent backup required')
    if out.parent.stat().st_dev==backup.parent.stat().st_dev:raise ValueError('Separate backup filesystem required')
    import math
    prior_failed=Path(prior_failed).resolve()
    prior_request=json.loads((prior_failed/'request.json').read_text())
    failure=json.loads((prior_failed/'producer/resources.json').read_text())
    log=(prior_failed/'producer/worker.log').read_text()
    if (prior_request['continuation_sha256']!=pin or failure.get('success') is not False
            or failure.get('workers_reaped') is not True or failure.get('exit_code')!=1
            or 'TypeError: Object of type float32 is not JSON serializable' not in log):
        raise ValueError('Only the reviewed serialization failure may precede this repair')
    charged=math.ceil(failure['seconds'])
    if not 0<charged<LIMITS['seconds']:raise ValueError('Qualification budget exhausted')
    files=[Path(__file__).resolve(),ROOT/'scripts/diagnostics/mac_kd_synthetic.py',
           ROOT/'src/training/segmenter_kd_evidence_executor_v1.py',
           prior_failed/'request.json',prior_failed/'producer/resources.json',prior_failed/'producer/worker.log']
    request=dict(version='mac-kd-treatment-check-2',continuation=str(Path(root).resolve()),continuation_sha256=pin,
                 backup=str(backup),limits=LIMITS,prior_failed=str(prior_failed),prior_backup=prior_request['backup'],charged_producer_seconds=charged,code_pins={str(f):sha(f) for f in files},scientific_updates=0)
    out.mkdir();write(out/'request.json',request)
    return request


def check(out,pin):
    request=read_bound(out/'request.json',pin)
    if request['version']!='mac-kd-treatment-check-2' or request['limits']!=LIMITS:raise ValueError('Qualification identity changed')
    check_pins(request['code_pins'])
    return request,continuation.check(Path(request['continuation']),request['continuation_sha256'])


def safety(out,request,r):
    continuation.safety(r)
    from scripts.diagnostics.qualify_distillation_mac import storage_preflight
    storage_preflight()
    if (continuation.original.usage(out)+continuation.original.usage(request['prior_failed'])>LIMITS['output_bytes']
            or continuation.original.usage(request['backup'])+continuation.original.usage(request['prior_backup'])>LIMITS['backup_bytes']):
        raise ValueError('Qualification storage cap')


def exercise(out,stage,request,context,restore,update,compare,tick,backup_admission):
    """Same engine with real sessions in worker and invented sessions in CPU tests."""
    import torch
    from src.training.segmenter_kd_evidence_executor_v1 import journal_value
    dest=out/stage;backup=Path(request['backup'])
    if stage=='producer':
        session=restore(None,None) if context is None else restore(torch.load(context['checkpoint'],weights_only=True,map_location='cpu')['session'],context['identity'])
        first=update(session);tick()
        torch.save(session.state(),dest/'saved.pt')
        backup_admission((dest/'saved.pt').stat().st_size)
        backup.mkdir(exist_ok=False)
        with (dest/'saved.pt').open('rb') as src,(backup/'saved.pt').open('xb') as dst:
            shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        if sha(dest/'saved.pt')!=sha(backup/'saved.pt'):raise ValueError('Independent backup mismatch')
        write(dest/'identity.json',session.identity)
        second=update(session);tick();torch.save(session.state(),dest/'expected.pt')
        write(dest/'updates.json',journal_value([first,second]))
    else:
        producer=out/'producer'
        if sha(producer/'saved.pt')!=sha(backup/'saved.pt'):raise ValueError('Independent backup changed')
        identity=json.loads((producer/'identity.json').read_text())
        saved=torch.load(backup/'saved.pt',weights_only=True,map_location='cpu')
        session=restore(saved,identity);compare(session.state(),saved)
        row=update(session);tick()
        expected=json.loads((producer/'updates.json').read_text())[1]
        for key in ('step','batch_sha256','member_id','learning_rate','kd_weight','teacher_accessed'):
            if row.get(key)!=expected.get(key):raise ValueError('Cold next input/counter differs: '+key)
        compare(session.state(),torch.load(producer/'expected.pt',weights_only=True,map_location='cpu'))
        write(dest/'updates.json',journal_value([row]))
    tick()
    evidence={str(p):sha(p) for p in dest.iterdir() if p.is_file() and p.name not in ('worker.log',)}
    evidence[str(backup/'saved.pt')]=sha(backup/'saved.pt')
    write(dest/'result.json',dict(success=True,stage=stage,scientific_updates=0,
          engineering_updates=2 if stage=='producer' else 1,evidence=evidence))


def worker(out,stage,pin):
    if os.environ.get('PROWL_CONTINUATION_CHECK')!='1':raise ValueError('Owned worker required')
    request,r=check(out,pin)
    dispatch=json.loads((out/stage/'dispatch.json').read_text())
    if dispatch!=dict(stage=stage,request_sha256=pin):raise ValueError('Dispatch mismatch')
    import torch
    from scripts.diagnostics.prepare_rsuper_full_provider import provider
    from scripts.diagnostics.mac_kd_synthetic import compare
    from src.training.segmenter_errata_kd_session_v1 import ErrataKDSession
    from src.data.segmenter_teacher_cache_v1 import TeacherTargetStore
    from scripts.diagnostics.qualify_distillation_mac import storage_preflight,check_storage_budget
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0' or not torch.backends.mps.is_available():raise ValueError('Actual MPS required')
    torch.set_num_threads(1);inputs,_,_=provider()
    design=r['scientific']['designs'][r['scientific']['order'].index(r['order'][0])]
    if inputs.pin!=design['provider_sha256']:raise ValueError('Provider changed')
    target=Path(r['scientific']['preparation']['admitted_targets'])
    targets=TeacherTargetStore(target,design['target_manifest_sha256'],control=inputs.control,
                              common_identity=json.loads((target/'common-identity.json').read_text()))
    def tick():
        safety(out,request,r);torch.mps.synchronize()
        if torch.mps.driver_allocated_memory()>continuation.original.LIMITS['mps_bytes']:raise ValueError('MPS allocation cap')
    def admission(size):
        space=storage_preflight()
        check_storage_budget(space['internal_free_bytes'],space['external_free_bytes'],space['existing_backup_bytes'],new_backup_bytes=size)
        if continuation.original.usage(request['backup'])+size>LIMITS['backup_bytes']:raise ValueError('Backup cap')
    def restore(saved,identity):
        if saved is not None:return ErrataKDSession.restore(saved,identity)
        from copy import deepcopy
        from src.training.segmenter_full_session_v1 import Session
        from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent
        from src.training.segmenter_distillation_v1 import DistillationConfig
        cfg=deepcopy(design['student_configuration']);init=cfg['initialization']
        init['checkpoint']=str((ROOT/init['checkpoint']).resolve())
        if sha(init['checkpoint'])!=init['sha256']:raise ValueError('Initialization differs')
        loss={k:v for k,v in design['distillation'].items() if k!='policy'}
        return ErrataKDSession(OnDemandStudent(Session(cfg['session'],inputs.control,device='mps',initialization=init)),
            teacher_identity=r['scientific']['preparation']['teacher'],loss_config=DistillationConfig(**loss),
            target_manifest_sha256=targets.pin)
    exercise(out,stage,request,r['context'],restore,lambda s:s.update(inputs,targets),compare,tick,admission)
    write(out/stage/'device.json',dict(device='mps',fallback=False))


def verify_stage(out,stage,pin):
    result=json.loads((out/stage/'result.json').read_text());resources=json.loads((out/stage/'resources.json').read_text())
    device=json.loads((out/stage/'device.json').read_text())
    if (result.get('success') is not True or result.get('stage')!=stage or result.get('scientific_updates')!=0
            or result.get('engineering_updates')!=(2 if stage=='producer' else 1)
            or resources.get('success') is not True or resources.get('workers_reaped') is not True
            or resources.get('exit_code')!=0 or device!=dict(device='mps',fallback=False)):
        raise ValueError('Actual GPU stage did not qualify')
    if json.loads((out/stage/'dispatch.json').read_text())!=dict(stage=stage,request_sha256=pin):raise ValueError('Wrong qualification dispatch')
    check_pins(result['evidence'])
    return {str(p):sha(p) for p in (out/stage).iterdir() if p.is_file()}


def run_stage(out,stage,pin):
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v3 import run
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        request,r=check(out,pin)
        if stage=='cold':
            receipt=read_bound(out/'producer-receipt.json',sha(out/'producer-receipt.json'))
            if receipt['request_sha256']!=pin:raise ValueError('Producer request changed')
            check_pins(receipt['evidence'])
        safety(out,request,r);dest=out/stage;dest.mkdir(exist_ok=False)
        write(dest/'dispatch.json',dict(stage=stage,request_sha256=pin))
        env=dict(os.environ,PROWL_CONTINUATION_CHECK='1',PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='1')
        ok=run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--root',str(out),
                '--worker',stage,'--request-sha256',pin],dest,seconds=LIMITS['seconds']-(request['charged_producer_seconds'] if stage=='producer' else 0),rss_bytes=LIMITS['rss_bytes'],
                tick=lambda:safety(out,request,r),env=env)
        if not ok:raise ValueError('Qualification failed; preserve attempt and do not retry')
        safety(out,request,r);evidence=verify_stage(out,stage,pin);check(out,pin)
        write(out/(stage+'-receipt.json'),dict(request_sha256=pin,evidence=evidence))
        if stage=='cold':
            evidence.update(verify_stage(out,'producer',pin))
            evidence[str(out/'request.json')]=pin
            evidence.update(request['code_pins'])
            write(out/'qualified.json',dict(version='mac-kd-treatment-gpu-2',success=True,workers_reaped=True,
                  continuation_sha256=request['continuation_sha256'],evidence=evidence,scientific_updates=0,
                  scope='Actual MPS state restore and next-update equivalence; native validation ordering covered separately'))


def validate_qualification(path,pin,continuation_pin):
    path=Path(path);out=path.parent
    proof=read_bound(path,pin)
    if (proof.get('version')!='mac-kd-treatment-gpu-2' or proof.get('success') is not True
            or proof.get('workers_reaped') is not True or proof.get('continuation_sha256')!=continuation_pin
            or proof.get('scientific_updates')!=0):raise ValueError('Bound real GPU continuation qualification required')
    check_pins(proof['evidence'])
    request_pin=proof['evidence'].get(str(out/'request.json'))
    if not request_pin:raise ValueError('Bound qualification request required')
    request=read_bound(out/'request.json',request_pin)
    if request['continuation_sha256']!=continuation_pin or request['limits']!=LIMITS:
        raise ValueError('Qualification request mismatch')
    check_pins(request['code_pins'])
    for stage in STAGES:
        artifacts=verify_stage(out,stage,request_pin)
        if any(proof['evidence'].get(name)!=digest for name,digest in artifacts.items()):
            raise ValueError('Qualification stage evidence incomplete')
    return proof


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--prepare',action='store_true');mode.add_argument('--stage',choices=STAGES);mode.add_argument('--worker',choices=STAGES)
    p.add_argument('--prior-failed',type=Path);p.add_argument('--continuation',type=Path);p.add_argument('--continuation-sha256');p.add_argument('--backup',type=Path);p.add_argument('--request-sha256')
    a=p.parse_args()
    if a.prepare:prepare(a.continuation,a.continuation_sha256,a.root,a.backup,a.prior_failed);print(sha(a.root/'request.json'))
    elif a.worker:worker(a.root,a.worker,a.request_sha256)
    else:run_stage(a.root,a.stage,a.request_sha256)

if __name__=='__main__':main()
