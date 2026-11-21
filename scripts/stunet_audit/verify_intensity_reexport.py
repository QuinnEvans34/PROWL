"""Test explicit integer/clipping re-export hypotheses on one admitted CT pair.

Only complete-query exact transformed hash equality can confirm an image here.
All other residual statistics remain descriptive, not a patient identity test.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scripts.stunet_audit.confirm_cropped_images import digest, load, voxel_digest


def hypotheses(query, reference):
    q,r=np.asarray(query),np.asarray(reference)
    if q.ndim!=3 or r.ndim!=3 or max(q.size,r.size)>128_000_000:
        raise ValueError('Native bound')
    if not np.isfinite(q).all() or not np.isfinite(r).all():raise ValueError('Nonfinite')
    if any(x>y for x,y in zip(q.shape,r.shape)):raise ValueError('Contained hypothesis only')
    crop=r[tuple(slice(0,n) for n in q.shape)]
    target=voxel_digest(q);rows=[]
    for rounding in ['none','nearest','truncate','floor','ceil']:
        for clipping in [None,[-999,999],[-1000,1000]]:
            candidate=crop
            if clipping is not None:candidate=np.clip(candidate,*clipping)
            if rounding=='nearest':candidate=np.rint(candidate)
            elif rounding=='truncate':candidate=np.trunc(candidate)
            elif rounding=='floor':candidate=np.floor(candidate)
            elif rounding=='ceil':candidate=np.ceil(candidate)
            error=np.abs(q-candidate);actual=voxel_digest(candidate)
            rows.append(dict(rounding=rounding,clipping=clipping,offset_voxels=[0,0,0],
                exact_equal_fraction=float(np.mean(q==candidate)),
                mean_absolute_error=float(error.mean()),max_absolute_error=float(error.max()),
                error_quantiles=np.percentile(error,[50,90,95,99,99.9,100]).tolist(),
                within_one_fraction=float(np.mean(error<=1)),
                transformed_voxel_sha256=actual,query_voxel_sha256=target,
                exact_complete_query_identity=actual==target))
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if digest(a.request)!=a.request_sha256:raise ValueError('Request differs')
    req=json.loads(a.request.read_text())
    for name,pin in req['source_pins'].items():
        if digest(name)!=pin:raise ValueError('Source differs')
    pair=req['pair']
    if pair['query']['role']!='development' or pair['reference']['role']!='pretraining_reference':raise ValueError('Role')
    if (pair['query']['case_id'],pair['reference']['case_id'])!=('PanTS_00001389','TotalSegV1:s1014'):raise ValueError('One previously reviewed pair')
    a.output.mkdir(exist_ok=False)
    rows=hypotheses(load(pair['query']),load(pair['reference']))
    (a.output/'results.json').write_text(json.dumps(rows,indent=2))
    (a.output/'summary.json').write_text(json.dumps(dict(case_id=pair['query']['case_id'],reference_id=pair['reference']['case_id'],
       tested_hypotheses=len(rows),exact_complete_query_matches=[r for r in rows if r['exact_complete_query_identity']],
       patient_identifier_crosswalk=False,physical_geometry_qualified=False,model_forwards=0,optimizer_updates=0),indent=2))


if __name__=='__main__':main()
