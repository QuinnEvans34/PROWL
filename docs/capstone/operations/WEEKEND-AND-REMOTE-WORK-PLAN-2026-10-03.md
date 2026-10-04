# Weekend and remote-work queue — October 3, 2026

**Later October 3 settlement:** Quinton authorized the [local preservation commit](PRESERVATION-COMMIT-2026-10-03.md)
and [Monday wording](COURSE-START-SUMMARY-2026-10-05.md). The separate
[Plan07 support handback](../retrieval/CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md) completed
L1 decision reconciliation and prepared L2/L3/L4/L6 documents. R-06 now starts from those concrete
S1/S2/integration choices rather than drafting them again. A subsequent Claude log records separate
S1/S2, cleanup/integration decisions and cloud S2 dispatch; do not overwrite or redispatch that lane.
Public push, work beyond this local checkpoint and
R-03–R-05/R-07 remain separate decisions. Earlier proposed-session wording below is preserved.


Prepared during Quinton's approved repository-checkpoint review. He has a couple of focused hours
Saturday evening, two or three focused hours Sunday, intermittent phone access Sunday, and a laptop
available at home during the school week. Phone availability is asynchronous; it is not continuous
review attention. These are capacity assumptions and proposed work blocks, not recorded working hours.

## Current dispatch and priorities

The repository review, its verification, R-01 portability repair and R-02 Monday account are authorized. Quinton dispatched the latter two by asking Codex to continue the recommended review and necessary work. D-335 remains
the latest experiment decision. No experiment, source job, Git commit/push, Claude phase, database
installation, orchestration spike, automation, or unattended work loop is dispatched by this queue.
Quinton initially confirmed no newer Claude work and asked to include the accepted P3 handback. Newer October 3 planning records subsequently arrived during review; see RETRIEVAL-HANDBACK-REVIEW-2026-10-03.md in
the checkpoint proposal. Claude retains ownership of retrieval implementation.

The [checkpoint review](GIT-CHECKPOINT-REVIEW-2026-10-03.md) found a practical first coding question:
the populated native workspace passes all 2,933 tests, but a clean file export cannot collect the
suite because some tests depend on ignored local evidence. Recommend resolving that portability
boundary before approving public publication. This is separate from model quality.

## Suggested focused sessions

| Session | Proposed use of available attention | Concrete finish line |
|---|---|---|
| Saturday evening, remaining time | 20–30 minutes reviewing the checkpoint findings; 20–30 minutes agreeing the fixture-repair scope and Monday message; remaining time for a separately dispatched bounded task | Decide whether the checkpoint is preservation-only or should first gain portable fast tests; agree the first remote task |
| Sunday, 2–3 focused hours | 30 minutes reviewing any fixture handback; 30 minutes preparing the Monday account and actual course deadlines; 45–60 minutes discussing the duration/coverage proposal; 15–30 minutes reconciling product/retrieval dependencies | Reviewed Monday summary, ranked Week 1 queue, and one concrete next imaging question |
| Sunday phone intervals | Start a named approved packet, read its short handback later, and supply decisions needed for the next packet | Progress without requiring immediate replies or keeping a long approval chain active |
| Weekdays at school | Run one agreed packet at a time on the existing laptop/checkout; review the handback when available | A completed bounded artifact or a specific unresolved decision, with no automatic scope expansion |

These are planning estimates. Revise after actual course assignments and review availability are
known. Agent runtime is not Quinton's study time. A completed experiment or useful contour is not a
guaranteed Week 1 outcome.

Tentative daily order for October 5–9: Monday, the course-start account and evidence/requirement
reconciliation; Tuesday, the duration packet; Wednesday, ROI-containment and varied-cohort packets;
Thursday, the literature decisions and bounded DAG/UI implementation packets; Friday, review the
week's actual evidence, remaining blockers and the Week 2 starting queue. R-01 takes precedence
until the portable-test boundary is settled. Move unfinished packets forward without assuming an
experiment or implementation has been approved just because its proposed day arrived.

## Proposed finite packets

