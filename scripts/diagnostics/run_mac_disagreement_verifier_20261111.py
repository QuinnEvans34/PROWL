"""Train a CPU candidate verifier on training-only proxies and test frozen disagreements."""
import argparse
from collections import Counter
import csv
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

from scripts.diagnostics import replay_mac_disagreement_refiner_20261111 as prior
from scripts.diagnostics import run_mac_search_window_locator_20261111 as miner
from src.operations.mac_teacher_supervision_v3 import run
from src.training.stunet_local_refiner_v1 import crop

BASE = prior.saved.ARTIFACTS
PILOT = prior.refiner_run.pilot
LOCATOR = BASE / 'candidate-locator-mac-20261111-a01/fit/checkpoint.pt'
LOCATOR_PROOF = ROOT / 'docs/capstone/operations/LOCAL-CANDIDATE-LOCATOR-MAC-RESULTS-20261111.json'
FROZEN = BASE / 'disagreement-refiner-mac-20261111/verified/result.json'
FROZEN_BACKUP = Path.home() / 'PROWL-Backups/disagreement-refiner-mac-20261111/verified/result.json'
ARM = 'refine50_near5'
SEED = 20261111
CAP = 2400
BATCH = 6
read, sha = prior.saved.read, prior.saved.sha


def write(path, data):
    encoded = json.dumps(data, allow_nan=False, indent=2) + '\n'
    with path.open('x') as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def select_training(cases):
    _, parent = prior.refiner_run.verify(read(prior.PROOF)['request_sha256'])
    excluded = {r['case_id'] for r in parent['train']} | PILOT.ERRATA
    development = {r['case_id'] for r in cases}
    assigned = {r['sources']['ct']['sha256'] for r in cases + parent['train']}
    train_ids = set((PILOT.MANIFEST/'train.txt').read_text().split())
    with (PILOT.MANIFEST/'manifest.csv').open() as stream:
        rows = [r for r in csv.DictReader(stream) if r['protected_role'] == 'train']
    if len(train_ids) != 1333 or {r['case_id'] for r in rows} != train_ids or train_ids & development:
        raise ValueError('Train/development membership differs')
    pools = {'small': [], 'empty': []}
    for row in sorted(rows, key=lambda r: r['case_id']):
        case = row['case_id']
        if case in excluded:
            continue
        path = PILOT.MANIFEST/'metadata'/(case+'.json')
        meta = read(path)
        native = meta['transform']
        shape, affine = native['source_shape'], native['source_affine']
        if meta['case_id'] != case or math.prod(shape) > 42_000_000:
            continue
        ct_sha = meta['source_sha256']['ct']
        if ct_sha in assigned:
            continue
        voxel = abs(float(np.linalg.det(np.asarray(affine)[:3, :3])))
        components = meta['fidelity']['components']
        if bool(components) != (row['target_state'] == 'positive'):
            raise ValueError('Training target state differs')
        small = [x for x in components if 20 <= x['native_voxels'] * voxel < 1000]
        if components and not small:
            continue
        sources = {k: dict(path=row[k+'_path'], sha256=meta['source_sha256'][k])
                   for k in ('ct','lesion','pancreas')}
        group = 'small' if small else 'empty'
        pools[group].append(dict(case_id=case, group=group, sources=sources, native_shape=shape,
            native_affine=affine, metadata=str(path), component=small[0] if small else None))
        assigned.add(ct_sha)
    rng = np.random.default_rng(SEED)
    groups = {'fit': [], 'calibration': []}
    for name, fit, calibration in (('small', 48, 24), ('empty', 24, 12)):
        pool = pools[name]
        if len(pool) < fit + calibration:
            raise ValueError(f'Too few {name} training-only cases: {len(pool)}')
        order = rng.permutation(len(pool))[:fit+calibration]
        groups['fit'].extend(pool[i] for i in order[:fit])
        groups['calibration'].extend(pool[i] for i in order[fit:])
    return groups


