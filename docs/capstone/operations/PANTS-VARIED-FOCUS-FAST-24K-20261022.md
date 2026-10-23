# Varied lesion-focused views without losing coverage — faster input preparation

October 22, 2026. Engineering setup is approved; scientific training and scheduled
launches remain paused. This is the same proposed scientific experiment, not an
additional model comparison. The original
[scientific plan](PANTS-VARIED-FOCUS-24K-20261022.md) and JSON govern the hypothesis,
endpoints, guards and recipe. The adjacent FAST JSON adds engineering gates only.

**Current status: BLOCKED_NUMERICAL_EQUIVALENCE.** The full cache and input pilot
passed, but the33update GPU candidate failed final-state closeness despite exact
inputs. All workers are reaped. Cold restore/freeze/launch were NOT performed.
Do not execute the remaining handoff steps until a separately approved diagnostic
and reviewed qualification resolve this gate. Existing evidence/cache must be reused.

The subsequently approved original-loader repeatability control completed33updates
within600seconds and also exceeded the SAME numerical bound, with larger aggregate
weight drift than the earlier original-fast comparison. Baseline non-repeatability
is now demonstrated, but optimized-path equivalence is not certified. The failed
gate is preserved; a new deterministic paired qualification/cold check is recommended
for user approval. No data conversion/audit/pilot needs to be repeated.

## What will change

Relative to the completed pancreas-assisted run, focused training views vary around
components while preserving every patient's complete coverage bank. The frozen
24,000-update schedule contains 2,518 bank reservations, 15,482 component-focused
jitter views and 6,000 unchanged context views. Same 1,333 training / 70 development
cases, fresh SuPreM, augmentation, optimizer, resolution, pancreas assistance and
native validation every 2,000 updates. No EMA, PANORAMA, learning-rate change or
test-set evaluation.

Relative to the previously prepared sampler implementation, the only change is
equivalent input throughput: lossless training-target/metadata cache, pointwise CT
normalization after lossless region extraction, and one deterministic prefetched
window. No CT voxel cache, new interpolation, downsampling or random-view cache.
Validation uses the original reader and native reconstruction. One jitter window
need not contain every annotation; the retained reservation bank provides complete
annotated-field exposure across the schedule.

## Scientific decision

Primary control: completed parent selected 22k native positive-case macro Dice
0.35671408297710466. Terminal 24k control: 0.35432550042446787. H0 is selected
native Dice improvement <=0; reject only if the paired 95% interval lower bound
is >0. Practical adoption additionally requires >=0.02 improvement and every
predeclared detection, alarm, pancreas, empty-voxel and macro-voxel-recall guard.
The recall decrease may not exceed 0.03. Use the exact original JSON for all guard
definitions and tie/selection rules. A terminal improvement cannot replace a failed
primary endpoint. Historical native record 0.423761 and project target 0.50 are
separate milestones. This remains development-set research, not clinical validation.

## Evidence and limits

Evidence root: `E:/PROWL/readiness/region-throughput-20261022-a01`.
See [throughput evidence](PANTS-INPUT-THROUGHPUT-20261022.md) for the preserved
failed profiles, explicitly authorized correction, measurements and all-stage status.

- Twelve difficult training cases: original/candidate region images, targets,
  window traces and representative augmentation match exactly; all twelve PNGs
  were actually reviewed and individually hashed.
- Full 24k metadata-only replay: original patient order, exposure/focus counters,
  reservation/jitter/context counts and CPU model RNG match exactly.
- 121 training/input/launch regression tests and 19 existing monitor tests pass.
- Pilot region loading totals: 79.641 seconds original versus 20.187 seconds
  candidate (3.945x); this is not an end-to-end training speed claim.
- Full training-target conversion passed all1,333cases without exclusions.
- Paired CUDA inputs matched exactly, but final model/optimizer numerical state
  exceeded the frozen tolerance. Observed2.7823x update speedup is descriptive only.
  Cold qualification and readiness receipt remain blocked. Do not infer readiness
  from unit tests, fast timings or the executor's completed event alone.

Engineering updates are nonpromotable and excluded from scientific training hours.
Neither their loss nor their two-case native validation is a scientific Dice result.
No difficult case is excluded. Original cohort/audit evidence is reused, not rerun.
The original 503 parent and 515 prepared-successor producing pins remain immutable.

## Ordered handoff — no automatic retries

Inspect stage files, logs and owned processes before every action. A started or
failed stage must never be dispatched again without a separately approved remedy.
Use `.venv-prowl-windows/Scripts/python.exe` from the repository root.

1. Finish the existing `build_fast_varied_cache.py` process. Require all 1,333
   members, exact existing coverage-proof agreement, resource limits and reaping.
2. `scripts/diagnostics/qualify_fast_varied.py --prepare` once. This freezes a
   paired 32–40-update schedule ending on component jitter and qualification pins.
3. Run `--stage reference`, then `--stage producer`, then `--stage cold`, once each
   after prior success/reaping. Require exact actual batches/traces, close numerical
   state, independent checkpoint backup, exact cold restore/next input, clean
   shutdown and >=1.10x measured mean update speedup under the frozen timing rule.
4. Complete the evidence report and run
   `scripts/train_fast_varied_region.py --freeze`. The new receipt must say
   `READY_AWAITING_USER_LAUNCH`, not that training has started.
5. Return results to the user. Only a subsequent explicit training instruction
   permits `--launch-sha256 EXACT_READY_HASH --explicit-user-launch` on that same
   launcher. Never use an old launcher/receipt or automatically resume/retry.
6. After authorized launch, apply only the staged local dashboard configuration
   after checking its original hashes. Preserve all six prior runs, private access
   and journal-derived total hours. Verify actual advancing updates, independent
   initial backups, stored live MLflow loss metrics and phone API before reporting
   the scientific run live. Do not create or reactivate an AI schedule.

The intended scientific output remains
`E:/PROWL/artifacts/pants_varied_focus_24k_20261022` (one run). The launcher creates
the new human-named MLflow run only at explicit dispatch, with the completed parent
ID and frozen provenance. No model run or hours are invented during setup. Scientific
limits remain 96 hours including validation, 12 GiB owned RSS, 32 GiB combined cache,
100 GiB free floors on C:/E:, existing backup cap and AC power. If a gate fails,
preserve evidence and ask the user; do not lower the gate or expand the budget.