| ID / priority | Allowed work and initial boundaries | Deliverable / verification | Needs before execution |
|---|---|---|---|
| R-01 / first | Design and then repair fast-test portability in `tests/test_audit_assessment_link.py`, `tests/test_segmenter_cache_qualification.py`, `tests/segmenter_short_fixtures.py`, `tests/segmenter_v5_fixtures.py`, `tests/test_segmenter_v5_boundaries.py`, new test-owned fixtures, and any explicitly reviewed marker configuration | Fast tests collect and run without ignored evidence; existing failure/role/coverage assertions survive; retained-real regressions stay available in an explicitly selected evidence suite; original evidence and D-335 pins remain preserved in their sealed snapshots | Agree the fixture-versus-retained-evidence boundary. Inspect transitive test consumers before finalizing the allowlist. Do not change production consumers merely to make tests pass |
| R-02 / draft completed October 3 | Read approved requirements, current evidence and Week 1 records; draft a one-page course-start account in `docs/capstone/operations/` | Clear research question, demonstrated work, weak/null results, remaining commitments and next task; no gate closure based on test count | Quinton supplies actual assignments/due times when known; otherwise label them unverified |
| R-03 / Week 1 imaging | Prepare a fresh same-cohort segmenter duration proposal in operations/evaluation documentation | Hypothesis, controlled recipe, proposed duration/cadence, terminal-primary endpoint, per-case pancreas/lesion/component coverage, FP volume/precision, stop rules, and incremental primary/keeper/restore/control budget | Discuss consequential experiment choices. Preparation cannot launch, extend CAP-EXP-014, import weights, or use 2514 for selection |
| R-04 / Week 1 autonomy | Specify the boundary from retained localizer predictions to segmenter inputs; use existing numeric evidence first | ROI/transform/export contract, containment and failure accounting, and the exact next zero-update qualification packet | Any new model forward, target read, cleanup adoption or cascade execution needs its own concrete scope. Provided-region and predicted-region evidence remain distinct |
| R-05 / Week 1 data | Inventory existing multiclass/negative evidence and propose varied role-separated descendants | Qualification coverage/gaps, retained tiny/boundary cases and holds, verified-negative requirements and separate development evaluation | No new source reads, membership publication, refill, reinterpretation of empty labels, or publisher-test use implied |
| R-06 / parallel literature | Codex reviews the latest handed-back records and prepares a concise decision list for Quinton; Claude performs separately dispatched lane work | Latest October 3 handoff/record reconciliation, S1 storage-prerequisite and S2 sizing-packet plans, integration options and acceptance requirements | Claude owns its planning and implementation; Codex review does not gate that planning. Accepted P3 remains synthetic; no automatic sizing/P4/P5 dispatch, acquisition, service installation or external messaging |
| R-07 / integration planning | Bound the Plan 04 spike and real-artifact/UI adapter tasks in their existing plans | Exact allowed paths, prerequisites, checks, artifacts and human-review boundary for each task | Plan 04 coding/spike authorization and the relevant UI implementation gates remain separate |

R-01 is complete: [portable test results](TEST-PORTABILITY-RESULTS-2026-10-03.md) record
2,933 fast passes in an export without local outputs/registry and eight additional local-evidence
checks passed. The transitive review added candidate, native-scoring, localizer ancestry and storage
refusal tests to the initial allowlist; production consumers and retrieval files stayed unchanged.
Seven current D-335-pinned test files differ, while their historical sealed sources remain preserved.
Future experiments must qualify their actual sources separately.

R-02 produced [Monday's course-start account](COURSE-START-SUMMARY-2026-10-05.md).
Quinton reviews its wording and checks the actual course assignment/due time. It is not submitted
or sent anywhere. R-03 through R-07 remain proposals requiring their stated scope decisions.
The refreshed repository proposal is [V2](GIT-CHECKPOINT-REVIEW-V2-2026-10-03.md); Git publication
remains a separate decision.

## Remote execution agreement to adopt

Use the same authoritative checkout. A packet states the objective, allowed paths, exclusions,
verification command, expected output and stop point. Give the agent enough scope to finish it
without routine micro-approvals. Once dispatched, it may read, edit and verify within that scope,
then produce a handback and stop at its finish line.

If a consequential choice or missing authority blocks one part, preserve the evidence, describe
the specific decision, and continue independent work already authorized in that packet. An absent
phone reply does not grant permission. Do not turn a completed packet into a recurring monitor or
start the next experiment, acquisition, installation, publication or agent lane automatically.

Keep one accelerator/storage writer owner. Avoid concurrent sessions editing the same source or
shared decisions. Laptop availability alone does not verify AC power, mounts, free space, resource
limits or approval for unattended training. Each later approved run still needs its exact preflight
and supervision policy; this plan changes none of those requirements.

Every handback should fit a phone screen before linking detail:

1. Outcome and whether the packet finished.
2. Files changed and verification result.
3. Any decision needed, with the concrete options and recommendation.
4. Exact next starting point; no inferred follow-on dispatch.

Suggested start message after a packet's scope is agreed:

> Execute R-XX from WEEKEND-AND-REMOTE-WORK-PLAN-2026-10-03.md within its agreed allowlist.
> Verify the checkout, preserve existing changes/evidence, complete its stated checks, and leave
> a concise handback. Stop at its finish line or at a consequential decision outside its scope.

## Week 1 finish lines and protections

Minimum proposed commitment: reviewed repository preservation, an accurate Monday account,
portable-test repair or a precise retained blocker, and a reviewable next imaging packet. Additional
implementation depends on the packet review and actual available attention.

Keep PANORAMA, the full DAG, varied multiclass data, literature and durable reviewer interaction in
the weekly queue. Reconcile existing acceptance evidence rather than repeating all pre-course
planning. Protect Week 8 integration/evaluation, Week 9 stabilization and Week 10 delivery. Quinton
owns publisher/stakeholder outreach; no contact occurs through this plan.
