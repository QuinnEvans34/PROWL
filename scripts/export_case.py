#!/usr/bin/env python3
"""Export showcase cases for the NiiVue 3D viewer (static-first UI, docs/ui.md §5).

For each case it writes, in the model's whole-box input space so everything aligns:
  <out>/<case_id>/ct.nii.gz     preprocessed CT (what the model saw)
  <out>/<case_id>/gt.nii.gz     ground-truth 3-class mask (0 bg / 1 pancreas / 2 lesion)
  <out>/<case_id>/pred.nii.gz   predicted 3-class mask
  <out>/<case_id>/mesh/*.obj    world-aligned surface meshes (pancreas + lesion, pred + gt)
  <out>/results.json            per-case CADe summary (merged across runs)

The React + NiiVue app renders the CT volume in 3D and overlays the meshes.

Pick the showcase trio first with --list (runs the model over the val set and prints
per-case flags + Dice), then export the three you choose:
  --list                                 -> table to pick healthy / tumor / wrong-prediction
  --case PanTS_XXXX [--case PanTS_YYYY]   -> export those cases

Preprocessing flags MUST match the checkpoint's training recipe (whole-box example):
  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/export_case.py \
    --ckpt outputs/checkpoints/pants-level45/wholebox_p128_1p5_GOOD.pt \
    --case PanTS_00001234 --crop-native 16 --whole-box --roi 128 --spacing 1.5
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.dataset import get_dataset
from src.models.segresnet import build_model
from src.training import trainer as T
from src.inference.sliding_window import predict_volume

from monai.data import DataLoader


def dice(a, b) -> float:
    a, b = np.asarray(a).astype(bool), np.asarray(b).astype(bool)
    s = int(a.sum() + b.sum())
    return 1.0 if s == 0 else 2.0 * int((a & b).sum()) / s


def get_affine(meta_tensor) -> np.ndarray:
    """Pull the 4x4 world affine out of a (possibly batched) MONAI MetaTensor."""
    aff = getattr(meta_tensor, "affine", None)
    if aff is None:
        return np.eye(4)
    aff = aff.detach().cpu().numpy() if hasattr(aff, "detach") else np.asarray(aff)
    return aff.reshape(-1, 4, 4)[0]


def save_nifti(arr, affine, path):
    import nibabel as nib
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(np.asarray(arr), affine), str(path))


def _vertex_normals(verts, faces):
    """Area-weighted smooth vertex normals for stable web lighting."""
    verts = np.asarray(verts, dtype=np.float64)
    faces = np.asarray(faces, dtype=np.int64)
    normals = np.zeros_like(verts)
    tri = verts[faces]
    face_normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for corner in range(3):
        np.add.at(normals, faces[:, corner], face_normals)
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0] = 1.0
    return (normals / lengths[:, None]).astype(np.float32)


def write_obj(verts, faces, path):
    """OBJ writer with explicit smooth normals. Faces are 1-indexed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"v {v[0]:.3f} {v[1]:.3f} {v[2]:.3f}" for v in verts]
    normals = _vertex_normals(verts, faces)
    lines += [f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}" for n in normals]
    lines += [
        f"f {t[0]+1}//{t[0]+1} {t[1]+1}//{t[1]+1} {t[2]+1}//{t[2]+1}"
        for t in faces
    ]
    path.write_text("\n".join(lines) + "\n")


def rewrite_obj_with_normals(path):
    """Upgrade a prepared OBJ in place without changing its vertices or faces."""
    verts, faces = [], []
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            verts.append([float(value) for value in line.split()[1:4]])
        elif line.startswith("f "):
            faces.append([int(token.split("/")[0]) - 1 for token in line.split()[1:4]])
    if verts and faces:
        write_obj(np.asarray(verts, dtype=np.float32), np.asarray(faces, dtype=np.int64), path)


def _taubin_smooth(verts, faces, iters=12, lam=0.53, mu=-0.53):
    """Taubin (lambda/mu) mesh smoothing: relaxes vertices toward neighbor averages to
    remove marching-cubes facets while (unlike plain Laplacian) preserving volume/shape.
    Vectorized with a sparse adjacency; fast enough for showcase meshes."""
    from scipy import sparse
    n = len(verts)
    f = np.asarray(faces)
    I = np.concatenate([f[:, 0], f[:, 1], f[:, 2], f[:, 1], f[:, 2], f[:, 0]])
    J = np.concatenate([f[:, 1], f[:, 2], f[:, 0], f[:, 0], f[:, 1], f[:, 2]])
    A = (sparse.coo_matrix((np.ones(len(I)), (I, J)), shape=(n, n)) > 0).astype(np.float64).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    deg[deg == 0] = 1.0
    L = sparse.diags(1.0 / deg) @ A          # row-normalized neighbor average
    V = verts.astype(np.float64)
    for _ in range(iters):
        V = V + lam * (L @ V - V)
        V = V + mu * (L @ V - V)
    return V.astype(np.float32)


