# D-295 — bounded broader-cohort preprocessing

Quinton requested the next step after the D-294 freeze. Scope: separately versioned role-safe inputs
and preprocessing for exactly113 train/40 development-validation members (306 CT/pancreas files).
No model forward, optimizer update, new training request, source rewrite, qualification change,
replacement, lesion/PANORAMA input or publisher-test access.

## Fixed inputs and meaning

The capability lists exact member IDs and15 disjoint batches: a4-case role-diverse pilot, nine
16-case standard batches, and five large singleton batches. Pilot3/5190/1004/2727 includes sparse
and boundary references. Reuse the independently published AND freshly replayed D-294 inputs and
derived bytes by their separately retained hashes, plus the completion and current-manifest pins.
Runtime verifies both exact file hashes before parsing; it does not accept a caller's claim that a
new payload is valid. The complete D-294 derivation/replay remains the qualification evidence.
Descriptors enforce roles/purpose, bytes, live binary policy and retain per-case observations.

V3 preserves3mm spacing, HU[-100,300], RAS, image bilinear/target nearest interpolation and symmetric
96-minimum zero padding. No target-derived image crop. Source cap96M; output cap8M. Restore in
16-slice source-grid slabs to bound interpolation-grid allocations, with the original source affine
translated for each slab. Synthetic comparisons must agree with full restoration before use.

## Resources and execution

Before real reads: native tests and supervised96M synthetic preprocessing/image-only parity and
restoration rehearsal with exact source/environment pins. A changed implementation invalidates that
resource record. Every real request pins capability/recipe, code/environment, resource receipt and
batch projections. Claims are keyed by capability and batch, preventing new request IDs from
silently rereading a consumed batch. Failure leaves its partial evidence and requires a new scoped
recovery plan; never delete a claim to retry.

Per job:20minutes,16GiB process RSS,256MiB evidence and100GiB internal free floor, supervised.
Per file:128MiB compressed,512MiB expanded. Aggregate source scope:306 files,
5,152,089,856compressed bytes and13,196,550,237expanded bytes;6GiB/16GiB outer byte ceilings.
Each batch's read budget derives exact compressed/expanded sizes and unique URIs from qualification
evidence, rejects repeats, and requires complete coverage. Whole continuation ceiling:90minutes and
2GiB retained output across15 jobs, no unaccounted batch reset or automatic retries.

Inspect pilot sheets before continuation; inspect all remaining transformation sheets. Large jobs
run separately after the same successful96M rehearsal. Compare model-input image bytes with the
image-only transform; require preserved nonempty binary targets and correctly restored native grids.
Record round-trip Dice/recall, source/transformed/reference counts, shape/projection, source hashes,
phase/coverage observations, time, RSS and predicted processed-cache bytes. Round-trip reference
metrics assess resampling, not model performance or expert contour quality.

A disappearing target is a recorded preprocessing failure, not permission to omit or fabricate it.
Retain failures and stop before training readiness; investigate the specific recipe/evidence issue.
No whole-organ claim follows from a visible-reference qualification. No MPS/cache training budget
can be inferred from CPU preprocessing alone; that is the subsequent measured runner step.

## Explicit pilot recovery, attempt02

Attempt01 request `d06f830e80ba965b2c7b83de3e1de402a13be511621f3b33541c069d19b24d44`
failed at cohort-store semantic-report comparison, before source-root access/array reading. The
callback checked the exact D-294 payload hashes but returned None instead of the retained validation
report. Correct the callback, test report equality, rerun native tests and the96M rehearsal, then
freeze a new request under capability attempt02. Old request/result/claim remain intact. This is an
explicit zero-source recovery, not a claim deletion or automatic retry. Aggregate source scope stays
306 files because attempt01 read none; include both attempts' logs in final accounting.
