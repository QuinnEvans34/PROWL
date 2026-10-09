# Week 2 living work plan

**Dates:** October 12–18, 2026 (America/Denver)
**Prepared:** October 9; early start this weekend, refine at Sunday review
**Owner:** Quinton Evans + Mac development chat
**Status:** Proposed execution order; no new implementation or training dispatched
**Weekly commitment:** Reproducible protected cohorts, with an early autonomous prediction integration slice.

## Direction confirmed October 9

Quinton reports training running on Lenovo and the entire dataset downloaded there. Lenovo now owns
training execution, environment/runtime work, checkpoint recovery and training-result production.
Mac owns application/pipeline development, integration, data correctness and evaluation tooling, using
the available 4TB drive. This supersedes the optional two-laptop weekend training plan. Small inference
and development tests may still run on Mac; no new long Mac training job is planned.

Lenovo readiness is user-reported; its CUDA changes, manifest and measurements have not been reviewed
in this chat. Request its compact report through Quinton when available; this need not block independent
Mac development. Do not alter its running code or change its experiment inputs. No cross-chat message
has been sent. Future fixes are handed back as reviewed commits for a subsequent run.

The Mac's prior run result reports24,000 completed updates and best development Dice0.3953174294791896.
This is reference-crop/tensor-grid development performance, not an autonomous or benchmark result.
Training operations move to Lenovo; experiment interpretation and selection remain part of the project.

## Proposal commitments and starting evidence

Approved proposal section6 assigns Week2 frozen cohorts, patient separation, manifests and repeatability
tests. Week3 adds PANORAMA; Weeks4–5 deliver integrated processing and an autonomous baseline.
The early imaging slice below advances those later outcomes without replacing the Week2 deliverable.

Existing foundations include protected identity/manifest/cohort modules, admitted training lists and
content reviews, geometryv2, a predicted-ROI adapter and React/NiiVue. Reuse these. The first task is to
identify and close the remaining connections, not design another manifest framework.

Week1's architecture outline exists. Its living closeout checklist still has unverified evidence;
carry those specific items visibly rather than mark every gate complete or postpone all development.
See [Week1](WEEK-01-WORK-PLAN.md), [Plan02](../implementation/02-data-and-cohorts.md) and
[autonomous investigation](../imaging/AUTONOMOUS-PREDICTION-INVESTIGATION.md).

## Outcomes

- [ ] One reproducible, portable cohort package with protected membership and explicit identity limitations.
- [ ] One small CT-only cascade produces original-coordinate outputs and explicit failures.
- [ ] The same development cases can be scored using reference and predicted regions without mixing the paths.
- [ ] If those are covered, one saved prediction package can be inspected in the existing viewer.

## Ordered task board

| ID | Priority | Task | Owner | Status | Finish criterion |
|---|---|---|---|---|---|
| W02-01 | Required | Finish protected portable cohort consumption | Mac; coordinate Lenovo path changes via handback | Ready to inspect current implementation | Repeat build gives identical memberships/content identities; overlap and role misuse rejected; machine roots do not redefine membership |
| W02-02 | Primary development | Connect native CT → predicted region → segmenter → native masks | Mac | Ready to specify exact patch after source trace | Small eligible set runs without reference-label access; tilted/large geometry behavior covered; every request has output or named failure |
| W02-03 | Primary evaluation | Matched reference/autonomous report | Mac | Depends on W02-02 | Same cases/checkpoint/native scoring; coverage, lesion/pancreas Dice, false alarms, failure denominator and paired case changes recorded |
| W02-04 | Secondary product | Show one prediction package in current viewer | Mac | Depends on stable output from W02-02 | CT and masks align; case/model identity shown; loading/missing/failure states explicit |
| W02-05 | Small closeout | Reconcile Week1 evidence and obtain Lenovo handback | Quinton + Mac | Pending available evidence | Specific carryovers and actual run/code identities recorded; no blanket completion claims |

## W02-01 — Dataset and cohort boundary

**Inputs:** existing `src/data/protected_identity.py`, manifest/cohort modules, original protected split
hashes, current admitted lists/review/exclusions, and the private Lenovo handoff. Inspect current code
and tests before choosing changed files. Lenovo may already have implemented root mapping; reuse a
reviewed implementation instead of writing a competing one.

