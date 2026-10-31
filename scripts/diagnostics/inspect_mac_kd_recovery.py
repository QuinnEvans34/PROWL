"""Read-only checkpoint/pause readiness audit. Never signals or launches a job."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.teacher_target_publication_v1 import read_bound
from src.operations.kd_continuation_v1 import inspect_checkpoint, remaining_budget
from src.operations.kd_gpu_qualification_v1 import check_pins, write


def audit(root,pin,arm,filename):
    root=Path(root).resolve(strict=True)
    r=read_bound(root/'ready.json',pin)
    if r['version']!='mac-matched-kd-launch-1' or arm not in r['order']:
        raise ValueError('Frozen matched comparison required')
    check_pins(r['pins'])
    dispatch=json.loads((root/arm/'dispatch.json').read_text())
    if dispatch['receipt_sha256']!=pin:raise ValueError('Arm dispatch differs')
    context=inspect_checkpoint(root/arm/'execution',Path(r['backup'])/arm,filename)
    raw=(root/arm/'execution/history.jsonl').read_bytes()
    # Only complete records are needed for the live, read-only progress estimate.
    raw=raw[:raw.rfind(b'\n')+1]
    updates=[v for v in map(json.loads,raw.splitlines()) if v['event']=='update']
    latest=updates[-1]['step'] if updates else 0
    resources=root/arm/'resources.json'
    budget=None
    if resources.exists():budget=remaining_budget(r['limits']['seconds_per_arm'],[json.loads(resources.read_text())])
    return dict(version='mac-kd-recovery-audit-1',comparison_sha256=pin,arm=arm,
        checkpoint=context,observed_updates=latest,updates_after_checkpoint=latest-context['step'],
        budget=budget,scientific_ready=False,
        note='Read-only audit. Live run unchanged. Continuation launch and GPU qualification still required.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--receipt-sha256',required=True)
    p.add_argument('--arm',choices=('control','treatment'),required=True)
    p.add_argument('--checkpoint',default='last.pt');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.root,a.receipt_sha256,a.arm,a.checkpoint)
    a.output.mkdir(parents=True,exist_ok=False);write(a.output/'audit.json',result)
    print(json.dumps(dict(recoverable_step=result['checkpoint']['step'],observed_updates=result['observed_updates'],
                         updates_after_checkpoint=result['updates_after_checkpoint'],scientific_ready=False)))

if __name__=='__main__':main()
