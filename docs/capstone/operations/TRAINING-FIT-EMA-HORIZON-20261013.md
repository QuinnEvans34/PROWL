# Training fit first, then EMA and a longer horizon

Status: setup only; no diagnostic inference or new long training launched.
Authority: October13 user approved prioritizing the existing training-fit → EMA/longer-horizon
backlog over the newly suggested sampling experiment, and requested setup with MLflow logging.

## First diagnostic: do our completed models fit their own training scans?

Use the completed PanTS-only selected14k checkpoint and PANORAMA-added selected8k checkpoint.
This is inference on cases used in training, not another overfit experiment or optimizer run.
Keep both original training runs, their frozen files and checkpoints unchanged.

- Sample50 positive and50 reference-empty PanTS training studies, without replacement within
  class; Python Random seed20261013 on sorted IDs, positive bucket then empty bucket. Freeze
  the exact list before any predictions. Both models see the same100 cases; verify unchanged
  PanTS membership and target semantics. This class-stratified sample is not prevalence-estimating.
- Compare against existing native scores on the same retained70 development cases. Do not
  rescore development or read protected test cases. No source duplicate audit/cache rebuild.
- Use the existing native inverse transform, semantic label decoder and `native_metrics`;
  same provided-pancreas crop and argmax prediction, no postprocessing or threshold search.
  Load prepared CT tensors, then native training labels for scoring. No raw CT replay required.
- Report positive macro lesion Dice including zero-overlap cases, pancreas Dice, any-overlap
  detection, component counts, empty alarms, predicted volume and50mm3 alerts. Describe lesion
  Dice by native size band with actual counts; random sampling may yield small subgroups.
- Separate MLflow records: one FINISHED **setup** record explicitly marked not executed;
  on explicit diagnostic launch, two new **evaluation** records linked to the source model runs.
  Log progress during execution, train100 metrics, saved dev70 metrics, descriptive differences,
  request, per-case results and resource reports. Failures are FAILED, never scientific nulls.
  Private local SQLite tracking only; no CT/label/prediction-volume/checkpoint payload upload.
- Local per-case journal remains primary evidence. Tracking failure stops this diagnostic for
  reconciliation, with partial evidence preserved and no automatic retry. This is not yet the
  separate resilient training-time MLflow integration needed for a future long run.
- Existing CUDA lock, AC requirement,12GiB worker limit,100GiB C/E floors,1GiB report ceiling,
  maximum1hour per model, sequential workers, no automatic retries. Estimated20–30minutes total
  from the preceding70-case native evaluations; bounds are safety ceilings, not promised duration.

No accept/reject hypothesis: this is a descriptive diagnostic. A large training/development gap
would support investigating generalization. Poor training Dice would motivate optimization,
schedule, label/geometry and capacity questions. Neither observation uniquely identifies a cause;
memorizing a tiny sample never proved adequate capacity across the entire cohort. The old0.80/0.50
bands and0.474 test reference are historical heuristics, not validated decision thresholds here.
Training-minus-development differences compare different cases and are not paired causal effects.
PANORAMA training-fit is explicitly not measured by this first PanTS-only sample.

## Following experiment: EMA / longer horizon — design draft

Human-readable candidate: **Does weight averaging and a longer learning schedule improve the
PanTS reference without worsening lesion detection or empty-reference alarms?**

The current recommendation is the stronger PanTS-only recipe as the initial control, with the
same retained70 development comparison. Final source choice follows the diagnostic and user
agreement; this document is not approval to remove PANORAMA from a launched run.

Two distinct comparisons must be preserved:

1. EMA versus ordinary weights from the same training trajectory. Candidatealpha0.99, initialize
   EMA by copying current weights after500-update warmup, update thereafter; save/restore both
   states and update count. No change to ordinary optimizer updates. Compare at fixed checkpoints;
   define any separate EMA checkpoint selection before launch. No tuningalpha after seeing results.
2. Longer schedule: candidate72k updates, stretching cosine LR to72k, retain24/36/48/60/72k.
   Compare72k versus24k within that trajectory and report the existing24k-horizon baseline
   separately. A stretched schedule changes the first24k optimization history, so the old run
   is not a matched-prefix control. An alternative matched-prefix continuation requires its own
   explicitly defined nonzero LR tail; do not silently continue the near-zero old cosine endpoint.

Do not retroactively combine a better EMA checkpoint with a different raw selection opportunity.
Use native development Dice, detection, alarms and pancreas guardrails; no repeated official-test
curve. Freeze exact primary endpoint, practical gain, uncertainty and guardrails after diagnostic
review. One seed remains exploratory. Long-run training-time MLflow, EMA recovery tests, bounded
CUDA smoke, storage/checkpoint retention and an appropriate approved watchdog are still required.
At current throughput72k is roughly55–60hours, not a24hour job; no ceiling extension is made here.

## Backlog order

1. Training-fit diagnostic (setup now; explicit launch remains separate).
2. Decide and freeze EMA / longer-horizon comparison using its findings.
3. Revisit positive/empty sampling if supported; not the immediate next experiment.
4. Later: anisotropic organ-shaped inputs, surrounding-organ supervision, external-model error
   analysis and literature-derived presence-gate features. Pancreas-mask input is also later,
   not what the user meant by retaining mask supervision.

Historical notebook sources: EXP-34(training fit), EXP-32(EMA), EXP-33(schedule). The completed
models already used pancreas and lesion masks as targets; no unsupervised model is being repaired.

## Setup and launch interface

`scripts/diagnostics/setup_training_fit.py` creates an immutable request and MLflow setup receipt
under readiness alias `training-fit-20261013-a01`. It reads control records and hashes, not tensors.
`scripts/diagnostics/run_training_fit.py --request REQUEST --sha256 RECEIPT_HASH` is read-only
preflight. Adding `--launch` executes only the two training-fit evaluations, never optimization.
The worker path is a new training-role adapter; the historical development evaluator is unchanged.
Unit checks/preflight do not constitute real-GPU qualification or completed diagnostic results.
