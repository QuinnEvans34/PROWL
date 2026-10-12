# Week 2 work plan and delivery benchmark

**Dates:** October 12–18, 2026, America/Denver\
**Baseline set:** October 12, at Quinton's request\
**Owner:** Quinton + Mac development chat; training/PANORAMA execution belongs to the other laptop/chat\
**Status:** October 12 engineering review delivered; hours and Sunday closeout pending\
**Purpose:** One authoritative weekly specification, linked to Trello and reviewed at week end.

## 1. Commitment and alignment

The approved proposal section 6 assigns Week 2 **frozen protected cohorts, patient/group separation,
manifests and repeatability checks**. See [confirmed delivery outline](PROJECT-DELIVERY-OUTLINE-2026-10-09.md)
and [Plan 02](../implementation/02-data-and-cohorts.md). This remains our first obligation.

This week's selected delivery benchmark is:

1. **Required proposal outcome:** a reproducible portable cohort package with enforced protected roles
   and explicit limits on biological-patient identity.
2. **Supporting imaging disposition:** review the seven unresolved-unit cases and flagged source/anatomy
   issues; apply only evidence-backed fixes and retain explicit unresolved failures.
3. **Planned product delivery:** one saved prediction package displayed correctly in the existing viewer,
   including identity and loading/missing/failure states.
4. **Required closeout:** resolve or explicitly retain Week 1 evidence gaps, confirm human hours with
   Quinton, maintain Trello, and publish a Week 2 acceptance summary.

These are commitments to deliver and verify the stated artifacts, not claims that they are already done.
A blocked or partial outcome is recorded as such; a blocker note does not satisfy the missing deliverable.
No accuracy target, model improvement or finish time for a long-running job is promised.

**October 12 AI planning update:** [database implementation plan](../retrieval/PGVECTOR-IMPLEMENTATION-PLAN-2026-10-12.md)
proposes the synthetic W02-08 platform trial first; it can run independently of real corpus preparation.
This refines the sequence below without declaring W02-08 complete or starting a database job.

**Real-data AI expert sequence after the Week 2 engineering outputs:** full journal selection → permitted
text/passages → bounded pgvector retrieval slice → real evidence-panel connection planning. These
remain specified follow-ons, not prerequisites for Week 2 completion. Administrative hours confirmation
or an unavailable new model must not become an indefinite blocker to returning to the AI expert. Optional research stretch goals follow the committed system, not just this week's AI progress.
Keep Week 9 for stabilization and Week 10 for delivery.

## 2. Starting point — completed before this week

| Area | Retained evidence | What remains |
|---|---|---|
| Cohorts | Protected identity/registry/bundle code, original split ancestry, admitted 1,333 train/75 development cases | Exact consumer/root portability and current admission evidence need reconciliation |
| Imaging | CT-only cascade; 68/75 development outputs, seven unresolved-unit cases | Source-unit/anatomy concerns and quality remain open; do not rebuild the delivered cascade |
| Evaluation | 68 matched reference/predicted-crop pairs; reusable predict/score/compare CLI, 24 focused tests | Evaluate a new candidate only when supplied or a policy changes |
| Viewer | React/NiiVue and guided evidence fixtures | Saved prediction connection/alignment still pending |
| Literature | 1,656-file replay verified complete, 41,226,017 records, 510.13GB catalog; MeSH 2026 verified | Full candidate selection, permitted representation, passages and index |
| Expert responses | Guided questions, one saved fixture response/request, citations and explicit failure/refusal states | Live retrieval/generation and quality evaluation remain future milestones |
| Training | Retained Mac result: 24,000 updates; provided-region development Dice 0.3953174294791896 | Other laptop/chat owns all future training; no fresh remote status inferred |

Evidence: [import runbook](../retrieval/STREAMING-CORPUS.md),
[MeSH](../retrieval/MESH-VERIFICATION-2026-10-10.md),
[selection implementation](../retrieval/TOPIC-SELECTION-V0.md),
[guided fixture](../retrieval/GUIDED-FIXTURE-DEMO.md),
[imaging report](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md),
[evaluator](../../evaluation-autonomous-cohort.md).
Historical details at the end are evidence of earlier work, not new Week 2 completion credit.

## 3. Ordered execution queue — read Trello top to bottom

October 12 sequencing correction requested by Quinton: finish Week 2 work first, then return to
AI expert development. This supersedes the earlier plan to run journal selection alongside cohort work.
Card IDs stay stable; list position communicates order.

