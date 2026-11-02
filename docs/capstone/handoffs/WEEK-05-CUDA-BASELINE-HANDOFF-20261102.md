# Week 5 CUDA laptop handoff — autonomous baseline

Owner: Plan capstone experiment workflow, Windows CUDA laptop.
Prepared November 2, 2026. Board tasks W05-01, W05-05 and W05-09.

## Objective and scope

Prepare the existing CT-only pancreas-localization cascade for a bounded CUDA
baseline evaluation while the Mac continues its frozen KD treatment. Return a
concrete readiness report and executable commands. This handoff authorizes inspection,
CPU preparation and additive implementation/tests; it does not authorize interrupting
the verifier, launching another training experiment, or opening protected test cases.
Real GPU evaluation requires a completed, frozen packet with the gates below met
and an explicit dispatch decision. Do not infer that the Mac's KD launch authority
also authorizes a new Windows experiment.

Success is an eligible, reproducible full-CT → predicted-region → segmentation →
native-output path with honest failure accounting. A good Dice score is not promised.
Do not rebuild the existing pipeline or create a new planning/tooling framework.

## First: inspect ownership and current work

1. Inspect the existing verifier journal, result, supervisor/worker ownership,
   checkpoint backups and MLflow state. The last chat record reports a successful
   launcher exit after the November2 launch; that alone does not establish complete
   evaluation, cleanup or a free GPU. Preserve all producing pins and attempts.
2. Check AC, mounted data/checkpoint volumes, current free storage, RAM/VRAM and
   accelerator lock. Use this laptop's applicable resource gates; do not copy the
   Mac's storage thresholds or waive existing gates. Do not kill unrelated workers.
3. Record the checkout SHA and dirty state. Read this pushed document without
   switching, merging or pulling over files pinned by a live process. If needed,
   inspect the remote commit in isolation until that process has finished.

## Evidence and existing implementation to reuse

Read these repository files before choosing a change:

- docs/capstone/weeks/WEEK-05-WORK-PLAN.md
- docs/capstone/imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md
- docs/capstone/operations/CAP-EXP-012-RESULTS-2026-10-01.md
- docs/capstone/imaging/PREDICTED-ROI-ADAPTER-CONTRACT-V1.md
- docs/capstone/evaluation/PREDICTION-SETS-AND-HOLDOUTS.md
- docs/capstone/evaluation/METRIC-SPECIFICATION.md
- scripts/predict_autonomous_ct.py and scripts/evaluate_autonomous_cohort.py
- src/inference/cascade_models_v1.py, autonomous_cascade_v1.py,
  localizer_region_selection.py, fixed_cohort_evaluation.py and saved_prediction_scoring.py

The trained binary localizer is CAP-EXP-012 child step300 (absolute600), with
113 training/40 development cases. It already ran through CT-only inference.
Original40-case mean recall0.962519, Dice0.129078, median mask/reference volume
14.2596x, joint ROI screen15/40: available candidate, not accepted precise localization.
October9 largest-component cascade evaluation completed68 development cases;
seven unresolved-unit cases remain visible in the original75-case denominator.
Those results used an older segmenter and are neither current KD outcomes nor
fresh independent evaluation. No threshold/margin selection on final test data.

## Artifact inventory and transfer request

The Mac has these private, ignored files under
outputs/prowl/autonomous-real-ct-20261009/:

| Artifact | Purpose |
| --- | --- |
| localizer.pt | Inference-only localizer weights, 18,830,236 bytes |
| checkpoint-review.json | Checkpoint ancestry and training-membership review |
| request-a02.json | Historical request/recipe example; do not replay its paths/output |

Verified localizer.pt SHA256:
46417801f3d3c37e618d06823027e84f0ce84343f469f24124537167d40198d5.
These files are not included in Git. First inventory whether exact matching artifacts
already exist on Windows. Return a minimal missing-file list, destination and hashes;
do not assume this Markdown push transfers weights. Use an approved private transfer
route and verify bytes before loading. No credentials, raw images or weights in Git.
Reuse locally matching CT files by hash instead of transferring the entire dataset.

The proposed current segmenter is the completed Mac control's preselected20k checkpoint,
subject to eligibility and compatibility review. Locate its exact checkpoint hash,
recipe, class mapping, ancestry and selection record before requesting/exporting it.
Do not guess its filename or substitute a better-scoring laptop checkpoint. If it is
missing, report the dependency; do not block CPU preparation on the transfer.

## Critical compatibility check

