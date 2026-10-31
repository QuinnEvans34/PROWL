"""Request a safe-boundary pause of the additive continuation controller only.

The original launcher does not support this protocol. This command never signals
processes and never reports cleanup merely because a request was written.
"""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.teacher_target_publication_v1 import read_bound
from src.operations.kd_gpu_qualification_v1 import write


def request(root,pin):
    root=Path(root)
    receipt=read_bound(root/'ready.json',pin)
    if receipt.get('version')!='mac-kd-continuation-launch-1':
        raise ValueError('Original launcher requires a separately verified stop; cooperative pause unavailable')
    if (root/'complete.json').exists():raise ValueError('Comparison already complete')
    value=dict(action='operator_pause',receipt_sha256=pin)
    path=root/'pause-request.json'
    if path.exists():
        import json
        if json.loads(path.read_text())!=value:raise ValueError('Different pause request exists')
    else:write(path,value)
    return dict(requested=True,cleanup_verified=False,
                message='Pause requested; current update or native validation must finish before cleanup verification.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--receipt-sha256',required=True)
    a=p.parse_args();print(request(a.root,a.receipt_sha256))

if __name__=='__main__':main()
