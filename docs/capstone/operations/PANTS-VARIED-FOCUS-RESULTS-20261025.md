# Varied lesion-focused views without losing coverage — completed results

Reviewed October25,2026. All24000updates and twelve complete70case native
validations finished normally; best checkpoint is terminal24000. All3275producing
pins and independent checkpoint/report/journal/result backups match. Workers
reaped; live process IDs absent; GPU idle. MLflow a84c0a6ae0cb424ca182350425adc7aa
is FINISHED with961stored train/loss points before retrospective logging.

Evidence: E:/PROWL/readiness/varied-focus-review-20261025-a01/results.json.
Four retrospective tests pass. An initial report helper used the superseded
parent-binding directory and failed before report creation; failure retained at
varied-focus-review-20261025-attempt01-failure.json. Corrected only the new unfrozen
report helper to read the actual launched receipt's parent binding. No trainer
change, data audit, CT/mask read, inference, optimizer update or protected test read.

## Hypothesis and decision

Primary H0: selected positive-patient macro native Dice gain versus the completed
previous pancreas-region run is<=0. Paired10000patient bootstrap draws,
seed20261022, two-sided95% interval; conditional on selected checkpoints.

| Metric | Previous region run, selected22k | Varied views, selected24k |
|---|---:|---:|
| Positive native Dice |0.356714|0.396139|
| Positive patients with any overlap |32/36|34/36|
| Negative patients with any false prediction |34/34|33/34|
| Positive macro voxel recall |0.435074|0.533401|
| Negative predicted lesion voxels |136506|90374|
| Negative predicted lesion volume, total mL |118.944|65.450|
| All-case pancreas Dice |0.772710|0.775636|
| Detected reference components |38/45|38/45|

Primary Dice delta+0.039425,95%CI[+0.009929,+0.069369]. **Reject H0; accept the
sampling intervention under the preregistered practical criteria.** Gain exceeds
.02 and all five detection/alarm/pancreas/negative-voxel/positive-recall guards pass.
22positive patients improved,12worsened,2unchanged. Do not call this universally
better, independent generalization or clinically validated detection.

Mandatory terminal24k comparison: parent0.354326 versus0.396139,
delta+0.041814,CI[+0.012158,+0.071216]; reject H0 and practical accept, all guards
pass. This secondary result does not replace the primary comparison.

Historical matched70native record remains0.423761 at18k in the augmented-view
run. Current result is0.027622below that record and0.103861below project target.50.
The historical run is not the preregistered control; no new PR is claimed.

## What improved and what remains weak

Patient-size strata, descriptive: small5cases Dice.163917→.215314, medium24cases
.396999→.418825, large7cases.356305→.447520. Corresponding voxel recall improved
in every stratum. These are patient total-volume strata, not a small-component
guard. Component detection remains38/45; seven components are still missed.
False-positive volume fell about45%, but33/34negative patients still have some
prediction. Any-overlap detection and any-voxel alarms are permissive definitions;
neither establishes useful clinical sensitivity/specificity.

Actual sampler exposure:2518reserved-bank updates,15482component-jitter updates,
6000context updates. All7839positive component-jitter updates retained lesion
voxels after augmentation. Positive cases had86/1245reserved windows and1108/2997
context windows without lesions; this is compatible with whole-pancreas bank
coverage/context and is not itself a coverage failure. Complete-field admission
is separate. Best score occurred at the horizon, but this alone does not prove
that extending training will help; don't silently extend or resume this run.

This one-seed repeatedly reused development cohort supports an exploratory
strategy decision. Checkpoint selection is not accounted for by the conditional
paired interval. Pancreas masks assist inference; this is not autonomous fullCT
localization. Equivalent-fast input changes were separately qualified before launch.

## Runtime

| Journal-derived phase | Previous region run | Varied views |
|---|---:|---:|
| Total hours |72.117|35.031|
| Native validation hours |12.707|13.497|
| Outside recorded validation hours |59.411|21.534|
| Median regular update interval, seconds |7.812|2.656|

Total elapsed time fell51.4%, approximately2.06x faster. The cache/prefetch
improvement is consistent with most of the saving occurring outside validation;
these are descriptive timings, not an isolated hardware-controlled benchmark.
Validation now consumes38.5%of elapsed time. Do not reduce scientific evaluation
cadence opportunistically. Any validation speed optimization needs an additive
version and equivalent native outputs. Restricted-generator training deliberately
has no development-based checkpoint selection and therefore does not need this
12validation schedule, but its runtime still needs measurement.

## Next Windows run and gates

Continue the already approved plan: **Candidate generator with reserved verifier
patients**, then **Reject false alarms without losing small lesions**. The next
24k run is a prerequisite segmenter trained on800patients, not the verifier itself
and not a claim that fewer patients should beat0.3961. Keep the successful varied
views, freshSuPreM, inherited coverage geometry and fixedterminal24k selection.
Reserved266fit/67tune/200calibration remain excluded from generator optimization;
70dev remains excluded from selection. Inherited geometry is explicitly
design-informed/exploratory. Existing broad models cannot supply unseen-patient
generator predictions for these new reserved roles.

Completed: partition/schedule,12real input pilot and visual review,58CPUtests,
fixed-terminal executor, frozen CUDA qualification request. Do not repeat audits.
The current-run completion dependency is NOW satisfied. Required next:

1. Inspect the unchanged frozen request/process inventory; run the prepared five
   nonpromotable CUDA updates and one independent-backup cold replay, sequentially,
   under existing20min/12GiBper-stage limits. No automatic retry on failure.
2. Complete scientific supervisor/MLflow integration, final configuration and
   readiness receipt. Preserve all prior pins; additive implementation only.
3. Review exact run/budget and obtain scientific launch approval. Only on actual
   dispatch switch the existing phone dashboard and verify loss, backups and steps.
4. After generator completion, separately bound candidate inference over reserved
   patients, assess candidate availability, then train/calibrate the verifier.

Mac knowledge distillation remains a separate route to better outlines. This
retrospective did not verify its latest external progress. The Windows upstream
teacher reference remains blocked by timm0.6.12/Python3.12 import compatibility;
that is NOT a blocker for the SuPreM verifier-generator experiment. Do not delay
or silently substitute one experiment for the other. No new run started in this
review and no schedules were enabled.
