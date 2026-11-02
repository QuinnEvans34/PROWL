"""Saved-probability investigation only: no CT, weights, inference or new tolerances."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.segmenter_native_windows_v1 import tiles

BASE=Path('E:/PROWL/readiness/week05-cross-device-comparison-20261102-a01')
WIN=Path('E:/PROWL/readiness/week05-physical-qualification-20261102-a01')
MAC=Path('E:/PROWL/transfer/week05-mac-reference-20261102-a01/extracted/week05-mac-reference')
OUT=Path('E:/PROWL/readiness/week05-saved-difference-review-20261102-a01')


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()


def summary(values):
    x=np.asarray(values,dtype=float)
    return dict(min=float(x.min()),median=float(np.median(x)),max=float(x.max()))


def main():
    if OUT.exists():raise FileExistsError('Saved review already exists; inspect first')
    files=[BASE/'comparison.json',BASE/'probability-failures.json',WIN/'output/result.json',MAC/'output/result.json',
           WIN/'output/region-probabilities.npy',MAC/'output/region-probabilities.npy']
    pins={str(p):sha(p) for p in files};started=time.monotonic()
    if pins[str(BASE/'comparison.json')]!='fd7be15a0745e5acdec22fdf738c9b6d4a95be35dbaaf555fd56906ad083c974':raise ValueError('Original failure changed')
    original=json.loads(files[0].read_text());failures=json.loads(files[1].read_text())['rows']
    wreport=json.loads(files[2].read_text());mreport=json.loads(files[3].read_text())
    for root,report in ((WIN,wreport),(MAC,mreport)):
        if sha(root/'output/region-probabilities.npy')!=report['artifacts']['region-probabilities.npy']['sha256']:raise ValueError('Output changed')
    a=np.load(files[4],mmap_mode='r');b=np.load(files[5],mmap_mode='r')
    OUT.mkdir();(OUT/'request.json').write_text(json.dumps(dict(input_pins=pins,producer_sha256=sha(__file__),
        resource_limits=dict(seconds=600,rss_bytes=2*1024**3),inference=False,tolerance_change=False),indent=2))
    e=wreport['evidence'];grid=e['reconstruction']['physical_grid'];origins=tiles(grid['shape'])
    low=np.asarray(e['region_low']);parent=e['parent_geometry'];affine=np.asarray(e['geometry']['affine'])
    from nibabel.orientations import inv_ornt_aff
    to_source=inv_ornt_aff(np.asarray(parent['forward']),parent['source_shape'])
    rows=[];unique={};fail64=0;reverse64=0;global_min_margin=[1.,1.];max_stable_ratio=0.;sum_abs=0.;sum_sq=0.
    for start in range(0,a.shape[1],8):
        x=a[:,start:start+8].astype(np.float64);y=b[:,start:start+8].astype(np.float64)
        d=np.abs(x-y);fail64+=int((d>1e-5+1e-4*np.abs(y)).sum());reverse64+=int((d>1e-5+1e-4*np.abs(x)).sum())
        sum_abs+=float(d.sum());sum_sq+=float(np.square(d).sum())
        for k,v in enumerate((x,y)):
            ordered=np.sort(v,axis=0);margin=ordered[-1]-ordered[-2]
            global_min_margin[k]=min(global_min_margin[k],float(margin.min()))
        del x,y,d
    codes=np.argmax(b,axis=0).astype(np.uint8)
    for original_row in failures:
        idx=tuple(original_row['roi_index']);x=np.asarray(a[(slice(None),*idx)],dtype=float);y=np.asarray(b[(slice(None),*idx)],dtype=float)
        order=np.argsort(y);winner=int(order[-1]);margin=float(y[order[-1]]-y[order[-2]])
        eps=float(np.max(np.abs(x-y)));ratio=2*eps/margin if margin else None
        if ratio is not None:max_stable_ratio=max(max_stable_ratio,ratio)
        fine=np.asarray(grid['factors'])*(np.asarray(idx)+.5)-.5
        contributions=[o for o in origins if all(o[k]<=fine[k]<=min(o[k]+143,grid['shape'][k]-1) for k in range(3))]
        nearest_face=min(min(*(fine-np.asarray(o)),*(np.minimum(np.asarray(o)+143,np.asarray(grid['shape'])-1)-fine)) for o in contributions)
        parent_index=np.asarray(idx)+low;source_index=(to_source @ [*parent_index,1])[:3]
        world=(affine @ [*idx,1])[:3]
        row=dict(original_row,windows_all_classes=x.tolist(),mac_all_classes=y.tolist(),predicted_class=winner,
            top_probability=float(y.max()),top_two_margin=margin,twice_max_channel_error_over_margin=ratio,
            source_voxel=source_index.tolist(),world_mm=world.tolist(),contributing_tiles=len(contributions),
            nearest_contributing_tile_face_fine_voxels=float(nearest_face),
            roi_edge_distance_native_voxels=int(min(*idx,*(np.asarray(codes.shape)-1-idx))))
        rows.append(row);unique[idx]=row
    spacing=np.linalg.norm(affine[:3,:3],axis=0)
    for label in sorted(set(r['predicted_class'] for r in rows)):
        distance=ndimage.distance_transform_edt(codes==label,sampling=spacing)
        for idx,row in unique.items():
            if row['predicted_class']==label:row['nearest_other_predicted_class_center_mm']=float(distance[idx])
        del distance
    for row in rows:row['nearest_other_predicted_class_center_mm']=unique[tuple(row['roi_index'])]['nearest_other_predicted_class_center_mm']
    assert fail64==len(rows)==169
    result=dict(status='SAVED_REVIEW_COMPLETE_ORIGINAL_GATE_STILL_FAILED',original_comparison_sha256=pins[str(files[0])],
        input_pins=pins,seconds=time.monotonic()-started,inference_calls=0,labels_read=False,ct_read=False,
        arithmetic=dict(float64_rule_failures=fail64,reverse_reference_float64_failures=reverse64,
            global_mean_absolute_difference=sum_abs/a.size,global_rms_difference=float(np.sqrt(sum_sq/a.size))),
        unique_failure_voxels=len(unique),failed_values=len(rows),
        failure_roi_bounds=[np.min(list(unique),axis=0).tolist(),np.max(list(unique),axis=0).tolist()],
        failure_predicted_class_counts={str(k):sum(r['predicted_class']==k for r in unique.values()) for k in range(3)},
        failure_channel_probability=summary([r['mac'] for r in rows]),
        failure_top_confidence=summary([r['top_probability'] for r in unique.values()]),
        failure_top_two_margin=summary([r['top_two_margin'] for r in unique.values()]),
        maximum_twice_error_over_margin=max_stable_ratio,global_minimum_top_two_margin=global_min_margin,
        nearest_predicted_other_class_mm=summary([r['nearest_other_predicted_class_center_mm'] for r in unique.values()]),
        roi_edge_voxels=summary([r['roi_edge_distance_native_voxels'] for r in unique.values()]),
        tile_face_distance_fine_voxels=summary([r['nearest_contributing_tile_face_fine_voxels'] for r in unique.values()]),
        tile_contribution_counts=sorted(set(r['contributing_tiles'] for r in rows)),rows=rows)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Saved input changed during review')
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','input_pins')},indent=2))


if __name__=='__main__':main()
