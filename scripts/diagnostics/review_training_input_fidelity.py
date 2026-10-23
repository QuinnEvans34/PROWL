"""Focused saved-input review. No models, optimizer, test data or cache writes."""
import csv
import json
import sys
import time
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.segmenter_geometry_v2 import restore_codes, validate_record
from src.data.segmenter_content_v1 import target_content
from src.training.experiment_config import sha256

SETUP = Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01')
OUT = Path('E:/PROWL/readiness/input-fidelity-20261018-a01')


def read(p): return json.loads(p.read_text())


def overlap(reference, predicted):
    n, m = int(reference.sum()), int(predicted.sum())
    tp = int(np.count_nonzero(reference & predicted))
    return dict(reference_voxels=n, restored_voxels=m, true_positive=tp,
                dice=2*tp/(n+m) if n+m else None, recall=tp/n if n else None)


def plane(array, affine, world, order):
    coords = (np.linalg.inv(affine) @ world.reshape(4, -1))[:3]
    return map_coordinates(array, coords, order=order, mode='constant', cval=0,
                           prefilter=False).reshape(world.shape[1:])


def render(alias, ct, lesion, pancreas, cached, target, restored, transform, result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    affine = np.asarray(transform['source_affine'])
    tensor_affine = np.asarray(transform['tensor_affine'])
    # A lesion voxel nearest the lesion centroid avoids empty centroid planes.
    points = np.argwhere(lesion)
    center_index = points[np.argmin(((points-points.mean(0))**2).sum(1))]
    center = (affine @ np.r_[center_index, 1])[:3]
    edge = np.asarray(transform['world_low_edge_mm'])
    extent = np.asarray(transform['physical_extent_mm'])
    fig, axes = plt.subplots(3, 3, figsize=(12, 10), facecolor='#101820')
    for row, (fixed, horizontal, vertical, name) in enumerate([(2,0,1,'Axial'),(1,0,2,'Coronal'),(0,1,2,'Sagittal')]):
        u = np.linspace(edge[horizontal], edge[horizontal]+extent[horizontal], 380)
        v = np.linspace(edge[vertical], edge[vertical]+extent[vertical], 380)
        uu, vv = np.meshgrid(u, v)
        world = np.ones((4,380,380)); world[fixed] = center[fixed]
        world[horizontal] = uu; world[vertical] = vv
        images = [plane(ct, affine, world, 1), plane(cached, tensor_affine, world, 0)]
        native_mask = plane(lesion.astype(np.uint8), affine, world, 0)
        pan = plane(pancreas.astype(np.uint8), affine, world, 0)
        tensor_mask = plane((target == 2).astype(np.uint8), tensor_affine, world, 0)
        back = plane((restored == 2).astype(np.uint8), affine, world, 0)
        bounds = (u[0], u[-1], v[0], v[-1])
        for col, ax in enumerate(axes[row]):
            ax.imshow(images[1] if col == 1 else images[0], cmap='gray', vmin=0, vmax=1,
                      origin='lower', extent=bounds, aspect='equal')
            masks = [(tensor_mask, '#00e5ff')] if col == 1 else [(native_mask, '#ff4f70'), (pan, '#ffdc64')] if col == 0 else [(native_mask, '#ff4f70'), (back, '#00e5ff')]
            for mask, color in masks:
                if mask.any() and not mask.all(): ax.contour(mask, levels=[.5], colors=[color], linewidths=.8, origin='lower', extent=bounds)
            ax.set_xticks([]); ax.set_yticks([])
            if col == 0: ax.set_ylabel(name, color='white')
            if row == 0: ax.set_title(['Original CT + reference','Exact cached CT + training target','Original + returned cached target'][col], color='white', fontsize=10)
    fig.suptitle(f'{alias} | crop coverage {result["crop_coverage"]:.2%} | target round-trip Dice {result["lesion"]["dice"]:.3f}\nSame physical planes, RAS axes; final spacing {transform["effective_spacing_mm"][0]:.3f} mm', color='white', fontsize=12)
    fig.legend(handles=[Line2D([0],[0],color='#ff4f70',label='Original lesion'),Line2D([0],[0],color='#00e5ff',label='Cached / returned lesion'),Line2D([0],[0],color='#ffdc64',label='Original pancreas')],loc='lower center',ncol=3,facecolor='white')
    fig.tight_layout(rect=(0,.05,1,.93)); fig.savefig(OUT/(alias+'.png'), dpi=130); plt.close(fig)


def main():
    started = time.monotonic()
    review = read(SETUP/'cohort-review.json'); cache = Path(review['prepared_cache']['root'])
    source = read(cache/'control.json')
    with Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-manifest.csv').open(newline='') as f:
        rows = {r['case_id']:r for r in csv.DictReader(f)}
    train = Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-admitted/train.txt').read_text().split()
    dev = (SETUP/'development.txt').read_text().split()
    metas = {n:read(cache/(n+'.json')) for n in train}
    positive = [n for n in train if review['target_states'][n]=='positive']
    by_size = sorted(positive, key=lambda n:sum(c['native_voxels'] for c in metas[n]['fidelity']['components'])*abs(np.linalg.det(np.array(metas[n]['transform']['source_affine'])[:3,:3])))
    selected_train = []
    for order in [by_size, sorted(positive,key=lambda n:metas[n]['transform']['effective_spacing_mm'][0])]:
        for q in [0,.1,.3,.5,.8,1]:
            n = order[round(q*(len(order)-1))]
            if n not in selected_train: selected_train.append(n)
    for n in by_size:
        if len(selected_train)>=12: break
        if n not in selected_train: selected_train.append(n)
    old = read(Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01/parent-reduced-comparison.json'))['reports']['best']['cases']
    new = read(Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017/execution/native-selected.json'))['cases']
    a={r['case_id']:r['metrics'] for r in old}; b={r['case_id']:r['metrics'] for r in new}
    selected_dev=sorted(n for n in dev if b[n]['reference_positive'] and b[n]['size_band'] in ('small','large'))
    worst=sorted((n for n in dev if b[n]['reference_positive'] and b[n]['size_band']=='medium'),key=lambda n:b[n]['lesion']['dice']-a[n]['lesion']['dice'])[:3]
    selected_dev+=worst
    selected=selected_train+selected_dev
    assert len(selected)==len(set(selected)) and set(selected)<=set(train+dev)
    # Six examples fixed before inspecting fidelity outcomes.
    large_worst=min((n for n in selected_dev if b[n]['size_band']=='large'),key=lambda n:b[n]['lesion']['dice']-a[n]['lesion']['dice'])
    small=min((n for n in selected_dev if b[n]['size_band']=='small'),key=lambda n:b[n]['target_volume_mm3'])
    visual=set([selected_train[0],selected_train[3],selected_train[-1],large_worst,small,worst[0]])
    OUT.mkdir(exist_ok=False)
    (OUT/'selection.json').write_text(json.dumps(dict(train=selected_train,development=selected_dev,visual=sorted(visual),rule='12 training size/spacing quantiles; all 5 small and 7 large dev positives + 3 worst medium deltas',test_reads=0),indent=2))
    results=[]
    for i,n in enumerate(selected):
        assert time.monotonic()-started<1800, '30 minute diagnostic bound'
        meta=read(cache/(n+'.json')); transform=meta['transform']
        assert sha256(cache/(n+'.json'))==review['prepared_cache']['members'][n]['metadata_sha256']
        validate_record(transform,meta['transform_sha256'])
        assert sha256(cache/(n+'.npz'))==meta['cache_sha256']
        labels={}
        for kind in ('lesion','pancreas'):
            path=Path(rows[n][kind+'_path']); assert sha256(path)==meta['source_sha256'][kind]
            obj=nib.load(path); assert obj.shape==tuple(transform['source_shape']) and np.allclose(obj.affine,transform['source_affine'],atol=1e-5,rtol=0)
            p=obj.dataobj; labels[kind],_=target_content(p.get_unscaled(),dict(slope=float(p.slope),intercept=float(p.inter)))
        with np.load(cache/(n+'.npz'),allow_pickle=False) as z: target=z['target']; image=z['image'][0]
        restored=restore_codes(target,transform,trusted_record_sha256=meta['transform_sha256'])
        lesion=labels['lesion'].astype(bool); pancreas=labels['pancreas'].astype(bool)
        lo,hi=transform['native_box']; box=tuple(slice(l,h) for l,h in zip(lo,hi))
        inside=int(lesion[box].sum()); total=int(lesion.sum())
        alias=('training-' if n in train else 'development-')+f'{i+1:02d}'
        r=dict(alias=alias,case_id=n,role='train' if n in train else 'development',crop_coverage=inside/total,
            outside_crop_voxels=total-inside,lesion=overlap(lesion,restored==2),
            pancreas=overlap(pancreas & ~lesion,restored==1),spacing_mm=transform['effective_spacing_mm'][0],
            source_shape=transform['source_shape'],normalized_shape=transform['normalized_shape'],
            transform_sha256=meta['transform_sha256'],cache_sha256=meta['cache_sha256'])
        if n in b:r.update(size_band=b[n]['size_band'],model_dice=b[n]['lesion']['dice'],previous_model_dice=a[n]['lesion']['dice'])
        if n in visual:
            path=Path(rows[n]['ct_path']); assert sha256(path)==meta['source_sha256']['ct']
            obj=nib.load(path); assert obj.shape==lesion.shape and np.allclose(obj.affine,transform['source_affine'],atol=1e-5,rtol=0)
            ct=np.clip((obj.get_fdata(dtype=np.float32)+100)/350,0,1)
            render(alias,ct,lesion,pancreas,image,target,restored,transform,r)
            r['figure']=str(OUT/(alias+'.png'));del ct
        results.append(r)
        with (OUT/'cases.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
        print(json.dumps(r),flush=True)
    summary=dict(completed=True,cases=results,elapsed_seconds=time.monotonic()-started,ct_reads=len(visual),
        label_cases=len(selected),model_inference=0,optimizer_updates=0,test_reads=0,
        code_sha256=sha256(__file__),scope='Targeted diagnostic subset, not population estimate or model ceiling')
    (OUT/'results.json').write_text(json.dumps(summary,indent=2))


if __name__=='__main__':main()
