#!/usr/bin/env python3
"""Make Workbench display assets faster to load. Display-only; no model output changes.

1. Surfaces: every mesh listed in results.json files.mesh is rewritten as gzipped MZ3
   (NiiVue's binary surface format) next to the OBJ, and results.json points at the MZ3.
   Binary surfaces are ~4x smaller and skip text parsing in the browser. OBJ files stay.
2. Region CT: for native-resolution studies, `ct_region.nii.gz` is the native CT cropped to
   the saved prediction's pancreas box (+ margin). The 3D "Region" scene uses it, so Region
   is a real pancreas-region view again (the native `ct` spans the whole body in-plane).
   The crop uses the prediction only, never reference labels.

Usage:
  python3 scripts/optimize_workbench_assets.py --results ui/public/cases/results.json [--case PanTS_x ...]
"""
from __future__ import annotations

import argparse
import gzip
import json
import struct
from pathlib import Path

import nibabel as nib
import numpy as np
import trimesh

REGION_MARGIN_MM = (25.0, 25.0, 15.0)
CT_SLOPE, CT_INTER = 1.0 / 400.0, 0.25


def write_mz3(obj_path: Path, mz3_path: Path) -> tuple[int, int]:
    mesh = trimesh.load(str(obj_path), process=False, force='mesh')
    faces = np.ascontiguousarray(mesh.faces, dtype='<u4')
    verts = np.ascontiguousarray(mesh.vertices, dtype='<f4')
    header = struct.pack('<HHIII', 23117, 3, len(faces), len(verts), 0)  # magic, attr face|vert
    mz3_path.write_bytes(gzip.compress(header + faces.tobytes() + verts.tobytes(), 6))
    return len(faces), len(verts)


def write_region_ct(case_dir: Path, ct_rel: str, pred_rel: str) -> str | None:
    ct_img = nib.load(str(case_dir.parent / ct_rel))
    pred = np.asarray(nib.load(str(case_dir.parent / pred_rel)).dataobj)
    idx = np.argwhere(pred > 0)
    if not len(idx):
        return None
    zooms = np.array(ct_img.header.get_zooms()[:3], dtype=float)
    pad = np.ceil(np.array(REGION_MARGIN_MM) / zooms).astype(int)
    lo = np.maximum(idx.min(0) - pad, 0)
    hi = np.minimum(idx.max(0) + pad + 1, ct_img.shape[:3])
    if np.prod(hi - lo) > 0.7 * np.prod(ct_img.shape[:3]):
        return None  # already a region-sized crop (prepared studies)
    raw = np.asarray(ct_img.dataobj.get_unscaled())
    crop = np.ascontiguousarray(raw[tuple(slice(a, b) for a, b in zip(lo, hi))])
    affine = ct_img.affine.copy()
    affine[:3, 3] = nib.affines.apply_affine(ct_img.affine, lo)
    header = ct_img.header.copy()
    out = nib.Nifti1Image(crop.astype(raw.dtype), affine, header)
    out.set_qform(affine, code=int(ct_img.header['qform_code']) or 1)
    out.set_sform(affine, code=int(ct_img.header['sform_code']) or 1)
    rel = f'{case_dir.name}/ct_region.nii.gz'
    path = case_dir.parent / rel
    nib.save(out, str(path))
    slope, inter = ct_img.dataobj.slope, ct_img.dataobj.inter
    if not (np.isclose(slope, 1.0) and np.isclose(inter, 0.0)):
        data = bytearray(gzip.open(path).read())
        data[112:120] = struct.pack('<ff', float(slope), float(inter))
        path.write_bytes(gzip.compress(bytes(data), 6))
    check = nib.load(str(path))
    assert np.allclose(check.dataobj.slope, slope) and np.allclose(check.dataobj.inter, inter)
    assert np.allclose(np.asarray(check.dataobj)[:2, :2, :2], np.asarray(ct_img.dataobj)[tuple(slice(a, a + 2) for a in lo)])
    print(f'  region {tuple(int(v) for v in hi - lo)} of {ct_img.shape[:3]}')
    return rel


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--case', action='append', default=[])
    args = ap.parse_args()
    root = args.results.parent
    results = json.loads(args.results.read_text())
    for case_id, entry in results.items():
        if args.case and case_id not in args.case:
            continue
        files = entry.get('files', {})
        case_dir = root / case_id
        print(case_id)
        meshes = files.get('mesh') or {}
        before = after = 0
        for key, rel in list(meshes.items()):
            src = root / rel
            if rel.endswith('.mz3'):
                obj = src.with_suffix('.obj')
                if not obj.exists():
                    continue
                src = obj
            if not src.exists():
                continue
            dst = src.with_suffix('.mz3')
            write_mz3(src, dst)
            before += src.stat().st_size
            after += dst.stat().st_size
            meshes[key] = str(dst.relative_to(root))
        if meshes:
            print(f'  meshes {len(meshes)}: {before / 1e6:.1f} MB OBJ -> {after / 1e6:.1f} MB MZ3')
        if entry.get('display_resolution') == 'native' and files.get('ct') and files.get('pred'):
            region = write_region_ct(case_dir, files['ct'], files['pred'])
            if region:
                files['ct_region'] = region
                entry.setdefault('display_provenance', {})['ct_region'] = (
                    'Native CT cropped to the saved prediction pancreas box + 25 mm in-plane / 15 mm slices; '
                    'no reference labels used')
    args.results.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
