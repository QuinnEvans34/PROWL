#!/usr/bin/env python3
"""Run the frozen CP01 screen on one retained, exposed development package."""
import argparse
import json
from pathlib import Path
import sys

import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_prediction_boundary import digest, verified_package_images
from src.inference.component_selection import select_largest_union, compare_selection


def run(package, pancreas, lesion, output):
    output.mkdir(parents=True, exist_ok=False)
    try:
        m, e, pred, ref = verified_package_images(package, pancreas)
        # Pin new annotation before decode; retain this identity even if its validation fails.
        identity = {'case_id': m['case_id'], 'role': 'exposed_development_exploratory',
                    'model_sha256': m['model_sha256'], 'prediction_id': m['prediction_id'],
                    'package_files': m['files'], 'pancreas_sha256': digest(pancreas),
                    'lesion_sha256': digest(lesion), 'lesion_bytes': lesion.stat().st_size,
                    'lesion_identity_basis': 'local dataset annotation; Windows lesion hash not independently matched'}
        root = Path(__file__).resolve().parents[1]
        identity['producer_files'] = {name: digest(root / name) for name in (
            'scripts/compare_prediction_components.py', 'scripts/audit_prediction_boundary.py',
            'src/inference/component_selection.py',
            'docs/capstone/retrieval/COMPONENT-SELECTION-PLAN-2026-10-20.md')}
        (output / 'input-pins.json').write_text(json.dumps(identity, indent=2) + '\n')
        if lesion.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('Oversized reference file')
        lesion_img = nib.load(lesion)
        if (lesion_img.shape != pred.shape or lesion_img.header.get_xyzt_units()[0] != 'mm'
                or not np.allclose(lesion_img.affine, pred.affine, atol=1e-5, rtol=0)):
            raise ValueError('Lesion reference geometry/units mismatch')
        raw = np.asanyarray(pred.dataobj)
        candidate, selection = select_largest_union(raw)
        report = compare_selection(raw, candidate, np.asanyarray(ref.dataobj), np.asanyarray(lesion_img.dataobj),
                                   pred.affine, e['reconstruction']['native_box'])
        candidate_img = nib.Nifti1Image(candidate, pred.affine, pred.header.copy())
        candidate_img.set_data_dtype(np.uint8)
        candidate_img.header.set_slope_inter(1, 0)
        filename = output / 'candidate.nii.gz'
        nib.save(candidate_img, filename)
        restored = nib.load(filename)
        if not np.array_equal(np.asanyarray(restored.dataobj), candidate) or not np.array_equal(restored.affine, pred.affine):
            raise ValueError('Candidate export does not preserve native labels/geometry')
        # Recheck evaluated bytes after analysis; no source may have changed during the run.
        if (digest(package / 'prediction.nii.gz') != m['files']['pred']['content_sha256']
                or digest(pancreas) != identity['pancreas_sha256'] or digest(lesion) != identity['lesion_sha256']):
            raise ValueError('Inputs changed during comparison')
        report.update(identity=identity, selection=selection, candidate_sha256=digest(filename))
        (output / 'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        return report
    except Exception as error:
        (output / 'failure.json').write_text(json.dumps({'error': str(error), 'type': type(error).__name__}) + '\n')
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'pancreas', 'lesion', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    result = run(args.package, args.pancreas, args.lesion, args.output)
    print(json.dumps({k: result[k] for k in ('selection', 'targets', 'reference_lesion_components', 'rules', 'screen_pass')}, indent=2))
