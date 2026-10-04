# From the current data foundation to the first capstone training run

**Status:** Draft for discussion; planning only. **Owner:** Quinton Evans. **Implementation/review:** Codex.
**Reviewed:** September 28, 2026. **Target:** ready October 2; first bounded real smoke reviewed by October 4.
**Dependencies:** Plans 01/02/05/06/09/10, relevant Plan 04 authorization, G0/G1 and R0–R8.
This elaborates the [weekly outline](PRECOURSE-TRAINING-WEEK-2026-09-28.md), not a thirteenth component plan.
No implementation, source qualification, experiment registration or launch is authorized by this draft.

## Outcome and why this is the right goal

Build one usable path: qualified PanTS CT and pancreas annotations → frozen training cohort →
checked loader and preprocessing → newly initialized pancreas localizer → identifiable checkpoint →
image-only full-volume prediction restored to the source grid → reviewed and preserved evidence.

This directly addresses autonomous localization in approved proposal v3.8 and appendix v3.1.
It produces early learning and resource evidence for Plans 05/06 without waiting for the literature
system or finished review interface. It does not establish lesion performance, the full cascade,
G4, a model comparison, or generalization. Formal Week 5/6 milestones retain their scope.

The recommended first scope is **PanTS only, scratch initialization, background/pancreas output,
1–4 qualified train-role cases**. The count is a proposed upper range, not permission to silently
reduce a frozen request. Select the exact count after qualification, then freeze it. Lesion-positive
status is not required for pancreas supervision. Existing historical trained weights are prohibited.

## Starting evidence and remaining work

- Latest recorded native suite: 813 passes, including 182 retrieval tests. This planning pass does
  not rerun or extend those tests. P3 acceptance is synthetic only.
- Approved original memberships reproduce as 7,200 train / 1,800 validation / 901 publisher test.
- The current five-study diagnostic package contains ten quarantined annotations and 22 holds;
  **zero eligible annotations and no production training cohort**. It is not a training dataset.
- Binary decoding policy D-259 is approved and independently pinned; mapping/allowed-use
  publication and eligible target consumption are not complete.
- The purpose checker enforces denials; it cannot grant eligibility or accept issue resolutions.
- Python and bounded UI foundations exist. Full G0 reconciliation, G1, production root resolution,
  real preprocessing, capstone training/checkpoint handling and exact-run preflight remain open.
- Cases 2/266 retain unknown-unit holds; case 78 is excluded from pancreas-present localizer
  supervision. Preserving these cases does not require admitting them to this smoke.

Evidence and current authority: [checkpoint](CURRENT-CHECKPOINT.md),
[regroup](DEVELOPMENT-REGROUP-2026-09-28.md),
[purpose package](../data/PURPOSE-DISPOSITION-PACKAGE-2026-09-28.md),
[first-experiment gates](FIRST-EXPERIMENT-READINESS-2026-09-28.md).
The last document's early pilot counts are historical; its R0–R8 identifiers remain the launch checklist.

## Non-negotiable boundaries

Preserve originals, old packages and original split membership. Separate preservation/protection from
permission to consume a target. Fail closed on unknown role, stale bytes, ambiguous geometry,
unapproved target use, unresolved relevant holds or unsupported schema. Use the approved
study-as-subject fallback honestly; it is not proof of biological uniqueness. Known duplicate and
cross-role protections still apply. No publisher-test image inspection, old model reuse, automatic
source repair, unit guessing, destructive cleanup, cloud spending or unrecorded experiment.

No complete UI, full retrieval/database implementation, mixed-source integration or stakeholder
session is required for this headless smoke. Their committed later milestones remain.

D-266 now locks permanent original membership, purpose-specific permission and training only through
frozen positively qualified subsets. The policy is settled; exact contracts/evidence remain to specify.

D-267 prohibits eligibility filtering based solely on difficulty or model performance. Preserve
qualified variation and record it for sampling/evaluation. Use the
[qualification checklist](../data/LOCALIZER-QUALIFICATION-CHECKLIST-2026-09-28.md); distinguish
integrity/interpretability requirements from this smoke's selection conditions and descriptive flags.
A tiny-set learning result does not establish generalization or representative coverage.

D-268 now approves staged qualification: broad source/split verification, detailed qualification of
every consumed case and expansion through new frozen cohorts. The remaining work is exact check
coverage, evidence, schema specification and bounded execution scope, not renewed policy approval.

