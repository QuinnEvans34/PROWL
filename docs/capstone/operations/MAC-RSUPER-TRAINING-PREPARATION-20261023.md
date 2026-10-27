# Authorized R-Super distillation: launch preparation

The user explicitly authorized setup and training with R-SuperPanTSMerlin. Actual
student distillation works on two real exposed cases, but the full scientific run
has not started. This is not a claim that KD improves segmentation.

## Completed engineering

Fresh production SegResNet initialized from the fixed SuPreM checkpoint, MPS
float32/fallback disabled,144-cube input, original24k learning-rate horizon,
DiceFocal/AdamW and existing augmentation/sampling functions. Two-case engineering
membership is explicit; these checkpoints are not scientific starting points.

- One supervised update and one zero-KD update matched complete state at existing
  rtol1.3e-6/atol1e-5; zero-KD did not read teacher targets.
- Two positive-KD updates used saved, pinned R-Super native probabilities from
  cases6222 then2720. Maximum KD weight0.1, temperature2,1000-update ramp retained.
  Actual weights0.0001/0.0002; KD losses1.492844/0.589467;
  eligible voxels2,973,398/2,159,741. All annotations retain supervised loss;
  teacher contradictions and ties do not contribute KD.
- Independent internal checkpoint copy verified SHA256
  `84a4e7c5ab7e5a4f1c3f1982e2ac6bc6190c500506e3c6364cefaf610185df61`.
  A fresh process restored it and matched the next complete student state at the
  original tolerance. This is not bit-exact long-run reproducibility.
- Producer20.68s/2,087,927,808B RSS; cold10.97s/2,199,027,712B;
  both exited0 with workers reaped. Five total engineering optimizer updates;
  zero scientific updates.66 focused tests passed in5.87s.

Evidence: external `distillation-mac-20261023/rsuper-real-kd-01/`.
The two-case provider, incomplete target manifest and checkpoints must not be
passed off as full1333-case admission or a shortened scientific experiment.

## Full-cohort cost and prerequisites

All4209 source files for1333train/70development exist,46.55GB compressed.
Byte-hash binding against transferred source identities is underway in
`rsuper-training-sources-01`; no repeated decoded-voxel coverage audit.
Internal88.997GB/external2.064TB free at inventory;50GB/100GiB floors pass.

Full metadata predicts110,248 teacher windows. Extrapolation from the selected
12-case pilot is89.6hours, not a guaranteed ETA. Raw native uint16 predictions
would total30.36GB; sample compression extrapolates0.777GB, also not guaranteed.
Only12 saved predictions currently exist. Full target preparation therefore
prevents a credible promise of full-cohort student training by morning.

Prepared builder reuses those12 outputs and generates remaining training targets
with the same fixed single-pass teacher policy. Bounds:96hours,12GiB owned RSS,
12GiB post-tile MPS allocation,31GiB output within32GiB combined cache, shared GPU
lock, AC, guardian and disk checks. Stop/preserve on failure; no automatic retry
or resume. No development teacher predictions. Complete prediction payloads still
require provider-bound cache admission before scientific training.

The paired full24k/control design remains the target. Remaining work includes
full corrected-label provider integration, complete teacher-target admission,
actual full-recipe recovery/executor/native-evaluation qualification and frozen
paired launch receipts. Scientific MLflow runs must record actual updates only.
No automatic student launch is embedded in the target builder.

## Laptop reference

The laptop reports matching source CT/mask identities and a verified R-Super
checkpoint download. Existing training still owns CUDA. Upstream source import
also needs isolated `batchgenerators`; failed import audit preserved. Upstream
bfloat16 accumulation and second-pass options differ from the Mac policy.
No upstream CUDA result yet; the Mac pilot does not establish upstream equivalence.
This evidence does not remove known teacher misses/false positives or unresolved
teacher training-membership limitations. Results remain exploratory.

## Launch update

Full source admission completed:1403cases/4209files match,512.56s,
563,789,824B peak owned RSS,exit0/reaped. Full training-target worker is now active
in `rsuper-full-targets-01`; observed first case6311 at25/105 windows. Follow
`progress.jsonl` (completed cases), `tiles.jsonl` (current inference), `worker.log`
and eventual `resources.json`/`result.json`. Current tool session21973 owns its
supervisor; do not duplicate or automatically retry. Caffeinate inhibits idle sleep
while the worker runs; keep AC/drive connected. This does not guarantee lid-closed
operation or survive a reboot.

No scientific student run or automatic student-launch chain exists. Full target
completion and remaining qualification are still required. Preserve all request
pins while this worker is active. Initial target-job dispatch and progress are
prerequisite work, not training hours or a model-quality result.

Laptop follow-up: isolated batchgenerators0.25.1 import now passes, but corrected
CPU import audit stops on upstream timm0.6.12 mutable-dataclass-default incompatibility
with Python3.12.14.33.64s/workers reaped; both failures preserved. Current training
reported17647/24000. An isolated compatible runtime or documented adaptation is
still needed; no upstream inference result exists. No model-quality inference
follows from this dependency failure.

## October27 CPU backup-failure qualification (W04-03)

Added `tests/test_kd_backup_boundaries.py`: twenty injected failures cover disk-full
(ENOSPC) and I/O errors (EIO) at initial, latest, scheduled and best checkpoints,
and scheduled/selected/terminal native reports and their component sidecars.
Each case runs the existing KD evidence executor with an invented two-update
session and tiny arrays. No production executor or scientific recipe changed.

All cases stop at the exact failed backup, propagate the original error, retain
source artifacts and earlier byte-identical copies, append a failed journal event,
and omit training completion/current native completion. No backup retry occurs;
reusing the failed output directory is rejected without altering its journal.
The existing actual checkpoint-stack CPU restore and positive evidence-copy tests
also pass:25tests total in4.04s, two upstream Torch deprecation warnings.

First collection in `.venv-retrieval` failed because that environment lacks MLflow;
no tests executed there. Reused the existing `.venv312` and external test dependencies
without installation. Reproduce with CUDA_VISIBLE_DEVICES=-1,OMP_NUM_THREADS=1,
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies,
`.venv312/bin/python -m pytest -q tests/test_kd_backup_boundaries.py
 tests/test_kd_evidence_executor_v1.py tests/test_kd_executor_recovery_v1.py`.

These are injected exception checks, not real drive-disconnection or process-kill
qualification, and do not prove full-provider MPS/native-evaluator readiness.
The teacher remains active and all329repository producing pins match. Full targets,
actual executor qualification and matched frozen launch receipts remain required;
no student training was launched. W04-03 remains gated, with this CPU slice complete.
