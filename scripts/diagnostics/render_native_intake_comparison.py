"""Private, approximately plane-matched old/new input figures; no model inference."""
from itertools import product
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_native_intake import OUT,provider,verify
from src.data.segmenter_native_windows_v1 import extract
from src.training.experiment_config import sha256


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    verify();p=provider();directory=OUT/'comparisons';directory.mkdir(exist_ok=False)
    for name in ('PanTS_00002720','PanTS_00003059'):
        c=p.load(name,role='train');meta=json.loads((p.root/(name+'.json')).read_text())
        cached=p.root/(name+'.npz')
        if sha256(cached)!=p.review['prepared_cache']['members'][name]['cache_sha256']:raise ValueError('Old tensor changed')
        with np.load(cached,allow_pickle=False) as z:old_image=z['image'][0];old_target=z['target']
        old_aff=np.array(meta['transform']['tensor_affine']);aff=np.array(c['geometry']['affine'])
        old_z=int(np.argmax((old_target==2).sum(axis=(0,1))))
        world_z=(old_aff @ [0,0,old_z,1])[2]
        native_z=int(np.clip(round((world_z-aff[2,3])/aff[2,2]),0,c['image'].shape[2]-1))
        world_z=(aff @ [0,0,native_z,1])[2]
        old_z=int(np.clip(round((world_z-old_aff[2,3])/old_aff[2,2]),0,143))
        count=len(c['coverage']);fig,axes=plt.subplots(1,2+count,figsize=(5*(2+count),5))
        def show(ax,image,target,title):
            ax.imshow(image.T,origin='lower',cmap='gray',vmin=0,vmax=1,interpolation='nearest')
            for label,color in ((1,'cyan'),(2,'red')):
                m=target==label
                if m.any() and not m.all():ax.contour(m.T,levels=[.5],colors=[color],linewidths=.8)
            ax.set_title(title,fontsize=10);ax.set_axis_off()
        show(axes[0],old_image[:,:,old_z],old_target[:,:,old_z],f'Original actual 144³ tensor\nSlice {old_z}; spatially resampled')
        show(axes[1],c['image'][:,:,native_z],c['target'][:,:,native_z],f'Full source CT field\nNative slice {native_z}; red = reference lesion')
        old=meta['transform'];corners=np.array(list(product(*[(a,b-1) for a,b in zip(*old['native_box'])])))
        transform=np.linalg.inv(aff) @ np.array(old['source_affine'])
        q=(transform @ np.c_[corners,np.ones(len(corners))].T).T[:,:3]
        low=q.min(0);high=q.max(0)+1
        if low[2]<=native_z<high[2]:axes[1].add_patch(Rectangle(low[:2]-.5,*(high-low)[:2],fill=False,edgecolor='orange',linewidth=2,label='old crop'))
        for i,origin in enumerate(c['coverage']):
            color=['lime','magenta','yellow'][i%3]
            axes[1].add_patch(Rectangle((origin[0]-.5,origin[1]-.5),144,144,fill=False,edgecolor=color,linewidth=1.2))
            x,_=extract(c['image'],origin);y,_=extract(c['target'],origin);local_z=native_z-origin[2]
            if not 0<=local_z<144:raise ValueError('Display plane outside coverage window')
            show(axes[2+i],x[:,:,local_z],y[:,:,local_z],f'New actual window {i+1} of {count}\nNative voxels; no spatial interpolation')
            for spine in axes[2+i].spines.values():spine.set_edgecolor(color)
        spacing=np.linalg.norm(aff[:3,:3],axis=0)
        fig.suptitle(f'{name} — input coverage comparison\nOrange = old crop; green/magenta = new coverage windows. Native spacing {spacing.round(3).tolist()} mm.\nApproximately matched physical axial planes; panels show different fields of view. Masks are targets, not input channels.',fontsize=11)
        fig.tight_layout(rect=(0,0,1,.83));fig.savefig(directory/(name+'.png'),dpi=110);plt.close(fig)
    verify()


if __name__=='__main__':main()
