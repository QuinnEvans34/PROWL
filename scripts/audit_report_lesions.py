"""Triage the cases where a radiology report DESCRIBES a pancreas lesion but the mask is EMPTY.

Renders a contact sheet: one axial slice per case, centred on the pancreatic subregion the report
names (head / body / tail), with the pancreas outlined and the reported finding printed above it.

The question each tile answers: is there visibly a mass where the report says there is one?
  - visible mass  -> annotation was never done; report supervision is genuinely additive (R-Super premise)
  - nothing there -> the report is unreliable for this case; filter it out
  - mask garbage  -> a data-quality defect, not a missing annotation

Usage:
  python scripts/audit_report_lesions.py --n 12
  python scripts/audit_report_lesions.py --cases PanTS_00009725 PanTS_00005419
"""
import argparse, re, sys
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P

LESION_BLOCK = "Pancreas lesions:"


def clean(t):
    return str(t).replace("_x000D_", "")


def parse_report(text):
    """Pull the first reported lesion's location, 2-D size, volume, and enhancement."""
    if LESION_BLOCK not in text:
        return {}
    seg = text.split(LESION_BLOCK)[1].split("Kidney:")[0]
    g = lambda p: (re.search(p, seg).group(1).strip() if re.search(p, seg) else None)
    return {
        "location": g(r"Location:\s*([^.]+)\."),
        "size": g(r"Size:\s*([\d.]+\s*x\s*[\d.]+\s*cm)"),
        "volume_cc": g(r"Volume:\s*([\d.]+)\s*cc"),
        "enhancement": g(r"Enhancement relative to pancreas:\s*(\w+)"),
        "n_lesions": len(re.findall(r"Pancreas lesion \d+:", seg)),
    }


def subregion_for(location, row):
    """Map the report's stated location onto the matching subregion mask path."""
    loc = (location or "").lower()
    for key, col in (("head", "head_path"), ("body", "body_path"), ("tail", "tail_path")):
        if key in loc and isinstance(row.get(col), str):
            return row[col]
    return row.get("pancreas_path")


def load(path):
    img = nib.load(str(path))
    return np.asanyarray(img.dataobj)


def window(sl, lo=-100, hi=300):
    return np.clip((sl - lo) / (hi - lo), 0, 1)


def render(ax, row, info):
    cid = row["case_id"]
    try:
        ct = load(row["ct_path"]).astype(np.float32)
        panc = load(row["pancreas_path"]) > 0
        target = subregion_for(info.get("location"), row)
        focus = load(target) > 0 if isinstance(target, str) else panc
        if not focus.any():
            focus = panc
        if not focus.any():
            ax.text(.5, .5, f"{cid}\nno pancreas mask", ha="center", va="center",
                    color="#F96363", fontsize=8, transform=ax.transAxes)
            ax.axis("off"); return

        z = int(np.argmax(focus.sum(axis=(0, 1))))          # slice with most of the named subregion
        ax.imshow(np.rot90(window(ct[:, :, z])), cmap="gray", interpolation="nearest")
        pm = np.rot90(panc[:, :, z])
        if pm.any():
            ax.contour(pm.astype(float), levels=[.5], colors="#26C5A6", linewidths=.9)
        fm = np.rot90(focus[:, :, z])
        if fm.any():
            ax.contour(fm.astype(float), levels=[.5], colors="#F4BC55", linewidths=1.3)

        cap = (f"{cid}\n{info.get('location') or '?'} · {info.get('size') or '?'} · "
               f"{info.get('volume_cc') or '?'} cc · {info.get('enhancement') or '?'}")
        ax.set_title(cap, fontsize=7.5, color="#EDF5F7", pad=4)
    except Exception as e:
        ax.text(.5, .5, f"{cid}\n{type(e).__name__}", ha="center", va="center",
                color="#F96363", fontsize=8, transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#213444")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--n", type=int, default=12, help="how many cases to render")
    ap.add_argument("--cases", nargs="*", default=None, help="explicit case ids")
    ap.add_argument("--max-cc", type=float, default=None,
                    help="only cases whose reported volume is <= this (plausibility filter)")
    ap.add_argument("--min-cc", type=float, default=None, help="only cases >= this reported volume")
    ap.add_argument("--largest", action="store_true",
                    help="take the largest reported volumes instead of a random sample")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="outputs/report_lesion_audit.png")
    a = ap.parse_args()

    cfg = load_config(a.config)
    man = pd.read_csv(P.data_paths(cfg)["manifest"])
    man["rep"] = man["structured report"].fillna("").map(clean)

    cand = man[(~man["has_lesion"].astype(bool)) & (man["rep"].str.contains(LESION_BLOCK, regex=False))].copy()
    cand["info"] = cand["rep"].map(parse_report)
    cand["cc"] = cand["info"].map(lambda d: float(d.get("volume_cc") or 0))

    if a.cases:
        cand = cand[cand["case_id"].isin(a.cases)]
    else:
        if a.max_cc is not None:
            cand = cand[cand["cc"] <= a.max_cc]
        if a.min_cc is not None:
            cand = cand[cand["cc"] >= a.min_cc]
        # random sample by default — sorting by size cherry-picks the extremes and biases the read
        cand = (cand.sort_values("cc", ascending=False) if a.largest
                else cand.sample(min(a.n, len(cand)), random_state=a.seed))
    cand = cand.head(a.n)
    if cand.empty:
        sys.exit("no matching cases")

    print(f"rendering {len(cand)} case(s) — reported lesion, empty mask")
    n = len(cand); cols = min(4, n); rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.6 * cols, 4.0 * rows),
                             facecolor="#071019", squeeze=False)
    for ax in axes.flat:
        ax.set_facecolor("#071019"); ax.axis("off")
    for ax, (_, row) in zip(axes.flat, cand.iterrows()):
        ax.axis("on")
        info = row["info"]
        loc = info.get("location") or "?"
        siz = info.get("size") or "?"
        vol = info.get("volume_cc") or "?"
        print(f"  {row['case_id']}  {loc:<22} {siz:<14} {vol} cc")
        render(ax, row, info)

    fig.suptitle("Reports describing a pancreas lesion where the mask is EMPTY\n"
                 "teal = pancreas mask   ·   amber = reported subregion   ·   is a mass visibly present?",
                 color="#EDF5F7", fontsize=11, y=0.995)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(a.out, dpi=130, facecolor="#071019")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
