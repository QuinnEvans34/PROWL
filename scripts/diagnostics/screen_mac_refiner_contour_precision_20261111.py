"""Compare frozen seed-anchored contour trims and same-scan FP budgets."""
import argparse
import gc
import json
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
from scripts.diagnostics import run_mac_disagreement_verifier_20261111 as previous
from src.operations.mac_teacher_supervision_v3 import run

read, sha, write = previous.read, previous.sha, previous.write
RULES = {
    'seed_intersection': (None, 0.0),
    'p65_r3': (.65, 3.0),
    'p75_r3': (.75, 3.0),
    'p85_r3': (.85, 3.0),
    'p75_r5': (.75, 5.0),
    'p90_r2': (.90, 2.0),
}
BUDGETS = (1, 2)
CAP = 600
MIN_MM3 = 10.0


def freeze(directory):
    replay.safety()
    if sha(previous.FROZEN) != sha(previous.FROZEN_BACKUP):
        raise ValueError('Saved refiner result differs from independent copy')
    receipt = previous.FROZEN.parent.parent/'verified/resources.json'
    resources = read(receipt)
    if not resources['success'] or not resources['workers_reaped']:
        raise ValueError('Refiner evidence is incomplete')
    inputs = [Path(__file__), Path(replay.__file__), Path(previous.__file__),
              previous.FROZEN, previous.FROZEN_BACKUP, receipt, replay.PROOF,
              replay.saved.CONFIG, replay.saved.OLDER/'request.json']
    directory.mkdir()
    write(directory/'request.json',dict(
        rules={name:list(pair) for name,pair in RULES.items()},swap_ratios=list(BUDGETS),
        minimum_volume_mm3=MIN_MM3,incumbent='verified 24k core',candidate=previous.ARM,
        elapsed_limit_s=CAP,rss_bytes=4*replay.GIB,
        objective='keep a new small lesion and raise Dice without any scan increasing FP',
        roles='same exposed development cases; no fitting, new checkpoint, or threshold changes',
        pins={str(p.resolve()):sha(p) for p in inputs}))


def verify(directory, expected):
    path = directory/'request.json'
    request = read(path)
    if sha(path) != expected or any(sha(p) != h for p,h in request['pins'].items()):
        raise ValueError('Frozen contour screen changed')
    if request['rules'] != {name:list(pair) for name,pair in RULES.items()}:
        raise ValueError('Contour grid differs')
    return request


def spatial_points(indices, shape):
    return np.column_stack(np.unravel_index(indices,shape))


def capture(case, old, current, base, pancreas, model, voxel_mm3):
    """Reconstruct only the accepted frozen refiner contour and its scores."""
    shape, affine = case['native_shape'], np.asarray(case['native_affine'])
    basis = affine[:3,:3]
    prompts, _ = replay.prompts(old,current,base,voxel_mm3)
    source = case['sources']['ct']
    if sha(source['path']) != source['sha256']:
        raise ValueError('CT source changed')
    image = nib.load(source['path'])
    if list(image.shape) != shape or not np.allclose(image.affine,affine,atol=1e-5,rtol=0):
        raise ValueError('CT geometry changed')
    g = replay.geometry(shape,affine)
    to_source = nib.orientations.inv_ornt_aff(np.asarray(g['forward']),shape)
    to_ras = np.linalg.inv(to_source)
    for number,(_,_,_,seed,center) in enumerate(prompts,1):
        canonical = nib.affines.apply_affine(to_ras,center).astype(int)
        window = replay.crop_record(g['shape'],g['affine'],canonical,replay.SIZE)
        x,support = replay.ct_crop(image,g,window,to_source)
        with torch.inference_mode():
            probability = model(torch.from_numpy(x)[None])[0,0].sigmoid().numpy()
        if not np.isfinite(probability).all():
            raise ValueError('Nonfinite refiner output')
        origin = np.asarray(window['origin'])
        patch = nib.affines.apply_affine(to_ras,spatial_points(seed,shape)).astype(int)-origin
        candidate = replay.component_at_seed(probability,support,patch,window,to_source,
                                             shape,base,.50,voxel_mm3)
        if len(candidate) and replay.within_pancreas_distance(candidate,pancreas,shape,basis):
            points = nib.affines.apply_affine(to_ras,spatial_points(candidate,shape)).astype(int)-origin
            values = probability[tuple(points.T)]
            if np.any(values < .5) or not support[tuple(points.T)].all():
                raise ValueError('Sparse contour replay differs')
            return candidate, seed, values, number
    raise ValueError('Prior selected contour could not be reproduced')


