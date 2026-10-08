# Week 1 living work plan

**Dates:** October 5–11, 2026 (America/Denver)  
**Updated:** October 8, 2026  
**Owner:** Quinton Evans  
**Status:** In progress — closeout evidence not yet reconciled  
**Weekly commitment:** Architecture and test readiness; a concrete starting point for Week 2.

This is the working task list for the week. Update it as work progresses instead of creating another
competing queue. The [approved Week 1 baseline](WEEK-01.md), [master plan](../MASTER-PLAN.md), and
component contracts retain their scope authority. Historical packets remain evidence, not current
instructions to repeat their work. This plan does not require the entire product or a particular
Dice score to be finished in Week 1.

## Proposal alignment — reviewed October 8

Source: [approved proposal v3.8](../../../Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx),
sections 2–4 and 6, and [technical appendix v3.1](../../../Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx),
sections A2–A5 and A8. Source hashes match [approved sources](../../../references/governance/APPROVED-SOURCES.md).
The original documents remain unchanged.

| Week | Approved scheduled outcome | Consequence for our planning |
|---|---|---|
| 1 | Architecture, acceptance criteria, workflow design and test plan | Reconcile evidence and specify missing boundaries; a complete product is not required this week |
| 2 | Frozen protected cohorts; patient separation, manifests and repeatability tests | Primary next-week deliverable; reuse existing manifests and audit their evidence before extending them |
| 3 | PANORAMA integration, label mapping, provenance, exclusions and duplicate checks | Preserve this commitment alongside PanTS; do not silently replace it with training infrastructure |
| 4 | Unified reproducible, restartable preprocessing and orchestration | Early training preparation should contribute reusable pieces to this deliverable |
| 5 | Autonomous imaging baseline and versioned, queryable retrieval foundation | Raw CT must reach predictions without reference-mask localization; report errors and limitations |
| 6 | Controlled model comparison and retrieval evaluation | Record a model decision, including false-alarm tradeoffs; improvement is not guaranteed |
| 7 | UI refinement and stakeholder review | Integrate review actions and record feedback |
| 8 | End-to-end integration, tests and locked evaluation | Finish the committed system and documentation drafts |
| 9–10 | Protected stabilization buffer, then final delivery | No new features consume the buffer or delivery week |

The product path is raw CT → automatic pancreas localization/region selection → pancreas and lesion
segmentation → original-coordinate masks, measurements and review-order score → reviewer accept/edit/reject
with persisted history. Literature retrieval remains a parallel committed capability with citations and
unsupported-answer handling. This is a research annotation-assist system, not a clinical diagnostic claim.

Reference masks remain valid training labels and evaluation targets. They must not supply or repair the
region during autonomous prediction. The reference-region arm remains useful for measuring the autonomy
gap. The appendix allows single-stage, cascaded or other anatomy-aware models; test the cascade first
using existing work, then decide from measured performance. Matching published PanTS performance is
Quinton's research aspiration, not a promised score or a Week1 acceptance condition.

## Outcomes we need by Sunday

- [ ] A clear, current account of the product architecture and implemented versus missing components.
- [ ] Reproducible Python and UI development checks, with remaining gaps explicitly resolved or reported.
- [ ] Every Week 1 requirement linked to evidence or a named blocker; no blanket completion claims.
- [ ] A specified Week 2 queue with owners, dependencies, experiment questions and finish criteria.
- [ ] Course deliverables, human hours and Trello completion reconciled with actual evidence.

## Starting evidence — preserve and build on it

