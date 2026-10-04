# Pre-course training week: September 28–October 4

Owner: Quinton Evans. Prepared by Codex after the requested development regroup.
**Status: proposed execution schedule for discussion; concrete targets, not a training launch.**
The course begins Monday, October 5. Existing data, source-use, protected-role and run gates remain.
This plan narrows priorities under the approved continuous-learning lane; it does not change the
formal Week 5/6 baseline/comparison milestones or the protected Weeks 9/10.

Detailed planning companions: [implementation phases](TRAINING-READINESS-IMPLEMENTATION-PLAN-2026-09-28.md),
[data-contract proposal](../data/PROTECTED-MEMBERSHIP-AND-ELIGIBILITY-PROPOSAL-2026-09-28.md), and
[pre-course completeness review](PRECOURSE-COMPLETENESS-REVIEW-2026-09-28.md).
These expand this outline for discussion; they do not authorize execution or close readiness gates.

## Goal

**By Friday, October 2: a qualified, tested PanTS-only pancreas-localizer training path is ready.**
**By Sunday, October 4: complete and review its first bounded real training smoke, if the gates pass.**

Start earlier if ready. The weekend is recovery/verification buffer, not a reason to delay a ready
run. These are work targets, not measured estimates: required source reconciliation and cohort
integration are the largest schedule uncertainties. Raise a concrete blocker when discovered.

Training-ready means all of the following exist together:

- a frozen, tiny train-role cohort with qualified pancreas targets, reviewed source-use evidence,
  exact source/annotation hashes, protected ancestry and enforceable holds;
- a capstone loader accepting that cohort identity and rejecting stale, wrong-role or held inputs;
- verified binary decoding, pancreas-only supervision, image/mask transforms, cache identity and
  image-only full-volume inference with source-grid restoration;
- scratch initialization for the first smoke, unique run/checkpoint destinations, saved configuration,
  code/environment/cohort identity and successful save/reload/interruption tests;
- run-relevant G0/G1 and component checks reconciled, plus verified mounted roots, capacity,
  accelerator ownership, measured memory/time headroom and a numeric stop budget;
- a preregistered CAP-EXP game plan in docs/experiments.md naming exact inputs, purpose, measurements,
  outputs and pass/stop conditions.

Writing a recipe is not training-ready. A smoke proves wiring/learning/recovery; it is not the
formal autonomous baseline, a generalization estimate or evidence of superiority.

## Rest of today — Monday, September 28

Today's goal is to remove ambiguity from the next implementation block.

1. **Complete Claude review.** Done in this session: P3 accepted for synthetic scope; 182 retrieval
   and 813 full native tests pass. Schema 1.0.0 accepted as the first reviewed baseline. No database
   phase automatically starts. See ../retrieval/CODEX-P3-REREVIEW-2026-09-28.md.
2. **Agree the first imaging scope.** Recommend PanTS only, dedicated background/pancreas output,
   scratch initialization, 1–4 qualified training cases initially. Choose exact cases only after
   evidence review; cases 2/266 remain unit-held and 78 stays outside pancreas-present supervision.
3. **Settle the protection-versus-eligibility contract.** Keep the full original 7,200/1,800/901
   membership record, with separate purpose-qualified executable children. Define how the source
   completeness requirement and parent protection artifact are represented under the current
   contracts. If an amendment is necessary, show the exact change for Quinton's decision before
   coding; no partial diagnostic package is silently renamed complete.
4. **Make one finite readiness checklist.** Reconcile existing G0 evidence, name each remaining
   first-run requirement, its implementation owner and acceptance check. Scope the source inventory/
   qualification work and reusable training functions. Complete already-established checks by
   citing their evidence; do not require unrelated future release components.
5. **Prepare the first implementation packet.** Name files, input scope and acceptance tests for
   source/cohort/consumer work. Where shared Plan 04 run-control code is needed, include its explicit
   coding authorization and scoped Plan 10 preconditions as a separate decision, not a hidden
   assumption. The explanation gate is already complete and need not be repeated.

End-of-day deliverable: an agreed training scope, a resolved or precisely identified cohort-contract
change, and a ready-to-execute implementation packet with concrete first acceptance checks. The
review and schedule are complete; items 2–5 are the proposed remainder of today's work, not claimed
as finished merely by writing this file. No additional anomaly adapter is the default next task.

## Rest of the week