def trim(candidate, seed, values, shape, basis, voxel_mm3):
    points = spatial_points(candidate,shape)
    seeds = spatial_points(seed,shape)
    distance = cKDTree(seeds @ basis.T).query(points @ basis.T,workers=1)[0]
    anchor = np.isin(candidate,seed)
    output = {}
    for name,(threshold,radius) in RULES.items():
        selected = anchor if threshold is None else (values>=threshold)&(distance<=radius)
        indices = np.flatnonzero(selected)
        if not len(indices) or not anchor[indices].any():
            output[name] = candidate[:0]
            continue
        coordinates = points[indices]
        low = coordinates.min(0)
        local = coordinates-low
        mask = np.zeros(local.max(0)+1,dtype=bool)
        mask[tuple(local.T)] = True
        labels,_ = ndimage.label(mask,structure=replay.saved.STRUCTURE)
        ids = labels[tuple(local.T)]
        counts = np.bincount(ids[anchor[indices]])
        keep = indices[ids==counts.argmax()]
        output[name] = candidate[keep] if len(keep)*voxel_mm3>=MIN_MM3 else candidate[:0]
    return output


def decisions(trimmed, weak, pancreas, raw_pancreas, shape, basis):
    empty = np.empty(0,dtype=np.intp)
    arms = {}
    for name,add in trimmed.items():
        arms[name+'_raw_add'] = (add,empty,empty)
        allowed = len(add) and replay.within_pancreas_distance(add,pancreas,shape,basis)
        arms[name+'_near5_add'] = (add if allowed else empty,empty,empty)
        for ratio in BUDGETS:
            remove = weak[:ratio*len(add)]
            restored = remove[np.isin(remove,raw_pancreas)]
            augmented = np.concatenate((pancreas,restored))
            apply = (len(add)>0 and len(remove)==ratio*len(add)
                     and replay.within_pancreas_distance(add,augmented,shape,basis))
            arms[f'{name}_near5_swap{ratio}'] = (add,remove,restored) if apply else (empty,empty,empty)
    return arms


def count_mask(base, pancreas, labels, pan_truth, add, remove, restored):
    lesion = np.concatenate((base[~np.isin(base,remove)],add))
    removed_pan = add[np.isin(add,pancreas)]
    n = int(pan_truth.sum())
    p = len(pancreas)-len(removed_pan)+len(restored)
    t = int(pan_truth[pancreas].sum()-pan_truth[removed_pan].sum()+pan_truth[restored].sum())
    tp = int(np.count_nonzero(labels[add]))
    return dict(replay.saved.score(lesion,labels),added=len(add),removed=len(remove),
                added_tp=tp,added_fp=len(add)-tp,removed_tp=int(np.count_nonzero(labels[remove])),
                removed_fp=int(np.count_nonzero(labels[remove]==0)),pancreas_restored=len(restored),
                pancreas_relabelled=len(removed_pan),pancreas_dice=2*t/(n+p),
                added_false_component=bool(len(add) and not tp))


