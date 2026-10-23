"""Twelve prior difficult training examples, actual region-loader input review."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scripts.train_pancreas_region import provider,SETUP,write,resource_check
from src.data.segmenter_native_windows_v1 import orient
from src.data.segmenter_pancreas_region_v1 import bank
from src.data.segmenter_physical_windows_v1 import sample_window


def run():
    resource_check();p=provider();root=SETUP/'pilot';root.mkdir(exist_ok=False)
    request=json.loads(Path('E:/PROWL/readiness/native-intake-20261018-a02/request.json').read_text())
    records=request['pilot'];names=[r['case_id'] if isinstance(r,dict) else r for r in records]
    if len(names)!=12 or not set(names)<=set(p.control['train']):raise ValueError('Pilot must be original twelve training examples')
    results=[]
    for i,name in enumerate(names):
        resource_check();began=time.monotonic();case=p.load(name,role='train');record,cover=bank(case)
        target=case['target'];support=target==2 if (target==2).any() else target>0
        center=[int(np.median(np.flatnonzero(support.any(axis=tuple(k for k in range(3) if k!=d))))) for d in range(3)]
        full_pancreas=orient(case['original_pancreas'],case['parent_geometry'])
        sl=tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
        if full_pancreas[sl].sum()!=full_pancreas.sum():raise ValueError('Pilot pancreas clipping')
        if (target==2).sum()!=case['original_lesion'].sum():raise ValueError('Pilot lesion clipping')
        fig,axes=plt.subplots(2,3,figsize=(12,8))
        for d in range(3):
            image=np.take(case['image'],center[d],axis=d).T;label=np.take(target,center[d],axis=d).T
            axes[0,d].imshow(image,cmap='gray',vmin=0,vmax=1,origin='lower')
            if (label>0).any():axes[0,d].contour(label>0,levels=[.5],colors=['cyan'],linewidths=.6)
            if (label==2).any():axes[0,d].contour(label==2,levels=[.5],colors=['red'],linewidths=.8)
            axes[0,d].set_title(f'Region axis {d}; native spacing retained')
        patch,transform=sample_window(case['image'],record,cover[0],order=1)
        label,_=sample_window(target,record,cover[0],order=0)
        support=label==2 if (label==2).any() else label>0
        for d in range(3):
            c=int(np.median(np.flatnonzero(support.any(axis=tuple(k for k in range(3) if k!=d)))))
            img=np.take(patch,c,axis=d).T;lab=np.take(label,c,axis=d).T
            axes[1,d].imshow(img,cmap='gray',vmin=0,vmax=1,origin='lower')
            if (lab>0).any():axes[1,d].contour(lab>0,levels=[.5],colors=['cyan'],linewidths=.6)
            if (lab==2).any():axes[1,d].contour(lab==2,levels=[.5],colors=['red'],linewidths=.8)
            axes[1,d].set_title(f'Actual 144-cube coverage window; axis {d}')
        for ax in axes.flat:ax.axis('off')
        fig.suptitle(f'Private training pilot {i+1}/12: full retained region and first detail window')
        fig.tight_layout();fig.savefig(root/f'case-{i+1:02d}.png',dpi=110);plt.close(fig)
        results.append(dict(case_id=name,figure=f'case-{i+1:02d}.png',coverage_pass=True,cover_windows=len(cover),seconds=time.monotonic()-began))
        print(json.dumps(dict(completed=i+1,seconds=results[-1]['seconds'])),flush=True)
    write(root/'result.json',dict(cases=results,completed=True,ct_reads=12,test_reads=0))


if __name__=='__main__':run()
