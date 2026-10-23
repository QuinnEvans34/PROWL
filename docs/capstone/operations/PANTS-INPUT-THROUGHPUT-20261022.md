# Faster equivalent inputs before varied lesion-focused training

October 22: user approves the retrospective's setup recommendation. Scope is
engineering preparation and qualification, not scientific training or scheduling.
Preserve both frozen parent and successor producers; add separately versioned code
and evidence. No changes to model, sampling rules, 1333/70 cohorts, geometry,
augmentation, inference or twelve native validation opportunities. No test reads,
duplicate audit, repeated source-content audit, automatic failed-stage retry or
unapproved budget expansion. Historical failed profile remains preserved.

## Ordered gates

1. Verify no trainer is active, both pin sets unchanged, resources/AC available.
   Close the completed parent's backup journal tail with a recoverable copy and
   exact hash verification; do not alter the authoritative journal.
2. New bounded CPU profile attempt: explicit CUDA_VISIBLE_DEVICES=-1 (verified
   unavailable), six stratified training cases, no optimizer/inference. Reuse the
   prior measurement implementation, store in a new directory and preserve failure
   evidence. 600-second/12-GiB limit and owned worker cleanup.
3. Select an exact-equivalent performance design from measurements. Current cache
   occupies 22,926,366,182 bytes of the 34,359,738,368-byte cap; no raw full-cohort
   region cache fits. Prefer eliminating redundant work and bounded pipelining if
   measured lossless storage cannot fit. No eviction/deletion of existing evidence.
4. Add versioned implementation, role/integrity/boundary/equivalence/shutdown tests.
   Require identical sampled arrays and augmentation; deterministic patient order,
   sampling origins, counters and cold restoration. Measure sustained performance
   and combined resources. Any changed inference must pass equivalent native output.
5. Reuse the complete intake proof; perform only changed-path twelve-training-case
   sampler/input pilot, actual visual review, and bounded nonpromotable GPU/cold
   qualification. Freeze a new configuration/evidence receipt, with a separate
   launch gate requiring user review. Keep existing MLflow/dashboard integration;
   no scientific RUNNING record, fake Dice/hours, or active dashboard switch yet.

Failed quality/resource stages stop for diagnosis; do not weaken guards or silently
retry. Document outcomes here and in the living experiment notebook. The prepared
varied-focus scientific hypothesis and all endpoint thresholds remain unchanged.

## Measured design choice and intermediate results

The original profile's empty CUDA device mask failed its isolation guard. The new
v2 passed explicit `CUDA_VISIBLE_DEVICES=-1` isolation but failed a diagnostic input
report-path lookup before CT reads (14.047 seconds, workers reaped). The user then
explicitly authorized one corrected attempt. V3 passed all six stratified training
cases in 53.047 supervised seconds, peak owned RSS 2,072,047,616 bytes, workers
reaped. Old failures remain intact, not overwritten or treated as successful.

Across six cases, original region loading took 34.012 seconds in aggregate.
Nested profile categories included 12.02 seconds in mask decoding/validation,
4.92 seconds in component anchors, 4.82 seconds in region construction, and
7.49 seconds in CT get_fdata. These categories are not all disjoint. The selected
design caches the lossless native uint8 training targets and deterministic metadata,
not CTs or random views. It removes repeated full-mask conversion and geometry/
component work, normalizes the exact region after lossless cropping, and prepares
one next window in a bounded thread while the GPU runs. Pointwise float32 HU
clipping/normalization commutes exactly with cropping; this is tested numerically.
Validation still delegates to the original source reader and native reconstructor.

All twelve difficult pilot cases passed exact full-region image/target comparisons,
all scheduled focused windows, sampled context and representative augmentation.
Complete original banks are preserved, with 5–15 distinct jitter origins among
these cases. All twelve two-view, three-plane PNGs were actually inspected; factual
notes and hashes are in visual-review.json. Large/nonselected structures can still
cross an individual window edge; full-field coverage is a schedule property, not
a claim each jitter shows every annotation. Tiny annotations and acquisition noise
remain visible. This is not clinical adjudication of supplied masks.

Pilot supervised time 276.406 seconds, peak owned RSS 1,942,638,592 bytes, reaped;
24 CT reads for paired reader comparison, no source/duplicate audit replay or test
reads. The twelve derived target/metadata members occupy 377,127 bytes. Initial
unit-test fixture omitted `max_steps`; corrected before 47 passing pre-pilot tests.
The broader current suite passes 121 tests; 19 unchanged monitor tests pass.

Full 24k metadata-only sequence replay matches patient order, exposure/focus
counters and the 2,518/15,482/6,000 reservation/jitter/context mix exactly; CPU model
RNG is unchanged. No optimizer updates were made by that replay.

All 1,333 training target conversions completed: 1,321 new plus twelve reused pilot
members. Zero CT voxel reads, test reads or exclusions. Derived members occupy
30,781,377 bytes; supervised time 2,862.906 seconds, peak combined owned RSS
4,542,889,984 bytes, both workers reaped. Do not repeat this successful conversion
or edit its request-pinned producers. GPU qualification began only after cleanup.

The GPU qualification design in PANTS-VARIED-FOCUS-FAST-24K-20261022.json uses the
same frozen 32–40-update schedule on original and candidate paths, then one cold
replay of a jitter update, with two native development cases through the actual
candidate executor. These are nonpromotable engineering updates, excluded from
scientific hours. Require exact inputs/traces, close numerical state, clean shutdown,
independent backup, and >=1.10 measured mean update speedup after warmup and
checkpoint-boundary exclusions. No scientific model Dice is inferred from it.

