# Next slice — consume the D-294 broader cohorts

Status: implementation packet; no raw-input job or training request launched by this file.
Purpose: connect the new immutable 113/40 role cohorts to verified preprocessing, without dropping
large, noisy or partial-coverage members to satisfy the old runtime's limits.

## Dependencies and contract

Require the D-294 published completion, input and current-manifest pins together. Replay the bundle,
then resolve exact optimizer/evaluator members. Candidate accounting remains 128/48 and 23 held;
only the frozen 113/40 subset supplies inputs. Validation targets never enter optimizer sampling.
Preserve the old 16/11 loader, capability, recipe, checkpoints and reports. Use separately versioned
modules/capability for this expansion. Do not substitute the previous bundle's input JSON layout:
the new inputs retain multiple evidence packages and a separately pinned selection.

Descriptors must carry source references, operation/role, qualification, cohort/manifest identity,
geometry, binary-policy lineage and case coverage observations. Carry visible-reference scope into
metric/export records. Cases 2727/5190 and limited-coverage observations cannot disappear at loading.

## Exact implementation sequence

1. Build role descriptors from the independently resolved bundle, with tests for held cases,
   role swaps, stale manifest/qualification, substitutions and mutated descriptors. Require the exact
   reviewed CT/pancreas pairs. Recheck the existing storage UUID/registry and live binary policy.
2. Compute header-only source and resampling projections for every member before any raw read.
   Retain the existing 3 mm / HU / orientation / interpolation recipe unless a separately documented
   failure requires a changed recipe. Only version resource capability initially; no silent recipe
   tuning or case filtering. Five qualified cases exceed the old 64M source cap: train1935/3206/6822/
   8937 and validation6186. Proposed next cap96M requires preprocessing allocation tests; D-293's
   content-decoding rehearsal is not sufficient by itself.
3. Replace the old hard-coded 54-file/1GiB compressed/4GiB expanded job accounting with exact
   frozen batch budgets from qualified source sizes and decoded headers. Keep the existing per-file
   128MiB compressed/512MiB expanded ceiling if every member fits; fail preflight otherwise.
   Process sequentially in bounded batches, with completed evidence per batch and no automatic retry.
   Set a total scope and budget across batches as well; a budget reset must not authorize extra files.
4. Synthetic checks: physical geometry/orientation, image-only parity, nearest-neighbor binary label
   preservation, source-grid inversion, capped allocations and failures before large allocations.
   Ensure short/single-slice reference cases retain foreground after resampling. If a target disappears,
   record the affected case and reassess preprocessing; do not silently omit or fill it.
5. Freeze exact read-only requests after tests and source/environment capture. Start with a small
   role-diverse batch, inspect paired native/transformed alignment and measured resources, then
   continue the accounted remaining members and separately verified large cases. Every consumed file
   must match qualification hashes, size, geometry and source stat/volume checks.
6. Review all transformation sheets and source-grid restoration records. Compare header projections
   to observed tensor sizes and publish per-case errors/holds if any; qualification alone does not
   establish preprocessing success. Preserve partial evidence if a batch fails.
7. Measure processed cache size and peak memory before choosing full RAM cache versus bounded
   streaming. Do not simply multiply prior16/11 timings. Record load/preprocess duration, process/MPS
   memory, evaluation duration and usable resource headroom under an exact no-update profile.

## Exit to a future training run

All frozen members must resolve and preprocess with explicit role and geometry evidence. Complete
fresh-process checkpoint/backup recovery checks for the new input identity, deterministic sampling,
interruption handling, localization metrics and prediction export bindings. Only then freeze the next
scratch experiment's exact updates, wall time, memory, checkpoint cadence and stop criteria. Preserve
CAP-EXP-005/006 comparisons; do not rerun consumed requests or reuse their weights by implication.
No lesion/PANORAMA/retrieval work is a prerequisite for this pancreas-localizer slice.

## Retained-evidence sizing (not a new source read)

| Role | Pairs | Compressed bytes | Expanded file bytes | Maximum source voxels |
|---|---:|---:|---:|---:|
|train|113|3,984,225,006|10,230,735,232|92,889,088|
|validation|40|1,167,864,850|2,965,815,005|67,279,872|

306 source files total. Expanded file bytes are decompressed payload sizes, not peak tensor memory.
These totals require new cumulative budgets or an explicitly scoped batch plan. Preprocessed tensors,
coordinate grids, temporary copies, CPU/MPS evaluation and caches need their own measured bounds.

Metadata resolution may use the explicit `manifest_validation_session` context from D-294. Its
one-entry reuse requires identical actual manifest/membership/schema bytes and is process-local.
Keep mutation rejection and independent bundle pins; no persistent or caller-asserted validation cache.
