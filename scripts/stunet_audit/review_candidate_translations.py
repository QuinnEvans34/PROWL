"""Bounded descriptive translation search; never declares patient identity."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from scipy.signal import correlate

from scripts.stunet_audit.confirm_cropped_images import digest, load


def review(query, reference):
    """Rank contained translations by demeaned normalized intensity correlation."""
    q = np.asarray(query, dtype=np.float32)
    r = np.asarray(reference, dtype=np.float32)
    if q.ndim != 3 or r.ndim != 3 or max(q.size, r.size) > 16_000_000:
        raise ValueError('Descriptive allocation bound')
    if not np.isfinite(q).all() or not np.isfinite(r).all() or np.std(q) == 0 or np.std(r) == 0:
        raise ValueError('Invalid intensity distribution')
    if any(a > b for a, b in zip(q.shape, r.shape)):
        return dict(status='NOT_CONTAINED', identity_confirmed=False)
    qc = q - np.mean(q, dtype=np.float64)
    ones = np.ones(q.shape, dtype=np.float32)
    numerator = correlate(r, qc, mode='valid', method='fft')
    sums = correlate(r, ones, mode='valid', method='fft')
    squares = correlate(r * r, ones, mode='valid', method='fft')
    variance = np.maximum(squares - sums * sums / q.size, 0)
    denominator = np.sqrt(variance * np.sum(qc * qc, dtype=np.float64))
    scores = numerator / np.maximum(denominator, 1e-12)
    offset = np.unravel_index(np.argmax(scores), scores.shape)
    crop = r[tuple(slice(int(s), int(s) + n) for s, n in zip(offset, q.shape))]
    # Recompute descriptive statistics in float64 after approximate FFT ranking.
    x = crop.ravel().astype(np.float64)
    y = q.ravel().astype(np.float64)
    xc, yc = x - x.mean(), y - y.mean()
    slope = float(np.dot(xc, yc) / max(np.dot(xc, xc), 1e-12))
    intercept = float(y.mean() - slope * x.mean())
    residual = y - (slope * x + intercept)
    body = (x > -500) & (x < 1000) & (y > -500) & (y < 1000)
    return dict(status='DESCRIPTIVE_TRANSLATION_ONLY', offset_voxels=list(map(int, offset)),
                whole_query_correlation=float(np.corrcoef(x, y)[0, 1]),
                body_correlation=float(np.corrcoef(x[body], y[body])[0, 1]) if body.sum() > 100 else None,
                body_voxels=int(body.sum()), slope=slope, intercept=intercept,
                mean_absolute_difference=float(np.mean(np.abs(y - x))),
                fitted_residual_rmse=float(np.sqrt(np.mean(residual ** 2))),
                exact_equal_fraction=float(np.mean(x == y)),
                identity_confirmed=False, patient_independence_verified=False,
                physical_geometry_qualified=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if digest(args.request) != args.request_sha256:
        raise ValueError('Request differs')
    request = json.loads(args.request.read_text())
    if len(request['pairs']) > 6:
        raise ValueError('Six existing candidate pairs only')
    for name, pin in request['source_pins'].items():
        if digest(name) != pin:
            raise ValueError('Pinned source changed')
    args.output.mkdir(exist_ok=False)
    start = time.monotonic()
    rows = []
    for pair in request['pairs']:
        if time.monotonic() - start > 150:
            raise RuntimeError('Time bound')
        q, r = pair['query'], pair['reference']
        if q['role'] != 'development' or r['role'] != 'pretraining_reference':
            raise ValueError('Image role')
        result = review(load(q), load(r))
        result.update(case_id=q['case_id'], reference_id=r['case_id'])
        rows.append(result)
        (args.output / 'progress.json').write_text(json.dumps(rows, indent=2))
    (args.output / 'results.json').write_text(json.dumps(rows, indent=2))
    (args.output / 'summary.json').write_text(json.dumps(dict(pairs=len(rows), seconds=time.monotonic()-start,
        identity_confirmation=False, model_forwards=0, optimizer_updates=0), indent=2))


if __name__ == '__main__':
    main()
