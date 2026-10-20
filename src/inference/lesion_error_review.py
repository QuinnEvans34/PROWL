"""Describe retained class errors without changing predictions or thresholds."""
import numpy as np
from scipy import ndimage


def review_errors(prediction, pancreas, lesion, affine):
    p,a,l=map(np.asarray,(prediction,pancreas,lesion));affine=np.asarray(affine,dtype=float)
    if (p.ndim!=3 or min(p.shape)<1 or p.size>32_000_000 or a.shape!=p.shape or l.shape!=p.shape
            or not np.isin(p,[0,1,2]).all() or not np.isin(a,[0,1]).all() or not np.isin(l,[0,1]).all()):
        raise ValueError('Invalid aligned class/reference grids')
    if (affine.shape!=(4,4) or not np.isfinite(affine).all()
            or not np.array_equal(affine[3],[0,0,0,1]) or abs(np.linalg.det(affine[:3,:3]))<1e-12):
        raise ValueError('Invalid physical geometry')
    target=np.where(l,2,a).astype(np.uint8)
    confusion=np.bincount((target*3+p).ravel(),minlength=9).reshape(3,3)
    false=(p==2)&(l==0);miss=(l>0)&(p!=2)
    ids,n=ndimage.label(l,structure=np.ones((3,3,3)))
    if n>4096:raise ValueError('Component diagnostic budget')
    components=[]
    objects=ndimage.find_objects(ids)
    for i,box in enumerate(objects,1):
        member=ids[box]==i;local=p[box]
        counts=[int(np.count_nonzero(member&(local==k))) for k in range(3)]
        components.append(dict(id=i,voxels=sum(counts),predicted_as_background=counts[0],
            predicted_as_pancreas=counts[1],predicted_as_lesion=counts[2],
            box=[[s.start for s in box],[s.stop for s in box]]))
    v=float(abs(np.linalg.det(affine[:3,:3]))/1000)
    count=int(np.count_nonzero(l))
    return dict(schema='retained-lesion-error-review-v1',confusion_rows_reference_cols_prediction=confusion.tolist(),
        class_order=['background','pancreas_parenchyma','lesion'],voxel_ml=v,
        reference_lesion_voxels=count,predicted_lesion_voxels=int((p==2).sum()),
        true_positive=int(confusion[2,2]),false_negative=int(miss.sum()),
        missed_as_pancreas=int(confusion[2,1]),missed_as_background=int(confusion[2,0]),
        lesion_recall=float(confusion[2,2]/count) if count else None,
        false_positive=int(false.sum()),false_positive_inside_provided_pancreas=int((false&(a>0)).sum()),
        false_positive_outside_provided_pancreas=int((false&(a==0)).sum()),
        reference_lesion_components=components,release_qualified=False)
