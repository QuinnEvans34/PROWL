# Development regroup and path to first training

September 28, 2026. Requested by Quinton after purpose-disposition publication and case-2
review. **Assessment and proposed work ordering, not a training launch or a gate waiver.**

## Main assessment

We should now prioritize a working training path. We have substantial tested foundations,
mostly completed Week 1 design work, partial Week 2 data implementation, and early work supporting
later milestones. We do not yet have a capstone-qualified loader/cohort/run path or a new capstone
model. Counting tests, documents, downloaded bytes or approved plans as a percentage of the final
system would exaggerate completion.

The course starts October 5. September 28 is pre-course preparation, not Week 4 or Week 5.
We are not late against the official course calendar. That does not justify delaying training:
the plan explicitly makes early model learning continuous once the particular run is ready.

The immediate risk is spending more effort on isolated diagnostic records than on connecting
verified inputs to a useful experiment. A new record is valuable when it closes a concrete decision
or protects a real consumer; it should not automatically lead to another administrative slice.

## Sources and authority reviewed

The approved proposal v3.8 and technical appendix v3.1 were read from their preserved Word files;
both SHA-256 values match references/governance/APPROVED-SOURCES.md. The newer unapproved v3.9 file
was not substituted. Reviewed the master schedule, all twelve component plans' outcomes, relevant
implementation sequences, decisions, readiness/acceptance gates and handoffs; implementation-start,
cohort protocol, first-experiment checklist, current checkpoint, risk/requirement/test traceability,
and dated data/test/operations evidence. Plan 07's current phase map and D-260–D-265 supplement its
older plan. Current code was inspected to distinguish implemented helpers from promised consumers.
This is a planning/development assessment, not a fresh scientific or full-code acceptance audit.

Core planning sources: [master](../MASTER-PLAN.md), [plan index](../implementation/README.md),
[implementation start](../IMPLEMENTATION-START.md), [first-run checklist](FIRST-EXPERIMENT-READINESS-2026-09-28.md),
[cohort protocol](../data/COHORT-PROTOCOL.md), [current status](CURRENT-CHECKPOINT.md).

## Completed work with concrete value

- All twelve component designs are approved. Source hierarchy, scientific boundaries and the
  ten-week schedule are established. This substantially satisfies the design intent of Week 1;
  formal G0 executable-evidence reconciliation remains open.
- Clean Python foundation, preserved historical tests, and growing synthetic data/contract tests.
  Latest recorded full suite: 751 passes, including 120 retrieval tests; latest data-only rerun:
  631 passes. These are software results, not scientific performance or completion percentages.
- UI foundation: recorded September 20 clean installs/build, 18 unit/component tests and one
  synthetic browser flow. It does not establish real NiiVue geometry or durable review persistence.
- Acquisition/extraction and targeted integrity work: September 28 receipts report 15 completed
  archives, 300,608 files and 565,327,340,747 expanded bytes. These counts are not complete payload
  qualification. Publisher-test images remain unextracted at the latest recorded checkpoint.
- Protected base-list hashes/counts reproduce: 7,200 train / 1,800 validation / 901 test. Identity
  and migration guards exist. Biological uniqueness remains explicitly unverified under the approved
  study-as-subject fallback; we need not invent a patient identifier to proceed.
- Manifest assemblers, metadata/file/header adapters, voxel audits, v2 annotation representation,
  strict binary policy/lineage and purpose-denial helpers are implemented and tested.
- Retained voxel evidence covers seven distinct PanTS training studies (1, 2, 3, 26, 31, 78, 266),
  not the entire dataset. The current five-study package has ten quarantined annotations and 22
  blocking issues, including the two new purpose denials. It grants no training use.
- Scoped storage/root checks and an initial independent synthetic restore passed. A reviewed
  115-file Git snapshot was pushed. Recent work and ignored evidence still need their own checkpoint/
  backup treatment; source recovery and backup architecture are not starting from zero.
