# Week 4 work plan — October 26–November 1, 2026

Prepared October26. This is the execution plan for the week, not a replacement for
the approved proposal or frozen experiment recipes. [Trello board](https://trello.com/b/vac4k8Po/prowl-quinton-evans-capstone).

## Weekly outcome

Make the existing software and training path dependable: qualify a restartable
cross-stage workflow, finish teacher targets and qualify the full distillation
executor, and demonstrate the connected reviewer experience. A stronger model is
the experimental objective, not a promised result. Full completion of both24k
training arms by Sunday is not promised.

The original proposal's Week4 milestone is **reproducible training inputs and an
executable DAG with valid-stage reuse and recovery from an injected failure**.
Single-checkpoint resume alone does not satisfy it. KD is later user-authorized
experimental work. Reference comparisons and reviewed training feedback (AI-06/07)
remain final commitments; they have not been silently removed or accepted.

## Starting evidence and Week 3 disposition

- PANORAMA's original exploratory integration is complete, including the reported
  24k mixed-source comparison. The negative result was not promoted. The newer
  physical-window port is separate work. [Corrected handoff](../data/PANORAMA-HANDOFF-AUDIT-2026-10-20.md).
- Reviewed literature answers and general source extracts work in bounded cases.
  Exact quotations are not equivalent to fluent synthesis, relevance or completeness.
  [Current general-answer evidence](../retrieval/GENERAL-SOURCE-ANSWER-2026-10-23.md).
  Preserve the failed original evaluation; questions used for repair are exposed
  regression material. Fresh independent acceptance remains outstanding.
- A connected reviewer slice exists; representative end-to-end acceptance remains
  separate from its implementation. [Integration record](../implementation/REVIEW-INTEGRATION-2026-10-21.md).
- Latest recorded teacher continuation04 verified/reused313 saved targets and began
  fresh inference. This is a startup observation, not today's live completion count.
  Full1333 coverage is required. [Durability record](../operations/MAC-KD-DURABILITY-20261025.md).
- Actual two-case MPS KD and cold recovery passed; this does not qualify the full
  cohort executor. [Training preparation](../operations/MAC-RSUPER-TRAINING-PREPARATION-20261023.md).

## Ordered work and observable completion

Owner is Quinton with Mac development unless noted. Training-laptop work remains
with its owner; no interruption or additional cross-chat request follows this plan.

| Card | Starting status / dependency | Deliverable and stopping condition |
| --- | --- | --- |
| [W04-01 Restartable DAG](https://trello.com/c/Z9QSh78P) | Queued; original proposal priority | Inventory existing stage contracts first. Connect only missing stages. Record input/output identity, valid reuse, stale-output rejection and injected-failure recovery across stages. Stop when the bounded executable workflow passes; document wider gaps instead of claiming universal recovery. |
| [W04-02 Teacher targets](https://trello.com/c/1AZAsgib) | In progress; KD-MAC parent | Complete and verify1333 training targets with exact membership, hashes, native geometry and resource accounting. Preserve completed outputs and failures. Stop on a failed guard; no automatic retry. |
| [W04-03 Full executor and matched launch](https://trello.com/c/pyQUMV4S) | Queued; depends on full targets and readiness | Bind corrected annotations/targets; qualify sampling, native evaluation, actual full-provider MPS zero/positive-KD updates, independent backup and cold restore. Freeze matched recipes and launch under existing authorization only after all gates pass. Finish with recorded advancing scientific updates or a specific preserved blocking gate. |
| [W04-04 Reviewer and assistant walkthrough](https://trello.com/c/KPvynqav) | Queued; existing UI/services | Open case → inspect contours → qualified measurements or limitation → cited literature → save/reopen/revise review. Check failed-save draft retention. Report support, completeness, citations, refusal and latency separately in Research/Workbench. Fix demonstrated blockers; stop after a reproducible walkthrough and explicit remaining limitations. |
| [W04-05 Weekly closeout](https://trello.com/c/Ws4HcntT) | Queued; Sunday review | Evidence-linked outcomes, remaining gates, next-week handoff and Quinton-confirmed human hours. Never imply course submission or count unattended processing as human work. |

W04-02/03 are execution slices of [KD-MAC](https://trello.com/c/natlITz0), not
additional experiments. W04-04 consolidates W03-02, W07-01, AI-04 and AI-05 for this
week; passing the slice does not automatically close those broader commitments.

## Sequence and resource use

1. Monday: reconcile board and plan, then inventory W04-01's existing contracts and
   recovery evidence. Teacher generation continues under its existing supervisor.
2. While targets run: use CPU-only/synthetic workflow checks and existing saved
   review artifacts. Do not edit active producing pins or compete for the Mac GPU.
   Schedule live answer/renderer performance checks in a deliberate available slot;
   record contention and cold/warm conditions instead of blaming UI from one timing.
3. Once targets finish: verify the complete manifest, qualify the full executor,
   then freeze and launch the matched comparison if all gates pass. Same student,
   initialization, data, sampling and budget; KD is the intended changed factor.
4. Before Sunday: demonstrate the integrated path, review completed model evidence
   for missed lesions, false positives, contour quality, measurement error and
   coverage separately. Do not substitute Dice or fluent answers for these checks.
5. Sunday: close evidence and confirmed hours; carry forward unmet conditions honestly.

Keep the existing50GB Mac storage admission rule and experiment-specific external
limits. AC power and mounted data drive remain execution prerequisites. User-directed
pauses preserve completed outputs but extend calendar duration. Unknown teacher
development membership keeps KD results exploratory. No new polling automation,
framework, full corpus-selection run or extra scientific factor is part of this plan.

## Carryovers and capacity

Original task IDs and histories remain. W01-05/W02-05/W03-06 await human-hour or
closeout confirmation; they do not block engineering. W02-02 retains unresolved
source-unit/provenance failures until specific evidence closes them. AI-05 retains
measurement qualification; AI-06/07 stay visible in backlog pending their dependencies.
Older completed lists are preserved. Only Week3 Complete remains as a Week3 column;
unfinished work is queued in Week4, not marked completed to tidy the board.

Available human hours and laptop availability are unconfirmed. Plan one primary
engineering task alongside the teacher job. If time is tight, prioritize the proposal
DAG deliverable and correct training readiness over additional assistant features.
No machine-hour estimate is entered as personal work time.

## October26 setup record

Renamed Week3 To Do/In Progress to Week4, created Week4 Complete, retained Week3
Complete, corrected the PANORAMA completion record, refreshed the dashboard and
stale AI/KD/reviewer descriptions, and created W04-02 through05. Existing broad
carryovers are queued; only the KD parent and target-generation slice represent
active execution. This planning change does not alter or restart any running job.

### October26 implementation update

W04-01 is now In Progress. Its bounded CPU recovery slice is implemented: deterministic dependency
plans, validated reuse, preserved interrupted attempts and an invented native-case/citation package
smoke with operator commands.98 checks pass; standalone repeated execution reuses all stages and an
evidence-setting change rebuilds only evidence/bundle. [Results](../orchestration/CPU-WORKFLOW-RECOVERY-20261026.md).
This is partial milestone evidence, not full G3 or production training integration. Teacher execution
was not changed. Next W04-01 decision is D-201 selection and the smallest production adapter qualification.

### October26 continuation

D-201 now selects the repository runner: isolated Prefect clean-flow8.11s failed the existing5s
criterion; rerun3.38s passed, and unrun trials remain explicitly unmeasured.
[Selection evidence](../orchestration/TOOL-SELECTION-RESULTS-20261026.md). The first read-only saved-package
adapter verifies source bytes and prepares exact review-target IDs; existing development-package
execution/reuse passed, with107 regression checks. [Handoff](../orchestration/SAVED-PACKAGE-HANDOFF-20261026.md).
Full G3, live literature-response linkage and training/resource integration remain open.

### October26 literature linkage

The offline case/literature handoff is delivered using the actual UI answer validator, original
capture bytes and explicit case/capture pins.122 backend/workflow tests plus1 runtime guard and72 UI
tests pass. The existing saved package and retained public answer completed and reused all4 stages
under Node24; no fresh answer-quality claim. [Handoff and limits](../orchestration/CASE-LITERATURE-HANDOFF-20261026.md).
Live UI capture/review-history association and remaining G3 gates remain open; teacher execution unchanged.

### October27 reviewer verification

W04-04 moved to In Progress. An isolated browser walkthrough using the production
review panel and API passed lost-save-acknowledgement recovery, duplicate-free
retry, literature attachment/citation reopening, append-only revision and API
restart persistence. [Evidence and limits](../orchestration/REVIEWER-WALKTHROUGH-20261027.md).
This closes the synthetic persistence slice, not the full real-case walkthrough
or live answer quality/latency checks. W04-02 teacher generation continues;
W04-03 still requires complete targets and actual executor qualification.
Next CPU priority is the remaining W04-01 resource/schema qualification; retain
W04-05 closeout and the separate measurement requirements.