| Area | What exists | What this does not establish |
|---|---|---|
| Design | Twelve approved component designs, architecture/contracts and traceability | All components implemented or full G0 verification |
| Training | New configurable full-cohort session/executor, SuPreM initialization, geometry v2, backups and checkpoint continuation | Completed 24k run, autonomous raw-CT performance or PanTS benchmark parity |
| Current experiment | FULL-SEG-MAC-001; 1,333 train/75 development; resumed from13,500 in `full_segmenter_suprem_mac_01_resume01`, owned session96730 | Live progress must be read from the log; this document is not a live monitor |
| Development scoring | Reference-pancreas crops; tensor-grid positive-case lesion Dice | Reference-free prediction or comparable native full-scan Dice |
| Localization | Existing experimental localizers and a predicted-ROI adapter tested on invented inputs | A qualified integrated real-data cascade; prior localizers had coverage/overprediction issues |
| UI | React/NiiVue foundation; prior build,18unit and1synthetic-browser checks | Current whole-app acceptance, real scan rendering/alignment or durable review persistence |
| Retrieval | Prior synthetic/native foundation and binding evidence | Current owner status, actual-domain rehearsal completion or a live evaluated corpus |
| Second machine | Lenovo specs commit `0c78ff7`: RTX4060Laptop/8GBVRAM,32GBRAM; user reports1TB external drive | CUDA compatibility of our new trainer, measured fit or a configured training environment |

Evidence: [training guide](../../training-full-segmenter.md), [experiments](../../experiments.md),
[UI foundation](../testing/UI-FOUNDATION-2026-09-20.md),
[predicted-ROI adapter](../operations/PREDICTED-ROI-ADAPTER-RESULTS-2026-10-06.md),
[earlier evidence map](WEEK-01-EVIDENCE-MAP-2026-10-06.md).

## Required Week 1 closeout work

Statuses: **Ready** = specified and available to start; **In progress** = actively owned;
**Blocked** = named unmet dependency; **Done** = finish criteria and evidence recorded.
An unresolved mandatory gate remains open; documenting it does not turn it into a pass.

| ID | Task | Status | Owner | Depends on | Finish criterion |
|---|---|---|---|---|---|
| W01-C01 | Reconcile actual architecture and current status | Ready | Quinton + this development chat | Existing code, plans and current training evidence | One accurate component/status map; misleading current-status statements superseded |
| W01-C02 | Verify Python/UI development readiness | Ready | This development chat | Existing environment and test records | Documented reproducible commands and evidence for required checks; specific defects fixed or blockers retained |
| W01-C03 | Specify product integration boundaries | Ready | Quinton + this development chat | C01; existing contracts | Raw-CT flow and first UI integration slice have inputs, outputs, failure behavior and checks |
| W01-C04 | Reconcile requirements, risks and other workstream status | Ready | This development chat; existing retrieval owner retains its work | C01–C03 evidence; owner status | Each Week1 criterion mapped; retrieval/other unknowns labeled; no invented completion |
| W01-C05 | Select and specify Week2 development/experiments | Ready | Quinton + this development chat | C01–C04; model result when available | Ordered Week2 plan with bounded tasks and proposed experiment comparison |
| W01-C06 | Weekly review, course evidence, hours and board closeout | Ready | Quinton + this development chat | C01–C05 | Honest gate decision; confirmed course status; hours separated; completed cards reconciled |

### W01-C01 — Reconcile architecture and current status

**Purpose:** Ensure the next session starts from the software we actually have.

- Trace raw CT → preprocessing → predicted localization → region selection → segmentation →
  original-coordinate output → case package → reviewer UI. Show literature retrieval separately.
- Mark each boundary implemented, tested only with invented inputs, tested on real data, or missing.
- Explain the current reference-crop training/evaluation route separately from autonomous inference.
- Reconcile stale top-level status in `operations/CURRENT-CHECKPOINT.md`, the documentation hub and
  Week1 checklist; preserve dated history and retirement of old runs.
- Map requirements to existing component plans rather than write a new architecture from scratch.

**Deliverable:** Updated navigation/status and one linked architecture map.  
**Verification:** Compare claims to code and retained results; all local links resolve.  
**Not included:** Replacing models, changing the active run, or claiming architecture choice is experimentally settled.

### W01-C02 — Python and UI development readiness

**Purpose:** We can write and verify software on the Mac without the full training drive attached.

- Inventory the active supported Python and Node environments, dependency pins and existing evidence.
- Define the required fast Python scope; distinguish model-free, native-GPU, real-data and release checks.
- Reuse the UI foundation: `ui/package.json` already defines `test:run`, `test:e2e`, and `build`.
  Check the pinned Node version and lockfile; do not install or upgrade blindly.
