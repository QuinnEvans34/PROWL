# PanTS lesion outlining with varied training views

**Owner:** Quinton Evans. **Specified:** October 17, 2026. **Experiment:** CAP-EXP-019, version 1.
**Status:** Scientific plan recorded; augmentation implementation and launch qualification pending.
The user requested this specification and repository synchronization, not a training launch.

The next experiment asks whether modest training-time augmentation improves lesion outlining at
the same 24,000-update budget. Keep the existing PanTS cases, whole-pancreas crops, masks, model
and optimization recipe. Change only the policy that varies each training view. This is a test of
the complete augmentation policy, not an attribution to any individual transform.

The machine-readable companion is [PANTS-AUGMENTED-VIEWS-24K-20261017.json](PANTS-AUGMENTED-VIEWS-24K-20261017.json).
Neither file is an executable training config or a launch receipt. Do not pass either to the legacy
trainer or silently add unused augmentation keys to `configs/level45.yaml`.

## Evidence and priority

The original PanTS-only 24k schedule selected its 14k checkpoint: native positive-case Dice
0.4050923173, detection 34/36 and empty-reference alarms 32/34 on the matched 70 development cases.
Adding expert PANORAMA positives produced 0.371897 and failed the alarm guardrail. Within the
longer-schedule run, ordinary native Dice fell from 0.312373 at 24k to 0.253297 at 72k. Selected EMA
at 8k reached 0.4066500385, but with 33/36 detections and 34/34 alarms; it was not promoted.

See the [mixed-data review](PANORAMA-POSITIVE-RESULTS-20261013.md),
[long-schedule review](PANTS-EMA-72K-RESULTS-20261016.md) and
[selected native review](PANTS-SELECTED-NATIVE-20261017.md). Falling training loss and declining
development Dice motivate regularization, but modest training-fit Dice leaves optimization,
supervision, resolution and capacity as competing explanations.

