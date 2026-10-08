#!/usr/bin/env python3
"""Check selected NIfTI headers against capstone geometry; does not decode image arrays."""
import argparse
import csv
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nibabel as nib
import numpy as np
from src.data.segmenter_geometry_v1 import canonical_geometry, recipe


def audit(manifest, output, seconds=600):
    start = time.monotonic(); counts = dict(checked=0, failed=0); maximum = 0
    with Path(manifest).open(newline='') as stream: rows = list(csv.DictReader(stream))
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    with (output/'headers.jsonl').open('x') as journal:
        for row in rows:
            if time.monotonic()-start >= seconds: break
            result = dict(case_id=row['case_id'], issues=[], headers={})
            loaded = {}
            for kind in ('ct', 'pancreas', 'lesion'):
                try:
                    obj = nib.load(row[kind+'_path'])
                    shape = list(obj.shape); maximum = max(maximum, int(np.prod(shape)))
                    result['headers'][kind] = dict(shape=shape, affine=obj.affine.tolist(),
                        dtype=str(obj.get_data_dtype()), slope=float(obj.dataobj.slope),
                        intercept=float(obj.dataobj.inter))
                    canonical_geometry(shape, obj.affine, recipe())
                    loaded[kind] = obj
                except (OSError, ValueError) as exc: result['issues'].append(f'{kind}: {exc}')
            if len(loaded) == 3 and any(v.shape != loaded['ct'].shape or not
                np.allclose(v.affine, loaded['ct'].affine, rtol=0, atol=1e-5) for v in loaded.values()):
                result['issues'].append('CT/target geometry mismatch')
            counts['checked'] += 1; counts['failed'] += bool(result['issues'])
            journal.write(json.dumps(result)+'\n');journal.flush()
    report = dict(**counts, requested=len(rows), completed=counts['checked']==len(rows),
        max_source_voxels=maximum, seconds=time.monotonic()-start, payload_arrays_decoded=0,
        scope='header_compatibility_not_content_or_negative_label_acceptance')
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True);p.add_argument('--output',required=True)
    p.add_argument('--seconds',type=int,default=600)
    print(json.dumps(audit(**vars(p.parse_args())),indent=2),flush=True)