- Reuse applicable results. Run only missing/stale/affected checks needed for the readiness claim;
  keep expensive model work off the active training accelerator.
- Identify a minimal synthetic/sample-data fixture set for UI and pipeline development.
- Fix concrete setup/test failures; preserve diagnostic output. Document one clear entry sequence.

**Deliverable:** Updated setup/testing instructions and a check/result table with environment/commit/scope.  
**Verification:** Selected checks actually pass; unsupported or untested areas remain explicit.  
**Not included:** Running every historical test, a UI redesign, deployment or full clinical-image validation.

### W01-C03 — Product integration specifications

**Purpose:** Make the next coding task small enough to implement and review.

- Reuse the case-package, prediction, spatial-transform and review-event contracts.
- Specify the first UI slice: read a case package, display case/model identity and available outputs,
  and handle loading, missing, failed and stale predictions.
- Name the source and destination modules and the exact fixture used to demonstrate the slice.
- Define independent evaluation joins: reference masks may score predictions, never locate or repair
  the region during autonomous inference.
- Keep durable reviewer decisions and retrieval integration as separately sized tasks.

**Deliverable:** An implementation-ready task specification linked here and in Week2.  
**Verification:** Inputs/outputs/owner/failures/test/finish criteria are all named.  
**Not included:** Requiring a production localizer or complete end-to-end application this week.

### W01-C04 — Requirement and risk reconciliation

- Use the existing43-requirement evidence map; do not infer current acceptance from old test counts.
- Map every Week1 acceptance item to current evidence, a remaining task, or a specific blocker.
- Confirm the retrieval lane's present state from its evidence/owner before repeating its work.
- Track remaining risks: oracle evaluation, localization misses, resize losses, false positives,
  annotation/subject uncertainty, pretraining membership, hardware portability and independent backups.
- For each high-impact risk, name a practical check and fallback; avoid turning every research unknown
  into a prerequisite for all development.

**Deliverable:** Updated evidence map and explicit G0-design/G0-verification decision.  
**Verification:** Quinton can see what is complete and what prevents any unclosed gate.

### W01-C05 — Week2 plan and experiment selection

The [two-week autonomous prediction investigation](../imaging/AUTONOMOUS-PREDICTION-INVESTIGATION.md)
tracks the matched cascade comparison, alternative architectures, specialist routing and PANORAMA
experiment questions for October8–22. Keep findings there and weekly task ownership here.

- Anchor the main Week2 outcome to proposal section6: frozen, reproducible protected cohorts.
- Inventory existing manifests, patient/group identity evidence, split assignments, annotation provenance,
  duplicate/exclusion records and cohort hashes. Distinguish reference-empty cases from verified negatives.
  Name unresolved evidence rather than claiming existing train/development counts prove separation.
- Specify the smallest missing separation/repeatability checks and a portable input manifest. Keep stable
  case identities and cohort membership separate from machine-specific paths.
- Advance raw-CT inference and the usable review application in parallel when the primary outcome is covered.
- First imaging comparison proposal: same segmenter/cases/native scoring, reference-region versus
  predicted-region inference. Count localization failures and missed lesions in the denominator.
- Inspect existing localizer eligibility/results before choosing reuse, fine-tuning or new training.
- Keep single-stage full-CT training as a planned challenger; architecture superiority is unproven.
- Separate architecture/precision/device changes so conclusions remain interpretable.
- Include the Lenovo port as a proposed task with a concrete first experiment, not an indefinite
  infrastructure project. One fixed, resumable training job is its first operational finish line.

**Deliverable:** `WEEK-02-WORK-PLAN.md` created during Sunday planning, with selected tasks specified.  
**Verification:** The first task can start without reconstructing this conversation; experiment arms,
metrics, cohort, runtime, storage, failure handling and expected outputs are stated before launch.

### W01-C06 — Close the week

