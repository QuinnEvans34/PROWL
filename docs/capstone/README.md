# PROWL capstone documentation hub

**Weekly execution:** [Week1 living work plan](weeks/WEEK-01-WORK-PLAN.md) is the October8
task/specification and closeout overlay. Follow the [Sunday planning routine](weeks/README.md)
and [weekly template](weeks/WEEKLY-WORK-PLAN-TEMPLATE.md) for subsequent weeks. Older status
snapshots below need reconciliation as specified in that plan.

Current execution/ownership summary: [CURRENT-CHECKPOINT](operations/CURRENT-CHECKPOINT.md).
Read it before older status prose below. The latest approved database amendment is
[D-260](operations/POSTGRES-PGVECTOR-DECISION-2026-09-28.md), supplemented by D-261–D-265.
Plan 07 reconciliation and P1 freeze are complete; Quinton confirmed Claude is working on P3.
Historical download/test counts below are not live status.

**Project:** Pancreatic Review and Outlining Workflow for Lesions (PROWL)  
**Status:** All twelve designs approved; scoped Python/storage and UI build/synthetic checks passed; archives acquired; source validation/full G0 pending  
**Planning baseline date:** 2026-09-07  
**Official course start:** 2026-10-05 (confirmed by Quinton on 2026-09-18)  
**Owner:** Quinton Evans

This directory is the active navigation layer for the capstone. It converts the approved proposal
and technical appendix into implementation plans, decision gates, tests, and completion evidence.
It does not erase the earlier project's history.

## Source-of-truth hierarchy

When two documents disagree, use the first applicable source in this list:

1. `Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx` — approved purpose, scope, and schedule.
2. `Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx` — approved technical boundaries,
   data facts, evaluation requirements, and fallbacks.
3. [`MASTER-PLAN.md`](MASTER-PLAN.md) and [`DECISIONS.md`](DECISIONS.md) — current execution choices
   made within the approved boundaries.
4. The implementation plan for the component being changed.
5. [`../experiments.md`](../experiments.md) — living experiment plans, outcomes, and next-step
   reasoning linked to immutable evidence; prior technical documents and completed deliverables —
   historical context, not automatic capstone commitments.
6. Superseded proposal drafts and exploratory notes — provenance only.

The approved filenames and integrity hashes are cataloged in
[`../../references/governance/APPROVED-SOURCES.md`](../../references/governance/APPROVED-SOURCES.md).

The approved appendix is intentionally technology-flexible. A relational database, managed vector
service, cloud platform, or particular model architecture is not required until a measured need and
recorded decision justify it.

## Active documents