## Phase A — settle contracts and the finite readiness scope

**When:** remainder of planning, before Tuesday's implementation. **Gates:** R0/R1/R2.

1. Review the [membership/eligibility proposal](../data/PROTECTED-MEMBERSHIP-AND-ELIGIBILITY-PROPOSAL-2026-09-28.md).
   Approve exact completeness, purpose qualification and protection-only parent semantics before
   modifying schemas. No partial diagnostic snapshot may be renamed complete.
2. Inventory required G0 evidence against the master gate: clean supported environments, unchanged
   historical baseline/classification, core contract fixtures and fast Python/UI checks. Cite already
   completed evidence; identify each remaining check. Do not replace G0 with a new informal gate.
3. Review historical model/data/training/inference functions for reuse versus adapters. Protect
   historical entry points and results; a changed drive path is not a capstone consumer.
4. Issue a bounded implementation packet for Phase B with named schema versions, allowed files,
   evidence inputs, test cases and run restrictions. Separate pure synthetic implementation from
   later on-drive inventory and qualification jobs.
5. Obtain the existing Plan 04 coding authorization before implementing shared publication,
   ownership/locks, retry or workflow code. Its explanation gate is already satisfied. The bounded
   Prefect evaluation/fallback belongs to that authorization; do not build an unofficial parallel runner.

**Exit:** decision references, schema-change specification, finite G0 gap table and an implementation
packet marked Ready. Unresolved decisions have an owner and required evidence, not invented approvals.

## Phase B — reconcile source coverage, qualify targets and freeze the cohort

**When:** Tuesday; largest uncertainty. **Gates:** R1/R2, G1.

1. Before any source job, pin its source/archive receipts, metadata, accepted base-list hashes,
   exact file scope, registered roots, output destination and time/bytes/memory limits. Verify the
   actual mount identity and capacity; today's planning has not inspected the drive.
2. Reconcile the required source inventory and all protected identities. Account for missing,
   unexpected, duplicate and intentionally unextracted members. Separate inventory completeness
   from payload integrity assurance and per-target usability. Existing extraction totals alone
   prove neither. Record exactly what full-source or scoped completeness means under the approved
   contract. If that scope cannot satisfy G1, stop real training and report the remaining work.
3. Determine a bounded candidate pool from original train-role membership using deterministic
   rules. Reuse verified retained evidence where sufficient. New reads are limited to approved
   candidates/required inventory; do not expand into a full voxel audit of every label.
4. For each candidate, verify CT/pancreas hashes, source-release linkage and permitted local target
   use; finite data, physical units, invertible affine, image/mask alignment and verified nonempty
   pancreas foreground for this pancreas-present smoke only. This is not a universal eligibility
   condition. Bind the D-259 mapping and lineage. Preserve source label scaling evidence.
   Do not infer manually drawn annotations or disease-negative status from an empty lesion mask.
5. Publish independent qualification and issue-resolution evidence under the reviewed contract.
   A resolution needs its own evidence and new artifact; deleting a hold is not qualification.
6. Build protected base membership and the executable smoke descendant. Resolve full parent graph,
   exact subject/study/protection-group overlap checks, allowed target use and exact requested size.
   Report exclusions, provenance, grouping fallback, requested/achieved counts and assurance limits.
7. Repeat the same build; membership/profile hashes must match. Publish immutable membership,
   profile, ancestors and completion record. Resolve it by cohort ID with tamper/role checks.

**Exit:** accepted G1 evidence for this path, qualified selected targets, frozen reproducible train-role
cohort and tested resolver. A list of plausible case IDs is insufficient.
**Fallback:** if no qualified case exists, continue authorized synthetic work and report the specific
source/provenance/geometry blocker. Do not spend the week adapting held case 2 merely to add another
quarantined record. Do not reassign validation/test members or silently refill a cohort.

## Phase C — connect the consumer and prove preprocessing

**When:** Wednesday. **Gates:** R3 and R1/R2 regression.

1. Capstone entry accepts a cohort ID. Resolve immutable CT/annotation/policy references before
   loading arrays. Reject raw ID lists, missing completion markers, unsafe root escapes, stale bytes,
   wrong roles, protection-only parents, unsupported versions and held targets before model work.
