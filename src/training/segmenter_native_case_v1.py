"""Native development scoring shared by the EMA horizon job; no test-role access."""
import json
from pathlib import Path
import nibabel as nib
import numpy as np
import torch
from src.data.source_inventory_records import require
from src.data.segmenter_geometry_v2 import restore_codes
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_full_inputs_v1 import Inputs
from src.training.experiment_config import sha256
from src.training.pants_native_evaluation import native_metrics


def native_case(session,provider,name):
    _,x,_=session._batch(provider,name,'validation','evaluator')
    meta=json.loads((provider.root/(name+'.json')).read_text());affine=np.asarray(meta['transform']['source_affine'])
    with torch.no_grad(),session.rng_scope():
        session.model.eval();logits=session.model(x[None].to(session.device))
        require(torch.isfinite(logits).all().item(),'Nonfinite native prediction')
        codes=logits.argmax(1)[0].cpu().numpy().astype(np.uint8)
    restored=restore_codes(codes,meta['transform'],trusted_record_sha256=meta['transform_sha256'])
    labels={}
    for kind in ('pancreas','lesion'):
        path=Path(provider.rows[name][kind+'_path']);require(sha256(path)==meta['source_sha256'][kind],'Native label changed')
        obj=nib.load(path);require(obj.shape==restored.shape and np.allclose(obj.affine,affine,atol=1e-5,rtol=0),'Native geometry mismatch')
        proxy=obj.dataobj;labels[kind],_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
        require(Inputs.observe(path)==provider.source['observations'][name][kind],'Native label changed during read')
    return dict(case_id=name,step=session.step,metrics=native_metrics(restored,labels['pancreas'],labels['lesion'],affine),scope='native_development_provided_pancreas')
