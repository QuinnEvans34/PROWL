# Input quality and the Dice ceiling — November 8, 2026

False positives explain a substantial, measurable part of the low lesion Dice.
They do not explain all of it. The completed STU-Net checkpoint has both excess
prediction and missed annotation; the saved evidence does not establish a hard
architecture ceiling at .40 or a new geometry/label-decoding bug.

This is a report-only review of saved counts, input traces and source code.
The corrected-label continuation remains unchanged. No new scan/mask arrays,
model/checkpoint tensors or protected test data were read for this review.

## What happens if false positives disappear?

| Completed checkpoint | Actual positive-case Dice | Perfect FP removal, existing misses retained | Perfect FN recovery, existing FP retained |
| --- | ---: | ---: | ---: |
| STU-Net, selected and terminal 12k | .371633 | **.648455** | .622579 |
| KD control, selected 20k | .383593 | .634170 | .644278 |
| KD treatment, selected 20k | .389084 | **.604102** | .660786 |
| KD control, terminal 24k | .381964 | .647237 | .631171 |
| KD treatment, terminal 24k | .383439 | .617982 | .645014 |

These are **reference-mask oracles**, not measured postprocessing improvements.
They require knowing exactly which predicted voxels are wrong. A confidence
threshold can also delete correct voxels; these results do not predict its gain.
Rows describe each run internally, not a controlled cross-model ranking.

For each positive case, let N be reference lesion voxels, P predicted lesion
voxels, and T overlap. Actual Dice is 2T/(N+P). Removing only false positives
leaves P=T, giving 2T/(N+T). Recovering only false negatives leaves prediction
volume N+(P−T), giving 2N/(2N+P−T). We calculate each case first and average over
the same 36 positives. Substituting macro recall into the nonlinear formula
would give an incorrect macro Dice. The two gains must not be added.

The 34 reference-empty cases are excluded from this headline metric. Removing
false alarms **only on those cases changes headline Dice by exactly zero**,
although it would improve the separately reported false-alarm burden. An empty
reference is not independent clinical proof of a lesion-free patient.

At STU-Net 12k there are 171,603 extra lesion voxels on positive cases, 113,259
on empty cases, and 84,240 missed reference voxels. Fifteen of 36 positive cases
miss more than half their annotation. Four of 45 lesion components have no
overlap. A removal-only filter cannot recover those components.

The five cases with total annotated lesion volume below 1 mL have actual Dice
.077216 and perfect-FP-removal Dice .523371. This is a **case-volume group**, not
a per-component size audit. Case 4267 is a concrete overprediction example:
actual Dice .182329, recall .919650, oracle .958143. Case 4681 has zero overlap
and remains Dice zero after perfect FP removal. These patterns require different
solutions. Counts do not identify where extra predictions lie anatomically.

## The curve suggests a precision/recall tradeoff

| STU-Net step | Actual Dice | Perfect FP removal | Macro recall |
| --- | ---: | ---: | ---: |
| 2k | .144179 | .389844 | .310745 |
| 4k | .222087 | .391558 | .320046 |
| 6k | .347182 | .548400 | .452044 |
| 8k | .328011 | **.746525** | .645718 |
| 10k | .346184 | .576514 | .473164 |
| 12k | .371633 | .648455 | .541016 |

At 8k the model overlaps more reference tissue but predicts much more extra
tissue: 428,645 FP voxels on positives, versus 171,603 at 12k. Its lower raw
Dice therefore does not mean it found less lesion tissue. This supports checking
confidence/calibration, while **not** establishing that a threshold can achieve
.746525. It is a retrospective observation, not authorization to select 8k by
oracle performance or expand a threshold search. Raw Dice was still improving
10k→12k; six noisy checkpoints do not establish a permanent .40 ceiling.

## Input findings: confirmed versus unresolved