- Retrieval P1 is frozen; Claude's P3 synthetic foundation was reviewed natively. Five contract
  findings still block acceptance. No real evaluated retriever or evidence assistant exists yet.
- Historical training, inference, MLflow, model and UI code provide reusable engineering. Historical
  trained checkpoints and earlier results are not new capstone deliverables.

## Twelve-plan development map

| Plan | Implemented/evidenced now | Remaining outcome |
|---|---|---|
| 01 Architecture | Approved boundaries; schemas and some validators | Complete relevant cross-record/producer-consumer enforcement |
| 02 Data/cohorts | Identity guards, manifest assembly, retained evidence and denials | Qualified source/use records; frozen cohort publisher/resolver; actual consumer enforcement |
| 03 PANORAMA | Approved mapping/provenance design, acquisition and label integrity evidence | Source adapter, geometry/remap qualification, duplicate controls and mixed-source cohort |
| 04 Orchestration | Approved design and completed walkthrough | Explicit coding dispatch, bounded tool selection, tested run/reuse/recovery/control path |
| 05 Imaging | Reusable historical model/transforms/inference code | Dedicated pancreas-only capstone path, spatial parity, new localizer/segmenter and autonomous baseline |
| 06 Evaluation | Approved protocol and some golden metric tests | Run registry, complete evaluator, baseline error analysis, matched comparison and final freeze |
| 07 Retrieval | Approved detailed phases, frozen needs, synthetic P3 implementation | P3 corrections, seed review, separately authorized infrastructure/acquisition, corpus, retrieval/response evaluation |
| 08 Interface | Existing viewer and scoped build/unit/browser baseline | Versioned case/evidence adapters and durable review writer; real workflow verification |
| 09 Quality | Python/UI foundations and many specific regressions | Explicit current G0 reconciliation, missing high-risk boundary tests, later end-to-end/release matrix |
| 10 Operations | Scoped roots/filesystem/backup setup and locked environment evidence | Production resolver/preflight, run storage/checkpoint recovery and representative resource measurements |
| 11 Stakeholders | Approved protocol and outreach history | Confirm participant/fallback by Week 5; conduct review in Week 7 |
| 12 Delivery | Approved integration/release process | Actual integrated candidate, final evaluation, restore/release proof, documentation and presentation |

Design approval is not execution completion. No G1–G9 completion is established by this review.
The exact full G0 closure remains to be assessed against existing evidence rather than assumed from
test counts or kept indefinitely open by requiring future release tests.

## Week 1 to Week 10 against current development

Calendar dates follow the recorded October 5 start; exact assignment deadlines remain the course's.

| Week and dates | Approved milestone | Present position / intended next progress |
|---|---|---|
| 1 — Oct 5–11 | Architecture, acceptance criteria, workflow and test planning | Substantial design work already done. Reconcile executable readiness and aim for first qualified localizer smoke if its gates pass. |
| 2 — Oct 12–18 | Frozen protected cohorts, separation and repeatability | Partly implemented; no frozen capstone cohorts yet. This is the most important missing deliverable for training. |
| 3 — Oct 19–25 | Validated PANORAMA integration | Data acquisition is ahead of schedule; adapter/eligibility/duplicate work remains. PanTS-only training can proceed independently. |
| 4 — Oct 26–Nov 1 | Reproducible prepared inputs and restartable DAG | Designed, not implemented as a trusted capstone workflow. Build incrementally; do not wait until this week to connect imaging. |
| 5 — Nov 2–8 | Scored autonomous baseline and queryable retrieval prototype | No new capstone baseline yet. Early smoke/exploratory runs should precede this formal deadline. |
| 6 — Nov 9–15 | Controlled comparison, false-alarm tradeoff and retrieval metrics | Not started. Required comparison chosen from new baseline errors, with fixed factors and honest null results. |
| 7 — Nov 16–22 | Integrated review flow and stakeholder session | Existing viewer is a head start; durable review/evidence integration and session remain. |
| 8 — Nov 23–29 | Full integration, held-out evaluation, tests and documentation drafts | Future complete-system acceptance. Do not postpone all integration until this week. |
| 9 — Nov 30–Dec 6 | Protected stabilization buffer | Keep protected; defect-driven corrections only. |
| 10 — Dec 7–13 | Delivery and presentation | Keep protected; no result-changing model selection or new features. |

