# Pre-course completeness review: what belongs before October 5

**Status:** Planning assessment, not gate closure. **Date:** September 28, 2026.
**Owner:** Quinton Evans; prepared by Codex. This accompanies the
[detailed training plan](TRAINING-READINESS-IMPLEMENTATION-PLAN-2026-09-28.md).

## Judgment

Prioritizing a qualified first localizer smoke is appropriate. It advances the proposal's central
imaging problem and exposes practical constraints early. It is an ambitious pre-course engineering
target, not an approved proposal requirement to finish a trained system before Week 1. Readiness by
October 2 and review by October 4 remain conditional on source/cohort evidence and available time.

The main addition is not another product feature: it is making source completeness, protected
membership and executable eligibility precise, then demonstrating recovery and preserving evidence.
Do not require every capstone component before starting, or mistake one smoke for completed Plans 02/05.

## Sources and authority reviewed

| Source | Relevance and interpretation |
|---|---|
| Approved proposal v3.8, sections 6–9; technical appendix v3.1 | Autonomous imaging, multi-source controls, model experimentation, literature support, review workflow, tests and reproducibility; committed system by Week 8, protected Weeks 9/10 |
| MASTER-PLAN, REQUIREMENTS-TRACEABILITY and twelve component plans | Continuous training after applicable gates; calendar weeks describe milestones, not a ban on earlier experiments |
| IMPLEMENTATION-START and weeks/WEEK-01 | G0 design versus executable verification; experiment-strategy discussion before training; older setup status must be reconciled with later evidence |
| Plans 02/05/06 and COHORT-PROTOCOL | Protected ancestry, source/mapping qualification, new model lineage, tiny fixtures before baseline; no arbitrary historical ID files |
| Plans 04/09/10 and operations policies | Separate workflow coding authorization; tested environment, publication/recovery, resource budgeting and independent artifact preservation |
| Plan 07 PHASES and current P3 review | Pre-Oct4 front-loading includes P0–P2/P3; installations and acquisition depend on explicit approvals; P3 accepted, P2 still pending |
| Plans 08/11/12 | Interface and stakeholder milestones later; incremental integration now, complete reproduction/release later |
| CURRENT-CHECKPOINT, DEVELOPMENT-REGROUP, PRECOURSE-TRAINING-WEEK | Latest evidence supersedes accumulated historical checkpoint prose |

Approved proposal SHA-256: `00546c805f0f49df2bf11cf452dc29171ede49e6931f23f5186562e39e613612`.
Approved appendix SHA-256: `6c26f2ae2652c32c0fa444cc10bc608ae4a81aab5c7970c294ce4f031f2b64e3`.
The repository also contains later drafts; they do not replace approved authority. Subsequent explicit
decisions, including literature-only PostgreSQL/pgvector D-260–D-265, amend the implementation baseline.

This is a repository/approved-document review, not verification of the course portal. Assignment
formats, exact due times and any pre-course work remain for Quinton to confirm. No new deadline is
inferred from old five-week project documents or the September planning calendar.

## What should be covered before Week 1

| Item | Current evidence | Action / owner | Blocks first smoke? |
|---|---|---|---|
| Scope and experiment strategy | Twelve designs approved; localizer-first sequence proposed | Quinton/Codex agree smallest question, scope and next decision | Yes, exact run plan |
| G0 evidence reconciliation | Python foundation and later native 813-pass result; Node24 bounded UI build/unit/browser evidence | Codex map actual evidence to master G0, run only missing/invalidated checks | Yes, full applicable G0 requirements |
| Source/protection/qualification contract | Counts pinned; diagnostic annotations remain held; contract gap identified | Quinton/Codex review linked proposal, then implement and verify | Yes |
| Frozen cohort, loader, transforms, scratch/run/recovery | Partial reusable foundations; no qualified production path | Codex follow detailed Phases B–E | Yes |
| Storage and backup | D-258 scoped setup and synthetic restore; no actual trained keeper yet | Codex recheck registered roots/headroom, fixture restore before run and actual keeper after | Yes, relevant controls; actual keeper preservation follows run |
| New work checkpoint | Earlier reviewed snapshot pushed; newer work remains uncommitted | Review concrete permitted diff, then approved commit/push; protect ignored evidence separately | Code identity required; dirty captured smoke permitted, formal run requires clean revision |
| Literature next step | P1 frozen and P3 synthetic accepted; P2 seed/protocol review pending | Quinton dispatch Claude's bounded P2 when desired; reserve author review time | No imaging dependency |
| Literature infrastructure/acquisition | P4a/P4b/P5 separately gated | Only proceed under their own approvals, no pressure to finish all before Oct5 | No |
| Course expectations and progress reporting | Proposal approved; current assignment details unverified | Quinton confirm actual pre-work; reconcile technical status and professor-facing work log with real effort | Not a technical gate; genuine course deadlines take priority |
| Stakeholder/outreach | Radiologist contacted; current confirmation/session pending | Quinton owns outreach; retain role/status. Fallback by Week5, main review Week7 | No; do not invent a pre-course session requirement |
| Publisher questions | Sendable draft exists; Quinton plans to send in a few days | Quinton sends when ready; keep unit/release holds unless evidence changes | Relevant source-use evidence may block affected cases; email receipt itself is not a universal prerequisite |
| Security/environment debt | Earlier UI advisories recorded; browser test uses synthetic viewer stub | Keep tracked; triage applicability before exposed services/demo. No broad dependency upgrade in this plan | Relevant runtime defect can block; unrelated UI completion does not |
| Week1 queue and requirements reconciliation | Extensive design work already done | Codex/Quinton map evidence to commitments and choose next experiments Sunday | Planning deliverable, not a reason to delay an otherwise ready run |

