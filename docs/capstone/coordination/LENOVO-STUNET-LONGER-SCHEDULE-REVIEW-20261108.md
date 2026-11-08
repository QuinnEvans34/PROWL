# Completed STU-Net review and longer-schedule planning — November 8

Analysis/planning only. The completed 12k run, its pins and earlier export remain unchanged. No continuation, fresh training, inference, threshold screen or new monitor is authorized by this report.

## What the completed run supports

The terminal/selected model reached positive-case macro lesion Dice **0.371633** at 12k, compared with .346184 at 10k and .347182 at 6k. Detection was 35/36 cases and 41/45 reference components; empty-reference alarms remained 27/34. Full 70-case results from all six validations are preserved in the adjacent completed metadata packet. Unknown pretraining exposure and supplied-pancreas scope remain explicit; final KD arm-bound reference matching remains unresolved.

Loss decreases across all six blocks, including the final blocks where view-kind proportions are unchanged. This makes another longer-schedule test reasonable, but does not establish that more updates will improve held-out Dice or reach .5. The 8k dip and persistent empty-case alarms argue against treating the endpoint as a guaranteed upward trend. Early loss changes are also confounded by the transition from coverage views to component-jitter views near 4k.

## Saved optimization records

Each row contains exactly 2,000 saved losses. Loss is a sampled training objective, not native validation Dice.

| Steps | Mean loss | Median loss | First LR | Last LR | Update path (h) | Native validation (h) |
| --- | --- | --- | --- | --- | --- | --- |
| 1-2000 | 0.923582 | 0.755445 | 2e-07 | 9.58605651e-05 | 3.292 | 1.539 |
| 2001-4000 | 0.709150 | 0.662408 | 9.58551216e-05 | 7.88340161e-05 | 3.357 | 1.543 |
| 4001-6000 | 0.674671 | 0.640576 | 7.8822856e-05 | 5.34121207e-05 | 3.317 | 1.543 |
| 6001-8000 | 0.633912 | 0.610474 | 5.33984933e-05 | 2.69967481e-05 | 3.344 | 1.543 |
| 8001-10000 | 0.607198 | 0.599592 | 2.69846213e-05 | 7.27902977e-06 | 3.336 | 1.540 |
| 10001-12000 | 0.590295 | 0.588634 | 7.27193432e-06 | 0 | 3.309 | 1.542 |

The 29.31-hour run comprises 19.96 hours on the update path, 9.25 hours inside six native validations, about 6.32 minutes of checkpoint work and about 6.94 seconds of remaining initialization/bookkeeping. Validation is approximately 31.6% of elapsed time; each full70 pass took about 92.5 minutes. Update-path time includes input loading/augmentation, forward/backward, optimizer and synchronization, not isolated GPU computation. Checkpoint event intervals include saving, copying and hashing. Native intervals include inputs, inference, scoring, report writes and report backup. No loader-versus-GPU bottleneck is isolated by these logs.

## Backbone, heads and supervision

The exact pinned Session constructor passes `self.model.parameters()` to AdamW with learning rate1e-4, weight decay1e-5 and foreach=False; update runs model.train(), deep supervision, loss.backward(), then checks every parameter for a present finite gradient before optimizer.step(). This is full-model fine-tuning, not head-only optimization. The transfer code copies all 58,157,984 body parameters and keeps 2,991 fresh head parameters. No per-parameter change or gradient magnitude is claimed from this review: checkpoint tensors were not loaded.

The combined loss is five-scale CE plus soft Dice, weights [16,8,4,2,1]/31. CE is mean over voxels for all three classes; soft Dice averages foreground classes pancreas/lesion with smoothing1e-5 and absent classes included. Lower-scale labels use nearest-neighbor interpolation. Only the combined scalar is saved. Per-scale losses, separate CE/Dice terms, per-class loss, head/backbone gradient norms and parameter deltas are absent. Lower-scale small-target loss is a plausible concern, not a measured cause of misses. The old helper docstring still says proposed; completed scientific qualification/receipt is the authority for the executed recipe. No source edits made.

## Actual exposure and coverage

All 1,333 training cases were visited: 671 lesion-positive and 662 empty cases. Per-case visits range7-16, median9; 6,043 updates used positive cases, 5,957 empty cases. Only 5,189/12,000 actual patches contained lesion voxels (43.24%); a positive source case does not guarantee a lesion-containing crop. This is recorded behavior, not evidence of an intake failure.

