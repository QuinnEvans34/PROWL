"""Explicit full-range int8 binary annotation decoding; never a generic threshold."""
import json
from pathlib import Path
import nibabel as nib
import numpy as np
from scripts.qualify_annotation_units import digest


def decode_endpoints(raw, slope, intercept):
    raw = np.asarray(raw)
    if (raw.dtype != np.dtype('int8') or slope != float(np.float32(1/255))
            or intercept != float(np.float32(128/255))):
        raise ValueError('Not canonical full-range int8 binary encoding')
    if not np.isin(raw, [-128, 127]).all():
        raise ValueError('Intermediate annotation codes are ambiguous')
    return (raw == 127).astype(np.uint8)


def derive(ct_path, annotation_path, ct_sha, annotation_sha, output):
    ct_path, annotation_path, output = map(Path, (ct_path, annotation_path, output))
    receipt_path=output.with_name(output.name+'.receipt.json')
    if output.exists() or receipt_path.exists():
        raise ValueError('Output must be new')
    for p,h in [(ct_path,ct_sha),(annotation_path,annotation_sha)]:
        if p.stat().st_size > 64*1024**2 or digest(p)!=h:
            raise ValueError('Source identity or compressed budget')
    ct,source=nib.load(ct_path),nib.load(annotation_path)
    for img in (ct,source):
        n=int(np.prod(img.shape))
        if (not isinstance(img,nib.Nifti1Image) or len(img.shape)!=3 or n>32_000_000
                or n*max(4,img.get_data_dtype().itemsize)+352>128*1024**2
                or img.header.get_xyzt_units()[0]!='mm' or not np.isfinite(img.affine).all()
                or abs(np.linalg.det(img.affine[:3,:3]))<1e-12):
            raise ValueError('Unsupported geometry/units/budget')
    if ct.shape!=source.shape or not np.array_equal(ct.affine,source.affine):
        raise ValueError('CT and annotation grids differ')
    slope,inter=source.dataobj.slope,source.dataobj.inter
    # Check encoding before allocating; never decode this scaled mask to float64.
    if (source.get_data_dtype()!=np.dtype('int8') or slope!=float(np.float32(1/255))
            or inter!=float(np.float32(128/255))):
        raise ValueError('Unsupported annotation encoding')
    raw=source.dataobj.get_unscaled()
    binary=decode_endpoints(raw,slope,inter)
    header=source.header.copy();header.set_data_dtype(np.uint8);header.set_slope_inter(1,0)
    result=nib.Nifti1Image(binary,source.affine,header)
    result.header.set_slope_inter(1,0)
    with output.open('xb'):
        pass
    nib.save(result,output)
    restored=nib.load(output)
    if (restored.dataobj.slope!=1 or restored.dataobj.inter!=0
            or not np.array_equal(restored.affine,source.affine)
            or not np.array_equal(np.asanyarray(restored.dataobj),binary)):
        raise ValueError('Binary export verification failed')
    if digest(ct_path)!=ct_sha or digest(annotation_path)!=annotation_sha:
        raise ValueError('Inputs changed during derivation')
    receipt=dict(schema='full-range-int8-binary-annotation-v1',ct_sha256=ct_sha,
                 source_sha256=annotation_sha,derived_sha256=digest(output),
                 raw_background=-128,raw_foreground=127,slope=slope,intercept=inter,
                 decoded_background=-128*slope+inter,decoded_foreground=127*slope+inter,
                 foreground_voxels=int(binary.sum()),background_voxels=int(binary.size-binary.sum()),
                 foreground_locations_preserved=True,spatial_resampling=False,threshold_used=False,
                 shape=list(source.shape),affine=source.affine.tolist())
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
