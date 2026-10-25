"""Disposable supervised pause probe; no CT/model/GPU use."""
import os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.mac_pilot_supervision_v1 import run

if __name__ == '__main__':
    output=Path(sys.argv[1])
    if '--worker' in sys.argv:
        for _ in range(120):
            with (output/'ticks.txt').open('a') as stream:stream.write('tick\n')
            time.sleep(1)
    elif not run([sys.executable,__file__,str(output),'--worker'],output,
                 seconds=180,rss_bytes=256*1024**2,env=os.environ.copy()):
        raise SystemExit(1)