2. Adapt validated records to MONAI without dropping lineage. Keep input CT and supervision distinct.
   The localizer receives one CT input and a binary pancreas target; lesion masks cannot influence
   input channels, crops, target generation or inference. Training-only target-guided sampling,
   if selected, is explicitly recorded; inference never receives reference masks or a supplied ROI.
3. Configure orientation, spacing, HU normalization, interpolation, padding/cropping and target
   decoding. Images/probabilities and discrete masks use their declared interpolation policies.
   Reject rather than guess unsupported geometry. Persist the transform chain needed for inversion.
4. Test anisotropic/oblique/orientation fixtures, thin structures, foreground preservation, mask
   label set and source-grid round trip. A same-shape array alone does not establish alignment.
5. Cache identity includes input bytes, target/policy identity, transform code/config and relevant
   environment. Test cold/warm equivalence and stale-cache refusal. Choose a bounded cache/worker
   policy; do not cache all volumes by default on unified memory.
6. After gates pass, perform the separately scoped real-case loading check. Inspect CT/target overlays
   in three planes and record target extent, spacing, shape, source and transformed foreground counts.
   Use local permitted artifacts; no patient images in public Git.

**Exit:** valid cohort reaches correct tensors; planted role/geometry/target errors are rejected;
source-space restoration and real overlay checks pass. No training launch yet.

## Phase D — learning, run identity and recovery on synthetic fixtures

**When:** Thursday; pure tests can be prepared before Phase B completes if separately authorized.
**Gates:** R4/R5/R6 and relevant R7 controls.

1. Reuse reviewed model internals; configure the dedicated binary localizer and prove scratch
   initialization. Reject project-trained initialization and implicit checkpoint auto-discovery.
2. Use synthetic fixtures with a known signal to test forward/backward, finite loss/gradients,
   parameter updates and learning. Define empty-target/empty-prediction behavior explicitly;
   report undefined values as such. Confirm metric values against independent small oracles.
3. Record code/config/environment/cohort identities before compute, including device/precision,
   seeds, worker/cache policy and source capture. Smoke runs may use the approved dirty-source
   capture policy and remain non-promotable; formal comparisons require a clean revision.
4. Implement the approved run/checkpoint publication path: unique run and attempt IDs, no overwrite,
   complete versus partial state, hashes, typed configuration and model/optimizer/scheduler state.
   Capture RNG/sampler state or declare an exact supported restart boundary. Do not promise exact
   mid-batch or bitwise MPS continuation unless demonstrated.
5. Interrupt at a controlled point. Reload the last complete checkpoint, check all parent/config
   identities, and resume at the declared boundary. Corrupt/partial/mismatched checkpoints fail.
   A retry creates an attempt record and never erases the failed attempt.
6. Verify reload prediction agreement on a fixed fixture using a prespecified tolerance. Test
   output class/shape, image-only full-volume inference and inverse spatial transformation.
7. Connect local experiment tracking under the existing plan; immutable records remain sufficient
   to reconstruct a run if the tracking service is unavailable. Record the actual failure policy.

**Exit:** native synthetic learning, save/load, corruption, interruption and inference tests pass;
checkpoint is usable and identity-bound. This is engineering evidence, not real model performance.

## Phase E — resource profile, freeze the exact recipe and launch review

**When:** Friday, or earlier if ready. **Gates:** R0–R8 together.

Use [compute protocol](COMPUTE-DECISION-PROTOCOL.md),
[run identity](ENVIRONMENT-AND-RUN-IDENTITY.md) and [backup policy](BACKUP-RETENTION-AND-RECOVERY.md).
Any real-data profiling is itself a bounded recorded operation, not an unlogged training attempt.

Measure representative cold load/preprocessing, warm cache, forward/backward, checkpoint write/read
and full-volume inference. Record raw timings, warmup, median/range and memory measurement method;
MPS allocation alone is not total unified-memory use. Forecast total time/disk plus at least 25%
contingency. Check one accelerator owner, power/connection arrangements, external free space,
root identity and backup headroom. Do not assume overnight availability.

Freeze these fields before compute; missing values block R8:

