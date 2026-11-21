"""Exact whole-query crop identity, independent of millimetre/clinical geometry claims."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import nibabel as nib

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024**2):h.update(block)
    return h.hexdigest()

def voxel_digest(array):
    a=np.asarray(array,dtype='<f4',order='C')
    h=hashlib.sha256(str(a.shape).encode());h.update(a.tobytes());return h.hexdigest()

def exact_crop(query,reference,*,suggested_offsets=()):
    q=np.asarray(query,dtype=np.float32);r=np.asarray(reference,dtype=np.float32)
    if q.ndim!=3 or r.ndim!=3 or q.size<100000 or q.size>128000000 or r.size>128000000:raise ValueError('Crop allocation/evidence bound')
    if not np.isfinite(q).all() or not np.isfinite(r).all():raise ValueError('Nonfinite crop input')
    difference=np.asarray(r.shape)-q.shape
    if (difference<0).any():return dict(status='SHAPE_NOT_CONTAINED')
    expected=voxel_digest(q);tested=set()
    def check(offset):
        offset=tuple(map(int,offset))
        if offset in tested or any(s<0 or s>n for s,n in zip(offset,difference)):return None
        tested.add(offset)
        crop=r[tuple(slice(s,s+n) for s,n in zip(offset,q.shape))]
        if voxel_digest(crop)==expected:
            return dict(status='EXACT_CROPPED_IMAGE_IDENTITY',offset_voxels=list(offset),
                        query_shape=list(q.shape),matching_query_voxels=int(q.size),
                        query_voxel_sha256=expected,reference_crop_voxel_sha256=expected,
                        geometry_qualified=False,patient_identity_mapped=False)
        return None
    for offset in suggested_offsets:
        found=check(offset)
        if found:return found
    rng=np.random.default_rng(14242);anchors=[]
    for c in rng.integers(0,np.asarray(q.shape),size=(256,3)):
        value=float(q[tuple(c)])
        if -500<value<2000 and value not in (0.,-200.,255.,1024.):anchors.append((c,value))
        if len(anchors)==16:break
    offsets=None
    for coordinate,value in anchors:
        if offsets is None:
            mask=r==value;count=int(np.count_nonzero(mask))
            if count==0:return dict(status='NO_EXACT_CROP',tested_offsets=len(tested),not_independence_clearance=True)
            if count>20000:continue
            offsets=np.argwhere(mask)-coordinate
            offsets=offsets[((offsets>=0)&(offsets<=difference)).all(axis=1)]
        else:
            locations=offsets+coordinate
            offsets=offsets[r[tuple(locations.T)]==value]
        if len(offsets)==0:return dict(status='NO_EXACT_CROP',tested_offsets=len(tested),not_independence_clearance=True)
        if len(offsets)<=64:
            for offset in offsets:
                found=check(offset)
                if found:return found
            return dict(status='NO_EXACT_CROP',tested_offsets=len(tested),not_independence_clearance=True)
    return dict(status='INSUFFICIENT_DISTINCTIVE_ANCHORS',not_independence_clearance=True)

def load(row):
    path=Path(row['path'])
    if digest(path)!=row['sha256']:raise ValueError('Source bytes differ')
    n=nib.load(path)
    if len(n.shape)!=3 or np.prod(n.shape)>128000000:raise ValueError('Native allocation bound')
    # Exactly the fingerprint producer's orientation and scaled-float32 convention.
    a=n.get_fdata(dtype=np.float32)
    canonical=nib.as_closest_canonical(nib.Nifti1Image(a,n.affine)).get_fdata(dtype=np.float32)
    if voxel_digest(canonical)!=row['normalized_voxel_sha256']:raise ValueError('Canonical source identity differs')
    return canonical

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if digest(a.request)!=a.request_sha256:raise ValueError('Request differs')
    req=json.loads(a.request.read_text())
    if len(req['pairs'])>225:raise ValueError('Pair bound')
    for name,pin in req['source_pins'].items():
        if digest(name)!=pin:raise ValueError('Code changed')
    a.output.mkdir(exist_ok=False);start=time.monotonic();results=[];last_case=None;query=None
    for pair in req['pairs']:
        if time.monotonic()-start>550:raise RuntimeError('Crop confirmation time bound')
        q=pair['query'];r=pair['reference']
        if q['role']!='development' or r['role']!='pretraining_reference':raise ValueError('Protected role')
        if q['case_id']!=last_case:
            query=load(q);last_case=q['case_id'];gc.collect()
        reference=load(r)
        proof=exact_crop(query,reference,suggested_offsets=pair.get('suggested_offsets',[]))
        proof.update(case_id=q['case_id'],reference_id=r['case_id'],query_file_sha256=q['sha256'],reference_file_sha256=r['sha256'])
        results.append(proof);del reference;gc.collect()
        with (a.output/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(completed=len(results),case_id=q['case_id'],reference_id=r['case_id'],status=proof['status'],seconds=time.monotonic()-start))+'\n')
    (a.output/'results.json').write_text(json.dumps(results,indent=2))
    summary=dict(pairs=len(results),confirmed_pairs=sum(r['status']=='EXACT_CROPPED_IMAGE_IDENTITY' for r in results),
                 seconds=time.monotonic()-start,physical_units_assigned=False,patient_independence_verified=False)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))

if __name__=='__main__':main()
