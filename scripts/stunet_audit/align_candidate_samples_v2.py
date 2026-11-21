"""Sparse numeric-coordinate translation review; no patient identity clearance.

Uses bounded sampled coordinates instead of the previous full-array FFT. Numeric
voxel coordinates are not an assertion of valid physical units or clinical geometry.
"""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize

from scripts.stunet_audit.confirm_cropped_images import digest, load


def align(query, reference, initial, *, max_points=48**3):
    q, r = np.asarray(query), np.asarray(reference)
    if q.ndim != 3 or r.ndim != 3 or max(q.size, r.size) > 128_000_000:
        raise ValueError('Native allocation cap')
    if not np.isfinite(q).all() or not np.isfinite(r).all():
        raise ValueError('Nonfinite source')
    axes = [np.linspace(0, n-1, min(n, 48), dtype=np.float64) for n in q.shape]
    coords = np.stack(np.meshgrid(*axes, indexing='ij')).reshape(3, -1)
    if coords.shape[1] > max_points:
        raise ValueError('Sample allocation cap')
    target = map_coordinates(q, coords, order=1, mode='nearest', prefilter=False).astype(np.float64)
    mask = (target > -400) & (target < 1000)
    if mask.sum() < 100:
        raise ValueError('Insufficient tissue-range samples')
    points, target = coords[:, mask], target[mask]
    center = target-target.mean()
    norm = np.linalg.norm(center)
    if norm < 1e-8:
        raise ValueError('Constant target samples')

    def objective(offset):
        moved = points + np.asarray(offset)[:, None]
        valid = ((moved >= 0) & (moved <= np.asarray(r.shape)[:, None]-1)).all(axis=0)
        if np.mean(valid) < .95:
            return 2.
        values = map_coordinates(r, moved, order=1, mode='nearest', prefilter=False).astype(np.float64)
        values -= values.mean()
        return 1-float(np.dot(center, values)/(norm*np.linalg.norm(values)+1e-12))

    initial = np.asarray(initial, dtype=float)
    result = minimize(objective, initial, method='Powell',
                      bounds=[(v-4, v+4) for v in initial],
                      options=dict(maxiter=40, maxfev=350, xtol=.005, ftol=1e-7))
    moved = points + result.x[:, None]
    values = map_coordinates(r, moved, order=1, mode='nearest', prefilter=False).astype(np.float64)
    vc = values-values.mean()
    slope = float(np.dot(vc, center)/(np.dot(vc, vc)+1e-12))
    intercept = float(target.mean()-slope*values.mean())
    return dict(status='APPROXIMATE_ALIGNMENT_NOT_IDENTITY', sampled_tissue_points=int(len(target)),
                initial_offset_voxels=initial.tolist(), fitted_offset_voxels=result.x.tolist(),
                initial_tissue_correlation=1-objective(initial),
                fitted_tissue_correlation=1-objective(result.x),
                fitted_intensity_slope=slope, fitted_intensity_intercept=intercept,
                fitted_residual_rmse=float(np.sqrt(np.mean((target-slope*values-intercept)**2))),
                optimizer_success=bool(result.success), objective_evaluations=int(result.nfev),
                patient_identity_confirmed=False, image_identity_confirmed=False,
                physical_units_assigned=False, physical_geometry_qualified=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if digest(a.request) != a.request_sha256:
        raise ValueError('Request differs')
    req = json.loads(a.request.read_text())
    for name, pin in req['source_pins'].items():
        if digest(name) != pin:
            raise ValueError('Source differs')
    pairs = req['pairs']
    if len(pairs) != 5 or len({x['query']['case_id'] for x in pairs}) != 5:
        raise ValueError('Five frozen geometry-candidate queries required')
    a.output.mkdir(exist_ok=False)
    start = time.monotonic()
    rows = []
    for pair in pairs:
        if time.monotonic()-start > 150:
            raise RuntimeError('Stage time cap')
        q, r = pair['query'], pair['reference']
        if q['role'] != 'development' or r['role'] != 'pretraining_reference':
            raise ValueError('Role boundary')
        row = align(load(q), load(r), pair['suggested_offsets'][0])
        row.update(case_id=q['case_id'], reference_id=r['case_id'])
        rows.append(row)
        (a.output/'progress.json').write_text(json.dumps(rows, indent=2))
    (a.output/'results.json').write_text(json.dumps(rows, indent=2))
    (a.output/'summary.json').write_text(json.dumps(dict(completed_pairs=len(rows),
        seconds=time.monotonic()-start,clearance_issued=False,model_forwards=0,optimizer_updates=0),indent=2))


if __name__ == '__main__':
    main()
