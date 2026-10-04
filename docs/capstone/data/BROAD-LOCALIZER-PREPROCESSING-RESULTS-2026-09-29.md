# D-295 — broader loader and preprocessing results

September 29, 2026. Engineering checks and limited visual review complete for all **113 train / 40
development-validation** members. All153 targets survive the fixed3mm recipe. **Substantial
resampling loss on tiny boundary references remains a scientific limitation to resolve explicitly
before training.** No cohort filtering, qualification changes, model forward or optimizer updates.

## Implementation and verification

Added separate `src/data/broad_localizer_inputs.py`, `src/data/localizer_preprocessing_v3.py`,
`configs/capstone/localizer-preprocessing-v3.json`, the exact input capability, diagnostic runner
`scripts/diagnostics/broad_localizer_preprocessing.py` and23 regression tests in
`tests/test_broad_localizer_inputs.py`. V1/v2 preprocessing and the historical16/11 runtime unchanged.
V3 raises the separately bounded source ceiling to96M voxels and restores native grids in16-slice
slabs. Synthetic full-versus-slab comparisons cover discrete/probability and oblique grids. The image
recipe remains RAS,3mm,HU[-100,300],bilinear image/nearest target,minimum96 padding,no crop.

The consumer verifies exact D-294 input/derived/completion/manifest pins, retains the independent
D-294 derivation attestation, enforces operation/role/purpose and qualified source hashes, and carries
visible-reference scope and existing observations. Read budgets enforce unique scoped URIs and exact
compressed/expanded bytes. Held members and wrong-role requests are refused. No permission is derived
from apparent image quality or model performance.

Native full suite: **1,307 passed,2 existing warnings,34.88s**. The separately supervised96M synthetic
rehearsal completed in2.5424s at4,527,685,632bytes RSS. It covered preprocessing,image-only parity and
slab restoration before real reads. Live source/environment capture still matches the frozen receipt
after completion. `git diff --check` passes.

## Execution and accounting

One4-case pilot, nine16-case standard batches, and five large singleton batches completed. All306
source files were read within the scoped requests, exactly once in successful preprocessing jobs:
5,152,089,856compressed bytes /13,196,550,237expanded bytes. Exact153 membership,113/40 roles and
per-batch partitions were independently reconciled from retained reports against the capability.
All source file hashes/CRC checks and target-independent image transforms passed. All processed
references were binary/nonempty. All output receipt entries were rehashed before review.

| Measurement | Result |
|---|---:|
| Sum of15 successful job durations |448.307s|
| Continuation queue wall time (14 jobs, including request preparation) |488.808s|
| Largest observed process RSS |7,057,948,672bytes (6.57GiB)|
| Aggregate processed image+target tensor size |1,149,621,835bytes (1.07GiB)|
| Largest processed volume |4,372,068voxels|
| Real model forwards / optimizer updates |0 /0|

Per-job20minute/16GiB/256MiB limits and continuation90minute/2GiB limits held. The five source volumes
above64M voxels (1935,3206,6186,6822,8937) ran separately and passed; none was dropped. Tensor sizes are
measured float32-image/uint8-target payload sizes, **not a retained tensor cache**, total runner RAM,
MPS qualification or a training budget.

## Visual review and reference fidelity

Codex inspected all153 three-plane source/restored/processed sheets: pilot4 at full size,144 standard
cases through27 six-case-or-smaller montages, and5 large cases at full size. Additional full-sheet
inspection covered2454,4965,6110,8988;2727 already received full pilot inspection. This is a limited
engineering alignment review, not all-slice inspection or expert contour acceptance. No gross global
orientation/displacement error was identified. Partial coverage, noise and boundary contacts remain.

Round-trip metrics compare the supplied reference with its3mm resampling restored to the source grid;
**they are not model scores, model recall ceilings, or proof of annotation quality.**

