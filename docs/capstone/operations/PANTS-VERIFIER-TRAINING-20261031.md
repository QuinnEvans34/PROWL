# Reject false lesion candidates while preserving real lesions

Status: READY for explicit scientific launch, October 31. Setup and qualification
are complete. Scientific training has NOT started. Design and producing files are frozen.
The completed533-patient candidate archive and original failed export are retained.
No candidate-generator retraining or duplicate dataset audit is needed.

## Scientific scope and roles

The fixed terminal restricted800-patient SuPreM generator is unchanged. The verifier
uses its predictions on266 fitting patients,67 tuning patients and later200
calibration patients. The70 development patients remain protected during design,
fitting, checkpoint selection and threshold calibration. The inherited pancreas
margins and unknown SuPreM pretraining membership retain the design-informed,
exploratory scope. We make no independent-generalization claim.

The fitting-only candidate review measures component extents, overlap labels,
missed GT components and small-lesion accounting. No tune/calibration labels are
used to choose the representation. Zero-candidate patients remain in accounting;
they provide no candidate-classification updates. A missing generator proposal
cannot be recovered by a verifier.

## Candidate representation under qualification

Every26-connected predicted component is retained without size filtering. Two
64-cube views use four channels: windowedCT, lesion probability, component support
and validCT sampling locations. A global view contains the complete predicted
component plus10mm context; the supplementary64mm detail view centers on the
component's highest predicted lesion probability. Ground truth chooses neither
view. Global steps adapt to extent; detail steps are1mm along the preserved source
axes. Obliquity is preserved, not deobliqued. Resampling a thick slice does not
create new acquired detail.

CT uses linear interpolation. Probability uses linear interpolation plus maximum
candidate-voxel splatting. Component support combines nearest-neighbor voxel occupancy with conservative
voxel-center splatting, preserving thick-slice support and one-voxel candidates. The global view must account for
every source component voxel; local view clipping is measured and explicitly
allowed because it supplements the complete global view. Global detail loss and
voxel merging are measured separately from field coverage. Padding is explicit.
Float16 cached storage must retain support/valid channels exactly and differ from
float32 by at most0.00025. Model computation remainsfloat32.

Four prediction-only scalars retain physical scale and confidence: log1p volume
inmL divided by10, log1p global side length inmm divided by10, mean and maximum
component probability. These contain no labels or ground-truth-derived locations.
Any overlap with a GT lesion gives a positive candidate label. Merged components
can hit several GT components; their hits are preserved rather than forced into
one-to-one matches.

## Proposed fitting recipe

Shared3D encoder: stride2 convolutions16/32/64 channels, GroupNorm,SiLU and global
average pooling on each view. Concatenate the two64-dimensional representations
and four scalars, then a32-unitSiLU head and one logit. No dropout or augmentation
in this first controlled verifier. AdamW lr0.0003, weight_decay0.0001, gradient
clip5, batch8, seed20261031,80 complete candidate epochs. Deterministic CUDA with
fixed backend settings matches qualification. Candidates are shuffled once per
epoch; inverse candidates-per-patient weights balance fitting-patient contribution.
No diagnosis/healthy label is inferred from annotation-negative status.

Tune-only patient-balanced BCE is measured after each epoch. Select its earliest
minimum, preserving selected checkpoints and terminal weights with independent
backups. No calibration or development metrics participate in model selection.
Scientific run length in updates is computed from the actual fit candidate count.
Scientific launch requires a new ready receipt and explicit launch instruction.

## Calibration and hypotheses

After checkpoint selection is frozen, use the200 calibration patients to choose
the largest score threshold satisfying no additional missed positive patient,
no loss of detected<1mL GT components, positive macroDice delta>=-0.01 and no
increase in negative-case lesion voxels, against the same generator alone.
Scores>=threshold retain the entire component; tied scores stay together. Include
threshold0 and next-representable values above scores so the search is complete.
Missing positive/negative/small-lesion denominators produce an explicit
nonestimable result and threshold0 fallback, not a guard pass.

The final matched70-case comparison retains the originalH0: negative-patient
alarm reduction<=0. RejectH0 only if paired95% bootstrap lower bound>0
(10,000 resamples,seed20261023). Practical support additionally needs>=0.10
absolute reduction and all sensitivity/Dice guards. Failure to rejectH0 is not
proof of no effect. This classifier cannot trim an oversized retained boundary;
improving positive-case Dice to0.50 is not assumed.

