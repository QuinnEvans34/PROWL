#!/usr/bin/env python3
"""Precompute radiologist-review assets for a native-resolution Workbench study.

Display/review aids only. Spec:
docs/capstone/interface/WORKBENCH-RADIOLOGIST-TOOLSET-SPEC-20261120.md

Inputs (case directory produced by scripts/export_native_workbench_case.py):
  ct.nii.gz, pred.nii.gz, gt.nii.gz            native crop grid
  ct_prepared.nii.gz, pred_prepared.nii.gz     1.5 mm model grid (confidence map)
  --labels    PanTS segmentations directory (reference anatomy)
  --checkpoint/--config  the saved segmenter that produced pred_prepared

Outputs (in the case directory): smoothed surfaces in mesh/, reference anatomy
(anatomy.nii.gz + mesh/anatomy_*.obj), confidence.nii.gz, cpr_*.png and
insights.json; results.json gains the new file entries.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import deque
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import splev, splprep
from scipy.spatial import ConvexHull
from skimage import measure, morphology
import trimesh

ANATOMY = [  # (label value, PanTS file, display name, kind)
    (1, 'superior_mesenteric_artery', 'SMA', 'artery'),
    (2, 'celiac_artery', 'Celiac artery', 'artery'),
    (3, 'veins', 'Portal / SMV / splenic veins', 'vein'),
    (4, 'aorta', 'Aorta', 'artery'),
    (5, 'postcava', 'IVC', 'vein'),
    (6, 'common_bile_duct', 'Common bile duct', 'duct'),
    (7, 'pancreatic_duct', 'Pancreatic duct', 'duct'),
]
BANDS = [('contact', 0.0, 2.0), ('near', 2.0, 5.0), ('close', 5.0, 10.0), ('far', 10.0, 1e9)]
CONTACT_TOLERANCE_VOX = 1
ISO_MM = 0.8
SMOOTH_SIGMA_MM = 0.8
CPR_HALF_WIDTH_MM, CPR_STEP_MM = 30.0, 0.25
DUCT_UPPER_NORMAL_MM = {'pancreatic_duct': 3.0, 'common_bile_duct': 7.0}


def spacing(img):
    return np.array(img.header.get_zooms()[:3], float)


def load(path):
    img = nib.load(str(path))
    return img, np.asarray(img.dataobj)


# ---------------------------------------------------------------- surfaces
def surface(mask: np.ndarray, affine: np.ndarray, zooms: np.ndarray, margin_mm: float = 4.0):
    """Smooth, volume-preserving surface of a binary mask in world (NIfTI) coordinates."""
    if not mask.any():
        return None
    idx = np.argwhere(mask)
    pad = np.ceil(margin_mm / zooms).astype(int) + 2
    lo = np.maximum(idx.min(0) - pad, 0)
    hi = np.minimum(idx.max(0) + pad + 1, mask.shape)
    sub = mask[tuple(slice(a, b) for a, b in zip(lo, hi))].astype(np.float32)
    factors = zooms / ISO_MM
    iso = ndimage.zoom(sub, factors, order=1)
    iso = ndimage.gaussian_filter(iso, SMOOTH_SIGMA_MM / ISO_MM)
    if iso.max() < 0.5:
        return None
    verts, faces, _, _ = measure.marching_cubes(iso, 0.5)
    # iso index -> source index -> world
    src = verts / factors + lo
    world = nib.affines.apply_affine(affine, src)
    mesh = trimesh.Trimesh(world, faces[:, ::-1] if np.linalg.det(affine[:3, :3]) < 0 else faces, process=True)
    trimesh.smoothing.filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=12)
    # Quadric decimation keeps the smoothed shape at a browser-friendly size.
    if len(mesh.faces) > 6000:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=max(6000, len(mesh.faces) // 3))
        except Exception as error:  # fast-simplification missing: keep full resolution
            print(f'  decimation skipped: {error}')
    mesh.fix_normals()
    return mesh


def write_obj(mesh, path: Path):
    if mesh is None or not len(mesh.faces):
        return False
    mesh.export(str(path), file_type='obj', include_normals=False, include_texture=False)
    return True


# ---------------------------------------------------------------- geometry helpers
def edt_mm(mask: np.ndarray, zooms) -> np.ndarray:
    """Distance (mm) to the nearest voxel of mask; inf when mask is empty."""
    if not mask.any():
        return np.full(mask.shape, np.inf, np.float32)
    return ndimage.distance_transform_edt(~mask, sampling=zooms).astype(np.float32)


def slice_axis_of(zooms) -> int:
    return int(np.argmax(np.asarray(zooms) + np.array([0, 0, 1e-6])))


def take_slice(arr, axis, k):
    return np.take(arr, k, axis=axis)


def contact_angle(vessel: np.ndarray, lesion: np.ndarray, axis: int, inplane_mm):
    """Max circumferential tumour contact (degrees) over slices and vessel components."""
    best = {'angle_deg': 0.0, 'slice': None}
    if not vessel.any() or not lesion.any():
        return best
    grow = ndimage.binary_dilation(lesion, iterations=CONTACT_TOLERANCE_VOX)
    ks = np.where(np.logical_and(vessel, grow).any(axis=tuple(a for a in range(3) if a != axis)))[0]
    for k in ks:
        v2, l2 = take_slice(vessel, axis, k), take_slice(grow, axis, k)
        comps, n = ndimage.label(v2)
        for c in range(1, n + 1):
            comp = comps == c
            boundary = comp & ~ndimage.binary_erosion(comp)
            contact = boundary & l2
            if not contact.any() or boundary.sum() < 4:
                continue
            cy, cx = np.argwhere(comp).mean(0)
            pts = np.argwhere(boundary)
            ang = np.degrees(np.arctan2((pts[:, 0] - cy) * inplane_mm[0], (pts[:, 1] - cx) * inplane_mm[1])) % 360
            bins_all = set(np.floor(ang).astype(int))
            hit = np.argwhere(contact)
            ang_hit = np.degrees(np.arctan2((hit[:, 0] - cy) * inplane_mm[0], (hit[:, 1] - cx) * inplane_mm[1])) % 360
            covered = 0
            hit_bins = set(np.floor(ang_hit).astype(int))
            # Close 1-degree gaps between neighbouring contact pixels on small vessels.
            spread = set()
            for b in hit_bins:
                for d in range(-3, 4):
                    if (b + d) % 360 in bins_all:
                        spread.add((b + d) % 360)
            covered = len(spread)
            angle = 360.0 * covered / max(len(bins_all), 1)
            if angle > best['angle_deg']:
                best = {'angle_deg': round(float(angle), 0), 'slice': int(k)}
    return best


def feret(points_mm: np.ndarray):
    """Longest diameter and the width perpendicular to it (mm)."""
    if len(points_mm) < 3:
        return 0.0, 0.0
    try:
        hull = points_mm[ConvexHull(points_mm).vertices]
    except Exception:
        hull = points_mm
    d = np.linalg.norm(hull[:, None] - hull[None], axis=-1)
    i, j = np.unravel_index(np.argmax(d), d.shape)
    longest = float(d[i, j])
    u = (hull[j] - hull[i]) / max(longest, 1e-6)
    perp = np.array([-u[1], u[0]])
    proj = hull @ perp
    return longest, float(proj.max() - proj.min())


def lesion_diameters(lesion, axis, inplane_mm):
    best = {'long_axis_mm': 0.0, 'short_axis_mm': 0.0, 'slice': None}
    for k in np.where(lesion.any(axis=tuple(a for a in range(3) if a != axis)))[0]:
        sl = take_slice(lesion, axis, k)
        comps, n = ndimage.label(sl)
        for c in range(1, n + 1):
            pts = np.argwhere(comps == c).astype(float)
            # use voxel corners so a 1-voxel lesion still has extent
            corners = np.concatenate([pts + [dy, dx] for dy in (-.5, .5) for dx in (-.5, .5)])
            long_mm, short_mm = feret(corners * inplane_mm)
            if long_mm > best['long_axis_mm']:
                best = {'long_axis_mm': round(long_mm, 1), 'short_axis_mm': round(short_mm, 1), 'slice': int(k)}
    return best


def max_calibre_mm(mask, axis, inplane_mm):
    """Twice the largest in-plane inscribed radius over slices (duct calibre)."""
    best = 0.0
    for k in np.where(mask.any(axis=tuple(a for a in range(3) if a != axis)))[0]:
        sl = take_slice(mask, axis, k)
        r = ndimage.distance_transform_edt(np.pad(sl, 1), sampling=inplane_mm).max()
        best = max(best, 2.0 * float(r))
    return round(best, 1)


# ---------------------------------------------------------------- curved reformat
def centreline(mask, affine, zooms):
    """Ordered, smoothed centreline of a tubular mask in world mm (head = patient right first)."""
    factors = zooms / 1.0
    iso = ndimage.zoom(mask.astype(np.float32), factors, order=1) > 0.5
    iso = ndimage.binary_closing(ndimage.binary_opening(iso, iterations=1), iterations=2)
    comps, n = ndimage.label(iso)
    if n == 0:
        return None
    iso = comps == (np.argmax(np.bincount(comps.ravel())[1:]) + 1)
    skel = morphology.skeletonize(iso)
    pts = np.argwhere(skel)
    if len(pts) < 10:
        return None
    index = {tuple(p): i for i, p in enumerate(pts)}
    offsets = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
    nbrs = [[index[t] for t in ((p[0] + a, p[1] + b, p[2] + c) for a, b, c in offsets) if t in index] for p in pts]

    def bfs(start):
        dist = np.full(len(pts), -1)
        prev = np.full(len(pts), -1)
        dist[start] = 0
        q = deque([start])
        while q:
            u = q.popleft()
            for v in nbrs[u]:
                if dist[v] < 0:
                    dist[v], prev[v] = dist[u] + 1, u
                    q.append(v)
        return dist, prev

    d0, _ = bfs(0)
    a = int(np.argmax(d0))
    da, prev = bfs(a)
    b = int(np.argmax(da))
    path = [b]
    while path[-1] != a:
        path.append(int(prev[path[-1]]))
    ordered = pts[path] / factors  # back to source index space
    world = nib.affines.apply_affine(affine, ordered)
    if world[0, 0] > world[-1, 0]:  # RAS: smaller x = patient right = head
        world = world[::-1]
    if len(world) < 6:
        return None
    tck, _ = splprep(world.T, s=len(world) * 4.0)
    dense = np.array(splev(np.linspace(0, 1, 2000), tck)).T
    seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
    arc = np.concatenate([[0], np.cumsum(seg)])
    samples = np.arange(0, arc[-1], CPR_STEP_MM)
    out = np.stack([np.interp(samples, arc, dense[:, i]) for i in range(3)], 1)
    return out, float(arc[-1])


def straightened_cpr(volume_world_sampler, line):
    tangents = np.gradient(line, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True) + 1e-9
    anterior = np.array([0.0, 1.0, 0.0])
    normals = anterior - (tangents @ anterior)[:, None] * tangents
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-9
    offsets = np.arange(CPR_HALF_WIDTH_MM, -CPR_HALF_WIDTH_MM - 1e-6, -CPR_STEP_MM)  # anterior at top
    grid = line[None, :, :] + offsets[:, None, None] * normals[None, :, :]
    return volume_world_sampler(grid), offsets


def sampler(arr, affine, order):
    inv = np.linalg.inv(affine)

    def run(grid_world):
        shape = grid_world.shape[:-1]
        ijk = nib.affines.apply_affine(inv, grid_world.reshape(-1, 3)).T
        out = ndimage.map_coordinates(arr, ijk, order=order, mode='constant', cval=-1024 if order else 0)
        return out.reshape(shape)
    return run


def window_u8(hu, level=40, width=400):
    lo = level - width / 2
    return np.clip((hu - lo) / width * 255, 0, 255).astype(np.uint8)


def contour_rgba(label_img, colours):
    h, w = label_img.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    for value, colour in colours.items():
        m = label_img == value if not callable(value) else value(label_img)
        edge = m & ~ndimage.binary_erosion(m)
        rgba[edge] = colour
    return rgba


# ---------------------------------------------------------------- confidence
def confidence_map(case_dir: Path, checkpoint: Path, config: Path, repo: Path):
    import torch
    import yaml
    sys.path.insert(0, str(repo))
    from src.models.segresnet import build_model
    cfg = yaml.safe_load(config.read_text())
    ck = torch.load(str(checkpoint), map_location='cpu', weights_only=False)
    net = build_model(cfg)
    net.load_state_dict(ck.get('model', ck), strict=True)
    net.eval()
    prep_img, x = load(case_dir / 'ct_prepared.nii.gz')
    _, saved = load(prepared_path(case_dir, 'pred'))
    x = torch.from_numpy(np.asarray(x, np.float32))[None, None]
    probs = []
    with torch.no_grad():
        for flips in [(), (2,), (3,), (4,), (2, 3), (2, 4), (3, 4), (2, 3, 4)]:
            xi = torch.flip(x, flips) if flips else x
            yi = net(xi).softmax(1)
            probs.append((torch.flip(yi, flips) if flips else yi)[0].numpy())
    identity = probs[0].argmax(0)
    agreement = float((identity == saved).mean())
    if agreement < 0.999:
        raise SystemExit(f'Model does not reproduce the saved prediction ({agreement:.4f}); confidence map refused')
    mean = np.mean(probs, axis=0)
    entropy = -(mean * np.log(np.clip(mean, 1e-8, 1))).sum(0) / np.log(3)
    tta_label = mean.argmax(0)
    return prep_img, entropy.astype(np.float32), agreement, tta_label


def prepared_path(case_dir: Path, name: str) -> Path:
    p = case_dir / f'{name}_prepared.nii.gz'
    return p if p.exists() else case_dir / f'{name}.nii.gz'


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--case-dir', type=Path, required=True)
    ap.add_argument('--labels', type=Path, required=True)
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--checkpoint', type=Path)
    ap.add_argument('--config', type=Path, default=Path('configs/level45.yaml'))
    ap.add_argument('--repo', type=Path, default=Path('.'))
    args = ap.parse_args()
    case_dir, case_id = args.case_dir, args.case_dir.name

    ct_img, ct = load(case_dir / 'ct.nii.gz')
    # The stored int16 values are HU; scl_slope/inter only map them to the prepared 0-1 display scale.
    hu = np.asarray(ct_img.dataobj.get_unscaled(), np.float32)
    ct = hu
    aff, zooms = ct_img.affine, spacing(ct_img)
    _, pred = load(case_dir / 'pred.nii.gz')
    _, gt = load(case_dir / 'gt.nii.gz')
    lesion, pancreas = pred == 2, pred >= 1
    axis = slice_axis_of(zooms)
    inplane = np.array([z for i, z in enumerate(zooms) if i != axis])
    print(f'{case_id}: grid {ct.shape} @ {np.round(zooms, 3)} mm, slice axis {axis}, lesion voxels {int(lesion.sum())}')

    # Reference anatomy, resampled onto the CT crop grid by world coordinates (nearest).
    native_like = nib.load(str(args.labels / 'pancreas.nii.gz'))
    inv_native = np.linalg.inv(native_like.affine)
    ii = np.indices(ct.shape).reshape(3, -1).T
    native_idx = np.rint(nib.affines.apply_affine(inv_native @ aff, ii)).astype(int)
    inside = np.all((native_idx >= 0) & (native_idx < native_like.shape), axis=1)

    def on_grid(name):
        src = np.asarray(nib.load(str(args.labels / f'{name}.nii.gz')).dataobj) > 0
        out = np.zeros(ct.shape, bool).reshape(-1)
        out[inside] = src[tuple(native_idx[inside].T)]
        return out.reshape(ct.shape)

    anatomy = np.zeros(ct.shape, np.uint8)
    structures = {}
    for value, name, label, kind in ANATOMY:
        m = on_grid(name)
        anatomy[m & (anatomy == 0)] = value
        structures[name] = (value, label, kind, m)
    nib.save(nib.Nifti1Image(anatomy, aff), case_dir / 'anatomy.nii.gz')

    # Surfaces ---------------------------------------------------------------
    mesh_dir = case_dir / 'mesh'
    backup = case_dir / 'mesh_prepared'
    if mesh_dir.exists() and not backup.exists():
        shutil.copytree(mesh_dir, backup)
    mesh_dir.mkdir(exist_ok=True)
    meshes = {}
    sets = {
        'pancreas_pred': pancreas, 'lesion_pred': lesion,
        'pancreas_gt': gt >= 1, 'lesion_gt': gt == 2,
        'pancreas_agreement': pancreas & (gt >= 1), 'pancreas_pred_only': pancreas & ~(gt >= 1), 'pancreas_gt_only': ~pancreas & (gt >= 1),
        'lesion_agreement': lesion & (gt == 2), 'lesion_pred_only': lesion & ~(gt == 2), 'lesion_gt_only': ~lesion & (gt == 2),
    }
    for key, m in sets.items():
        # Thin difference shells are noise at display scale; keep only components >= 20 mm^3.
        if key.endswith('_only') and m.any():
            comps, n = ndimage.label(m)
            sizes = ndimage.sum(m, comps, range(1, n + 1)) * np.prod(zooms)
            m = np.isin(comps, np.where(sizes >= 20)[0] + 1)
        path = mesh_dir / f'{key}.obj'
        if write_obj(surface(m, aff, zooms), path):
            meshes[key] = f'{case_id}/mesh/{key}.obj'
        elif path.exists():
            path.unlink()

    lesion_dist = edt_mm(lesion, zooms)
    anatomy_meshes, vessels = {}, []
    for value, name, label, kind in ANATOMY:
        m = structures[name][3]
        mesh = surface(m, aff, zooms, margin_mm=3.0)
        if mesh is None:
            continue
        key = f'anatomy_{name}'
        write_obj(mesh, mesh_dir / f'{key}.obj')
        anatomy_meshes[key] = f'{case_id}/mesh/{key}.obj'
        record = {'name': name, 'label': label, 'kind': kind, 'value': value,
                  'volume_ml': round(float(m.sum() * np.prod(zooms) / 1000), 2)}
        if lesion.any():
            record['min_distance_mm'] = round(float(lesion_dist[m].min()), 1)
            if kind != 'duct':
                ca = contact_angle(m, lesion, axis, inplane)
                record['contact_angle_deg'] = ca['angle_deg']
                record['contact_slice'] = ca['slice']
                record['contact_category'] = ('none' if ca['angle_deg'] == 0 else 'abutment' if ca['angle_deg'] <= 180 else 'encasement')
                # distance-banded copies of the vessel surface
                vd = nib.affines.apply_affine(np.linalg.inv(aff), mesh.vertices)
                vd = ndimage.map_coordinates(lesion_dist, vd.T, order=1, mode='nearest')
                face_d = vd[mesh.faces].min(1)
                for band, lo, hi in BANDS:
                    sel = np.where((face_d >= lo) & (face_d < hi))[0]
                    if len(sel):
                        part = mesh.submesh([sel], append=True)
                        bkey = f'anatomy_{name}__{band}'
                        write_obj(part, mesh_dir / f'{bkey}.obj')
                        anatomy_meshes[bkey] = f'{case_id}/mesh/{bkey}.obj'
        if kind == 'duct':
            record['max_calibre_mm'] = max_calibre_mm(m, axis, inplane) if m.any() else None
            record['upper_normal_mm'] = DUCT_UPPER_NORMAL_MM[name]
            record['dilated'] = bool(record['max_calibre_mm'] and record['max_calibre_mm'] > DUCT_UPPER_NORMAL_MM[name])
        vessels.append(record)
    for value, name, label, kind in ANATOMY:
        if not structures[name][3].any():
            vessels.append({'name': name, 'label': label, 'kind': kind, 'value': value, 'annotated': False})

    # Lesion characteristics --------------------------------------------------
    lesion_info = {'present': bool(lesion.any())}
    if lesion.any():
        dia = lesion_diameters(lesion, axis, inplane)
        sub = {}
        for part in ('pancreas_head', 'pancreas_body', 'pancreas_tail'):
            sub[part] = on_grid(part)
        labels_sub = np.zeros(ct.shape, np.uint8)
        for i, part in enumerate(sub, start=1):
            labels_sub[sub[part]] = i
        if labels_sub.any():
            _, nearest = ndimage.distance_transform_edt(labels_sub == 0, sampling=zooms, return_indices=True)
            assigned = labels_sub[tuple(nearest[:, lesion])]
            counts = np.bincount(assigned, minlength=4)[1:]
            share = counts / max(counts.sum(), 1)
            names = ['head', 'body', 'tail']
            location = {names[i]: round(float(share[i]) * 100) for i in range(3)}
            primary = names[int(np.argmax(share))]
        else:
            location, primary = {}, None
        parenchyma = ndimage.binary_erosion(pancreas & ~lesion, iterations=1)
        core = ndimage.binary_erosion(lesion, iterations=1) if ndimage.binary_erosion(lesion, iterations=1).sum() > 20 else lesion
        les_hu, par_hu = float(np.mean(hu[core])), float(np.mean(hu[parenchyma])) if parenchyma.any() else None
        delta = None if par_hu is None else les_hu - par_hu
        attenuation = None if delta is None else ('hypoattenuating' if delta <= -10 else 'hyperattenuating' if delta >= 10 else 'isoattenuating')
        lesion_info.update({
            **dia,
            'volume_ml': round(float(lesion.sum() * np.prod(zooms) / 1000), 2),
            'location': primary, 'location_share_pct': location,
            'lesion_mean_hu': round(les_hu), 'parenchyma_mean_hu': None if par_hu is None else round(par_hu),
            'attenuation_delta_hu': None if delta is None else round(delta), 'attenuation': attenuation,
        })

    # Curved reformat along the predicted pancreas ------------------------------
    cpr = None
    cl = centreline(pancreas, aff, zooms)
    if cl is not None:
        line, length = cl
        ct_s, offsets = straightened_cpr(sampler(hu, aff, 1), line)
        lab_s, _ = straightened_cpr(sampler(pred.astype(np.float32), aff, 0), line)
        ana_s, _ = straightened_cpr(sampler(anatomy.astype(np.float32), aff, 0), line)
        gt_s, _ = straightened_cpr(sampler(gt.astype(np.float32), aff, 0), line)
        Image.fromarray(window_u8(ct_s)).save(case_dir / 'cpr_ct.png')
        Image.fromarray(contour_rgba(lab_s, {
            (lambda a: a >= 1): (38, 197, 166, 255), 2: (249, 99, 99, 255)}), 'RGBA').save(case_dir / 'cpr_prediction.png')
        Image.fromarray(contour_rgba(gt_s, {
            (lambda a: a >= 1): (56, 189, 248, 255), 2: (251, 191, 36, 255)}), 'RGBA').save(case_dir / 'cpr_reference.png')
        ana_rgba = contour_rgba(ana_s, {1: (244, 114, 182, 255), 2: (232, 121, 249, 255), 3: (96, 165, 250, 255),
                                        4: (248, 113, 113, 255), 5: (129, 140, 248, 255), 6: (52, 211, 153, 255), 7: (163, 230, 53, 255)})
        Image.fromarray(ana_rgba, 'RGBA').save(case_dir / 'cpr_anatomy.png')
        cols = np.where((lab_s == 2).any(0))[0]
        cpr = {
            'ct': f'{case_id}/cpr_ct.png', 'prediction': f'{case_id}/cpr_prediction.png',
            'reference': f'{case_id}/cpr_reference.png', 'anatomy': f'{case_id}/cpr_anatomy.png',
            'length_mm': round(length, 1), 'width_mm': round(2 * CPR_HALF_WIDTH_MM, 1), 'step_mm': CPR_STEP_MM,
            'pixels': [int(ct_s.shape[1]), int(ct_s.shape[0])],
            'lesion_span_mm': None if not len(cols) else [round(cols.min() * CPR_STEP_MM, 1), round(cols.max() * CPR_STEP_MM, 1)],
            'orientation': 'Head (patient right) on the left, tail on the right; anterior at the top',
            'method': 'Straightened reformat along the smoothed skeleton of the predicted pancreas; window L40/W400',
        }

    # Confidence -----------------------------------------------------------------
    confidence = None
    if args.checkpoint:
        prep_img, entropy, agreement, tta_label = confidence_map(case_dir, args.checkpoint, args.config, args.repo)
        ii2 = np.indices(ct.shape).reshape(3, -1).T
        src = nib.affines.apply_affine(np.linalg.inv(prep_img.affine) @ aff, ii2).T
        ent = ndimage.map_coordinates(entropy, src, order=1, mode='constant', cval=0).reshape(ct.shape)
        near = ndimage.binary_dilation(pancreas, iterations=4) if pancreas.any() else np.ones(ct.shape, bool)
        pct = np.clip(np.rint(ent * 100), 0, 100).astype(np.uint8)
        pct[~near] = 0
        nib.save(nib.Nifti1Image(pct, aff), case_dir / 'confidence.nii.gz')
        boundary = lesion & ~ndimage.binary_erosion(lesion) if lesion.any() else pancreas & ~ndimage.binary_erosion(pancreas)
        tta_lesion_ml = float((tta_label == 2).sum() * np.prod(spacing(prep_img)) / 1000)
        confidence = {
            'file': f'{case_id}/confidence.nii.gz', 'units': 'normalised entropy x100 (0 certain, 100 maximally uncertain)',
            'display_threshold': 20, 'reproduction_agreement': round(agreement, 5),
            'uncertain_share_of_prediction_pct': round(float((pct[pancreas] >= 50).mean() * 100), 1) if pancreas.any() else None,
            'mean_boundary_uncertainty': round(float(pct[boundary].mean()), 1) if boundary.any() else None,
            'flip_average_lesion_ml': round(tta_lesion_ml, 2),
            'method': '8 flip views of the saved SegResNet on its prepared 1.5 mm input; entropy of the averaged softmax, resampled to the native grid',
        }

    insights = {
        'schema': 'prowl.workbench.insights.v1', 'case_id': case_id,
        'grid': {'shape': list(ct.shape), 'spacing_mm': [round(float(z), 4) for z in zooms], 'slice_axis': axis},
        'lesion': lesion_info, 'anatomy': vessels, 'cpr': cpr, 'confidence': confidence,
        'provenance': {
            'model': 'Saved July SegResNet prediction (Segmenter v1, step 18000) resampled to the native grid',
            'anatomy': 'PanTS reference annotations (not model output): vessels, ducts and pancreas subregions',
            'contact': f'Axial slices; vessel boundary within {CONTACT_TOLERANCE_VOX} voxel of the predicted lesion, degrees around the vessel centroid; max over slices and components',
            'diameters': 'Feret diameter of the predicted lesion on the axial slice with the longest diameter, plus the perpendicular width',
            'attenuation': 'Mean HU of the eroded predicted lesion vs eroded remaining predicted pancreas; +/-10 HU thresholds',
            'surfaces': f'Marching cubes on {ISO_MM} mm isotropic, Gaussian {SMOOTH_SIGMA_MM} mm smoothed masks, Taubin 12 iterations',
            'scope': 'Review aids for the demo; not a resectability or diagnostic call',
        },
    }
    (case_dir / 'insights.json').write_text(json.dumps(insights, indent=1) + '\n')

    results = json.loads(args.results.read_text())
    entry = results[case_id]
    files = entry.setdefault('files', {})
    files['mesh'] = {**{k: v for k, v in files.get('mesh', {}).items() if not k.startswith('anatomy_') and k in meshes}, **meshes, **anatomy_meshes}
    files['anatomy'] = f'{case_id}/anatomy.nii.gz'
    files['insights'] = f'{case_id}/insights.json'
    if confidence:
        files['confidence'] = confidence['file']
    if cpr:
        files['cpr'] = {k: cpr[k] for k in ('ct', 'prediction', 'reference', 'anatomy')}
    entry['display_mesh_version'] = 'v4-native-taubin'
    args.results.write_text(json.dumps(results, indent=1) + '\n')
    print(json.dumps({'lesion': lesion_info, 'anatomy': vessels, 'cpr': cpr and {k: cpr[k] for k in ('length_mm', 'lesion_span_mm')},
                      'confidence': confidence and {k: confidence[k] for k in ('reproduction_agreement', 'mean_boundary_uncertainty', 'flip_average_lesion_ml')},
                      'meshes': sorted(list(meshes) + list(anatomy_meshes))}, indent=1))


if __name__ == '__main__':
    main()
