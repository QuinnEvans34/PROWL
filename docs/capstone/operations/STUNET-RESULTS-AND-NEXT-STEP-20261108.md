# STU-Net completed-run review and longer-training decision

Date: November 8, 2026. Status: **analysis complete; correction-first continuation proposed, not launched or qualified**.

The 12k run finished normally. Its final checkpoint is also its selected checkpoint,
with lesion Dice **0.371633** on the 36 positive development cases. A longer run is
worth testing, but the original input policy must be corrected first. The completed
run, producing sources, original caches, receipts and all prior attempts remain intact.

## What the full curve says

All six validations completed the same 70 cases: 36 positive, 34 empty, 45 reference
lesion components. Dice is the positive-case macro mean; detection is any overlap,
not adequate lesion coverage or a clinical detection claim.

| Updates | Lesion Dice | Positive cases overlapped /36 | Empty cases with false positives /34 |
| --- | ---: | ---: | ---: |
| 2,000 | 0.144179 | 28 | 33 |
| 4,000 | 0.222087 | 26 | 29 |
| 6,000 | 0.347182 | 30 | 26 |
| 8,000 | 0.328011 | 35 | 33 |
| 10,000 | 0.346184 | 34 | 27 |
| 12,000 | **0.371633** | **35** | **27** |

The last interval gained 0.025449 Dice; 22 positive cases improved, 13 worsened and
one was unchanged. The best score occurs at the training limit, so a plateau is
not established. The curve fluctuates rather than rising at every validation.
Patch training loss decreases from 0.923582 in the first 2k block to 0.590295 in
the last. Early blocks change their coverage/jitter mix, and no validation loss
or train-set full-volume Dice was logged. These numbers cannot establish underfitting
or rule out overfitting.

At 12k, macro lesion recall is 0.541016 and defined macro precision is 0.370010.
Fifteen of 36 positive cases miss more than half the reference lesion; 13 predict
at least twice its volume. There are 84,240 missed lesion voxels and 284,862 false
positive voxels across the cohort. Forty-one of 45 reference components overlap a
prediction; cases 2235, 2935, 4681 and 6755 each retain one component miss.

The five cases with total reference lesion volume below 1 mL have mean Dice
0.077216. This is a **case-volume group**, not an individual-component analysis.
Case 4681 is a complete miss despite substantial false positives; case 7868 has
only 12 of 1,218 reference voxels overlapped. Three other small cases predict about
9–24 times the reference volume. Thus both missed coverage and overprediction need
attention. Confidence filtering could remove false positives but cannot add a
missing lesion. Spatial causes require the current model's contours/probabilities;
these saved counts do not establish a particular boundary or anatomical cause.

## A confirmed input-policy omission

STU-Net reused the original varied-target cache without the seven-case PanTS
annotation errata already applied to Mac KD. Its frozen metadata consequently
lists 671 positive and 662 empty training cases instead of the corrected 664/669.
All 1,333 cases remain eligible; this is a target correction, not case exclusion.

