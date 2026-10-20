"""Native face/slab overlap diagnostics; no coverage acceptance or mask changes."""
import numpy as np


def audit_faces(prediction, reference, roi):
    p,r,b=np.asarray(prediction),np.asarray(reference),np.asarray(roi)
    if (p.ndim!=3 or min(p.shape)<1 or p.size>32_000_000 or r.shape!=p.shape
            or not np.isin(p,[0,1,2]).all() or not np.isin(r,[0,1]).all()):
        raise ValueError('Invalid prediction/reference grids')
    if (b.shape!=(2,3) or not np.issubdtype(b.dtype,np.integer)
            or (b[0]<0).any() or (b[1]>p.shape).any() or (b[1]<=b[0]).any()):
        raise ValueError('Invalid region')
    result={'schema':'native-reference-face-audit-v1','shape':list(p.shape),'native_box':b.tolist(),
            'reference_role':'provided pancreas; also used to select inference region',
            'release_qualified':False,'surfaces':{}}
    for name,box in [('ct',np.array([[0,0,0],p.shape])),('crop',b)]:
        faces={};unique=np.zeros(p.shape,dtype=bool)
        for axis in range(3):
            for side in ['low','high']:
                plane=int(box[0,axis] if side=='low' else box[1,axis]-1)
                sl=[slice(int(box[0,i]),int(box[1,i])) for i in range(3)];sl[axis]=plane
                unique[tuple(sl)]=True
                slabs=[]
                for d in range(min(4,int(box[1,axis]-box[0,axis]))):
                    sl[axis]=plane+(d if side=='low' else -d)
                    x,y=p[tuple(sl)],r[tuple(sl)]>0
                    slabs.append(dict(distance_voxels=d,plane=int(sl[axis]),reference_voxels=int(y.sum()),
                        prediction_union_voxels=int((x>0).sum()),pancreas_voxels=int((x==1).sum()),
                        lesion_voxels=int((x==2).sum()),union_reference_overlap=int(((x>0)&y).sum()),
                        union_outside_reference=int(((x>0)&~y).sum()),reference_missed=int(((x==0)&y).sum())))
                faces[f'{axis}_{side}']=dict(axis=axis,side=side,plane=plane,
                    coincides_with_ct_face=plane in (0,p.shape[axis]-1),inward_planes=slabs)
        result['surfaces'][name]=dict(faces=faces,unique_contact=dict(
            prediction_union_voxels=int(((p>0)&unique).sum()),reference_voxels=int(((r>0)&unique).sum()),
            union_reference_overlap=int(((p>0)&(r>0)&unique).sum()),
            lesion_voxels=int(((p==2)&unique).sum())))
    return result
