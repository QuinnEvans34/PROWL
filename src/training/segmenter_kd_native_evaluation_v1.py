"""Teacher-free native evaluation with complete, report-bound component evidence."""
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
from src.data.manifest_records import canonical,digest
from src.training.pants_native_evaluation import native_metrics
from src.training.native_error_review_v1 import component_table,POLICY
from src.training.segmenter_physical_windows_session_v1 import predict_native
from src.data.segmenter_native_windows_v1 import orient
from src.training.segmenter_pancreas_region_executor_v1 import write_report

def components(prediction,lesion,affine):
    if prediction.shape!=lesion.shape or lesion.ndim!=3 or not np.isin(lesion,[0,1]).all() or not np.isin(prediction,[0,1,2]).all():raise ValueError('Invalid native component grids/codes')
    voxel=abs(float(np.linalg.det(np.asarray(affine)[:3,:3])))
    if not np.isfinite(voxel) or voxel<=0:raise ValueError('Invalid native voxel volume')
    labels,count=ndimage.label(lesion,structure=np.ones((3,3,3)))
    sizes=np.bincount(labels.ravel());hits=set(np.unique(labels[prediction==2]))
    return [dict(component_id=i,voxels=int(sizes[i]),volume_mm3=int(sizes[i])*voxel,detected=i in hits) for i in range(1,count+1)]

def evaluate(session,provider,name,progress):
    case=provider.load(name,role='validation',operation='evaluator')
    local,reconstruction=predict_native(session.raw,case['image'],case['geometry'],progress=progress)
    parent=case['parent_geometry'];codes=np.zeros(parent['shape'],np.uint8)
    slices=tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
    if local.shape!=codes[slices].shape:raise ValueError('ROI reconstruction shape')
    codes[slices]=local;codes=orient(codes,parent,inverse=True)
    reconstruction.update(region_low=case['region_low'],region_high=case['region_high'],outside_region='background',assistance='provided_pancreas_mask',lesion_guided_region=False)
    affine=np.asarray(parent['source_affine'])
    evidence=dict(case_id=name,target_sha256=case['source_sha256']['lesion'],geometry_sha256=digest(canonical(dict(shape=list(codes.shape),affine=affine.tolist()))),components=components(codes,case['original_lesion'],affine))
    return dict(case_id=name,step=session.step,scope='native_provided_pancreas_region_development',reconstruction=reconstruction,metrics=native_metrics(codes,case['original_pancreas'],case['original_lesion'],affine),component_evidence=evidence)

def bind_sidecar(report_path):
    path=Path(report_path);payload=path.read_bytes();report=json.loads(payload)
    sidecar=dict(version='native-components-1',report_sha256=digest(payload),matching=POLICY['component_matching'],cases=[r['component_evidence'] for r in report['cases']])
    component_table(sidecar,report,digest(payload))
    output=path.with_name(path.stem+'-components.json');write_report(output,sidecar)
    return output
