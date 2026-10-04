# Next slice — qualified segmenter inputs and zero-update MPS

Proposed after [D-322 synthetic learning/recovery](SEGMENTER-LEARNING-RECOVERY-RESULTS-2026-10-01.md). Complete the next engineering readiness slice before preparing a short real training request. This is an implementation packet, not a frozen source-read request or training launch. No optimizer updates are allowed in this slice.

## Fixed ancestry and input permissions

Keep D-319 purpose/transition replay and the registered D-320 protected cohorts authoritative. Exact train cases: 3, 26, 2232, 2973, 5821, 6238; development-validation: 2514. Preserve all twelve candidates and five holds: 6110, 4965, 2727 and 7265 are unknown empties; 5641 has an unresolved annotation relationship. No refill, inferred negatives, publisher-test inputs or changes to old localizer 153 members/23 holds.

|Existing immutable input|SHA-256|
|---|---|
|D-320 cohort completion|`73e7e034f16c4a42e9f08e8318eb834bd654a400377274fba13521a1bd2587ed`|
|D-320 executable descriptors|`cd52c55577c93b08b67ecfbb2ed6a76288b35d31d26004b8bf31bb8e1cf49481`|
|D-321 geometry acceptance|`b3ff4db94b49f1ea9b44d57afd975c17f16309c9929df35fa3e0d9f7e67e7384`|
|D-321 recipe|`2382855d8414a5d52a9f80813eb00093835adc3cd21690fd787b58aa6017d488`|
|D-321 completed fidelity evidence|`5c958ac1877c52c2eefd55e3cfe0824428322ca72dbd12ad52043c02e1d8fe1f`|

Acceptance lives at `outputs/prowl/SEGMENTER-GEOMETRY-REVIEW-20261001/accepted-geometry.json`. Require full persisted pins and every per-case transform. The provided-pancreas recipe is 10 mm margin, 1 mm intermediate spacing, uniform scale/pad to 144³, zero jitter and HU clipping [-100,250]. Effective tensor spacing varies. Class 2 retains lesion precedence, including foreground outside the pancreas mask. Tiny 2973 and boundary 6238 remain consumed inputs. Provided-reference ROI does not qualify autonomous localization.

The D-321 request `07d3bb4f8e49220a721b5d79efb66595f0f22350ca1a1f75c25c9d34195cc476` is consumed. Its evidence contains no reusable tensor/native-array cache. All later source reads require fresh stage-specific request identity, exact file inventory, one-shot consumption and supervision.

## 1. Synthetic role-safe persisted cache and consumer

Add separate versioned cache/binding/readiness modules. Keep the D-319/D-320/D-321 producers and D-322 synthetic session immutable. Do not broaden `segmenter_geometry_loader_v1.read_case`, which is intentionally restricted to the consumed geometry-fidelity stage. A new stage wrapper may reuse unchanged registered cohort resolution, checked descriptors, `read_triple` and geometry primitives only after its own complete capability/request/purpose/role checks.

Persist float32 one-channel image and uint8 three-class target per exact member, with no pickle/object arrays. Bind source file hashes, parent qualification/cohort/role, CT units, geometry recipe and portable transform, tensor dtype/shape/class counts, output hashes, code/runtime and completion receipt. Serial reload must reproduce bytes/counts/transform and reject missing/changed/extra inputs, wrong roles, held cases and stale lineage before model use. Validation can reach inference/evaluation but no optimizer consumer. Keep image-only inference independent of lesion references. A cache may contain evaluation targets; that does not authorize using them in the optimizer.

Invented tests include sparse/multiple/boundary/outside-pancreas lesions, unknown empty rejection, verified synthetic negatives, class precedence and transform/inverse mismatch. Cache publication must be atomic and completion-last; abandoned partial outputs remain failed attempts. Freeze a new scoped cache storage capability rather than altering the registry or reusing D-322's synthetic-checkpoint capability for real inputs.

## 2. Fresh bounded seven-case cache build

Derive a fresh inventory from replayed D-320 descriptors and byte-matched retained source evidence, without new exploratory reads. Exact proposed scope is 21 files (CT/pancreas/lesion for seven cases): 145,701,969 compressed hash bytes plus the same compressed decode bytes; 544,986,944 expanded source bytes. Recompute these totals and every row before freezing the new request; matching old totals never transfers old permission.