The schedule is a set of outcomes, not a rule requiring plans to execute serially. Early training
is already approved as a direction in Plan 06/D-251/D-252; this review does not change Week 5/6 or
Weeks 9/10 commitments.

## What actually blocks the first real training run

1. **Qualified inputs and protected membership.** The current records deliberately permit no
   training targets. Reconcile the required source inventory, record source-protocol applicability
   and a purpose-specific local-use decision, verify geometry and label mapping, then freeze a
   small train-role cohort with exact parents and hashes. Quarantine unresolved cases; do not
   repair every anomaly as a condition of choosing usable members.
2. **An enforced loading path.** The pure guards do not automatically protect scripts/train.py.
   That historical entry point still accepts split/ID paths, and src/data/dataset.py still builds
   from a CSV and ID lists. Add a capstone cohort resolver/consumer with no arbitrary-list bypass;
   validate its real record-to-MONAI handoff.
3. **Pancreas-only preprocessing and model behavior.** Prove shared image/mask geometry, binary
   decoding, target construction without lesion supervision, cache identity, image-only full-volume
   inference and source-grid restoration. Reuse sound functions instead of rewriting everything.
4. **Run/checkpoint and resource safety.** New output destination, scratch initialization or audited
   permitted pretraining, config/code/environment/cohort identity, loss/metric sanity, save/reload and
   interruption behavior, correct mounted roots, sufficient space and one accelerator owner.
   Measure a small representative workload before setting the actual run budget.
5. **A concrete run plan and evidence closure.** Reconcile run-relevant G0/G1/Plan 05/06/09/10 checks,
   register the CAP-EXP game plan, pass the smallest end-to-end smoke, then widen. G3 is required for
   expensive baseline training; the complete orchestration product is not automatically a tiny
   smoke prerequisite. Shared Plan 04 runner/locking code still needs its explicit coding dispatch.

These are real code/integration tasks, not merely additional approval notes. The first learning
question should be: can a newly initialized pancreas-only model learn a tiny registered training
set, save/reload, and produce correctly aligned full-volume output? A provisional scope is 1–4
qualified cases and a short measured step budget. Exact members, steps, memory/time ceiling and
pass bars are intentionally not invented or registered by this review.

## One contract detail to resolve without expanding the project

The approved policy preserves every original base member and qualifies use separately. Plan 02
also asks to reproduce the full base family, while COHORT-PROTOCOL requires eligible members and
complete manifests for executable cohorts. The current diagnostic assembler marks a manifest
quarantined if it contains unresolved blocking issues anywhere. Together, these rules need an
explicit implementation distinction between the full protected-membership record and the
purpose-qualified executable training cohort.

Proposed clarification: preserve all 9,901 protected identities and original role assignments;
retain all exclusions/holds visibly; admit only qualified members to a separately frozen train
child. Define how the parent protection record and source completeness are represented, and test
that an ineligible member cannot be consumed. This is not permission to rename a partial diagnostic
manifest “complete,” silently omit validation/test identities, or weaken G1. If existing contracts
cannot express the distinction, bring the exact small amendment for Quinton's decision before
implementation. Do not make resolving every held case a hidden requirement for the entire dataset.

The approved PanTS subject fallback is already a decision, not an unanswered demand for unavailable
biological-patient proof. Known duplicates and protected-role conflicts still need their controls.
Inventory/protection metadata are separate from reading final-test images or using test outcomes.
No publisher-test extraction or model access is authorized by this regroup.

