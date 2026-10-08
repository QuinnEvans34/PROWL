# Week 1 retrospective and training refocus — October 7, 2026

Requested by Quinton after reviewing the gap between completed engineering work and full training.
This is a retrospective and proposed execution correction. It does not alter historical results,
data dispositions, frozen requests, or scientific stopping rules, and does not launch a job.

## What the proposal actually commits to

Read the accepted proposal v3.8 and technical appendix v3.1 directly from their DOCX text.
Both SHA-256 values match `references/governance/APPROVED-SOURCES.md`.

The committed product is an autonomous pancreas/lesion annotation-assist workflow with newly trained
models, reconciled PanTS/PANORAMA data, controlled model comparisons, patient-level evaluation,
saved reviewer decisions, cited literature support and professional documentation. It is not a
clinical diagnostic system. Prior pipeline code may be adapted; prior course-trained models may
not become the capstone model. No particular modeling strategy or Dice improvement is guaranteed.

Week 1 (October 5–11) commits to approved architecture, acceptance criteria, workflow design and
test planning: data design, retrieval requirements, workflow DAG, UI-extension requirements, and
unit/integration test strategy. Its behind-schedule signal is unresolved design/test criteria.
It does not require a finished autonomous model or a complete new training platform this week.
Week 2 covers frozen cohorts; Week 4 the tested restartable workflow; Week 5 the formal autonomous
baseline; Week 6 a controlled model comparison. Week 8 completes the system, Week 9 stabilizes,
and Week 10 delivers. D-058 explicitly makes training continuous: Week 5 is not a training start date.

Most design deliverables are already recorded as approved. The Week 1 acceptance checklist remains
open: reconcile current requirements/evidence, bounded blockers, test-environment evidence and the
Week 2 starting gate. Historical test totals do not certify the current entire repository. Course
submissions/presentation and active human hours require separate factual confirmation.

## What was built and what it demonstrates

| Work | Useful outcome | Limit |
|---|---|---|
| Input/geometry/cache/scoring foundation | Protected roles, checked target interpretation, spatial mapping, native masks and metrics | Only six lesion-training cases and one report-only case qualified in the current path |
| Localizer and segmenter training | Actual learning, saved models, exports and small experiments; earlier pancreas-class collapse repaired | Useful contours and a broad autonomous baseline remain unproven |
| Predicted-region adapter, commit 16e672d | Connects predicted support to shared crop/restoration geometry | Artificial-input tests only; existing real consumers not switched |
| SuPreM work, commits 79e2208 through 0596e64 and 056b2af | Checkpoint inspection, actual identity/metadata verification, artificial-weight loading/session tests | Source acceptance unresolved; no full pretrained capstone training |
| Duration runner, d158190 and follow-ups | Bounded training, journaling, checkpoint preservation, native scoring and resource supervision | Implementation is specialized to six cases/192 updates |
| Recovery work | Saved inference qualified; stopped R01 artifacts independently restored | Bit-exact optimizer continuation remains unqualified |
| Retrieval, c636e00 | Parsing/sizing/storage integration tests | No live operational corpus/index established by those tests |
| Documentation/coursework | Designs, deliverables, traceability and historical evidence | Completion of a document is not completion of the capability it describes |

R01 ended at 48 actual updates under its declared recall stop. That is a real failed small
experiment, not evidence that a 24,000-update model would fail. Preserve its outcome unchanged.

## Why a single parameter change does not extend the current runner

The restrictions are in code, not just in an experiment configuration:

- `src/training/segmenter_duration_session_v1.py`: `validate_config` requires 144-cubed native
  inputs to use exactly 192 steps; sampler/control validation requires six train and one validation.
- `src/training/segmenter_duration_executor_v1.py`: request validation fixes native steps to 192,
  checkpoint cadence to 0/48/96/144/192, and work accounting to 253 forwards/192 optimizer calls.
- `src/training/segmenter_duration_policy_v1.py`: fixes seven roles, terminal step and screens,
  including quality decisions for that specific duration comparison.
- Evidence and source-reference accounting also encode those fixed cases and stages. Altering one
  number leaves other checks and accounting inconsistent; disabling them would hide that mismatch.

By contrast, `scripts/train.py` derives duration from `--max-iters` and supports configurable
validation/checkpoint intervals, schedules and disk caching. It is the first reuse candidate.
Its presence is not proof that its current inputs and environment are ready for immediate execution.
The old recipe also differs from the new one in initialization, loss, geometry and schedule.

One concrete input detail: `src/data/dataset.py:build_records` takes image/mask paths directly from
the manifest. Changing only `paths.pants_root` does not repair stale paths inside that manifest.
The other imaging chat reports the historical 1,412-case split has no overlap with original
development/test lists, but its manifest uses the former drive location. Reuse that split audit;
reconcile current files, annotation meaning, existing holds and manifest completeness before use.

## Where the work went wrong

1. The tiny wiring-check milestone remained the default after Quinton requested full experiments.
2. A specific scientific experiment was encoded across infrastructure instead of represented by
   validated configuration. The resulting runner is less flexible than its name suggests.
3. Exact replay, independent recovery and specialized launch controls became a serial prerequisite
   for training, without consistently separating uninterrupted development from future resume claims.
4. New machinery generated its own rework: file-hash reconciliation, rejected script paths, an
   unsupported helper argument and a missing canonical JSON newline. These were integration defects,
   not evidence against long model training.
5. Tracking emphasized completed pieces. Trello W01-14 is titled "Resolve SuPreM source-separation
   evidence gap" and marked Done while its description says the gap remains unresolved. W01-28
   correctly records a finished failed attempt, but cannot represent a completed full-training goal.
