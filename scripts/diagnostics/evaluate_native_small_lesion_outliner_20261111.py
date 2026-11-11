"""Pair frozen native STU-Net masks with the existing CPU outliner."""
import argparse
import gc
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import torch

from scripts.diagnostics import replay_mac_disagreement_refiner_20261111 as replay
from scripts.diagnostics import run_mac_disagreement_verifier_20261111 as io
from src.inference.standard_segmentation_postprocess_v1 import postprocess
from src.operations.mac_teacher_supervision_v3 import run
from src.training.pants_native_evaluation import native_metrics

CAP = 1500
STEP = 32000
CHECKPOINT_SHA = '6de354d26cad3672e14998e5ad90e95603dbd69ef47125abb2f8441597574754'
REPORT_SHA = 'b2f0c6eb08beb497e472085b24633e1f05e8a2cef15f1054ab8e8362a0638f99'
MIN_MM3 = 10.0
MAX_MM3 = 1000.0
POLICY = ROOT/'configs/inference/segmentation-postprocessing-v1.json'
read, sha, write = io.read, io.sha, io.write


def safety():
    from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety as platform
    if not os.path.ismount('/Volumes/PROWL-Data'):
        raise ValueError('Approved source volume absent')
    platform()


def unpack_native(member, shape):
    with np.load(member, allow_pickle=False) as data:
        if set(data.files) != {'packed','shape'} or data['shape'].tolist() != shape:
            raise ValueError('Mask shape or encoding differs')
        packed = data['packed']
        size = int(np.prod(shape))
        if (packed.dtype != np.uint8 or packed.ndim != 1 or len(packed) != (size+1)//2
                or (size%2 and packed[-1]>>4)):
            raise ValueError('Malformed packed mask')
        flat = np.empty(size,dtype=np.uint8)
        flat[::2] = packed & 15
        flat[1::2] = packed[:size//2] >> 4
        if flat.max() > 2:
            raise ValueError('Unexpected mask classes')
        return flat.reshape(shape)


def verify_manifest(path, cases):
    data = read(path)
    if data.get('step') != STEP or data.get('schema') != 'prowl.stunet.native-mask-export.v1':
        raise ValueError('Expected native 32k manifest')
    checkpoint = data.get('checkpoint_sha256','')
    if checkpoint != CHECKPOINT_SHA or checkpoint != data.get('independent_checkpoint_sha256'):
        raise ValueError('Missing independent checkpoint identity')
    report_path = path.parent/'native-32000.json'
    if sha(report_path) != REPORT_SHA or data['report_sha256'] != REPORT_SHA:
        raise ValueError('Reference report binding differs')
    report = read(report_path)
    if report.get('step') != STEP or report['summary']['positive'] != 36 or report['summary']['empty'] != 34:
        raise ValueError('Report step or cohort differs')
    rows = {r['case_id']:r for r in report['cases']}
    members = {r['case_id']:r for r in data['cases']}
    if (len(rows) != 70 or len(data['cases']) != 70 or len(report['cases']) != 70
            or set(members) != set(rows) or set(rows) != {r['case_id'] for r in cases}):
        raise ValueError('Exact 70-member cohort required')
    for case in cases:
        name = case['case_id']
        member = members[name]
        source = {k:v['sha256'] for k,v in case['sources'].items()}
        if (member['source_sha256'] != source or member['native_shape'] != case['native_shape']
                or member['native_affine'] != case['native_affine'] or member['mask_file'] != name+'.npz'
                or rows[name]['gaps'] != 0 or member['tiles'] != rows[name]['tiles']):
            raise ValueError('Native geometry, source, or coverage differs')
        if sha(path.parent/member['mask_file']) != member['mask_sha256']:
            raise ValueError('Mask archive digest differs')
    return data,rows,members,report


def native_candidates(prediction, affine):
    labels,count = ndimage.label(prediction==2,structure=replay.saved.STRUCTURE)
    sizes = np.bincount(labels[prediction==2],minlength=count+1)
    voxel_mm3 = abs(float(np.linalg.det(affine[:3,:3])))
    eligible = np.flatnonzero((sizes*voxel_mm3>=MIN_MM3)&(sizes*voxel_mm3<MAX_MM3))
    boxes = ndimage.find_objects(labels,max_label=count)
    return labels,eligible,boxes,voxel_mm3


def center_in_component(points, basis):
    distance = np.square((points-points.mean(0)) @ basis.T).sum(axis=1)
    return points[distance.argmin()]


def refine(case, raw, model):
    shape = case['native_shape']
    affine = np.asarray(case['native_affine'])
    labels,eligible,boxes,voxel_mm3 = native_candidates(raw,affine)
    if not len(eligible):
        return raw,raw,0,0
    source = case['sources']['ct']
    if sha(source['path']) != source['sha256']:
        raise ValueError('CT hash differs')
    image = nib.load(source['path'])
    if list(image.shape) != shape or not np.allclose(image.affine,affine,atol=1e-5,rtol=0):
        raise ValueError('CT shape or affine differs')
    g = replay.geometry(shape,affine)
    to_source = nib.orientations.inv_ornt_aff(np.asarray(g['forward']),shape)
    to_ras = np.linalg.inv(to_source)
    baseline = np.flatnonzero(raw.reshape(-1)==2)
    proposed = raw.copy().reshape(-1)
    contour_trim = raw.copy().reshape(-1)
    touched = 0
    prior_replacements = []
    for component in eligible:
        box = boxes[component-1]
        points = np.argwhere(labels[box]==component)+[s.start for s in box]
        original = np.ravel_multi_index(points.T,shape)
        native_center = center_in_component(points,affine[:3,:3])
        canonical = nib.affines.apply_affine(to_ras,native_center).astype(int)
        window = replay.crop_record(g['shape'],g['affine'],canonical,replay.SIZE)
        x,support = replay.ct_crop(image,g,window,to_source)
        with torch.inference_mode():
            probability = model(torch.from_numpy(x)[None])[0,0].sigmoid().numpy()
        if not np.isfinite(probability).all():
            raise ValueError('Nonfinite refiner output')
        patch_seed = nib.affines.apply_affine(to_ras,points).astype(int)-window['origin']
        if ((patch_seed<0)|(patch_seed>=replay.SIZE)).any():
            continue  # preserve original if its full extent is outside the crop
        others = baseline[~np.isin(baseline,original)]
        replacement = replay.component_at_seed(probability,support,patch_seed,window,to_source,shape,
                                               others,.50,voxel_mm3)
        if not len(replacement) or np.any((proposed[replacement]==2)&~np.isin(replacement,original)):
            continue
        # Keep previously predicted pancreas unchanged in both lesion edits.
        replacement = replacement[raw.reshape(-1)[replacement]!=1]
        if not len(replacement) or not np.isin(replacement,original).any():
            continue
        shared = original[np.isin(original,replacement)]
        # Restrict to a connected component seeded at the original lesion after
        # the pancreas protection mask. Reject split/merged shape edits.
        other_components = np.concatenate((others,*prior_replacements))
        if (not connected(replacement,shape) or not connected(shared,shape)
                or touches(replacement,other_components,shape)):
            continue
        proposed[original] = 0
        proposed[replacement] = 2
        contour_trim[original] = 0
        contour_trim[shared] = 2
        touched += 1
        prior_replacements.append(replacement)
    return proposed.reshape(shape),contour_trim.reshape(shape),len(eligible),touched


def touches(candidate, other, shape):
    if not len(other):
        return False
    xyz = lambda indices: np.column_stack(np.unravel_index(indices,shape))
    nearest = cKDTree(xyz(other)).query(xyz(candidate),p=np.inf,workers=1)[0]
    return bool((nearest<=1).any())


def connected(indices, shape):
    points = np.column_stack(np.unravel_index(indices,shape))
    points -= points.min(0)
    mask = np.zeros(points.max(0)+1,dtype=bool)
    mask[tuple(points.T)] = True
    return ndimage.label(mask,structure=replay.saved.STRUCTURE)[1] == 1


def arm_metrics(prediction, pancreas, lesion, components, affine):
    m = native_metrics(prediction,pancreas,lesion,affine)
    m['hit_ids'] = [int(k) for k in np.unique(components[prediction==2]) if k]
    return m


def score(case, raw, expected, model):
    shape = case['native_shape']
    affine = np.asarray(case['native_affine'])
    voxel_mm3 = abs(float(np.linalg.det(affine[:3,:3])))
    expanded,trimmed,eligible,changed = refine(case,raw,model)
    # All predictions and fixed postprocessing are decided independently of truth.
    policies = {}
    for name,mask in (('baseline',raw),('replace',expanded),('trim',trimmed)):
        filtered,details = postprocess(mask,affine)
        policies[name+'_raw'] = (mask,None)
        policies[name+'_near5'] = (filtered,details['applied'])
    lesion = replay.open_reference(case['sources']['lesion'],shape,affine)
    pancreas = replay.open_reference(case['sources']['pancreas'],shape,affine)
    components,count = ndimage.label(lesion,structure=replay.saved.STRUCTURE)
    sizes = np.bincount(components[lesion!=0],minlength=count+1)
    small = [i for i in range(1,count+1) if sizes[i]*voxel_mm3<1000]
    arms = {}
    for name,(mask,applied) in policies.items():
        metrics = arm_metrics(mask,pancreas,lesion,components,affine)
        if name=='baseline_raw' and {k:v for k,v in metrics.items() if k!='hit_ids'} != expected['metrics']:
            raise ValueError('Reconstructed native 32k mask failed exact metric replay')
        arms[name] = dict(metrics,policy_applied=applied)
    if arms['trim_raw']['lesion']['predicted_voxels'] > arms['baseline_raw']['lesion']['predicted_voxels']:
        raise ValueError('Trim arm expanded')
    return dict(case_id=case['case_id'],small_ids=small,eligible=eligible,changed=changed,arms=arms)


def summarize(rows):
    from statistics import mean
    result = {}
    if len(rows)!=70 or len({r['case_id'] for r in rows})!=70:
        raise ValueError('Incomplete comparison')
    for key in rows[0]['arms']:
        controls = key.split('_')[1]
        baseline_key = 'baseline_'+controls
        pos = [r for r in rows if r['arms'][key]['reference_positive']]
        empty = [r for r in rows if not r['arms'][key]['reference_positive']]
        if (len(pos),len(empty))!=(36,34):
            raise ValueError('Positive and empty cohort differs')
        def fp(m):
            return m['lesion']['predicted_voxels']-m['lesion']['true_positive']
        def fp_ml(rs):
            return sum(fp(r['arms'][key])*r['arms'][key]['voxel_mm3']/1000 for r in rs)
        result[key] = dict(dice=mean(r['arms'][key]['lesion']['dice'] for r in pos),
            recall=mean(r['arms'][key]['lesion']['true_positive']/r['arms'][key]['lesion']['target_voxels'] for r in pos),
            pancreas_dice=mean(r['arms'][key]['pancreas']['dice'] for r in rows),
            small_total=sum(len(r['small_ids']) for r in pos),
            small_hits=sum(len(set(r['small_ids'])&set(r['arms'][key]['hit_ids'])) for r in pos),
            empty_alarms=sum(r['arms'][key]['false_alarm_any'] for r in empty),
            total_fp_ml=fp_ml(rows),empty_fp_ml=fp_ml(empty),
            cases_with_more_fp=sum(fp(r['arms'][key])>fp(r['arms'][baseline_key]) for r in rows),
            lost_reference_hits=sum(len(set(r['arms'][baseline_key]['hit_ids'])-set(r['arms'][key]['hit_ids']))
                                    for r in rows))
    return result


def worker(manifest,directory,expected):
    req = read(directory/'request.json')
    if sha(directory/'request.json')!=expected or any(sha(p)!=h for p,h in req['pins'].items()):
        raise ValueError('Frozen comparison pins differ')
    cases,_ = replay.saved.admitted_cases()
    package,controls,members,report = verify_manifest(manifest,cases)
    model,refiner_sha = replay.verified_checkpoint(cases)
    rows = []
    with (directory/'cases.jsonl').open('x') as journal:
        for case in cases:
            safety()
            name=case['case_id']
            member=members[name]
            raw=unpack_native(manifest.parent/member['mask_file'],case['native_shape'])
            row=score(case,raw,controls[name],model)
            rows.append(row)
            journal.write(json.dumps(row,allow_nan=False)+'\n')
            journal.flush()
            print(json.dumps(dict(scans=len(rows),eligible=row['eligible'],changed=row['changed'])),flush=True)
            gc.collect()
        os.fsync(journal.fileno())
    result=summarize(rows)
    if not math.isclose(result['baseline_raw']['dice'],report['summary']['lesion_dice'],rel_tol=0,abs_tol=1e-12):
        raise ValueError('Aggregate 32k baseline differs')
    write(directory/'result.json',dict(step=STEP,request_sha256=expected,checkpoint_sha256=package['checkpoint_sha256'],
         refiner_sha256=refiner_sha,metrics=result,cases=len(rows),rows=rows))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path)
    p.add_argument('directory',type=Path)
    p.add_argument('--worker')
    a=p.parse_args()
    if a.worker:
        worker(a.manifest,a.directory,a.worker)
        return
    safety()
    cases,_=replay.saved.admitted_cases()
    verify_manifest(a.manifest,cases)
    a.directory.mkdir()
    files=[Path(__file__),Path(replay.__file__),POLICY,replay.PROOF,a.manifest,a.manifest.parent/'native-32000.json']
    write(a.directory/'request.json',dict(pins={str(f.resolve()):sha(f) for f in files},step=STEP,
          scope='70 exposed development scans; no training or candidate reference access',
          raw_and_fixed_5mm=True,threshold=.50,min_component_mm3=MIN_MM3,max_component_mm3=MAX_MM3,
          rss_bytes=4*replay.GIB,wall_seconds=CAP,started_unix=time.time()))
    digest=sha(a.directory/'request.json')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
             PYTHONDONTWRITEBYTECODE='1')
    if not run([sys.executable,__file__,str(a.manifest),str(a.directory),'--worker',digest],
               a.directory,seconds=CAP,rss_bytes=4*replay.GIB,tick=safety,env=env):
        raise SystemExit('Outliner comparison stopped. Preserve evidence.')
    resources=read(a.directory/'resources.json')
    if not resources['workers_reaped'] or resources['exit_code']!=0:
        raise ValueError('Worker cleanup not verified')
    write(a.directory/'closeout.json',dict(status='VERIFIED_COMPLETE',request_sha256=digest,
          result_sha256=sha(a.directory/'result.json'),resources=resources))


if __name__=='__main__':
    main()
