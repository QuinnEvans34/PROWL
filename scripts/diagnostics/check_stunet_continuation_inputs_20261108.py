"""Bounded CPU-only actual loader checks; no model or optimizer."""
import argparse,json,os,sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.training.train_stunet_transfer_20261106 import write,backup
from src.data.stunet_inputs_20261106 import sha


def worker(r):
    import numpy as np
    from src.data.stunet_continuation_inputs_20261108 import Inputs
    from src.data.stunet_errata_20261108 import EXPECTED
    p=Inputs(r['inputs']);observations=[]
    for name,source in p.sources.items():
        for kind in ('ct',) if name in p.train else ('ct','pancreas','lesion'):p.check_file(name,kind)
    for name in r['cases']:
        index=next(i for i,x in enumerate(p.plan['schedule']) if x['case_id']==name and x['kind']=='coverage')
        x,y,trace=p.training(12000+index)
        if x.shape!=(1,128,128,128) or y.shape!=(128,128,128) or not np.isfinite(x).all() or not np.isin(y,[0,1,2]).all():raise ValueError('Actual window invalid')
        if trace['step']!=12000+index or (name in EXPECTED and (y==2).any()):raise ValueError('Actual correction/address')
        observations.append(dict(case_id=name,trace=trace,labels=np.unique(y).tolist(),shape=list(x.shape)))
        print(name,flush=True)
    if not set(EXPECTED).issubset(r['cases']):raise ValueError('Missing seven')
    write(r['result'],dict(status='PASS',cases=observations,source_stats_checked=len(p.sources),train=len(p.train),dev=len(p.dev),scientific_updates=0))


def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
    if sha(a.request)!=a.sha256:raise ValueError('Request hash')
    r=json.loads(Path(a.request).read_text())
    for path,h in r['pins'].items():
        if sha(path)!=h:raise ValueError('Pin mismatch: '+path)
    if a.worker:return worker(r)
    from src.operations.full_training_platform import require_ac,watch_windows
    from src.operations.stunet_continuation_storage_20261108 import check_storage
    require_ac();check_storage();out=Path(r['stage']);out.mkdir(exist_ok=False)
    with (out/'worker.log').open('x') as f:
        child=subprocess.Popen([sys.executable,__file__,'--request',a.request,'--sha256',a.sha256,'--worker'],stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        write(out/'owner.json',dict(supervisor=os.getpid(),worker=child.pid))
        try:
            last=[0.]
            def tick():
                import psutil
                require_ac()
                if time.monotonic()-last[0]>60:check_storage();last[0]=time.monotonic()
                rss=psutil.Process().memory_info().rss
                try:owned=[psutil.Process(child.pid)]+psutil.Process(child.pid).children(recursive=True)
                except psutil.NoSuchProcess:owned=[]
                for proc in owned:
                    try:rss+=proc.memory_info().rss
                    except psutil.NoSuchProcess:pass
                if rss>4*1024**3:raise RuntimeError('Combined CPU RSS')
            result=watch_windows(child,seconds=600,rss_bytes=4*1024**3,tick=tick)
            evidence=backup(r['result'],r['backup'])
            write(out/'resources.json',dict(result,success=True,backup=evidence))
        except BaseException as e:
            write(out/'failure.json',dict(error=repr(e),resources=getattr(child,'duration_resources',{})));raise


if __name__=='__main__':main()