| Role | Mean round-trip Dice | Mean round-trip recall | Minimum recall |
|---|---:|---:|---:|
| Train113 |0.91672|0.91614|0.45956|
| Development-validation40 |0.90923|0.91513|0.76471|

Five cases had either Dice or recall below0.85; this was an inspection trigger, not a new eligibility
rule. Retained cases:2454 (Dice0.86401,recall0.84382),2727 (0.51656,0.76471),4965
(0.81713,0.89725),6110 (0.60241,0.45956),8988 (0.86331,0.84733).

- **6110:**272 source foreground voxels become31 processed voxels. The restored reference retains
  only45.96% of source foreground; its displayed source median axial plane loses visible foreground,
  although the restored volume remains nonempty. The tiny inferior-boundary reference is strongly
  affected by coarse-grid sampling. Passing nonemptiness is insufficient to call this loss acceptable.
- **2727:**51 source foreground voxels on one boundary slice become14 processed voxels and100 restored
  voxels. The overlap loss and enlargement are retained, not described as lossless conversion.
- **2454/4965/8988:**partial/source-boundary references show quantization/size changes.8988 also retains
  substantial image noise. No whole-organ interpretation or silent replacement is supported.

Proceed with runner integration/no-update resource work, but investigate tiny-boundary target
representation and document the chosen treatment before freezing a training launch. Compare methods
under a new bounded request if real reads are needed; preserve this baseline and all cases. Do not
improve these numbers by dropping difficult cases or by silently modifying validation references.

## Retained failure and explicit recovery

Attempt01 pilot request `d06f830e80ba965b2c7b83de3e1de402a13be511621f3b33541c069d19b24d44`
failed **before source-root/array access**: the store callback checked exact payload hashes but returned
None instead of the retained validation report. Its7.066s attempt, request, claim and logs are preserved.
Fixed callback equality, added its regression test, reran the full native suite and96M rehearsal,
then explicitly froze capability attempt02. No claim was removed; no automatic retry or extra source
read occurred. Attempt02 pilot and14 continuation requests are all consumed and must not be rerun.

## Evidence pointers and hashes

All paths below are relative to the repository root; source arrays remain in registered storage.

- Review/reconciliation/per-case record and sheet pins, native test log and retained scripts:
  `outputs/prowl/broad-preprocessing-review-20260929/`; review receipt SHA256
  `0894dd1edca6a128420580938a16ac81fcf88a027cee8428b3d0915baf7256e3`.
- Pilot queue: `outputs/prowl/broad-preprocessing-queue-fac764d7-5d93-40a4-b612-b0e2c6208680/`.
- Continuation queue: `outputs/prowl/broad-preprocessing-queue-54ff3153-a662-4902-a75e-e1cbea5476bb/`;
  each batch completion row retains request/result paths and receipt pins. Review inspection-progress
  also records all15 result paths and receipts.
- Failed result: `outputs/prowl/broad-preprocessing-d3458a31-3434-4849-a9b0-9059a2287164/`.
- Synthetic receipt: `outputs/prowl/broad-preprocessing-rehearsal-4f64435e-a577-4979-895a-ace12603a45c.json`,
  SHA256 `1e0e98db242a6b4e7eac22cfeef56b08370cce39f7e0f4587d4ed90dba0bd33b`.
- Capability SHA256 `29c4a48eeadbc61a23fa8e3e8cdf07211ef7a05786cdc24ab572a17703d70683`.
- Source SHA256 `9bcaa5b9b7c3ed4de18c4e72aa2b685bfa1f6900d1cc3a5f70739696a3ca31b9`.
- Environment SHA256 `2c7b2cf2158b183f766b14e2edcadc9b8db52287edd4e2eff8fe96f9322c8426`.

Next: [broader runner packet](../operations/BROAD-LOCALIZER-RUNNER-PACKET-2026-09-29.md), including
role-safe cache, zero-update MPS resource profile, fresh checkpoint/backup binding and the explicit
tiny-reference investigation. No new training request is frozen or awaiting launch.
