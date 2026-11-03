"""Trace two existing forwards without changing input/output, RNG or operation order."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch


class TraceForward(torch.nn.Module):
    def __init__(self, model, output, selected):
        super().__init__()
        self.model=model
        self.output=Path(output)
        self.selected={int(k):list(v) for k,v in selected.items()}
        if len(self.selected)!=2 or any(k<0 for k in self.selected):
            raise ValueError('Exactly two distinct preselected call indices required')
        self.calls=0
        self.records=[]

    def forward(self, value):
        index=self.calls;self.calls+=1
        result=self.model(value)
        if index in self.selected:
            if value.dtype!=torch.float32 or result.dtype!=torch.float32:
                raise ValueError('Only float32 diagnostic traces supported')
            arrays={'input':value.detach().cpu().numpy(),'logits':result.detach().cpu().numpy()}
            if sum(a.nbytes for a in arrays.values())>64*1024**2:
                raise ValueError('Per-window trace cap')
            row=dict(index=index,expected_origin=self.selected[index],artifacts={})
            for name,array in arrays.items():
                path=self.output/f'trace-{index:03d}-{name}.npy'
                with path.open('xb') as f:np.save(f,array,allow_pickle=False)
                if not np.array_equal(np.load(path,allow_pickle=False),array):
                    raise ValueError('Trace roundtrip changed tensor values')
                row['artifacts'][name]=dict(path=path.name,bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),shape=list(array.shape),dtype=str(array.dtype))
            self.records.append(row)
        return result

    def finish(self,actual_origins):
        if self.calls!=len(actual_origins) or len(self.records)!=2:
            raise ValueError('Trace forward accounting mismatch')
        if any(list(actual_origins[k])!=v for k,v in self.selected.items()):
            raise ValueError('Actual trace origins differ from preselected grid')
        path=self.output/'trace.json'
        with path.open('x') as f:json.dump(dict(forward_calls=self.calls,extra_forwards=0,records=self.records),f,indent=2)