def surface(field, affine, iso=0.5, presmooth=0.7, taubin=12):
    """A clean surface from a scalar field (a model probability channel, or a smoothed
    binary mask). Gaussian pre-smoothing turns the hard voxel steps into a smooth
    isosurface; Taubin smoothing polishes the mesh. Verts are mapped index->world (mm)
    via the affine. Returns (verts_world, faces) or None if the field never crosses `iso`.

    This is deliberately faithful, not invented detail: the model outputs a continuous
    probability, and meshing that field is closer to what it computed than a hard 0/1 mask."""
    from skimage import measure
    from scipy import ndimage
    v = np.asarray(field, dtype=np.float32)
    if presmooth and presmooth > 0:
        v = ndimage.gaussian_filter(v, sigma=presmooth)
    if float(v.max()) < iso:
        return None
    verts, faces, _, _ = measure.marching_cubes(v, level=iso)
    if taubin and taubin > 0 and len(verts):
        verts = _taubin_smooth(verts, faces, iters=int(taubin))
    world = (affine @ np.c_[verts, np.ones(len(verts))].T).T[:, :3]
    return world, faces


def export_difference_assets(pred, gt, affine, out, cid, files, presmooth=0.7, taubin=12):
    """Create presentation-only agreement/discrepancy assets from authoritative masks.

    Meshes use the same smoothing as the main prediction/reference surfaces
    (Gaussian 0.7 + 12 Taubin passes). Lighter smoothing left one-voxel slivers
    whose faces coincided with neighbouring regions and rendered as speckle.
    Consequence: discrepancies thinner than about one voxel may produce no 3D
    surface; they remain exact in the 2D difference volume written here."""
    files.setdefault("difference", {})
    files.setdefault("mesh", {})

    anatomy_masks = {
        "pancreas": (pred > 0, gt > 0),
        "lesion": (pred == 2, gt == 2),
    }
    for anatomy, (pred_mask, gt_mask) in anatomy_masks.items():
        agreement = pred_mask & gt_mask
        pred_only = pred_mask & ~gt_mask
        gt_only = gt_mask & ~pred_mask
        label = np.zeros(pred.shape, dtype=np.int16)
        label[agreement] = 1
        label[pred_only] = 2
        label[gt_only] = 3

        nifti_rel = f"{cid}/difference/{anatomy}.nii.gz"
        save_nifti(label, affine, out / nifti_rel)
        files["difference"][anatomy] = nifti_rel

        for region, field in (
            ("agreement", agreement),
            ("pred_only", pred_only),
            ("gt_only", gt_only),
        ):
            mesh = surface(
                field.astype(np.float32),
                affine,
                iso=0.5,
                presmooth=presmooth,
                taubin=taubin,
            )
            name = f"{anatomy}_{region}"
            if mesh is None:
                stale = files["mesh"].pop(name, None)
                if stale and (out / stale).exists():
                    (out / stale).unlink()
                continue
            rel = f"{cid}/mesh/{name}.obj"
            write_obj(mesh[0], mesh[1], out / rel)
            files["mesh"][name] = rel


def derive_existing_demo_assets(out, presmooth=0.7, taubin=12):
    """Retrofit discrepancy volumes/meshes and explicit normals into a prepared demo folder."""
    import nibabel as nib

    results_path = out / "results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"No prepared manifest found at {results_path}")
    results = json.loads(results_path.read_text())

    for cid, item in results.items():
        files = item.get("files", {})
        pred_path = out / files.get("pred", "")
        gt_path = out / files.get("gt", "")
        if not pred_path.exists() or not gt_path.exists():
            print(f"  ! skipping {cid}: prepared pred/gt mask missing")
            continue
        pred_img = nib.load(str(pred_path))
        gt_img = nib.load(str(gt_path))
        pred = np.asarray(pred_img.dataobj).astype(np.int16)
        gt = np.asarray(gt_img.dataobj).astype(np.int16)
        if pred.shape != gt.shape:
            print(f"  ! skipping {cid}: pred/gt shapes differ")
            continue
        export_difference_assets(
            pred,
            gt,
            pred_img.affine,
            out,
            cid,
            files,
            presmooth=presmooth,
            taubin=taubin,
        )
        for mesh_path in files.get("mesh", {}).values():
            prepared_mesh = out / mesh_path
            if prepared_mesh.exists():
                rewrite_obj_with_normals(prepared_mesh)
        item["files"] = files
        item["display_mesh_version"] = "v3-difference-main-smoothing"
        print(f"  + {cid}: discrepancy volumes and meshes")

    results_path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"updated {results_path} ({len(results)} case(s))")