## What can wait or proceed independently

- Case 2's pilot-format adapter and further investigation of cases 2/266 while unit evidence is
  unchanged. The completed [case-2 review](../data/CASE2-RETAINED-EVIDENCE-REVIEW-2026-09-28.md)
  explains why another serialization step would still leave it untrainable.
- More case-78 adjudication, anatomy-absent robustness and unusual-case ablations until their targets
  are qualified and a relevant experiment is designed. The existing exclusion already protects
  the first pancreas-present run.
- PANORAMA integration for a PanTS-only first run; it remains committed later work.
- Literature database/corpus/response completion, UI polish, durable-review completion, stakeholder
  session, remote compute and release packaging. They have their own milestones and cannot all
  become prerequisites to first training. Claude can address P3 independently.
- Full scientific evaluator/operating-curve machinery before a wiring/learning smoke. The smoke
  still needs truthful metrics; formal baseline/comparison claims need the full relevant evaluator.
- Broad architecture rewrites, more generic record frameworks, repeated unchanged evidence scans,
  and multiplying MD files per micro-step. Use one living training-readiness checklist and retain
  immutable evidence when an actual boundary changes.

Publisher outreach is useful, but the current source review separates local research qualification
from public-release clearance. Do not assume a reply is required for every other task, and do not
claim rights/allowed uses have already been granted. Keep source/derived data private; Quinton plans
to send the drafted email himself. This review makes no new legal determination.

## Proposed next implementation block and training timing

Make the next block **“verified PanTS cohort to first saved localizer checkpoint.”** Work in these
four acceptance slices, with the existing FIRST-EXPERIMENT-READINESS checklist as the gate record:

| Slice | Concrete acceptance | Scope control |
|---|---|---|
| A. Qualify and freeze | Source/protection distinction settled; required source evidence reconciled; usable target permissions recorded; repeatable frozen tiny train child | No new case-2 adapter or exhaustive anomaly repair merely to reach the first run |
| B. Load and transform | Registered cohort resolves; incorrect role/held member/stale source rejected; selected case loads with verified target and spatial behavior | Reuse historical internals after review; no legacy CLI bypass |
| C. Learn and recover | Scratch pancreas-only path on synthetic fixtures; save/reload/interruption checks; measured MPS and storage budget | No old project weights, cloud, whole cascade or full model search required |
| D. Run and interpret | CAP-EXP plan, all relevant gates passed, bounded real localizer smoke, saved result and decision | Train-role only; an overfit/timing result is not generalization performance |

Working target: the first real localizer smoke during Week 1 (October 5–11), earlier if the checks
pass. This is a planning target, not a measured delivery forecast. Source qualification and the
cohort-consumer work are not yet sized well enough to promise a day. After slice A and a small
resource benchmark, replace this target with a measured forecast. If the gates do not fit, report
the exact remaining work and revised date rather than either waiting silently or bypassing them.

After that, begin a bounded train-development learning loop and a segmenter smoke, then assemble
the autonomous cascade and score it on development-validation. Keep PANORAMA and retrieval moving
in their separate lanes. Weeks 5/6 remain the formal baseline/comparison milestones. Broad later
experiments are useful when each answers a distinct question; quantity alone is not the goal.

## Necessary work versus overbuilding: recommendation

Keep identity/leakage, geometry/target validity, no-old-checkpoint lineage, exact run records and
checkpoint safety. The project has concrete historical failures in these areas. Reduce serial
paperwork, anomaly follow-up with no new evidence, and premature completion of unrelated product
components. A passing “load → learn → save → reload → full-volume prediction” should become the next
headline, with documentation recording that evidence rather than replacing it.

No training, raw-source reads, code change, installation or model selection occurred in this review.
No new approval of Plan 04, cohort-policy amendment or execution budget is inferred. The next action
is the requested regroup with Quinton around this concrete training-first block.
