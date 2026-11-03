# Lenovo training-time reconciliation — November 3, 2026

QUINNS-LAPTOP is Lenovo model21FWS0DU00 (read-only Win32_ComputerSystem identity). The current nine-run dashboard-equivalent total is **964,509.828 seconds =267.9193967 hours**. The earlier six-run751,607.078 seconds =208.7797439 hours is a subset of this same Lenovo history, not Mac time.

These are recorded scientific training-session seconds, including in-loop validation, checkpointing and I/O. They are not optimizer-only, GPU-busy or human active hours. No calendar start/end subtraction was used. All nine journals have one start and no resume event or elapsed-counter reset. The stopped full-coverage attempt is included through its last measured update; no overnight pause or separate retry interval was invented. OS sleep cannot be separated from monotonic counters using these records alone.

| Experiment | Recorded seconds | Hours | MLflow run ID |
|---|---:|---:|---|
| Candidate generator with reserved verifier patients | 80018.000 | 22.227222 | 0acb9a8f7e8a463194dd599a01b78507 |
| Varied lesion-focused views without losing coverage | 126111.219 | 35.030894 | a84c0a6ae0cb424ca182350425adc7aa |
| Pancreas-assisted outlining with complete coverage | 259622.672 | 72.117409 | 1edf56ad4b7b48a5a5baa0e729e46a5c |
| Preserve full lesion coverage and detail | 78830.906 | 21.897474 | ecb6e402f0f84bc8a9df5e11239e5972 |
| PanTS with varied training views | 75647.875 | 21.013299 | dbf1a562e9eb4d5a96301718a19d07a8 |
| Longer PanTS training + EMA | 204494.015 | 56.803893 | 38cdd18be83449da87275f5ef8b12898 |
| Add expert PANORAMA lesions | 67675.813 | 18.798837 | c038332411df4f38bf52d650810c77c0 |
| PanTS-only baseline | 65335.797 | 18.148833 | 67d11609cc78406b86145f13e24ec61b |
| Reject false lesion candidates while preserving real lesions | 6773.531 | 1.881536 | 4475886fbdbf41c8a02d4f814a9733ac |

All nine MLflow IDs represent the same journal-backed work. Add them **zero additional times**. Two early runs were backfilled: their stored source-history hashes exactly match the journals. The other six local MLflow entries are setup, training-fit evaluation, standalone native checkpoint evaluation or input qualification, and are excluded. Metric timestamps from imports are not training clocks.

Native validation is included in the longer-EMA, full-coverage, pancreas-region and varied-focus sessions. Explicit native intervals total29,698.891 seconds (stopped full-coverage),45,743.876 seconds (pancreas-region),48,588.888 seconds (varied-focus). EMA native work lacks paired monotonic phase boundaries, so its exact split is not asserted. Augmentation uses training_completed and excludes its subsequent963.875-second final native evaluation tail. Early baseline/PANORAMA journals lack timed final completion, so their counters omit the final validation/checkpoint tail. The verifier session includes tuning; the generator has no development selection.

## Independent resource receipts (not additive time)

These cover the same processes plus setup/teardown overhead. Do not add them to journals or replace inconsistent boundaries silently.

- `E:/PROWL/readiness/pants-ema-72k-20261013-a01/training-resources.json`: 204508.828 seconds, workers_reaped=True; SHA256 `aad23254ea1ac1a61994eaa360461bfe5694d0a668fcac40829c98f747e843a6`.
- `E:/PROWL/readiness/pancreas-region-20261019-a01/scientific-resources.json`: 259643.859 seconds, workers_reaped=True; SHA256 `18dbb949a9e3737549547d8d723d2b90e99bf0fd69395f5f5b64bc9f8cf545cf`.
- `E:/PROWL/readiness/varied-deterministic-20261022-a02/scientific-resources.json`: 126137.328 seconds, workers_reaped=True; SHA256 `0b8cc6cab44c0d3e3fd315dc82c4e1f07cced630fab4a0fef4e699f855aec0de`.
- `E:/PROWL/readiness/verifier-generator-launch-20261025-a01/scientific-resources.json`: 80057.281 seconds, workers_reaped=True; SHA256 `ba112254ebf53f8288338fb6c63a3436fb4e26d251fde16553d6aa54b0d131e7`.
- `E:/PROWL/readiness/verifier-training-20261031-a01/scientific-resources.json`: 6796.563 seconds, workers_reaped=True; SHA256 `740f518b0d907dd2d0a5c64a0f2065e83b74f7e1caf23ab3668026804b3a6a07`.

## Reconciliation limits

The old first-five-weeks database configured at outputs/mlflow.db is absent here; root mlflow.db is also absent. Local mlruns/3 contains verifier artifacts, not a historical runtime ledger. The current local SQLite database has15runs (nine scientific sessions and six excluded records). Mac KD and any historical MLflow runtime must be supplied and matched by machine, run/attempt identity, journal hash and MLflow ID before a complete combined total is claimed. Copied/exported records are not extra computation.

Standalone native evaluation, prediction export, teacher-target generation, data download/restoration and engineering qualification are excluded from this training total. Their runtime is not asserted to be zero; it belongs in separate categories. No teacher-target generation or Mac student training is included here. Active human hours are unmeasured. Concurrent machine-hours may be summed as computational effort, not elapsed calendar duration.

The sanitized JSON contains per-run original source paths/hashes, exact stored floats, statuses, update counts, attempt start steps, MLflow mappings and exclusions. It contains no patient identifiers or imaging data. Snapshot SHA256: `25f7df6452d726a8cef06d0580b6a4a203e4b7363c9333a0c64c13bbb98bd0d7`. No dashboard/tracker/producer changes were made.

## Incidental live evaluation observation

During read-only accounting, the existing70-case handoff had completed64-CT restoration in3278.140 supervised seconds, then source admission stopped with `ValueError: Unresolved CT/reference units`. Admission supervisor exited1 after24.547s; workers reaped. The handoff recorded failed_no_retry at2026-11-03T21:36:44Z; no evaluation launched and no retry was made. Preserve its evidence under E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a02. This engineering/inference preparation time is not training time.
