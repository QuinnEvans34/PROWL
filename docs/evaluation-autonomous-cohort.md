# Fixed-cohort autonomous evaluation

Use `scripts/evaluate_autonomous_cohort.py` to predict, separately score saved native masks,
and compare two reports. It reuses the existing autonomous predictor, native scorer, summary
and owned-process watchdog. No optimizer or new crop policy is introduced.

## Prepare the private plan

Copy [the example](../configs/evaluation/autonomous-development.example.json) into a private output
folder; replace its placeholders with existing admitted cohort IDs, exact ordered membership, local
absolute paths and SHA256 pins. The example's single placeholder case is not an admitted cohort.
Keep all 75 development cases in the current evaluation plan, including the seven unresolved-unit
cases and the flagged anatomy/annotation concern on `PanTS_00001389`. Do not derive membership from
a directory glob. Cohort admission/role verification remains the existing cohort system's responsibility;
this command validates a supplied list and does not certify patient separation or test eligibility.

- `inference`: pinned inference-only localizer/segmenter bundles accepted by `cascade_models_v1`,
  the complete localizer recipe, patch/tensor shapes, device, region policy and sampling bound.
  Training checkpoints with optimizer state are not inference bundles.
- `limits`: per-case and total worker time, sampled owned-process RSS ceiling and output free-space
  floor. The example retains the previous 600s/12GiB per-case and 100GiB floor; choose a concrete
  whole-cohort time budget before running. The timer for new workers includes reuse/verification overhead; reuse checks still finish after that budget.
- Each case: CT path/hash, separately pinned pancreas/lesion reference paths/hashes, declared
  `reference_state` (`positive`, `reference_empty`, or `unknown`) and visible `flags`.
- `references.allow_unknown_units`: explicit scorer-only permission to assume mm for unknown-unit
  references on matching grids. Default example is false. This does **not** override CT units.
- Optional `spatial_units_review`: the existing CT-hash-bound source evidence review. Missing CT units
  remain a named prediction failure without this review. Never manufacture reviews from label masks.
- `limitations`: retained provenance, selection and source caveats to accompany the report.

The all-support policy remains default. `largest_component_26` is an opt-in experimental comparator.
Keep model-selection rules and CT/config settings fixed when comparing a control and challenger.
The segmenter's existing geometry recipe governs normalization, interpolation and 10mm margin.

## Run the three stages

From the repository root, after preparing `outputs/prowl/evaluation/plan.json`:

```sh
PROWL_EVAL_PLAN=outputs/prowl/evaluation/plan.json
PROWL_EVAL_PIN=$(shasum -a 256 "$PROWL_EVAL_PLAN" | awk '{print $1}')
.venv-prowl/bin/python scripts/evaluate_autonomous_cohort.py predict \
  --plan "$PROWL_EVAL_PLAN" --plan-sha256 "$PROWL_EVAL_PIN" \
  --output-dir outputs/prowl/evaluation/control
.venv-prowl/bin/python scripts/evaluate_autonomous_cohort.py score \
  --plan "$PROWL_EVAL_PLAN" --plan-sha256 "$PROWL_EVAL_PIN" \
  --journal outputs/prowl/evaluation/control/journal.jsonl \
  --report outputs/prowl/evaluation/control-report.json
```

Use the verified Python environment on Lenovo instead of the Mac venv path when appropriate.
Prediction executes sequential CT-only subprocesses. Only allowlisted CT/model/config fields enter
the worker request; case reference paths, flags and reference states do not. The existing worker's
file-access audit tripwire applies after model loading. This is not an OS isolation guarantee.
Mac MPS execution shares the existing nonblocking profile lock; it refuses a competing owned job.
CUDA execution must be scheduled on an available Lenovo GPU, preserving the active training run.

Each fresh case produces a request, inference log and native prediction/result files. `journal.jsonl`
accounts for every fixed case in order: `complete`, `reused`, `failed`, or `not_run_resource_limit`.
An ordinary case failure does not stop later cases. Resource ceilings leave remaining cases visible.
A manual interruption leaves a partial journal; the score stage rejects it rather than invent outcomes.
Outputs and reports never overwrite existing paths; there is no automatic retry or resume.

The score stage runs separately and opens references only after reading completed prediction receipts.
It rechecks CT/model/config identity and receipt/prediction pins, then calls `score_saved`. It retains
inference errors, worker failure receipts, case flags, scoring failures and resource observations.
Declared reference states are checked against scored masks. The summary reports positive lesion
Dice/recall, parenchyma and union Dice, empty-reference lesion volume, and full/scored/failure counts.
Empty-reference Dice and recall remain undefined; scored-only means do not assign zero to failures.

Compare independently saved control/challenger reports:

```sh
PROWL_BASE_PIN=$(shasum -a 256 outputs/prowl/evaluation/control-report.json | awk '{print $1}')
PROWL_CAND_PIN=$(shasum -a 256 outputs/prowl/evaluation/challenger-report.json | awk '{print $1}')
.venv-prowl/bin/python scripts/evaluate_autonomous_cohort.py compare \
  --baseline outputs/prowl/evaluation/control-report.json --baseline-sha256 "$PROWL_BASE_PIN" \
  --candidate outputs/prowl/evaluation/challenger-report.json --candidate-sha256 "$PROWL_CAND_PIN" \
  --report outputs/prowl/evaluation/comparison.json
```

Comparison requires the same ordered cohort, CT hashes and reference hashes/states. It reports paired
means on the same scored population, per-case metrics/deltas, positive gains/regressions/ties and all
unpaired failures. It does not enforce experimental causal comparability: review initializer, completed
updates, checkpoint-selection rule and intended config differences separately. Reference-crop diagnostics
remain a separate labeled path; this command never performs a reference-derived rescue.

## Reuse existing compatible outputs

An optional case-level `reuse` object names the original prediction directory, the SHA256 of its
`result.json`, and its producing CT-only request:

```json
{
  "directory": "/absolute/private/original/case/prediction",
  "result_sha256": "REPLACE_WITH_SHA256",
  "request": {
    "path": "/absolute/private/original/case/request.json",
    "sha256": "REPLACE_WITH_SHA256"
  }
}
```

Reuse requires matching CT/model content identities, recipe, shapes, backend, region policy, allocation
settings and unit review. Original output location must match the producing request. Local CT/model
roots may differ; their hashes define identity. Completed native output and receipt pins are verified.
No model or original CT is opened during compatible reuse. Incompatible reuse becomes an explicit case
failure and never falls back to new inference. Historical outputs produced with different allocation
settings require their matching plan; do not silently combine them into a uniform-config evaluation.

## Verification and scope

October 9 focused verification: 24 tests passed (two existing upstream TorchScript deprecation warnings).
Checks use synthetic data only: actual tiny CT → cascade → native scoring,
reference absence during prediction, separate CLI processes, compatible reuse, nine incompatible/tampered
reuse conditions, failure continuation, resource accounting, duplicate MPS lock refusal, and paired
source/failure checks. Existing scorer/summary tests are included in the focused verification.
No real-cohort predictions, new scientific comparison, model training or Lenovo changes were launched
for this software task. Lesion component survival and crop coverage remain existing separate diagnostic
tools; they are not newly claimed as outputs of this command.