def prepare(directory):
    prior.safety()
    if sha(FROZEN) != sha(FROZEN_BACKUP) or sha(FROZEN) != '44fc50a3ab6c48610f44c2639af177dfe0659f92225b2e3b0a31db573b360ab2':
        raise ValueError('Frozen development replay changed')
    if sha(LOCATOR) != read(LOCATOR_PROOF)['trained_checkpoint_sha256']:
        raise ValueError('Frozen hard-negative miner checkpoint changed')
    cases, _ = prior.saved.admitted_cases()
    cohort = select_training(cases)
    members = [row for part in cohort.values() for row in part]
    pins = [Path(__file__), Path(prior.__file__), Path(miner.__file__), Path(PILOT.__file__),
            LOCATOR, LOCATOR_PROOF, FROZEN, FROZEN_BACKUP, prior.PROOF, prior.saved.CONFIG,
            PILOT.MANIFEST/'manifest.csv', PILOT.MANIFEST/'train.txt',
            *[Path(r['metadata']) for r in members]]
    directory.mkdir()
    write(directory/'request.json', dict(
        cohort=cohort, pins={str(p.resolve()): sha(p) for p in pins},
        seed=SEED, cap_seconds=CAP, rss_bytes=4*prior.GIB, batch=BATCH,
        estimator='L2 logistic regression C=0.3, standardized, class balanced',
        threshold='nextafter(max negative training-role calibration score, +inf)',
        arm=ARM, label_scope='training-only proxy centers, frozen refiner/locator never fit on these case IDs',
        test_scope='frozen 70 exposed development scans, no threshold tuning',
        no_ct_or_prediction_exports=True))


def verify(directory, digest):
    path = directory/'request.json'
    request = read(path)
    if sha(path) != digest or any(sha(p) != expected for p, expected in request['pins'].items()):
        raise ValueError('Frozen verifier request or pins changed')
    return request


