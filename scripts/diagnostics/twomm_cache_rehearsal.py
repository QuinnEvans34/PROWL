"""Retain an invented two-role cache and deterministic 144-cube replay evidence."""
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import json
import time
import numpy as np
import torch
from src.data.localizer_preprocessing_v4 import preprocess
from src.data.manifest_records import canonical,digest
from src.training.twomm_cache import publish,DiskRoleCache
from src.training.twomm_adapter import patch_batch,pad_image,remove_padding


def main():
    torch.set_num_threads(2);start=time.monotonic();repo=Path(__file__).resolve().parents[2]
    recipe=json.loads((repo/'configs/capstone/localizer-preprocessing-v4.json').read_text())
    y=np.zeros((24,26,28),np.uint8);y[8:16,9:17,10:18]=1
    base=preprocess(y.astype(np.float32)*300-100,np.diag([2.,2.,2.,1.]),recipe,target=y)
    class Fixture:
        def __init__(self,role):self.role=role;self.recipe=deepcopy(recipe)
        def __len__(self):return 1
        def descriptor(self,i):return dict(study_id='invented-'+self.role,operation=self.role,protected_role='train' if self.role=='optimizer' else 'validation',observations=['synthetic only'])
        def load(self,i,*,operation):
            assert operation==self.role;x=deepcopy(base);x['provenance']={'descriptor':self.descriptor(i)};return x
    datasets={r:Fixture(r) for r in ('optimizer','evaluator')}
    binding=dict(schema_version='twomm-cache-1',review_sha256=digest(b'synthetic-review'),bundle_sha256=digest(b'synthetic-bundle'),recipe=recipe,
        roles={r:[dict(descriptor=d.descriptor(0),transform_record=base['transform_record'])] for r,d in datasets.items()})
    dest=repo/'outputs/prowl'/('twomm-cache-synthetic-'+str(uuid4()));dest.mkdir();cachepath=dest/'cache';cachepath.mkdir()
    pin=digest(canonical(binding));receipt=publish(cachepath,datasets,binding,pin);cache=DiskRoleCache(cachepath,receipt,binding,pin)
    config=dict(schema_version='twomm-adapter-1',patch_size=[144]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=4,loss_id='balanced_ce_dice_v1')
    rows=[]
    for step in range(4):
        item=cache.get('optimizer',0);a,b,t=patch_batch(item,config,step=step)
        # Reopen from retained bytes at each interruption boundary, then replay the next crop.
        fresh=DiskRoleCache(cachepath,receipt,binding,pin);aa,bb,tt=patch_batch(fresh.get('optimizer',0),config,step=step)
        assert torch.equal(a,aa) and torch.equal(b,bb) and t==tt
        padded,trace=pad_image(item['image'],config);assert torch.equal(remove_padding(padded,trace),item['image'])
        rows.append(t)
    denied=False
    try:patch_batch(cache.get('evaluator',0),config,step=0)
    except ValueError:denied=True
    assert denied
    (dest/'binding.json').write_bytes(canonical(binding))
    report=dict(state='passed',synthetic_only=True,source_reads=0,optimizer_updates=0,cache_receipt_sha256=receipt,binding_sha256=pin,
        config=config,replayed_steps=rows,validation_sampler_refused=denied,padding_roundtrip_exact=True,elapsed_seconds=time.monotonic()-start,
        files={str(p.relative_to(dest)):dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in dest.rglob('*') if p.is_file()})
    (dest/'receipt.json').write_bytes(canonical(report));print(dest);print(digest((dest/'receipt.json').read_bytes()))


if __name__=='__main__':main()
