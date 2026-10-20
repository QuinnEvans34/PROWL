# Week 3 work plan and delivery benchmark

**Dates:** October 19–25, 2026, America/Denver\
**Updated:** October 20, 2026\
**Owner:** Quinton; this chat owns DAG/RAG software, the other chat owns data/training execution\
**Status:** In progress; planning complete, demo restored and first live check passed\
**Weekly commitment:** Retain the approved PANORAMA integration milestone and deliver a dependable
development AI demo for explicitly covered literature topics.

## Week at a glance — visible progress

**Start here:** [Trello weekly dashboard](https://trello.com/c/cWuIVLyG).
Every current Week 3 card now has a **Week 3 — steps and evidence** checklist.
The table below is the October 20 planning snapshot; update it with material progress.

| Workstream | Status now | Next observable result | Target window |
|---|---|---|---|
| [W03-02 Reliability](https://trello.com/c/KCcUA5kn) | Done for bounded scope: 5/5 steps | Reopen on recurrence; historical exit2 cause remains unknown | Closed Tuesday |
| [W03-03 Volume answers](https://trello.com/c/pnaJmVIz) | Done for bounded scope: 4/4 steps | Local model composition, citations and clarification verified | Closed Tuesday |
| [W03-04 Question selection](https://trello.com/c/Avfr7Oei) | Ready; candidate adapter delivered | Fixed before/after paraphrase and boundary results | Thursday–Friday |
| [W03-05 Quality review](https://trello.com/c/cNjc35Bn) | Pending candidate and fixed check | Readable answer/source packet, complete scores and Quinton walkthrough | Friday–weekend |
| [W03-01 PANORAMA](https://trello.com/c/yfk5R2Vi) | Awaiting data/training evidence handoff | Reviewed mapping, provenance, exclusions and mixed-source smoke evidence | Parallel required Week 3 outcome |
| [W03-06 Closeout](https://trello.com/c/c8WDYybO) | Pending weekly outcomes and supplied hours | Evidence/hours reconciliation and Week 4 handoff | Sunday |

**Already evidenced:** services restored; UI contract-loading repair, 50 UI checks/build and one real
model-composed answer/citation; six lifecycle diagnostic tests; corrected clean recovery check with
503 during outage, identical recovered search result and exact 1,179-passage inventory. W03-02's
five steps are complete for this bounded scope; its historical unknown-cause risk remains explicit.
Volume scope and offline selection now have [first-block evidence](../retrieval/VOLUME-ROUTING-RESULTS-2026-10-20.md):
64 focused checks and seven exposed corpus examples pass. Subsequent
[composition/UI qualification](../retrieval/VOLUME-COMPOSITION-RESULTS-2026-10-20.md) passed the
corrected8/8 check, ten-paragraph source review and exact UI replay; local promotion/browser
verification complete. Earlier failures remain retained. W03-04/05 are next.

**Waiting on review/input:** AI-03 needs changed-scope review and independent-evaluation
responsibilities; W02-02 needs the model/source handoff; W01-05 and W02-05 need missing personal
hours and closeout confirmation. These remain visible in Week 3 To Do and do not block independent
AI implementation. AI-04 is the parent quality milestone; its checklist links the weekly work and
retains formal acceptance separately. Parent and child checklists must not be added together as a
completion percentage.

**How we will keep this current**

1. Before starting a task, mark its card In Progress and identify the next checklist item.
2. Check off a step only when its stated result has evidence. Attach the relevant report, test result
   or commit; a started run or promising example alone does not close a quality gate.
3. At each meaningful work-block handback, update the card and this plan with **completed work,
   evidence, remaining blocker and next step**. Commit coherent repository changes as we work.
4. Move a card to Week 3 Complete only when its finish criterion is satisfied. Mark blocked work
   explicitly with the needed input/owner; keep completed earlier-week history unchanged.
5. Before changing this week's scope, record what is added or deferred and why. Sunday review uses
   actual results, not a guessed project-completion percentage.

This is the week's full working specification, including carryovers below. Targets are planning
windows rather than promised completion dates. No implementation is started merely by checking
that this planning setup is complete.

## Approved proposal commitment

The [approved delivery outline](PROJECT-DELIVERY-OUTLINE-2026-10-09.md), based on proposal v3.8
section 6 and appendix v3.1, assigns Week 3 **PANORAMA integration**: source provenance, label
mapping, exclusions, duplicate/patient controls and mixed-source smoke loading before training
eligibility. [W03-01](https://trello.com/c/yfk5R2Vi) remains the required milestone. Quinton and the
data/training chat supply its evidence; this chat does not start or monitor training.

The AI work is authorized early development under the
[completion specification](../retrieval/AI-EXPERT-COMPLETION-SPEC.md), not a replacement for that
milestone. October 20's end-of-week target does not waive independent evaluation or make the
measurement-aware extension optional. The [extension plan](../retrieval/MEASUREMENT-AWARE-EXPERT-PLAN.md)
and AI-05/06/07 remain required after core acceptance.

## Outcomes for this week

- [ ] **Proposal:** verify PANORAMA integration evidence or report the exact remaining blocker.
- [ ] **Reliability:** reproducible demo startup, correct selected policy, clear recoverable errors,
  and integrated answer/source behavior without stale answers after a study switch.
- [ ] **Useful coverage:** readable cited disease-comparison and study-specific pancreas-volume
  answers, with methods, units, population and applicability limits intact.
- [ ] **Quality:** a fixed, bounded development check with separately scored support, completeness,
  readability, citations, failures and latency, followed by Quinton's walkthrough.
- [ ] **Closeout:** reconciled Trello, scoped commits, confirmed human hours and an explicit Week 4 handoff.

The demo target is a question → readable answer → inspectable sources flow for declared topics.
Returning passages for an answerable covered question does not count as success. Outside coverage,
the UI must explain its limit. We are not promising arbitrary medical answers, scan interpretation,
clinical validation or completion of the protected evaluation by Sunday.

## Starting evidence

| Area | Existing result | Remaining limit |
|---|---|---|
| Corpus | [Disease corpus](../retrieval/DISEASE-REFERENCE-CORPUS-2026-10-17.md): 14 papers, 1,179 passages, independent rebuild | Broad journal selector remains parked; topic coverage is bounded |
| Retrieval | [Record search](../retrieval/RECORD-SEARCH-RESULTS-2026-10-18.md): reviewed disease records and bounded English selection | Three disease records; volume routing and broader wording remain |
| Answers | [Record answers](../retrieval/RECORD-ANSWER-RESULTS-2026-10-18.md): pinned Qwen3:8b selects reviewed wording/paragraphs, code enforces facts/citations | Constrained composition, not unrestricted prose; outside coverage returns sources |
| Volume facts | [Source-fact prototype](../retrieval/SOURCE-FACT-RESULTS-2026-10-18.md): two separate MRI study groups | Not integrated into live free-text answers; not a universal CT reference |
| UI | Other chat's local redesign handback, `docs/capstone/interface/ui-redesign/IMPLEMENTATION-HANDBACK.md`; active checkout `claude/prowl-ui-implementation` at c5ca63e when reviewed | Recheck integrated literature behavior; preserve shared work. Handback may not be published on the retrieval branch |
| Evaluation | [AI-03](https://trello.com/c/NctoNxr8), prior version-specific approvals and development review packets | Current changed-scope review and independent protected labeling/freeze remain open |
| Runtime | October 20 17:42 UTC: UI5180, API8016, Ollama11434 and DB55433 refuse connections; PROWL-Data absent from mounted volumes | No live policy or answer-quality claim from this inventory; Quinton will reconnect the drive |

The October 18 initial DB failure and failed 7/8 answer attempt remain in their reports. Later
layout normalization and two browser checks do not erase those failures or establish general quality.

## Task board

| ID | Priority / status | Owner | Dependency | Finish evidence |
|---|---|---|---|---|
| [W03-01](https://trello.com/c/yfk5R2Vi) PANORAMA integration | Required / Ready for owner handoff | Quinton + data/training chat | W02-01 and source qualification | Mapping, provenance, exclusions, separation and mixed-source smoke receipt |
| [W03-02](https://trello.com/c/KCcUA5kn) Integrated AI demo reliability | Done for bounded scope; historical exit2 cause unknown | DAG/RAG chat | Existing runtime/data availability | [Closeout](../retrieval/RELIABILITY-CLOSEOUT-2026-10-20.md): 6 diagnostic tests, corrected recovery/503 check, exact inventory; recurrence procedure retained |
| [W03-03](https://trello.com/c/pnaJmVIz) Readable volume answers | Done for bounded scope, 4/4 steps | DAG/RAG chat; Quinton walkthrough remains W03-05 | Existing volume facts; W03-02 bounded closeout complete | [Results](../retrieval/VOLUME-COMPOSITION-RESULTS-2026-10-20.md), readable examples, corrected8/8 check, source review and live browser proof |
| [W03-04](https://trello.com/c/Avfr7Oei) Question wording and selection | Planned / Ready for matrix preparation | DAG/RAG chat | W03-03 candidate for comparison | Fixed development matrix, before/after selections, exposure and coverage-gap record |
| [W03-05](https://trello.com/c/cNjc35Bn) Quality checkpoint and demo | Planned / Pending dependencies | DAG/RAG chat + Quinton | W03-02/03/04 | Frozen candidate/checks, full per-case report and walkthrough; failures retained |
| [W03-06](https://trello.com/c/c8WDYybO) Weekly closeout | Required / Pending outcomes | Quinton + both work areas | Actual reports and supplied hours | Reconciled evidence, hours, carryovers and Week 4 plan |

[AI-04](https://trello.com/c/dWDF81CH) remains the parent answer-quality card. The new tasks are
bounded implementation slices, not duplicate feature acceptances. The active Week 2 To Do/In Progress
lists were rolled forward to Week 3; a new Week 3 Complete list was added. Week 2/Week 1/pre-course
completed history and existing card IDs remain intact.

## Task specifications

### W03-01 — PANORAMA evidence handoff

Use the existing source/cohort controls; obtain the data owner's actual handback rather than infer
eligibility from time spent preparing runs. Confirm full anatomy/lesion input coverage where relevant,
source labels, roles and exclusion reasons. This chat records dependencies and reviews supplied
integration evidence. No optimizer launch or protected arrays are part of this plan's execution.

### W03-02 — Reliable integrated demo

Inspect existing mount/configuration, runtime processes and selected service flags before starting
anything. Use `/literature-search/health` on API8016 and through UI5180; the selected answer policy must
be `source-record-answer-v1`. Investigate the recurring PostgreSQL interruption with retained logs.
A healthy request alone is not a root-cause repair.

Verify readable answers, source navigation, loading/failure feedback, cancellation and late-response
suppression using the existing UI contracts. Use synthetic checks for outages/study changes before a
bounded live question. Preserve DB/corpus/model identities, other containers and the redesign.
Finish with a reproducible startup/recovery record and evidence; name unresolved causes explicitly.

### W03-03 — Volume answers

Extend selection and reviewed wording using the existing two MRI study-group records. Preserve
sample count, method, units, matching, SEM meaning and applicability. Clarify ambiguous “size”
requests rather than equate volume, head diameter and length. Do not turn a study mean into a normal
range, disease threshold or comparison with a scan.

Output the adapter, meaningful regressions and a readable citation review. Expected evaluation
answers stay out of production prompts and indexing. Promote only after the declared candidate
checks pass; retain the existing policy if they fail.

### W03-04 — Wording and coverage

Freeze a small development matrix before changing selection: disease and volume paraphrases,
ambiguous size, mixed/negated questions, unsupported topics, patient-specific requests and injection.
Record exposure and distinguish wrong selection, missing evidence and composition failure.
Do not use an exact-question lookup. Add source records only after documenting the missing capability
and reviewing its evidence. Output per-case intended/actual matches and explicit residual gaps.

### W03-05 — Quality and promotion

Pin question set, corpus, record/wording/review hashes, model, policy and producing code before the
bounded run. Apply the existing completion-spec/AI-01 gates; do not lower thresholds after results.
Score factual support, completeness and readability separately. Also report citation identity,
qualifications, false refusals, model versus application fallback, service errors and HTTP/model
latency. Manually inspect each emitted claim and source locator in the batch.

Development cases are exposed; they cannot establish held-out acceptance. The formal split targets
remain at least 18/20 clean complete answerable responses and 10/10 required refusals per split,
with zero unsupported claims/invalid citations and the specified retrieval thresholds. This week's
focused slice does not replace those splits or claim their denominators. Review the readable packet
and demo with Quinton; publish the observed pass/fail outcome and selected version.

### W03-06 — Closeout and required follow-ons

Reconcile PANORAMA and AI outcomes separately, preserve failures and original card histories, and
link scoped commits/results. Confirm actual human hours; no unattended runtime, guessed daily totals
or duplicate other-chat time. Use Sunday review to prepare Week 4's broader DAG milestone.

Keep [AI-05 measurements](https://trello.com/c/Ob3VE0MN),
[AI-06 reference comparisons](https://trello.com/c/TKCLH5PZ) and
[AI-07 reviewed feedback](https://trello.com/c/pL25Swot) in the backlog until core acceptance.
The extension must distinguish computed mask measurements from literature facts, check crop/geometry
and reference compatibility, and avoid diagnosis from size alone. Existing
[W07-01](https://trello.com/c/IM0zPvP9) owns durable review integration; do not create a duplicate.

## Carryovers and gates

- [W02-08](https://trello.com/c/nqTumUtb): first pgvector/workflow prototype closed against retained
  October 14–17 evidence and moved to Week 2 Complete. This closes only that prototype.
- [AI-08](https://trello.com/c/HmDLnOYF): already delivered October 17 disease slice now marked complete,
  consistent with its existing Week 2 Complete placement.
- [W02-05](https://trello.com/c/lV0ikeEK) and [W01-05](https://trello.com/c/yU3zZfAz):
  outstanding hours and final closeout remain open; they do not block independent AI engineering.
- [W02-02](https://trello.com/c/jXIcbELc): source-unit/provenance failures remain; no new candidate
  handoff assumed. W02-03 stays conditional in backlog; no unchanged model rerun.
- AI-03 moved to To Do with its review/operator blocker explicit. Prior approvals are version-specific.
  No protected prompts/labels are requested or opened during this week's development.
- W05-02 must reuse existing corpus/index evidence and reconcile its broader milestone rather than
  rebuild by default. Legacy N4 is not a dependency of the current bounded literature path.
- Full selector remains parked; broader imaging DAG, DICOM ingestion and durable reviews are not
  silently declared complete by the new UI or this week's AI goal.

## Experiments, order and capacity

No training, model download, corpus expansion or broad sweep is launched by this plan. Bounded AI
checks require their own fixed cases, producing version, call/time/resource limits and fresh runtime
admission under AI-01. Preserve significant failed attempts and stop rather than silently retry.

1. **Tuesday:** finish board/plan, verify runtime and integrated UI, resolve concrete reliability gaps.
2. **Wednesday–Thursday:** volume adapter, then wording/selection qualification; offline preparation
   can proceed while the drive is unavailable.
3. **Friday:** freeze the candidate and run the bounded quality check; fix only demonstrated issues
   with explicit new versions and affected checks.
4. **Weekend:** buffer, Quinton walkthrough, weekly closeout and Week 4 planning.

These are dependency-based planning targets, not reserved working hours or promises. PANORAMA
proceeds in its owner's work area. Human capacity is unconfirmed; if time is tight, preserve a smaller
verified coverage slice and report the remainder instead of expanding into unreviewed answers.

## Decisions and coordination

| Date | Decision / evidence | Next action |
|---|---|---|
| Oct 20 | User requested Week 3 board preparation and an effective AI expert by week end | Five missing task cards created; existing PANORAMA and parent AI cards reused |
| Oct 20 | All four local service endpoints offline; data drive absent | Quinton will reconnect drive; fresh admission before live verification |
| Oct 20 | Drive reconnected; stale Docker bind repaired, existing DB recovered, UI contract access fixed | [Readiness result](../retrieval/WEEK3-DEMO-READINESS-2026-10-20.md); selected policy and one live answer verified; older DB exits still unexplained |
| Oct 20 | Bounded reliability closeout passed after retaining an invalid-request harness attempt | Earlier exit2 cause dispositioned as unknown; reopen on recurrence; advance to W03-03 |
| Oct 20 | User reports at least three active hours Oct 19 on CT input/run preparation elsewhere | Record as lower-bound estimate in [hours log](HOURS-LOG.md); no inferred extra time |
| Oct 20 | UI redesign is another chat's committed work in the shared checkout | Preserve it; publish only this chat's scoped changes to the retrieval branch |

No assignment submission, remote training result, protected acceptance or independent clinical
review is inferred. Trello is the status/evidence record; this file is the ordered weekly plan.

## Sunday review

- Completed outcomes and evidence: pending.
- PANORAMA outcome/remaining blocker and owner: pending handoff.
- AI quality outcome, selected version and remaining coverage: pending W03-05.
- Formal evaluation and measurement-extension gates: open.
- Human hours/exclusions and Week 2 closeout: pending confirmation; Oct 19 lower bound recorded.
- Lessons and Week 4 first implementation-ready task: pending review.

## October 20 current-scan amendment

Quinton prioritized connecting current-scan measurements after the volume literature closeout. AI-05 is now Week 3 In Progress under the [bounded contract](../retrieval/CURRENT-SCAN-VOLUME-CONTRACT-2026-10-20.md). Implement and test saved-mask volumes and safe current-study routing first, then return to W03-04 wording and W03-05 quality checks. This adds development scope, not a promise of whole-organ measurement accuracy or a waiver of formal RAG acceptance.

AI-05 native follow-up: [provenance and coverage adapter](../retrieval/NATIVE-MEASUREMENT-RESULTS-2026-10-20.md) is implemented and tested. The historical native example reaches a CT/inference boundary and correctly withholds size. The [current-producer review and handoff](../retrieval/ASSISTED-MEASUREMENT-HANDOFF-2026-10-20.md) identifies a pancreas-assisted pipeline, requiring a separate adapter rather than autonomous v2. The authorized training-owner handoff confirms no native prediction masks are retained by the current evaluator: it saves scores/reconstruction JSON only. Next: a separate qualified export path, then one bounded development output, assisted-adapter intake and anatomical review. No current-case resource fit or measurement accuracy is claimed. No inference/training or transfer was launched. W03-04/W03-05 core checkpoints remain pending.
