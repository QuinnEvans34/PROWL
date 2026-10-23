# What the existing errors tell us to demand from distillation

October 23, 2026. **Report-only interim analysis**, fixed at the current run's last
complete validation when this task began: 10,000 updates. The 12k validation was
in progress. We did not mix partial cases into a score, change the running job,
read CT/mask volumes, run inference, or repeat source/duplicate qualification.

## Findings

The model's problem is not simply failing to notice a lesion. It frequently finds
some lesion voxels while both missing much of the annotated region and predicting
lesion elsewhere. Those two errors can coexist in the same patient.

| Complete native checkpoint | Positive Dice | Voxel recall | Voxel precision | Detected | Negative alarms | Negative predicted volume |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Current varied-focus 10k | .241350 | .3315 | .2704 | 32/36 | 33/34 | 127.116 mL |
| Same-region parent 10k | .164295 | .2497 | .1761 | 29/36 | 33/34 | 206.895 mL |
| Current best through 10k: 4k | .263595 | .4616 | .2275 | 32/36 | 33/34 | 236.113 mL |
| Completed parent selected 22k | .356714 | .4351 | .3724 | 32/36 | 34/34 | 118.944 mL |
| Historical augmented selected 18k | .423761 | .4844 | .4511 | 33/36 | 27/34 | 59.080 mL |

Dice/recall are means across all 36 positive patients, including misses. Precision
averages positive patients with nonempty predictions; the current 10k denominator
is 36. Detection means any annotated-lesion overlap. An alarm means any predicted
lesion voxel on an annotation-negative scan. Neither is a clinical diagnostic
criterion. Historical input representation/selection differ; that last row is a
reference, not a controlled KD comparison.

At **matched 10k steps**, 28 positive patients improve in Dice, four worsen, and
four are unchanged. Mean paired change is +.077055 with exploratory 95% bootstrap
interval [.035588, .120215]. Recall improves by .081800 and detection by 3/36;
negative-patient alarm count is unchanged while predicted negative-case volume
falls by 79.779 mL. Native voxel burden falls by 24,591 voxels; its paired interval
[-111,811.875, 60,823.05] crosses zero even though the mL interval is negative.
Different voxel sizes make those distinct summaries, not interchangeable units.

This is encouraging same-horizon evidence, **not** a final H0 decision or proof
the 24k intervention succeeds. The current best-so-far and completed parent's
selected endpoint have different training/selection opportunities.

## Size reveals two important failure patterns

| Total annotated patient lesion volume | Cases | Dice | Recall | Precision | Complete misses | Cases with >50% annotation missed | Cases with >50% prediction outside annotation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Small, <1 mL | 5 | .0661 | .4412 | .0372 | 1 | 2 | 5 |
| Medium, 1–10 mL inclusive | 24 | .2786 | .3450 | .2771 | 3 | 16 | 19 |
| Large, >10 mL | 7 | .2390 | .2068 | .4142 | 0 | 7 | 5 |

- **Small-volume patients:** four of five have overlap, but all five predict at
  least twice the annotated lesion volume. Low precision, not just complete
  misses, is a major obstacle in this tiny subgroup. This does not prove all extra
  prediction is attached to the real lesion; some may be elsewhere.
- **Large-volume patients:** all seven have some overlap, but all seven miss over
  half the annotation. Finding a spot in a large lesion is not outlining its full
  extent. Five also have mostly extra predicted voxels, so increasing sensitivity
  alone is not an adequate prescription.
- **Across all positives:** 25/36 miss over half their annotation, 29/36 have more
  than half their prediction outside it, and all 36 have some false-positive
  voxels. Four complete misses still predict lesion somewhere else. Among the 32
  overlapping cases, 23 have more extra than missed voxels and nine the reverse.
- **Negative cases:** 33/34 have at least one predicted lesion voxel; 32/34 exceed
  the existing 50-mm³ predicted-volume alert flag. It is not solely isolated
  single-voxel speckle, but aggregate counts cannot locate the false-positive regions.

These are count-derived error patterns, not visual contour diagnoses. We have not
looked at new images. Net oversizing, missing voxels and extra voxels are not
mutually exclusive; the per-case JSON preserves TP/FP/FN, volume ratios and flags.
Patient volume groups must not be mistaken for individual component sizes.

## Consequences for the teacher pilot

Ask two separate questions: **does it suppress unsupported predictions around
small lesions/negative cases, and does it preserve the extent of large lesions?**
Do not judge the teacher by any-overlap detection alone or one pooled Dice.
The already-selected 12 training cases include a 12-voxel lesion, large/extensive
annotations, multiple components, the formerly clipped case and one negative.
Their identities/order remain unchanged; no validation-driven case replacement.

The agreement-masked KD design keeps manual supervision where teacher and mask
disagree. Nevertheless, if a tiny component has no eligible positive teacher
guidance, KD cannot teach that component through positive teacher targets. Record
that explicitly rather than attributing any later gain to knowledge transfer
without evidence. High-probability false positives and missing large-lesion
extent deserve inspection even if the teacher's average training Dice looks good.

The checklist and complete matched-comparison protocol are in
[the review protocol](PANTS-DISTILLATION-REVIEW-PROTOCOL-20261023.md). No LR, sampling,
threshold, loss-weight or inference change is proposed for the active run based
on this interim review. The teacher experiment's control remains unbound.

## Delivered tooling and evidence

- Pure report analysis: `src/training/native_error_review_v1.py`.
- Snapshot/review runner: `scripts/diagnostics/review_distillation_opportunities.py`.
- Completed-run comparator: `scripts/diagnostics/compare_native_distillation.py`.
- Private report, 18 original native-report snapshots, paired per-patient results,
  unbound comparison template and pending 12-case review form:
  `E:/PROWL/readiness/distillation-error-review-20261023-a01/analysis-02/`.
- Final regression: **35 tests passed**, 7.954 supervised seconds, peak owned RSS
  70,950,912 B, exit 0/reaped. Includes synthetic end-to-end completed 24k/70-case
  comparisons with mocked MLflow reads, selected/terminal separation, missing
  component guard rejection, receipt/config mismatch rejection and no overwrite.
  Evidence: `tests-03/`. No model, patient volume or real MLflow write in the tests.
- Successful report production: 1.390 s / 54,702,080 B, exit 0/reaped, fixed-source
  report hashes unchanged. Initial `analysis/` failure is retained: the historical
  producer used different top-level/case scope spellings. The adapter now admits
  that exact known legacy pair for descriptive summaries only; it still rejects
  cross-scope matched comparison. No metrics, cohort or quality guard was weakened.

Old frozen scientific and teacher-preparation files are preserved. No new run,
cache, schedule, dashboard state, checkpoint or MLflow record is created by this
work. Hypotheses remain prospective; the next GPU work still waits for completion
and the existing admission gates.
