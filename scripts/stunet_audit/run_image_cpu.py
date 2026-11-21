"""Fixed audit-only process bounds; existing independent guardian owns cleanup."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from src.operations.mac_pilot_supervision_v1 import run

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=int,required=True);p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args()
    if not 1<=a.seconds<=3600 or not a.command:raise ValueError('Bound required')
    a.output.mkdir(exist_ok=False)
    last=[0.]
    def tick():
        if time.monotonic()-last[0]<5:return
        last[0]=time.monotonic()
        if shutil.disk_usage('/Volumes/PROWL-Data').free<100*1024**3:raise RuntimeError('External free-space floor')
        power=subprocess.check_output(['pmset','-g','batt'],text=True,timeout=5)
        if 'AC Power' not in power:raise RuntimeError('AC disconnected')
    tick()
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    ok=run(a.command,a.output,seconds=a.seconds,rss_bytes=8*1024**3,tick=tick,env=env)
    sys.exit(0 if ok else 1)
