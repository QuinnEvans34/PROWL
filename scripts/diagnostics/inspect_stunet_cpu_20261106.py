"""Portable bounded-worker payload, synthetic CPU only; never launches science.

Invoke under a host resource supervisor. Output is exclusive; failed attempts
must be preserved, not overwritten. Optional --checkpoint adds strict original
pretrained load; omitting it explicitly audits random architecture only.
"""
import argparse
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.training.stunet_transfer_20261106 import make_model,load_transfer,sha256


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--checkpoint')
    args=p.parse_args()
    destination=Path(args.output)
    with destination.open('x') as handle:
        start=time.monotonic()
        try:
            import torch
            torch.set_num_threads(2)
            pools=[[2,2,2]]*4+[[1,1,2]]
            if args.checkpoint:
                model,proof=load_transfer(args.source,args.checkpoint,pools=pools)
            else:
                model=make_model(args.source,pools=pools)
                proof={'qualification':'RANDOM_ARCHITECTURE_ONLY','pretrained_loaded':False}
            model.eval()
            with torch.no_grad():
                result=model(torch.zeros(1,1,32,32,32))
            if len(result)!=5 or any(not torch.isfinite(x).all() for x in result):
                raise ValueError('Synthetic forward invalid')
            report=dict(status='PASS',proof=proof,parameters=sum(x.numel() for x in model.parameters()),
                        output_shapes=[list(x.shape) for x in result],pools=pools,
                        input_shape=[1,1,32,32,32],source_sha256=sha256(args.source),
                        seconds=time.monotonic()-start,actual_training_qualification=False,
                        clinical_input_reads=0,optimizer_updates=0,gpu=False)
        except BaseException as exc:
            json.dump(dict(status='FAILED',error=repr(exc),seconds=time.monotonic()-start),handle)
            handle.flush()
            raise
        json.dump(report,handle,indent=2);handle.flush()
        print(json.dumps(report),flush=True)


if __name__=='__main__':main()
