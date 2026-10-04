# CAP-EXP-006 coverage inspection — D-288

**The validation coverage failure persists on the original source grids.** The audit found no
source/export shape, affine, unit, role, identity or content-hash mismatch across all27 cases and
both saved runs. It also found an independent crop-size accounting issue: padded processed tensor
volume was being described as scan volume. That issue is corrected additively for future reporting,
with historical fields preserved. It does not explain or reverse the recall failure.

No optimizer update or model inference was performed. Exact54 qualified source files were read
once,54 saved prediction artifacts compared, and all27 source-grid overlays reviewed. The job
completed in278.46s,peakRSS4,230,856,704bytes (3.94GiB),684,668,314 compressed source bytes and
1,759,247,955 expanded bytes, within the frozen20min/16GiB/256MiB-evidence envelope.

## Independent source-grid comparison

| Run | Role | Native mean Dice | Native mean recall | Median volume ratio | Native ROI screen |
|---|---|---:|---:|---:|---:|
|CAP-EXP-005|Train|0.1265|0.9865|13.09|12/16|
|CAP-EXP-006|Train|0.7457|0.9590|1.49|16/16|
|CAP-EXP-005|Validation|0.1515|0.9492|12.72|7/11|
|CAP-EXP-006|Validation|0.4525|0.4594|1.09|2/11|

Native boxes here use10mm rounded upward on native spacing; processed boxes used10mm requested,
12mm realized on3mm voxels. Native crop fraction excludes model padding. Native ROI pass counts
therefore are a separate diagnostic, not replacements for the historical processed-grid scores.

CAP-EXP-006 validation mean absolute native-versus-processed difference is0.00486 Dice and0.00510
recall. Mean native recall falls0.9492→0.4594 between runs. The loss is far too large to attribute
to these observed grid differences alone. Native training recall ranges0.921–0.988; validation
recall ranges0.249–0.659, so every validation case has substantial missing reference at the frozen
operating point. This is not one anomalous case dominating the average.

The checks support a generalization/operating-point failure rather than a simple export-coordinate
mismatch. They do not prove that every preprocessing detail is optimal, that labels are perfect or
that data breadth is the only cause. Hard masks cannot tell whether missed voxels had probabilities
just below0.5 or near zero; a frozen probability-output audit would distinguish those hypotheses.

## Failure families

- **Missing pancreatic extent:** seven validation native boxes contain less than99.5% of reference.
  In1004,5747,7484, the prediction has just one connected component: largest-component cleanup
  cannot change those masks. At the same fixed margin, removing components cannot enlarge any of
  the seven deficient all-component boxes, so it cannot repair their missing extent.
- **Distant false foreground:**7482,7687,7839 have oversized native boxes (32.4%,33.2%,41.2%).
  Their predictions contain3/6/5 components with zero reference overlap, respectively. Such
  components are identified with reference only for post-hoc explanation, not an inference rule.
  The largest component accounts for79.3%,55.2%,86.3% of their predicted voxels. Cleanup may
  shrink boxes but would require a separate coverage-aware policy evaluation; none is adopted.
- **Both:**7839 has deficient coverage and an oversized box. More total crop volume does not
  guarantee containing the missing reference extension.
- **Native/source consistency:** all54 exports match source shape/affine/units and recorded native
  foreground. Compared reference masks come through the same positive-purpose, role-safe loader.
  These are independent binary-overlap calculations on acquired grids, not reusing the original
  Dice result or fitting an alignment transform to labels.

## Per-validation-case native evidence

| Case | Phase/spacing stratum | Recall | Box coverage | Scan fraction | Components | FP-only components | Interpretation |
|---|---|---:|---:|---:|---:|---:|---|
|00001004|arterial|medium_le5mm|0.566|84.96%|3.79%|1|0|missing extent|
|00002942|non-contrast|thick_gt5mm|0.593|93.85%|6.51%|3|2|missing extent|
|00003104|non-contrast|thin_le2mm|0.249|73.89%|3.76%|2|1|missing extent|
|00004995|arterial|thick_gt5mm|0.572|100.00%|6.83%|2|0|provisional ROI screen passes; mask still incomplete|
|00005747|venous|thick_gt5mm|0.352|64.98%|2.69%|1|0|missing extent|
|00007265|delay|thin_le2mm|0.386|98.10%|6.74%|2|1|missing extent|
|00007482|non-contrast|medium_le5mm|0.446|100.00%|32.37%|4|3|oversized box|
|00007484|venous|thick_gt5mm|0.331|53.00%|2.66%|1|0|missing extent|
|00007687|delay|medium_le5mm|0.492|100.00%|33.21%|8|6|oversized box|
|00007839|venous|medium_le5mm|0.407|93.91%|41.17%|6|5|coverage and oversized box|
|00008855|venous|thin_le2mm|0.659|99.65%|4.66%|1|0|provisional ROI screen passes; mask still incomplete|