- Confirm the What/Why/How presentation and image submission; prepared text is not submission evidence.
- Confirm other course submissions from Quinton or receipts, without submitting anything implicitly.
- Reconcile human hours in [HOURS-LOG](HOURS-LOG.md); exclude unattended work and agreed assignment exclusions.
- Update existing Trello cards from evidence; move only finished work at actual weekly close.
- Record completed outputs, open mandatory gates, lessons and carryover reasons below.
- Quinton reviews the closeout and next week's priorities. Week1 may be partially complete if a required
  gate remains unmet; optional features do not keep it open indefinitely.

## Parallel work and proposed follow-ons

These stay visible but are **not additional Week1 acceptance requirements**. Planning here does not
start downloads, another training job or another chat.

| ID | Work | Next concrete output | Dependency / status |
|---|---|---|---|
| W01-P01 | Finish and review current full training run | Terminal outcome, best/latest backups, development curve and limitations | Running when this plan was created; no automatic retry or model promotion |
| W01-P02 | Lenovo as stationary training machine | Portable cohort/data provisioning plan; bounded CUDA/session/launcher port; fit and save/resume checks; one chosen run | Quinton confirms dedicated uninterrupted home use for the remaining ten-week plan; 1TB external drive has no dataset loaded; actual environment/drive need inspection |
| W01-P03 | Reference-free inference diagnostic | Matched localizer → crop → current segmenter → native output test | Existing localizers/adapter need real integration and geometry compatibility review |
| W01-P04 | Retrieval integration | Current owner handback and next small interface task | Owner status not yet refreshed; no duplicate dispatch |

## Recommended development order for the rest of the week

1. **Thursday:** C01 and C02 inventory; confirm course submission/presentation status.
2. **Friday:** Resolve concrete readiness defects; finish C03 and C04 specifications/evidence.
3. **Saturday:** Finish selected carryover checks; review P01 outcome if available. Select a bounded
   integration task only if required closeout work is under control.
4. **Sunday:** C06 review and C05 next-week planning using the weekly template.

These are planning targets, not booked human hours or promises about training completion. If time
is short, prioritize reproducible development and a clear Week2 start over new infrastructure.

## Working decisions and open questions

| Item | Current position / next decision |
|---|---|
| Main architecture | Test two-stage first; single-stage remains a challenger, not rejected |
| Main outcome | Autonomous raw-CT performance; reference-crop Dice is a diagnostic |
| Hardware split | Confirmed by Quinton Oct8: Lenovo stays at home dedicated to training throughout the plan; Mac is the development machine. CUDA port/fit remain unproven |
| Storage | Lenovo external 1TB drive has no dataset loaded. First inventory usable space/filesystem, then size and provision the selected cohort plus derived data/checkpoints with content verification. Mac keeps development fixtures/selected artifacts; no drive formatting assumed |
| Next-week priority | Proposal Week2 protected cohorts first; Lenovo setup and early autonomous experiments can overlap without replacing that deliverable |
| First product slice | Propose case-package-to-viewer adapter; confirm after C01 inventory |
| Other workstream status | Refresh retrieval evidence with its existing owner; do not infer progress from old notes |

## Living update log

| Date | Change / decision | Evidence / effect |
|---|---|---|
| Oct8 | Created at Quinton's request; weekly Sunday planning adopted | Reconciles current training/resume progress with original Week1 architecture/test scope |
| Oct8 | Read approved proposal/appendix; confirmed dedicated Lenovo and autonomous prediction priority | Week2 primary outcome corrected to protected cohorts; early compute/inference work supports the scheduled Week4–5 outcomes |

## Sunday closeout — fill during review

- **Gate result:** Pending.
- **Completed task IDs and evidence:** Pending.
- **Unfinished mandatory tasks / reason / owner:** Pending.
- **Optional work deferred:** Pending.
- **Training outcomes and next hypothesis:** Pending; no forecast treated as a result.
- **Human hours:** See HOURS-LOG; reconcile exclusions with Quinton.
- **Week2 top outcomes and first task:** Pending Sunday selection.
- **Quinton review:** Pending.
