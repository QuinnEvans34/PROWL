#!/usr/bin/env python3
"""
Build a small, fast-to-open showcase folder of REAL data for a meeting.

Copies a handful of real PanTS cases (CT + pancreas mask + lesion mask) to the
internal SSD and pre-renders PNG overlays so nothing has to load in Finder.

    python scripts/build_demo_folder.py --out ~/Desktop/capstone-demo

Requires the external drive mounted (reads from the paths in outputs/manifest.csv).
"""
import argparse, os, shutil, textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def pick_cases(m: pd.DataFrame) -> pd.DataFrame:
    """Choose a small, deliberately varied set of real cases."""
    m = m.copy()
    m["vol"] = pd.to_numeric(m["lesion_volume_mm3"], errors="coerce")
    pos = m[m.has_lesion == 1].dropna(subset=["vol"])
    neg = m[m.has_lesion == 0]
    picks = []

    def take(df, note, n=1):
        for _, r in df.head(n).iterrows():
            r = r.copy(); r["demo_note"] = note; picks.append(r)

    # the 732 cc outlier — the case that proved MSD Task07 sits inside PanTS
    take(pos.sort_values("vol", ascending=False), "largest lesion in PanTS (732 cc)")
    # a typical tumour, near the median
    med = pos.vol.median()
    take(pos.assign(d=(pos.vol - med).abs()).sort_values("d"), "median-sized lesion (~5 cc)")
    # a small tumour — the class the model over-segments 3-13x
    take(pos[pos.vol.between(300, 1200)].sort_values("vol"), "small lesion (<1 cc) — hardest class")
    # healthy pancreata, two contrast phases
    for phase in ("Venous", "Non-contrast"):
        sel = neg[neg["ct phase"] == phase]
        if len(sel):
            take(sel, f"tumour-free, {phase.lower()} phase")

    out = pd.DataFrame(picks).drop_duplicates(subset="case_id")
    return out


def render(ct_p, panc_p, les_p, title, note, png_path):
    ct = nib.load(ct_p); arr = np.asanyarray(ct.dataobj).astype(np.float32)
    panc = np.asanyarray(nib.load(panc_p).dataobj) > 0 if panc_p and os.path.exists(panc_p) else None
    les = np.asanyarray(nib.load(les_p).dataobj) > 0 if les_p and os.path.exists(les_p) else None

    # slice through the lesion if there is one, else through the pancreas
    ref = les if (les is not None and les.any()) else panc
    z = int(np.round(np.argwhere(ref)[:, 2].mean())) if ref is not None and ref.any() else arr.shape[2] // 2

    sl = arr[:, :, z]
    sl = np.clip(sl, -100, 300)                       # abdominal window
    sl = (sl + 100) / 400.0

    fig, ax = plt.subplots(1, 2, figsize=(11, 5.6), facecolor="white")
    for a in ax:
        a.imshow(np.rot90(sl), cmap="gray", vmin=0, vmax=1)
        a.axis("off")
    ax[0].set_title("CT — abdominal window", fontsize=11)

    if panc is not None:
        ax[1].contour(np.rot90(panc[:, :, z]), levels=[0.5], colors="#1d9e75", linewidths=1.1)
    if les is not None and les[:, :, z].any():
        m = np.ma.masked_where(~np.rot90(les[:, :, z]), np.rot90(les[:, :, z]))
        ax[1].imshow(m, cmap=matplotlib.colors.ListedColormap(["#d84a4a"]), alpha=0.55)
    ax[1].set_title("expert annotation — pancreas outline, lesion filled", fontsize=11)

    fig.suptitle(f"{title}   ·   {note}   ·   axial slice {z}", fontsize=12)
    fig.tight_layout()
    fig.savefig(png_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="outputs/manifest.csv")
    ap.add_argument("--out", default=str(Path.home() / "Desktop" / "capstone-demo"))
    ap.add_argument("--copy-nifti", action="store_true",
                    help="also copy the raw .nii.gz files (adds a few hundred MB)")
    args = ap.parse_args()

    out = Path(args.out).expanduser()
    (out / "overlays").mkdir(parents=True, exist_ok=True)
    if args.copy_nifti:
        (out / "cases").mkdir(exist_ok=True)

    m = pd.read_csv(args.manifest, low_memory=False)
    sel = pick_cases(m)

    # preflight: the manifest lives in the repo, the volumes live on the external
    # drive. Fail here with one clear line rather than once per case.
    probe = next((p for p in sel.ct_path if isinstance(p, str)), None)
    if probe and not os.path.exists(probe):
        root = "/" + probe.strip("/").split("/")[0] + "/" + probe.strip("/").split("/")[1]
        raise SystemExit(
            f"\n  DRIVE NOT MOUNTED — {root} is not present.\n"
            f"  The manifest resolved fine, but the scans are on the external drive.\n"
            f"  Reconnect it (check `ls /Volumes`) and rerun.\n")

    print(f"selected {len(sel)} cases\n")

    rows = []
    for i, r in sel.iterrows():
        cid, note = r.case_id, r.demo_note
        vol = r.get("vol")
        vtxt = f"{vol/1000:.1f} cc" if pd.notna(vol) else "no lesion"
        print(f"  {cid:<18} {note}")
        png = out / "overlays" / f"{cid}__{note.split('—')[0].strip().replace(' ','_')}.png"
        try:
            render(r.ct_path, r.get("pancreas_path"), r.get("lesion_path"), cid, note, png)
        except Exception as e:
            print(f"     ! render failed: {e}")
        if args.copy_nifti:
            d = out / "cases" / cid; d.mkdir(exist_ok=True)
            for src, name in ((r.ct_path, "ct.nii.gz"),
                              (r.get("pancreas_path"), "pancreas.nii.gz"),
                              (r.get("lesion_path"), "lesion.nii.gz")):
                if isinstance(src, str) and os.path.exists(src):
                    shutil.copy2(src, d / name)
        rows.append({"case_id": cid, "note": note, "lesion": vtxt,
                     "phase": r.get("ct phase"), "manufacturer": r.get("manufacturer"),
                     "site": str(r.get("site detail"))[:40], "shape": r.get("shape"),
                     "spacing": r.get("spacing")})

    pd.DataFrame(rows).to_csv(out / "case_details.csv", index=False)

    (out / "README.md").write_text(textwrap.dedent(f"""\
        # Capstone — real data samples

        A small slice of the working datasets, pulled from the external drive so it
        opens instantly. The full archive is 382 GB across ~9,901 scans and does not
        browse well in Finder.

        - `overlays/` — rendered axial slices, CT beside the expert annotation.
          Green outline = pancreas, red fill = lesion. **Open these first.**
        - `case_details.csv` — the manifest row for each case: lesion volume,
          contrast phase, scanner, institution, voxel dimensions, spacing.
        {"- `cases/` — the actual NIfTI volumes for these cases." if args.copy_nifti else ""}

        ## The full picture, for scale

        | | |
        |---|---|
        | PanTS scans on the drive | 9,901 (9,000 train / 901 official test) |
        | tumour-positive | 1,033 — 10.4% |
        | annotated structures per case | 28 |
        | archive size | 382 GB compressed |
        | PANORAMA, second dataset | 2,238 cases, 676 tumours, 1,964 usable after deduplication |

        Selected cases span the largest lesion in the dataset (732 cc), a median
        lesion (~5 cc), a sub-centimetre lesion — the class the model over-segments
        most — and tumour-free pancreata in two contrast phases.
        """), encoding="utf-8")

    print(f"\n→ {out}")
    print("   open the overlays folder; everything is a PNG and loads instantly")


if __name__ == "__main__":
    main()