The current full trainer consumes fixed prepared tensors without random augmentation. Older course
augmentation settings are not connected to this route. SuPreM's official pancreas-tumor loader uses
rotations, flips and intensity/noise transforms; JHU's R-Super instructions also use augmented views.
Those recipes motivate this intervention, not a promised effect size or an exact recipe replication:
[SuPreM loader](https://github.com/MrGiovanni/SuPreM/blob/main/target_applications/pancreas_tumor_detection/dataset/dataloader.py),
[R-Super training](https://github.com/MrGiovanni/R-Super/blob/main/rsuper_train/README.md).

This plan takes priority over crop variation for the immediate provided-ROI Dice question.
[Crop variation](LENOVO-CROP-VARIATION-EXPERIMENT-HANDOFF.md) remains a separate proposed experiment
for imperfect automatic localization. Its different endpoint and expanded/off-center source crops
are not included here. Previous duration, EMA and PANORAMA verdicts remain unchanged.

## Question and hypotheses

Let Delta be treatment minus control mean native lesion Dice across all 36 positive development
cases, including misses and outside-crop reference lesions as zeros where appropriate. Each arm
uses the same prospectively fixed checkpoint-selection rule.

- **Null hypothesis H0:** Delta <= 0. This augmentation policy does not improve native lesion Dice.
- **Alternative H1:** Delta > 0. The varied training views improve native lesion Dice.
- **Practical hypothesis:** Delta >= 0.02 with positive paired uncertainty evidence and all critical
  detection, false-alarm and pancreas guardrails satisfied.

Mechanism: variation discourages reliance on a fixed orientation or appearance while preserving
whole-organ context and every labeled voxel. This mechanism is a hypothesis, not an established
diagnosis of the previous runs. A training-augmentation result does not revise the older negative
test-time-augmentation result; inference remains unaugmented.

## Control and fixed recipe

Use the original PanTS-only course-reference run as a retained control only after the changed-factor
audit below passes. Its 24k learning-rate horizon, not the later stretched 72k horizon, is the match.
Its saved metrics already select the same 14k checkpoint on the reduced development cohort.

| Factor | Both arms |
|---|---|
| Training cohort | Same ordered 1,333 PanTS cases: 671 positive, 662 reference-empty |
| Development | Same ordered 70 cases: 36 positive, 34 reference-empty |
| Initialization | Original SuPreM backbone, identical seed-42 fresh three-class head; no trained checkpoint initialization |
| Model | Existing SegResNet, init filters 16, GroupNorm, background/pancreas/lesion |
| Inputs | Existing qualified 144-cube cache; pancreas-only box with 10 mm margin; physical-RAS geometry v2 |
| Sampling and normalization | Existing 1 mm intermediate grid, fit-to-cube transform, HU [-100,250] mapped to [0,1] |
| Optimization | DiceFocal without background, gamma 2, equal Dice/focal weights; AdamW LR 0.0001, weight decay 0.00001 |
| Schedule | 500-update warmup, cosine horizon 24,000, exactly 24,000 updates; no encoder freeze |
| Exposure | Batch 1; existing seeded full-cohort permutations; no new positive/negative sampling |
| Numerics | Same Windows CUDA environment, float32, TF32 off; two Torch CPU threads |
| Selection | Ordinary weights only; complete dev70 tensor validation every 2,000 updates |
| Inference | Same native scorer and three-class argmax; no threshold search, cleanup, TTA or ensemble |

The five previously excluded uncertain development scans remain excluded and never enter training.
Original split files and all protected test roles stay unchanged. PANORAMA is not used. Reference-empty
does not mean independently verified healthy. Reuse the existing source/overlap decisions, cache and
mask qualification; no broad duplicate audit or CT preprocessing replay.

The original control evaluated 75 cases during training. Its saved scores were subsequently reduced
to the fixed 70 before this treatment existed. Verify that development forwards do not change the
optimizer, sampler or training RNG; retain this history as a disclosed evaluation-cohort amendment.

## Exact augmentation policy

Policy identity: `pants_cached_view_augmentation_v1`. Apply only to optimizer batches after verified
cache loading, using fresh arrays. Never rewrite a cache file, source image, mask or geometry record.

Apply in this order, with independently sampled decisions unless stated otherwise:

1. Flip each of the three spatial axes independently with probability 0.20. Apply the same flips
   to CT, target and valid-support mask.
2. With probability 0.20, rotate by a uniformly selected 1, 2 or 3 quarter-turns in the physical-RAS
   R/A plane (spatial axes 0 and 1). Apply to CT, target and support together. These are exact array
   permutations, not interpolated resampling.
3. With probability 0.15, multiply valid CT intensities by a scalar drawn uniformly from [0.90,1.10].
4. With probability 0.15, add a scalar drawn uniformly from [-0.10,0.10] to valid CT intensities.
5. With probability 0.20, add independent zero-mean Gaussian noise, standard deviation 0.01 in
   normalized intensity units, to valid CT voxels. Then clip valid intensities to [0,1].

Valid support is the unpadded rectangular region derived from the cached transform's `pad_low` and
`normalized_shape`, transformed alongside the arrays. It is NOT a pancreas/lesion mask and must not
be inferred from nonzero image intensity. Keep padding exactly zero; valid low-HU zero-valued voxels
remain eligible for augmentation. Targets stay integer 0/1/2, with exactly preserved class counts
and component topology under the spatial permutations. Masks remain supervision, never model inputs.

Use a dedicated stateless NumPy PCG64 generator, seeded from the first eight SHA256 bytes interpreted
little-endian of the UTF-8 string `pants_cached_view_augmentation_v1:{seed}:{update}:{case_id}`.
`update` is the one-based optimizer update being attempted. Pin NumPy in the launch environment.
Do not consume model/dropout, case-permutation or evaluation RNG to choose transforms. Record the
seed, sampled parameters and transformed array hashes with every update. Replaying a resumed update
must reproduce the same view and next optimizer state within the frozen numerical tolerance.

No blur, elastic deformation, arbitrary-angle rotation, translations, crop expansion, new patch
sampling or synthetic lesions. No EMA in this comparison. This is a modest policy motivated by the
old course settings and published recipes, not a claim that its probabilities are optimal.

## Selection and evaluation

Each completed arm has exactly 12 selection opportunities: updates 2k through 24k. Select the
highest mean positive-case tensor Dice, including zero-overlap cases; choose the earliest step on
an exact tie. Freeze this rule before training. No native-Dice reselection across checkpoints.

The primary comparison is selected-best versus selected-best, scored natively on the identical 70
cases with the existing provided-pancreas evaluator. Final24k versus final24k is mandatory secondary
reporting, never a fallback route to acceptance. Record the complete tensor curve and evaluate the
treatment's selected and terminal checkpoints natively after training; reuse valid retained control
reports. Failed/missing cases block a complete comparison rather than disappearing from the mean.

Use 10,000 paired patient bootstrap draws, seed 20261017, percentile 95% interval, deterministic
case-ID ordering. Use the same reference membership in each pair. The interval is conditional on
the selected models and reused development sample; it does not capture training-seed variability or
remove selection optimism. This is a controlled development intervention if compatibility passes,
not a confirmatory generalization study.

Critical point-estimate guardrails relative to the selected control:

- Positive-case any-overlap detection delta >= -0.03.
- Reference-empty any-lesion alarm-rate delta <= +0.03.
- All-case pancreas macro Dice delta >= -0.02.
- Total predicted lesion voxel burden on the same 34 empty references must not exceed control.
  This new burden guardrail prevents a numerical Dice win from hiding much larger false outputs;
  the retained control total is **205,564 voxels**, bound to the report checksum in the JSON plan.
  Verify this same baseline when freezing the launch receipt.

The last guardrail uses voxel counts to avoid turning the unresolved source-unit assumption into a
new physical-volume assertion. Also report the prior affine-derived mL values and >=50 mm3 alert
counts with their existing unit caveat, reference components, per-case gains/losses, and size bands.
Do not silently change spatial-unit interpretation or drop cases during this comparison. Small-lesion
results currently involve only five cases and are descriptive. These are operational point guardrails,
not statistical noninferiority or proof of clinically acceptable false alarms.

### Decision rules

- **Accept the practical intervention:** valid completed experiment, Delta >= 0.02, Dice interval
  lower bound > 0, and every critical guardrail passes.
- **Reject the practical intervention:** valid completed experiment with any guardrail failure,
  or Dice interval upper bound < 0.02.
- **Inconclusive:** other valid completed outcomes; do not automatically extend training or add seeds.
- **Invalid:** cohort/reference leakage, unaccounted numerical changes or corrupt scientific identity.
- **Operationally failed or canceled:** interruption or resource failure before the valid endpoint;
  not evidence against the scientific hypothesis.

Separately report H0 as rejected when the Dice interval lower bound > 0; otherwise report not
rejected. Never write "accepted H0." A positive Dice effect can coexist with a practical rejection
because of false alarms. Record both decisions rather than conflating them.

For orientation, +0.02 over retained control Dice 0.4050923173 means at least 0.4250923173. The
current descriptive record is 0.4066500385 from selected EMA8k. Exceeding that record alone does
not meet acceptance. Historical course/test scores and withdrawn contaminated scores are not
comparable targets. No model promotion without separate autonomous and release qualification.

## Implementation and pickup checklist

1. Read this plan, its JSON companion and the [integration record](WINDOWS-MAC-INTEGRATION-20261017.md).
   Confirm there is no active GPU worker and use `.venv-prowl-windows`; do not reinstall dependencies.
2. Bind the original control config/initialization, matched70 membership, saved per-case metrics,
   cache metadata and environment. Generate a changed-factor audit. The merge changed geometry
   capabilities but kept default training geometry; require old/new synthetic equality and compatible
   retained-cache metadata. Do not rewrite old receipts to pretend their code pins still match.
3. Implement an additive versioned augmented session on the current full trainer, with explicit
   configuration validation and checkpoint identity. Preserve the ordinary no-augmentation session's
   numerical behavior. Wire the real executor/launcher; the old `augment` YAML section is insufficient.
4. Add tests for image/target/support alignment, padding, target survival, intensity bounds, train-only
   application, deterministic view keys, unchanged sampling/model RNG, no-augmentation parity, and
   exact checkpoint restore plus the next update. Keep scientific evaluation unaugmented.
5. Prepare a new local resolved config, full provenance audit and resource request using the existing
   cache. A different environment or unexplained producing change blocks retained-control reuse.
   If a fresh control is needed, report the reason and extra compute to Quinton before launching it.
6. After setup authorization, qualify at most four real-CUDA producer updates and one cold next-update
   replay, with independent backup verification and one positive/one empty native evaluation. These
   are nonpromotable engineering checks. Log the attempt in the notebook; no two-scan overfit rerun.
7. Freeze a new receipt containing this plan/JSON hashes, resolved config, source and environment
   identities, cohort/cache/initialization pins, control reports, guardrail baseline and qualification.
   Read-only preflight must pass before asking for the separate scientific launch instruction.

The specification's portable consistency checks can be rerun now from the repository root:

```powershell
& ./.venv-prowl-windows/Scripts/python.exe -m pytest tests/test_pants_augmentation_plan.py -q
```

These validate the plan, not an augmentation implementation or launch readiness.

Planned output stem: `pants_only_augmented_views_24k_win_20261017`, reserved only at setup.
Readiness belongs under `E:/PROWL/readiness/`; artifacts under `E:/PROWL/artifacts/`; independent
backup under `C:/Users/quinn/PROWL-Backups/`. Existing runs and read-only dashboard services remain
untouched. Do not run `setup_pants_ema_72k.py` or replay an old launch receipt for this experiment.

## Runtime logging and retention

Expect roughly one day of training based on the prior 18-hour PanTS run, with augmentation overhead
measured during qualification. Proposed hard ceiling: 30 hours, 24k updates, 12 GiB worker RSS,
32 GiB existing aggregate cache cap, 100 GiB free floors on C/E and the existing 27,917,287,424-byte
aggregate backup cap. Check actual remaining backup capacity before admission; never delete prior
evidence automatically. Require AC, CUDA lock, process-tree supervision and independent checkpoint
readback. Stop on nonfinite state, identity/target mismatch, storage/power/resource fault or user stop.
No score-based early stopping, automatic retry/resume, horizon extension, schedule or successor launch.

Keep initial/latest/selected/8k/24k checkpoints, checkpoint every500 updates, with model, optimizer,
step, RNG, exposure and augmentation identity. The local journal records every update. Live local
MLflow records loss/LR/elapsed at step1 and every25, dev70 tensor curves, native selected/final metrics,
the human-readable title, policy, parent/control links, resolved spec hashes and final decision.
Training and setup records must be distinguishable; do not create a fake running training record
merely to store this plan. A tracking failure is journaled and can be backfilled; a model/data or
checkpoint failure stops execution. Do not upload CTs, masks, predictions or checkpoint payloads.

After completion, append outcomes and deviations here and in `docs/experiments.md`, retain the full
paired comparison, and discuss the next intervention before launching it. Every failure and null stays
in the record. This specification contains no result and does not authorize an automatic experiment queue.
