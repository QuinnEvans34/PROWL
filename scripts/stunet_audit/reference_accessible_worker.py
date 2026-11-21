"""Accessible-reference audit with explicit unusable source members; no clearance."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scripts.stunet_audit.overlap import fingerprint_file,fingerprint,FingerprintIndex

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024**2):h.update(block)
    return h.hexdigest()

def reference_fingerprint(path, *, native_voxel_limit=128_000_000):
    """Large native arrays use proxy sampling, never an enlarged allocation cap."""
    import nibabel as nib
    path=Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size>256*1024**2:raise ValueError('Reference file bound')
    image=nib.load(path)
    if len(image.shape)!=3 or min(image.shape)<3 or np.prod(image.shape)>1_000_000_000:raise ValueError('Reference header bound')
    if np.prod(image.shape)<=native_voxel_limit:
        f=fingerprint_file(path,appearance_only_unknown_units=True)
        f['native_voxel_hash_computed']=True
        return f
    units=image.header.get_xyzt_units()[0]
    if units not in ('mm','unknown'):raise ValueError('Unsupported reference units')
    if not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3,:3]))<1e-9:raise ValueError('Invalid reference affine')
    steps=np.maximum(1,np.ceil(np.asarray(image.shape)/96).astype(int))
    # Proxy slicing decompresses the NIfTI but allocates only the selected samples.
    overview=np.asarray(image.dataobj[tuple(slice(None,None,int(s)) for s in steps)],dtype=np.float32)
    affine=image.affine@np.diag([*steps,1])
    f=fingerprint(overview,affine,file_sha256=digest(path))
    f['overview_voxel_sha256']=f.pop('normalized_voxel_sha256')
    f['normalized_voxel_sha256']=None
    f.update(native_voxel_hash_computed=False,native_shape=list(image.shape),native_affine=image.affine.tolist(),
             source_proxy_stride=steps.tolist(),geometry_scope='sampled overview only',
             all_native_voxels_checked=False,declared_spatial_units=units,
             physical_geometry_certified=False,unknown_units_appearance_only=units=='unknown',
             voxel_hash_policy='Full native voxel hash not computed; original file SHA256 plus proxy appearance only')
    return f

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if digest(a.request)!=a.request_sha256:raise ValueError('Request differs')
    request=json.loads(a.request.read_text())
    for name,pin in request['source_pins'].items():
        if digest(name)!=pin:raise ValueError('Frozen source differs: '+name)
    rows=request['references'];queries=request['queries'];blocked=request['blocked_references']
    if len(rows)+len(blocked)!=1204 or len(queries)!=75:raise ValueError('Original reference/development scope')
    if any(r['role']!='pretraining_reference' for r in rows) or any(q['role']!='development' for q in queries):raise ValueError('Protected role')
    if len({r['case_id'] for r in rows})!=len(rows) or len({q['case_id'] for q in queries})!=len(queries):raise ValueError('Duplicate identities')
    a.output.mkdir(exist_ok=False);start=time.monotonic();refs=[];failures=[]
    for r in rows:
        if time.monotonic()-start>3500:raise RuntimeError('Reference time bound')
        try:
            f=reference_fingerprint(r['path'])
            if f['file_sha256']!=r['sha256']:raise RuntimeError('Reference source bytes changed')
            vectors=np.asarray(f.pop('vectors'),dtype=np.float32)
            descriptors=np.asarray(f.pop('descriptors'),dtype=np.float32)
            identifier=hashlib.sha256(r['case_id'].encode()).hexdigest()
            np.savez_compressed(a.output/(identifier+'.npz'),vectors=vectors,descriptors=descriptors)
            (a.output/(identifier+'.json')).write_text(json.dumps(f))
            f.update(vectors=vectors,descriptors=descriptors)
            refs.append(dict(case_id=r['case_id'],fingerprint=f))
        except ValueError as error:
            failures.append(dict(case_id=r['case_id'],error=str(error)))
        with (a.output/'progress.jsonl').open('a') as log:
            log.write(json.dumps(dict(completed=len(refs)+len(failures),case_id=r['case_id'],seconds=time.monotonic()-start))+'\n')
        gc.collect()
    index=FingerprintIndex(refs);results=[]
    for q in queries:
        if digest(q['fingerprint_path'])!=q['fingerprint_sha256']:raise RuntimeError('Query fingerprint changed')
        f=json.loads(Path(q['fingerprint_path']).read_text())
        if f['file_sha256']!=q['sha256']:raise RuntimeError('Query source binding differs')
        native_hash=f.get('normalized_voxel_sha256')
        if not isinstance(native_hash,str) or len(native_hash)!=64:raise RuntimeError('Query requires a complete native voxel hash')
        # File equality covers every extracted reference, including allocation-refused ones.
        exact=[r['case_id'] for r in rows if r['sha256']==q['sha256']]
        results.append(dict(case_id=q['case_id'],exact_file_matches_all_references=exact,blocked_reference_ids=[r['case_id'] for r in blocked],
                            candidates=index.rank(f),classification='UNRESOLVED',clearance_issued=False))
    (a.output/'candidates.json').write_text(json.dumps(results,indent=2))
    result=dict(reference_count=len(rows)+len(blocked),verified_reference_file_hashes=len(rows),blocked_references=blocked,references_fingerprinted=len(refs),reference_failures=failures,
                full_native_voxel_hashes=sum(r['fingerprint']['native_voxel_hash_computed'] for r in refs),
                proxy_only_references=sum(not r['fingerprint']['native_voxel_hash_computed'] for r in refs),
                query_count=len(results),seconds=time.monotonic()-start,clearance_issued=False)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
