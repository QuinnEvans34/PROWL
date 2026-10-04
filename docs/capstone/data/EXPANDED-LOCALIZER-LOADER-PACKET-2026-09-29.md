# Next implementation — expanded localizer input and preprocessing

Proceed from the D-282 frozen qualification/cohort bundle and its independently retained receipt,
input and current-manifest pins. Do not reopen selection or silently substitute cases. This packet
specifies the next bounded implementation; it is not evidence that the expanded loader already works.

## Why a new input boundary is needed

Retained complete-file facts show that, among the 27 positively qualified cases, **14 exceed the
old 20,000,000-source-voxel cap**, and **8 CT files exceed its 32 MiB compressed-file cap**. Largest:
case 8037, 55,808,000 voxels/66,651,439 compressed bytes; next 8855, 51,726,168/61,525,567;
then 3104, 47,224,320/56,434,503. No new source read was used to obtain these counts.

`localizer_inputs.py` explicitly binds two train members. `localizer_preprocessing.py` also
independently caps source arrays at 20 million voxels. Merely changing cohort constants would
bypass scope without making the whole path correct. Qualification is not input-runtime readiness.

## Bounded implementation

1. Add a separate cohort-bundle resolver/loader using the completed D-282 bundle, explicit
   optimizer/evaluator role, purpose-specific annotation use and independently supplied current
   manifest pin. Resolve all permissions before opening raw payloads; refuse held case 6350.
2. Bind the registered read-only extraction root, exact volume UUID, inventory observations,
   source URIs, file sizes and full compressed hashes. Reuse the tested bounded reader with
   128 MiB compressed/512 MiB expanded per file and 64 million source voxels, no-follow identity
   checks, full gzip CRC and before/after source checks. No registry-wide source activation.
3. Provide an explicit versioned preprocessing entry point/recipe with the larger source bounds;
   preserve v1 behavior. Apply image-only RAS orientation, HU scaling and physical resampling,
   nearest-neighbor pancreas transformation and recorded geometry restoration. Never derive image
   crops/coordinates from validation targets. Keep output bounds explicit and reject projected
   allocations before transformation. Start with the existing 3 mm/96-cube recipe as a comparison,
   not an assumption that it preserves every target.
4. Stream one case at a time, no all-cohort array cache or new workers. Verify finite arrays,
   binary targets, no complete loss of a positive reference, same image/target transformed grid,
   and source-grid restoration. Report every frozen member, including failures; do not drop a
   failing case from evaluation or treat a preprocessing failure as a bad-source finding.
5. Record case 4965's limited visible coverage and case 3717's boundary contact alongside geometry
   checks. Preserve noisy scans. Validate both train and validation consumers synthetically before
   preparing a pinned real preprocessing request for the exact 54 permitted files.

## Verification and execution boundary

Tests must reject cross-role optimizer use, stale authorization, changed files/stat observations,
symlink substitutions, missing held-case permission and exceeded allocation budgets. Include a
synthetic large-shape budget check, target-independent image transformation, label interpolation,
geometry round-trip and small boundary-contact target preservation checks. Keep historical v1
checks passing. No training or model prediction is required for this phase.

Before real preprocessing, freeze its source/code/environment/recipe inputs and exact budget:
maximum 1 GiB compressed reads, 4 GiB cumulative decompression, 16 GiB RSS, 20 minutes,
256 MiB evidence, 100 GiB internal free floor; sequential one-case processing. Confirm projected
output geometry from the retained headers and measure bounds before execution. Preserve failed
attempts and do not raise limits or retry automatically without a recorded evidence-based revision.

After all consumed members pass: measure actual preprocessing/inference resource needs, freeze a
scratch multi-case training plan, then train with separate validation. The current 11-case validation
subset lacks an arterial/thin-slice member because 6350 is held. Keep that limitation visible; do not
claim final-test performance, complete distribution coverage or biological uniqueness.
