#!/usr/bin/env python3
"""
Build PANORAMA demo material for a meeting.

Works straight from panorama_labels-main.zip — no extraction, no imaging download
required. If PANORAMA CT imaging is present it will overlay on the scan; otherwise
it renders the annotation masks on their own, which show all six structures.

    python scripts/build_demo_panorama.py \
        --zip /Volumes/JHU-PanTS/PANORAMA/panorama_labels-main.zip \
        --xlsx clinical_information.xlsx \
        --out ~/Desktop/capstone-demo

Optional: --imaging /path/to/batch_1  (folder of PANORAMA CT .nii.gz)
"""
import argparse, os, tempfile, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# PANORAMA label legend, verified against a real mask
LEGEND = {1: ("PDAC lesion", "#d84a4a"), 2: ("veins", "#3f7fd0"),
          3: ("arteries", "#a02020"), 4: ("pancreas parenchyma", "#1d9e75"),
          5: ("pancreatic duct", "#e0a020"), 6: ("common bile duct", "#8a5fc0")}
CMAP = ListedColormap(["#00000000"] + [LEGEND[i][1] for i in range(1, 7)])
NORM = BoundaryNorm(list(range(8)), CMAP.N)


def find_ct(imaging_dir, study_id):
    if not imaging_dir:
        return None
    for pat in (f"{study_id}.nii.gz", f"{study_id}_0000.nii.gz", f"{study_id}/ct.nii.gz"):
        p = Path(imaging_dir) / pat
        if p.exists():
            return str(p)
    return None


