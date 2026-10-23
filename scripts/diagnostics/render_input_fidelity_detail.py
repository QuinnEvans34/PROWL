"""Additional view of the discovered clipping case; local diagnostic images only."""
import csv
import json
import sys
from pathlib import Path
import numpy as np
import nibabel as nib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.review_training_input_fidelity import OUT,SETUP,read,render
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_geometry_v2 import restore_codes
from src.training.experiment_config import sha256


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    review=read(SETUP/'cohort-review.json');cache=Path(review['prepared_cache']['root'])
    n='PanTS_00002720'
    results=[json.loads(l) for l in (OUT/'cases.jsonl').read_text().splitlines()]
    result=next(r for r in results if r['case_id']==n)
    meta=read(cache/(n+'.json'));t=meta['transform']
    with Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-manifest.csv').open(newline='') as f:
        row=next(r for r in csv.DictReader(f) if r['case_id']==n)
    labels={}
    for kind in ('lesion','pancreas'):
        p=Path(row[kind+'_path']);assert sha256(p)==meta['source_sha256'][kind]
        obj=nib.load(p);proxy=obj.dataobj
        labels[kind],_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
    p=Path(row['ct_path']);assert sha256(p)==meta['source_sha256']['ct']
    obj=nib.load(p);assert np.allclose(obj.affine,t['source_affine'],atol=1e-5,rtol=0)
    ct=np.clip((obj.get_fdata(dtype=np.float32)+100)/350,0,1)
    with np.load(cache/(n+'.npz')) as z:x=z['image'][0];y=z['target']
    restored=restore_codes(y,t,trusted_record_sha256=meta['transform_sha256'])
    # Expand DISPLAY field only to include original lesion and pancreas; cache remains untouched.
    import itertools
    points=np.argwhere((labels['lesion']>0)|(labels['pancreas']>0))
    lo=points.min(0);hi=points.max(0)
    corners=np.array([list(c)+[1] for c in itertools.product(*zip(lo,hi))])
    world=(np.asarray(t['source_affine'])@corners.T).T[:,:3]
    display=dict(t,world_low_edge_mm=(world.min(0)-15).tolist(),physical_extent_mm=(world.max(0)-world.min(0)+30).tolist())
    render('clipped-training-lesion-expanded-context',ct,labels['lesion'].astype(bool),labels['pancreas'].astype(bool),x,y,restored,display,result)
    # Uncropped cube slices show exact tensor pixels and padding, not interpolated display planes.
    center=np.argwhere(y==2).mean(0).astype(int)
    fig,axes=plt.subplots(1,3,figsize=(12,4.6),facecolor='#101820')
    for ax,axis,name in zip(axes,[2,1,0],['Axial','Coronal','Sagittal']):
        im=np.take(x,center[axis],axis=axis).T; target=np.take(y,center[axis],axis=axis).T
        ax.imshow(im,cmap='gray',vmin=0,vmax=1,origin='lower',interpolation='nearest')
        ax.contour(target==2,levels=[.5],colors=['#00e5ff'],linewidths=.8)
        ax.set_title(name,color='white');ax.set_xticks([]);ax.set_yticks([])
    fig.suptitle('Exact 144 x 144 x 144 cached input | three slices, including zero padding\nCyan: surviving training lesion target; no mask is an input channel',color='white')
    fig.tight_layout(rect=(0,0,1,.85));fig.savefig(OUT/'exact-cached-cube.png',dpi=130);plt.close(fig)
    (OUT/'additional-view.json').write_text(json.dumps(dict(case_id=n,ct_reads=1,reason='11.6 percent lesion crop coverage discovered',display_only_expansion=True,cache_modified=False,code_sha256=sha256(__file__)),indent=2))


if __name__=='__main__':main()