| Day | Main work | Evidence to finish with |
|---|---|---|
| Tue Sep 29 | Source/cohort path | Required source inventory reconciliation, target-use qualification, exact protected membership and repeatable tiny cohort publication. If qualification is blocked, name the evidence gap immediately while independent synthetic consumer work proceeds. |
| Wed Sep 30 | Protected loader and preprocessing | Cohort resolves into model inputs; held/wrong-role/stale records are rejected; pancreas-only targets, binary mapping, geometry and cache behavior pass. Perform the bounded real-case load only after its prerequisites pass. |
| Thu Oct 1 | Training/checkpoint path | Reuse reviewed model/training internals; synthetic forward/backward, finite loss, save/reload, interruption and configuration identity pass. Prepare resource preflight and the exact smoke plan. |
| Fri Oct 2 | Readiness and first launch opportunity | Required gates reconciled, representative resource measurements recorded, numeric budget and stop criteria frozen. Training-ready declaration only if all checks pass. Begin the bounded run if ready. |
| Sat–Sun Oct 3–4 | Finish, inspect and preserve | Complete smoke, inspect learning and source alignment, verify saved checkpoint reload and run evidence; fix actual defects and rerun affected checks. Review/checkpoint code and independently back up irreplaceable evidence within approved storage limits. |

Dependencies outrank weekday labels. For example, train-consumer tests can be written while a
source audit is running, but no real training begins with unqualified inputs. Plan 04's four-hour
Prefect spike remains bounded if explicitly dispatched; its fallback prevents framework setup from
consuming the week. Full G3 is required before expensive baseline training, not automatically every
tiny smoke. Do not use that distinction to bypass required first-run recovery or ownership checks.

## Before October 5: acceptance target

Aim to enter Week 1 with:

1. One immutable qualified tiny training cohort and its tested consumer.
2. One completed capstone localizer smoke with a new checkpoint and reproducible run record.
3. Full-volume output on the registered training fixture, checked against source geometry.
4. Measured load/preprocessing/training/inference time and memory; a defensible next-run estimate.
5. A concise evidence review: what passed, what failed, what the model learned, and the next change.
6. A protected copy/checkpoint of the new work and a short prioritized Week 1 learning queue.

A run may legitimately fail to learn. Preserve and explain that result; distinguish successful
execution/recovery from successful tiny-set learning. If loss or outputs expose a correctness defect,
repair it before scaling. Do not quietly label an invalid run a successful smoke. Exact numerical
learning/timing bars belong in the run plan after fixture/resource review.

The minimum honest fallback by Sunday is the passed subset of this checklist plus the exact
remaining blocker, owner, next test and revised launch estimate. A missed target does not justify
relaxing protected roles, units, source terms or initialization lineage.

## Focus, ownership and capacity

- **Codex:** own the imaging critical path: usable inputs, cohort consumer, target/transforms,
  training/checkpoint integration and first-run evidence. Record useful outcomes in the existing
  readiness checklist/notebook instead of issuing a new architecture document per helper.
- **Claude:** P3 review is accepted. Proposed next literature task is bounded P2 seed-candidate work
  and acquisition-plan preparation for Quinton's review. Any P4a/P4b installation or driver work
  requires its own dispatch/approval and storage/resource envelope. Literature progress remains
  independent and must not compete with imaging for accelerator/memory/storage during a run.
- **Quinton:** decide the small cohort-contract change if needed, agree the first-run scope, review
  the resulting run plan/budget, and send the publisher email when intended. No new outreach is
  performed by Codex. Keep actual working availability in mind when adopting the weekday targets.

Defer case-2 record-format bridging, repeated anomaly investigation without new evidence, broader
robustness ablations, PANORAMA mixing, UI polish, cloud compute and broad model searches from this
week's first-training critical path. They are not removed from the capstone commitments where
applicable. Local-use qualification still needs its evidence; publisher release clarification is a
separate track and is not automatically a blocker for every local engineering activity.

## Checkpoints that prevent drift

- **Tuesday evening:** is the path to qualified training members and a frozen cohort demonstrated?
  If not, stop low-value follow-ups and expose the precise blocker. Do not spend Wednesday on more
  anomaly paperwork by default.
- **Thursday evening:** can the training/checkpoint path pass its synthetic checks, and are the
  remaining real-input/preflight checks explicit? If not, narrow the smoke, not its safety rules.
- **Friday:** declare ready or state the failed acceptance condition; revise the weekend plan from
  evidence. Never claim readiness solely because tests elsewhere in the project are green.
- **Sunday:** preserve/review the attempt and choose the first Week 1 experiment. This is a planned
  cadence, not a scheduled automation or authorization for unattended overnight work.

Week 1 should then focus on repeated measured learning, the segmenter/cascade path and incremental
orchestration, while continuing data qualification and independent retrieval. Formal Week 2
protected-cohort coverage, Week 3 PANORAMA and Week 4 DAG outcomes remain obligations; a tiny smoke
is an early engineering milestone, not evidence those whole plans are complete.
