#!/usr/bin/env python3
"""Rebuild a prepared Workbench study at the CT's native resolution.

Display-only export for the UI. It does not change any model output or score
used elsewhere. See docs/capstone/interface/WORKBENCH-VISUAL-REFRESH-SPEC-20261119.md.

Inputs
  --ct         original PanTS CT (native grid)
  --labels     PanTSMini_Label/<case>/segmentations directory
  --case-dir   existing ui/public/cases/<case> directory (1.5 mm prepared files)
  --results    ui/public/cases/results.json (updated in place for this case)

Use --full-only with an existing native crop to add the full native 3D CT
without modifying the crop, labels, measurements, or 2 mm full export.

The crop never uses reference labels: slice range comes from the saved
prediction's pancreas extent (+/- margin), in-plane extent from the body outline.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import struct
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage

SLICE_MARGIN_MM = 40.0
BODY_MARGIN_MM = 10.0
BODY_HU = -500.0
ALIGNMENT_MIN_DICE = 0.90
# Prepared Workbench CTs store (HU + 100) / 400, i.e. HU -100..300 -> 0..1 (fitted
# against the prepared files, residual < 0.001). The native CT keeps raw int16 HU and
# carries this mapping in scl_slope/scl_inter so every existing window preset applies.
CT_SLOPE, CT_INTER = 1.0 / 400.0, 0.25


def dice(a: np.ndarray, b: np.ndarray) -> float | None:
    total = int(a.sum()) + int(b.sum())
    return None if total == 0 else round(2.0 * int((a & b).sum()) / total, 3)


def world_to_index(affine: np.ndarray, points: np.ndarray) -> np.ndarray:
    return nib.affines.apply_affine(np.linalg.inv(affine), points)


def resample_labels(src: np.ndarray, src_affine: np.ndarray, dst_shape, dst_affine,
                    classes=(1, 2), smooth=True) -> np.ndarray:
    """Map a label volume onto another grid through world coordinates.

    smooth=True: trilinear interpolation of each class's one-hot channel, then
    argmax against background (keeps volume, avoids staircase edges).
    smooth=False: nearest neighbour.
    """
    ii, jj, kk = np.meshgrid(*[np.arange(n, dtype=np.float32) for n in dst_shape], indexing='ij')
    ijk = np.stack([ii.ravel(), jj.ravel(), kk.ravel()], axis=1)
    world = nib.affines.apply_affine(dst_affine, ijk)
    coords = world_to_index(src_affine, world).T
    if not smooth:
        return ndimage.map_coordinates(src, coords, order=0, mode='constant', cval=0).reshape(dst_shape).astype(np.int16)
    probs = [ndimage.map_coordinates((src == 0).astype(np.float32), coords, order=1, mode='constant', cval=1.0)]
    for c in classes:
        probs.append(ndimage.map_coordinates((src == c).astype(np.float32), coords, order=1, mode='constant', cval=0.0))
    winner = np.argmax(np.stack(probs), axis=0)
    out = np.zeros(winner.shape, np.int16)
    for index, c in enumerate(classes, start=1):
        out[winner == index] = c
    return out.reshape(dst_shape)


def load_reference(labels: Path, like: nib.Nifti1Image) -> np.ndarray:
    ref = np.zeros(like.shape, np.int16)
    for filename, code in [('pancreas.nii.gz', 1), ('pancreatic_lesion.nii.gz', 2)]:
        mask = nib.load(labels / filename)
        if mask.shape != like.shape or not np.allclose(mask.affine, like.affine, rtol=0, atol=1e-4):
            raise SystemExit(f'Reference mask {filename} does not match the CT grid (shape or affine)')
        ref[np.asarray(mask.dataobj) > 0] = code
    return ref


def difference(pred: np.ndarray, ref: np.ndarray, code: int) -> np.ndarray:
    # Pancreas (code 1) is the whole organ including lesion voxels, matching the
    # legacy difference files; lesion (code 2) is the lesion label alone.
    p, r = (pred >= 1, ref >= 1) if code == 1 else (pred == code, ref == code)
    out = np.zeros(pred.shape, np.int16)
    out[p & r] = 1
    out[p & ~r] = 2
    out[~p & r] = 3
    return out


def prepared(case_dir: Path, name: str) -> Path:
    """The 1.5 mm file: its *_prepared backup once a native export has run."""
    backup = case_dir / name.replace('.nii.gz', '_prepared.nii.gz')
    return backup if backup.exists() else case_dir / name


def check_difference_codes(case_dir: Path) -> None:
    """Confirm the legacy difference files use 1 agree / 2 pred-only / 3 ref-only."""
    pred = np.asarray(nib.load(prepared(case_dir, 'pred.nii.gz')).dataobj)
    ref = np.asarray(nib.load(prepared(case_dir, 'gt.nii.gz')).dataobj)
    legacy_dir = case_dir / 'difference_prepared'
    if not legacy_dir.exists():
        legacy_dir = case_dir / 'difference'
    for name, code in [('pancreas', 1), ('lesion', 2)]:
        path = legacy_dir / f'{name}.nii.gz'
        if not path.exists():
            continue
        legacy = np.asarray(nib.load(path).dataobj)
        mine = difference(pred, ref, code)
        agreement = float((legacy == mine).mean())
        if agreement < 0.999:
            raise SystemExit(f'Legacy {name} difference codes differ from 1/2/3 convention ({agreement:.4f})')


def read_results(path: Path, case_id: str) -> dict:
    try:
        results = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f'Cannot read results manifest {path}: {exc}') from exc
    if not isinstance(results, dict) or not isinstance(results.get(case_id), dict):
        raise SystemExit(f'Results manifest {path} has no valid entry for {case_id}')
    return results


def export_full_ct(native: nib.Nifti1Image, case_dir: Path, results_path: Path, dry_run: bool) -> None:
    case_id = case_dir.name
    entry = read_results(results_path, case_id)[case_id]
    files = entry.get('files')
    if not isinstance(files, dict) or entry.get('display_resolution') != 'native' or files.get('ct') != f'{case_id}/ct.nii.gz':
        raise SystemExit('Export the native CT crop for this study before adding its full 3D volume')
    crop = nib.load(case_dir / 'ct.nii.gz')
    if len(native.shape) != 3 or len(crop.shape) != 3:
        raise SystemExit('The source CT and its native crop must be 3D')
    crop_in_full = np.linalg.solve(native.affine, crop.affine)
    start = np.rint(crop_in_full[:3, 3]).astype(int)
    end = start + np.asarray(crop.shape)
    if (not np.allclose(crop_in_full[:3, :3], np.eye(3), rtol=0, atol=1e-5)
            or not np.allclose(crop_in_full[:3, 3], start, rtol=0, atol=1e-3)
            or np.any(start < 0) or np.any(end > native.shape)):
        raise SystemExit('The source CT grid does not contain the existing native crop')

    values = np.asarray(native.dataobj, dtype=np.float32)
    limits = np.iinfo(np.int16)
    if not limits.min <= values.min() <= values.max() <= limits.max:
        raise SystemExit('The source CT has non-finite or out-of-range intensities')
    full_hu = np.rint(values).astype(np.int16)
    region = tuple(slice(a, b) for a, b in zip(start, end))
    expected_crop_hu = np.clip(full_hu[region], -1024, 3071)
    if (not np.isclose(crop.dataobj.slope, CT_SLOPE, rtol=1e-6, atol=0)
            or crop.dataobj.inter != CT_INTER
            or not np.array_equal(expected_crop_hu, crop.dataobj.get_unscaled())):
        raise SystemExit('The source CT intensities do not match the existing native crop')

    print(f'{case_id}: full native CT {native.shape} @ {native.header.get_zooms()} mm')
    if dry_run:
        return

    filename = 'ct_full_native.nii.gz'
    image = nib.Nifti1Image(full_hu, native.affine)
    image.header.set_xyzt_units('mm')
    image.header.set_slope_inter(CT_SLOPE, CT_INTER)
    with tempfile.TemporaryDirectory(dir=case_dir) as staging:
        image_path = Path(staging) / filename
        nib.save(image, image_path)
        os.replace(image_path, case_dir / filename)

    # Publish the manifest after the volume is fully available.
    results = read_results(results_path, case_id)
    results[case_id]['files']['ct_full_native'] = f'{case_id}/{filename}'
    with tempfile.TemporaryDirectory(dir=results_path.parent) as staging:
        manifest = Path(staging) / results_path.name
        manifest.write_text(json.dumps(results, indent=1) + '\n')
        os.replace(manifest, results_path)
    print(f'  wrote {filename} and updated {results_path.name}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--ct', type=Path, required=True)
    parser.add_argument('--labels', type=Path)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--full-only', action='store_true', help='add the full native CT without rebuilding the crop')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not args.full_only and args.labels is None:
        parser.error('--labels is required unless --full-only is used')

    case_dir: Path = args.case_dir
    case_id = case_dir.name
    native = nib.load(args.ct)
    if args.full_only:
        export_full_ct(native, case_dir, args.results, args.dry_run)
        return

    results = read_results(args.results, case_id)
    entry = results[case_id]
    prepared_pred = nib.load(prepared(case_dir, 'pred.nii.gz'))
    prepared_gt = nib.load(prepared(case_dir, 'gt.nii.gz'))
    zooms = [round(float(z), 4) for z in native.header.get_zooms()[:3]]
    print(f'{case_id}: native {native.shape} @ {zooms} mm, axcodes {nib.aff2axcodes(native.affine)}')

    reference = load_reference(args.labels, native)

    # Alignment gate: the native reference, mapped onto the old 1.5 mm grid,
    # must reproduce the old gt.nii.gz. Proves a shared world frame.
    ref_on_old = resample_labels(reference, native.affine, prepared_gt.shape, prepared_gt.affine, smooth=False)
    old_gt = np.asarray(prepared_gt.dataobj)
    gate = dice(ref_on_old >= 1, old_gt >= 1)
    print(f'  alignment gate: pancreas+lesion Dice on the prepared grid = {gate}')
    if gate is None or gate < ALIGNMENT_MIN_DICE:
        raise SystemExit('Alignment gate failed; native and prepared grids do not share world coordinates')
    check_difference_codes(case_dir)

    # Crop: slice range from the saved prediction's pancreas extent (no reference labels).
    pred_old = np.asarray(prepared_pred.dataobj)
    idx = np.argwhere(pred_old >= 1)
    if not len(idx):
        raise SystemExit('Saved prediction has no pancreas; cannot frame the crop')
    corners = np.array([[a, b, c] for a in (idx[:, 0].min(), idx[:, 0].max())
                        for b in (idx[:, 1].min(), idx[:, 1].max())
                        for c in (idx[:, 2].min(), idx[:, 2].max())], float)
    world = nib.affines.apply_affine(prepared_pred.affine, corners)
    native_idx = world_to_index(native.affine, world)
    # Identify the native slice axis (largest spacing; ties -> last axis).
    slice_axis = int(np.argmax(np.array(zooms) + np.array([0, 0, 1e-6])))
    margin = SLICE_MARGIN_MM / zooms[slice_axis]
    lo = max(0, int(np.floor(native_idx[:, slice_axis].min() - margin)))
    hi = min(native.shape[slice_axis], int(np.ceil(native_idx[:, slice_axis].max() + margin)) + 1)
    if lo >= hi:
        raise SystemExit('Saved prediction does not overlap the native CT slice range')

    window = [slice(None)] * 3
    window[slice_axis] = slice(lo, hi)
    body = np.asarray(native.dataobj[tuple(window)], dtype=np.float32) > BODY_HU
    if not body.any():
        raise SystemExit('Native CT has no body voxels in the selected slices')
    bounds = []
    for axis in range(3):
        if axis == slice_axis:
            bounds.append((lo, hi))
            continue
        other = tuple(a for a in range(3) if a != axis)
        present = np.where(body.any(axis=other))[0]
        pad = int(np.ceil(BODY_MARGIN_MM / zooms[axis]))
        bounds.append((max(0, int(present.min()) - pad), min(native.shape[axis], int(present.max()) + pad + 1)))
    crop = tuple(slice(a, b) for a, b in bounds)
    crop_affine = native.slicer[crop].affine
    shape = tuple(b - a for a, b in bounds)
    print(f'  crop {bounds} -> {shape}')

    ct_crop = np.clip(np.rint(np.asarray(native.dataobj[crop], dtype=np.float32)), -1024, 3071).astype(np.int16)
    ref_crop = reference[crop]
    pred_native = resample_labels(pred_old, prepared_pred.affine, shape, crop_affine, smooth=True)
    voxel_mm3 = float(abs(np.linalg.det(crop_affine[:3, :3])))
    stats = {
        'dice_pancreas': dice(pred_native >= 1, ref_crop >= 1),
        'dice_lesion': dice(pred_native == 2, ref_crop == 2),
        'lesion_volume_mm3': round(float((pred_native == 2).sum()) * voxel_mm3, 1),
        'gt_has_lesion': bool((ref_crop == 2).any()),
        'pred_has_lesion': bool((pred_native == 2).any()),
    }
    old_lesion = float((pred_old == 2).sum()) * float(abs(np.linalg.det(prepared_pred.affine[:3, :3])))
    print(f'  native stats {stats}; prepared lesion volume {old_lesion:.1f} mm3')
    if args.dry_run:
        return

    def save(array, name):
        img = nib.Nifti1Image(array, crop_affine)
        img.header.set_xyzt_units('mm')
        if array.dtype == np.int16 and name != 'ct.nii.gz':
            img.header.set_intent(1002)  # label map
        nib.save(img, case_dir / name)

    for name in ['ct.nii.gz', 'pred.nii.gz', 'gt.nii.gz']:
        backup = case_dir / name.replace('.nii.gz', '_prepared.nii.gz')
        if not backup.exists():
            shutil.copy2(case_dir / name, backup)
    (case_dir / 'difference_prepared').mkdir(exist_ok=True)
    for name in ['pancreas', 'lesion']:
        src = case_dir / 'difference' / f'{name}.nii.gz'
        dst = case_dir / 'difference_prepared' / f'{name}.nii.gz'
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    save(ct_crop, 'ct.nii.gz')
    # Attach the prepared-CT intensity mapping (nibabel would otherwise choose its own).
    ct_path = case_dir / 'ct.nii.gz'
    raw = bytearray(gzip.open(ct_path).read())
    raw[112:120] = struct.pack('<ff', CT_SLOPE, CT_INTER)
    ct_path.write_bytes(gzip.compress(bytes(raw), 6))
    save(pred_native, 'pred.nii.gz')
    save(ref_crop, 'gt.nii.gz')
    (case_dir / 'difference').mkdir(exist_ok=True)
    nib.save(nib.Nifti1Image(difference(pred_native, ref_crop, 1), crop_affine), case_dir / 'difference' / 'pancreas.nii.gz')
    nib.save(nib.Nifti1Image(difference(pred_native, ref_crop, 2), crop_affine), case_dir / 'difference' / 'lesion.nii.gz')

    entry.update(stats)
    entry['spacing_mm'] = zooms
    entry['display_resolution'] = 'native'
    entry['display_provenance'] = {
        'ct': 'Original PanTS test-set CT, native spacing and orientation; index crop only; int16 HU with scl_slope 1/400, scl_inter 0.25 (prepared 0-1 scale)',
        'crop': f'slices = saved prediction pancreas extent +/-{SLICE_MARGIN_MM:g} mm; in-plane = body (HU>{BODY_HU:g}) +{BODY_MARGIN_MM:g} mm; no reference labels used',
        'prediction': 'Saved July SegResNet prediction (1.5 mm) resampled to the native crop: trilinear one-hot + argmax',
        'reference': 'PanTS native pancreas and pancreatic_lesion masks',
        'dice': 'Recomputed on the native crop for display; not a benchmark result',
        'prepared_files': '*_prepared.nii.gz and difference_prepared/ keep the previous 1.5 mm files',
        'alignment_gate_dice': gate,
    }
    args.results.write_text(json.dumps(results, indent=1) + '\n')
    print(f'  wrote native study and updated {args.results.name}')


if __name__ == '__main__':
    main()