## Readiness order and budgets

1. Fit-only review266; one CPU stage,60min/12GiB. Preserve any failure.
2. Restore232 additional fit/tune CTs (7,297,244,827bytes) and reuse101 already
   recovered files by exact original identity. No masks/test/calibration content
   opened by restoration;3h/8GiB new-source cap and100GiB free floor.
3. Freeze design after fit-only size/label review. Pilot12 real fitting patients,
   inspect actual PNGs and record coverage/detail/padding/precision and resource
   measurements. No silent exclusions. CPU pilot30min/12GiB/2GiB outputs.
4. Build all333 fit/tune inputs under frozen design:2h/12GiB,8GiB cache plus8GiB
   independent backups,40GiB combinedC-backup cap and100GiB free floors. No
   calibration inputs at this stage. Verify complete patient/candidate accounting.
5. Five nonpromotable actualGPU updates and cold replay of the fifth update from
   independentC: step4 backup;20min/12GiB/6GiBGPU each. Require finite nonzero
   gradients, exact restoration and exact next model/optimizer/RNG/input trace.
6. Freeze source/configuration/input hashes, final tests, evidence report and
   dashboard handoff. No MLflowRUNNING record or dashboard switch until approved
   scientific launch. Proposed science bound8h/12GiB/6GiBGPU; no auto-resume.

MLflow will have a separate human-named verifier run with training loss and tuning
BCE. Neither diagnostic updates nor prediction recovery are added to training
hours. The phone dashboard must show classification metrics without inventing
development Dice. No recurring monitoring task is created by this preparation.

## Prospective representation correction and pilot dispatch

Before real pilot or tune-label access, review found that native voxel-center
splatting alone makes thick-slice components sparse when upsampled. Design-v3
combines nearest-neighbor occupancy with conservative center splatting. Three
synthetic tests pass for thick slices, tiny candidates, and global/local coverage.
Old receipts remain preserved; patients, labels and fitting recipe are unchanged.
Design-v3 SHA: acd8c39562a44bfa2ac99c6cc8f59b0fba6b9b9626ea01e0dda4f24ea9bd7cc7.
Fit review completed:266 patients,1053 candidates (140 overlap/913 false),eight
zero-candidate patients;923.171s/2534268928-byte peak owned RSS/clean exit.
Real12-case pilot owned5136 is running; visual and resource gates remain.

## Real pilot result

All twelve selected fitting-case PNGs were actually reviewed. Seventy candidates
passed complete global-coverage and storage checks; one supplementary detail view
was partial. Maximum float16 error was0.000244140625. Native annotations and
predictions remain separate; predicted false positives and incomplete outlines
are inherited generator errors, not grounds for excluding patients. Representative
axial images support the alignment review; volumetric accounting establishes3D
coverage. Upsampled CT can look smooth and does not create acquired detail.

Pilot exited0 with workers reaped,109.969seconds and1,681,715,200-byte peak owned
RSS. The bound visual-review.json is in the pilot evidence directory. The final
37-test CPU suite passed in13.31seconds; an additional tuning-path/launch suite
passed8 tests in8.76seconds. GPU qualification will also time a complete tune pass
and verify that it leaves checkpoint state unchanged. This pass is diagnostic;
it neither selects a scientific checkpoint nor accesses calibration/development.

## Final readiness review

All readiness gates passed. The evidence summary is
`E:/PROWL/readiness/verifier-training-20261031-a01/readiness-review.json`.
The exact frozen launch receipt is `ready.json` in that directory, SHA-256:
`0ae6d1eae68c1a6cc23ffe575138286ea1de13d81d69b3fcf0c757c3d669e77a`.
An independently hash-matched copy of the ready receipt, configuration, design,
visual review and final evidence summary is saved under
`C:/Users/quinn/PROWL-Backups/verifier-readiness-20261031-a01`.

- Complete intake: all 333 patients, exactly 266 fitting and 67 tuning; no exclusions.
- Candidates: 1,053 fitting (140 overlapping annotations, 913 nonoverlapping) and
  253 tuning (34 overlapping, 219 nonoverlapping). Eight zero-candidate patients
  remain in patient-level outcome accounting. They generate no classifier updates.
- Every predicted component is fully represented in the global view. Twenty-two
  supplementary detail views are partial; they do not replace the global view.