| Finding | Evidence and interpretation |
| --- | --- |
| Earlier crop clipping was real and repaired | The October 18 intake qualification found 43 clipped positive training cases in the old crop. The replacement preserved all 1,403 train/dev fields, with actual pilot target round trips and complete field/exposure proofs. The current 128-cube STU schedule separately binds 2,978 coverage addresses, all observed. Reused evidence, not a fresh cohort audit or proof of perfect clinical labels. |
| Seven erroneous lesion annotations were used in the first STU run | The completed run used 671 positive/662 empty training cases. Seven upstream-confirmed normal cases contributed 177 erroneous native lesion voxels and 46 lesion-containing updates. The current run binds the qualified correction and 664/669 counts. The parent weights retain that exposure; the size of its effect on Dice is unknown. None of the seven is in development. |
| No new train/inference intensity discrepancy found | Both STU paths call `normalize_region`: nibabel scaled float CT, lossless orientation/crop, clip −100…250 and map to 0…1; training alone then applies the recorded augmentation. Code does not manually reapply NIfTI scaling after `get_fdata`. This is source evidence, not a new DICOM-to-NIfTI HU calibration audit. |
| CT/target identity and geometry have explicit checks | Training binds cached target/source hashes and original shape/affine; development checks CT/mask shape/affine, uses the same orientation/physical sampler, restores native coordinates, and rejects clipped annotation fields. The corrected provider has actual seven-case correction and nine-case input qualification. These checks reduce specific failure risks; they do not prove every annotation is clinically complete. |
| Spatial augmentation is paired and label-preserving | The inspected implementation flips and rotates image, target and support together by exact permutations. Intensity augmentation affects only image support. No interpolated elastic/zoom augmentation was found in this path. |
| “75% focused” does not mean “75% lesion-containing” | On the completed 12k run, 5,189/12,000 patches (43.24%) actually contained lesion voxels. Empty-source focus targets pancreas; positive-source windows can also be lesion-empty. All 2,978 coverage addresses were observed. Sampling is working as specified, but its lesion learning signal may warrant a separate ablation. |
| Pretraining compatibility is unresolved | Our fixed HU window differs from the mean/std path associated with the publisher's recorded nonCT/no-mask plan. Our physical-detail spacing/context also differs from the published sidecar's 1.5-mm plan. This is a transfer-recipe compatibility hypothesis, **not** proof the current preprocessing is wrong, nor a demonstrated cause of low Dice. |
| Tiny-lesion supervision needs measurement | The actual loss uses nearest-neighbor targets at five resolutions with weights 16/31, 8/31, 4/31, 2/31, 1/31. A small target can disappear at coarse scales. Whether and how often that occurs on real batches must come from the continuation's saved scale/class diagnostics or a separately bounded input audit. The full-resolution target can remain intact while coarse supervision loses it. |
| Annotation completeness and acquisition heterogeneity remain open | Array alignment/finite values do not establish contrast phase, adequate acquired slice detail, complete lesion annotation or patient independence. Apparent FP is defined against the supplied reference; a clinically real but unannotated region would still count as FP. No new clinical adjudication was performed. |

