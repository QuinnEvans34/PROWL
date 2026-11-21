"""Bounded duplicate-candidate retrieval, not a proof of patient independence.

Only synthetic fixtures have qualified this implementation. Different phases,
severe crops, nonlinear reconstructions and disjoint FOVs can evade detection.
"""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, zoom
from scipy.spatial import cKDTree

GRID = 12
MAX_VOXELS = 128_000_000


def unit(x):
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    x = x - x.mean()
    length = np.linalg.norm(x)
    if length < 1e-6:
        raise ValueError("Uninformative constant fingerprint")
    return x / length


def patches(array):
    lo, hi = np.percentile(array, [0.5, 99.5])
    if hi-lo < 1e-5:
        raise ValueError("Insufficient intensity support")
    mask = array > lo + .05*(hi-lo)
    coordinates = np.where(mask)
    bounds = [slice(int(c.min()),int(c.max())+1) for c in coordinates]
    body = array[tuple(bounds)]
    features = []
    for fraction in (1., .75, .5):
        size = np.maximum(3, np.ceil(np.asarray(body.shape)*fraction).astype(int))
        starts = [(0.,0.,0.)] if fraction == 1 else [*itertools.product((0.,1.),repeat=3),(.5,.5,.5)]
        for position in starts:
            start = np.floor((np.asarray(body.shape)-size)*position).astype(int)
            block = body[tuple(slice(int(s),int(s+n)) for s,n in zip(start,size))]
            block = np.clip(block, lo, hi)
            block = gaussian_filter(block, sigma=.5)
            sampled = zoom(block, np.asarray([GRID]*3)/block.shape, order=1, prefilter=False)
            try:
                features.append(unit(sampled))
            except ValueError:
                continue
    if not features:
        raise ValueError("No informative patches")
    return np.stack(features)


def fingerprint(array, affine, *, file_sha256=None):
    import nibabel as nib
    array = np.asarray(array)
    affine = np.asarray(affine,dtype=float)
    if array.ndim != 3 or min(array.shape)<3 or array.size > MAX_VOXELS:
        raise ValueError("Volume allocation bound")
    if affine.shape != (4,4) or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<1e-9:
        raise ValueError("Invalid affine")
    if not np.isfinite(array).all():
        raise ValueError("Nonfinite CT")
    canonical = nib.as_closest_canonical(nib.Nifti1Image(array.astype(np.float32), affine))
    values = canonical.get_fdata(dtype=np.float32)
    # Exact scaled float32 equality; this is not rounded/quantized equality.
    exact_values = np.asarray(values,dtype="<f4",order="C")
    geometry = dict(shape=list(values.shape), affine=np.round(canonical.affine,6).tolist())
    # Keep appearance processing small. Exact equality still uses every voxel.
    steps=np.maximum(1,np.ceil(np.asarray(values.shape)/96).astype(int))
    overview=values[tuple(slice(None,None,int(step)) for step in steps)]
    vectors = patches(overview)
    # Small projections are only an approximate retrieval index. Full vectors rank candidates.
    descriptors = []
    for vector in vectors:
        block = vector.reshape((GRID,)*3)
        projections = np.concatenate([block.mean(axis=axis).reshape(-1) for axis in range(3)])
        descriptors.append(unit(projections))
    return dict(schema="prowl.stunet.overlap-fingerprint.v1", file_sha256=file_sha256,
                normalized_voxel_sha256=hashlib.sha256(str(values.shape).encode()+exact_values.tobytes()).hexdigest(),
                voxel_hash_policy="RAS orientation; scaled float32; exact C-order bytes and shape",
                appearance_stride=steps.tolist(),
                geometry=geometry, vectors=vectors.tolist(), descriptors=np.stack(descriptors).tolist(),
                patient_identity_confirmed=False)


def fingerprint_file(path, *, appearance_only_unknown_units=False):
    import nibabel as nib
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size>256*1024**2:
        raise ValueError("File bound/path refusal")
    image = nib.load(path)
    units=image.header.get_xyzt_units()[0]
    if len(image.shape)!=3 or np.prod(image.shape)>MAX_VOXELS:
        raise ValueError("Native allocation bound")
    if units!="mm" and not (appearance_only_unknown_units and units=="unknown"):
        raise ValueError("Explicit mm required outside appearance-only unknown-unit audit")
    h=hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024**2): h.update(block)
    result=fingerprint(image.get_fdata(dtype=np.float32), image.affine, file_sha256=h.hexdigest())
    result.update(declared_spatial_units=units,physical_geometry_certified=False,
                  unknown_units_appearance_only=units=="unknown")
    return result


class FingerprintIndex:
    """Build the approximate candidate index once for the frozen reference pool."""
    def __init__(self,references):
        self.references=references
        descriptors=[];self.owners=[]
        for index,ref in enumerate(references):
            f=ref['fingerprint']
            f['vectors']=np.asarray(f['vectors'],dtype=np.float32)
            for d in f['descriptors']:
                descriptors.append(d);self.owners.append(index)
        self.tree=cKDTree(np.asarray(descriptors)) if references else None

    def rank(self,query,*,top_k=5,coarse_candidates=20):
        if not self.references:return []
        if not 1<=top_k<=20 or not 1<=coarse_candidates<=100:raise ValueError('Candidate bound')
        references=self.references;exact=set()
        for index,ref in enumerate(references):
            f=ref['fingerprint']
            if ((query.get('file_sha256') and query['file_sha256']==f.get('file_sha256')) or
                query['normalized_voxel_sha256']==f['normalized_voxel_sha256']):exact.add(index)
        distances,indices=self.tree.query(query['descriptors'],k=min(3,len(self.owners)))
        coarse={}
        for distance,index in zip(np.asarray(distances).reshape(-1),np.asarray(indices).reshape(-1)):
            owner=self.owners[int(index)];coarse[owner]=min(coarse.get(owner,float('inf')),float(distance))
        candidates=exact|set(sorted(coarse,key=coarse.get)[:coarse_candidates])
        ranked=[];q=np.asarray(query['vectors'],dtype=np.float32)
        for index in candidates:
            ref=references[index];f=ref['fingerprint']
            score=float(np.max(q@np.asarray(f['vectors'],dtype=np.float32).T))
            kind='APPROXIMATE_CANDIDATE'
            if query['normalized_voxel_sha256']==f['normalized_voxel_sha256']:kind='CANONICAL_VOXEL_EQUAL'
            if query.get('file_sha256') and query['file_sha256']==f.get('file_sha256'):kind='EXACT_FILE_EQUAL'
            ranked.append(dict(reference_id=ref['case_id'],similarity=min(1.,max(-1.,score)),
                               match_type=kind,patient_identity_confirmed=False,
                               case_classification='REQUIRES_REVIEW',absence_proves_independence=False))
        return sorted(ranked,key=lambda r:(r['match_type']!='EXACT_FILE_EQUAL',
                                          r['match_type']!='CANONICAL_VOXEL_EQUAL',-r['similarity'],r['reference_id']))[:top_k]


def rank(query,references,*,top_k=5,coarse_candidates=20):
    return FingerprintIndex(references).rank(query,top_k=top_k,coarse_candidates=coarse_candidates)


def reliable_id_candidates(left, right):
    """IDs are comparable only under verified original collection/release namespaces."""
    required=("original_collection","original_release","original_id")
    if not left.get("identity_verified") or not right.get("identity_verified"):
        return False
    return all(left.get(k) and left[k]==right.get(k) for k in required)
