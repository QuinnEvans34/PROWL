# Week 5 Windows CUDA baseline preparation

**Status: CPU preparation complete; NOT ready for real GPU evaluation.**
No new training, real inference, threshold search, protected-test reads, Mac
commands, or automatic successor were performed. Dispatch requires the missing
private receipts/weights and the integration gates below. This report does not
replace them with guessed hashes or an executable-looking placeholder command.

Handoff read in isolation from commit
`d03e904d93d6985a2f37afa999fe20bf79fa372d`. Only `git fetch` was used; no pull,
merge, reset or remote working-tree overlay. Starting checkout was
`b884f4785e897ca3157fa410148e014554182caa`, with substantial pre-existing uncommitted
Windows training work. That work is preserved. New additive CPU code is committed
separately as `8a0dfb3` on `codex/week05-cuda-readiness`; it is not integrated into
the historical or proposed GPU worker. Mac KD remains untouched.

## Verifier closeout and machine state

Observed at 2026-11-02T19:20:42.855863Z. The verifier finished all 10,560 updates
and 80 tuning passes. All update indices are contiguous. Selected epoch 47,
update 6,204, tuning patient-balanced BCE **0.2773905406758086**; terminal epoch 80
BCE **0.28156344968730823**. Training duration **6,773.531 seconds / 1.88154 hours**.
These are classification losses, not Dice or false-positive reduction results.
Calibration and development evaluation remain pending; H0 is not tested.

MLflow `4475886fbdbf41c8a02d4f814a9733ac` is FINISHED. Its 10,560 loss and 80 tuning
records exactly match the journal. Seventeen execution artifacts, including all
saved checkpoints, final execution result and journal, match independent C:
backups. Supervisor exit 0 / workers reaped, 6,796.563 supervised seconds and
1,748,967,424-byte peak owned RSS. No training Python process remains; only the
phone monitor was present. `nvidia-smi` reported no compute applications.
AC passed and the existing CUDA lock was acquired/released without using the GPU.
Free space at inspection: C:176,284,401,664 bytes; E:371,313,082,368 bytes.

Private evidence directory:
`E:/PROWL/readiness/week05-cuda-baseline-20261102-a01`.
See `verifier-closeout.json`, `environment.json`, and
`preserved-repository-pins.json`. The completed verifier's original repository
producing files remain unchanged. Availability is an observation, not reservation
of a future GPU slot; repeat the ownership/AC/free-space gate at dispatch.

## Artifacts and smallest private transfer

Searched names in repository outputs, E:/PROWL/artifacts, E:/PROWL/transfer and
C:/Users/quinn/PROWL-Backups. No matching localizer inference bundle or October 9
checkpoint-review/request files were found there. The E: transfer weights contain
SuPreM initialization, which is not a substitute. The October 23 metadata bundle
contains older control information, not evidence identifying the completed Mac
control's selected 20k checkpoint. Do not use a higher-scoring laptop checkpoint.

Destination proposal: `E:/PROWL/transfer/week05-cuda-baseline-20261102-a01`.
Transfer only through a separately arranged private route, with sender SHA manifest:

| Needed item | Identity / minimum contents |
| --- | --- |
| `localizer.pt` | 18,830,236 bytes; SHA256 `46417801f3d3c37e618d06823027e84f0ce84343f469f24124537167d40198d5` |
| `checkpoint-review.json` and `request-a02.json` | Exact retained October 9 files plus sender hashes. Review ancestry/settings; never replay the old paths/output directory. |
| Selected current-control 20k inference export | Exact source checkpoint path/hash and safe tensor-equal export to `prowl-cascade-weights-1`, role segmenter, three-class architecture, finite float32 state. Its filename/hash are unresolved. No optimizer file is needed on Windows. |
| Current-control provenance/recipe records | Selected-checkpoint record and relevant frozen ready/closeout/configuration/source hashes, training and selection ancestry IDs, class mapping, label revision and units decisions. Existing Git design JSON is not a launch receipt. |
| Retained cross-device case evidence | Existing PanTS_00001070 localizer native mask/probabilities and current-control native output/transform/probabilities, if retained, with hashes and producing recipe. If absent, report absence; do not interrupt KD or regenerate on the Mac under this handoff. |

No bulk CT transfer is requested. The complete downloaded PanTS training archives
are already on E:. The five proposed development CT hashes/shapes are recorded in
`cohort-proposal.json`; restore only those exact eligible files after binding units
and source identity. Existing recovered verifier CTs are training-role files and
are not proof that these development scans are extracted. No source CT or reference
mask was opened for this preparation. Unknown transfer hashes remain null in
`transfer-request.json`; null is an unresolved gate, never an accepted identity.