| Area | Required concrete values |
|---|---|
| Scientific question | Tiny-set learning/wiring question; smoke classification; next decision |
| Data | Exact source, manifest, cohort, member, annotation, mapping and protection hashes |
| Model | Architecture/version, channels, scratch lineage, seed, precision/device |
| Transform/sampling | Orientation, spacing, HU window, interpolation, crop/patch dimensions, samples, padding, augmentation, cache/workers |
| Optimization | Loss and reductions/background handling, optimizer, LR, schedule, batch/accumulation, exact maximum updates |
| Measurement | Loss reporting, full-volume training-fixture Dice and empty-case handling, foreground volume, alignment checks, inference settings and reload tolerance |
| Recovery | Checkpoint cadence, retention, interruption boundary, retry policy and attempt identity |
| Resources | Numeric wall-time/step/memory/disk limits, monitoring method, stop action and reserved output space |
| Evidence | Notebook CAP-EXP plan, run/artifact roots, source capture, logs/metrics, checkpoint/predictions and backup selection |

**Starting budget proposal for discussion:** no more than four cases, one accelerator job, at most
100 optimizer updates, 60 minutes of training and two hours for the entire real attempt including
inference/checkpoint inspection; stop at the first reached limit. These are ceilings to validate or
revise *before launch*, not throughput estimates or permission to execute. Freeze memory/disk limits
from measurements; if the first volume cannot fit safely, revise the registered resolution/patch/cache
recipe and rerun affected checks. Never extend a run automatically because it has not learned.

Create the next available CAP-EXP entry in `docs/experiments.md` only when its concrete inputs are
known. Every experiment gets a game plan under D-252; a smoke does not require the full statistical
preregistration of a controlled comparison. Agree a fixed before/after learning measurement after
synthetic validation and before real output is seen. Do not choose a favorable threshold afterward.

**Exit:** readiness record links passing evidence for each R0–R8 row, exact budget/recipe reviewed,
no pending source or contract exception. Only then can a separate launch proceed.

## Phase F — execute, inspect, preserve and choose the next experiment

**When:** Friday/weekend, conditional on launch review. **Gates:** R5–R8 evidence completion.

1. Run only the frozen attempt. Log step/loss/time, resource observations and any failure/cancellation.
   Stop on nonfinite values, identity/geometry failure, missing drive, failed publication or a budget
   limit. Preserve diagnostic evidence; no automatic retry into new settings.
2. Generate full-volume predictions on the registered training fixture without reference inputs.
   Report all requested cases and failures, source-grid checks, pancreas Dice/foreground behavior,
   checkpoint identity and reload agreement. Training-case scores are not held-out performance.
3. Inspect three-plane source overlays and error locations. Distinguish: execution passed; recovery
   passed; alignment passed; learning passed/failed/inconclusive. A finite decreasing loss alone is
   insufficient evidence of meaningful segmentation, and a valid null learning result is still useful.
4. Preserve the run plan, config/code/environment, cohort lineage, logs, metrics, images permitted for
   local retention and the selected checkpoint. Verify an independent copy and restore/load the
   checkpoint from that copy. Enforce the shared 20 GiB backup cap and 100 GiB internal free-space
   floor; measure existing allocation and do not delete files to fit. Test the procedure with a small
   loadable fixture before launch; restore the actual retained checkpoint afterward.
5. Review permitted code/docs for a Git checkpoint, with concrete staged scope and publishing
   authorization. Git does not back up ignored scientific payloads. Update the notebook, current
   checkpoint and progress records with actual evidence; do not invent effort hours.
6. Select the next experiment from the failure or success: repair correctness first; if correct but
   no learning, test one justified optimization change; if learning/alignment/recovery pass, progress
   to a tiny segmenter and predicted-ROI cascade, then larger train-only/development cohorts.

**Exit by October 4 target:** one reviewed real attempt and usable preserved evidence, clear outcome,
measured next-run estimate and prioritized Week 1 queue. Successful tiny-set learning is desired,
not guaranteed. A failed valid attempt and an invalid attempt must be labeled differently.

## Implementation locations and verification contract

Existing paths below are reuse/review targets, not blanket permission to rewrite them. Proposed new
names are reconciled in the Phase A packet to avoid duplicating repository infrastructure.