def process_case(case, row, receipt, old_receipt, model, evidence_dir):
    replay.safety()
    affine = np.asarray(case['native_affine'])
    shape = case['native_shape']
    basis = affine[:3,:3]
    voxel_mm3 = abs(float(np.linalg.det(basis)))
    old = replay.saved.archive(old_receipt['artifact'],replay.saved.unpack_12k,shape)
    current = replay.saved.archive(receipt['artifact'],replay.saved.unpack_24k,shape)
    index,tiers,distances,shells = replay.saved.core_support(current,affine,trim_levels=[2,3],grow_radii=[1.5])
    keep = (tiers>3)|(distances<=4)
    base = np.concatenate((index[keep],shells[1.5]))
    code = current.reshape(-1)
    raw_pancreas = np.flatnonzero((code<6)&((code&1)==1))
    pancreas = np.flatnonzero((code<4)&((code&1)==1))
    weak = keep & (tiers<=3) & (old.reshape(-1)[index]<2)
    ordering = np.lexsort((index[weak],-distances[weak],tiers[weak]))
    weak = index[weak][ordering]
    candidate,seed,values,forwards = capture(case,old,current,base,pancreas,model,voxel_mm3)
    trimmed = trim(candidate,seed,values,shape,basis,voxel_mm3)
    edits = decisions(trimmed,weak,pancreas,raw_pancreas,shape,basis)
    del old,current,code
    # Decisions above are frozen before reading annotations. The archive
    # records candidate coordinates and refiner values, with no CT or labels.
    path = evidence_dir/(case['case_id']+'.npz')
    with path.open('xb') as stream:
        np.savez_compressed(stream,candidate=candidate,seed=seed,score=values,shape=np.asarray(shape),
                            affine=affine)
        stream.flush()
        os.fsync(stream.fileno())
    with np.load(path,allow_pickle=False) as source:
        if any(not np.array_equal(source[k],v) for k,v in
               [('candidate',candidate),('seed',seed),('score',values),('affine',affine)]):
            raise ValueError('Saved contour did not replay')

    reference = replay.open_reference(case['sources']['lesion'],shape,affine)
    labels,count = ndimage.label(reference,structure=replay.saved.STRUCTURE)
    del reference
    labels = labels.reshape(-1)
    pan_truth = replay.open_reference(case['sources']['pancreas'],shape,affine).reshape(-1)
    pan_truth[labels>0] = 0
    empty = candidate[:0]
    baseline = count_mask(base,pancreas,labels,pan_truth,empty,empty,empty)
    original = count_mask(base,pancreas,labels,pan_truth,candidate,empty,empty)
    expected = row['arms'][previous.ARM]
    for observed,control in ((baseline,row['arms']['baseline']),(original,expected)):
        if any(observed[k]!=control[k] for k in ('p','t','hits','added','pancreas_relabelled','pancreas_dice')):
            raise ValueError('Frozen lesion or pancreas reference metrics differ')
    if count!=row['components'] or int(np.count_nonzero(labels))!=row['n']:
        raise ValueError('Frozen reference census differs')
    results = {key:count_mask(base,pancreas,labels,pan_truth,*edit) for key,edit in edits.items()}
    small = sorted(set(original['hits']) & (set(row['small'])-set(baseline['hits'])))
    diagnostics = dict(candidate_voxels=len(candidate),forwards=forwards,weak_incumbent_voxels=len(weak),
                       weak_incumbent_fp_voxels=int(np.count_nonzero(labels[weak]==0)),
                       new_small=small,sparse_sha256=sha(path))
    return results,diagnostics


def summarize(rows, control):
    totals = replay.summarize(rows)
    base = totals['baseline']
    if base != control['baseline'] or totals['rules'][previous.ARM]!=control['rules'][previous.ARM]:
        raise ValueError('Cohort controls differ')
    for key,m in totals['rules'].items():
        if key in control['rules']:
            continue
        m['added_tp'] = sum(row['arms'][key].get('added_tp',0) for row in rows)
        m['added_fp'] = sum(row['arms'][key].get('added_fp',0) for row in rows)
        m['removed_tp'] = sum(row['arms'][key].get('removed_tp',0) for row in rows)
        m['removed_fp'] = sum(row['arms'][key].get('removed_fp',0) for row in rows)
        m['passes'] = bool(m['passes'] and m['added_tp']>=m['removed_tp'])
    return {k:v for k,v in totals['rules'].items() if k not in control['rules']}


