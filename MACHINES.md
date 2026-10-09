# MACHINES.md — PROWL compute register

Every agent (Codex, Claude) reads this before launching, sizing, or comparing a training run.
It records which physical machines exist, what each can run, and the rules for running two jobs
at once. Update a machine's section in place when its facts change; keep the date of each fact.

Created 2026-10-07 at Quinton's request (two laptops → two concurrent training jobs).

## Machines

| Tag | Machine | Role | Status |
|---|---|---|---|
| `mac` | 14" MacBook Pro, Apple M5 Pro | Canonical repository checkout, data caches, primary training | Active |
| `win` | Windows laptop | Second concurrent training job | **Inventory pending**: run `scripts/diagnostics/machine_inventory.ps1` and paste the result below |

Use the tag in every run name (for example `cap_baseline_wholebox_rspancreas_mac`) so archives,
ledgers and MLflow runs always say where they ran.

## `mac` — MacBook Pro (M5 Pro)

Source: owner-reported hardware (CLAUDE.md, historical) and repository inspection 2026-10-07.

| Item | Value |
|---|---|
| CPU / GPU | 18-core CPU, 20-core Apple GPU (Metal/MPS), 16-core Neural Engine |
| Memory | 64 GB unified (shared CPU/GPU, no separate VRAM limit) |
| Internal disk | 1 TB SSD (free space: check `df -h /` before a run; not recorded here) |
| Checkout | `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL` (location record only) |
| Python envs | `.venv312` (Python 3.12.13, torch 2.13.0, MONAI 1.6.0, MLflow 3.15.0) is the legacy long-trainer env; `.venv-prowl` (torch 2.13.0, MONAI 1.6.0, no MLflow) is the capstone test env |
| Device | `device: mps` in `configs/level45.yaml`; fp32; set `PYTORCH_ENABLE_MPS_FALLBACK=1` |
| Measured speed | Summer whole-box 128³ recipe: 24,000 updates ≈ 13–14 h after cache fill (`docs/experiments.md`, EXP-17c/EXP-24) |
| Preprocessed caches | `outputs/cache/` on the internal SSD (git-ignored). Built 2026-07-23..27, after the legacy trainer/transforms were last changed (2026-07-20/21) |
| External data drive | `PROWL-Data`, 4 TB WD Elements, **APFS** (Windows cannot read APFS natively) |
| Keep awake | Prefix long runs with `caffeinate -dimsu`; keep on power |

Notable caches (folder name → cases):

| Cache folder (under `outputs/cache/`) | Cases | Size |
|---|---|---|
| `v2-anat_scaledmax_clean_lmpancreas_lesion_prcombined_sp1.5_p128_wb1_cn16_cpNone_rspancreas_tr` | 1,412 | 24 GB |
| `v2-anat_val_lmpancreas_lesion_prcombined_sp1.5_p128_wb1_cn16_cpNone_rspancreas_val` | 20 | 0.3 GB |
| `v2-anat_fullhealthy_lmpancreas_lesion_prcombined_sp1.5_p128_wb1_cn16_cpNone_rsunion_tr` | 7,200 (entire train split) | 118 GB |
| `v2-anat_scaled1to3_lmpancreas_lesion_prcombined_sp1.5_p128_wb1_cn16_cpNone_rsunion_tr` | 2,824 | 46 GB |
| `v2-anat_val_lmpancreas_lesion_prcombined_sp1.5_p128_wb1_cn16_cpNone_rsunion_val` | 20 | 0.3 GB |

## `win` — Windows laptop

**Not yet inventoried.** Paste the output of `scripts/diagnostics/machine_inventory.ps1` here,
then summarize: GPU model and VRAM, driver/CUDA version, RAM, free disk, Python/torch/MONAI,
and whether a PROWL clone exists.

Known constraints before inventory:

- `configs/level45.yaml` says `device: mps`. On Windows, `src/training/trainer.py:get_device`
  silently falls back to **CPU** unless the device is set to `cuda`. A CUDA device override must
  exist and be verified (startup log shows a CUDA device) before any Windows run counts.
- It cannot read the APFS `PROWL-Data` drive. Move inputs by network share or an exFAT drive.
- A Git clone does not include git-ignored inputs. A run also needs `outputs/manifest.csv`,
  `outputs/splits/`, `pretrained_weights/supervised_suprem_segresnet_2100.pth`, and the exact
  cache folder(s) it will read.
- Cache reuse depends on identical manifest strings and the same MONAI version (cache files are
  keyed by a hash of each case record). A 30-update smoke test proves a cache hit: a miss fails
  fast with `FileNotFound` on a `/Volumes/JHU-PanTS/...` path.

## Rules for two concurrent jobs

1. One training job per machine at a time. Never run the same run name on both.
2. The Mac checkout is the canonical repository. Windows works from a clone at the same commit;
   record that commit in the run notes.
3. Pre-register each run in `docs/experiments.md` (plan first, outcome after) and name the machine.
4. A comparison between a `mac` run and a `win` run is not single-variable: MPS and CUDA differ
   numerically and in speed. Prefer putting both arms of a controlled comparison on one machine,
   or state the hardware difference as a confound.
5. Copy each Windows run archive (`outputs/checkpoints/pants-level45/runs/<run>/`) and its ledger
   row back to the Mac. MLflow databases are per-machine; note the source machine when merging.
6. Agents must not edit the same files at the same time. Before writing, check `git status`
   for another agent's uncommitted changes.