| Component | Existing touchpoints | Proposed bounded implementation/evidence |
|---|---|---|
| Qualification | `src/data/manifest_records_v2.py`, `annotation_v2_records.py`, `annotation_contract_v2.py`, `purpose_disposition.py`, `protected_identity.py`; data schemas | Explicit new contract version where semantics change; qualification/resolution tests; new immutable package, old packages unchanged |
| Cohorts | cohort/member schemas, protected-cohort protocol | Proposed `src/data/cohort_records.py`, `cohort_registry.py` and matching tests; repeat-build, overlap, ancestor and tamper reports |
| Consumer/transforms | `src/data/dataset.py`, `transforms.py`, binary policy | Separate capstone adapter/entry path; synthetic and bounded real load evidence |
| Model/inference | `src/models/segresnet.py`, `src/inference/sliding_window.py` | Reviewed reuse, dedicated binary config, image-only inference and inversion tests |
| Training/checkpoints | `src/training/`, historical `scripts/train.py`, run-manifest schema | Proposed capstone training entry accepting cohort ID; approved shared run/publisher helpers, recovery tests |
| Operations | storage registry, Plan 04/10 contracts | Root/preflight/ownership/backup integration after scoped authorization; no ad hoc runner |
| Records | `docs/experiments.md`, existing R0–R8 checklist | One run-readiness report and immutable run evidence, not a new narrative document per helper |

Required fault tests include wrong role through a grandparent; same subject across roles; altered
membership or source bytes; protection-only parent consumed directly; applicable unresolved hold;
unapproved binary mapping; unknown units; flipped orientation; mask/input mismatch; lesion/reference
input canary; stale cache; hidden checkpoint load; nonfinite training; mismatched resume; truncated
checkpoint; disk/drive failure; same-device copy mislabeled as independent backup. Use synthetic
fixtures for injected corruption; never damage real sources to test failure handling.

Run focused native tests after each component, then the existing full command after integration:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

The future packet must name focused test files/commands after paths are settled. Real geometry,
MPS/resource and restore evidence are separate from CPU pytest. No artificial test-count target.

## Calendar, decisions and fallbacks

| Checkpoint | Required result | If absent |
|---|---|---|
| Before Tuesday execution | Approved completeness/eligibility semantics and bounded Phase B packet | Continue paper/synthetic work only; identify exact decision/evidence |
| Tuesday evening | Required inventory and at least one qualifying route demonstrated; frozen cohort if ready | Reforecast Friday immediately; no more unrelated anomaly work by default |
| Wednesday evening | Cohort consumer and geometry checks pass | Repair the failing boundary before real compute |
| Thursday evening | Synthetic learning/reload/interruption pass | Narrow implementation scope without removing identity/recovery tests |
| Friday | R0–R8 closed for exact recipe, or named failed rows | Launch only if ready; otherwise report owner, next test and revised estimate |
| Sunday | Reviewed attempt, preservation and Week 1 queue | Preserve completed work and explicit blockers; do not claim training completion |

Open decisions: approve first-smoke scope; specify/review D-266's concrete contract amendment; authorize the
bounded Plan 04 work when its packet is concrete; freeze measured recipe/budget before launch.
Quinton's available hours and course pre-work remain unconfirmed. Dates are targets, not estimates.
The next discussion should define qualification evidence and source-completeness scope under D-266,
then review the concrete contract changes and authorize the smallest
implementation packet. No automatic phase dispatch follows from this document.


## September 28 execution update — synthetic MPS profile

The [resource handback](LOCALIZER-RESOURCE-PROFILE-HANDBACK-2026-09-28.md) supplies bounded
96³ MPS update/inference and internal diagnostic checkpoint timing under D-272. This satisfies
that part of Phase E, not production run-root binding, keeper restore, external checkpoint timing
or R8. Local smoke feasibility is supported; full-capstone D-210 remains open. Current candidate
limits are 100 updates, 10-minute update cap and 20-minute end-to-end cap, to freeze after the real
input/checkpoint bridge is verified. No real-data experiment launched.


## September 28 execution update — qualified bridge and recovery

[D-273 verification](LOCALIZER-RUN-BRIDGE-HANDBACK-2026-09-28.md) connects the exact cohort to MPS
without real updates and verifies external checkpoint publication/independent backup/consumer restore
using a synthetic rehearsal. [CAP-EXP-001's design](CAP-EXP-001-LAUNCH-PLAN-2026-09-28.md) fixes the
candidate first-run settings and limits. The remaining implementation is the bounded real-update loop
and terminal metrics/export; finish it before launch approval. No new broad prerequisites are implied.
