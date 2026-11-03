"""Offline component and contour descriptions, never crop selection or optimization."""
import numpy as np
from scipy import ndimage

def components(predicted,reference,affine):
    predicted=np.asarray(predicted,bool);reference=np.asarray(reference,bool)
    if predicted.shape!=reference.shape or predicted.ndim!=3:raise ValueError('Aligned masks required')
    voxel_ml=abs(float(np.linalg.det(np.asarray(affine)[:3,:3])))/1000
    result={}
    for key,mask,other in [('reference',reference,predicted),('predicted',predicted,reference)]:
        labels,n=ndimage.label(mask,structure=np.ones((3,3,3),np.uint8))
        sizes=np.bincount(labels.ravel(),minlength=n+1);hits=np.bincount(labels[other],minlength=n+1)
        boxes=ndimage.find_objects(labels);rows=[]
        for i,b in enumerate(boxes,1):
            rows.append(dict(component_id=i,voxels=int(sizes[i]),volume_ml=float(sizes[i]*voxel_ml),overlap_voxels=int(hits[i]),
                any_overlap=bool(hits[i]),overlap_fraction=float(hits[i]/sizes[i]),
                bounds_xyz_half_open=[[s.start,s.stop] for s in b],
                acquired_boundary_contact=any(s.start==0 or s.stop==mask.shape[k] for k,s in enumerate(b))))
        result[key]=rows
    result.update(connectivity=26,detection_definition='any shared voxel, descriptive; not IoU threshold or clinical detection',
        reference_count=len(result['reference']),reference_hit_count=sum(r['any_overlap'] for r in result['reference']),
        false_positive_components=sum(not r['any_overlap'] for r in result['predicted']))
    return result

def contour(predicted,reference,affine):
    """Physical voxel-center surface distances on orthogonal native acquisitions."""
    a=np.asarray(affine)[:3,:3];spacing=np.linalg.norm(a,axis=0);unit=a/spacing
    if not np.allclose(unit.T@unit,np.eye(3),atol=1e-5,rtol=0):
        return dict(state='not_computed_oblique_shear',reason='EDT spacing cannot represent shear')
    predicted=np.asarray(predicted,bool);reference=np.asarray(reference,bool)
    if not predicted.any() or not reference.any():return dict(state='undefined_empty_mask')
    structure=ndimage.generate_binary_structure(3,1)
    ps=predicted & ~ndimage.binary_erosion(predicted,structure=structure,border_value=0)
    rs=reference & ~ndimage.binary_erosion(reference,structure=structure,border_value=0)
    dt=ndimage.distance_transform_edt(~rs,sampling=spacing);pr=dt[ps];del dt
    dt=ndimage.distance_transform_edt(~ps,sampling=spacing);rp=dt[rs];del dt
    return dict(state='computed',definition='6-neighbor surface voxel centers; maximum directed95th percentiles; pooled mean',
        hausdorff95_mm=float(max(np.percentile(pr,95),np.percentile(rp,95))),
        mean_symmetric_surface_distance_mm=float((pr.sum()+rp.sum())/(pr.size+rp.size)))

def coverage(mask,region):
    n=int(np.count_nonzero(mask));inside=int(np.count_nonzero(np.asarray(mask,bool)&np.asarray(region,bool)))
    return dict(reference_voxels=n,inside_voxels=inside,outside_voxels=n-inside,fraction=inside/n if n else None)
