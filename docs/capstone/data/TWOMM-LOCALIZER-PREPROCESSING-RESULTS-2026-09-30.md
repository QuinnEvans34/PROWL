# D-297 — uniform 2 mm preprocessing qualification results

Completed September 30, 2026. Authority and exact limits: [job plan](TWOMM-LOCALIZER-PREPROCESSING-JOB-2026-09-30.md).

## Outcome and recommendation

The separate V4 uniform 2 mm candidate passed numerical checks for all **113 training / 40 development-validation cases**. All 153 limited three-plane transformation sheets were reviewed. The 153 frozen members, 23 holds, original labels and current 3 mm paths are unchanged. No model forward, real optimizer update, cache publication or training launch occurred.

Recommend carrying uniform 2 mm into bounded runner/resource qualification. Improved reference fidelity supports this next step, but does not prove improved learning/localization. Final training recipe and physical-context policy remain to be recorded with measured MPS evidence. No per-case resolution choice or removal of difficult cases is proposed.

## Reference fidelity

These are source-reference → processed-reference → source-grid metrics, **not model scores**, expert label quality, or whole-organ truth. Same case roles, source hashes and native reference foreground counts were verified against D-295.

| Role | Mean Dice, 3 mm → 2 mm | Mean recall, 3 mm → 2 mm |
|---|---|---|
| Train (113) | 0.916724 → 0.943803 | 0.916135 → 0.944986 |
| Development-validation (40) | 0.909228 → 0.947150 | 0.915132 → 0.947109 |

Dice improves for 148 cases and declines for 5; recall improves for 147 and declines for 6. All targets remain nonempty. Both tiny-boundary pilot cases reproduce D-296: case 6110 recall 0.459559 → 0.904412 and Dice 0.602410 → 0.779715; case 2727 recall 0.764706 → 0.882353 and Dice 0.516556 → 0.918367. Case 6110 still has restored volume 1.320× its tiny source reference; improvement is not complete recovery.

All cases with a regression in either metric are retained:

| Case | Dice change | Recall change |
|---|---|---|
| 1282 | -0.006298 | -0.002649 |
| 4359 | -0.012768 | -0.029523 |
| 5569 | -0.003139 | -0.001292 |
| 5946 | +0.011694 | -0.001836 |
| 6727 | -0.000349 | +0.003792 |
| 7604 | +0.015523 | -0.008178 |
| 8956 | -0.000933 | -0.004727 |

Case 4359 has the largest recall decline (about 2.95 percentage points), short acquired coverage and source-face contact. Its full sheet shows aligned source/restored references with boundary resampling differences. This is not a reason to silently choose a different recipe for it. Lowest 2 mm recall is 0.879241 (case 7604); lowest Dice is 0.779715 (6110).

## Resource and implementation evidence

- Native suite: **1,337 passed**, two existing upstream warnings, 36.60 seconds. Tests include the separate 16M output envelope, preserved old 8M refusal and unchanged 96M source cap.
- V4 preserves RAS orientation, HU [-100,300], bilinear image / nearest target interpolation, minimum 96 padding, no crop and 16-slice source restoration. Image-only preprocessing equals preprocessing with the target on every real case.
- Synthetic maximum-envelope rehearsal: 96M source voxels, 15,163,200 processed voxels, 5.073 seconds and 4.76 GiB peak RSS. No source reads or updates.
- All 15 single-use real requests completed: four-case pilot, nine standard batches, five large singletons. Exact aggregate: 306 files, 5,152,089,856 compressed bytes and 13,196,550,237 expanded bytes.
- Successful job durations sum to **511.861 seconds** (8.53 minutes; excludes review/operator gaps); maximum CPU RSS **6.664 GiB**. All per-job and aggregate limits passed. Job outputs total 92,832,445 bytes.
- Actual maximum processed volume: 14,672,632 voxels. Measured float32-image/uint8-label tensor payload is **3,116,434,900 bytes (2.902 GiB)**, **2.711×** the retained 3 mm total. This is payload accounting, not a published cache or peak training memory.
- Source/environment captures were checked again after completion against the rehearsal. Old implementations/configurations remain unchanged; no environment dependencies were installed.

## Visual scope and retained limitations

Every case was reviewed through source/restored matching planes and processed-reference planes. The four pilot cases, all five large cases and all seven cases with any regression received original-sheet inspection; standard batches were inspected as six-case montages. No gross displacement was observed in these displayed planes. Noise, artifacts, partial coverage, source-face contacts and sparse/tiny references remain attached to their records. This is limited transform QA, not all-slice or radiologist review.

The development-validation set has been exposed for preprocessing debugging. No sealed-test or population-generalization claim follows. The uniform candidate does not fix missing acquisition coverage or establish annotation correctness.

## Retained evidence

Repository-relative evidence root: `outputs/prowl/twomm-preprocessing-review-20260930/`.
Its `receipt.json` SHA-256 is `086fa4216633900a7e100840693803d974aaf05398bfbc80f262ec705d03e657`. It pins the complete comparison, per-case visual observations/sheet hashes, all 15 result receipts, native test logs and execution/analysis helpers. Each result receipt was checked against all retained result-file sizes and hashes.

Synthetic rehearsal: `outputs/prowl/twomm-preprocessing-rehearsal-3c265ff7-f79b-422a-ab04-fce14683a1c2.json`, SHA-256 `6a315d82454d88e2c273bd393be878b38b94b466647f6ea213bea0f18a818402`.
The pilot review and all consumed claims/requests remain intact. An optional plotting attempt lacked matplotlib; no environment modification was made, and the numeric table/JSON remains authoritative.

## Next bounded implementation

[Runner readiness packet](../operations/TWOMM-RUNNER-READINESS-PACKET-2026-09-30.md): profile physical context, build a role-safe cache under a fresh bounded capability, verify zero-update MPS throughput and independent checkpoint recovery, then prepare an exact fresh training request.

A 96³ patch covers 192 mm at 2 mm versus 288 mm previously. A 144³ patch restores that span with 3.375× the input voxels; actual memory/time must be measured. Resolution, cohort and patch changes must be reported as separate changed factors. Current results do not authorize copying the old training settings or launching an unrestricted longer run.