| Order | Existing card | Concrete work and completion evidence |
|---|---|---|
| 1 — complete | W02-01 | Audit the actual cohort consumer; reuse or repair root/role/group checks; produce the admitted portable package and verification report. If already correct, verify and close without rebuilding. |
| 2 — disposition delivered; source issues open | W02-02 | Reconcile seven unresolved-unit cases and source/anatomy concerns; make evidence-backed fixes where possible and retain every unresolved case with reason/next evidence needed. A disposition report does not certify a repaired scan. |
| 3 — complete | W02-04 | Connect one saved eligible prediction package to the viewer; verify alignment, identities, loading/missing/failure states and case-switch isolation. |
| 4 — complete | W01-01 carryover | Link current requirement/check evidence; resolve actual gaps or state remaining gates explicitly. Do not require later-week features to pass Week 1 design closeout. |
| 5 — user input | W01-05 carryover | Record Quinton's confirmed active daily hours and Week 1 total. Unknown hours remain pending, not zero. |
| 6 — weekly review | W02-05 | Review the engineering acceptance records and every project area; record Week 2 hours when supplied and prepare the next task. Final Sunday review remains scheduled in the plan even if engineering finishes early. |
| Then AI 1 | W02-06 | Execute and reconcile the full journal candidate selection. |
| Then AI 2 | W02-07 | Qualify permitted text and publish stable source-linked passages. |
| Then AI 3 | W02-08 | Build and verify a bounded pgvector retrieval slice with pinned embeddings/corpus identity. |

W02-03 stays conditional in Backlog until a new candidate model or changed policy is ready. It is
not required to rerun the completed baseline before returning to the AI expert. Legacy W01-04 N4
remains a dependency review in Backlog; resolve its relevance when selecting the retrieval storage path.
Training and PANORAMA implementation remain in the other chat. No task here starts those jobs.

**Board protocol:** Week 2 — To Do contains the ordered current work. Only the task actually being
executed moves to In Progress; one implementation at a time. Record the result and evidence on its
existing card, then move accepted work to Week 2 Complete. A blocked card names its dependency;
proceed with independent work and preserve its open status. AI follow-ons are at the top of Backlog
in selection → passages → pgvector order until the Week 2 engineering review is complete.

## Task specifications and dependencies

All engineering tasks below are owned by this Mac development chat with Quinton reviewing outcomes.
Quinton relays external model/data handbacks; no other chat is dispatched by this plan.

