# R-SuperPanTSMerlin: completed Mac pilot

The report-supervised teacher downloads, loads strictly and completes the fixed
12-case MPS pilot. It improves average overlap, but persistent undercoverage,
missed annotation components and false positives block unconditional KD adoption.
No training or full teacher-target cache was launched.

## Identity and execution

Release `AbdomenAtlas/R-SuperPanTSMerlin`, revision
`eab1a7e9f421740bf8f3f834d1f69d17cbe3a8aa`; checkpoint606,931,502bytes,
SHA256 `38535f10430265e431ca3ffa7fe3ff15efed5bccb65ba909b6e3ce18af11e459`.
Safe restricted inert-record tensor extraction exported raw and EMA weights with
exact reload; no unsafe pickle fallback. EMA export SHA256
`68a3b5b2dc77dbdabb4fc2b8d981c486c131be97379a681b333ae479490161f8`.
Conversion13.71s/1,042,939,904B peak RSS, exit0/reaped.

Same fixed12 cases/order, EMA variant,26channels/lesion19/sigmoid, model constructor,
source revision, preprocessing, geometry, reconstruction and threshold as baseline.
New release config is byte-preserved under a documented runtime path alias.
All869 tiles finished in2542.38s (42.37min), peak owned RSS4,229,545,984B,
exit0/workers reaped. Model state remained exact. Final394 file pins match.
All12 representative three-plane overlays were inspected; this is not exhaustive
clinical review. Baseline and original annotations/results remain unchanged.

## Matched descriptive results

Case3059 is interpreted as negative in both derived comparisons using the existing
annotation correction; original reports and raw overlay remain preserved.

| Metric | Mask-only baseline | R-SuperPanTSMerlin |
|---|---:|---:|
| Macro Dice,10 positive cases |0.412151|0.456147|
| Macro recall,10 positive cases |0.518595|0.563252|
| Positive cases with zero overlap |0|0|
| False-positive voxels,2 negative cases |8,122|4,194|
| Annotation components with any overlap |11/17|11/17|
| Components below1mL with any overlap |2/8|2/8|
| High-confidence false voxels (p≥0.9),all12 |24,035|28,026|

Eight positive cases improve Dice;246 and1193 regress. Severe undercoverage remains:
2720 recall3.12%→5.94%;246 recall6.14%→3.32%. Negative691 improves from8,112 to4,002
false voxels; corrected-negative3059 worsens from10 to192. Both negatives still
have predictions. Two cases cannot establish population specificity.

All six missed components occur in8658 and range approximately0.002–0.199mL.
These are26-connected annotation components, not confirmed clinical lesion counts.
The component audit uses saved uint16 probability caches (half-step uncertainty near
thresholds), no CT reads/model execution;9.72s/1,905,147,904B RSS, exit0/reaped.

## Decision and limits

Keep the new teacher as an operational, exploratory candidate. Do not replace the
baseline silently or generate full KD targets yet: higher average overlap does not
resolve harmful suppression or confident false targets. Neither this exposed
training subset nor unknown teacher membership establishes independent accuracy.
This matched comparison tests checkpoint choice under our current inference path;
it does not establish upstream CUDA equivalence or that all preprocessing is correct.

Next useful diagnostic is a bounded upstream CUDA reference for2720, with6222 as a
stronger-overlap comparison, after the laptop GPU is free and its missing upstream
dependency is resolved. That run has not been launched. Only after resolving the
remaining teacher-quality issue should we qualify a matched KD/control experiment.

The request's inherited `teacher.model_card_license: MIT` describes baseline
metadata and is not verified for this candidate. Its card has no explicit license
field. This correction is recorded additively in final-review.json; frozen request
is preserved. No model redistribution. External source license is separate.

## Evidence

External root `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023`:
`teacher-rsuper-merlin`, `rsuper-merlin-convert-01`, `rsuper-merlin-pilot-01`
(request/result/resources, matched-settings, paired-comparison, final-review),
and `rsuper-merlin-components-01` (request/result/resources).

Baseline result SHA256 `23c9d7d00e980ad9c09c83cd38992cc8db6e44d90f26f5090f95f453b7c55bda`;
candidate result SHA256 `e465761fa7217e7cf7b7f1121ec579e374444532ef4c3412e4b3c02dde35c5bc`.
Five public comparison/checkpoint tests passed before launch; preserved receipts
and final pin verification establish the code used for this run.