No additional required pre-October5 product milestone was found in the approved proposal. The
pre-course literature schedule is front-loaded capacity, not authorization to install or acquire.
P2 work should remain visible so imaging focus does not quietly erase the retrieval authoring burden.
Reserve later time for Quinton's 60-question evaluation set and labeling; do not expose held-out items
to implementation agents or public Git.

## Position against the ten-week plan

| Week / dates | Committed milestone | Position and implication of this week's work |
|---|---|---|
| 1: Oct5–11 | Approved architecture, acceptance criteria, workflow and test plan | Much design is already approved; reconcile executable G0 and remaining decisions. Continue measured imaging experiments when ready |
| 2: Oct12–18 | Frozen cohorts and separation/repeatability tests | Partial implementation. A tiny descendant proves the path, not qualification of all intended training/evaluation cohorts |
| 3: Oct19–25 | PANORAMA mapping, provenance, exclusions and duplicates | Acquisition evidence exists; integration still owed. G2 is not a PanTS-only smoke prerequisite |
| 4: Oct26–Nov1 | Tested restartable preprocessing/workflow DAG | First-run controls are a bounded slice; full DAG/tool selection and restart coverage still owed |
| 5: Nov2–8 | Autonomous baseline, errors and queryable retrieval prototype | Tiny localizer is an enabling experiment. Still need segmenter, predicted ROI/cascade and training-disjoint development evaluation |
| 6: Nov9–15 | Controlled comparison, operating tradeoffs and retrieval metrics | Select comparison from new baseline evidence; broad experiment intent does not justify unfrozen comparisons |
| 7: Nov16–22 | Integrated review interface and stakeholder feedback | Existing UI is a starting point; durable review, real artifacts and feedback remain |
| 8: Nov23–29 | Full integration/tests, frozen held-out evaluation and documentation | Preserve final-test boundary and build evidence incrementally now |
| 9: Nov30–Dec6 | Buffer and stabilization | No planned new model/product scope |
| 10: Dec7–13 | Packaging, rehearsal and delivery | No result-changing training or new features |

“Held-out baseline” in Week5 means the current Plan05/06 train-disjoint development protocol; it is
not permission to repeatedly inspect publisher test. Prior-project evaluation exposure remains disclosed.
A percentage-complete estimate would be misleading: design progress is substantial; capstone imaging
execution is still at its first qualified-input/run boundary.

## Priorities and capacity

First priority is Phases A/B: contract decision, required source reconciliation and positive target
qualification. Next are consumer/geometry and synthetic training/recovery. Keep the Friday launch
conditional; use the weekend for inspection/recovery instead of assuming all implementation can slip
there. If Tuesday cannot demonstrate a qualifying path, revise the estimate then.

Defer from this first-smoke critical path: case-2 format bridging, more unchanged unit investigation,
all-label voxel surveys, PANORAMA mixing, UI polish, database installation, broad model searches,
cloud rental and matched ordinary/unusual robustness experiments. Some remain committed later work.
Neither publisher delay nor a held unusual case should trigger an unsupported eligibility exception.

Hands-on availability is unknown. Before treating this as a commitment, add Quinton's available
review blocks and any actual course pre-work. If time is short, protect correctness, source controls
and evidence; reduce first-run size after recording a new plan, not the scientific safeguards.

## Sunday handoff checklist

- [ ] Current readiness row status and exact remaining blockers, with owners/next checks.
- [ ] Frozen cohort and completed attempt evidence, or an honest explanation of which are absent.
- [ ] Learning/alignment/recovery outcomes reported separately; no generalization claim.
- [ ] Measured throughput and budget for the next experiment, with contingency.
- [ ] Reviewed code/docs and independently preserved irreplaceable artifacts.
- [ ] Living experiment notebook and current checkpoint updated; progress/work logs reconciled.
- [ ] Week1 priorities mapped to proposal, including remaining data/workflow and retrieval work.
- [ ] Actual course deadlines confirmed and stakeholder/publisher status accurately retained.

This review changes planning/navigation only. It closes no G-gate, grants no eligibility, registers no
experiment and starts no Claude phase. The next conversation is the concrete membership/eligibility
proposal, followed by the bounded implementation packet after decisions are recorded.
