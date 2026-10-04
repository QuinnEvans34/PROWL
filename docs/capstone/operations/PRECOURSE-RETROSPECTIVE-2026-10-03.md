# PROWL retrospective and course-start priorities — October 3, 2026

Prepared by Codex for Quinton's requested strategy discussion. Today is Saturday, October 3;
official Week 1 begins Monday, October 5. This is an evidence review and a proposed priority order,
not approval of a new experiment, source job, installation, Claude phase, Git publication or gate closure.

## Judgment

We have exceeded the pre-course goal of getting a qualified, bounded PanTS localizer smoke run
working before class. We now have a reproducible localizer training path on 113 training and 40
development-validation cases, plus a separately qualified three-class segmenter pilot. Real training,
native-coordinate evaluation, prediction exports, interruption handling and independent checkpoint
recovery have been exercised. The latest source baseline has 2,933 native tests.

The scientific and product outcomes remain substantially less mature than the execution machinery.
The localizer still proposes oversized regions, the segmenter still produces poor contours, and the
segmenter currently receives a reference-derived pancreas ROI. That is a provided-region experiment,
not an autonomous localize-then-segment baseline. PANORAMA integration, the full workflow DAG, live
literature retrieval, durable reviewer interaction and final evaluation are still committed work.

My recommendation is to arrive Monday with preserved work, a concise account of the evidence and
one clear experimental question. A useful deployed model is not a prerequisite to starting class.
Do not consume the weekend trying to force convergence or marking whole project gates complete
because individual consumers passed. We should continue early training while protecting the rest
of the approved system and the Week 8 completion deadline.

## Authority and review scope

Reviewed the approved Word documents directly, the [master plan](../MASTER-PLAN.md),
[Week 1](../weeks/WEEK-01.md), the September 28
[pre-course completeness review](PRECOURSE-COMPLETENESS-REVIEW-2026-09-28.md), current execution
records and the latest local Claude planning log. Approved sources remain:

- Proposal v3.8: SHA-256 `00546c805f0f49df2bf11cf452dc29171ede49e6931f23f5186562e39e613612`.
- Technical Appendix v3.1: SHA-256 `6c26f2ae2652c32c0fa444cc10bc608ae4a81aab5c7970c294ce4f031f2b64e3`.

Subsequent approved decisions amend implementation details; old five-week project plans and old
checkpoint paragraphs do not replace these authorities. Course-portal assignments, exact due times
and Quinton's available hours were not verified. Confirm those separately; do not invent pre-work
requirements or report agent runtime as Quinton's working hours.

## What we have built

| Area | Demonstrated accomplishment | What it does not establish |
|---|---|---|
| Architecture and governance | Twelve component designs, versioned contracts, ownership boundaries, decisions, traceability and testing/operations plans | Every formal acceptance gate or implemented component is complete |
| Data protection and eligibility | Protected 7,200/1,800/901 base membership; permanent membership, purpose-specific permission and positively qualified frozen descendants | Every source case is usable, biological patient uniqueness is proven, or pancreas permission grants lesion permission |
| Localizer data | 176 candidates reconciled into 153 qualified members: 113 train/40 development-validation; 23 holds retained, no refill | All source data has been qualified or the development set is a final untouched test |
| Geometry and fidelity | Dedicated loaders, native inverse/export checks, 3 mm versus 2 mm target investigation and persisted 2 mm/144³ localizer path | Reference labels are infallible or all future geometry variants are covered |
| Localizer experiments | Fresh and controlled training comparisons, broad-cohort evaluation, crop/coverage accounting and retained failures | An adopted, useful autonomous ROI policy |
| Segmenter data and mechanics | Separate 6 train/1 report-only cohort, three-class targets, shared ROI geometry, cache, native scoring and tested training/recovery | Broad lesion qualification, specificity or realistic predicted-ROI performance |
| Latest segmenter experiment | CAP-EXP-014 reverses the prior complete pancreas-class collapse and passes its five declared training screens | Useful contours, generalization or model promotion |
| Operations and preservation | Bounded requests, resource measurement, checkpoints, independent keepers and cold restores; failed attempts retained | The complete workflow DAG or a published Git checkpoint of all recent work |
| Literature | P1 needs/refusal policy frozen; P3 synthetic contracts and tests accepted; P2 selection/seed planning reviewed | Frozen live corpus, operational index, measured retrieval quality or grounded end-to-end answers |
| Interface | Existing React/NiiVue starting point and scoped synthetic build/test foundation | Real new-model integration, complete-volume alignment acceptance or durable accept/edit-required/reject workflow |

