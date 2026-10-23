# Distillation comparison and teacher-pilot review protocol

October 23, 2026. Additive analysis protocol; it does **not** modify the frozen
teacher preparation, running trainer, current experiment's hypotheses or launch
authority. Teacher-assisted/exploratory scope is explicitly approved; independent
generalization remains unestablished because teacher membership is unknown.

## 1. What the comparison will measure

Use the same 70 development patients, including every one of the 36 annotated
positive patients and 34 annotated-negative patients. Keep their exact identities,
native targets, voxel volumes and inference scope. The future matched supervised
control is **not yet selected**. Review the ongoing run before binding it. The old
augmented record is a separate reference, not an interchangeable control.

Primary endpoint is positive-patient macro native Dice at the best complete
scheduled validation among 2k, 4k, ..., 24k; earliest step wins a tie. Terminal-24k
comparison is mandatory and secondary, never substituted for primary. The same
full-horizon rule applies to both arms. Incomplete series produce no final verdict.

Paired percentile bootstrap: 10,000 draws, seed 20261023, patient as the resampling
unit. Dice, recall and detection use all 36 positive patients; alarms and empty-case
burden use all 34 negatives; pancreas Dice uses all 70. Burden intervals resample
paired patient contributions and sum 34 sampled contributions. Report predicted
native voxel counts **and** mL separately because voxel volumes differ.
Size-group Dice intervals are descriptive and not multiplicity-adjusted claims.

H0: selected KD minus matched-control Dice <=0. Reject only when the paired 95%
interval lower bound is above zero; otherwise fail to reject, not accept H0.
Practical acceptance additionally needs >=+.02 Dice and all point-estimate guards:

| Guard | Required treatment-minus-control change |
| --- | --- |
| Positive-patient any-overlap detection | >= -.03 |
| Negative-patient any-voxel alarm rate | <= +.03 |
| Pancreas macro Dice | >= -.02 |
| Total predicted lesion voxels in negative cases | <= 0 |
| Positive-patient macro lesion voxel recall | >= -.03 |
| Native <1 mL component detection recall | >= -.03; component evidence required |

A failed known guard or a Dice interval upper bound below +.02 means practical
rejection. Otherwise a missing mandatory guard means **not evaluable**, never
acceptance. With all guards known/passing, unmet Dice support is inconclusive.
Report statistical and practical decisions separately. These are research rules,
not clinical guarantees or statistical noninferiority tests.

These KD thresholds are not retroactively added to the current varied-focus run.
Its existing final analysis must use its own frozen specification/seed. The
current 10k analysis is explicitly exploratory and issues no interim H0 verdict.

### Individual small lesions versus small-volume patients

Existing reports group patients by **total** annotated lesion volume: small <1 mL,
medium 1–10 mL inclusive, large >10 mL. A large-volume patient can also contain a
tiny second lesion. Those patient bins cannot measure the proposed component guard.

Define a reference lesion component by 26-connectivity of the native binary lesion
annotation. Its volume is its voxel count times abs(det(native affine)); <1,000 mm³
is small. A component is technically detected if at least one predicted lesion
voxel overlaps it. Each GT component is counted once. One predicted component can
overlap more than one GT component; this is an any-overlap measure, not proof of
correct instance separation or clinically meaningful localization.

Compute component recall as detected small components / all small components.
Bootstrap its difference by resampling paired **positive patients**, retaining all
components within each sampled patient, then taking the ratio of summed counts.
Count/report zero-denominator draws; no small components means not estimable.

The implemented sidecar contract requires every case and **all** GT components,
including missed and large components, with stable component IDs, voxel counts,
physical volumes, detection flags, target/geometry hashes and the exact native
report hash. Component totals must reproduce the existing per-case metrics.
Both arms must have identical component references. Do not build these records
from patient-level counts, infer them from Dice, or substitute a small-case average.

Existing saved reports lack these component details. An explicitly qualified
evaluation-sidecar producer or approved saved-prediction analysis is still needed
before a practical KD acceptance can be computed. No new inference or mask reads
are authorized by this document or performed in this preparation task.

### Comparison tooling and operator handoff

`scripts/diagnostics/compare_native_distillation.py` is report-only. The template is
at `E:/PROWL/readiness/distillation-error-review-20261023-a01/analysis-02/comparison-template.json`.
It intentionally says `UNBOUND_NOT_READY`; the control/treatment and matching
review are blank. Binding this template is not training launch authority.