**Work:** separate stable case/content identity from local roots; preserve existing split membership;
resolve train/development/test ancestry and annotation-use states; state where PanTS biological patient
identity is unavailable. Validate original and derived memberships rather than trusting source folders.
Build the selected cohort twice and compare canonical membership/content hashes. Keep machine-local
observations in local admission records; an unchanged portable identity does not make stale stat
observations valid on another machine.

**Checks:** wrong role, duplicate/overlapping member, altered source identity, missing labels, changed
root and repeated builds. Use focused existing fixtures; do not replay every historical audit.
**Output:** consumable portable package and a concise result describing actual guarantees and gaps.
**Boundary:** no split reshuffle, automatic healthy labels, full source re-download or test-set tuning.

## W02-02 — First autonomous integration

**Inputs:** eligible localizer/checkpoint with reviewed training membership, current segmenter checkpoint,
`src/data/segmenter_predicted_roi_v1.py`, geometryv2 and existing native export contracts/code.
The adapter currently imports geometryv1; support for the new trainer's geometry is a concrete gap,
not proof that it can be fixed by a one-line import replacement.

**Work:** trace existing localizer inference and native output; select a small fixed development set;
connect full CT inference to predicted region selection and segmentation, then map outputs back to
source coordinates. Reference labels enter a separate scorer after predictions are saved. Add targeted
geometry/round-trip tests and an explicit check that prediction succeeds without label access.

**Output:** a reproducible command plus inspectable native masks and failure records for each requested
case. Track localizer, crop policy, segmenter and transform identities. Empty localization or missed
coverage cannot be repaired using a reference box or removed from the requested-case denominator.
**Boundary:** does not require a better trained localizer, an ensemble, a classifier or a full UI rewrite.
If no eligible existing localizer can support the diagnostic, finish the integration with fixtures,
record that narrow model dependency and send a concrete training need through Quinton to Lenovo.

## W02-03 — Matched report

Freeze cases and segmenter checkpoint; compare reference-derived and predicted regions with the same
native scoring. Report effective lesion coverage after transforms, organ/lesion Dice with declared
empty-case conventions, sensitivity, eligible negative-case false alarms, inference failures and cost.
Select operating thresholds on development only. Reference-empty cases are not automatically clinically
healthy. Use paired cases and failure examples to choose whether the next job should improve localization,
crop robustness, segmentation or routing. Reuse the [investigation](../imaging/AUTONOMOUS-PREDICTION-INVESTIGATION.md)
for result history rather than create another experiment queue.

## W02-04 — Visible product slice

Reuse React/NiiVue and current case-package contracts. Load a saved CT/prediction package, overlay
pancreas/lesions, show provenance and indicate missing/failed predictions. Verify spatial alignment
and the supported UI states using a small fixture. Durable editing/review persistence and retrieval
integration remain separately scoped follow-ons; do not make them prerequisites for seeing an output.

## Development order and scope control

1. Reconcile current cohort/Lenovo changes and trace the autonomous code path in one focused inventory.
2. Implement the missing cohort consumption checks and the smallest runnable CT-only cascade slice.
3. Produce the paired evaluation report; use the findings to choose Lenovo's next experiment.
4. Add viewer integration once the output format is stable and required cohort work is covered.

The first coding session should end with an implemented/tested connection or a specific evidenced
blocker, not another general architecture proposal. Track retrieval's existing owner/status during
closeout; it remains a proposal commitment, but no duplicate retrieval work is scheduled here.
PANORAMA integration remains Week3; classifier/specialist and full-volume challengers remain candidate
experiments. Cloud provisioning and new training infrastructure are deferred unless a measured need arises.

## Sunday review

- Confirm priorities and available human time; refine the early draft without restarting planning.
- Record Week1 evidence/carryovers, course submissions and hours separately from unattended runtime.
- Review Lenovo run result/config/checkpoint identity when delivered; no presumed quality improvement.
- Select the next experiment from a written question; Lenovo owns launch and monitoring.
- Update task status from evidence and identify the first Monday implementation task.
