# Week 1 — architecture and test planning

**Status:** Active  
**Official week:** 2026-10-05 through 2026-10-11  
**Preparation began:** 2026-09-07; early work carries forward as completion evidence  
**Primary focus:** Architecture and test planning  
**Approved outcome:** Confirm data design, retrieval requirements, workflow DAG, UI-extension
requirements, and test strategy.

**October 6 execution reconciliation:** use the
[current development focus](WEEK-01-DEVELOPMENT-FOCUS-2026-10-06.md) and
[human-hours log](HOURS-LOG.md) for this week's live priorities and actual/provisional time.
The approved [execution queue](WEEK-01-EXECUTION-QUEUE-2026-10-06.md) now contains the delivered
invented adapter (133targeted passes), duration/data drafts and43-requirement map; hourly follow-ups
through Sunday resume only new explicitly approved scope or report changed dependencies.
The designs and early evidence below remain the planning baseline. Imaging training/export/recovery
is demonstrated, while useful contours and the autonomous cascade remain open. October 6 native
retrieval v1.2 had two failures; v1.3 passed160sizing/342retrieval native checks and the guarded
binding passed626combined checks; actual N4 APFS rehearsal remains with the existing owner.
The later SuPreM B03 metadata pass/R04 completion, source/session/keeper gates and ongoing
commit practice are recorded in the live queue; current human time is provisional4h/range3–5h.
This reconciliation closes no full-system or scientific gate.

## Week outcome

At the end of this week, the capstone should be implementation-ready without prematurely locking
tools the proposal intentionally left open. Every component will have a plan, cross-component data
contracts will be explicit, high-risk assumptions will be tested or labeled, and Week 2 cohort work
will have a binary start gate.

## Deliverables

- [x] Source-of-truth hierarchy and active documentation hub.
- [x] Master plan aligned to the approved 10-week schedule.
- [x] Initial requirements traceability, decisions, and risk register.
- [x] Repository cleanup proposal and reference-material policy.
- [x] One Markdown file for every implementation area.
- [x] System context, container/component, and data-flow diagrams.
- [x] Canonical artifact layout and run-manifest contract.
- [x] Cross-system identity/versioning plus run, case-package, prediction, and review-event schemas.
- [x] Source, subject, study, annotation, and cohort record schemas.
- [x] Tool-independent corpus, passage, query, retrieval, evidence-response, and retrieval-evaluation
      schema design; executable schemas/fixtures remain Plan 09 work.
- [x] PANORAMA identity, exclusion, label-remap, annotation-quality, and duplicate-control design.
- [x] Workflow stage graph, state model, retry/idempotency rules, and provisional tool selection;
      implementation remains gated on explicit coding authorization and the bounded spike; the
      walkthrough was accepted 2026-09-20 (D-045).
- [x] Autonomous input/output, localization, spatial-transform, model-lineage, and failure design.
- [x] Evaluation metric, failure-denominator, holdout, experiment, continuous-training, and reporting
      design; Plan 06 is approved and Plan 09 executable fixtures remain.
- [x] Retrieval corpus/rights, query/passage, question-set, vector-tool selection, response/citation,
      and refusal contracts; design approved, while executable schemas and D-202 remain gated.
- [x] UI extension inventory, wireflow, state model, adapter/persistence boundary, trust model,
      accessibility boundary, and fixture plan based on the current interface; Plan 08 is approved
      and executable contracts remain.
- [x] Approved lightweight stakeholder protocol, review tasks, outreach tracker, and findings fields;
      actual participant/session/finding evidence remains pending.
- [x] Complete testing design: environments, commands, suite taxonomy, high-risk matrix,
      fixture/oracle policy, UI/browser boundary, traceability, CI, and release evidence; Plan 09
      design approved and implementation remains gated.
- [x] Complete reproducibility/operations design: drive roles, roots, artifact publication,
      environment/run identity, retention/backup/restore, preflight/migration/reproduction, and
      local-versus-rented compute protocol; Plan 10 is approved and new-drive capability/root setup
      remains. The old drive is unusable per Quinton; fresh acquisition is the active route (D-257).
- [x] Plan 12 integration, freeze/evaluation, defect, packaging, recovery, and delivery design approved.
- [ ] Clean runnable Python/UI test environments and executable baseline suites.
- [x] First Python foundation slice: hashed clean install, 37 unchanged historical tests plus 30
      contract checks pass; see `../testing/FOUNDATION-2026-09-19.md`. UI/full G0 remain open.
- [x] Focused design/prerequisite review: all twelve approvals and bounded execution gates recorded
      in `../IMPLEMENTATION-START.md`; full executable readiness remains pending.

## Planning blocks

The order matters because later plans depend on earlier identities and contracts.

### Block 1 — establish governance and baseline health