## Compatibility matrix

| Property | Historical cascade | Physical-window control / required disposition |
| --- | --- | --- |
| Localizer | Binary SegResNet, full-CT 2 mm preprocessing, HU [-100,300], 144-cube windows, overlap .25, constant blend, native argmax | Reuse verified CAP-EXP-012 bundle and exact request recipe; independently verify units/ancestry. Localizer history is development-exposed. |
| Segmenter input | Predicted region resampled through 1 mm intermediate grid into one 144-cube, uniform scaling/letterbox | Integer subdivision to at most 1 mm, preserving finer spacing and voxel-cell field; many 144-cube windows, stride 72. No region-to-single-cube resize. |
| Segmenter HU | [-100,250] normalized to [0,1] | Same in inspected implementation; bind to actual control receipt. |
| Margins | 10 mm around selected prediction | Current declared control has 10 mm base plus [81,43,71] mm extra in SOURCE index-plane coordinates, with two separate ceil operations. Must be receipt-bound; a single ceil of summed margin or canonical-axis reinterpretation is different. |
| Region source | CT-only predicted binary pancreas; all_support default, largest-component explicit experimental option | Proposed baseline keeps all_support; no new threshold/component search. Provided-region arm uses only pancreas reference and runs separately. |
| Padding | Whole-crop resize with symmetric letterbox | High-side zero padding of individual tiles; native acquired obliquity retained. |
| Reconstruction | Argmax on resized tensor, then nearest native restoration | Softmax probabilities sampled/blended at native centers using positive triangular weights, then argmax; outside region background. Zero reconstruction gaps required. |
| Class codes | 0 background, 1 pancreas parenchyma, 2 lesion | Same declared mapping; strict export/architecture check still required. |
| Backend | Historical MPS | Proposed CUDA fp32; same weights alone do not establish recipe or numerical equivalence. |
| References | Separate saved-output scorer | Preserve separate process/data boundary; annotations cannot repair/expand autonomous crops. |

The inspected physical/native window files match d03e904 byte-for-byte; cascade
loader/core match after CRLF normalization (Git reports no semantic diff). This
proves code correspondence, not that the actual Mac control receipt used those
files. Git's errata control JSON is explicitly NOT a qualified launch receipt.
It declares a seven-case normal-mask correction; exact correction binding and
selection history must be received before claiming a matched current-control arm.

## Small additive changes and tests

`predicted_physical_region_v1.prepare` accepts only CT, predicted mask, affine and
explicit margin/allocation parameters. It reuses the existing geometry selector,
preserves source-plane margin rounding, performs lossless closest-RAS orientation,
normalizes CT and returns the native-region structure consumed by existing physical
window primitives. Empty/invalid localization fails; no reference or whole-CT
fallback is supplied. It neither loads a model nor dispatches inference.

`ct_access_policy_windows_v1.CtAccessPolicy` is an additive file-open tripwire.
It accepts byte paths safely, allows the exact platform null device, permits writes
only beneath a fresh output directory, refuses CT/code writes, and accepts only
explicit runtime/source roots for read access. It does not whitelist the repository
or data drive. Windows standard library is outside sys.prefix in this environment;
future wiring must name sysconfig's exact stdlib directory. It is not a malicious-
code sandbox. Existing worker/audit code remains untouched.

Tests: historical requested suite **32 passed, 1 skipped in 37.86 s**. The skip is
the fcntl-dependent Unix lock test, not a Windows cleanup qualification. Final new
suite **10 passed in 7.26 s**: axis flips/permutations and native embedding, all
source faces, physical margins/non-resizing, invalid/empty/nonfinite/over-budget
inputs, reference independence, path/write restrictions and an actual subprocess
rejecting reference access while allowing the declared CT/output/null device.
The final test also compares source-axis margin bounds with the existing control.
The earlier nine-test report is preserved; the later report includes the margin
semantics refinement. Both runs are synthetic CPU work, not real GPU qualification.

CPU reproduction commands (already executed):

```powershell
$env:OMP_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
$env:CUDA_VISIBLE_DEVICES=''
.venv-prowl-windows/Scripts/python.exe -m pytest -q tests/test_cascade_models_v1.py tests/test_autonomous_cascade_v1.py tests/test_localizer_region_selection.py tests/test_fixed_cohort_evaluation.py tests/test_saved_prediction_scoring.py
.venv-prowl-windows/Scripts/python.exe -m pytest -q tests/test_week05_cpu_bridge_20261102.py
```