The [publisher's pinned preprocessing source](https://github.com/uni-medical/STU-Net/blob/0652eaf5cafda6bc269942238c3695994f2dc4f0/nnUNet-1.7.1/nnunet/preprocessing/preprocessing.py#L275-L284)
uses per-case mean/std for its nonCT/no-mask branch. The locally preserved
restricted plan summary binds original plan SHA256
`5436717587df44a6b18fd911f8ad1e93d99f46c09a39338e4a54a827c9455851`;
the separately inspected publisher checkpoint sidecar binds SHA256
`2e6507001004d6c47f48f81572debb90176f75d4eca21c30a5cdaa5df06ef1ff`.
These describe a plan/code path, not a recovered case-by-case execution ledger.
Fine-tuning can legitimately use target-task preprocessing. Testing compatibility
requires a controlled prospective comparison, not switching normalization on a
model trained with another input distribution. A z-score adapter would also
need matching augmentation/support handling; the current augmenter requires
0…1 inputs. It is not a one-line live change.

Both reported STU and KD Dice use **provided-pancreas regions**. They do not
establish fully autonomous raw-CT performance. The separate autonomous baseline
and its earlier visual review must not be mixed into the current STU evidence.

## Live saved-input crosscheck

Lenovo's [bounded saved-input review](STUNET-SAVED-INPUT-REVIEW-20261108.md),
published in `a728b0a` and clarified in `dcaa0b5`, captured the unchanged run at
global 12,334: **334 new updates, 32.28 recorded minutes, MLflow RUNNING**, same
owned processes. This is a dated snapshot, not a promise of the current count.
The adjacent JSON is imported byte-for-byte, SHA256
`86378997607f46669af57b85254da546540c02584e6607df29f73468b8b3ce26`.

Of those 334 patches, 122 contained lesion voxels; 35 of the 157 positive-source
patches did not. Sampled voxels were 95.50% background, 4.22% pancreas and 0.275%
lesion. These are patch-weighted prefix counts, not unique-cohort prevalence.
The prefix's 251 coverage/83 context windows match the frozen schedule.
Component jitter begins at global 15,971 (new update 3,971), after the reserved
coverage sequence. That is a concrete scheduling consideration for interpreting
early validation and planning a later sampling ablation, not a schedule defect.

The first saved scientific scale diagnostic is an empty patch; both body and
head gradients are nonzero there. A saved positive **qualification** patch,
case 1996, retains 4,821→597→74→9→1 lesion voxels across all five scales.
This rules out disappearance for that patch, not for all small lesions.
No corrected case had appeared in that 334-update prefix; their first scheduled
visit is global 12,373. Actual scientific exposure must be distinguished from
the already-passed real corrected-target qualification. No new integrity failure
was found in the examined evidence. Saturation histograms and representative
tiny-target scale measurements remain missing.

## Recommended next work

1. Let the already qualified corrected continuation run. Review its saved
   per-scale class counts, CE/Dice terms and head/body gradients at the recorded
   cadence. Track false-positive burden and recall alongside Dice. Do not edit
   producing sources or add a competing GPU job.
2. After closeout, use the already proposed bounded confidence-policy experiment
   with the prospectively selected checkpoint, common probabilities and existing
   recall/component/small-case guards. Retain raw outputs if suppression harms
   detection. This tests a practical way to exploit part of the FP oracle gain.
   CAP-EXP-020 remains proposed, not queued by this review; reconcile its old
   storage assumptions with the then-current retained artifacts before execution.
3. Prepare a bounded **training-only** input review spanning small/large targets,
   thick/thin spacing, corrected cases and ordinary empty cases. Bind the case
   list and source hashes before viewing. Show native CT+reference, actual
   normalized sampled window, paired augmentation and target presence at every
   supervision scale; record intensity saturation, physical field of view,
   padding and target class counts. Reuse existing approved images/diagnostics
   first. No repeat full-cohort CT audit, protected-test access or silent relabeling.
4. Use those measurements to choose **one** subsequent training ablation:
   preprocessing compatibility, tiny-target supervision, or lesion-containing
   sampling. Keep checkpoint initialization, cohort, budget and evaluation
   otherwise matched. Do not change normalization, spacing, loss and sampling
   together and then attribute the result to a larger model.

The useful conclusion is that false positives provide substantial headroom,
while misses and small-target behavior also need work. We have an identified
label correction and several testable input/learning hypotheses—not evidence
that all data are bad, that all FP can be removed safely, or that a bigger model
alone will fix this.

## Reproduction and evidence

[ERROR-ORACLES-20261108.json](ERROR-ORACLES-20261108.json) retains every positive
case's counts and both oracles, every empty-case FP count, all six STU reports,
and both selected/terminal KD arms. The reader verifies immutable source hashes,
70 unique identities, 36/34 denominators, legal voxel counts, saved case Dice and
macro Dice. Eight CPU tests cover hand-calculated confusion counts, complete
misses, perfect predictions, invalid counts, saved-score inconsistencies,
nonlinear macro averaging, duplicate/missing cases and changed source bytes.

```sh
.venv312/bin/python -m unittest tests.test_error_oracles_20261108 -v
.venv312/bin/python scripts/diagnostics/review_error_oracles_20261108.py \
  --stunet docs/capstone/coordination/LENOVO-STUNET-COMPLETE-NATIVE-METADATA-20261108.json \
  --kd outputs/prowl/kd-results-20261105-final-01/report.json \
  --output /tmp/prowl-error-oracles-UNUSED.json
```

Output creation is exclusive; prior results are not overwritten. Source hashes:
STU native metadata `c5dcdb2aa77dbe2df2d214932b2d7e27b9dd55351c2aea798f2d676fd047f3cf`;
completed KD report `2679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b`.

Related evidence: [STU completed review](STUNET-RESULTS-AND-NEXT-STEP-20261108.md),
[KD completed review](KD-DESCRIPTIVE-ANALYSIS-20261106.md),
[intake qualification](PANTS-NATIVE-INTAKE-QUALIFICATION-20261018.md),
[STU errata crosscheck](STUNET-ERRATA-CROSSCHECK-20261108.json),
[corrected-provider qualification](STUNET-CONTINUATION-QUALIFICATION-20261108.json),
[live launch evidence](STUNET-CORRECTED-LAUNCH-20261108.json), and
[proposed confidence-policy experiment](CAP-EXP-020-PROPOSED-20261107.md).

The inspected Lenovo source is commit `48ea7c5f2561010c7aa589f97fe682eb4cfddc40`:
`stunet_inputs_20261106.py`, `stunet_transfer_20261106.py`,
`stunet_continuation_session_20261108.py`, plus the frozen common
`segmenter_fast_varied_v1.py`, `segmenter_augmentation_v1.py`,
`segmenter_pancreas_region_v1.py` and `segmenter_physical_windows_v1.py`.
Exact live runtime/Git line-ending reconciliation was already closed in
[the frozen source snapshot](source-snapshots-20261108/README.md).
