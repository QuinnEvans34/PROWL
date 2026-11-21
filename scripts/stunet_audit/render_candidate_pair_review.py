"""Local-only matched-index CT views for the already admitted candidate pair."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from scripts.stunet_audit.confirm_cropped_images import digest, load


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if digest(a.request) != a.request_sha256:
        raise ValueError('Request identity')
    request = json.loads(a.request.read_text())
    for name, pin in request['source_pins'].items():
        if digest(name) != pin:
            raise ValueError('Source identity')
    pair = request['pair']
    if (pair['query']['case_id'], pair['reference']['case_id']) != ('PanTS_00001389','TotalSegV1:s1014'):
        raise ValueError('One existing candidate only')
    if pair['query']['role'] != 'development' or pair['reference']['role'] != 'pretraining_reference':
        raise ValueError('Role boundary')
    q, r = load(pair['query']), load(pair['reference'])
    if any(x > y for x,y in zip(q.shape,r.shape)):
        raise ValueError('Contained view required')
    a.output.mkdir(exist_ok=False)
    crop = r[tuple(slice(0, n) for n in q.shape)]
    mask = (q > -400) & (q < 1000)
    quantiles = [0, 1, 5, 50, 95, 99, 100]
    summary = dict(case_id=pair['query']['case_id'],reference_id=pair['reference']['case_id'],
        query_shape=list(q.shape), reference_shape=list(r.shape),
        quantile_percentages=quantiles,query_quantiles=np.percentile(q,quantiles).tolist(),
        reference_quantiles=np.percentile(crop,quantiles).tolist(),
        exact_tissue_fraction=float(np.mean(q[mask] == crop[mask])),
        tissue_absolute_error_quantiles=np.percentile(np.abs(q[mask]-crop[mask]),quantiles).tolist(),
        view_policy='Identical numeric voxel indices, not clinical registration; display clipping -200..300 numeric intensity',
        identity_confirmed=False,physical_geometry_qualified=False,images_uploaded=False)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2))
    fig, axes = plt.subplots(3,3,figsize=(12,11),layout='constrained')
    for col, axis in enumerate((2,1,0)):
        index=q.shape[axis]//2
        qa,ra=np.take(q,index,axis=axis).T,np.take(crop,index,axis=axis).T
        axes[0,col].imshow(qa,cmap='gray',vmin=-200,vmax=300,origin='lower')
        axes[1,col].imshow(ra,cmap='gray',vmin=-200,vmax=300,origin='lower')
        axes[2,col].imshow(np.abs(qa-ra),cmap='magma',vmin=0,vmax=100,origin='lower')
        axes[0,col].set_title(f'Numeric axis {axis}, index {index}')
        for row in range(3):axes[row,col].set_xticks([]);axes[row,col].set_yticks([])
    for row,label in enumerate(['PanTS 1389','Original v1 s1014','Absolute intensity difference']):axes[row,0].set_ylabel(label)
    fig.suptitle('Candidate review only — no patient identity or physical geometry clearance')
    fig.savefig(a.output/'candidate-review.png',dpi=120)
    plt.close(fig)


if __name__ == '__main__':
    main()
