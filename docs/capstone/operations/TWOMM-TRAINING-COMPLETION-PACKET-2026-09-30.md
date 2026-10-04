# After full-cohort inference: finish evaluation and the bounded training executor

Planning packet, not a training request. D-303 has passed all153 cases and independent recovery; see
[full results](TWOMM-INFERENCE-FULL-RESULTS-2026-09-30.md). Full-cohort inference/export is qualified.
Existing113train/40development-validation members and23 holds stay unchanged. All data preparation
needed to supply model inputs is already implemented; avoid reopening cohort selection or rebuilding CT caches.

## 1. Native-reference access and metrics — completed under D-304

D-304 implemented and tested this slice and scored all153 original references; see
[results](NATIVE-REFERENCE-SCORING-RESULTS-2026-09-30.md). Both read requests are consumed.
The original requirements below remain the design record. Next implementation is section2;
future training evaluation requires its own stage-specific read budget, not replay of D-304.

The persisted cache has processed targets; genuine native-grid accuracy needs original pancreas
references. Current `twomm_cache_inputs.ExpandedDataset.load_native` reads both CT and pancreas;
calling it just to obtain a reference would reread153 CTs unnecessarily. Add a separate target-only,
purpose-bound reader with a fresh capability and exact read accounting. Do not widen/reuse D-300's
consumed paired-input requests or activate generic source aliases.

Retained binding identifies153 exact pancreas files:

| Role | Files | Compressed bytes | Expanded bytes |
|---|---:|---:|---:|
|Training fit diagnostics|113|17,030,094|3,410,258,336|
|Development-validation references|40|4,912,185|988,609,695|
|One complete pass|153|21,942,279|4,398,868,031|

These are metadata accounting, not new source reads. Maximum expanded file92,889,440bytes. Resolve
and verify the frozen cohort/qualification/annotation lineage, protected role, original file hashes,
strict-binary mapping implementation, source geometry and observed unit interpretation. Read one
reference at a time, retain source bytes unchanged and reject corruption/changed identity. Use source
CT geometry already qualified and hash-bound; no new inference about unknown physical units.
Training references remain training-fit diagnostics, not independent validation. No held case is promoted.

Implement a new bounded native metric API rather than weakening old helper limits. Existing
`localizer_coverage.inspect_coverage` caps the grid at64M and prediction foreground at4M, and creates
foreground-coordinate arrays. Existing processed metrics cap the grid at8M. Neither is a drop-in
consumer for this96M-source/16M-processed setting. In particular, a dense bad prediction must be
scored, not removed because it exceeds a foreground-count limit.

Use bounded slabs/axis reductions for counts and box bounds. Required outputs: TP/FP/FN, Dice,
precision, recall, reference/predicted volume and ratio, empty-localization state, all-component box
with the existing10mm voxel-axis-rounded margin, reference coverage and crop fraction using the
acquired native volume as denominator. Report partial-reference limitations and per-case failures.
Keep unsupported optional component-detail work explicit; it must not suppress basic metrics.
All153 retained source affines are orthogonal under the existing1e-4 tolerance (metadata-only check);
new code must still validate affine/spacing rather than assume that condition for arbitrary inputs.

Tests: empty/dense/fragmented predictions; tiny/boundary references; signed/permuted anisotropic axes;
large96M envelope without unbounded coordinate allocations; exact count/box arithmetic; wrong-role,
held, changed source/hash, changed decoder and wrong-geometry refusal. Current reference-free
inference remains separate and cannot silently acquire target access.

Qualify on synthetic data first. Then freeze a target-only scoring pilot and full pass under measured
limits. Existing D-302/D-303 initial native predictions can test this scoring path without another
model forward. Pin each export, its transform, initial weight digest and reference identity. That
produces initial-model diagnostics, not trained-model results. No new raw reads are authorized merely
by writing this planning packet.

## 2. Matching training executor and checkpoint version

Completed under D-305: [transaction results](TWOMM-TRAINING-TRANSACTION-RESULTS-2026-09-30.md).
1,539 native tests and final source-matched MPS transaction/recovery pass. The exact CAP-EXP-007
request is frozen and awaits launch approval; the requirements below remain the design record.
The implementation chooses a fresh baseline and386 total stage-specific label reads. No real launch.

Keep D-301 readiness sessions inference-only. Add a separate training identity with frozen plan,
request/authorization, cache/cohort/recipe, model/loss/sampler/optimizer, source/environment, prediction
policy and reference-scoring controls. Start from a fresh seeded model; no previous learned checkpoint.

Connect role-safe cache sampling to an explicit finite update loop. Record completed-step boundaries,
member and crop trace, loss, finite gradients/weights, scheduler position, evaluation/export references
and append-only progress. Evaluator entries must never enter the optimizer. Check interruption before
and after update/publication boundaries; retain incomplete attempts and require explicit continuation
from a completed verified checkpoint. Do not silently repeat an uncertain update or consumed request.

Synthetic end-to-end rehearsal must use the actual144³ model, a variable-volume fixture approaching
the16M processed envelope, nonzero updates, evaluation, export, save/reload, interruption injection and
independent backup/restore with primary reads blocked. D-301 already proves its synthetic step2 codec;
it does not prove the new authorization/progress/evaluation transaction. Keep16GiB memory, AC,
100GiB internal-free and20GiB backup controls, with output/checkpoint quotas recorded for this run.

## 3. Proposed first broader training diagnostic, to freeze after the above

A bounded300-update run fits the present adapter's ceiling and offers two complete113-case training
passes plus74 further case exposures. Deterministically shuffle per pass using a recorded seed/policy;
report exact exposures instead of calling300 updates “300 epochs.” Keep144³/2mm, seed42, balanced
CE+Dice, AdamW LR0.0003/weight decay0.00001 and the existing50/50 processed-grid sampler as the
starting proposal. This changes cohort, spacing and physical sampling context relative to CAP-EXP-006;
it is not a single-factor scientific comparison or a long-scale training conclusion.

Proposed checkpoints:0,113,226,300. Proposed evaluation:full113/40 before/after, development-validation
at113/226, with native coverage/crop fraction and per-case failure evidence alongside Dice. Existing
initialized exports may only substitute for a fresh baseline after exact cache, initialization weights,
prediction policy and geometry equality are established; otherwise regenerate. This is artifact reuse,
not a warm start from a learned model. No threshold tuning, case filtering or automatic promotion.

Use D-298's2.68s synthetic update measurement and D-303's actual full-volume timing to budget the
finished loop; a45minute total envelope is a proposal, not yet approved/frozen. Rehearsal must also
measure the actual sampler, native scoring and checkpoint costs. If those do not fit, revise the
explicit plan before launch rather than reducing membership or silently extending time.

The first run answers whether optimization remains healthy across the broader cohort and whether
coverage improves or collapses. Longer training should follow its learning/coverage evidence, not
repeat the small-cohort failure blindly. The final deliverable of these slices is an exact reviewable
training request, then an explicitly authorized launch. No literature/UI completion is a prerequisite.