The test count measures software verification coverage. It is not a model-performance score or a
percentage of the capstone complete. The 2,933-test result is the latest recorded native baseline;
this documentation-only retrospective did not rerun it.

## Scientific position

### Localization: training works; the ROI tradeoff is unresolved

[CAP-EXP-012](CAP-EXP-012-RESULTS-2026-10-01.md) used the broad 113/40 cohort. Its validation native
Dice was 0.129078 and mean recall 0.962519, but median predicted/reference volume was 14.2596×.
Only 15/40 passed the recorded ROI size/box screen, and 39/40 boxes retained at least 99.5% of the
reference. The run failed its declared usefulness endpoint, including the strict mean-recall bar;
rounding does not convert that failure to a pass. It was not adopted.

The [structure audit](LOCALIZER-STRUCTURE-AUDIT-RESULTS-2026-10-01.md) shows two problems:
small distant islands enlarge boxes, while the dominant component itself is oversized. A hypothetical
largest-component-only policy reduced average crop size, but its target containment was not measured.
Its 31/40 size-only successes are not 31 successful ROIs. Component cleanup remains a hypothesis
requiring coverage evidence, particularly for tiny or separated targets.

### Segmentation: a class-collapse repair, followed by a duration question

[CAP-EXP-014](CAP-EXP-014-RESULTS-2026-10-03.md) trained a fresh seed-42 segmenter for 48 updates
on the same six members as CAP-EXP-013, changing CE allocation/reduction to per-case present-class
mean CE. Other substantive comparison inputs stayed fixed. Terminal step 48 remained primary.

| Native macro metric | CAP-EXP-013 | CAP-EXP-014 |
|---|---:|---:|
| Training pancreas Dice | 0.000000 | 0.159877 |
| Training lesion Dice | 0.030886 | 0.055142 |
| Training lesion recall | 0.994807 | 0.833063 |
| Report-only lesion Dice | 0.025448 | 0.006397 |
| Report-only lesion recall | 0.974468 | 0.123936 |

All training lesion components were hit, but a hit only requires some overlap. Predicted training
lesion volumes remain 12.78–383.26× their references, with precision 0.0026–0.0450. The tiny case
remains included. The single report-only case, 2514, shows a substantial lesion-coverage decline and
must not select checkpoints, hyperparameters or membership. These positive cases cannot establish
negative-case specificity; empty reference masks elsewhere are not automatically trusted negatives.

Saved training loss and overlap were still improving at the final measured checkpoint. That supports
a fresh, bounded duration comparison as the next segmenter hypothesis, not an unbounded overnight
extension or a conclusion that more updates will solve false positives. Current v5 runtime remains
capped at 48; any longer version needs its own qualification, storage/resource budget, fixed endpoints
and exact launch review. No such request is currently pending.

### Lessons worth carrying into class

- Qualification must prove source meaning, units, targets and protected ancestry. File presence and
  matching grids alone were insufficient.
- Preserve original membership and difficult cases. Investigate unsupported uses; do not curate
  away tiny, noisy or boundary failures to make metrics improve.
- Measure overlap, lesion/component coverage, excess foreground and ROI containment together.
  A better Dice or smaller crop can conceal loss of the target the next stage needs.
- Physical resolution matters: the 2 mm investigation addressed small-target aliasing that was
  visible at 3 mm. Preserve the regressions as well as the gains.
- Synthetic learning and recovery checks caught real implementation/optimization risks cheaply.
  Their success does not predict real imaging accuracy.
- Loss reduction is a scientific choice: one class can disappear while another score improves.
  Numerical correctness and falling total loss alone do not prove useful multiclass learning.
- Short pilots answer bounded questions. Scale-up requires a varied multiclass cohort, separate
  development evaluation and realistic ROI conditions, not simply more updates on six positive cases.

## Position against the approved ten-week plan

Early execution carries forward as evidence. It does not mean we are already in formal Week 5 or
that every milestone before it is complete. The calendar is a milestone schedule, not a prohibition
on continuous training after applicable gates pass.