Latest execution checkpoint: [September 20 reconciliation](operations/STATUS-2026-09-20.md).
The drive is unavailable during away-from-home work. Download completion is not source readiness.
[Notion progress hub](https://app.notion.com/p/3e1171a9314081ba9ae0fea8ea1df67c) holds tasks and work logs;
technical authority remains here. [UI foundation evidence](testing/UI-FOUNDATION-2026-09-20.md)
now records the bounded build/unit/synthetic-browser slice and its limitations.
[Contract/metric foundation](testing/CONTRACT-METRICS-2026-09-20.md) adds 42 checks for a total of
147 passing Python tests; full cross-record and evaluation qualification remain open.
Plan 04 walkthrough accepted September 20; Prefect remains provisional pending its trial and coding
authorization is separate. Stakeholder preparation is deferred at Quinton's request until a
participant is confirmed or he asks for help; radiologist contacted, reply pending (September 20).

| Document | Purpose | Status |
|---|---|---|
| [`operations/WORKSPACE-SAFETY.md`](operations/WORKSPACE-SAFETY.md) | Shared agent rules for checkout identity, missing paths, configuration, and duplicate cleanup | Approved working agreement |
| [`operations/WORKSPACE-INVENTORY-2026-09-20.md`](operations/WORKSPACE-INVENTORY-2026-09-20.md) | Bounded read-only old/new location comparison and database preservation warning | Audit snapshot; no cleanup authorized |
| [`operations/RELOCATION-2026-09-20.md`](operations/RELOCATION-2026-09-20.md) | Renamed checkout, rebuilt environment, workspace sanity check, and verification | Repository fixes verified; app folder selection remains manual |
| [`MASTER-PLAN.md`](MASTER-PLAN.md) | Governing scope, workstreams, milestones, gates, and 10-week execution | Active |
| [`IMPLEMENTATION-START.md`](IMPLEMENTATION-START.md) | Focused prerequisite review, scoped G0 checkpoints, current diagnostics, first implementation slice, and training-start strategy | Current implementation handoff |
| [`testing/FOUNDATION-2026-09-19.md`](testing/FOUNDATION-2026-09-19.md) | Clean Python environment, 37 unchanged + 30 contract tests, classifications, evidence, and remaining limits | First slice verified; not full G0 |
| [`operations/STORAGE-SETUP-2026-09-19.md`](operations/STORAGE-SETUP-2026-09-19.md) | Approved roots, bounded filesystem/restore checks, 87 fast tests, and first acquisition evidence | Scoped checks passed; not full G0/source readiness |
| [`operations/OVERNIGHT-ACQUISITION-2026-09-19.md`](operations/OVERNIGHT-ACQUISITION-2026-09-19.md) | Historical queue-start evidence, 101-test checkpoint, resume commands, literature prerequisites | September 19 snapshot; completion recorded September 20 |
| [`operations/DATA-ACQUISITION-QUEUE.md`](operations/DATA-ACQUISITION-QUEUE.md) | Fresh PanTS/PANORAMA acquisition and remaining validation prerequisites | Archives complete; extraction and source readiness pending |
| [`RESTART-2026-09-18.md`](RESTART-2026-09-18.md) | Return-from-break status, drive findings, and planning reconciliation | September 18 history; see implementation handoff for current progress |
| [`REQUIREMENTS-TRACEABILITY.md`](REQUIREMENTS-TRACEABILITY.md) | Maps each approved commitment to an artifact and verification method | Active |
| [`DECISIONS.md`](DECISIONS.md) | Locked, provisional, open, deferred, and superseded decisions | Active |
| [`RISK-REGISTER.md`](RISK-REGISTER.md) | Risks, triggers, mitigations, contingencies, and review cadence | Active |
| [`DOCUMENTATION-STANDARD.md`](DOCUMENTATION-STANDARD.md) | Definition of an implementation-ready plan and update protocol | Active |
| [`REPO-CLEANUP-PLAN.md`](REPO-CLEANUP-PLAN.md) | Non-destructive proposal for reorganizing the repository | Proposed |
| [`architecture/README.md`](architecture/README.md) | Current-state and target architecture views | Active baseline |
| [`contracts/README.md`](contracts/README.md) | Shared identity, storage, run, case-package, and review-event contracts | Active baseline |
| [`data/README.md`](data/README.md) | Plan 02 inventory, data dictionary, and protected-cohort protocol | Active baseline |
| [`orchestration/README.md`](orchestration/README.md) | Plan 04 DAG, stage, state/recovery, and tool-selection design | Walkthrough accepted; coding authorization and tool selection pending |
| [`imaging/README.md`](imaging/README.md) | Plan 05 autonomous input, localization, spatial, lineage, and failure design | Approved design; dependencies remain |
| [`evaluation/README.md`](evaluation/README.md) | Plan 06 metrics, holdouts, experiments, continuous training, and reporting design | Approved design; dependencies remain |
| [`../experiments.md`](../experiments.md) | Living notebook: pre-run game plans, every attempt/outcome, and evidence-linked follow-ups | Active; historical record preserved |
| [`retrieval/README.md`](retrieval/README.md) | Plan 07 corpus, rights, query, vector retrieval, evaluation, and grounded-response design | Approved design; dependencies remain |
| [`interface/README.md`](interface/README.md) | Plan 08 current UI, wireflow, adapters, review persistence, trust, accessibility, and fixtures | Approved design; dependencies remain |
| [`testing/README.md`](testing/README.md) | Plan 09 environments, suites, fixtures/oracles, traceability, CI, and test evidence | Approved design; dependencies remain |
| [`operations/README.md`](operations/README.md) | Plan 10 storage roots, environments, backup/recovery, preflight/migration, reproduction, and compute decision | Scoped storage/Python checks passed; full operational qualification pending |
| [`implementation/11-stakeholder-validation.md`](implementation/11-stakeholder-validation.md) | Living outreach status, task script, session notes, findings, and approved revisions | Approved design; scheduling/session pending |
| [`weeks/WEEK-01.md`](weeks/WEEK-01.md) | Architecture-and-test-planning sprint for the current week | Active |
| [`implementation/README.md`](implementation/README.md) | Index of component implementation plans | Active |

## Implementation-plan sequence

| Order | Component | Approved week(s) | Planning status |
|---:|---|---:|---|
| 1 | [System architecture and contracts](implementation/01-system-architecture.md) | 1 | Ready |
| 2 | [Data inventory, identity, and protected cohorts](implementation/02-data-and-cohorts.md) | 1–2 | Ready |
| 3 | [PANORAMA integration](implementation/03-panorama-integration.md) | 3 | Ready |
| 4 | [Workflow orchestration](implementation/04-workflow-orchestration.md) | 1, 4 | Approved design; gated |
| 5 | [Autonomous imaging workflow](implementation/05-autonomous-imaging.md) | 5 | Approved design; gated |
| 6 | [Evaluation and model experimentation](implementation/06-evaluation-and-model-experimentation.md) | 5–6 and continuous lane | Approved design; gated |
| 7 | [Literature retrieval and grounded response](implementation/07-literature-retrieval.md) | 1, 5–6 | Approved design; gated |
| 8 | [Review interface and recorded decisions](implementation/08-review-interface.md) | 1, 7 | Approved design; gated |
| 9 | [Testing and quality strategy](implementation/09-testing-and-quality.md) | 1–9 | Approved design; gated |
| 10 | [Reproducibility, storage, and compute](implementation/10-reproducibility-and-operations.md) | 1–9 | Approved design; gated |
| 11 | [Stakeholder validation](implementation/11-stakeholder-validation.md) | 1, 7 | Approved design; session pending |
| 12 | [Integration, stabilization, and delivery](implementation/12-integration-and-delivery.md) | 8–10 | Approved design; execution gated |

`Draft` means the purpose, boundaries, dependencies, hazards, and acceptance gate are recorded, but
Week 1 review may still refine implementation details. `Approved design; gated` means Quinton has
approved the design, but a named prerequisite still forbids implementation. No plan becomes `Ready`
while a choice or prerequisite that could materially change its architecture remains unresolved.

## Standard working protocol

For every implementation:

1. Open this hub and the next component plan.
2. Confirm the scoped task is `Ready` and its dependencies are satisfied. G0-design permits the
   bounded environment/fixture/test foundation needed to pass G0-verification; it does not declare
   every component or real-data operation ready.
3. Resolve or explicitly defer every blocking decision in `DECISIONS.md`.
4. Create or update tests alongside the implementation, using the plan's test matrix.
5. Produce the listed artifacts and evidence; do not substitute an informal demonstration.
6. Verify the acceptance gate and update traceability, risks, decisions, and the weekly record.
7. Mark the plan `Complete` only when verification evidence is linked.

For every experiment, also use [`../experiments.md`](../experiments.md): write the plan before
execution, link every run/attempt and its outcome, then explain the evidence-based next experiment
or stop/defer decision. Historical future ideas require current capstone review, not blind replay.

This creates the workflow Quinton requested: finish one implementation, open the next Markdown file,
and have its rationale, sequence, tests, fallbacks, and finish line already available.

## What older documents mean now

- `docs/capstone-planning.md` is a research notebook. It contains important measurements alongside
  ideas later rejected by evidence or removed from the approved scope.
- `docs/capstone-architecture.md` is a useful contract study, but its mandatory Postgres design is
  superseded by the approved appendix's file-first boundary.
- `docs/architecture.md`, `docs/training.md`, `docs/data-pipeline.md`, and
  `docs/implementation-plan.md` describe the completed five-week project.
- `docs/ui-refactor-plan.md` contains deep UI design work. The capstone UI plan will reuse only the
  portions needed to extend the existing interface and complete the approved review workflow.
- `docs/SUBMISSION-READINESS.md` records real metric hazards. Those hazards remain actionable even
  though external Johns Hopkins submission is not a committed capstone deliverable.

## Immediate next move

All twelve designs are approved. Follow [the implementation-start handoff](IMPLEMENTATION-START.md)
for the remaining UI/test foundation, archive/source reconciliation, and first-training prerequisites. The
focused prerequisite review is complete; full G0 executable verification is not. Quinton's
stakeholder outreach continues independently; a confirmed radiologist meeting is not an early-
development gate. Plan 04's walkthrough is complete; explicit coding authorization is still required.
Preparation can finish before the October 5 course start. The old drive is optional; fresh pinned
source acquisition on `PROWL-Data` is the accepted recovery route. Week 9 and Week 10 stay protected.
