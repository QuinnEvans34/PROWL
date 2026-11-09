# Week 6 work plan — November 9–15, 2026

## November 8 evening handoff

The November7 preparation below is retained as dated history. The next week's
starting evidence has advanced:

- Original STU-Net12k is complete. The corrected continuation from that parent
  is running toward global24000, with its existing hourly monitor. First full
  raw14k validation Dice.353488 versus parent.371633 is an interim decline;
  review all remaining scheduled validations and selected/terminal checkpoints
  before deciding on the longer-training outcome. Do not change a live recipe
  in reaction to one point. The complete per-case14k export is published on
  Lenovo branch commit`02ba420`; it is not a filtered score.
- The [Mac confidence study](../operations/CAP-EXP-020-MAC-RESULTS-20261108.md)
  and [nine-policy spatial/boundary screen](../operations/STUNET-POSTPROCESS-RESULTS-20261108.md)
  are complete. Confidence cuts did not improve Dice; fixed5mm component
  filtering gave original12k developmentDice.394938 with unchanged recall and
  component hits. The entire policy grid and failures are retained; this is
  postprocessing evidence, not model learning or independent confirmation.
- The user made [fixed5mm postprocessing](../evaluation/SEGMENTATION-POSTPROCESSING-POLICY-V1.md)
  a standing requirement for future segmentation integrations. Preserve raw
  outputs and paired evaluation, qualify applicability/detection/recall per
  model, and retain explicit raw fallback for missing predicted pancreas.
  Do not retrofit this into the currently frozen evaluator or selection.
- [Six exact training-input replays](../operations/STUNET-INPUT-AND-SPATIAL-FINDINGS-20261108.md)
  found lesion labels disappearing at the8³ auxiliary target in3/4selected
  positive patches, while full-resolution labels survive. The isolated
  [16,8,4,2,0]/30 loss-weight candidate is CPU-tested, not CUDA/launch ready.
  Keep it as the next single-factor training proposal; do not mix normalization,
  sampling and spatial filtering into that comparison or queue another GPU job
  merely because preparation is complete.

Monday order: review new complete continuation results and backup/tracking
evidence; reconcile the formal baseline/comparison requirements; then prepare
the smallest matched loss ablation if still justified. While Lenovo trains,
Mac can finish the source-grounded retrieval/answer evaluation protocol and
reviewer checks for the proposed November14 participant walkthrough. Confirm
the session details and personal active hours/submission separately; unattended
compute is not human work time. Tonight's default is to leave the admitted run
unchanged with AC/drives/app available and its existing monitor active. No new
scientific launch or schedule is created by this handoff.

Prepare a defensible model decision and measure retrieval/answer quality while
finishing the open baseline and reviewer requirements. This is the November 7
preparation requested by Quinton; Week 5 and its outstanding hours/submission
remain open through November 8. No new GPU run is queued by this plan.

## Proposal commitment

The approved master schedule names **Model experiment and retrieval evaluation**:
complete one controlled model comparison, evaluate the false-alarm tradeoff, and
measure retrieval quality. Expected evidence is a documented model decision and
operating curve, retrieval metrics and grounded-response checks. The formal model
comparison depends on G4; completed exploratory KD or supplied-region transfer
cannot retrospectively satisfy that dependency.

## Work order

| Priority and owner | Work and inputs | Done condition |
| --- | --- | --- |
| 1. Mac + Lenovo: finish the available model evidence | Use completed KD selected/terminal results and all scheduled STU-Net results after its existing run finishes | Source-bound series, per-case errors, selection rules, failed attempts, tracking, checkpoints/backups and cleanup reviewed; incomplete evidence remains explicitly pending |
| 2. Mac + Quinton: reconcile G4 and select the formal comparison | Start from the exposed autonomous 63-score/seven-failure record and seven-case visual review; retain spatial-unit/provenance and cross-device qualification gaps | An admitted autonomous baseline and an evidence-selected, prospective comparison contract; if not achievable, document the precise shortfall and agree a scoped fallback without declaring G4 passed |
| 3. Mac: retrieval and grounded-answer evaluation | Existing pinned 14-source/1,179-passage corpus, eligible questions and source-linked expected support | Frozen question roles, protocol and failure rules; report retrieval relevance/recall and answer support, completeness, citations, refusal and cold/warm latency separately from exposed UI regressions |
| 4. Mac + Quinton: reviewer walkthrough | Existing saved scan/conversation fixtures, November 7 engineering checks and Plan 11 script | Current production viewer/service/presentation check, then actual role-appropriate participant session with observations and prioritized follow-up; scheduling alone is not acceptance |
| 5. Quinton + Mac: weekly evidence | Week 5 closeout and this week's immutable reports/commits | User-confirmed active hours, correct carryovers and course submission status; unattended compute remains separately accounted |

The preliminary aunt/fallback session is planned for **Saturday, November 14**.
Exact time, actual industry role and participation/note-taking permission are still
unconfirmed. Main Week 7/G7 acceptance remains visible. No feedback is invented.