def render(mask_path, ct_path, title, subtitle, png):
    lab = np.asanyarray(nib.load(mask_path).dataobj).astype(np.int16)
    tgt = (lab == 1) if (lab == 1).any() else (lab == 4)
    z = int(np.round(np.argwhere(tgt)[:, 2].mean())) if tgt.any() else lab.shape[2] // 2
    sl = np.rot90(lab[:, :, z])

    ncol = 2 if ct_path else 1
    fig, axes = plt.subplots(1, ncol, figsize=(5.6 * ncol, 5.8), facecolor="white", squeeze=False)
    axes = axes[0]

    if ct_path:
        ct = np.asanyarray(nib.load(ct_path).dataobj).astype(np.float32)
        base = np.rot90(np.clip(ct[:, :, z], -100, 300))
        axes[0].imshow(base, cmap="gray"); axes[0].set_title("CT — abdominal window", fontsize=11)
        axes[1].imshow(base, cmap="gray")
        axes[1].imshow(np.ma.masked_where(sl == 0, sl), cmap=CMAP, norm=NORM, alpha=0.6)
        axes[1].set_title("PANORAMA annotation over CT", fontsize=11)
    else:
        axes[0].imshow(np.ma.masked_where(sl == 0, sl), cmap=CMAP, norm=NORM)
        axes[0].set_facecolor("#111")
        axes[0].set_title("PANORAMA annotation — 6 structures", fontsize=11)

    for a in axes:
        a.axis("off")
    present = sorted(set(np.unique(lab)) - {0})
    axes[-1].legend(handles=[Patch(facecolor=LEGEND[v][1], label=f"{v} · {LEGEND[v][0]}")
                             for v in present if v in LEGEND],
                    loc="lower right", fontsize=8, framealpha=0.9)
    fig.suptitle(f"{title}   ·   {subtitle}   ·   axial slice {z}", fontsize=12)
    fig.tight_layout(); fig.savefig(png, dpi=110, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default="/Volumes/JHU-PanTS/PANORAMA/panorama_labels-main.zip")
    ap.add_argument("--xlsx", default="clinical_information.xlsx")
    ap.add_argument("--imaging", default=None)
    ap.add_argument("--out", default=str(Path.home() / "Desktop" / "capstone-demo"))
    args = ap.parse_args()

    out = Path(args.out).expanduser()
    (out / "overlays_panorama").mkdir(parents=True, exist_ok=True)

    if not os.path.exists(args.xlsx):
        raise SystemExit(f"\n  clinical_information.xlsx not found at {args.xlsx}\n"
                         f"  Run from the repo root, or pass --xlsx.\n")
    df = pd.read_excel(args.xlsx)

    # The deduplication table needs only the spreadsheet, so write it BEFORE
    # touching the label archive. It survives an unmounted drive.
    lv = df.level.value_counts().rename_axis("reference_standard").reset_index(name="cases")
    lv["pdac_cases"] = lv.reference_standard.map(lambda s: int((df[df.level == s].label == "PDAC").sum()))
    lv["note"] = lv.reference_standard.map(
        lambda s: "ALREADY INSIDE PanTS -- EXCLUDED" if s in ("MSD_dataset", "NIH_dataset") else "")
    clean = df[~df.level.isin(["MSD_dataset", "NIH_dataset"])]
    lv.loc[len(lv)] = ["TOTAL", len(df), int((df.label == "PDAC").sum()), ""]
    lv.loc[len(lv)] = ["USABLE AFTER DEDUPLICATION", len(clean), int((clean.label == "PDAC").sum()),
                       f"{len(df)-len(clean)} cases and "
                       f"{int((df.label=='PDAC').sum()-(clean.label=='PDAC').sum())} tumours removed"]
    lv.to_csv(out / "panorama_level_breakdown.csv", index=False)
    print(f"  deduplication table written · usable {len(clean):,} cases, "
          f"{(clean.label=='PDAC').sum()} PDAC · "
          f"{df.PANORAMA_patient_id.nunique():,} patients across {len(df):,} studies\n")

    # preflight: locate the label archive, checking the likely places before giving up
    zp = Path(args.zip).expanduser()
    if not zp.exists():
        for alt in (Path.cwd() / "panorama_labels-main.zip",
                    Path.home() / "Downloads" / "panorama_labels-main.zip",
                    Path.home() / "Desktop" / "panorama_labels-main.zip"):
            if alt.exists():
                zp = alt; print(f"  using label archive at {zp}"); break
        else:
            raise SystemExit(
                f"\n  LABEL ARCHIVE NOT FOUND — {args.zip}\n"
                f"  If that path is on the external drive, it is not mounted "
                f"(check `ls /Volumes`).\n"
                f"  Otherwise download it and pass --zip:\n"
                f"    https://github.com/DIAGNijmegen/panorama_labels/archive/refs/heads/main.zip\n")
    z = zipfile.ZipFile(zp)
    members = {os.path.basename(n)[:-7]: n for n in z.namelist() if n.endswith(".nii.gz")}
    manual = {os.path.basename(n)[:-7] for n in z.namelist() if "/manual_labels/" in n}

    # deliberately varied: expert-annotated tumour, an excluded import, a healthy case
    picks = []
    def take(sel, note):
        for sid in sel:
            if sid in members:
                picks.append((sid, note)); return

    pdac_manual = df[(df.label == "PDAC") & (~df.level.isin(["MSD_dataset", "NIH_dataset"]))]
    take([s for s in pdac_manual.PANORAMA_study_id if s in manual],
         "PDAC · expert delineation · KEPT")
    take([s for s in df[df.level == "MSD_dataset"].PANORAMA_study_id],
         "Decathlon import · EXCLUDED (already inside PanTS)")
    take([s for s in df[(df.label == "non-PDAC") & (df.level == "radiology")].PANORAMA_study_id],
         "tumour-free · 3-year follow-up standard")

    tmp = tempfile.mkdtemp()
    rows = []
    for sid, note in picks:
        print(f"  {sid:<16} {note}")
        p = z.extract(members[sid], tmp)
        png = out / "overlays_panorama" / f"{sid}__{note.split('·')[0].strip().replace(' ','_')}.png"
        meta = df[df.PANORAMA_study_id == sid].iloc[0]
        try:
            render(p, find_ct(args.imaging, sid), sid,
                   f"{meta.label} · {meta.level} · {'expert' if sid in manual else 'automated'} mask", png)
        except Exception as e:
            print(f"     ! render failed: {e}")
        rows.append({"study_id": sid, "label": meta.label, "reference_standard": meta.level,
                     "mask": "expert" if sid in manual else "automated",
                     "age": meta.patient_age, "sex": meta.patient_sex,
                     "scanner": meta.scanner, "demo_note": note})
    pd.DataFrame(rows).to_csv(out / "panorama_case_details.csv", index=False)
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
