# Pancreas-assisted complete coverage: results and runtime review

Reviewed October 22, 2026. This is a retrospective and a proposed next-step plan,
not a new launch, changed receipt, MLflow write, or resumed schedule.

## Outcome

**Pancreas-assisted lesion outlining with complete coverage and interleaved views**
completed all 24,000 contiguous optimizer updates and twelve complete 70-case
native-resolution evaluations. Selected checkpoint: 22,000 updates. Terminal
checkpoint: 24,000 updates. Workers were reaped. Local MLflow run
`1edf56ad4b7b48a5a5baa0e729e46a5c` is FINISHED; read-only SQLite inspection verified
961 stored train/loss points through 24,000 and twelve native metric points through
24,000. No model was trained or evaluated again for this retrospective.

Primary control is the selected 18k checkpoint from **PanTS lesion outlining with
varied training views**, evaluated on the same 70 native cases. The older .45 value
is not substituted for this matched native comparison.

| Selected native endpoint | Augmented control | Complete-coverage region run |
| --- | ---: | ---: |
| Positive-case macro lesion Dice, 36 cases | .423761 | .356714 |
| Pancreas Dice, all 70 cases | .811406 | .772710 |
| Positive cases with any lesion overlap | 33/36 | 32/36 |
| Empty cases with any predicted lesion | 27/34 | 34/34 |
| Total predicted lesion voxels in empty cases | 100,767 | 136,506 |
| Total predicted lesion volume in empty cases | 59.080 mL | 118.944 mL |
| Positive-case macro lesion voxel recall | .484432 | .435074 |
| Detected annotated components | 36/45 | 38/45 |

Any-overlap detection and any-voxel alarms are permissive technical endpoints,
not clinical sensitivity/specificity at an actionable lesion threshold. Native
voxel volumes vary by case, so aggregate voxel counts and mL need not change by
the same percentage.

### Hypothesis decisions

Preregistered H0: selected native positive-case macro Dice improvement is <=0.
Observed delta **-.067047**, paired 95% bootstrap interval
**[-.124709, -.014553]** (10,000 patient resamples, seed 20261019).

- Statistical decision: **fail to reject H0 of no improvement**. This is not
  proof that H0 is true; the interval here points toward deterioration.
- Practical intervention decision: **reject**. The required +.02 improvement
  was not met. Alarm, pancreas-Dice and empty-voxel-burden guards failed; the
  detection-fraction guard passed (one fewer detected case is within .03).
- Mandatory terminal comparison: .393723 -> .354326, delta -.039397,
  interval [-.092790, .013437]. Again fail to reject H0; practical rejection.
  This secondary result does not replace the primary endpoint.

The existing full-coverage engineering qualification remains valid. We reject
adoption of this bundled learning intervention as an improvement, not the need
to preserve annotations or the demonstrated coverage correctness. These are
different questions.

### What the model learned, and what remains uncertain

Native Dice progressed .0573 at 2k, .2175 at 6k, .3051 at 14k, .3490 at 20k,
.3567 at 22k, and .3543 at 24k. This was learning, not a stalled optimizer. It
does not establish that another longer horizon would help.

Among positive cases, 15 improved, 19 worsened and two were unchanged. Descriptive
size-band Dice: large (7 cases) .3346 -> .3563; medium (24) .4884 -> .3970;
small (5) .2384 -> .1639. More components were detected, but aggregate contours,
voxel recall and false-positive behavior worsened. These small subgroups do not
establish a causal mechanism.

Coverage, physical representation, anatomical context per window, sampling and
inference all differ from the old augmented pipeline. The old selection used
tensor validation and the new selection uses native validation. This is a
bundled exploratory comparison on a repeatedly reused development cohort and
one seed. The interval is conditional on selected checkpoints, not a correction
for checkpoint selection or a claim about clinical/general external performance.

## Why 24k took much longer

