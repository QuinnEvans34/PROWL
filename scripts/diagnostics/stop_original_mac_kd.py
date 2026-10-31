"""Explicit original-launcher stop with ownership checks; no automatic restart.

Without --stop this verifies ownership and recovery evidence only. --verify
checks cleanup after a separately recorded stop. Never force-kills a worker.
"""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.inspect_mac_kd_recovery import audit
from scripts.resume_mac_kd_comparison import stopped
from src.operations.kd_gpu_qualification_v1 import write
from src.data.segmenter_teacher_cache_v1 import sha


def owner(root,pin,arm,checkpoint):
    checked=audit(root,pin,arm,checkpoint)
    job=json.loads((root/'dispatch.json').read_text());proc=json.loads((root/arm/'process.json').read_text())
    if (root/arm/'resources.json').exists():raise ValueError('Already stopped; use verification')
    if not re.fullmatch(r'gui/'+str(os.getuid())+r'/com\.prowl\.mac-kd-comparison-[a-z0-9.-]+',job['target']):
        raise ValueError('Unexpected registered owner')
    description=subprocess.check_output(['launchctl','print',job['target']],text=True)
    match=re.search(r'^\s*pid = (\d+)\s*$',description,re.M)
    if not match or int(match[1])!=proc['supervisor']:raise ValueError('Supervisor ownership differs')
    born=subprocess.check_output(['ps','-p',str(proc['worker']),'-o','lstart='],text=True).strip()
    parent=subprocess.check_output(['ps','-p',str(proc['worker']),'-o','ppid='],text=True).strip()
    if born!=proc['worker_start'] or int(parent)!=proc['supervisor']:raise ValueError('Worker ownership differs')
    return dict(target=job['target'],process=proc,audit=checked)


def stop(root,pin,arm,checkpoint,output):
    verified=owner(root,pin,arm,checkpoint)
    output.mkdir(exist_ok=False)
    write(output/'request.json',dict(root=str(root.resolve()),receipt_sha256=pin,arm=arm,checkpoint=checkpoint,
          ownership=verified,action='explicit_operator_stop',automatic_resume=False))
    # Recheck immediately before the only signal; no PID-only kill or fallback.
    current=owner(root,pin,arm,checkpoint)
    if current['target']!=verified['target'] or current['process']!=verified['process']:raise ValueError('Owner changed before stop')
    subprocess.run(['launchctl','kill','SIGTERM',verified['target']],check=True)
    return dict(requested=True,cleanup_verified=False)


def verify(output):
    from src.operations.full_training_platform import training_guard
    request=json.loads((output/'request.json').read_text());root=Path(request['root'])
    stopped(root)
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        checked=audit(root,request['receipt_sha256'],request['arm'],request['checkpoint'])
        if checked['budget'] is None:raise ValueError('Measured reaped resources required')
        write(output/'receipt.json',dict(stopped=True,cleanup_verified=True,gpu_released=True,
              request_sha256=sha(output/'request.json'),audit=checked,automatic_resume=False))
    return dict(stopped=True,recoverable_step=checked['checkpoint']['step'],budget=checked['budget'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path);p.add_argument('--receipt-sha256')
    p.add_argument('--arm',choices=('control','treatment'),default='control');p.add_argument('--checkpoint',default='last.pt')
    p.add_argument('--output',type=Path);g=p.add_mutually_exclusive_group();g.add_argument('--stop',action='store_true');g.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.verify:result=verify(a.output)
    elif a.stop:result=stop(a.root,a.receipt_sha256,a.arm,a.checkpoint,a.output)
    else:result=owner(a.root,a.receipt_sha256,a.arm,a.checkpoint)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
