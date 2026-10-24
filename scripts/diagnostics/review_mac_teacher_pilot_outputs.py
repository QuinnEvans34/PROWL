"""Bounded post-pilot training-mask/probability review; no CT or model reads."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from src.data.segmenter_native_windows_v1 import orient
from src.data.segmenter_content_v1 import target_content


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def review(base,output):
    if output.exists():raise ValueError('Preserve existing output')
    pilot=base/'patient-pilot-02'
    result=json.loads((pilot/'result.json').read_text());resources=json.loads((pilot/'resources.json').read_text())
    if not result['success'] or not resources['success'] or not resources['workers_reaped']:raise ValueError('Completed pilot required')
    bindings=json.loads((base/'pilot-local-bindings-01.json').read_text())['pilot']
    if [r['case_id'] for r in result['cases']] != [r['case_id'] for r in bindings]:raise ValueError('Pilot order differs')
    rows=[]
    for binding in bindings:
        name=binding['case_id'];meta=json.loads((base/f'metadata-received-01/native-region/members/{name}.json').read_text())
        if np.prod(meta['parent_geometry']['source_shape'],dtype=np.int64)>256000000:raise ValueError('Source voxel cap')
        slices=tuple(slice(l,h) for l,h in zip(meta['region_low'],meta['region_high']))
        for role in ('pancreas','lesion'):
            p=Path(binding['files'][role]['path'])
            if sha(p)!=binding['files'][role]['sha256']:raise ValueError('Mask identity changed')
            obj=nib.load(p)
            if list(obj.shape)!=meta['parent_geometry']['source_shape'] or not np.allclose(obj.affine,meta['parent_geometry']['source_affine'],rtol=0,atol=1e-4):raise ValueError('Mask geometry differs')
            proxy=obj.dataobj;mask,_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
            region=orient(mask,meta['parent_geometry'])[slices]
            if role=='pancreas':target=region.astype(np.uint8)
            else:target[region!=0]=2
            del obj,mask,region
        file=pilot/(name+'-probability.npz')
        with np.load(file,allow_pickle=False) as z:
            raw=z['probability'];assert raw.dtype==np.uint16 and raw.shape==target.shape
            q=raw.astype(np.float32)/65535
        assert int((target==2).sum())==meta['lesion_voxels']
        labels,count=ndimage.label(target==2,structure=np.ones((3,3,3)))
        components=[];voxel_mm3=abs(float(np.linalg.det(np.asarray(meta['geometry']['affine'])[:3,:3])))
        for i in range(1,count+1):
            values=q[labels==i]
            components.append(dict(component=i,voxels=len(values),volume_ml=len(values)*voxel_mm3/1000,
                detected=bool((values>.5).any()),eligible_positive_voxels=int((values>.5+.5/65535).sum()),
                suppressed_at_point1=int((values<=.1).sum())))
        rows.append(dict(case_id=name,components=components,probability_sha256=sha(file),
            strata={str(k):dict(voxels=int((target==k).sum()),high_at_point9=int((q[target==k]>=.9).sum()),low_at_point1=int((q[target==k]<=.1).sum())) for k in (0,1,2)},
            image_sha256=sha(pilot/(name+'.png')),source_mask_sha256={k:binding['files'][k]['sha256'] for k in ('pancreas','lesion')}))
        print(name,'components',count,'detected',sum(c['detected'] for c in components),flush=True)
        del target,q,raw,labels
    report=dict(cases=rows,quality_accepted=False,decoded_CT_reads=0,model_runs=0,
        scope='training-only diagnostic; supplied annotations; quantized probabilities',
        threshold_note='Quantized comparisons near thresholds have half-step rounding uncertainty; not calibrated confidence.',
        pilot_result_sha256=sha(pilot/'result.json'))
    with output.open('x') as f:json.dump(report,f,indent=2)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();review(a.base,a.output)
