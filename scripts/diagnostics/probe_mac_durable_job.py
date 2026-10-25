"""Synthetic process-lifetime probe; no data/model/GPU access."""
import json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
if __name__=='__main__':
    out=Path(sys.argv[1])
    if '--worker' in sys.argv:
        for n in range(20):
            with (out/'ticks.jsonl').open('a') as f:f.write(json.dumps(dict(tick=n,pid=os.getpid(),parent=os.getppid()))+'\n')
            time.sleep(1)
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        (out/'ownership.json').write_text(json.dumps(dict(pid=os.getpid(),parent=os.getppid())))
        if not run([sys.executable,__file__,str(out),'--worker'],out,seconds=45,rss_bytes=256*1024**2,env=os.environ.copy()):raise SystemExit(1)
