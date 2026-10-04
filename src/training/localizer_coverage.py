"""Independent source-grid diagnostics; never selects a production ROI or annotation use."""
import numpy as np
from scipy import ndimage
from src.data.source_inventory_records import require


def inspect_coverage(prediction,reference,affine):
    p=np.asarray(prediction);y=np.asarray(reference);a=np.asarray(affine,dtype=float)
    require(p.ndim==3 and p.shape==y.shape and 0<p.size<=64_000_000,'Bounded matching grids required')
    require(np.isin(p,[0,1]).all() and np.isin(y,[0,1]).all(),'Binary inputs required')
    require(a.shape==(4,4) and np.isfinite(a).all() and np.allclose(a[3],[0,0,0,1]),'Invalid affine')
    spacing=np.linalg.norm(a[:3,:3],axis=0)
    require((spacing>0).all() and np.allclose(a[:3,:3].T@a[:3,:3],np.diag(spacing**2),atol=1e-4,rtol=1e-4),'Orthogonal physical axes required')
    p=p.astype(bool);y=y.astype(bool);n=int(y.sum());v=int(p.sum())
    require(0<n<=2_000_000 and v<=4_000_000,'Reference/foreground diagnostic budget')
    truth=np.column_stack(np.nonzero(y));hits=p[tuple(truth.T)];tp=int(hits.sum())
    def world_center(coords):return (a[:3,:3]@coords.mean(0)+a[:3,3]).tolist()
    result=dict(reference_voxels=n,predicted_voxels=v,true_positive=tp,false_negative=n-tp,false_positive=v-tp,
        dice=2*tp/(n+v),recall=tp/n,precision=tp/v if v else None,volume_ratio=v/n,
        reference_volume_ml=n*abs(np.linalg.det(a[:3,:3]))/1000,
        reference_extent_mm=((truth.max(0)-truth.min(0)+1)*spacing).tolist(),
        reference_center_world=world_center(truth),spacing_mm=spacing.tolist(),
        source_reference_boundary_faces=[(truth.min(0)==0).tolist(),(truth.max(0)==np.array(y.shape)-1).tolist()],
        missing_review_center=np.median(truth[~hits] if (~hits).any() else truth,axis=0).astype(int).tolist(),
        box=None,box_coverage=None,scan_fraction=None,outside_faces=None,center_offset_mm=None,
        components=0,largest_component_fraction=None,fp_only_components=0,fp_only_component_voxels=0,
        margin_mm=10.,roi_diagnostic_pass=False,scope='native grid; voxel-axis rounded10mm; no policy selection')
    if not v:return result
    coords=np.column_stack(np.nonzero(p));pad=np.ceil(10/spacing).astype(int)
    lo=np.maximum(0,coords.min(0)-pad);hi=np.minimum(p.shape,coords.max(0)+1+pad)
    inside=((truth>=lo)&(truth<hi)).all(1);coverage=float(inside.mean());fraction=float(np.prod(hi-lo)/p.size)
    labels,count=ndimage.label(p,structure=ndimage.generate_binary_structure(3,1))
    sizes=np.bincount(labels.ravel(),minlength=count+1)[1:]
    overlaps=np.bincount(labels[tuple(truth.T)],minlength=count+1)[1:]
    result.update(box=[lo.tolist(),hi.tolist()],box_coverage=coverage,scan_fraction=fraction,
        realized_unclipped_margin_mm=(pad*spacing).tolist(),
        outside_faces=dict(lower=(truth<lo).mean(0).tolist(),upper=(truth>=hi).mean(0).tolist(),note='native array axes; face fractions overlap'),
        center_offset_mm=float(np.linalg.norm(np.array(world_center(coords))-result['reference_center_world'])),
        components=int(count),largest_component_fraction=float(sizes.max()/v),
        fp_only_components=int((overlaps==0).sum()),fp_only_component_voxels=int(sizes[overlaps==0].sum()),
        roi_diagnostic_pass=bool(coverage>=.995 and fraction<=.25))
    return result


def mapped_source_box(box,*,processed_shape,processed_affine,source_shape,source_affine):
    """Map the SAME processed voxel-edge box to a clipped native crop; padding is not scan.

    Supports signed axis permutations/scales, not oblique/sheared relative grids. It rounds
    outward to native voxel edges. No target, margin change, model policy or mask is consulted.
    """
    from itertools import product
    ps=np.asarray(processed_shape);ss=np.asarray(source_shape)
    require(ps.shape==ss.shape==(3,) and all(np.issubdtype(x.dtype,np.integer) and (x>0).all() for x in (ps,ss)),'Positive integer shapes required')
    require(int(np.prod(ps))<=8_000_000 and int(np.prod(ss))<=64_000_000,'Mapping grid budget')
    pa=np.asarray(processed_affine,dtype=float);sa=np.asarray(source_affine,dtype=float)
    require(all(a.shape==(4,4) and np.isfinite(a).all() and np.allclose(a[3],[0,0,0,1]) for a in (pa,sa)),'Invalid mapping affine')
    require(abs(np.linalg.det(sa[:3,:3]))>1e-12 and abs(np.linalg.det(pa[:3,:3]))>1e-12,'Singular mapping affine')
    matrix=np.linalg.solve(sa,pa);nonzero=np.abs(matrix[:3,:3])>1e-6
    require((nonzero.sum(0)==1).all() and (nonzero.sum(1)==1).all(),'Unsupported oblique relative grids')
    if box is None:return dict(schema_version='source-crop-geometry-v1',box=None,scan_fraction=None,padded_tensor_fraction=None)
    b=np.asarray(box);require(b.shape==(2,3) and np.issubdtype(b.dtype,np.integer) and (b[0]>=0).all() and (b[1]<=ps).all() and (b[1]>b[0]).all(),'Invalid processed box')
    corners=np.array(list(product(*zip(b[0]-.5,b[1]-.5))))
    native=corners@matrix[:3,:3].T+matrix[:3,3]
    # Snap tiny affine roundoff at integer voxel edges before outward rounding.
    edges=np.stack([native.min(0),native.max(0)])+.5
    edges=np.where(np.isclose(edges,np.rint(edges),rtol=0,atol=1e-6),np.rint(edges),edges)
    lo=np.maximum(0,np.minimum(ss,np.floor(edges[0]).astype(int)));hi=np.maximum(0,np.minimum(ss,np.ceil(edges[1]).astype(int)))
    fraction=float(np.prod(np.maximum(0,hi-lo))/np.prod(ss))
    return dict(schema_version='source-crop-geometry-v1',box=[lo.tolist(),hi.tolist()],scan_fraction=fraction,
        padded_tensor_fraction=float(np.prod(b[1]-b[0])/np.prod(ps)),
        semantics='same processed voxel-edge region, outward native rounding, clipped to acquired source grid')