| Journal-derived time | Augmented control | Complete-coverage region run |
| --- | ---: | ---: |
| Total including recorded validation | 21.281 h | 72.117 h |
| Outside recorded validation | 20.776 h | 59.411 h |
| Recorded validation, including post-training endpoints | .505 h | 12.707 h |
| Mean ordinary update interval, excluding 500-step boundaries | 3.113 s | 8.903 s |
| Median ordinary update interval | 3.156 s | 7.812 s |
| 95th percentile ordinary update interval | 3.235 s | 15.742 s |

Total is 3.39 times longer, an additional 50.84 hours. Approximately 38.63 of
those extra hours (76%) are outside validation; 12.20 hours (24%) are validation.
"Outside validation" includes input IO/transforms, GPU forward/backward, logging,
checkpointing and supervision. It must not be labeled GPU-compute time alone.

### Confirmed implementation differences

1. The old provider read an already-prepared 144-cubed tensor from its small
   cache. The current `RegionInputs.load` calls `NativeInputs.load` every update:
   reopen source CT/masks, load the full CT array, normalize/orient the full
   volume, validate labels and compute component/coverage information, then
   crop the pancreas region and extract the actual 144-cubed window. There is
   no persistent image cache and the batch-loading path is synchronous.
2. Some native-loader component/coverage work is not used by the region sampler,
   which computes its own union-annotation bank. This is an optimization
   candidate, not permission to remove provenance or quality guards.
3. Current validation predicts 2,600 windows per 70-case evaluation, twelve times
   (31,200 windows total). Its mean duration is 63.53 minutes. The old in-training
   validation predicted one prepared cube per patient, with two inexpensive
   native endpoint reconstructions after training. Current native inference
   samples, forwards, transfers predictions back and reconstructs windows
   sequentially. This is genuinely more evaluation work.
4. The network still receives 144-cubed inputs and uses the same architecture
   and precision. We did not triple network size. Across successive 2k blocks,
   median regular intervals stayed between 7.625 and 8.000 seconds: no journal
   evidence of a progressive stall. Historical thermal/GPU-utilization telemetry
   is unavailable, so this does not prove absence of thermal limits.

Metadata-only analysis of all 1,333 training cases found Pearson correlation
**.955672** between source voxel count and each case's mean regular update
interval, versus .757490 for retained-region voxel count. Source voxel count was
recovered as retained-region voxel count / saved `region_fraction`. This supports
source-volume work as a major avoidable cost, without partitioning IO, CPU and GPU
seconds. No CT contents were read for this calculation.

A bounded six-case CPU profile was attempted but **failed before reading any CT**:
the CPU-only guard still observed CUDA availability despite an empty device-mask
environment variable. It was not retried and produced no timings. Its supervisor
reports workers reaped, 46.453 seconds and 821,841,920 bytes peak owned RSS. Preserve
`profile.log` and `profile-resources.json`; do not call this a passing microbenchmark.

## Recommended next setup — proposal, not implementation

Keep **Varied lesion-focused views without losing coverage** as the next scientific
test. Its fixed patient order and global 3:1 focus/context mix reserve 2,518 updates
for complete pancreas/lesion coverage banks, use 15,482 component-jittered focused
views, and retain 6,000 unchanged context views. Keep fresh SuPreM, PanTS-only,
24k horizon, LR, loss, augmentation, physical geometry and inference unchanged.
The focused-view hypothesis is plausible, not proven by this retrospective.

Use the completed parent selected .356714 and terminal .354326 as controls.
The +.02 practical improvement threshold is .376714 selected Dice, alongside
CI/guards, including the already specified voxel-recall guard. Passing that test
would not automatically beat the historical matched-native record .423761 or
meet the project target .50. The parent already alarms on all 34 empty cases,
so that binary guard is saturated: report continuous false-positive burden and
larger-volume alert counts, without changing preregistered acceptance post hoc.

Before spending another approximately three days, recommend a separately approved
**input-throughput engineering pass**:

1. Preserve the current run and all 503/515 parent/successor pins. Record a new
   additive performance candidate and evidence revision; do not silently patch
   the frozen sampler, overwrite setup, or treat old qualification as covering
   new code. No repeat duplicate or full source-content audit is needed.
2. Correct the diagnostic-only CPU isolation guard in a new attempt/version and
   measure a bounded representative loader profile. Precompute immutable region,
   geometry, coverage-bank and component metadata with source-bound identities;
   investigate removing redundant full-volume work from the hot path.
3. Evaluate lossless native-region/chunked storage and bounded prefetch. A raw
   float32 CT plus uint8 target for training alone projects to **70.696 GiB**;
   all 1,403 cases project to 74.695 GiB, before metadata/other masks. That exceeds
   the current 32 GiB cap. Measure a lossless layout and total occupied cache
   first; otherwise explicitly request a budget change. No unapproved dense
   cache, lower-resolution squeeze, or tiny-LRU speedup promise. Patients recur
   only after a full shuffled cohort traversal, so a tiny case LRU is unlikely
   to help much.
4. Require identical sampled CT/target arrays, origins, augmentation, order and
   exposure/counter state; preserve full coverage and role boundaries. Qualify
   cold restoration and numerical model-update agreement. For inference changes,
   also require gap-free native reconstruction and numerical output agreement.
   Keep native validation every 2k for the controlled sampling test: reducing
   frequency would change selection opportunities and save at most a minority
   of the observed excess runtime.
5. Measure sustained throughput, peak combined RSS/GPU memory, disk footprint
   and native validation costs before predicting a 24k runtime. Only then freeze
   a new receipt and perform the existing changed-sampler pilot, visual review,
   bounded CUDA/cold-restore qualification and explicitly directed launch.

Caching deterministic preprocessing before random augmentation is consistent
with the [official MONAI acceleration guide](https://github.com/Project-MONAI/tutorials/blob/main/acceleration/fast_model_training_guide.md).
The [NiBabel memory guide](https://nipy.org/nibabel/images_and_memory.html) explains
the proxy/get_fdata behavior; turning on image-object caching alone would not
solve our recreation/discarding of those objects each visit. Bounded asynchronous
loading is a candidate from the [PyTorch performance guide](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html),
not a measured speedup for this Windows process/memory budget.

No lower LR, EMA, PANORAMA, distillation, horizon extension or reduced validation
is bundled into this proposed sampling test. The scheduled handoff remains paused.
The latest user request is review and planning; no successor stage was dispatched.

## Integrity and closeout evidence

- Retrospective JSON: `E:/PROWL/readiness/pancreas-region-review-20261022-a01/results.json`.
  Produced by `scripts/diagnostics/review_region_results_timing.py`, whose recorded
  SHA256 is `d89983f79632a3aed5017bb47fdbe438321b919704bca915c325338d6b547419`.
  Three focused review tests passed. Review optimizer updates/inference/CT reads: zero.
- All 503 parent and 515 successor producing-file hashes matched. All 15 parent
  checkpoint copies and native reports matched independent C: backups.
- Small closeout issue: the backed-up journal is an exact byte prefix of the
  authoritative E: journal but lacks the final three completion events:
  `native_completed`, `training_completed`, `completed`. Final native reports
  and all model checkpoints are intact. This was documented, not silently
  repaired. Copy/verify the final journal as approved housekeeping before handoff;
  a future additive launcher should copy it after completion events are written.
- Authoritative final journal SHA256:
  `5dc520f5b31fe8b21498db71f6aacc707d7c02075f7dee884f5c54d57b5c6f01`.
- Selected native report SHA256:
  `1fb54ae0642147b7f1dee7a8d1bdafb9f4dcffae409e5e023682b1786e5f9e7d`.
- Terminal native report SHA256:
  `4af7b5abb9e20ca9ed55e81c7c6907e1c2154e45463a5efe9001f9f671a7d088`.
- Existing parent receipt, successor setup, scientific sources/configuration,
  dashboard, MLflow records, datasets and protected test roles were not changed.