| ID / Trello | Commitment | Initial status | Dependencies | Deliverable |
|---|---|---|---|---|
| [W02-01](https://trello.com/c/8WvBwmi7) | Required | Done October 12 — local package/consumer scope; remote execution unverified | Existing cohorts, source identity and root maps | [Portable package and verification](../data/PORTABLE-COHORT-2026-10-12.md) |
| [W02-06](https://trello.com/c/LxvwMa3s) | After Week 2 engineering | Queued, not running | Completed catalog, MeSH, v0.1 policy, resource fit | Reconciled full candidate set + selection receipt |
| [W02-04](https://trello.com/c/Jfzjuctc) | Planned product delivery | Done October 12 — local saved prediction slice | Retained PanTS_00001070 package | [Native viewer and acceptance checks](../imaging/SAVED-PREDICTION-VIEWER.md) |
| [W02-02](https://trello.com/c/jXIcbELc) | Supporting work | Disposition delivered October 12; source issues remain open | CT units and upstream anatomy provenance | [Source disposition](../imaging/SOURCE-DISPOSITION-2026-10-12.md); no justified unit override |
| [W02-03](https://trello.com/c/KstCVvhp) | Conditional | Await changed model/policy | Admitted candidate and W02-01 | Matched native report and decision |
| [W02-07](https://trello.com/c/fGxysGgy) | Front-load next | Depends on selection | W02-06 and permitted text decisions | Stable, traceable passages |
| [W02-08](https://trello.com/c/nqTumUtb) | Front-load after passages | Not ready | W02-07, embedding choice and measured capacity | Bounded PostgreSQL/pgvector retrieval slice |
| [W02-05](https://trello.com/c/lV0ikeEK) | Required weekly upkeep | Planning complete; final review pending | Task evidence + Quinton's hours | Sunday acceptance review and Week 3 starting task |

### W02-01 — Protected portable cohorts

- **Reuse:** `src/data/protected_identity.py`, `cohort_registry.py`, `cohort_records_v3.py`,
  `segmenter_cohort_bundle_v1.py`, current admitted manifests and original protected split records.
- **Work:** trace the actual evaluator/data consumer, identify missing checks, and repair only those
  gaps. Separate root alias/relative path resolution from stable case/content identity. Preserve
  original memberships, parent roles, exclusions and annotation-purpose evidence.
- **Outputs:** canonical cohort control/member records with hashes, root mapping instructions,
  consumer example and a report stating identity assurance and exclusions.
- **Acceptance:** repeated builds match membership/content hashes; a different local root preserves
  identity; changed content, duplicate/group overlap, wrong role, missing required annotation and
  invalid ancestry are rejected by relevant focused tests. Verify the intended consumer actually
  consumes the package; existence of an unused manifest is insufficient.
- **Limits:** PanTS study-as-subject fallback is not proven biological-patient uniqueness. Enforce
  source grouping wherever identifiers exist and report residual uncertainty. No held-out payload
  inspection or split reshuffling. A simulated second root does not prove a Lenovo execution passed.
- **Fallback:** use verified local fixtures to finish portability mechanics if external data is
  unavailable, but keep real-package admission open until its source evidence is available.

### W02-06 — Full journal candidate selection

- **Reuse:** complete catalog, verified MeSH, `src/retrieval/streaming_corpus.py`, policy v0.1 and
  existing deterministic selection checks. Do not redownload/replay the completed catalog.
- **Work:** inspect source/output availability and execution recovery behavior, set a concrete output
  location and runtime/storage budget, then execute full selection into a new output directory.
  Establish seed/reserve/exposure controls before relevance evaluation or article-level labeling.
- **Outputs:** candidate PMID list, per-record dispositions, counts/exclusion reasons, policy/code/
  catalog/MeSH identities, completion receipt and operating-cost record.
- **Acceptance:** all eligible input records accounted for; journal-only policy and deletion precedence
  retained; global WORKFLOW cap and ordering verified; output identity/hash reconciliation passes;
  incomplete output is not consumed. Existing targeted tests are reused unless changes warrant reruns.
- **Fallback:** diagnose an interrupted/oversized run and preserve evidence. Resume only if the actual
  selector supports it; replay resumability does not imply selection resumability. A preview remains
  partial, not full completion. No wall-clock ETA until measured throughput is available.

### W02-04 — One saved prediction in the viewer

- **Reuse:** existing React/NiiVue UI, native exports, case-package contracts and saved-output metadata.
- **Work:** connect one eligible saved CT and its pancreas/lesion prediction overlays; show case/model
  identity and provenance. Label reference overlays distinctly if used for validation.
- **Outputs:** reusable package adapter/configuration, documented demo command and verification evidence.
- **Acceptance:** spatial alignment checked against package geometry, expected layers displayed,
  loading/missing/failed states explicit, case switching cannot show a stale prediction; affected UI
  checks and one browser integration path pass. Use saved outputs rather than requiring retraining.
- **Fallback:** synthetic package proves UI mechanics if real data is unavailable; report real-case
  demonstration as pending rather than substituting it silently. Durable review history and voxel
  editing are not part of this slice.

### Supporting and conditional work

- **W02-02:** inventory all seven unresolved-unit cases and flagged anatomy/source issues, record
  evidence needed, and implement a bounded correction only when justified. Never invent units or
  drop failed cases to improve reported performance. Use this work where it unblocks the viewer.
- **W02-03:** when a candidate arrives, verify model/configuration/role lineage, use the same admitted
  development cohort and native scorer, preserve the requested-case denominator and report pancreas/
  lesion quality, coverage, false alarms and failures. Record adopt/reject/inconclusive with limits.
  Reuse unchanged baseline outputs; no training or final held-out release evaluation here.
- **W02-07:** establish which selected text can be used, retain source/version/rights/correction
  status, normalize into stable passage IDs with exact locators, and verify round-trip citations and
  rebuild identity. Missing abstracts/full text are explicit dispositions, not fabricated content.
- **W02-08:** select an embedding configuration only after permitted text and measured size are known;
  specify storage/runtime, ingest a bounded versioned corpus into PostgreSQL/pgvector, and demonstrate
  queries returning exact source passages with reproducible index lineage. No corpus-wide embedding
  launch merely because the database is installed. Canonical files remain the rebuild authority.

## 4. Weekly sequence and capacity

Dates are target work blocks, not fabricated hour estimates or automatic job launches. Available
focused human time is being confirmed with Quinton. Leave approximately 20% of that time unallocated
for debugging/review; remove optional work first if capacity is lower than expected.

| Day | Main work | End-of-block benchmark |
|---|---|---|
| Monday Oct 12 | Baseline this plan; audit actual protected-cohort consumers and Week 1 evidence gaps | Concrete cohort gap list, reusable evidence, next implementation step; no broad rewrite |
| Tuesday Oct 13 | Implement/verify cohort portability and role checks | Package/repeatability result, or named failing acceptance item with a repair plan |
| Wednesday Oct 14 | Finish cohort acceptance; reconcile imaging source failures | Required deliverable status explicit; each unresolved case has a reason and next action |
| Thursday Oct 15 | Connect the saved prediction package | Initial aligned viewer path and explicit failure states |
| Friday Oct 16 | Verify viewer; inspect source failures or supplied model as relevant | Demonstrable viewer states and remaining defects; decide whether front-loading fits |
| Saturday Oct 17 | Repair committed-deliverable defects first; then passages/pgvector if ready | Evidence for completed outputs; no speculative expansion while core work is blocked |
| Sunday Oct 18 | Review every area, hours, Trello and acceptance results; prepare Week 3 | Honest weekly disposition and a ready next-week task |

One primary implementation at a time. Finish the ordered Week 2 engineering queue before returning
to selection/index development. No repeated polling replaces useful development.
If a required task is still blocked at Wednesday's checkpoint, suspend optional indexing and use the
remaining development time for that task. Record any scope change here and in the existing card.

## 5. Whole-project coverage — nothing silently dropped

| Area | This week's checkpoint | Later committed delivery / owner |
|---|---|---|
| Data identity/cohorts | W02-01 acceptance | Week 2, this chat |
| PANORAMA | Record handback/dependency readiness for Week 3; unknown status stays unknown | Week 3 integration, other laptop/chat; Quinton coordinates |
| Training/models | Consume a supplied report/checkpoint only if ready | Other laptop/chat owns setup, training and monitoring |
| Imaging/evaluation | Existing 68-output baseline preserved; unit/source issues visible; changed candidates evaluated conditionally | Autonomous baseline Week 5; controlled comparison Week 6 |
| Viewer/product | W02-04 saved prediction slice | Persistent accept/correction-required/reject and integrated workflow Week 7 |
| Measurements/review ordering | Keep validity/uncertainty requirements in traceability; no unsupported score | Structured outputs Weeks 4–7, operating-point evidence Weeks 5–7 |
| AI expert | Queued after Week 2 engineering: selection → passages → index | Queryable prototype Week 5; retrieval/response evaluation Weeks 6–8 |
| Whole-system DAG | Reuse stage contracts; record remaining cross-stage recovery work | Executable/restartable integration Week 4 |
| Testing/reproducibility | Tests matched to each changed path; immutable input/output identities and failure records | Full integration/regression and frozen evaluation Week 8 |
| Stakeholder/ethics | Keep source rights, unsupported-answer and clinical-scope boundaries explicit; participant planning visible | Confirm session/fallback by Week 5; walkthrough Week 7 |
| Documentation/course | Weekly evidence, hours and board; new assignment dates only from actual course information | Documentation drafts Week 8; delivery Week 10 |
| Release/stretch | Maintain later-feature backlog; no new parallel tracker | Stabilization Week 9; stretch selected only with spare capacity |

Later capabilities remain tracked by the [complete feature inventory](PROJECT-DELIVERY-OUTLINE-2026-10-09.md)
and existing W03–W10 Trello cards. This table is a weekly coverage check, not a requirement to implement
all project areas this week. Better models and every stretch idea are ambitions, not guaranteed outcomes.

## 6. Week 1 carryovers

- [W01-01](https://trello.com/c/hpTmjopp): reconciliation delivered October 12 in the
  [43-requirement closeout](WEEK-01-CLOSEOUT-2026-10-12.md). G0-design delivered; current full
  G0-verification partial, with setup follow-up tracked in W02-05. Original scope: architecture/test traceability and G0
  design-versus-executable disposition. Reuse existing evidence; fix only identified missing checks.
- [W01-05](https://trello.com/c/yU3zZfAz): Quinton confirms remaining active daily hours/weekly total.
  No agent, overnight download, processing or overlapping chat time is credited.
- [W01-04](https://trello.com/c/XcloMmhR): decide whether legacy N4 storage recovery is still used.
  If retained, its separate qualification stays open; if superseded, cite replacement evidence.
  Successful PubMed replay does not independently close that gate.
- Resources and What/Why/How are confirmed completed by Quinton on October 12. Do not request those
  confirmations again. Week 2 course deadlines/submissions are not inferred from project milestones.

## 7. October 12 engineering review and Sunday acceptance record

| Outcome | Passing benchmark | Actual result / evidence |
|---|---|---|
| Protected cohorts | Immutable package consumed; repeat/root/role/group checks pass; identity limits documented | Passed local package/consumer scope October 12; 1,333/75, repeat build exact, 58 focused checks; biological uniqueness and Lenovo execution unverified. See portable cohort report. |
| Imaging disposition | All seven unit failures/source concerns accounted for; fixes backed by evidence and unresolved cases retained | Disposition delivered; seven unknown-unit cases remain blocked on source evidence. Source workbook corroborates head-study concern. [Report](../imaging/SOURCE-DISPOSITION-2026-10-12.md); W02-02 stays open. |
| Viewer slice | Saved package aligns; identity and failure/case-switch states verified | Passed local saved-package scope; 7 Python + 12 UI + 3 real-browser checks and build. [Report](../imaging/SAVED-PREDICTION-VIEWER.md). Full case-package workflow remains later work. |
| Week 1 closeout | Evidence disposition and user-confirmed hours recorded; residual gaps named | Partial overall: [43-requirement reconciliation](WEEK-01-CLOSEOUT-2026-10-12.md) complete; hours still pending. G0-design delivered, current full G0-verification partial. |
| Whole-project review | Every row above reviewed; Week 3 dependencies/owner/next task stated | October 12 review delivered below; Sunday October 18 final review remains open. |
| AI follow-ons | Selection/passages/index credited only after actual acceptance; not required Week 2 outputs | Engineering review permits returning to W02-06 preparation next; no selection, embedding or indexing job started in this review. |

Overall at October 12: **selected local engineering outputs delivered; weekly closeout partial**.
The protected-cohort package meets the local consumer benchmark; biological-patient uniqueness and
actual Lenovo execution remain unverified. Source issues, human hours and final Sunday acceptance
remain open. This is an early checkpoint, not a claim that the entire week or project is complete.
Record Quinton's human hours in [HOURS-LOG.md](HOURS-LOG.md); Trello provides task evidence, not a timer.

### Whole-project checkpoint — October 12

| Area | Review conclusion | Owner / next action |
|---|---|---|
| Protected cohorts | Local 1,333/75 package and protected evaluator delivered; package hash rechecked against report | Mac consumes fixed package; Quinton relays Lenovo execution evidence when available. No split reshuffling. |
| PANORAMA | Week 3 integration remains unverified here | Other laptop/chat owns implementation; Quinton relays versioned manifest, mapping/exclusion/duplicate report and smoke result before integration claims. Existing W03-01 remains open. |
| Models/training | No new candidate handoff received; no training work here | Other laptop/chat; Mac runs W02-03 only for a supplied candidate or changed policy. |
| Imaging/evaluation | 68/75 outputs retained, seven unit failures and head-study issue explicit; model quality weak | W02-02 source evidence pending; no unchanged-baseline rerun or unsupported mm override. |
| Viewer/product | Saved abdominal package works locally; reference-free display with identity/geometry checks | W02-04 complete. Full case-package, measurements and durable accept/edit/reject remain Week 7. |
| Measurements/review ordering | Design and metric primitives exist; no validated integrated clinical score | Mac, Plans 05/06/08; develop with named prediction/units and acceptance evidence in Weeks 4–7. |
| AI evidence | Download/catalog/MeSH complete; guided saved fixture works | Mac: W02-06 selection preparation next, then permitted passages and bounded pgvector. No live retrieval/generation claim. |
| Whole-system DAG | Stage contracts exist; component recovery is not whole-system resume | Mac, W04-01; versioned cross-stage failure/retry/idempotency acceptance remains Week 4. |
| Testing/reproduction | Focused cohort/viewer evidence passes; full current-tree clean-environment verification remains open | Mac, W02-05 follow-up: document supported runtimes and bounded install/collection/skip reconciliation before full G0/G8 claim. Current shell Node 20.20.1; successful UI runtime Node 24.19.0. |
| Storage/recovery | PubMed replay complete; separate legacy N4 rehearsal still unverified | Mac, W01-04: determine whether selected next storage path uses N4 before relying on it; do not repeat obsolete work just to clear a card. |
| Stakeholder/ethics | Research wording and protocol exist; no actual stakeholder session claimed | Quinton owns outreach; confirm role/fallback by Week 5, conduct review Week 7. Source/public-release restrictions stay explicit. |
| Documentation/course | Current evidence and week plan updated; course tasks already confirmed | Mac maintains Trello/docs; Quinton supplies hours and actual new course deadlines. No submission inferred. |
| Release/stretch | Week 9 stabilization and Week 10 delivery retained | Select stretch work only after committed outputs; no new tracker or release claim. |

### Deferred checks — revisit later this week

Quinton explicitly requested on October 12 that the following remain documented for later-week
review while we discuss the AI expert prerequisites. These are open items, not completed gates.
The dates below are planning checkpoints, not scheduled automations or promises of resolution.

| Check | Owner / tracking | Revisit | Evidence needed to close |
|---|---|---|---|
| Seven unknown CT spatial units | Mac review; W02-02 | Wednesday Oct 14; carry unresolved items to Sunday | Acquisition metadata or applicable publisher unit documentation tied to each pinned CT; reviewed override and targeted verification only if justified. No inferred mm. |
| Head-study annotation question, PanTS_00001389 | Mac source review; W02-02 | Wednesday Oct 14; Sunday if no new evidence | Upstream anatomical/annotation provenance explaining the head study and pancreas label. Keep existing issue/output evidence; no silent exclusion. |
| Cross-machine cohort verification | Other laptop/chat executes; Quinton relays; W02-05 follow-up | Friday Oct 16 | Same package digest, role/member/content bindings and successful local-root consumer verification on Lenovo. Mac root simulation alone is insufficient. |
| Reproducible environment checks | Mac; W02-05 / REQ-E03,E10 | Friday Oct 16 | Supported Python/Node reproduction instructions, clean install and collection/skip reconciliation scoped to current source. Node 24.19.0 passed focused UI checks; Node 20.20.1 setup failure remains recorded. |
| Confirmed human hours | Quinton; W01-05 and W02-05 | When supplied; final reconciliation Sunday Oct 18 | Exact Tuesday estimate, net Oct 7–11 active hours, then Week 2 daily time. Exclude unattended/overlapping time; unknown is not zero. |

**Sunday October 18:** W02-05 stays open for final review, remaining blockers, confirmed hours and
Week 3 priorities. Absence of new source/remote evidence leaves the relevant check open. No messages
are sent to the other chat or publisher by this deferral. These checks do not block independent
journal selection preparation; they still gate claims that depend on their results.

### Before returning to AI expert execution — discussion packet

Existing scope remains journal-first policy v0.1, guided reviewer questions and one saved response
per request, with the approved refusal/failure wording. Download, ordered catalog replay and MeSH
verification are already complete. No policy redesign, fresh download or training is needed.

1. **Protect evaluation before inspecting results.** Reconcile the existing seed set and prior
   exposure record; record the fixed reserve salt/sampling controls. Seed verification/freeze and
   reserve/exposure rules must be settled before selection evaluation or article labeling. A
   computational candidate pass is not itself an official policy freeze or a retrieval-quality result.
2. **Prepare a concrete selection run.** Confirm catalog completion identity and verified MeSH/policy
   pins; choose a fresh output directory and measured disk/runtime limits. Use the streaming `select`
   command, not the bounded 10,000-record preview. No full 500GB rehash just to repeat completion checks.
3. **Resolve the interruption tradeoff before a long run.** The current selector does not resume:
   failed attempts retain evidence and restart in a new output directory. Import replay resumability
   does not transfer to selection. Review measured cost and choose whether this is acceptable or a
   small checkpointing change is warranted. Do not promise an ETA from the earlier 30,000-record trial.
4. **Define selection acceptance.** Account for every PMID, deletions/exclusions and the global
   WORKFLOW cap; preserve candidate hashes and completion summary. The intermediate selection SQLite
   ledger is not the final corpus. Only then move to permitted text and stable passages (W02-07),
   followed by a bounded PostgreSQL/pgvector slice (W02-08). Embedding configuration/size choices
   belong after we know permitted passage volume; live generation remains a later connection.

This packet is for discussion and preparation. No selector, text download, embedding or database job
was launched by the October 12 review or deferral.

### Next task and review boundary

**Next: W02-06 — prepare and execute the journal candidate selection.** Before launch, inspect the
existing selector's actual recovery behavior, settle seed/reserve/exposure controls, pin the completed
catalog/MeSH/policy identities, and set a concrete output location and runtime/storage budget. No
redownload, catalog replay, embeddings or training is part of this step. Selection output must reconcile
candidate/exclusion/deletion counts; a preview is not full selection. Its next work card can move to
To Do now; In Progress means work has actually begun.

This review does not wait indefinitely on hours or unavailable models. W02-02, W01-04 and the
runtime-verification follow-up retain explicit owners/dependencies. W02-05 stays open until the final
weekly review and supplied hours; its October 12 engineering review is complete. Sunday's review must
revisit this table, record newly completed work and remaining blockers, reconcile hours, and baseline
Week 3 PANORAMA handback/dependencies. No scheduled automation is created by this plan.

Human-hours status: Monday October 5 = 4; Tuesday = 5–6 (exact entry unselected); October 7–11 net
active hours remain unconfirmed in this log. October 12 is also pending. The 9–10 hour subtotal is
not the Week 1 total. Clarification requested; no elapsed job time or open clock interval is credited.

## 8. Weekly working agreement and change log

At the beginning of each week, review the previous results, map the approved week's commitments,
inspect all project areas, specify outputs/tests/dependencies/owners, confirm capacity, and save one
numbered work plan. Update existing Trello cards rather than creating duplicate trackers. Midweek,
compare actual progress against acceptance criteria; at week end move only completed work into the
week's Complete list and prepare the next starting task. This routine does not create an automation.

| Date | Change | Effect |
|---|---|---|
| Oct 12 | Quinton requested a committed weekly benchmark and complete project coverage | This plan supersedes the October 9 draft task priorities; retained results below stay historical |
| Oct 12 | Initial draft selected cohorts, selection and viewer | Superseded by the sequencing decision below |
| Oct 12 | Quinton requests Week 2 first, AI expert afterward | Cohorts → imaging disposition → viewer → evidence closeout; AI selection/passages/index remain ordered follow-ons |

## Historical implementation evidence — October 9–11

The following dated notes preserve prior attempts and results. Statements such as “running,” “next,”
or “pending” describe their date; the current task board and starting-point table above govern now.

October9 implementation: predicted-region geometryv2 adapter and seven new tests delivered;74 focused
checks pass. See the investigation result. Full CT/model inference and native real-case evaluation remain pending.

October9 continuation: CT-only cascade execution/native NIfTI export and mask-absence/invariance tests
implemented;19 focused checks pass. Trained-checkpoint authentication, ancestor separation and real
CT-only evaluation remain open; no leakage-free benchmark claim. See investigation evidence.

October9 trained-checkpoint integration: [two CT-only diagnostics](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md)
complete with native exports. A01 appears non-abdominal yet received organ predictions; investigate
source/annotation provenance and unsupported-input handling. Separate scoring and quality acceptance remain open.

October9 fixed-cohort baseline: all75 admitted development IDs accounted for;56 scored outputs,19
explicit inference failures. Mean positive lesion Dice0.244807 over28 scored positive cases;10positive
and9reference-empty cases remain unscored. Missing CT units and geometry allocation limits are concrete
engineering gaps. Source/anatomy review and matched cohort-wide crop comparison remain open. See the
[checkpoint connection report](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md).

October9 capacity correction: configurable bounded64M geometry limits recover all12 geometry failures
without changing spacing/crops/models.68/75 outputs now available, seven CT-unit cases require source
evidence. Explicit hash-bound unit-review support is implemented/tested; no real reviews invented.
31 focused tests pass. Quality remains weak: combined mean lesion Dice0.225818 over33 positive cases,
with changed population; this is not an accuracy-improvement claim. Lenovo remains untouched.

October9 matched analysis: all68 available cases paired. Same segmenter improves mean lesion Dice
from0.225818 to0.422671 on33 positive cases when given reference crops; no entire lesion component
is lost under either transform. Predicted crops are materially larger/coarser. Crop scale/context
robustness is the next experimental focus; the reference-assisted number is not an autonomous result.
Seven unknown-unit cases and source/anatomy issues remain open. Current Lenovo training stays unchanged.

October9 CT-only crop challenger completed: largest26-connected region plus10mm preserves full native
lesion box coverage33/33 and modestly improves Dice0.225818→0.246612, with8 improved/8 worsened/17 tied
positive cases. All68 cases ran; raw localizer masks match baseline. Opt-in experimental policy only;
default unchanged. Confidence-based crop sizing and crop-variation training remain open questions.

October 9 next-step handoff: [Lenovo crop-variation experiment](../operations/LENOVO-CROP-VARIATION-EXPERIMENT-HANDOFF.md)
specifies one controlled successor run while preserving the active training job. Further crop-policy
sweeps are deferred. Mac priorities are a reusable fixed-cohort evaluation command, completion of
portable cohort checks, and a saved-prediction connection to the existing viewer. This is a development
plan, not a claim that the augmentation or successor launch has already been implemented.

October 9 conversation continuation: [fixed-cohort evaluator](../../evaluation-autonomous-cohort.md)
now wraps the existing CT-only predictor, separate saved-output scorer and summary. It provides pinned
plans, compatible saved-output reuse, full case/failure accounting and paired report comparisons.
24 focused tests pass, covering actual synthetic cascade/native scoring and reuse/tamper/resource/identity boundaries;
no new real-cohort experiment was run. Component/crop-coverage diagnostics remain separate.
W02-03 tooling is implemented; this does not finish portable cohort admission, unresolved-unit reviews,
source/anatomy concerns, viewer integration or scientific quality work. Lenovo remains user-reported
and untouched. Human-hours records remain unchanged.

October 9 planning recenter: Quinton requested proposal review and discussion before selecting today's
implementation. [Feature and weekly delivery outline](PROJECT-DELIVERY-OUTLINE-2026-10-09.md) records
the approved scope, current evidence, Week 1 closeout, ten-week deliverables and an early AI-expert DAG
option. It is a discussion guide, not a second task queue or a blanket completion declaration.
The subsequent decision selected the guided evidence fixture slice below; protected cohorts remain
Week 2's primary commitment.

October 9 ownership clarification: Quinton confirmed that this chat has no training responsibility.
The other laptop/chat owns training code, setup, launches and monitoring. This chat develops the
application/data/evidence workflows and tests supplied candidate models when ready. Cross-machine
cohort identity remains relevant to model consumption, but remote training readiness is not a task
for this chat. Trello is the required work/grading log; see the weekly working agreement.

October 9 selected expert slice: guided reviewer questions now produce one locally saved JSON response
per request through a separate model-free fixture service. The UI distinguishes supported synthetic
content, insufficient evidence, clinical-scope refusal and unconfirmed/service failure; it displays
exact passages and provenance, preserves idempotent retry, and clears pending results on case changes.
See [demo and run instructions](../retrieval/GUIDED-FIXTURE-DEMO.md) and
[W01-30](https://trello.com/c/3qTiK9p4). Validation: 15 Python tests, 25 UI unit tests, 2 browser tests
with the real fixture API and synthetic viewer, plus production build. Node 24 was needed for existing
UI test dependencies. No real literature, generation, model quality, patient diagnosis, or production
writer qualification is claimed. Partial/conflicting evidence and case-linked history remain future work.

October 10 handoff continuation: commit `3078b23` supplies the offline catalog preview. The original
download continues without a second launch; at 10:01 MDT its checkpoint recorded 1,010/1,656 verified
compressed XML files (30,612,722,204 bytes). This is a historical checkpoint, not a completion claim.
Training and PANORAMA integration remain with the Lenovo chat.

[Topic-selection v0 implementation](../retrieval/TOPIC-SELECTION-V0.md) now provides the approved
stage-1 text/MeSH rules, exclusions, WORKFLOW cap, reasons/counts and hashed candidate IDs. Catalog v2
adds final-deleted-PMID accounting and requires a fresh output path; the real v1 preview is preserved.
48 focused invented-data tests pass, including catalog/selection preview integration. No actual topic
selection, held-out inspection, seed freeze, rights qualification or vector loading was performed.
[W01-31](https://trello.com/c/nMzTPlCq) records this implementation slice.

Next dependencies: finish verified raw download, obtain verified MeSH 2026 data, decide how policy v0
should handle PubmedBookArticle records, and qualify full-scale replay beyond the current ten-file
catalog preview. Resolve seed/reserve controls before selection evaluation. Selection candidates then
need separate representation/rights qualification before retrieval and evidence-panel integration.

October 10 book-scope decision: Quinton approved journal records for the first corpus. Policy
[v0.1](../retrieval/planning/SEARCH-AND-SELECTION-V0.1.md) preserves v0 and adds explicit
`record_type_excluded` handling for books. Raw/catalog book records remain available; known book
counts are reported separately and deletion precedence is retained. The selector now handles this
case without guessing field mappings. MeSH verification and full-scale replay remain the next work.

October 10 MeSH verification complete: the official 2026 file resolves all 14 required names;
independent parsing confirms all hierarchy group members across 31,110 descriptors. Source, hashes,
receipts and remaining prerequisites are documented in
[MeSH verification](../retrieval/MESH-VERIFICATION-2026-10-10.md). The next engineering dependency
is streaming full-corpus replay/selection: the current 10,000-record selector preview cannot consume
even the existing 30,000-record one-file catalog. Raw acquisition remains in progress; seed/reserve
preparation precedes evaluation, and representation/rights qualification precedes vector loading.

October 10 streaming processing: [implementation and runbook](../retrieval/STREAMING-CORPUS.md)
adds resumable ordered replay and disk-backed selection/global WORKFLOW ranking. Seven new focused
checks pass with the prior 53 selector/catalog checks. Two real 30,000-record import probes and a
30,000-record selection probe passed with aggregate-only reporting; no selection evaluation or freeze.
The ordered first-1,200-file import is now running under a 12-hour/768 GiB/400 GiB-free resource scope.
After it stops and acquisition is complete, resume the same catalog through all 1,656 files before
full selection. [Trello](https://trello.com/c/LxvwMa3s) tracks this work; completion remains pending.

October 11 import acceleration: [profile and benchmark](../retrieval/IMPORT-PERFORMANCE-2026-10-11.md)
identified SQLite read waits. A tested UPSERT path with configurable cache passed63 focused checks
and produced identical record hashes on four isolated clone comparisons; selected configuration
reduced the 1,000-event benchmark from~133s to118s. Full-scale benefit remains unmeasured. Import
resumed from1608 with4GiB cache, existing durability/time/storage safeguards and per-file timing logs.