Remaining demonstrated integration gaps: the old cohort runner imports a Unix
/bin/ps watchdog and takes only an MPS lock; the old prediction CLI still calls the
single-tensor cascade and the old file hook. Its evidence validator requires a
single tensor-shape transform. Add a separately versioned physical-window worker,
request/evidence verification branch and Windows runner using the existing
`watch_windows`/CUDA lock, preserving old reproduction behavior. Wire the reviewed
access policy into that worker after safe weight loading; no global audit bypass.
Do this after exact control recipe binding, rather than guessing a new native
inference recipe now. The existing offline scorer remains reusable; full metric
reporting needs the frozen metric-spec fields, denominators and failure accounting.

## Cohort and exposure proposal

Pilot: PanTS_00001070, the retained historical abdominal diagnostic. Its CT SHA is
`90bf329d4a959144dfc453c5f1adce83ac18b1d5493984cb8aaa3911a1f1000f`.
Four-case development proposal: PanTS_00002028, PanTS_00000909,
PanTS_00004681, PanTS_00006755. Deterministic selection is the four lowest SHA256
values of UTF8 `20261102:case_id` from the existing 70-case development membership,
excluding the diagnostic case. No outcome or label-based selection was used.
Parent membership SHA:
`6b69605f49de0dd20346bee9db7fea4842c050cea4cf8d85268775deabc301bf`.

These IDs are a fixed proposal, NOT an eligible published cohort or final-test set.
Complete localizer/segmenter ancestor train/selection intersections, source/units
checks and a role-valid subset artifact are required. Prior documentation reports
localizer113 train disjoint from historical75 development by study ID; the private
review is still needed to bind that claim here. This does not prove biological
patient independence or resolve unknown SuPreM pretraining. Current control used
these development data for checkpoint selection; report exploratory development
only, never independent acceptance. Preserve all failures and unresolved-unit
cases; no replacements selected from results. The old suspicious-anatomy case and
seven old unresolved-unit cases remain visible in historical denominators.

## Numeric execution proposal — not dispatched

| Gate | Proposed cap |
| --- | --- |
| Single-case qualification | 600 s per attempt, 1,800 s total; 12 GiB owned RSS, 6 GiB reserved GPU; 2 GiB outputs and 2 GiB independent backups |
| Four-case batch, autonomous and separate provided-region arm | 600 s per case per arm; 4,800 s total; same memory limits; 8 GiB outputs and 8 GiB independent backups |
| Shared storage | At least 100 GiB free on both C: and E:; 40 GiB combined C: backups ceiling including retained prior work |
| Input allocations | 96,000,000 source voxels; at most 64,000,000 localizer sampling voxels; exact tile count/resource preflight still required |
| Execution | One GPU owner, AC required, fresh directories, owned-tree cleanup, zero optimizer updates, no retries or automatic next stage |

These are proposed allowances, not a waiver or an installed supervisor. Qualification
failure stops before batch dispatch. Predicted-region full-volume tiling can be
expensive; never shrink coverage or raise caps silently to pass.

Predeclared cross-device rule proposal: identical source/model/recipe identity,
exact native shape, affine atol1e-5, finite normalized probabilities and valid
0/1/2 codes; probability atol1e-5/rtol1e-4 against retained same-recipe MPS output,
argmax disagreement fraction <=0.001 and exact predicted-region bounds. Preserve
and investigate any failure without changing tolerances afterward. Old resized-
geometry and current physical-window outputs are different experiments: numerical
parity is not expected across them. A missing continuous reference leaves that
parity gate unresolved, rather than substituting aggregate Dice.

`evaluation-proposal.json` deliberately records `launch_command: null` and status
PROPOSAL_BLOCKED_NO_GPU_DISPATCH. An exact ready command cannot honestly be supplied
until checkpoint hashes, eligible cohort, integration and qualification-request
hash exist. The old predict/evaluate CLI shapes in the handoff are not compatible
launch commands for the new geometry. The next handoff must bind a fresh request,
then provide the versioned Windows supervisor command and exact request SHA.

## Handback and next required information

Verifier fit is complete and the laptop GPU is available at observation. CPU
foundations and regression tests are complete. **Autonomous CUDA baseline is not
launch-ready**: receive the minimal private bundle, confirm actual control geometry
and ancestry, resolve source units and same-recipe reference availability, finish
the narrow worker/runner integration, freeze its bounded qualification request,
then obtain the explicit dispatch decision. No need for bulk CT transfer, new
localizer training, another planning framework or changes to the running Mac KD.
Board W05-09 evidence is captured here for the Mac to reconcile; no cross-chat
message or board mutation was sent from this preparation.