Before use, supply pinned configurations, launched receipts, input controls,
results, reaped-worker reports, tracking IDs, and a matching-review record. That
review must approve `auxiliary_teacher_loss_only` and bind both configuration
hashes after reviewing source/model/input/evaluator equivalence. The tool checks
the actual receipt's configuration/control hashes, exact fixed recipe equality,
cohort separation, contiguous 24k journals, all twelve complete native reports,
selected/terminal endpoints and read-only MLflow FINISHED status. It rejects
unknown configuration interventions and mixed inference scopes. No model loads,
prediction or training occur.

Pinned-file records have `path` and `sha256`. The matching-review JSON contains
`approved`, `changed_factor`, `control_configuration_sha256`, and
`treatment_configuration_sha256`. Native component sidecars have version
`native-components-1`, `report_sha256` (the scheduled `native-XXXXXX.json` bytes),
`matching` exactly equal to the protocol's component rule, and `cases`. Each case
contains `case_id`, `target_sha256`, `geometry_sha256`, and `components`; each
component has one-based `component_id`, `voxels`, `volume_mm3`, `detected`.

```powershell
.venv-prowl-windows/Scripts/python.exe scripts/diagnostics/compare_native_distillation.py --manifest <bound-comparison.json> --output <new-report-directory>
```

Outputs preserve all paired-patient records, deltas, bootstrap intervals, guard
states and input hashes. Existing output directories are never overwritten. A
missing component sidecar does not prevent reporting Dice, but prevents an
otherwise favorable result from being called practical acceptance.

## 2. Teacher-pilot checklist: unchanged 12 training cases

Selection and order remain exactly those in the frozen preparation. Do not choose
new cases based on this development analysis, silently exclude difficult cases,
or use development/test data to generate optimizer targets.

| Case | Why it is already in the pilot | Emphasis at review |
| --- | --- | --- |
| PanTS_00002720 | Previously severely clipped; retained/corrected | Entire annotated field, distant extent and frame edges |
| PanTS_00003615 | Positive case with largest coverage bank | Tiling seams, complete extent and both pancreas/lesion ends |
| PanTS_00000691 | Negative case with largest coverage bank | Unsupported high probabilities inside/outside pancreas |
| PanTS_00003059 | Smallest positive annotation: 12 native voxels | Tiny-target support after teacher resampling and KD eligibility |
| PanTS_00000246 | Largest positive lesion by voxel count | Large-extent underprediction and boundary/detail loss |
| PanTS_00008658 | Most annotated lesion components | Each component, not just the largest lesion or central slice |
| PanTS_00003777 | Existing difficult positive case | Small targets, contrast and local probability support |
| PanTS_00004735 | Existing difficult positive case | Contours, extra predictions and neighboring structures |
| PanTS_00002498 | Existing difficult positive case | Orientation, physical alignment and contour completeness |
| PanTS_00001193 | Existing difficult positive case | False-negative regions versus incorrect positive regions |
| PanTS_00005832 | Existing difficult positive case | Small-target detail and probability suppression |
| PanTS_00006222 | Existing difficult positive case | Larger extent, shape and partial-coverage patterns |

All twelve are training patients. There is only **one annotation-negative pilot
patient**; this pilot cannot establish population specificity. Training/potential
teacher-seen performance is an engineering diagnostic, not independent accuracy.

### A. Identity, geometry and full field — hard engineering checks

- All 12 accounted for, unchanged source/teacher/config/preprocessing/control pins,
  strict 26-class loading and lesion channel 19/sigmoid/EMA identity preserved.
- Verify admitted source shape/affine against ITK/NIfTI coordinates, including
  axis order, flips, translations, spacing and obliquity. Review the three physical
  planes and source-landmark alignment; matching shape alone is insufficient.
- Teacher inference tiles depend on CT geometry, not manual lesions. Labels may
  select illustrative slices only. Student masks remain supervision, not channels.
- Defined probability support for **100% of the native annotated field**, no
  reconstruction gaps, uncovered coordinates, hidden zeros, missing components or
  silently dropped cases. This means a probability exists there—not that the
  teacher must classify every lesion voxel correctly. Count boundary-cell extension.
- All probabilities finite/in [0,1], continuous through native reconstruction and
  cache quantization. Preserve the current quantified rounding error and ambiguity
  treatment at 0.5. Verify the student-window support and exact spatial replay.