| Week / dates | Approved milestone | Current position / remaining work |
|---|---|---|
| 1: Oct 5–11 | Architecture and test planning | Design is substantially complete, with extensive executable evidence. Reconcile traceability and actual gate evidence; settle remaining implementation choices rather than restart planning |
| 2: Oct 12–18 | Protected splits and reproducible cohorts | Several frozen purpose/role descendants work. Broader multiclass qualification and unresolved identity/negative evidence remain; do not infer complete patient independence |
| 3: Oct 19–25 | PANORAMA integration | Acquisition/integrity and mapping design exist. Source reconciliation, exclusions, duplicate controls and eligible mixed-source loading still owed |
| 4: Oct 26–Nov 1 | Unified restartable workflow DAG | Tested consumers, transactions and recovery are valuable pieces. Full DAG/tool spike and end-to-end artifact rebuilding remain |
| 5: Nov 2–8 | Autonomous baseline and queryable literature prototype | Both imaging stages train separately. Predicted-ROI cascade, formal scored baseline and live retrieval prototype remain |
| 6: Nov 9–15 | Controlled comparison and operating tradeoffs | Diagnostic comparisons are underway. A defensible baseline-derived comparison, detection/specificity and retrieval evaluation remain |
| 7: Nov 16–22 | Integrated UI and stakeholder review | Existing interface and protocol provide a start. Real case/evidence adapters, durable review events and participant/session evidence remain |
| 8: Nov 23–29 | Full integration, held-out evaluation and documentation | Incremental evidence is strong. Freeze and test the committed system, apply final evaluation protocol and assemble reproducible deliverables |
| 9: Nov 30–Dec 6 | Protected buffer and stabilization | Keep available for defects and recovery; do not allocate routine new model/product scope here |
| 10: Dec 7–13 | Packaging and delivery | Rehearsal, presentation and submission; avoid result-changing late development |

The approved proposal accepts honest weak/null results. It still requires a coherent evaluated
autonomous system and reviewer workflow. Good model metrics alone would not complete the capstone.

## What should happen before Monday

The September 28 goal was training readiness by October 2 and a bounded first smoke by October 4.
That goal has been exceeded. No further required pre-October-5 product milestone was found in the
approved proposal. The remaining weekend work is consolidation and risk reduction.

| Priority | Concrete outcome | Proposed timing |
|---|---|---|
| 1. Preserve recent repository work | Inventory and review the exact code/docs/control diff; then obtain approval for a concrete Git checkpoint and publication. Retain ignored experiment evidence independently | Saturday / next bounded task |
| 2. Prepare the Monday account | One-page summary: research question, completed evidence, honest failures, next experiment and remaining system commitments. Confirm actual course assignments/due times and available hours | Saturday–Sunday |
| 3. Choose one Week 1 imaging question | Agree on a bounded segmenter duration comparison and its coverage/false-positive reporting; separately identify the next autonomous ROI evidence gap | Sunday discussion; no launch implied |
| 4. Reconcile parallel lanes | Confirm Claude's latest handback, decide the outstanding P2 policy/seed questions and identify the next authorized literature task | Sunday if available; no imaging dependency |
| 5. Move to a fresh conversation | Use the saved handoff, preserve D-335 state and start with a short priority discussion | After this retrospective |

Git preservation deserves attention: the latest commit is September 28 (`21f838c`), while substantial
later source and documentation remain uncommitted. Verified independent experiment keepers protect
valuable evidence, including the current producing files; they are not proof that all repository work
has been reviewed and published. Do not stage raw imaging, secrets, private evaluation material or
large scratch outputs by default. This retrospective does not commit or push anything.

CAP-EXP-014 checkpoints and exports have already been independently restored and checked. There is
no need to repeat unchanged real reads or retrain to produce a Monday story. The D-335 protected
controls contain 201 files; the final whole-backup inventory is 17,341,924,636 bytes against the fixed
18,318,645,873-byte ceiling, leaving 976,721,237 bytes. Keep that ceiling and the registered 20 GiB
limit; a new run needs an actual incremental storage calculation, not a silent reset or deletion.

