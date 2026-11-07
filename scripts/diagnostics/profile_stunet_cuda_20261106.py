"""Nonpromotable synthetic actual-pretrained128 CUDA resource payload.

Host must enforce wall/RSS, exclusive GPU ownership and clean process reaping.
One attempt per output directory. No CT reads, scientific MLflow or successor.
"""
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.stunet_transfer_20261106 import load_transfer,deep_supervision_loss


def enable_checkpoints(model):
    from torch.utils.checkpoint import checkpoint
    for group in (model.conv_blocks_context,model.upsample_layers,model.conv_blocks_localization):
        for stage in group:
            original=stage.forward
            def wrapped(*args,_forward=original):
                return checkpoint(_forward,*args,use_reentrant=False,preserve_rng_state=True)
            stage.forward=wrapped


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--checkpoint',required=True)
    p.add_argument('--output',required=True);p.add_argument('--activation-checkpointing',action='store_true');a=p.parse_args()
    out=Path(a.output);out.mkdir(exist_ok=False);started=time.monotonic();stage='import';report={}
    try:
        import torch
        torch.set_num_threads(2);torch.manual_seed(42)
        cap=6*1024**3
        total=torch.cuda.get_device_properties(0).total_memory
        torch.cuda.set_per_process_memory_fraction(cap/total,0)
        torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        stage='strict_cpu_load'
        model,proof=load_transfer(a.source,a.checkpoint,pools=[[2,2,2]]*4+[[1,1,2]])
        if a.activation_checkpointing:enable_checkpoints(model)
        stage='to_cuda';model.to('cuda').train()
        optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=1e-5,foreach=False)
        x=torch.randn(1,1,128,128,128,device='cuda');target=torch.zeros(1,128,128,128,dtype=torch.long,device='cuda')
        target[:,32:96,32:96,32:96]=1;target[:,60:68,60:68,60:68]=2
        losses=[];timings=[]
        for step in range(3):
            torch.cuda.synchronize();before=time.monotonic();optimizer.zero_grad(set_to_none=True)
            stage='forward';outputs=model(x)
            stage='loss';loss=deep_supervision_loss(outputs,target)
            stage='backward';loss.backward()
            stage='gradient_check'
            if any(p.grad is None or not torch.isfinite(p.grad).all() for p in model.parameters()):raise ValueError('Missing/nonfinite gradients')
            stage='optimizer';optimizer.step();torch.cuda.synchronize()
            timings.append(time.monotonic()-before);losses.append(float(loss.detach()))
            allocated=torch.cuda.max_memory_allocated();reserved=torch.cuda.max_memory_reserved()
            if max(allocated,reserved)>cap:raise RuntimeError('6GiB cap')
            with (out/'progress.jsonl').open('a') as f:
                f.write(json.dumps(dict(step=step+1,loss=losses[-1],seconds=timings[-1],allocated=allocated,reserved=reserved))+'\n');f.flush();os.fsync(f.fileno())
            del outputs,loss
        report=dict(status='PASS',proof=proof,synthetic_updates=3,losses=losses,step_seconds=timings,
                    activation_checkpointing=a.activation_checkpointing,input=[1,1,128,128,128],dtype='float32',
                    allocated_peak=torch.cuda.max_memory_allocated(),reserved_peak=torch.cuda.max_memory_reserved(),
                    seconds=time.monotonic()-started,scientific_updates=0,real_input_qualified=False)
    except BaseException as e:
        report=dict(status='FAILED',stage=stage,error=repr(e),seconds=time.monotonic()-started,scientific_updates=0,
                    activation_checkpointing=a.activation_checkpointing)
        try:report.update(allocated_peak=torch.cuda.max_memory_allocated(),reserved_peak=torch.cuda.max_memory_reserved())
        except Exception:pass
        raise
    finally:
        with (out/'result.json').open('x') as f:json.dump(report,f,indent=2)


if __name__=='__main__':main()