- Maximum float16 storage error: 0.000244140625; support/valid channels stay binary.
- Cache: 1,755,972,137 bytes. Independent cache/manifest backup: 1,758,471,764 bytes.
- Full build: 2,598.688 seconds, 2,629,173,248-byte peak owned RSS, exit 0/reaped.
- Actual GPU producer: five finite, nonzero-gradient updates, plus all 253 tuning
  candidates; 32.750 seconds supervised, 1,512,415,232-byte peak owned RSS and
  316,669,952-byte peak reserved GPU memory. Tune inference did not mutate state.
- Cold process: loaded the independent C: step-4 backup and reproduced the fifth
  update exactly, including inputs, loss, model, optimizer and RNG. Supervised
  11.937 seconds, 1,509,027,840-byte peak owned RSS, exit 0/reaped.
- CPU evidence: 37 targeted tests plus the additional actual tuning-path test pass;
  the separate tuning/launch suite also reran seven existing launch tests.
- Intake/qualification producing pins, complete cached inputs and independent
  backups were checked by the final freeze. No diagnostic checkpoint is promoted.

### Boundary-context limitation

Across 1,306 candidate inputs, 22 global views and 59 detail views contain less
than 50% valid region samples. Minimum fractions are 0.20352 and 0.15371.
The worst examples (fitting case 802 and tuning case 1617) were additionally
reviewed in three orthogonal planes for both views, using cached arrays only.
Support remains visible inside the inherited region boundary; full component
coverage passes. The available-context mask distinguishes padding from tissue.
These crops do not provide full surrounding CT context outside the generator's
pancreas region, and boundary artifacts may become classifier cues. This is a
recorded limitation of the frozen design, not an exclusion or a claim of perfect
context. No representation change followed tuning-data access. Full-source
annotation counts match the inherited region counts for all 266 fitting cases;
tuning annotation containment was checked during the complete build.

### Proposed scientific run and next action

Run: **Reject false lesion candidates while preserving real lesions**
(`pants_candidate_verifier_20261031`). Fresh initialization; 80 epochs, batch 8,
10,560 updates. Select the earliest minimum tuning patient-balanced BCE. The
200 calibration patients and 70 development patients remain protected during
fitting. Calibration and the matched combined-model outcome review follow fitting
as separate stages; no automated scientific successor is armed.

Measured steady diagnostic updates took approximately 0.5 seconds and a complete
tuning pass took 8.437 seconds. Core projection is 5,954.96 seconds (1.65 hours).
Plan approximately 1.5–2.5 hours with logging/backup/thermal/disk variability; this
is an estimate, not a guarantee. The eight-hour supervisor limit remains fixed.

MLflow read-only SQLite health/access passed and launch logging is tested. A new
human-named run will record live training loss and tuning BCE only after launch.
The phone dashboard changes are staged, parser-tested and not applied. Its launch
handoff must preserve historical runs and journal-derived training hours, show
classification metrics, and avoid displaying invented development Dice.

After explicit user launch approval, first inspect existing output/dispatch and
process ownership, then use the frozen entry point:

```powershell
.venv-prowl-windows/Scripts/python.exe scripts/train_verifier_20261031.py --launch-sha256 0ae6d1eae68c1a6cc23ffe575138286ea1de13d81d69b3fcf0c757c3d669e77a --explicit-user-launch
```

Apply the staged dashboard only after the saved before-hash checks and backups.
Verify advancing actual journal updates, stored live MLflow loss, matching initial
independent checkpoints and the private phone API before reporting launch. No
scientific output or MLflow RUNNING record exists from this preparation.

H0 is **not tested**. Engineering qualification is not evidence that this verifier
reduces false positives, preserves detection, or raises Dice. Its usefulness will
be assessed using the frozen calibration/comparison procedure after fitting.

## November 2 launch handoff

Explicit launch approval received. Owned68400/supervisor18400/worker25708 runs
this exact frozen receipt. Actual updates advanced122->168->200; MLflow RUNNING
with stored losses and first tuning BCE0.37431773265418505 at132. Initial E:/C:
checkpoint hashes match. Monitor17148/PID38312 serves nine experiments through
the unchanged private Tailscale route; local/private APIs200 and actual summed
journal time verified. Evidence: launch-verification-20261102.json and dashboard-
applied-20261102.json. A display-only encoding cleanup affected three separators
in live unpinned HTML; staged frozen source remains unchanged. No redispatch,
source edits, automatic retry or next experiment. Calibration/dev evaluation is
separate from this fitting run. Earlier readiness-only status is historical.