- Verify proposal/appendix hierarchy and prior/new boundary.
- Classify active versus historical documents.
- Capture current repository and test-environment hazards.
- Define plan, decision, risk, and traceability update rules.

**Exit:** A future session cannot accidentally use an old schedule or obsolete database/NLP plan.

### Block 2 — define the system and artifact contracts

- Draw system context and component boundaries.
- Define immutable sources, derived artifacts, naming/versioning, checksums, and completion markers.
- Define common identifiers used across imaging, retrieval, UI, and review events.
- Specify what is file-first and what could justify a later database.

**Exit:** Every stage has a named input, output, owner, schema, and invalidation rule.

### Block 3 — eliminate data and scientific ambiguity

- Define subject/study/case identity and protected cohorts.
- Specify PANORAMA mapping, provenance, exclusions, overlap checks, and annotation-quality strata.
- Define autonomous versus provided-region evaluation and multi-lesion-safe processing.
- Specify golden metric fixtures and operating-point reporting.

**Exit:** No training run can begin with ambiguous identity, labels, or metrics.

### Block 4 — design orchestration and operations

- Enumerate DAG stages and dependency graph.
- Define idempotency, retry, partial-run quarantine, resume, logging, and artifact lineage.
- Benchmark requirements for local versus rented compute decisions.
- Select the smallest orchestration approach that passes the requirements.

**Exit:** An injected mid-run failure has a documented and testable recovery path.

### Block 5 — define retrieval, UI, and stakeholder workflow

- Freeze the initial literature corpus boundary and evaluation-set construction method.
- Define structured finding → query → passages → cited response/refusal contracts.
- Map existing UI behavior to the approved review flow.
- Produce wireframes/data states before implementing presentation changes.
- Write realistic stakeholder tasks and questions.

**Exit:** The UI and retrieval layers can be built independently against stable fixtures.

### Block 6 — adversarial review and readiness decision

- Walk every approved requirement through traceability.
- Challenge each plan using its failure-mode table.
- Verify schedule and critical path; protect Weeks 9–10.
- Mark plans Ready, Draft, or Blocked with reasons.
- Produce the exact Week 2 starting checklist.

**Exit:** G0-design passes or its blockers are named. G0-verification then requires clean environment,
baseline, and contract/fast-test evidence; design approval alone does not satisfy full G0.

## Time budget

Spending up to roughly 50 focused hours is acceptable. A suggested distribution is:

| Area | Approximate hours |
|---|---:|
| Governance, audit, and repository structure | 6–8 |
| Architecture and artifact/data contracts | 10–12 |
| Cohorts and PANORAMA integration design | 8–10 |
| Autonomous workflow, metrics, and experimentation design | 8–10 |
| Retrieval, UI, and stakeholder design | 8–10 |
| Test strategy, adversarial review, and consolidation | 6–8 |

These are ceilings and planning guidance, not a requirement to consume hours after decisions are
clear.

## Questions that must be answered this week

1. What is the canonical identity key for each source, and how are multiple studies per subject
   represented?
2. Which PANORAMA annotations may enter the primary training comparison, and how is source quality
   visible?
3. What exact artifacts cross every stage boundary?
4. What makes a DAG run restartable and safe after partial failure?
5. What information is forbidden from autonomous inference?
6. What post-processing and metric conventions preserve multiple lesions and match the intended
   scientific comparison?
7. What corpus material may be stored and retrieved, and how is every passage cited?
8. How is the retrieval evaluation set frozen before tuning?
9. What reviewer action does `edit` mean if browser contour editing is not committed?
10. Which UI changes are necessary for the approved workflow versus presentation stretch?
11. What evidence would justify a database, managed vector store, or rented compute?
12. What single command proves the test environment is ready?

## Week 1 acceptance gate

- [ ] All twelve component plans meet the Definition of Ready or state a bounded blocker.
- [ ] Every requirement has a plan, artifact, and verification method.
- [ ] All High-impact risks have preventive controls and contingencies.
- [ ] No active document conflicts with the approved proposal or appendix.
- [ ] Test dependencies install in the documented environment and the baseline suite runs.
- [ ] Week 2 data/cohort plan is Ready.
- [ ] Quinton reviews the architecture, major decisions, UI wireflow, and Week 2 gate before code
      proceeds.

September 18: all component designs are approved and the focused prerequisite review is complete.
Bounded foundation setup can now produce G0-verification evidence. Full G0 and real-data gates are
still pending; the two historical CPU diagnostic scripts passing 13 tests do not replace them.

## Daily record template

At the end of each planning session, add:

- decisions made and evidence;
- questions still open;
- risks added/changed;
- documents promoted toward Ready;
- time spent and next starting point.

Do not use this file as an unstructured diary. Material detail belongs in the relevant component
plan; this page records progress and readiness.
