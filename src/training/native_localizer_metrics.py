"""Bounded native-grid metrics, including dense failures; no model/ROI policy selection."""
import math
import numpy as np
from src.data.source_inventory_records import require

MAX_VOXELS=96_000_000


def measure(prediction,reference,affine):
    p=np.asarray(prediction);y=np.asarray(reference);a=np.asarray(affine,dtype=np.float64)
    require(p.ndim==3 and p.shape==y.shape and 0<math.prod(p.shape)<=MAX_VOXELS and
            p.dtype.kind in 'buif' and y.dtype.kind in 'buif','Invalid bounded metric arrays')
    require(a.shape==(4,4) and np.isfinite(a).all() and np.allclose(a[3],[0,0,0,1],rtol=0,atol=1e-8),'Invalid affine')
    spacing=np.linalg.norm(a[:3,:3],axis=0)
    require((spacing>0).all() and np.allclose(a[:3,:3].T@a[:3,:3],np.diag(spacing**2),atol=1e-4,rtol=1e-4),
            'Orthogonal physical axes required')
    n=v=tp=0;lo=np.array(p.shape);hi=np.zeros(3,dtype=np.int64)
    # No full foreground coordinate list or connected-component volume. Each transient is a16-slice slab.
    for start in range(0,p.shape[2],16):
        pp=p[:,:,start:start+16];yy=y[:,:,start:start+16]
        require(np.isin(pp,[0,1]).all() and np.isin(yy,[0,1]).all(),'Binary metrics required')
        n+=int(np.count_nonzero(yy));v+=int(np.count_nonzero(pp));tp+=int(np.count_nonzero(np.logical_and(pp,yy)))
        for axis in range(3):
            occupied=np.flatnonzero(np.any(pp,axis=tuple(k for k in range(3) if k!=axis)))
            if occupied.size:
                offset=start if axis==2 else 0
                lo[axis]=min(lo[axis],int(occupied[0])+offset);hi[axis]=max(hi[axis],int(occupied[-1])+offset+1)
    require(n>0,'Empty reference is outside the qualified positive-reference scope')
    box=None;coverage=fraction=None
    if v:
        pad=np.ceil(10/spacing).astype(np.int64);lo=np.maximum(0,lo-pad);hi=np.minimum(p.shape,hi+pad)
        covered=0
        for z in range(int(lo[2]),int(hi[2]),16):
            covered+=int(np.count_nonzero(y[lo[0]:hi[0],lo[1]:hi[1],z:min(z+16,hi[2])]))
        box=[lo.tolist(),hi.tolist()];coverage=covered/n;fraction=math.prod((hi-lo).tolist())/math.prod(p.shape)
    voxel_ml=abs(float(np.linalg.det(a[:3,:3])))/1000
    return dict(schema_version='native-localizer-metrics-1',reference_voxels=n,predicted_voxels=v,
        true_positive=tp,false_positive=v-tp,false_negative=n-tp,dice=2*tp/(n+v),recall=tp/n,
        precision=tp/v if v else None,volume_ratio=v/n,reference_volume_ml=n*voxel_ml,predicted_volume_ml=v*voxel_ml,
        box=box,box_reference_coverage=coverage,scan_fraction=fraction,margin_mm=10.,
        localization_state='region_available' if v else 'failed_empty_localization',
        roi_diagnostic_pass=bool(coverage is not None and coverage>=.995 and fraction<=.25),
        component_detail_state='not_computed',scope='native acquired grid; visible-reference comparison, not whole-organ completeness')