def load_full_ct(cfg, ct_path, downsample_mm=2.0):
    """Load the ORIGINAL full abdomen CT in RAS world space (optionally downsampled for the
    web), windowed to [0,1]. The affine is RAS-consistent with the whole-box meshes, so the
    organ surfaces land in the right place inside the full scan. Returns (array, affine)."""
    from monai.transforms import (Compose, LoadImaged, EnsureChannelFirstd,
                                   Orientationd, Spacingd, ScaleIntensityRanged)
    pre = cfg["preprocessing"]
    hu_lo, hu_hi = pre["hu_window"]
    tfs = [LoadImaged(keys="image"), EnsureChannelFirstd(keys="image"),
           Orientationd(keys="image", axcodes=pre.get("orientation", "RAS"))]
    if downsample_mm:
        tfs.append(Spacingd(keys="image", pixdim=(downsample_mm,) * 3, mode="bilinear"))
    tfs.append(ScaleIntensityRanged(keys="image", a_min=hu_lo, a_max=hu_hi, b_min=0.0, b_max=1.0, clip=True))
    img = Compose(tfs)({"image": ct_path})["image"]
    return img[0].cpu().numpy().astype(np.float32), get_affine(img)


def infer_case(cfg, model, device, split, case_id):
    ds = get_dataset(cfg, split, train=False, cache=False, ids=[case_id])
    batch = next(iter(DataLoader(ds, batch_size=1, num_workers=0)))
    img = batch["image"].to(device)
    with torch.no_grad():
        logits = predict_volume(model, img, cfg, device)
    probs = torch.softmax(logits, dim=1)[0].cpu().numpy()   # (3,H,W,D)
    pred = probs.argmax(0).astype(np.int16)
    ct = img[0, 0].cpu().numpy().astype(np.float32)
    gt = batch["label"][0, 0].cpu().numpy().astype(np.int16)
    affine = get_affine(batch["image"])
    return ct, gt, pred, probs, affine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--case", action="append", default=[], help="case_id to export (repeatable)")
    ap.add_argument("--split", default="val")
    ap.add_argument("--out", default="outputs/ui_cases")
    ap.add_argument("--list", action="store_true", help="scan the val set and print a per-case table to pick the trio")
    ap.add_argument("--list-n", type=int, default=25, help="how many val cases to scan in --list mode")
    # preprocessing overrides (MUST match the checkpoint's training recipe)
    ap.add_argument("--roi", type=int, default=None)
    ap.add_argument("--spacing", type=float, default=None)
    ap.add_argument("--crop-native", type=int, default=None)
    ap.add_argument("--crop-pancreas", type=float, default=None)
    ap.add_argument("--whole-box", action="store_true")
    ap.add_argument("--smooth-sigma", type=float, default=0.7,
                    help="Gaussian pre-smoothing of the field before marching cubes (0 = off, more = smoother)")
    ap.add_argument("--taubin", type=int, default=12,
                    help="Taubin mesh-smoothing iterations (0 = off; ~12 gives a clean organ surface)")
    ap.add_argument("--full-ct", action="store_true",
                    help="also export the full abdomen CT (fun mode); meshes land on it via world-consistent affines")
    ap.add_argument("--full-ct-mm", type=float, default=2.0,
                    help="downsample spacing for the full CT export, to keep the web volume small")
    ap.add_argument("--derive-existing", action="store_true",
                    help="retrofit difference assets into an existing prepared demo folder; no model or dataset required")
    args = ap.parse_args()

    if args.derive_existing:
        derive_existing_demo_assets(
            Path(args.out),
            presmooth=args.smooth_sigma,
            taubin=args.taubin,
        )
        return
    if not args.ckpt:
        ap.error("--ckpt is required unless --derive-existing is used")

    cfg = load_config(args.config)
    if args.roi:
        cfg["sampling"]["patch_size"] = [args.roi] * 3
        cfg["inference"]["sw_roi_size"] = [args.roi] * 3
    if args.spacing:
        cfg["preprocessing"]["target_spacing"] = [args.spacing] * 3
    if args.crop_native is not None:
        cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
    if args.crop_pancreas is not None:
        cfg["preprocessing"]["crop_to_pancreas_margin_mm"] = args.crop_pancreas
    if args.whole_box:
        cfg["preprocessing"]["whole_box"] = True
    set_seed(get(cfg, "seed", 42))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    spacing = np.array(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5]), dtype=float)
    vox_mm3 = float(spacing.prod())

    model = build_model(cfg).to(device)
    T.load_checkpoint(args.ckpt, model, map_location=device)
    model.eval()

    import pandas as pd
    man = pd.read_csv(dp["manifest"])
    vset = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}

    # --- LIST mode: help pick a healthy / tumor / wrong-prediction trio ---
    if args.list:
        vdf = man[man["case_id"].isin(vset)]
        # mix of tumor-positive and healthy so all three archetypes appear
        pos = vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist()[: args.list_n // 2]
        neg = vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist()[: args.list_n // 2]
        print(f"{'case_id':<18} {'gt_tumor':>8} {'pred_tumor':>10} {'lesion_dice':>11} {'panc_dice':>9}")
        print("-" * 60)
        for cid in pos + neg:
            ct, gt, pred, probs, aff = infer_case(cfg, model, device, args.split, cid)
            flag = int((pred == 2).sum()) * vox_mm3 >= get(cfg, "inference.postprocess.lesion_min_volume_mm3", 50)
            print(f"{cid:<18} {str(bool((gt==2).any())):>8} {str(flag):>10} "
                  f"{dice(pred==2, gt==2):>11.3f} {dice(pred==1, gt==1):>9.3f}")
        print("\nPick: a healthy case (gt_tumor False, pred_tumor False), a tumor case (both True, "
              "high lesion_dice), and a wrong case (a False/True mismatch = false alarm or a miss).")
        return

    if not args.case:
        ap.error("give --case CASE_ID (repeatable), or --list to pick the trio first")

    out = Path(args.out)
    results_path = out / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}

    for cid in args.case:
        print(f"\n=== exporting {cid} ===")
        ct, gt, pred, probs, affine = infer_case(cfg, model, device, args.split, cid)
        cdir = out / cid
        save_nifti(ct, affine, cdir / "ct.nii.gz")
        save_nifti(gt.astype(np.int16), affine, cdir / "gt.nii.gz")
        save_nifti(pred.astype(np.int16), affine, cdir / "pred.nii.gz")

        files = {
            "ct": f"{cid}/ct.nii.gz",
            "gt": f"{cid}/gt.nii.gz",
            "pred": f"{cid}/pred.nii.gz",
            "mesh": {},
        }

        if args.full_ct:
            ctp = man.loc[man["case_id"] == cid, "ct_path"]
            if len(ctp):
                fct, faff = load_full_ct(cfg, ctp.iloc[0], downsample_mm=args.full_ct_mm)
                save_nifti(fct, faff, cdir / "ct_full.nii.gz")
                files["ct_full"] = f"{cid}/ct_full.nii.gz"
                print(f"  + full CT {tuple(fct.shape)} @ {args.full_ct_mm}mm")
        # Smooth surfaces. Prediction meshes come from the model's PROBABILITY field
        # (smoother and more faithful than the hard argmax); the pancreas shell uses
        # pancreas+lesion probability so the tumor is not carved out of the organ.
        mesh_specs = [
            ("pancreas_pred", probs[1] + probs[2]),
            ("lesion_pred",   probs[2]),
            ("pancreas_gt",   (gt > 0).astype(np.float32)),
            ("lesion_gt",     (gt == 2).astype(np.float32)),
        ]
        for name, fld in mesh_specs:
            m = surface(fld, affine, iso=0.5, presmooth=args.smooth_sigma, taubin=args.taubin)
            if m is not None:
                rel = f"{cid}/mesh/{name}.obj"
                write_obj(m[0], m[1], out / rel)
                files["mesh"][name] = rel

        export_difference_assets(pred, gt, affine, out, cid, files)

        lesion_vox = int((pred == 2).sum())
        results[cid] = {
            "case_id": cid,
            "gt_has_lesion": bool((gt == 2).any()),
            "pred_has_lesion": lesion_vox > 0,
            "lesion_volume_mm3": round(lesion_vox * vox_mm3, 1),
            "dice_pancreas": round(dice(pred == 1, gt == 1), 3),
            "dice_lesion": round(dice(pred == 2, gt == 2), 3),
            "confidence": round(float(probs[2][pred == 2].mean()) if lesion_vox > 0 else 0.0, 3),
            "spacing_mm": spacing.tolist(),
            "display_mesh_version": "v2-explicit-normals-difference",
            "files": files,
        }
        print(f"  saved CT/gt/pred + {len(files['mesh'])} meshes -> {cdir}")
        print(f"  lesion {results[cid]['lesion_volume_mm3']} mm3, "
              f"dice panc {results[cid]['dice_pancreas']} / lesion {results[cid]['dice_lesion']}")

    out.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {results_path} ({len(results)} case(s)). Point the NiiVue app at {out}/.")


if __name__ == "__main__":
    main()