Seven image/target pairs have raw tensor payload 104,509,440 B (seven × 144³ × five bytes), excluding metadata/container overhead. Qualify the largest supported native grid and peak mapping/cache/reload memory synthetically first. Proposed initial CPU envelope: serial, two threads, 1,800 s, 8 GiB RSS, 512 MiB output and 100 GiB free floor. Freeze measured ceilings before real execution. Hash/decode using read-only no-follow source handles, verify observations/grids/scaling/classes and reserve each exact case before reading. No CT copies, new source activation or model updates. Check reload for all seven; preserve regressions and failed attempts rather than replacing difficult members.

## 3. Fresh real-input inference-only MPS session

Create a separate qualified-input task/session at step 0, with deterministic fresh scratch initialization. It must reject optimizer updates and imported weights. Do not initialize from D-322's synthetic learned checkpoints, old localizer checkpoints, prior-project weights or unknown/pretrained state. Bind D-322's tested architecture/signature and D-321's accepted geometry to the fresh task, real role cache and code/runtime. Do not relabel a synthetic checkpoint as a qualified-input checkpoint.

Profile all seven images at 144³, one at a time, with fallback disabled. Confirm finite normalized three-channel probabilities, image-only inputs, unchanged initial weights and exact class mapping. Restore continuous probabilities to original grids before argmax; outside-ROI background and source affine/shape must be exact. Export immutable uint8 masks and transform/provenance records. Seven uncompressed native masks total 136,244,888 B; largest probability workspace is three float32 channels × 40,547,328 voxels. These are payloads, not peak-resource measurements.

Proposed MPS envelope: serial, 1,200 s per producer/recovery, 12 GiB RSS/driver, 1 GiB export/evidence ceiling, AC power, no concurrent model worker and 100 GiB free floor. Measure/profile first and freeze an exact request. Dense, sparse, empty, fragmented and wrong predictions must remain evaluable outcomes; resource envelopes must not exclude failures because of foreground fraction or component count.

Checkpoint the fresh step-0 task and protect all declared configuration/evaluation/export records through an independently budgeted keeper path. Use a new capability for this real-input task, preserving existing areas and quota accounting. Cold recovery must restore all declared required artifacts with external primary access blocked, validate every member/receipt and reproduce image-only probability/native export probes within predeclared tolerances. Clearly mark large masks/cache as derived scratch if not protected; do not imply recovery coverage beyond the declared inventory.

## 4. Separate original-reference scoring

The mapped cache target is not original native truth. If native model metrics require rereading original references, freeze a separate target-only fourteen-file request: seven pancreas/seven lesion files, 1,265,220 compressed hash bytes plus the same decode bytes, 272,494,704 expanded bytes. These proposed totals are derived from D-321's saved exact file inventory, with no new arrays read. Recompute and pin its rows/descriptors, profile the largest/dense synthetic scoring envelope and consume once. No CT reads or optimizer updates in this job.

Report per-case/per-role background, pancreas parenchyma, lesion and pancreas-or-lesion union counts/Dice/recall against original references; preserve every original lesion component and missed component. Unknown empty candidates stay held. Do not assign perfect lesion Dice to an absent reference or score transformed targets as native accuracy. A single positive validation case and no verified real negatives support engineering checks only.

## Exit and short-training handoff

Run meaningful synthetic regressions and the full native suite, independently verify saved cache/export/metric bytes and integers, inspect real-input alignments, and seal all attempts. Exit requires role-safe exact cache/reload, all-seven unchanged-weight MPS inference/native exports, separately supported native metrics and primary-blocked checkpoint/required-artifact recovery within measured limits.

Before real training, finish the historical checkpoint hash inventory/import-denial audit, qualify the real optimizer consumer and recovery/sampler/evaluation transaction, and freeze architecture, exact objective reductions/weights, LR/duration/sampler, exposure, resource ceilings, stopping rules and before/after evaluation. D-322's 256× lesion CE objective is an accepted synthetic engineering candidate; it is not established as the best real objective. Issue a fresh short exact launch for review; no automatic training or duration extension follows from this packet. Formal jitter, broader positives/verified negatives, cascade utility and long-scale performance remain later experiments.