def worker(directory,expected):
    verify(directory,expected)
    cases,receipts = replay.saved.admitted_cases()
    model,checkpoint = replay.verified_checkpoint(cases)
    frozen = read(previous.FROZEN)
    native = {x['case_id']:x for x in cases}
    old_cases = {x['case_id']:x for x in read(replay.saved.OLDER/'request.json')['cases']}
    if set(native)!=set(old_cases) or len(frozen['rows'])!=70 or checkpoint!=frozen['checkpoint_sha256']:
        raise ValueError('Frozen cohorts or checkpoint differ')
    rows,diagnostics = [],{}
    directory_sparse = directory/'sparse-contours'
    directory_sparse.mkdir()
    keys = [name+suffix for name in RULES
            for suffix in ('_raw_add','_near5_add',*(f'_near5_swap{k}' for k in BUDGETS))]
    for row in frozen['rows']:
        case_id = row['case_id']
        row = dict(row,arms=dict(row['arms']))
        if row['arms'][previous.ARM]['added']:
            case = native[case_id]
            old_case = old_cases[case_id]
            if any(case[k]!=old_case[k] for k in ('sources','native_shape','native_affine')):
                raise ValueError('Checkpoint source identity differs')
            name = case_id+'.json'
            if sha(replay.saved.OLDER/name)!=sha(replay.saved.OLDER_BACKUP/name):
                raise ValueError('Older receipt differs')
            arms,proof = process_case(case,row,receipts[case_id],read(replay.saved.OLDER/name),model,directory_sparse)
            if list(arms)!=keys:
                raise ValueError('Arm order differs')
            row['arms'].update(arms)
            diagnostics[case_id]=proof
            print(json.dumps(dict(contours_replayed=len(diagnostics))),flush=True)
        else:
            row['arms'].update({k:row['arms']['baseline'] for k in keys})
        rows.append(row)
        gc.collect()
    if len(diagnostics)!=9 or len({row['case_id'] for row in rows})!=70:
        raise ValueError('Cohort mismatch')
    results = summarize(rows,frozen)
    verify(directory,expected)
    write(directory/'result.json',dict(request_sha256=expected,checkpoint_sha256=checkpoint,
          baseline=frozen['baseline'],untrimmed=frozen['rules'][previous.ARM],rules=results,
          rows=rows,diagnostics=diagnostics,development_scans=len(rows),new_model_forwards=sum(x['forwards'] for x in diagnostics.values())))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--worker')
    args=parser.parse_args()
    if args.worker:
        worker(args.directory,args.worker)
        return
    freeze(args.directory)
    expected=sha(args.directory/'request.json')
    limit=min(CAP,replay.refiner_run.pilot.DEADLINE-time.time()-60)
    if limit<120:
        raise ValueError('Insufficient time for supervised replay')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
             PYTHONDONTWRITEBYTECODE='1')
    if not run([sys.executable,__file__,str(args.directory),'--worker',expected],args.directory,
               seconds=limit,rss_bytes=4*replay.GIB,tick=replay.safety,env=env):
        raise SystemExit('Contour replay stopped; preserve evidence.')
    evidence=read(args.directory/'resources.json')
    if not evidence['workers_reaped'] or evidence['exit_code']!=0:
        raise ValueError('Worker closeout did not verify')
    verify(args.directory,expected)
    write(args.directory/'closeout.json',dict(status='VERIFIED_COMPLETE',request_sha256=expected,
          result_sha256=sha(args.directory/'result.json'),resources=evidence))


if __name__=='__main__':
    main()
