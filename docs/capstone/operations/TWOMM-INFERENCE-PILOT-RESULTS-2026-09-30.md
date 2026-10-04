# D-302 — eight-case real-cache inference pilot passed

All eight specified cases completed full-volume144³ MPS inference and native-grid exports from the
D-300 uniform2mm cache. The actual-cache-bound step0 checkpoint was independently backed up and
restored in a fresh process with primary reads blocked. Probe difference0, exact model weights.
No real optimizer updates, raw source reads, membership changes or training request.

## Measured result

| Stage / measure | Result |
|---|---:|
|Profile worker total, including cache checks/exports/checkpoint/backup|53.480s|
|Fresh-process independent recovery|3.942s|
|Initial153-entry cache integrity verification|2.101s|
|Eight cache loads, already warm|0.212s total|
|Full-volume inference|26.001s total;1.667–4.893s per case|
|Native-grid restoration|14.149s total|
|Export and first reopen verification|4.274s total|
|Independent post-run export/package verification|3.882s for semantic recheck, plus hashes|
|Peak profile process RSS|4,829,233,152bytes =4.498GiB|
|Peak recovery process RSS|728,645,632bytes =0.679GiB|
|Maximum stage-end sampled MPS driver|1,429,913,600bytes =1.332GiB, including recovery|
|Local package, excluding final receipt|26,692,430bytes =25.46MiB|

The two worker processes total57.423s; this excludes the parent's final export recheck and initial
request/preflight. All stages stayed below the shared20minute,16GiB and1GiB-output limits. Driver
values are sampled observations, not allocator peaks. Cache timings are warm, not cold-device estimates.

Cases6110/2727/5190/7957/6822/8937/6186/1935 all passed. Extra144³ patch padding was removed before
V4 restoration. Reopened NIfTI files match source shape, binary uint8 values, millimeter units,
foreground counts and retained source affine at NIfTI1 float32 sform precision. Model digests were
unchanged after every case; step0 and empty optimizer state were preserved. All153 cache entries
were checked for integrity, but only the specified eight real cases entered the model.

These are random initialized predictions. Successful exports and checkpoint recovery are engineering
readiness evidence, not localization quality, native-reference accuracy or improved model learning.
No native references were read or reconstructed for scoring.

## Implementation and tests

Added `src/training/twomm_inference_export.py`, `scripts/diagnostics/twomm_inference_pilot.py` and
`tests/test_twomm_inference_pilot.py`. D-301 `Session.predict_cache` now optionally reports separate
cache-load/inference timings; its return value and input permissions stay the same.

1,437 native tests passed (31 new; two existing upstream warnings), output `/tmp/prowl_d302_tests.log`.
Tests cover flipped/anisotropic geometry, asymmetric patch padding, invalid probabilities, altered
exports, changed role/index/member/control/limits, current-code drift, raw-source access denial,
consumed request/worker-stage refusal, resource stops and interrupted-worker cleanup. Real runs use
single-use request and per-stage markers; incomplete attempts cannot publish completion or auto-restart.
Scoped diff whitespace check passes. Earlier96³ consumers and Claude's retrieval lane are unchanged.

## Exact evidence and attempt status

Single request and output directory:
`outputs/prowl/twomm-session-pilot-72fa2ebb-0fe4-4ee4-9682-b001335f05b1`.
Request SHA-256: `a336fcfccba6ca100746dc2ece1f7843092d96fd96795015ad7215e1fa9f39ea`.
Completion SHA-256: `5764b267a2f2cfef95e327804364b5b4228f51c2359274e1c4b18c0e54f3d76f`.
All31 completion members independently size/hash verified after the run; all eight exports reopened
again. Exact request/source/environment pins rechecked. This request is consumed; do not rerun it.
The one native attempt passed; no background worker remains.

Restore artifact: `restore:cd193e6c-5691-4e47-8ae7-056745817b59`.
Restore completion: `55708cc4414d7df1445d12f4413a4c18774f9c7b2126000415c08067fa3b9c5b`.
Primary/backup references and producing controls are retained in the package and independent keeper.
This uses a process read prohibition, not physical drive disconnection. Recovery compared a generated
fixture probe without depending on the real cache or primary drive.

Independent review and continuation projection:
`outputs/prowl/twomm-inference-pilot-review-20260930`.
Review receipt: `191719577d7e5180ed19c08be78a37cce43926281c338ed8de73c8e1224a897d`.

## Next: remaining145, without changing the cohort

The retained projection lists exactly107 train and38 development-validation cases remaining. They
require580 sliding windows versus64 in the pilot, and3.938billion source voxels versus460million.
Measured stage rates project about430s variable work plus a60s fixed reserve, roughly8.2minutes.
This is a planning estimate, not a guarantee or a measurement of the remaining cases. The proposed
20minute/16GiB/4GiB-output continuation budget remains reasonable with enforced stops. Maximum
remaining processed grid14,657,670voxels and native grid72,356,352voxels fit tested bounds.

Next implement/test a distinct145-case continuation request, bind this passing pilot evidence,
freeze it, then execute and reconcile153 unique cases. Do not change or reuse the pilot request or
silently widen its eight-case allowlist. Preserve113/40 roles and23 source/target holds.

After that: select the bounded training exposure and checkpoint/evaluation schedule, provide an
explicit qualified native-reference measurement path, and complete the matching training executor
before freezing the next training request. Random-initialized inference readiness does not promote
2mm/144³ or any model to a proven scientific improvement.