The [publisher email draft](../data/PANTS-PUBLISHER-EMAIL-DRAFT-2026-09-28.md) is ready for Quinton
to send when desired. Sending it and checking stakeholder availability are useful owner follow-ups,
not reasons to pause all qualified PanTS work. Source holds remain until relevant evidence changes.
No email or other external message was sent during this review.

## Proposed Week 1 direction

**Goal:** carry the pre-course foundation into a preserved, auditable course baseline, answer one
well-defined imaging question, and make the next autonomous-integration step concrete while keeping
the literature and reviewer-workflow commitments active.

1. Reconcile approved requirements with existing evidence. Update only the status rows supported
   by actual checks; retain named gaps. Historical unchecked boxes are not permission to redo every
   successful test, and later test totals are not permission to close full G0/G1/G3 gates wholesale.
2. Prepare the fresh same-cohort duration proposal. Keep initialization/recipe controls, tiny and
   boundary cases, terminal-primary policy and report-only 2514. Predeclare class/component coverage
   and false-positive reporting, qualify the changed runtime, measure budget and seek exact approval.
   Run only if those conditions pass; otherwise retain the blocker and reduce the proposed task.
3. Specify how saved localizer output reaches the segmenter and how ROI containment failures are
   reported. Prioritize the missing component/box coverage evidence before choosing cleanup. Preserve
   provided-region evaluation as a separate comparison; do not label it autonomous.
4. Define a varied multiclass expansion and verified-negative plan using existing evidence first.
   Qualify every consumed case for its intended purpose and role; freeze new descendants without
   replacing held members or silently treating unlabeled/empty lesions as negative.
5. Reopen the integration queue: bound the Plan 04 tool spike and real artifact-to-UI adapter tasks.
   Their existing explicit implementation gates still apply. Seek the narrow authorizations when
   packets are concrete; do not build unrelated infrastructure just to increase progress counts.
6. Keep a parallel literature decision block. The latest local P2 handback still has unfrozen policy,
   provisional candidates, a second family-2 seed gap and unsigned acquisition. Confirm whether
   Claude has newer work before dispatch. P3 synthetic acceptance is not a live retrieval system.

Available review/development hours should determine which of these become Week 1 commitments.
The minimum is preservation, accurate course-start reporting and a concrete next imaging packet.
A successful launch or useful-model result cannot be guaranteed by a calendar date.

## Risks and course corrections

| Risk | Course correction |
|---|---|
| Accumulating plans/wrappers without new scientific information | Reuse qualified consumers; each new change should answer a named uncertainty or satisfy a missing committed boundary |
| Scaling poor contours prematurely | Use one controlled duration test, then varied multiclass/realistic-ROI evidence before broad long training |
| Tuning against one repeatedly visible case | Keep 2514 report-only; design future role-separated development evaluation explicitly |
| Treating qualification as a quality filter | Hold unsupported uses, retain difficult supported members and keep complete original accounting |
| Imaging absorbs the whole capstone | Track PANORAMA, DAG, retrieval, UI and stakeholder outcomes alongside experiments; protect Week 8 integration |
| Preservation debt | Review/publish recent source and docs; keep ignored irreplaceable evidence independently protected |
| Confusing progress with formal completion | Report demonstrated slices and remaining acceptance evidence separately; avoid a single percentage-complete claim |

## Evidence and handoff

Start with [CURRENT-CHECKPOINT](CURRENT-CHECKPOINT.md),
[CAP-EXP-014 results](CAP-EXP-014-RESULTS-2026-10-03.md),
[CAP-EXP-012 results](CAP-EXP-012-RESULTS-2026-10-01.md),
[localizer structure audit](LOCALIZER-STRUCTURE-AUDIT-RESULTS-2026-10-01.md),
[segmenter cohort freeze](SEGMENTER-COHORT-FREEZE-RESULTS-2026-10-01.md),
[Claude's running log](../retrieval/planning/RUNNING-LOG.md),
[accepted P3 review](../retrieval/CODEX-P3-REREVIEW-2026-09-28.md), and
[UI foundation](../testing/UI-FOUNDATION-2026-09-20.md).

The [new-conversation handoff](NEXT-CONVERSATION-HANDOFF-2026-10-03.md) preserves the exact state
and a copyable opening prompt. No experiment is running or pending, consumed requests stay consumed,
and this retrospective changes navigation/documentation only.
