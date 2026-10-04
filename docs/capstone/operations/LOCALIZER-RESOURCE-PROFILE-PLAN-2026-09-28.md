# Localizer MPS resource profile plan

September 28, 2026. D-272: Quinton explicitly requested resource profiling. Scope is synthetic
local compute and internal diagnostic artifacts, not real CT training, production run activation,
external writes, downloads or edits to Claude's lane.

## Fixed workload and acceptance

Use the reviewed scratch binary SegResNet (4,700,914 parameters), float32, one 96³ patch per update,
AdamW LR 0.003/weight decay 1e-5, cosine horizon 40, seed 42, two CPU threads, zero data workers/cache.
Reuse the existing patch sampler and loss. Synthetic normalized volumes have shapes 136×96×98 and
108×96×134, matching retained preprocessed dimensions but containing no patient values. Synthetic
foreground is a centered rectangular block; no anatomical/model-quality claim.

Two warm-up updates followed by six measured updates. Synchronize MPS before/after each timing.
Record sampler/copy-inclusive update time and raw loss, finite logits/gradients/parameters.
Full-volume image-only sliding-window inference: 96³, batch 1, overlap 0.25, constant blending,
MPS predictor and CPU stitching; two repeats of each shape. No target-derived inference crop.
Save one CPU-portable model/optimizer/scheduler checkpoint, fsync/hash/read it, restore on MPS and
compare the same fixed patch probabilities with absolute tolerance 1e-5, relative tolerance 0.
One extra resumed update must have finite loss/gradients (nine total updates). Do not claim bitwise
MPS continuation or production checkpoint publication from this diagnostic serialization check.

## Controls before execution

- MPS required; PYTORCH_ENABLE_MPS_FALLBACK=0 in worker before importing torch. No CUDA/fallback.
- AC power required at start and monitored. Record hardware, packages, Git base/status and allowlisted
  source text before compute. Capture no credentials or arbitrary environment values.
- One cooperating profile owner via persistent nonblocking flock; inspect process names before launch.
  This is cooperative task exclusion, not proof that other applications never use the GPU.
- Parent deadline 600 seconds, polling 0.25 seconds; RSS cap 16 GiB; MPS allocator budget 16 GiB
  (fraction of its reported recommended maximum), driver allocation cap 16 GiB at stage boundaries.
  These overlap and must not be summed as independent physical memory. Polling is not instantaneous.
- Internal output cap 256 MiB and 100 GiB free-space floor; no external artifact-root activation.
- Stop on unsupported operations, OOM, nonfinite values, failed monitoring/power, timeout, cap or
  reload mismatch. Preserve every attempted package and traceback. No automatic shape/budget retry.

Owned changes: new diagnostic script/tests, this plan and handback, shared decisions/checkpoint/
readiness/notebook entries. Existing CPU checkpoint identity remains synthetic-CPU-only.

## Interpretation

Report raw samples, median/range, observed RSS and MPS allocation samples, checkpoint transfer/write/
read/reload timings and bytes. First inference per shape includes shape-specific startup; no false
cold-disk claim. OS cache is uncontrolled. Source loading/preprocessing is excluded; reuse its prior
measured evidence only as a labeled provisional estimate, not a current source benchmark.
Project a candidate 100-update, two-case smoke with full-volume checks, checkpoint overhead and at
least 25% contingency. Local feasibility for this smoke does not settle full capstone D-210.
Production run binding, external checkpoint/backup performance, keeper restore and exact launch plan
remain separate tasks. No real-data run starts from a favorable benchmark alone.
