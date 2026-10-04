"""Read-only target-representation experiments; never an active training recipe."""
from copy import deepcopy
import numpy as np
import torch
from src.data.localizer_preprocessing_v3 import preprocess,restore_to_source
from src.data.source_inventory_records import require


def center_splat(target,source_affine,processed_affine,processed_shape):
    """Map source foreground centers, not voxel volumes; this is not conservative occupancy."""
    target=np.asarray(target);require(target.ndim==3 and np.isin(target,[0,1]).all(),'Binary 3D target required')
    coords=np.argwhere(target>0);require(len(coords)<=100000,'Sparse diagnostic foreground cap')
    transform=np.linalg.inv(np.asarray(processed_affine))@np.asarray(source_affine)
    mapped=np.rint(coords@transform[:3,:3].T+transform[:3,3]).astype(np.int64)
    require(np.all(mapped>=0) and np.all(mapped<np.asarray(processed_shape)),'Foreground center outside output grid')
    out=np.zeros(processed_shape,dtype=np.uint8)
    if len(mapped):out[tuple(mapped.T)]=1
    return out


def measure(reference,restored,affine):
    a=np.asarray(reference,dtype=bool);b=np.asarray(restored,dtype=bool)
    require(a.shape==b.shape and a.any(),'Same grid and positive reference required')
    tp=int(np.logical_and(a,b).sum());na=int(a.sum());nb=int(b.sum())
    return dict(source_foreground=na,restored_foreground=nb,true_positive=tp,false_negative=na-tp,false_positive=nb-tp,
                recall=tp/na,precision=tp/nb if nb else 0.,dice=2*tp/(na+nb),volume_ratio=nb/na,
                source_volume_mm3=na*abs(float(np.linalg.det(np.asarray(affine)[:3,:3]))))


def compare(target,affine,recipe):
    """Zero CT surrogate: only target geometry/representation is investigated."""
    import gc
    rows=[];source=np.asarray(target,dtype=np.uint8)
    for spacing in (3.,2.,1.5):
        r=deepcopy(recipe);r['spacing_mm']=[spacing]*3
        result=preprocess(np.zeros(source.shape,dtype=np.float32),affine,r,target=source)
        record=result['transform_record'];label=result['label'].as_tensor().numpy()[0].astype(np.uint8)
        variants=[('nearest',label)]
        if spacing==3.:variants.append(('foreground_center_splat',center_splat(source,affine,record['processed_affine'],record['processed_shape'])))
        for name,mask in variants:
            restored=restore_to_source(torch.from_numpy(mask[None]),record,discrete=True).as_tensor().numpy()[0]>0
            rows.append(dict(method=name,spacing_mm=spacing,processed_foreground=int(mask.sum()),processed_shape=record['processed_shape'],
                             processed_affine=record['processed_affine'],**measure(source,restored,affine)))
            del restored
        del result,label,variants;gc.collect()
    coords=np.argwhere(source);return dict(source_shape=list(source.shape),source_affine=np.asarray(affine).tolist(),
        foreground_bounds_xyz=[coords.min(0).tolist(),coords.max(0).tolist()],foreground_counts_by_axis=[dict(zip(*[x.tolist() for x in np.unique(coords[:,axis],return_counts=True)])) for axis in range(3)],comparisons=rows)
