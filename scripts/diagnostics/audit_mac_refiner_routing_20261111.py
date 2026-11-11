"""Read-only proposal feasibility. Does not invoke the refiner or open CT voxels."""
import argparse
import gc
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.diagnostics.audit_stunet_selected_dice_20261110 import admitted_cases, read, sha, STUDY
from scripts.diagnostics.screen_stunet_lesion_core_20261110 import core_support
import nibabel as nib
import numpy as np
from scipy import ndimage
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_native_windows_v1 import geometry,orient
from src.inference.stunet_margin_screen_20261110 import STRUCTURE, components, unpack

CORE=Path('/tmp/prowl-core-screen-20261110.ImvTkV/result.json')
CORE_PROOF=ROOT/'docs/capstone/evaluation/STUNET-24K-CONFIDENT-CORE-RESULTS-20261110.json'
ARMS=('incumbent_le1ml','incumbent_le2ml','additional_plus1_le1ml')


def describe(ids, labels, truth, sizes, affine):
    boxes=ndimage.find_objects(labels)
    labels_at_ref=labels[truth!=0]
    ref_at_ref=truth[truth!=0]
    hits={}
    false_count=0
    for i in ids:
        found=set(int(k) for k in np.unique(ref_at_ref[labels_at_ref==i]))
        if not found:
            false_count+=1
            continue
        box=boxes[i-1]
        center=[(s.start+s.stop-1)//2 for s in box]
        # Same 64-voxel native-RAS crop as the known-location pilot.
        crop=truth[tuple(slice(max(0,c-32),min(n,c+32)) for c,n in zip(center,truth.shape))]
        counts=np.bincount(crop.ravel(),minlength=len(sizes))
        for k in found:
            hits[k]=max(hits.get(k,0.),float(counts[k]/sizes[k]))
    return dict(proposals=len(ids),zero_overlap_proposals=false_count,
                hits=sorted(hits),crop_covers_90_percent=sorted(k for k,v in hits.items() if v>=.9))


def examine(case,receipt,expected):
    a=np.asarray(case['native_affine'])
    g=geometry(case['native_shape'],a)
    source=case['sources']['lesion']
    if sha(source['path'])!=source['sha256']:
        raise ValueError('Reference hash changed')
    img=nib.load(source['path'])
    if list(img.shape)!=case['native_shape'] or not np.allclose(img.affine,a,atol=1e-5,rtol=0):
        raise ValueError('Reference geometry changed')
    target,_=target_content(img.dataobj.get_unscaled(),
         dict(slope=float(img.dataobj.slope),intercept=float(img.dataobj.inter)))
    truth,n=ndimage.label(target,structure=STRUCTURE)
    del target
    truth=orient(truth,g)
    sizes=np.bincount(truth[truth!=0],minlength=n+1)
    v=abs(np.linalg.det(a[:3,:3]))/1000
    small={i for i in range(1,n+1) if sizes[i]*v<1}
    source=receipt['artifact']
    if sha(source['backup'])!=source['sha256']:
        raise ValueError('Prediction archive changed')
    with np.load(source['backup'],allow_pickle=False) as data:
        code=unpack(data['packed'],[int(x) for x in data['shape']])
    if list(code.shape)!=case['native_shape']:
        raise ValueError('Prediction geometry changed')
    idx,tiers,dist,shells=core_support(code,a,trim_levels=[2,3],grow_radii=[0,1.5,3])
    mask=np.zeros(code.shape,dtype=bool)
    mask.flat[idx[(tiers>3)|(dist<=4)]]=True
    mask.flat[shells[1.5]]=True
    ras=orient(mask,g)
    hits=truth[ras]
    actual=dict(p=len(hits),t=int(np.count_nonzero(hits)),hits=[int(x) for x in np.unique(hits) if x])
    if actual!={k:expected[k] for k in actual}:
        raise ValueError('Incumbent mask replay changed')
    labels,k=ndimage.label(ras,structure=STRUCTURE)
    counts=np.bincount(labels[ras],minlength=k+1)
    result={}
    for name,limit in zip(ARMS[:2],(1.,2.)):
        ids=np.flatnonzero((counts>0)&(counts*v<=limit))
        result[name]=describe(ids,labels,truth,sizes,a)
    del labels,ras
    pred,labels,info=components(code,1.,a)
    del pred
    incumbent_overlap=np.unique(labels[mask])
    candidate=(info['sizes']>0)&(info['sizes']*v<=1.)&(info['distance']<=5.)
    candidate[incumbent_overlap]=False
    candidate[0]=False
    if not info['context']:
        candidate[:]=False
    result[ARMS[-1]]=describe(np.flatnonzero(candidate),orient(labels,g),truth,sizes,a)
    return dict(case_id=case['case_id'],reference_components=n,small=sorted(small),
         incumbent_hits=actual['hits'],arms=result)


def summary(rows):
    if (len(rows),len({r['case_id'] for r in rows}),sum(r['reference_components'] for r in rows),
         sum(len(r['small']) for r in rows),sum(bool(r['reference_components']) for r in rows))!=(70,70,45,12,36):
        raise ValueError('Fixed cohort changed')
    out={}
    for name in ARMS:
        arm=[r['arms'][name] for r in rows]
        out[name]=dict(proposals=sum(a['proposals'] for a in arm),
            zero_overlap_proposals=sum(a['zero_overlap_proposals'] for a in arm),
            empty_scans_with_proposals=sum(bool(r['arms'][name]['proposals']) for r in rows if not r['reference_components']),
            small_hits=sum(len(set(r['small'])&set(r['arms'][name]['hits'])) for r in rows),
            small_hits_with_90_percent_in_crop=sum(len(set(r['small'])&set(r['arms'][name]['crop_covers_90_percent'])) for r in rows),
            small_hits_incumbent_missed=sum(len((set(r['small'])&set(r['arms'][name]['hits']))-set(r['incumbent_hits'])) for r in rows),
            larger_hits=sum(len(set(r['arms'][name]['hits'])-set(r['small'])) for r in rows))
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if sha(CORE)!=read(CORE_PROOF)['full_local_result_sha256']:
        raise ValueError('Verified comparator changed')
    core=read(CORE)
    prior={r['case_id']:r['arms'][core['selected']] for r in core['rows']}
    cases,receipts=admitted_cases()
    rows=[]
    for case in cases:
        k=case['case_id']
        rows.append(examine(case,receipts[k],prior[k]))
        gc.collect()
        print(f'verified {len(rows)}/70',flush=True)
    with args.output.open('x') as f:
        json.dump(dict(scope='Proposal coverage only; no refiner, CT, GPU or optimizer calls',
          comparator=core['selected'],candidates=summary(rows),rows=rows),f,indent=2,allow_nan=False)
        f.write('\n')


if __name__=='__main__':
    main()
