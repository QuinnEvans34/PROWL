"""CPU metadata/synthetic diagnosis; no CT decoding, model load or inference."""
import argparse
import ast
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import nibabel as nib
import SimpleITK as sitk


def teacher_grid(parent, *, preserve_centres=False):
    affine=np.asarray(parent['source_affine'],float);shape=np.asarray(parent['source_shape'])
    transform=nib.orientations.ornt_transform(nib.orientations.io_orientation(affine),nib.orientations.axcodes2ornt(('R','A','I')))
    oriented=affine@nib.orientations.inv_ornt_aff(transform,shape)
    size=shape[np.argsort(transform[:,0])];spacing=np.linalg.norm(oriented[:3,:3],axis=0)
    direction=oriented[:3,:3]/spacing
    for target in (np.array([1.,1.,spacing[2]]),np.ones(3)):
        extent=(size-1)*spacing/target
        size=np.ceil(extent-1e-9).astype(int)+1 if preserve_centres else np.rint(size*spacing/target).astype(int)
        spacing=target
    result=oriented.copy();result[:3,:3]=direction*spacing
    reverse=np.eye(4)[:,[2,1,0,3]]
    return dict(shape=size[::-1].tolist(),affine=(result@reverse).tolist())


def coverage(teacher,native):
    matrix=np.linalg.solve(np.asarray(teacher['affine']),np.asarray(native['affine']))
    corners=np.array(list(itertools.product(*[(0,n-1) for n in native['shape']]))).T
    coordinates=matrix[:3,:3]@corners+matrix[:3,3,None]
    lo=coordinates.min(axis=1);hi=coordinates.max(axis=1);shape=np.array(teacher['shape'])
    return dict(min_indices=lo.tolist(),max_indices=hi.tolist(),teacher_shape=shape.tolist(),
        beyond_boundary_cells_voxels=np.maximum(np.maximum(-.5-lo,hi-(shape-.5)),0).tolist(),
        covered=bool(np.all(lo>=-.5-1e-5) and np.all(hi<=shape-.5+1e-5)))


def interpolation_probe(source):
    """Execute only the pinned pure upstream resampling function on invented data."""
    tree=ast.parse(source.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='ResampleXYZAxis')
    scope={'sitk':sitk};exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),scope)
    data=np.zeros((5,7,9),np.float32);data[:,:,3]=100;data[:,3,:]+=50
    image=sitk.GetImageFromArray(data);image.SetSpacing((.7421879768371582,.7421879768371582,1.25))
    outputs=[sitk.GetArrayFromImage(scope['ResampleXYZAxis'](image,interp=m)) for m in (sitk.sitkLinear,sitk.sitkNearestNeighbor,sitk.sitkBSpline)]
    return dict(upstream_interpolation_arguments_produce_identical_outputs=all(np.array_equal(outputs[0],a) for a in outputs[1:]),
                upstream_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),synthetic_only=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve existing report')
    metadata=a.base/'metadata-received-01';cases=json.loads((metadata/'pilot-order.json').read_text());rows=[]
    for case in cases:
        small=json.loads((metadata/'native-region/members'/ (case+'.json')).read_text())
        old=teacher_grid(small['parent_geometry']);candidate=teacher_grid(small['parent_geometry'],preserve_centres=True)
        rows.append(dict(case_id=case,current=coverage(old,small['geometry']),candidate=coverage(candidate,small['geometry'])))
    result=dict(cases=rows,interpolation=interpolation_probe(a.base/'teacher/source/rsuper_train/dataset_conversion/utils.py'),
        candidate_status='metadata projection only; not approved preprocessing or model quality',model_runs=0,decoded_patient_voxel_reads=0)
    with a.output.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
