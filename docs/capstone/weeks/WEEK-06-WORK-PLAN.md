# Week 6 work plan — November 9–15, 2026

## November 10 priority: improve small-lesion contours

Week 6's model focus is to find out whether better supervision, a local refiner,
or training hyperparameters improve lesion overlap without increasing false
positives. Target by **Friday, November 13**: a matched supervision result and a
known-location refiner feasibility result, if hardware qualification passes.
Target by **Sunday, November 15**: finish the first four Optuna trials and, if
the refiner passes, measure its automatic proposal path. A verified negative
result counts; do not guarantee 0.50 Dice or independent confirmation this week.
This update changes priorities only. The existing reviewer/retrieval commitments
and formal G4 dependency remain visible.

Planned Week 6 cards: [W06-17: supervision](https://trello.com/c/JaQ2AMD8),
[W06-18: refiner](https://trello.com/c/KGeyILOB), and
[W06-19: Optuna](https://trello.com/c/cgdd1AqU). These are To Do, not active jobs.

**Starting evidence.** The 24k saved-output core rule reached 0.436709 Dice on
the 36 positive development scans, with the mean for the five under-1-mL
total-burden scans at 0.144914. That rule preserved hits on 39/45 components;
five of the six misses were under 1 mL, the other was 2.33 mL. Giving it the
complete masks of the six missed components while leaving existing predictions
would yield only 0.461436 Dice. The Lenovo's reported historical best on those
same five small cases was **0.2384** (varied-view 18k). Keep that as a comparator
if case/reference identities and geometry match; do not attribute the
cross-model difference to sampling or assume that an ensemble will help.
[Saved core experiment](../evaluation/STUNET-24K-CONFIDENT-CORE-RESULTS-20261110.json)
and [error audit](../evaluation/STUNET-24K-SELECTED-DICE-AUDIT-20261110.json).

### 1. Coarsest supervision: one changed loss term

- Use the existing CPU-verified candidate
  `src/training/stunet_supervision_candidate_v1.py`. Compare weights
  `[16,8,4,2,1]/31` versus `[16,8,4,2,0]/30`; keep the five outputs,
  nearest target reduction, CE + Dice formula, architecture and optimizer state.
  Verify zero loss gradient for the omitted scale, without silently freezing
  weights or discarding AdamW state. Keep the active 26k→36k recovery untouched.
- Bind the original 12k checkpoint, optimizer/RNG, corrected 1,333-case train
  set, exact sampling/augmentation addresses, and original corrected
  continuation's LR schedule. First compare **2,000 updates → global 14k**,
  using the identical schedule prefix and one full native 70-scan validation.
  Reuse the completed corrected run's 14k report only if ancestry, addresses,
  runtime and evaluator match and the baseline path passes parity
  qualification. Otherwise run a fresh matched control or report the blocker;
  never substitute the 24k or 36k result as control.
- Qualify actual CUDA updates, per-scale/component target survival, fixed input
  replay, checkpoint/independent backup and cold restore. Evaluate raw learning
  effects first; record paired raw and standing fixed 5 mm results separately.
  Keep the confident-core rule fixed as a labeled secondary comparison if
  matching saved margins are available. No new postprocessing search.
- **Estimate:** 2–3 hours setup and evidence review; **6–8 GPU slot hours**
  for qualification, one new 2k arm and full validation, or **11–14 hours**
  if the control needs replay. A complete 12k arm with six full validations
  is a separate **30–36 hour** decision. A null 2k result does not rule out
  a late effect. If coverage logs show too few usable small-lesion patches,
  prepare a separate sampler experiment that replaces some existing positive
  crops with small-component-centered crops while preserving negative/context
  slots, case coverage, and total steps. Do not combine it with this ablation.

### 2. Lesion refiner: test contours before building a detector

- On the Mac, build a versioned native-coordinate crop/restore adapter, patch
  manifest and component evaluator. Fit a small 3D segmentation refiner using
  only admitted training cases: small-component-centered positives with
  center jitter, some larger examples, and pancreas-region negative patches.
  Retain as much native resolution as practical; record slice spacing,
  physical field of view and coverage. Resampling does not add source detail.
  Test full-affine crop restoration, padding, label identity, and empty cases.
- Use the same trained refiner at known lesion locations on a fixed diagnostic
  subset (all available <1 mL components plus larger controls). Report
  component Dice versus the incumbent on matched locations, including zero
  overlap, missed tissue and extra predicted tissue. Reference boxes are used
  only in this labeled diagnostic evaluation. Predeclare a practical pilot
  gate of **+0.03 mean Dice on the small components** without a decline on the
  larger controls. A box-assisted result is neither automatic nor independent.
- If that passes, search the qualified predicted pancreas region with its
  fixed physical margin. Use a bounded dense-window score or candidate
  heatmap so regions the current mask misses can still be proposed. Freeze
  proposal count/threshold, duplicate merging and mask fusion before scoring.
  Compare the predicted-proposal pipeline with the incumbent on the same 70
  scans, report proposal coverage separately from refinement, and measure
  one-to-one component detection at a matched false-positive-per-scan budget,
  whole-scan Dice, small-lesion overlap, empty alarms and FP volume. If using
  provided pancreas regions during feasibility, label that scope separately
  from autonomous localization.
- **Estimate:** **5–8 hours engineering/CPU preparation**, then **2–6 GPU
  hours** for the qualified compact refiner and diagnostic result (unmeasured;
  benchmark a pilot). Allow **3–6 more hours engineering and 2–5 GPU hours**
  for the first automatic proposal pass. Mac GPU is optional only after a
  measured resource/restore check, AC, exclusive access and enough space.
  Otherwise run sequentially on Lenovo. If the diagnostic gate fails, keep
  the result and stop before spending GPU time on a new detector.

### 3. Optuna: four-trial pilot, six only if capacity allows

- Add a separate STU-Net adapter; the historical `scripts/tune_optuna.py`
  is for another model and is not used. Freeze one corrected parent, the
  optimizer-start choice, input addresses, augmentation, supervision setting,
  seed, and common schedule prefix. Tune only peak LR (start with
  `5e-6…4e-5`, log scale) and CE-to-Dice weight (`0.5…2`, log scale).
  Include the unchanged baseline as a trial and hold the rest fixed.
- Run **one baseline plus three candidates**, serially, at **1,000 updates
  and one full 70-scan evaluation per trial**. Keep pruning off for this
  first pilot. Maximize positive macro Dice, rejecting candidates that worsen
  overall or small-case recall, lose a baseline case/component hit, increase
  false alarms or FP volume, or fail the pancreas/geometry checks. Record
  all trials, including failed/infeasible ones, in Optuna SQLite and MLflow.
  The five small-burden scans are a diagnostic group, not the sole objective.
- **Estimate:** **3–5 hours adapter/CPU checks** during the occupied GPU
  window, **13–16 GPU hours for four trials** or **20–24 for six**. Keep at
  most two feasible finalists for a longer matched replay; allow **5–6 GPU
  hours per fresh 2k replay**. Short trials can misrank longer runs, so no
  trial win is called a generalization result. Confirmation needs a cleared,
  patient-disjoint cohort unused for tuning and defensible pretraining
  provenance. A new split of the already exposed 70 is not that cohort.

### Calendar and capacity

| When (Mountain) | Mac and analysis | Single Lenovo GPU |
| --- | --- | --- |
| Tue Nov 10 / Wed Nov 11 | Freeze controls, review the small-case training inputs, start refiner crop/restore and Optuna adapter tests | Finish and verify the existing 26k→36k recovery. The latest peer estimate around 5:42 p.m. Tue was 22–23 hours remaining, implying Wed afternoon only if progress and storage hold. |
| Wed evening / Thu Nov 12 | Verify the 14k comparator; prepare the refiner diagnostic set; implement scoring and trial logging | Qualify and run the matched 2k supervision pilot, after recovery closeout and new launch approval. |
| Fri Nov 13 | Report the matched learning result and, if qualified, the refiner's known-location result. Preserve reviewer/demo preparation. | Run the compact refiner diagnostic block if it cannot run on the Mac; then start Optuna baseline and first candidates. |
| Sat Nov 14 / Sun Nov 15 | Preserve the tentative stakeholder walkthrough. Compare full results and write next-week decisions. | Finish the four-trial Optuna pilot; run predicted proposals only after the refiner gate passes. Use extra time for trials five/six or finalist replay only if the first evidence warrants it. |

The Lenovo measured about **6.2 seconds/update** recently and **92.5 minutes**
per full native 70-case pass on the earlier 12k run. Budget **21–30 GPU hours
after recovery** for the 2k ablation, known-location refiner and four Optuna
trials, if the historical control is reusable; add roughly **5–6 hours** for
a fresh control and **2–5** for the automatic refiner pass. Recheck storage
and retained independent backups before every new run; the recovery's limits
do not authorize a new experiment. If capacity slips, protect the matched
ablation and known-location diagnostic, then finish four Optuna trials before
extra arms. No training, GPU scheduling, cohort access or policy deployment
is authorized by this plan.

Report both positive-case Dice and lesion-level overlap, small-bin counts,
component hits, per-case recall changes, empty-scan alarms, physical FP
volume, and failure denominators. These are exposed development comparisons
unless an independent cohort is separately admitted. References:
[supervision evidence](../operations/STUNET-INPUT-AND-SPATIAL-FINDINGS-20261108.md),
[measured runtime breakdown](../coordination/LENOVO-STUNET-LONGER-SCHEDULE-REVIEW-20261108.md),
[standing evaluation policy](../evaluation/SEGMENTATION-POSTPROCESSING-POLICY-V1.md),
[pancreatic tumor cascade study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11335681/),
and [Optuna constrained optimization](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/002_multi_objective.html).

## Current Trello board

At Quinton's explicit November9 request, the board is now rolled to Week6:
**12 To Do, 2 In Progress, 1 Done**; Week5 retains only its **7-card Done list**.
See the [rollover map and verification](WEEK-06-TRELLO-ROLLOVER-20261109.md).
Ten incomplete cards retain their IDs/history as W06-03 through W06-12; this is
carryover, not acceptance. Existing W06-01/02 proposal cards are in this week's
To Do. W06-13 covers per-model raw/5mm qualification, W06-14 weekly evidence and
W06-15 today's completed reporting/demo preparation. Revised planning dates do
not alter any training budget, gate or launch authority. The older dated entries
below retain the observation time and original card names used in those reports.

## November 9 check-in and current evidence

- [Degree-chair talking points](DEGREE-CHAIR-CHECKIN-20261109.md) prepared for a
  conversational ten-minute check-in, with evidence and remaining gaps.
  Meeting time/date, feedback, personal hours and course submission are not inferred.
- [Training-page reconciliation](../operations/TRAINING-ACCOUNTING-REFRESH-20261109.md):
  646.1 recorded training-session hours including 177.0 historical estimates;
  91.0 teacher-target hours separately. Lenovo snapshot at 12:24 p.m. MST records
  global 22,571; raw 14k/16k/18k/20k/22k Dice .3535/.3965/.4305/.4086/.4122. Best 18k,
  final 24k pending. No filter applied; supplied-region development scope unchanged.
- [Demo checks](../testing/CHAIR-DEMO-READINESS-20261109.md) verified a live cited
  answer, actual retained CT rendering and predicted-mask volume. Fixed the
  cold-start model/service reservation order and stale retained-export endpoint.
  Test decisions were not written. Temporary services were cleaned up afterward.
- [Autonomous-baseline next work](../operations/AUTONOMOUS-BASELINE-NEXT-WORK-20261109.md)
  separates source-unit evidence, resource failure 5592, numerical qualification
  and actual production-stage integration. G3/G4 remain open; no invented fix or
  failure exclusion.
- Continue the existing Lenovo run/monitor. Next Mac work remains the source-grounded
  retrieval/answer evaluation contract and an admitted production adapter, while
  preserving the November 14 participant plan. No successor GPU job is queued.

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
- Trello W06-01 and W06-02 retain their existing deadlines/dependencies and remain
  incomplete. The November9 rollover above supersedes the November7 preparation
  instruction to leave the board in Week5. Former W05-04 is now W06-12 and still
  needs Quinton's hours/submission confirmation. Former W05-08 is W06-07 and retains
  KD spatial follow-up, although compute and quantitative review are complete.