def features(x, support, probability, patch_affine):
    """Identical CT and refiner-response summaries for proxy and actual prompts."""
    points = np.argwhere(support)
    basis = np.asarray(patch_affine)[:3, :3]
    d2 = np.square((points-prior.SIZE//2) @ basis.T).sum(axis=1)
    values = x[0][tuple(points.T)]
    confidence = probability[tuple(points.T)]
    output = []
    for lo, hi in ((0, 3), (3, 6), (6, 12)):
        take = (d2 >= lo*lo) & (d2 < hi*hi)
        if not take.any():
            take[np.argmin(np.abs(d2-(lo+hi)**2/4))] = True
        ct, p = values[take], confidence[take]
        output.extend([float(ct.mean()), float(ct.std()), *np.quantile(ct, [.1,.5,.9]).tolist(),
                       float(p.mean()), float(p.max()), float(np.quantile(p,.9)), float((p>=.5).mean())])
    if not np.isfinite(output).all():
        raise ValueError('Nonfinite candidate features')
    return output


def response(model, x, support, window):
    with torch.inference_mode():
        probability = model(torch.from_numpy(x)[None])[0, 0].sigmoid().numpy()
    if not np.isfinite(probability).all():
        raise ValueError('Nonfinite refiner probabilities')
    return probability, features(x, support, probability, window['patch_affine'])


def example_centers(row, ct, labels, pancreas, geometry, count, locator):
    basis = np.asarray(geometry['affine'])[:3, :3]
    pan = np.argwhere(pancreas)
    if not len(pan):
        raise ValueError('Missing training pancreas context')
    near_pan = cKDTree(pan @ basis.T)
    truth = np.argwhere(labels)
    if bool(len(truth)) != (row['group']=='small'):
        raise ValueError('Training target state changed')
    near_truth = cKDTree(truth @ basis.T) if len(truth) else None
    centers = []
    if near_truth is not None:
        component = row['component']
        points = np.argwhere(labels == component['component_id'])
        if not 1 <= component['component_id'] <= count or len(points) != component['native_voxels']:
            raise ValueError('Training small component changed')
        d2 = np.square((points-points.mean(axis=0)) @ basis.T).sum(axis=1)
        center = points[d2.argmin()]
        centers.append((center, 1, 'small_reference_center'))
        shift = np.linalg.norm((points-center) @ basis.T, axis=1)
        jitter = points[np.argmin(np.where(shift>=1.5, np.abs(shift-3), np.inf))]
        if not np.array_equal(jitter, center) and (shift>=1.5).any():
            centers.append((jitter, 1, 'small_reference_offset'))
    picked = []
    for center in miner.mined_centers(locator, ct, pan, geometry, near_pan):
        point = np.asarray(center)
        world = point @ basis.T
        if near_truth is not None and near_truth.query(world, workers=1)[0] < 8:
            continue
        if picked and np.min(np.linalg.norm(np.asarray(picked)-world, axis=1)) < 12:
            continue
        picked.append(world)
        centers.append((point, 0, 'frozen_locator_hard_negative'))
        if len(picked) == 4:
            break
    return centers


def mine(directory, request, part, batch, digest):
    all_cases, _ = prior.saved.admitted_cases()
    model, checkpoint_sha = prior.verified_checkpoint(all_cases)
    checkpoint = torch.load(LOCATOR, map_location='cpu', weights_only=True)
    if checkpoint['steps'] != 900:
        raise ValueError('Unexpected locator checkpoint step')
    locator = miner.old.Locator().cpu().eval()
    locator.load_state_dict(checkpoint['model'])
    del checkpoint
    rows = []
    for row in request['cohort'][part][batch*BATCH:(batch+1)*BATCH]:
        prior.safety()
        ct, labels, pancreas, geometry, count = PILOT.read_case(row)
        centers = example_centers(row, ct, labels, pancreas, geometry, count, locator)
        for center, label, origin in centers:
            window = prior.crop_record(ct.shape, geometry['affine'], center, prior.SIZE)
            support = prior.valid_support(window)
            x = prior.channels(crop(ct,window),support)
            _, vector = response(model,x,support,window)
            rows.append(dict(case_id=row['case_id'], label=label, origin=origin, features=vector))
        print(json.dumps(dict(case=row['case_id'], samples=len(centers))),flush=True)
        del ct, labels, pancreas
        gc.collect()
    write(directory/f'{part}-{batch:02}'/'features.json',
          dict(request_sha256=digest, checkpoint_sha256=checkpoint_sha, examples=rows))


def logits(features_array, state):
    features_array = np.asarray(features_array)
    return ((features_array-np.asarray(state['mean']))/np.asarray(state['scale'])) @ state['coefficients'] + state['intercept']


def fit(directory, request, digest):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    data = {}
    for part, cases in request['cohort'].items():
        rows = []
        for index in range(math.ceil(len(cases)/BATCH)):
            batch = read(directory/f'{part}-{index:02}'/'features.json')
            if batch['request_sha256'] != digest:
                raise ValueError('Feature extraction request changed')
            rows.extend(batch['examples'])
        members = {r['case_id'] for r in cases}
        if not {r['case_id'] for r in rows} <= members:
            raise ValueError('Features outside training role')
        data[part] = rows
    by_part = [{r['case_id'] for r in rows} for rows in data.values()]
    if by_part[0] & by_part[1]:
        raise ValueError('Fitting and threshold selection overlap')
    train = data['fit']
    cal = data['calibration']
    X = np.asarray([x['features'] for x in train])
    y = np.asarray([x['label'] for x in train])
    cal_y = np.asarray([x['label'] for x in cal])
    if min(Counter(y).values()) < 24 or len(set(y)) != 2 or len(set(cal_y)) != 2 or min(Counter(cal_y).values()) < 12:
        raise ValueError('Insufficient training or calibration candidates')
    scaler = StandardScaler().fit(X)
    model = LogisticRegression(C=.3,class_weight='balanced',max_iter=1000,random_state=SEED)
    model.fit(scaler.transform(X),y)
    state = dict(mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(),
                 coefficients=model.coef_[0].tolist(), intercept=float(model.intercept_[0]))
    if not np.allclose(logits(X,state),model.decision_function(scaler.transform(X)),rtol=0,atol=1e-12):
        raise ValueError('Saved verifier score replay differs')
    scores = logits([x['features'] for x in cal],state)
    threshold = float(np.nextafter(scores[cal_y==0].max(), np.inf))
    state.update(request_sha256=digest, threshold=threshold,
                 training_examples=dict(Counter(str(x['label']) for x in train)),
                 calibration_examples=dict(Counter(str(x['label']) for x in cal)),
                 calibration_positive_accepted=int(np.count_nonzero((scores>=threshold)&(cal_y==1))),
                 calibration_negative_accepted=int(np.count_nonzero((scores>=threshold)&(cal_y==0))),
                 feature_count=int(X.shape[1]))
    write(directory/'verifier.json',state)


def frozen_candidate(case, old, current, model, row):
    shape = case['native_shape']
    affine = np.asarray(case['native_affine'])
    basis = affine[:3,:3]
    volume = abs(float(np.linalg.det(basis)))
    index,tiers,distances,shells = prior.saved.core_support(current,affine,trim_levels=[2,3],grow_radii=[1.5])
    base = np.concatenate((index[(tiers>3)|(distances<=4)],shells[1.5]))
    pancreas = np.flatnonzero((current<4)&((current&1)==1))
    candidates,_ = prior.prompts(old,current,base,volume)
    if len(candidates) != row['evaluated_prompts']:
        raise ValueError('Frozen candidate count changed')
    src = case['sources']['ct']
    if sha(src['path']) != src['sha256']:
        raise ValueError('Development CT identity changed')
    image = nib.load(src['path'])
    if list(image.shape) != shape or not np.allclose(image.affine,affine,atol=1e-5,rtol=0):
        raise ValueError('Development CT geometry changed')
    g = prior.geometry(shape,affine)
    to_source = nib.orientations.inv_ornt_aff(np.asarray(g['forward']),shape)
    to_ras = np.linalg.inv(to_source)
    for _,_,_,seed,center in candidates:
        center = nib.affines.apply_affine(to_ras,center).astype(int)
        window = prior.crop_record(g['shape'],g['affine'],center,prior.SIZE)
        x,support = prior.ct_crop(image,g,window,to_source)
        probability,vector = response(model,x,support,window)
        native = np.column_stack(np.unravel_index(seed,shape))
        patch = nib.affines.apply_affine(to_ras,native).astype(int)-window['origin']
        added = prior.component_at_seed(probability,support,patch,window,to_source,
                                       shape,base,.5,volume)
        if len(added) and prior.within_pancreas_distance(added,pancreas,shape,basis):
            return base, added, vector, int(np.count_nonzero(np.isin(added,pancreas)))
    raise ValueError('Previously accepted candidate was not reproduced')


def score(directory, digest):
    state = read(directory/'verifier.json')
    if state['request_sha256'] != digest or state['calibration_negative_accepted']:
        raise ValueError('Threshold not frozen on training-only calibration')
    cases, receipts = prior.saved.admitted_cases()
    model, checkpoint_sha = prior.verified_checkpoint(cases)
    frozen = read(FROZEN)
    by_case = {r['case_id']:r for r in cases}
    old_requests = {r['case_id']:r for r in read(prior.saved.OLDER/'request.json')['cases']}
    rows, audits = [], []
    for row in frozen['rows']:
        prior.safety()
        row = dict(row, arms=dict(row['arms']))
        case_id = row['case_id']
        expected = row['arms'][ARM]
        accepted = False
        if expected['added']:
            case = by_case[case_id]
            old_case = old_requests[case_id]
            if any(old_case[k] != case[k] for k in ('native_shape','native_affine','sources')):
                raise ValueError('Paired source differs')
            file = case_id+'.json'
            if sha(prior.saved.OLDER/file) != sha(prior.saved.OLDER_BACKUP/file):
                raise ValueError('Older receipt differs')
            old = prior.saved.archive(read(prior.saved.OLDER/file)['artifact'],prior.saved.unpack_12k,case['native_shape'])
            current = prior.saved.archive(receipts[case_id]['artifact'],prior.saved.unpack_24k,case['native_shape'])
            base,added,vector,relabelled = frozen_candidate(case,old,current,model,row)
            value = float(logits(vector,state))
            accepted = value >= state['threshold']
            del old,current
            truth = prior.open_reference(case['sources']['lesion'],case['native_shape'],np.asarray(case['native_affine']))
            labels,count = ndimage.label(truth,structure=prior.saved.STRUCTURE)
            labels = labels.reshape(-1)
            baseline = prior.saved.score(base,labels)
            exact = prior.saved.score(np.concatenate((base,added)),labels)
            if (baseline != {k:row['arms']['baseline'][k] for k in baseline}
                    or exact != {k:expected[k] for k in exact}
                    or len(added) != expected['added'] or relabelled != expected['pancreas_relabelled']
                    or count != row['components']):
                raise ValueError('Frozen arm counts or pancreas relabels changed')
            target = prior.saved.score(added,labels)
            if (target['t']==0) != expected['added_false_component']:
                raise ValueError('Frozen component match changed')
            audits.append(dict(case_id=case_id, accepted=accepted, logit=value, added=target['p'],
                               true_positive=target['t'], component_hits=target['hits'],
                               newly_found_small=sorted(set(target['hits']) & (set(row['small'])-set(baseline['hits'])))))
        row['arms']['verified_near5'] = expected if accepted else row['arms']['baseline']
        rows.append(row)
        gc.collect()
    summary = prior.summarize(rows)
    if len(audits) != frozen['rules'][ARM]['scans_with_additions'] or summary['baseline'] != frozen['baseline']:
        raise ValueError('Development replay denominator changed')
    write(directory/'result.json',dict(request_sha256=digest,refiner_sha256=checkpoint_sha,
          baseline=summary['baseline'],ungated=summary['rules'][ARM],gated=summary['rules']['verified_near5'],
          verification=state, candidates=audits, cases=70, frozen_candidate_arm=ARM,
          synthetic_or_proxy_training=True, development_used_for_fitting=False))


def supervise(directory):
    prepare(directory)
    digest = sha(directory/'request.json')
    request = verify(directory,digest)
    deadline = min(time.time()+CAP,PILOT.DEADLINE-120)
    if deadline-time.time() < 800:
        raise ValueError('Not enough time for a bounded verifier pilot')
    env = dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
               PYTHONDONTWRITEBYTECODE='1')
    resources = []
    def stage(mode, name):
        dest = directory/name
        dest.mkdir()
        remaining = deadline-time.time()
        if remaining <= 0 or not run([sys.executable,__file__,str(directory),'--worker',mode,digest],
                                      dest,seconds=remaining,rss_bytes=4*prior.GIB,tick=prior.safety,env=env):
            raise ValueError(f'Stopped during {name}; preserve evidence')
        evidence = read(dest/'resources.json')
        if not evidence['success'] or not evidence['workers_reaped'] or evidence['exit_code'] != 0:
            raise ValueError('Worker cleanup not verified')
        resources.append(dict(stage=name,**evidence))

    for part, members in request['cohort'].items():
        for batch in range(math.ceil(len(members)/BATCH)):
            name = f'{part}-{batch:02}'
            stage(name,name)
    stage('train','estimator')
    stage('score','development')
    verify(directory,digest)
    write(directory/'closeout.json',dict(status='VERIFIED_COMPLETE',request_sha256=digest,
          result_sha256=sha(directory/'result.json'),verifier_sha256=sha(directory/'verifier.json'),
          resources=resources))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--worker',nargs=2)
    args=parser.parse_args()
    if not args.worker:
        supervise(args.directory)
        return
    mode,digest=args.worker
    request=verify(args.directory,digest)
    if mode=='train':
        fit(args.directory,request,digest)
    elif mode=='score':
        score(args.directory,digest)
    else:
        part,batch=mode.split('-')
        mine(args.directory,request,part,int(batch),digest)


if __name__ == '__main__':
    main()