## First model-review task

November 7 follow-up: [STU-Net interim error analysis](../operations/STUNET-INTERIM-ERROR-ANALYSIS-20261107.md)
uses all 70 saved cases at 2k/4k/6k. Small-total-lesion cases remain particularly
weak; metadata does not establish spatial causes or final performance.
[CAP-EXP-020](../operations/CAP-EXP-020-PROPOSED-20261107.md) is registered as a
proposed bounded confidence-policy screen with synthetic code and explicit
lesion-preservation guards. It is exploratory, not a preselected substitute for
the formal G4-dependent comparison. No actual inference runner, launch receipt,
automatic successor or extra training run is issued. Review the full current
training result before deciding whether to admit that screen.

Use the new [read-only preparation tool and packet](../operations/WEEK-06-COMPARISON-PREPARATION-20261107.md).
Completed KD selected lesion DICE is .383593 control / .389084 treatment; terminal
is .381964 / .383439. Component overlap declines 39/45 to 37/45. These results
support a limited descriptive assessment, not automatic promotion. The original
control cleanup failure and all attempts remain recorded.

STU-Net is still running at this plan's preparation. Lenovo owns the authorized
12k/60h experiment, receipt, producing files, GPU and hourly monitor. Review all
six full 70-case validations, selected and terminal checkpoints, per-case misses
and false alarms, backup equality, MLflow closure and cleanup when available.
An aggregate dashboard cannot establish final closeout. Do not extend the horizon,
retry, change pins or launch a scratch arm merely to fill a comparison table.

Verify case/reference identities, units, metric definitions, raw output policy,
geometry and provided-region versus autonomous inputs before matching results.
The same 70 count is insufficient. Differences in architecture, pretraining,
input windows and 12k versus 24k horizons prevent an isolated causal attribution.
Unresolved patient/pretraining linkage restricts claims; it is not proof of
independence. The four-positive Universal screen remains publisher-model inference.

Review KD-specific aligned saved errors for the recorded gain/decline/miss cases
before proposing a mechanism. The existing autonomous gallery shows that cropping
alone does not explain all misses, near/far false positives or spillover. These are
different comparisons; reuse of a gallery is not KD spatial verification.

## Contract before any new comparison

After G4, select the smallest intervention justified by error frequency, severity,
an isolatable mechanism and available compute. Freeze the question/hypothesis,
control and changed factor(s), model/recipe/input identities, cohort/reference
roles, horizon, selection and terminal endpoints, metrics/empty/failure rules,
guardrails, uncertainty unit, resources and stop conditions before execution.
Report pancreas and lesion overlap, multi-lesion coverage, missed lesions,
false-positive burden, empty-case alarms and complete failure denominators.

An operating-curve or policy comparison may be cheaper than another training run,
but requires permitted raw outputs, development-only selection and its own frozen
contract. No threshold, largest-component filter, verifier or tighter crop is
selected from these aggregate observations. Preserve raw results and all failures;
never discard seven failed cases to present a full 70-case score.

If patient linkage remains unresolved, report descriptive study/case results and
the exact limitation; do not label bootstrap samples independent patients. If G4
cannot close, retain the formal milestone gap and discuss an honest fallback with
Quinton. Do not retroactively preregister the completed KD or transfer study.

## Capacity and review checkpoints

Monday: review the latest completed training evidence and confirm the baseline
admission gaps. Tuesday/Wednesday: freeze the eligible formal model/operating
comparison and retrieval protocol, then execute only admitted work. Thursday:
review failures and remaining evidence; avoid repeated tuning on protected cases.
Friday: finish the production walkthrough check and prepare the participant
packet. Saturday: preliminary session if confirmed. Sunday: record findings,
confirmed hours, remaining gates and Week 7 handoff.

One primary Mac coding task may run alongside the single Lenovo GPU job. Existing
metadata, CPU tests and saved-result UI checks need no training pause. No answer
model, new inference or second training job is authorized by this schedule.
Week 9's buffer and Week 10 delivery remain protected.

## Evidence and board

- [Week 5 technical closeout](WEEK-05-EVIDENCE-CLOSEOUT-20261107.md) retains G3/G4/G6/G7 gaps.
- [Plan 06](../implementation/06-evaluation-and-model-experimentation.md) governs
  formal comparison; [master plan](../MASTER-PLAN.md) remains the approved schedule.
- [Reviewer checks](../testing/REVIEWER-FLOW-20261107.md) and
  [Plan 11](../implementation/11-stakeholder-validation.md) distinguish engineering
  evidence from actual participant acceptance.
- Trello W06-01 and W06-02 retain their existing deadlines and dependencies;
  preparation does not mark them completed or roll the board early. W05-04 still
  needs Quinton's hours/submission confirmation. W05-08 retains KD spatial/patient
  follow-up even though compute and quantitative review are complete.