The PanTS collaborator reported that radiologist review confirmed the affected
patients as normal and the tiny masks as drawing-tablet annotation errors:
[PanTS issue 12, May 26 confirmation](https://github.com/MrGiovanni/PanTS/issues/12#issuecomment-4538401573).
The adopted local policy is `pants-issue12-local-normal-mask-1`; see
`MAC-KD-UPSTREAM-ERRATA-20261023.md` and `MAC-KD-ERRATA-CORRECTION-20261023.md`.

Lenovo verified frozen input/cache metadata and actual saved traces; Mac independently
matched the seven original lesion hashes/counts against its hash-verified corrected
overlay metadata. The seven cases received **62 updates**, **46** containing erroneous
lesion voxels. They have 177 original annotation voxels in total; none belongs to
the 70-case development cohort. The existing validation scores remain the scores
actually obtained by the original run. This confirms an integration omission,
**not the size or direction of its effect on Dice**. It cannot explain all errors
without a controlled experiment.

## Was only a new head trained?

No. The checkpoint transferred 58,157,984 body parameters and initialized 2,991
output parameters across five three-class deep-supervision heads. AdamW receives
`model.parameters()`; the backbone is not frozen. The saved source requires finite
gradients for all parameters. Measured body/head weight deltas and gradient norms
were not logged, so we do not claim a measured amount of backbone adaptation.

All 1,333 training cases received 7–16 sampled patch updates (median nine). All
2,978 planned coverage addresses executed; there were 6,022 component-jitter and
3,000 context updates. Only 5,189 of 12,000 patches actually contained lesion
voxels. These visits are not full-volume epochs. Coarse deep-supervision targets,
patch composition and the CE/Dice balance are plausible follow-up factors, but
per-scale/per-class losses were not saved and no one is a demonstrated cause.

## Recommended next experiment

Prepare **one additional 12k corrected-label fine-tuning phase**, starting from the
verified 12k checkpoint, preserving the learned body **and heads**. This is the
resource-efficient first choice over discarding the learned state. It would reach
24k total ancestry updates; it must be described as a new continuation experiment,
not a completed 24k run or a pure duration-only ablation.

Preparation must do the following before any launch decision:

1. Bind an additive corrected target/cache provider to the exact seven-case errata.
   Preserve CTs, pancreas masks, cohort and all other labels; rebuild affected
   component-focus metadata and prove 664/669 membership/positivity. Check every
   ordinary target remains unchanged. Reject stale original cache bindings.
2. Define a new learning-rate tail and a new deterministic 12k sampling plan. The
   original cosine reaches **zero at 12k**; its LR and sampler reject the next
   index. Merely increasing a loop bound cannot continue learning. Qualify one
   conservative LR restart without a head reset; freeze its numerical schedule,
   optimizer-moment policy and non-replayed augmentation addresses prospectively.
3. Implement an ancestry-aware checkpoint import with explicit allowed identity
   changes. Verify parent hash, full model/head state, retained optimizer/RNG/
   exposure state as specified, global update numbering, independent backup and
   cold restore. Preserve strict checks rather than relaxing the old restore gate.
4. Retain the original architecture, loss, inference settings and 70-case development
   cohort for this phase. Log per-class/per-scale loss diagnostics and body/head
   gradients without changing their optimization weighting. Evaluate all 70 every
   2k updates, select by the existing mean lesion Dice/earlier-tie rule, and retain
   selected plus terminal checkpoints and every validation.
5. Assess paired case changes in Dice, recall, precision, component misses, small
   case coverage and negative-case false positives against the unchanged parent.
   Preserve the parent as a fallback. A higher Dice with worse misses/alarms is
   a tradeoff to report, not automatic acceptance. Patient/pretraining exposure
   is still unresolved; no independent-test or leakage-free claim follows.

The target correction, LR restart and additional exposure are multiple explicit
interventions. To isolate label-correction benefit or duration alone would require
separate matched controls, not a causal conclusion from this phase. A fresh
corrected 24k run from the original pretrained body is a useful later alternative
if resources permit; it also changes the first 12k LR trajectory relative to this run.
Do not add a new loss, sampler ratio, architecture, model size or threshold selection
to the same phase. The separate proposed CAP-EXP-020 raw/fixed-confidence evaluation
remains available to measure false-positive filtering; it is not executed here.

Observed cost is 29.31 h for 12k plus six native validations. Another such phase
projects **29.3 h**, or **35.2 h with 20% headroom**, excluding correction/setup and
qualification. A fresh 24k with twelve validations projects **58.6 h**, or **70.3 h
with headroom**. These are estimates, not authorized budgets. About 9.25 h (31.6%)
of the original run was validation; update-path timing includes I/O/augmentation
and is not isolated GPU compute. Keep existing AC, storage, memory, GPU exclusivity
and backup gates; do not reuse the old 60h cap as successor authorization.

## Evidence and verification

- Peer source commits: completion `868ded3`, full-series/log export `410611d`,
  seven-case errata review `3ceda41`. Files imported byte-identically from Git;
  Windows CRLF source hashes are distinguished from LF Git-byte hashes.
- `STUNET-COMPLETE-ERROR-REVIEW-20261108.json`: locally recomputed overlap errors,
  six full-cohort checks, selection/terminal/backup inventory/log consistency.
- `STUNET-ERRATA-CROSSCHECK-20261108.json`: Mac overlay/source-hash and saved-trace
  crosscheck; peer detail in `../coordination/LENOVO-STUNET-ERRATA-REVIEW-20261108.json`.
- `review_stunet_complete_20261108.py` adds completion-binding checks while reusing
  the unchanged interim metric validator. **33 focused tests pass** across both
  reviewers, including incomplete closure, wrong selection/hash/backup/LR/timing
  and coverage failures. Saved JSON only: no new arrays, models, inference,
  optimizer updates or MLflow writes.
- Lenovo completion attests 237 pins, all 12,000 stored MLflow losses, FINISHED,
  all 34 independent backup pairs and reaped/absent workers. Mac verifies the
  published records' consistency, not the remote binary files or live GPU anew.
- No continuation, new GPU job, launch receipt or recurring monitor was created.