The old cascade resizes a predicted region to one144³ tensor and performs one
segmenter forward. The current control uses a physical-window training/evaluation
path. Strict weight loading alone does NOT establish compatible inference geometry.
Compare HU normalization, spacing, window size/stride, padding, class codes, native
reconstruction and ROI margins against the actual frozen current-control recipe.
List every difference. Reuse its qualified native-window executor where appropriate;
make an additive adapter rather than editing a producing module or silently using
the old resize path. A changed inference recipe must have its own identity and
qualification. Preserve old reproduction evidence as a separate diagnostic.

The inference-only loader currently requires prowl-cascade-weights-1 with exact
role/architecture/source-checkpoint hash/state_dict, finite float32 tensors and strict
loading. Export only after verified checkpoint provenance, using safe loading; do
not bypass the format gate or use unsafe pickle fallback.

## CPU preparation and tests

Produce a small manifest recording code/environment, weight and recipe hashes,
eligible case IDs and roles, CT identities, output root, policy and resource budget.
Review localizer and segmenter ancestors' training/selection overlap with the chosen
cohort. Distinguish study-ID disjointness from biological patient separation and
unknown pretrained membership. Exposed development cases remain development cases.

Prediction must receive only CT plus frozen model/configuration inputs. References
belong in a separate scoring process. Do not use a pancreas/lesion label to choose,
repair or expand an autonomous crop. Keep provided-region diagnostics explicitly
separate and matched on segmenter, case set and other inference settings.

Run affected CPU tests in the existing environment, including:

    python -m pytest -q tests/test_cascade_models_v1.py tests/test_autonomous_cascade_v1.py tests/test_localizer_region_selection.py tests/test_fixed_cohort_evaluation.py tests/test_saved_prediction_scoring.py

Add focused synthetic tests only for demonstrated adapter/platform gaps: native
geometry, units, invalid input, empty localization, failure records, reference
independence and cleanup. In particular inspect the CLI's file-access audit hook on
Windows; do not broadly disable it to fix platform file accesses. Record exact needs.

## GPU readiness and bounded execution proposal

Before dispatch, freeze exact checkpoints/configuration/cases, per-case and total
time/storage/memory ceilings, exclusive GPU ownership, supervisor and cleanup
behavior, and fresh output directories. Reuse applicable existing limits; if new
limits are needed, propose numeric values in the readiness report before launch.
No unbounded retries, silent cohort substitutions, policy search or final-test tuning.

Propose one small known development case for cross-device/old-path qualification,
then a fixed bounded development batch. Native grids, class mapping, finite outputs,
source identity and reference independence are mandatory. CUDA/MPS numerical
differences must be measured against a predeclared rule, not waived after results.
The same checkpoint alone does not make the old and new geometry comparable.

Existing CLI shapes, for a qualified packet only:

    python scripts/predict_autonomous_ct.py --request <fresh-request.json>
    python scripts/evaluate_autonomous_cohort.py predict --plan <plan.json> --plan-sha256 <SHA> --output-dir <fresh-directory>
    python scripts/evaluate_autonomous_cohort.py score --plan <plan.json> --plan-sha256 <SHA> --journal <journal> --report <new-report.json>

These are interfaces, not ready-to-run commands: the current CLI may need the
qualified geometry adapter. Inspect the runner's supervision and request schema;
wrap it with the existing qualified Windows executor where required. Never replay
completed output directories. Preserve every failure and count all requested cases.

## Deliverables and return message

1. Current verifier completion/cleanup/GPU status, with observation time.
2. Existing and missing artifacts with hashes; minimal private transfer request.
3. Compatibility matrix and smallest needed code change; focused test results.
4. Frozen eligible case/policy proposal, budgets and exact launch command; list any
   unresolved gate explicitly. Stop at readiness until the dispatch decision.
5. After separately authorized evaluation: per-case native results and failures,
   pancreas/lesion overlap, lesion recall/misses, false positives on empty references,
   localization containment, crop size, runtime/resource use and separate provided-
   region comparison. Return aggregate/error analysis and artifact hashes, not raw CT.

Commit small reviewed changes with clear messages. Do not push sensitive artifacts
or alter frozen scientific code. Update the existing W05-09 Trello card if available;
otherwise include the evidence in the return message for the Mac to reconcile.
Provide a concise handback in your chat for Quinton and the Mac to inspect. The Mac
can read this chat's result; sending another cross-chat message requires applicable
user authorization. No new scientific run or automatic successor is authorized.