## Visual review and cohort interpretation

Reviewed all27 six-plane native source overlays: planes at missed-reference coordinate medians and
reference medians. Views are explicitly reference-informed explanatory inspections; they never feed
model inputs. Training displays much stronger overlap; validation repeatedly misses reference
extensions and sometimes predicts distant regions. This is bounded engineering review, not full
slice-by-slice or clinical acceptance. Axis labels refer to native array axes; no anatomy subtype
or diagnostic inference is made.

Failures span arterial, delayed, noncontrast and venous metadata groups. Most phase×spacing cells
have only1–2 cases, so the audit cannot rank phase effects or establish causation. Native reference
volume medians are77.1mL train/84.7mL validation; training ranges1.03–118.1mL (includes partial
references), validation50.0–174.0mL. Do not infer a disease or label-quality judgment from volume.
Cases3717/4965 remain partial-coverage examples; noisy8037/8443 remain. No eligibility changes.

The current rare-first selection was designed to exercise varied inputs, not represent frequencies.
A larger cohort should retain those cases while increasing common-stratum exposure. A proposal
for128 training/48 development-validation **candidates** is now written separately; no selection,
qualification, replacement or freeze has occurred. Original roles, holds and final-test boundaries
remain. Held6350 is still held; candidate coverage is not positive qualification.

## Crop-size issue and correction

[Correction and exact examples](SOURCE-CROP-GEOMETRY-CORRECTION-2026-09-29.md).
A metadata-only same-box mapping holds predictions/margins fixed and maps processed voxel edges
through recorded affines to acquired-source bounds. Five CAP-EXP-00525%-size checks flip pass→fail:
train26/4226 and validation4995/7484/7687. No CAP-EXP-006 size check flips. This isolates a reporting
problem beyond the native-margin rounding difference. The same-box calculations do not on their
own recompute reference containment for that mapped box; don't combine them into a new acceptance
claim without the appropriate evaluation.

The new versioned `source_crop_geometry` is emitted by the expanded evaluator. Old `scan_fraction`
is explicitly labeled padded-tensor space; old provisional ROI booleans remain for compatibility.
A future launch/policy evaluation must use acquired-source crop size plus independently measured
coverage. Historical run artifacts, losses, predictions and decisions are unchanged.

## What to do next

1. Keep CAP-EXP-006 as evidence, not a promoted localizer. More duration on the same16 is not the
   priority. No cleanup or threshold change has been shown to solve the coverage problem.
2. Prepare the metadata-only candidate expansion using the [cohort proposal](LOCALIZER-NEXT-COHORT-PROPOSAL-2026-09-29.md):
   preserve existing diagnostic cases/holds, add common-stratum exposure, qualify consumed inputs
   in bounded batches and measure loader/cache resources.128/48 is Codex's proposed candidate
   budget, not a user-approved final cohort or claim of eligibility.
3. Before selecting the next training treatment, decide whether a small frozen probability/ROI
   diagnostic would answer the operating-point question. It requires inference and a predefined
   comparison; saved hard masks cannot answer it. Do not silently tune against final-test cases.
4. Freeze a new training plan with explicit data/exposure/schedule changes and corrected crop-size
   accounting. Separate data breadth from augmentation/loss/threshold changes when making causal
   comparisons. The expanded16/11 runtime is not permission to load arbitrary new members.

## Verification and preservation

Initial diagnostic suite1193 native passes; added geometry correction and evaluator integration are
covered by the final native suite (see completion record below). Two existing upstream torch
warnings remain. Diagnostic source/env/design were frozen before source reads and rechecked at
completion. The later same-box correction has its own code pin; no raw reread or inference occurred.
The unused first request was superseded after a nonfunctional source cleanup before execution;
only request910ba92b… was consumed. Production training/model/loader logic is unchanged except
additive evaluation geometry fields. Claude's files are untouched; no commit/push or remote upload.

Audit request `coverage-inspection-request-b4c81688-b873-4279-9714-30bae0a2474b`, SHA
`910ba92b6329812f45225a913394db54ef9244fa9e6cd51e55779cdd0f6f685d`.
Audit `outputs/prowl/coverage-inspection-b72d469f-9fef-41c2-8914-d5247c768ddb`, receipt SHA
`e9c74c6972d98570c8b047f60a40e8a5a319be6d994f69207d30b93eb1aa8da1`.
Review `outputs/prowl/coverage-inspection-review-20260929`: summaries, strata,7 visual pages,
same-box source geometry, final code/test pins and an independent derived hash receipt.

Final completion: **1,200 native tests passed**, two existing upstream warnings,32.95s.
Derived review receipt SHA `6e05ca4c6473c1c799ac8fb7f94019a08beb95d11b80496183550941a67981cd`.