The completed parent's journal backup now exactly matches its source; the former
prefix backup is preserved as history-pre-closeout-20261022.jsonl. Future launcher
copies the final journal after completion events. Parent and successor producing
pins remain intact. Staged dashboard handoff preserves six historical runs and
751,607.078 journal-derived seconds / 174,270 updates; the new run contributes no
hours before launch. Local API returned200. Live dashboard files were not changed.

## Final status: blocked on numerical equivalence, not ready for training

The frozen paired qualification chose 33 updates per path, ending on jitter.
Reference completed/reaped in325.125supervised seconds (peak RSS2,540,982,272bytes).
Candidate completed33updates and two native development cases, but then failed
the final state-closeness check. Its supervisor recorded exit1, successfalse,
424.296seconds, peak RSS2,336,419,840bytes and workers_reapedtrue. The executor's
internal completed event is NOT a qualification pass; the failed supervisor and
missing producer.json prevent cold-stage advancement and readiness freezing.

A subsequent CPU-only inspection of existing checkpoints/journals made zero model
updates or CT reads. `failure-review.json` binds the inspected artifacts by hash:

- All33actual image/target hashes, window/augmentation traces, patient order and
  learning rates match. Integer/scalar, saved CPU/CUDA RNG, exposure and focused
  counters also match.
- Final floating model/optimizer state does not meet the frozen rtol1.3e-6 and
  atol1e-5:2,561of14,102,876elements exceed the bound; max absolute difference
  0.0001224800944328308. The first raised tensor error was smaller and is NOT the
  global maximum. Loss first differs atstep2; maxlossdifference0.00005257129669.
- Descriptive mean update times under the frozen timing exclusions are
  8.370727seconds original versus3.008545candidate (2.782317x). Do not call this a
  qualified speedup or extrapolate it directly to full-cohort wall time.
- Both native development cases completed; their33update metrics are engineering
  artifacts, not scientific model results or training-hour credits.

The unchanged session isolates seeds and disables TF32 but does not explicitly
require deterministic CUDA algorithms. PyTorch documents that seeded execution
alone does not ensure deterministic operations; see
[PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html).
GPU numerical variation is therefore a hypothesis, NOT an established explanation
for this failure. Exact input equality is insufficient to waive the state gate.

No tolerance was loosened, no failed stage was rerun, and no cold restore, ready.json,
scientific output, new MLflow RUNNING record or dashboard switch occurred. All
original503/515pins and new request pins remain preserved. Heartbeat remains paused.

Proposed next check, requiring explicit approval: one33update unchanged-original
loader repeatability control on the same12training cases/frozen schedule, separate
output,600second/12GiB cap, no native inference or audit. Compare its final state
with the existing original reference to measure baseline run-to-run drift before
attributing the difference to the optimized loader. Preserve this failed gate even
if later evidence explains it; any amended qualification needs a new reviewed plan.

## Approved original-loader repeatability control — completed

The user approved the proposed single control. New runner
`scripts/diagnostics/control_original_repeatability.py` calls the exact frozen
`qualify_fast_varied.original_worker` function, redirecting only its output to
`original-repeatability-a01/`. Request pins bind the wrapper, seven passing tests,
prior schedule and checkpoints. No frozen producer was modified. The worker
performed exactly33nonpromotable updates, zero native evaluations, no audit/cache/
pilot repetition or test reads. Resource closeout:324.281seconds,2,539,991,040bytes
peak owned RSS, exit0, all workers reaped. The600second/12GiB bounds were respected.

All input hashes/traces, order, learning rates and original model identity match.
Saved RNG, integer/scalar states and exposure/focus counters match. Every comparison
below uses the same frozen rtol1.3e-6/atol1e-5 across14,102,876floating state elements.

| Saved-state comparison | Elements outside bound | Maximum absolute difference | Model-weight L2 difference |
| --- | ---: | ---: | ---: |
| Original reference vs original repeat | 5,889 | 0.00015291665 | 0.00300545 |
| Original reference vs fast candidate | 2,561 | 0.00012248009 | 0.00204479 |
| Original repeat vs fast candidate | 4,966 | 0.00015226379 | 0.00276112 |

Original repeat loss first differs atstep2, maximumlossdelta0.00009691715 (prior
original-fast maximum0.00005257130). The first two rows therefore show larger
original-repeat discrepancy by these aggregate measures. This is not a claim that
every model/optimizer element or statistic is better for the fast path; for example,
original-fast maximum optimizer-moment delta is larger than original-repeat's.

The new control recorded PyTorch2.11.0+cu128, CUDA12.8, cuDNNbenchmarkfalse,
cuDNNdeterministicfalse, deterministic_algorithmsfalse and no CUBLAS workspace
configuration. It did not change these flags. TF32 remains disabled inside the
unchanged numerical session. Actual baseline non-repeatability is established;
the precise nondeterministic kernel has not been isolated. See the installed-version
[PyTorch reproducibility guidance](https://docs.pytorch.org/docs/2.11/notes/randomness.html).

**Decision:** successful diagnostic, still NOT a passed launch qualification.
One added control is not a calibrated distribution or a new tolerance. The prior
failed stage stays failed; its output and all pins remain intact. No cold check,
ready.json, scientific output, new MLflow run, UI switch or scheduling change.

Recommended next step requires approval: a new, separately versioned matched
original/fast comparison with deterministic GPU algorithms enforced equally, then
an independent cold-restore check, retaining the original numerical bound. Existing
input/coverage/cache/pilot/native-path evidence is reusable. This recommendation is
not permission to edit frozen specifications or launch scientific training.
