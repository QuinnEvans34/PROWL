#!/usr/bin/env python3
"""One bounded invented native profile of the full session and large affine geometry."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def worker(output):
    import gc
    import time
    import numpy as np
    import torch
    from src.data import segmenter_geometry_v2 as g
    from src.data import segmenter_training_inputs_v1 as boundary
    from src.data.manifest_records import canonical,digest
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    torch.set_num_threads(2)
    control=dict(train=[f'invented-{i}' for i in range(9)],validation=['invented-development'])
    config=dict(max_steps=24000,tensor_shape=[144]*3,seed=42,learning_rate=.0001,
        weight_decay=.00001,warmup_steps=500,lr_schedule='warmup_cosine')
    session=Session(config,control,device='mps',initialization={'kind':'scratch'})
    # Largest observed header shape. Every source element is allocated/touched; no patient data.
    shape=(510,431,918);started=time.monotonic()
    ct=np.full(shape,30,np.float32);p=np.empty(shape,np.uint8);p.fill(0);l=np.empty(shape,np.uint8);l.fill(0)
    p[200:300,170:250,390:490]=1;l[245:255,205:215,435:445]=1
    angle=.04;c,s=np.cos(angle),np.sin(angle)
    affine=np.array([[c,-s,0,20],[s,c,0,-30],[0,0,1.5,80],[0,0,0,1.]])
    result=g.preprocess(ct,p,l,affine,g.recipe(),source_identity=dict(study_id='invented-largest-shape',ct_sha256='a'*64),lesion_target_state='positive')
    del ct,p,l;gc.collect()
    class Provider:
        def __init__(self):self.control=control
        def get(self,name,*,role,operation):
            return boundary.Batch(boundary._TOKEN,study_id=name,role=role,operation=operation,
                image=result['image'][None],target=result['target'],control_sha256=digest(canonical(control)))
    provider=Provider();rows=[session.update(provider),session.update(provider)]
    evaluation=session.evaluate_case(provider,'invented-development')
    output.mkdir(parents=True,exist_ok=False)
    atomic_checkpoint(output/'invented.pt',session,best_score=None,history_bytes=0)
    identity=session.identity;del session;gc.collect();torch.mps.empty_cache()
    state=torch.load(output/'invented.pt',map_location='cpu',weights_only=True)
    restored=Session.restore(state['session'],identity)
    recovered=restored.evaluate_case(provider,'invented-development')
    if recovered!=evaluation:raise ValueError('Restored native evaluation differs')
    report=dict(domain='invented_arrays_only',source_shape=list(shape),geometry=g.recipe(),
        optimizer_updates=2,forwards=4,real_payloads=0,seconds=time.monotonic()-started,
        native_checkpoint_evaluation_exact=True,optimizer_resume_qualified=False,updates=rows,
        fidelity=result['fidelity'])
    (output/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    p.add_argument('--worker',action='store_true');args=p.parse_args();output=Path(args.output).resolve()
    if args.worker:return worker(output)
    from src.operations.segmenter_duration_dispatch_v1 import watch
    if output.exists():raise FileExistsError(output)
    if 'AC Power' not in subprocess.check_output(['pmset','-g','batt'],text=True):raise ValueError('AC required')
    lock=ROOT/'outputs/prowl/.mps-profile.lock'
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--output',str(output),'--worker'],
            env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0'),start_new_session=True,cwd=ROOT)
        resources=watch(process,seconds=600,rss_bytes=12*1024**3)
        (output/'resources.json').write_text(json.dumps(resources,indent=2)+'\n')
        print(json.dumps(resources),flush=True)


if __name__=='__main__':main()