- Padding, seams, flips, off-by-one shifts or field truncation are unresolved
  engineering failures until explained; no invented Dice-based pass.

### B. Teacher behavior and detail — factual visual review

For each case record: observed anatomy/lesion alignment, missed extent, extra
predictions, tiny-component visibility, boundary smoothness/erosion, and the
probability pattern around annotated edges. Review all components and lesion
extremes, not only one attractive slice. The prepared figures show three selected
planes; if they do not cover all components/extremes, mark that item unresolved
and request an additive, bounded component-centered view. Do not edit the pinned
pilot just to label the original images sufficient.

Record teacher-versus-annotation voxel precision/recall and Dice at q>0.5 as
diagnostics, with missing/empty denominators explicit. Do not call a thin overlap
a good outline. A low round-trip or boundary-detail measure triggers investigation,
not removal of the case. No new global teacher Dice cutoff has been invented.

Before approving usefulness, inspect high-probability contradictions (q>=0.9 on
manual non-lesion voxels) and strongly suppressed true lesion voxels (q<=0.1), by
background/pancreas/lesion strata and per lesion component. These are descriptive
probability bands, **not calibrated confidence or clinical thresholds**, and do
not alter the KD loss. Record eligible positive KD voxels for each component;
an all-ineligible tiny lesion or widespread confident false predictions requires
an explicit usefulness decision, not an automatically approved pilot or case
exclusion. Manual DiceFocal remains active even where KD is excluded.

The frozen pilot currently saves native probability caches, per-case means,
teacher threshold counts, coverage/resource records and PNGs. It does **not**
already emit these per-component eligibility/high-probability contradiction
counts or a surface-distance analysis. A separate bounded read of the pilot's
new probabilities and existing training targets is needed for those supplemental
summaries. It must be logged, training-only, and performed only after the pilot;
no claim that this evidence exists today. Quantitative boundary distances, if
used, must declare their surface definition, physical units and empty-set behavior.

### C. Resource and operational checks — keep existing limits

| Check | Frozen pilot limit / required observation |
| --- | --- |
| Current run | Normal completion, final native validation, backups, reaped workers, MLflow FINISHED |
| GPU ownership | Existing exclusive GPU lock; no competing training |
| Wall time | <=5,400 s; no automatic retry/resume |
| Owned process-tree RSS | <=12 GiB |
| Observed GPU reservation | <=6 GiB; OOM fails without retry |
| Free space | >=100 GiB on C: and E: |
| Pilot target cache | <=2 GiB |
| All combined caches | <=32 GiB; do not delete old evidence to fit |
| Allocation/tile preflight | <=256 million source/resampled voxels; <=1,500 tiles/case; <=10,000 tiles total |
| Completion | 12 reports and actual reviewed figures; frozen teacher unchanged; workers reaped |

Record per-case time, tiles, peak memory, compressed target bytes and quantization
error. The existing metadata estimate is 837 total tiles, not a timing forecast.
Raw full-cohort teacher targets need 30.36 GB with only 11.40 GB left inside the
existing combined cap; measure compression before authorizing the whole cache.
Twelve deliberately difficult cases are not an unbiased timing/compression sample.
Report a range and assumptions; enforce actual caps throughout eventual generation.

### D. Review record and decision

Use `analysis-02/pilot-review-template.json` beside this task's error report. Every
case starts `reviewed: false` / `decision: pending`; the overall record says
`accepted: false`. Add reviewer, exact image/artifact hashes, factual findings,
missing evidence and each engineering/resource result after actual inspection.
No synthetic or imagined visual review is allowed.

Engineering pass requires every hard check and every case accounted for. Teacher
usefulness is a separate explicit judgment with unresolved failures stated; it
is not established by successful code execution or publication scores. If a
quality/resource gate fails, retain the failed output and seek a decision on a
separately versioned change. Neither this checklist nor a passing teacher pilot
authorizes scientific training. Complete targets, actual student CUDA/control/
cold-restore checks, measured scientific budget and a qualified launch receipt
plus explicit launch approval remain necessary.

## 3. Statistical and clinical limits

The development set has been repeatedly reused and selects checkpoints. Patient
bootstrap intervals condition on the selected models; they do not correct that
selection, estimate seed-to-seed reproducibility, or establish external/clinical
generalization. Unknown teacher exposure is an additional limitation. Report all
groups and failures, including zero-Dice cases and undefined quantities.

No training, evaluation, data audit, MLflow run, dashboard change, automation or
protected test read is started by this document.
