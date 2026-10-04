# Next runner step after uniform2mm qualification

Status: D-297 preprocessing qualification and review completed; see the
[results](../data/TWOMM-LOCALIZER-PREPROCESSING-RESULTS-2026-09-30.md). This packet prepares the next
implementation; it is not a training launch or final adoption of the candidate recipe.

## Required comparison and recipe decision

Use all153 case results, preserved native references and unchanged113/40 roles. Compare3mm versus2mm
reference fidelity, target survival, acquired coverage, worst cases, resource cost and any regressions.
Do not infer better model localization from label round-trip improvement. Carry partial-reference,
noise and resampling observations into the runner; retain all23 source/target holds outside the frozen
cohort. Record a uniform recipe decision before constructing the final training request.

## Physical context must be explicit

A96³ patch spans288mm at3mm but192mm at2mm. Changing spacing while retaining96³ therefore changes
both detail and the physical field of view. A144³ patch at2mm restores288mm physical span, with3.375×
as many input voxels as96³; this is not a prediction of proportional RAM/time. Model receptive field
and full-volume sliding-window cost also need consideration. Do not silently reuse the prior training
configuration and call it a pure resolution comparison.

Bounded synthetic MPS profiles should compare the proposed patch sizes using the actual model/loss,
checking network shape constraints and save/reload, peak allocated/driver/process memory, timings and
no fallback. Decide on physical-context handling with measured evidence before real optimizer updates.
Record changed factors (cohort,spacing,patch/context and sampling/exposure) honestly. Prior16/11 results
remain historical baselines; there is no automatic checkpoint warm start or continuation.

## Role-safe cache and real zero-update profile

1. Bind exact cohort completion/inputs/derived/manifest,selected recipe,source/environment and the
   D-297 result/review receipts. Keep3mm paths and all consumed requests intact.
2. Freeze a fresh cache-build capability and budget. D-297 retains reports/sheets,not image tensors;
   a cache build needs new scoped reads or an explicitly qualified retained artifact source. Avoid
   repeated unrecorded source access. Enforce exact member/role/target provenance and processed hashes.
3. Store float32 image and uint8 label entries with transforms and case limitations. Test partial
   writes,stale/cross-role entries,content changes,missing members and budget overruns. No validation
   entry may reach an optimizer. Exact cache accounting must include metadata/storage overhead.
4. Start real-data no-update profiling with an exact bounded subset selected for output/source size
   and target edge cases. If it passes,profile all153 under an explicit aggregate budget. Measure
   cache generation,forward/sliding-window evaluation,source-grid restoration/export separately.
   Prove weights unchanged. CPU preprocessing results do not qualify MPS or a larger patch budget.
5. Bind checkpoints to the new recipe/cohorts/patch policy/run identity and demonstrate independent
   backup restore with primary reads blocked. Use fresh-process parity checks and interruption handling.
   Preserve the registered20GiB backup cap and100GiB internal-free floor.

## Experiment request after readiness

Choose a finite update/time/output budget from measured throughput. Record case exposure per role,
patch sampling,seed,loss,optimizer,threshold and ROI rule,with before/after native metrics. Report
recall/crop coverage and crop fraction using acquired scan volume alongside Dice and per-case failures.
The broader development-validation set has already been exposed for preprocessing debugging; no
sealed-test or population-generalization claim. Preserve all members even when a metric is poor.
No model promotion on aggregate Dice alone and no automatic run extension.

The immediate desired result is a resource-qualified fresh training request that Quinton can review.
No source activation,PANORAMA mixing,literature dependency,UI change or source-label rewrite is needed
for this bounded imaging readiness step.