All 2,978 required unique coverage addresses appeared exactly as planned, plus 6,022 component-jitter and 3,000 context updates. These sum to12,000; the plan label focused_updates=9,000 includes coverage slots and must not be read as9,000 extra jitter updates. Component jitter on an empty case targets pancreas, not lesion. Every journal address/kind matches the frozen schedule and visit counts match final result.exposure. Qualified annotated-field coverage evidence is reused, not remeasured from masks; address coverage does not mean every crop contains the whole pancreas or every possible lesion view was learned. Per-case visit counts and histogram are included in the analysis JSON.

## Why a naive resume cannot work

The session learning-rate function only accepts zero-based indices0..11999: 500-update warmup then cosine decay to exactly zero on update12,000. The input loader requires exactly12,000 schedule entries and rejects index12,000. Its role contract is exactly1,333 training and70 development cases. The scientific worker initializes the pretrained-body/fresh-head model, creates a new output directory, and runs exactly12,000 iterations; it has no scientific-resume option. Cold restore is a diagnostic mode, with strict input identity, state version, membership, exposure sum and precision checks. Changing the schedule changes input identity. Bypassing these checks would invalidate the existing qualification.

Inputs remain128-cube windows/64-stride native reconstruction, FP32 batch1, inherited provided-pancreas regions and normalization, deterministic seed42, qualified physical-detail geometry, fixed role boundaries and source size cap256,000,000voxels. A longer schedule must preserve and explicitly rebind the intended input and coverage rules rather than taking modulo12k or silently replaying identical augmentation addresses.

## Two distinct future questions

1. **Fresh24k schedule:** restart from the original pretrained body and fresh heads, prospectively specify a24k sample plan and24k learning-rate horizon. This asks whether a longer planned schedule works better. A cosine horizon change also changes learning rates before12k, so it is a schedule-policy comparison, not a duration-only causal test. Evaluate matched reports and keep all cases; do not compare only each run best score without noting selection opportunities.
2. **New warm-restart continuation:** initialize from the completed selected/terminal12k checkpoint and train an additional12k. Predeclare reset versus retained optimizer moments, new LR/warmup/decay, sampler/RNG/address policy, checkpoint lineage and cumulative update numbering. This asks whether additional adaptation under a new schedule helps; it is not uninterrupted24k training. Restoring the old terminal LR unchanged supplies no useful learning, and current code will reject the next step.

My recommendation is to keep a longer-schedule experiment as a candidate, not automatically extend this run. If cost favors an additional12k continuation, label it explicitly as a warm-restart experiment and preserve the completed12k baseline. If the central question is the effect of planning24k from initialization, use the fresh schedule. Neither route is evidence that the target Dice will be reached. CAP-EXP-020 remains a separate proposed inference-policy screen; this report neither replaces nor launches it.

## Runtime and authority

For another12k plus six full70 validations, observed update/validation/checkpoint timing gives **29.31 hours**, or **35.17 hours with20% planning margin**. Repeating the slowest observed2k block six times gives29.50 hours before margin. These are estimates for the same hardware, representation and checkpoint cadence, not measured future performance; setup and qualification are additional. A fresh24k with twelve validations is approximately **58.62 hours**, or **70.35 hours with20% margin**. It has essentially no safe slack under60hours. Changing validation frequency would change cost and selection opportunities and must be separately specified.

The existing60-hour cap applied only to the completed original12k run. Its unused hours do not authorize a successor, retry or extension. Either proposal needs explicit scientific approval, a new frozen hypothesis/recipe and time/storage/resource budget, separate additive code and artifact/MLflow identity, exact ancestry and input bindings, focused CPU tests, actual bounded GPU updates and independent-backup cold replay on the changed path, and a readiness review before launch. Reuse valid source identity/coverage evidence; no duplicate whole-dataset audit is implied. Existing checkpoints consume disk space, so any new backup budget must account for retained originals and free-space floors. No budget, source code or monitor was changed.

## Evidence and checks

The completed metadata packet uses the original prowl-stunet-saved-native-metadata-v1 shape and binds the completed journal, selected checkpoint/report and completion receipt. Original six native reports and their independent copies were compared; exact case sets and denominators preserved. Four inspected producer files match their recorded frozen hashes. All12k ordered journal entries, schedule addresses, exposure counts and required coverage addresses reconcile. The earlier interim export is unchanged. Derived timing partitions sum to recorded total elapsed time; no model or image data was loaded.
