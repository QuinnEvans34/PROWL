"""Read-only diagnostic oracles for the verified terminal-24k development study."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
BASE = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-margin-mac-20261110')
STUDY = BASE/'screen-02'
SELECTED = 'grow0.5_seed-0.5_near5'
STRUCTURE = '26-connected'
GIB = 1024**3
RESULT_SHA = 'fad51ea37a0ff32d2f2d3f79d91c840a4f5cd437273296fb2080fb3653f1da41'
REQUEST_SHA = '1e8f3ff8b98014af3d560638bd0567fb6bf29ac40fb214deaef7db27154dbbdc'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dice(n, p, t):
    return 2*t/(n+p)


def oracle(rows, *, drop=lambda r: 0, fill=lambda r: 0):
    scores = []
    for r in rows:
        d, f = drop(r), fill(r)
        if not 0 <= d <= r['fp'] or not 0 <= f <= r['fn']:
            raise ValueError('Impossible oracle correction')
        scores.append(dice(r['n'], r['p']-d+f, r['t']+f))
    return mean(scores)


def admitted_cases():
    from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety
    safety()
    if sha(STUDY/'result.json') != RESULT_SHA or sha(STUDY/'request.json') != REQUEST_SHA:
        raise ValueError('Original study identity changed')
    req = read(STUDY/'request.json')
    for p,h in req['pins'].items():
        if sha(p) != h:
            raise ValueError('Primary source pin changed')
    cases = req['cases']
    ids = {r['case_id'] for r in cases}
    if len(cases) != 70 or len(ids) != 70 or {p.stem for p in STUDY.glob('PanTS_*.json')} != ids:
        raise ValueError('Development case census changed')
    receipts = {}
    backups = [Path.home()/'PROWL-Backups'/f'stunet-margin-mac-20261110-{n}' for n in ('01','02')]
    for c in cases:
        name = c['case_id']
        path = STUDY/(name+'.json')
        # Resumed cases have an independent receipt in 02; reused rows were already
        # copied from 01 byte for byte during the verified primary closeout.
        if not any((b/path.name).exists() and sha(b/path.name) == sha(path) for b in backups):
            raise ValueError('Saved case receipt differs from independent copy')
        r = read(path)
        if r['case_id'] != name or not r['independent_policy_replay']:
            raise ValueError('Missing independent policy replay')
        receipts[name] = r
    return cases, receipts


def examine(case, receipt):
    import nibabel as nib
    import numpy as np
    from scipy import ndimage
    from src.data.segmenter_content_v1 import target_content
    from src.inference.stunet_margin_screen_20261110 import (
        STRUCTURE as connectivity, components, policies, retained, unpack,
    )
    from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety
    safety()
    affine = np.array(case['native_affine'])
    source = case['sources']['lesion']
    if sha(source['path']) != source['sha256']:
        raise ValueError('Admitted lesion reference changed')
    obj = nib.load(source['path'])
    if list(obj.shape) != case['native_shape'] or not np.allclose(obj.affine, affine, rtol=0, atol=1e-5):
        raise ValueError('Reference geometry changed')
    lesion, _ = target_content(obj.dataobj.get_unscaled(),
        dict(slope=float(obj.dataobj.slope), intercept=float(obj.dataobj.inter)))
    ref, count = ndimage.label(lesion, structure=connectivity)
    ref_ids = ref[lesion != 0]
    sizes = np.bincount(ref_ids, minlength=count+1)
    del ref
    artifact = receipt['artifact']
    if sha(artifact['backup']) != artifact['sha256']:
        raise ValueError('Independent prediction code changed')
    with np.load(artifact['backup'], allow_pickle=False) as saved:
        code = unpack(saved['packed'], [int(x) for x in saved['shape']])
    if code.shape != lesion.shape:
        raise ValueError('Prediction shape changed')
    policy = policies()[SELECTED]
    pred, labels, info = components(code, policy['bias'], affine)
    del pred
    keep = retained(info, policy)
    label_ref = labels[lesion != 0]
    hits = keep[label_ref]
    comp_tp = np.bincount(ref_ids[hits], minlength=count+1)
    pred_tp = np.bincount(label_ref[hits], minlength=len(keep))
    n = int(sizes.sum())
    p = int(info['sizes'][keep].sum())
    t = int(comp_tp.sum())
    fp = p-t
    fn = n-t
    unconnected_fp = int(info['sizes'][keep & (pred_tp == 0)].sum())
    # Four-bit archive records winners at five frozen biases. A code below the
    # most permissive replay is not proof of zero model signal.
    ref_code = code[lesion != 0]//2
    still_candidate = int(np.count_nonzero(~hits & (ref_code >= 2)))
    candidate_at_one = int(np.count_nonzero(~hits & (ref_code == 1)))
    outside_grid = int(np.count_nonzero(~hits & (ref_code == 0)))
    saved = receipt['policies'][SELECTED]
    if ((n,p,t) != tuple(saved['lesion'][k] for k in ('target_voxels','predicted_voxels','true_positive')) or
            list(np.flatnonzero(comp_tp)) != saved['hit_component_ids'] or count != saved['reference_components'] or
            still_candidate+candidate_at_one+outside_grid != fn or not 0 <= unconnected_fp <= fp):
        raise ValueError('Exact prediction replay mismatch')
    mm3 = saved['voxel_mm3']
    ref_components = [dict(voxels=int(sizes[i]), tp=int(comp_tp[i]),
                           volume_ml=float(sizes[i]*mm3/1000)) for i in range(1,count+1)]
    small_components = [x for x in ref_components if x['volume_ml'] < 1]
    return dict(case=case['case_id'], n=n, p=p, t=t, fp=fp, fn=fn,
        group=saved['size_band'], volume_ml=saved['target_volume_mm3']/1000,
        voxel_mm3=mm3, components=ref_components,
        small_component_fn=sum(c['voxels']-c['tp'] for c in small_components),
        missed_component_fn=sum(c['voxels'] for c in ref_components if c['tp']==0),
        missed_small_component_fn=sum(c['voxels'] for c in small_components if c['tp']==0),
        unconnected_fp=unconnected_fp, attached_fp=fp-unconnected_fp,
        candidate_filtered_fn=still_candidate, candidate_only_at_plus_one_fn=candidate_at_one,
        outside_bias_grid_fn=outside_grid)


def summarize(rows):
    components = [c for r in rows for c in r['components']]
    small = [c for c in components if c['volume_ml'] < 1]
    if (len(rows),len(components),sum(r['group']=='small' for r in rows),
            sum(r['t']>0 for r in rows),sum(c['tp']>0 for c in components)) != (36,45,5,35,39):
        raise ValueError('Verified positive or component census mismatch')
    groups = {}
    for group in ('small','medium','large'):
        subset = [r for r in rows if r['group']==group]
        groups[group] = dict(cases=len(subset), dice=oracle(subset),
            case_hits=sum(r['t']>0 for r in subset), recall=mean(r['t']/r['n'] for r in subset))
    oracle_scores = dict(
        all_fp_removed=oracle(rows, drop=lambda r:r['fp']),
        all_fn_recovered=oracle(rows, fill=lambda r:r['fn']),
        all_five_small_cases_perfect=oracle(rows, drop=lambda r:r['fp'] if r['group']=='small' else 0,
                                                 fill=lambda r:r['fn'] if r['group']=='small' else 0),
        all_five_small_case_fn_recovered=oracle(rows, fill=lambda r:r['fn'] if r['group']=='small' else 0),
        all_small_component_fn_recovered=oracle(rows, fill=lambda r:r['small_component_fn']),
        all_missed_components_recovered=oracle(rows, fill=lambda r:r['missed_component_fn']),
        all_missed_small_components_recovered=oracle(rows, fill=lambda r:r['missed_small_component_fn']),
        zero_overlap_case_fn_recovered=oracle(rows, fill=lambda r:r['fn'] if r['t']==0 else 0),
        isolated_fp_removed=oracle(rows, drop=lambda r:r['unconnected_fp']),
        filtered_candidate_fn_recovered=oracle(rows, fill=lambda r:r['candidate_filtered_fn']),
        within_grid_fn_recovered=oracle(rows, fill=lambda r:r['candidate_filtered_fn']+r['candidate_only_at_plus_one_fn']),
    )
    errors = {k:sum(r[k] for r in rows) for k in (
        'fn','fp','unconnected_fp','attached_fp','candidate_filtered_fn',
        'candidate_only_at_plus_one_fn','outside_bias_grid_fn','missed_component_fn','small_component_fn')}
    volumes = {k:sum(r[k]*r['voxel_mm3']/1000 for r in rows) for k in errors}
    return dict(actual_dice=oracle(rows), groups=groups, oracles=oracle_scores,
        error_voxels=errors, error_volume_ml=volumes, small_components=len(small),
        small_components_hit=sum(c['tp']>0 for c in small), positive_cases=len(rows),
        reference_components=len(components), found_components=sum(c['tp']>0 for c in components),
        oracle_examples=dict(drop_50pct_fp=oracle(rows, drop=lambda r:.5*r['fp']),
                             add_20pct_fn=oracle(rows, fill=lambda r:.2*r['fn']),
                             drop_25pct_fp_add_20pct_fn=oracle(rows,drop=lambda r:.25*r['fp'],fill=lambda r:.2*r['fn'])),
        connectivity=STRUCTURE, policy=SELECTED, primary_result_sha256=RESULT_SHA, primary_request_sha256=REQUEST_SHA,
        cases=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    cases, receipts = admitted_cases()
    rows = []
    for c in cases:
        receipt = receipts[c['case_id']]
        if receipt['policies'][SELECTED]['reference_positive']:
            rows.append(examine(c, receipt))
            gc.collect()
            print(f'verified {len(rows)} positive cases',flush=True)
    result = summarize(rows)
    if result['actual_dice'] != read(STUDY/'result.json')['policies'][SELECTED]['positive_macro_dice']:
        raise ValueError('Headline Dice mismatch')
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False); f.write('\n')


if __name__=='__main__':
    main()