6. The plan explicitly allowed continuous training, yet that intention did not become a broad
   executable experiment. Historical code reuse was allowed and should have been evaluated earlier.

This was useful foundation work mixed with avoidable rework and a priority mismatch. Commit counts
and artificial-test counts cannot quantify time wasted or capstone completion. No hardware limit
or fundamental inability to train a long run has been established by this review.

## Recovery direction

### Quinton's clarified performance objective

Quinton explicitly wants a model competitive with published PanTS results and sustained long
training on the available eligible data. This is the modeling ambition alongside the committed
capstone deliverables, not a guarantee of a benchmark score or a change to protected evaluation.
The official PanTS repository, consulted October 7, lists nnU-Net DSC 50.9%, MedFormer 52.9% and
R-Super 53.4%, with specificity 90.1%, 90.0% and 93.2% respectively. R-Super uses additional
external data. Source: https://github.com/MrGiovanni/PanTS#pants-benchmark-official-in-distribution-test-set
These are official in-distribution benchmark results; historical provided-region development
scores do not establish equivalent performance. Select an exact comparator and evaluation protocol
before claiming parity; optimize on development data and preserve final test separation.

The proposed architecture is a reusable trainer plus a versioned experiment configuration, a
validated cohort manifest, and run-specific outputs. Duration, cohort, sampling, learning-rate
schedule, validation cadence, checkpoint cadence, selection and stopping policy belong in that
configuration. Input validity, split separation, finite computation and resource accounting remain
shared checks. Six-member/192-step assumptions belong only to the historical pilot.

The next concrete engineering deliverable is one executable full-baseline configuration and its
necessary input adapter/preflight, reusing `scripts/train.py` first. Completion means routine changes
to duration and cohort can run without editing trainer source, and actual selected inputs pass the
targeted checks. It does not mean another general infrastructure design has been written. Longer
schedules must set the learning-rate horizon coherently; extending an already completed run is a
separate recorded continuation, not a silent change to its original schedule or result.

Prioritize one PanTS-only development baseline through the existing long trainer. Retain proven
data separation, geometry, metrics, run records and checkpoint preservation. Do not require full
retrieval, UI, PANORAMA integration or a new orchestration system before that baseline.

The finite launch preparation should produce:

1. A current manifest and fixed train/development memberships, accounting for every requested case,
   existing hold and supported negative-label interpretation. Batch routine checks; do not silently
   drop records, relabel unknown empties or repeat already established split evidence.
2. One explicit initialization choice. Fresh scratch avoids dependence on unresolved SuPreM use;
   it is a new baseline, not an exact EXP-24 reproduction. Pretrained reproduction remains conditional.
3. A frozen recipe and exact command, with a proposed 24,000-update reference horizon, development
   selection and useful checkpoint cadence. Final horizon/resource limits need actual input/throughput
   evidence; fourteen hours is not a verified duration or an optimization endpoint.
4. A bounded runtime/input compatibility check and storage estimate covering cache and retained
   checkpoints. Repair demonstrated defects only, then run checks affected by those repairs.
5. A clear interruption policy. An uninterrupted first experiment can retain checkpoints without
   claiming qualified optimizer resume. Do not automatically resume or silently loosen replay claims.
6. New prospective quality rules appropriate to early learning. Poor early Dice alone is not proof
   of broken computation. Preserve operational stops for invalid inputs, nonfinite values, resource
   limits and failed checkpoint writes; distinguish final scientific rejection from emergency stop.

The requested priority is full training; no six-case overnight fit is a substitute. Source inspection,
exact allocation and executable job configuration still have to be made concrete. This review does
not certify immediate launch or promise a preparation ETA.

## End-of-week targets and prevention

**Required by the proposal:** finish the Week 1 architecture/acceptance/workflow/test readiness
review and make the Week 2 cohort work executable. Preserve the approved scope and protected weeks.

**Recommended accelerated training target:** launch one broad development run before Sunday if
the input/environment/resource checks pass; inspect its outputs and prepare the next experiment
from results. A failed or null result is acceptable evidence. If blocked, record the exact missing
input or failing check, rather than substituting more unrelated infrastructure work.

Working changes recommended for agreement:

- State whether each task delivers a tested component, a runnable experiment or a measured model.
- Require every new pre-training task to name the concrete failure it prevents and why an existing
  component cannot do it. Separate proposal requirements from local implementation preferences.
- Make future run length/cohort/cadence configurable; validate ranges and relationships rather than
  fixing a single experiment throughout the codebase.
- Approve complete experiment scopes with routine implementation autonomy; avoid splitting each
  predictable internal correction into a fresh planning cycle.
- Track broad usable cases, full runs, development results and integration milestones prominently.
  Rename misleading task titles when updating the board; preserve descriptions and history.
- Keep one implementation owner and one accelerator job. Review results in the morning and select
  the next overnight experiment explicitly; no blind unattended sweep.

## Review evidence and actions

Sources: accepted proposal/appendix; `MASTER-PLAN.md`, D-003/D-004/D-058/D-255 in `DECISIONS.md`;
`weeks/WEEK-01.md`; recent Git history; live PROWL Trello board and selected card descriptions;
current and legacy trainer source; retained R01/full-scale handbacks.

The other main imaging chat is idle after a matching long-trainer review. No cross-chat message was
sent. This review read documents/code and checked workspace identity; it did not run models, open
patient or weight payloads, rerun scientific tests, change training code/controls, edit Trello, or
publish Git changes. This new retrospective is the only repository edit from this turn.
