"""Explicit continuation after verified metadata rounding failure; no automatic retries."""
import argparse,json,math,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import build_rsuper_header_checked_v1 as worker
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.operations.mac_teacher_continuation_v1 import completed_members


def remaining(request, resources, log):
    if not (resources.get('workers_reaped') is True and resources.get('success') is False
            and resources.get('exit_code')==1 and resources.get('error')=="ValueError('Duration worker failed')"
            and "expected=metadata_grid(meta['parent_geometry'])" in log and log.rstrip().endswith('AssertionError')):
        raise ValueError('Expected reaped geometry failure required')
    elapsed=resources['seconds']
    if not math.isfinite(elapsed) or elapsed<0:raise ValueError('Invalid elapsed')
    result=request['limits']['seconds']-math.ceil(elapsed)
    if result<=0:raise ValueError('Budget exhausted')
    return result


def main():
    a=argparse.ArgumentParser();a.add_argument('--previous',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--audit',type=Path,required=True);a.add_argument('--worker',action='store_true');v=a.parse_args()
    previous=v.previous.resolve(strict=True);out=v.output.resolve();audit=v.audit.resolve(strict=True)
    if previous.parent!=BASE or out.parent!=BASE or previous==out:raise ValueError('Distinct artifact directories required')
    if v.worker:
        req=json.loads((out/'request.json').read_text());worker.OLD=previous;worker.OUT=out;worker.LIMITS=req['limits'];worker.worker();return
    from src.operations.full_training_platform import training_guard,require_ac
    from src.operations.mac_teacher_supervision_v2 import run
    require_ac();storage_preflight()
    req=json.loads((previous/'request.json').read_text());res=json.loads((previous/'resources.json').read_text())
    seconds=remaining(req,res,(previous/'worker.log').read_text())
    report=json.loads((audit/'result.json').read_text())
    if not report['success'] or report['total']!=len(req['train']):raise ValueError('Complete header audit required')
    rows=[json.loads(s) for s in (audit/'cases.jsonl').read_text().splitlines()]
    if [r['case_id'] for r in rows]!=req['train'] or not all(r['passed'] for r in rows):raise ValueError('Audit cohort differs')
    for p,h in {**req['pins'],**report['pins']}.items():
        if sha(Path(p))!=h:raise ValueError('Producing pin changed: '+p)
    members=completed_members(previous,req)
    req['reused_completed']=members;req['limits']=dict(req['limits'],seconds=seconds)
    req['continuation']=dict(previous_request_sha256=sha(previous/'request.json'),previous_resources_sha256=sha(previous/'resources.json'),previous_completed=len(members),prior_stage_seconds_charged=math.ceil(res['seconds']),original_wall_budget_seconds=96*3600,no_automatic_retry=True,header_audit_sha256=sha(audit/'result.json'),change='header-based geometry validation only; preprocessing and predictions unchanged')
    proof=BASE/'teacher-header-real-check-20261028-01.json'
    proof_result=json.loads(proof.read_text())
    if proof_result.get('success') is not True or proof_result.get('case_id')!='PanTS_00002331' or proof_result['max_affine_difference']>1e-4:raise ValueError('Real preprocessing qualification required')
    files=[proof,ROOT/'scripts/diagnostics/review_mac_teacher_failure.py',Path(__file__),Path(worker.__file__),ROOT/'src/data/teacher_header_geometry_v1.py',ROOT/'tests/test_teacher_header_geometry_v1.py',ROOT/'tests/test_resume_rsuper_header_checked_v1.py',audit/'result.json',audit/'cases.jsonl',previous/'request.json',previous/'resources.json',previous/'worker.log']
    files += [previous/(n+s) for n in members for s in ('.json','.npz')]
    req['pins'].update(report['pins']);req['pins'].update({str(p.resolve()):sha(p) for p in files})
    if sum(p.stat().st_size for p in BASE.rglob('*.npz'))+req['limits']['output_bytes']>32*1024**3:raise ValueError('Combined cache limit')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        out.mkdir(exist_ok=False);write(out/'request.json',req)
        def tick():
            if sum(p.stat().st_size for p in out.iterdir() if p.is_file())>req['limits']['output_bytes']:raise ValueError('Output budget')
        cmd=['caffeinate','-i',sys.executable,__file__,'--worker','--previous',str(previous),'--output',str(out),'--audit',str(audit)]
        if not run(cmd,out,seconds=seconds,rss_bytes=req['limits']['rss_bytes'],tick=tick,env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='2')):raise SystemExit(1)
if __name__=='__main__':main()
