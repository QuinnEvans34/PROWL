# Varied lesion-focused views without losing coverage

Approved October 22, 2026: prepare now; launch **one** qualified successor only after
the current pancreas-assisted run completes normally, including its final native
validation, backups, tracking finalization and worker shutdown. No interruption,
retry, resume, new exclusions, duplicate audit, protected-test evaluation or future
successor is authorized. This supersedes the older notebook's no-successor statement
for this single run. The accompanying JSON fixes the scientific decisions.

## Why this experiment

The current physical-region run preserves complete annotation coverage but repeats
few focused origins. Through 22,000 updates, 1,561/11,059 positive-case updates
(14.1%) contained no lesion voxels; median distinct focused origins was two.
Existing flips/rotations still vary these crops. Negative context is useful; these
observations do not prove that sampling caused lower Dice.

The intervention is **focused training-window selection only**. Preserve the same
1,333 PanTS training cases (671 positive), 70 development cases (36 positive),
original patient permutation and global three-focused/one-context schedule.
Keep fresh original SuPreM initialization, SegResNet/fresh 3-class head, seed42,
DiceFocal, AdamW1e-4/weight decay1e-5, 500 warmup/24k cosine, augmentation, 144-cubed
physical windows, spacing, pancreas-only region margins and native reconstruction.
No EMA, PANORAMA, lower LR, model-size change or altered inference crops.

For each patient, independently compute its total focused visits N in the unchanged
24k schedule and required union-annotation coverage-bank length B. Reserve visit
floor(j*N/B), j=0..B-1, for each original bank window, covering every annotated
pancreas and lesion voxel over the schedule. Reject N<B; never silently drop a case.
In remaining focused visits, cycle reproducibly through 26-connected lesion
components (pancreas components for empty cases). Randomize crop origins while
retaining the whole chosen component if it fits in 144 cubed; otherwise retain an
actual labeled anchor voxel. Large components remain fully exposed by the reserved
bank. Context windows use the **unchanged parent RNG/origins**. Stateful focus counts
are checkpointed; jitter is stateless keyed by seed, patient and visit/update.

This does not mean each patch sees the entire pancreas, or that component visibility
equals full-field coverage. We retain the existing complete-field proof separately.
Training annotations may guide training crops; development lesion masks never
choose, enlarge or repair inference regions. Provided pancreas assistance remains
explicit in every evaluation claim.

## Hypotheses and decision rules

Primary control: **the completed current pancreas-assisted run**, not an interim
20k result and not the different older .45 cohort. For both runs choose maximum
positive-case macro native Dice over twelve complete70 evaluations at 2k intervals;
earliest tie. Freeze parent selected/terminal reports and hashes before successor
optimization. Do not change the control after observing successor results.

- H0: selected native macro Dice improvement is <=0; H1: improvement is >0.
- Reject H0 only if the paired two-sided95% bootstrap lower bound is >0
  (10,000 positive-patient resamples, seed20261022). Otherwise **fail to reject** H0.
- Adopt the intervention only for gain >=.02, lower bound >0, detection fraction
  delta >=-.03, empty-any-alarm fraction delta <=+.03, all-case pancreas Dice
  delta >=-.02, no increase in total empty predicted lesion voxels, and positive
  macro lesion voxel recall delta >=-.03. Recall guard is newly preregistered here.
- Practical rejection: a guard fails or Dice interval upper bound <.02. Otherwise
  inconclusive if adoption criteria are unmet. Statistical and practical verdicts
  are reported separately. Do not equate failure to reject with proof of no effect.
- Mandatory secondary: terminal24k vs parent terminal24k, same rules; no replacing
  primary with a favorable secondary. Report the matched70 historical native record
  .4237607557 and project target .50 separately.

Repeated development reuse, checkpoint selection and one seed make this exploratory.
The paired interval is conditional on selected checkpoints, not a correction for
selection or a clinical generalization claim. Any-overlap detection is permissive;
also report component recall, size-stratified Dice/recall and empty false-positive
volume in mL descriptively. No protected test reads.

## Setup and handoff gates, in order

1. Add separate versioned sampler/session/launcher and focused tests. Never edit
   current receipt-pinned producers. Recompute all24k visits from metadata and prove
   every training patient retains its complete unchanged bank. Reuse the verified
   1,403-case intake and source identity evidence, not another duplicate/CT audit.
2. After parent normal completion, verify final70/selected/terminal journals,
   independent checkpoint backups, frozen pins, MLflow final status and reaped
   workers. Bind the parent comparison, not an interim checkpoint.
3. Run a bounded changed-path 12-training-case pilot (including clipped-history,
   tiny/multiple/large lesions, largest banks and empty cases). Verify actual sampled
   targets, anchor retention, exact repeatability, varied origins when geometrically
   possible and unchanged context origins; inspect private CT/target overlays. No
   automatic pass, difficult-case deletion or fallback if a gate fails.
4. With exclusive GPU lock, five nonpromotable producer updates plus one cold replay
   on a train-only qualification subset; exercise reserved, jitter and context
   paths, finite gradients, independent C: backup, exact next input and numerically
   close next weights, two native development cases, clean worker shutdown. These
   engineering updates are not scientific training hours or model Dice.
5. Freeze producing code/config/evidence hashes. Dispatch once only if all gates
   pass. Live MLflow uses the human experiment title; journals remain authoritative.
   Update the existing private dashboard at dispatch, retain the previous run card
   and include only actual scientific journal time in the total counter.

Keep existing96h wallcap including validation,12GiB owned RSS,100GiB C:/E: free
floors,32GiB cache cap,27,917,287,424B backup cap, AC/sleep inhibition and Windows
worker-job cleanup. No production output or MLflow RUNNING record during preparation.
GPU qualification waits for the parent; source/preparation failures stop the handoff
and require review rather than automatic retries. Keep the app open and drives/AC
connected for the scheduled follow-up. Setup status is not launch readiness.

### Exact continuation entry points

Use `.venv-prowl-windows/Scripts/python.exe scripts/train_varied_region.py` with
one of `--prepare`, `--bind-parent`, `--pilot`, `--qualify`, `--freeze`, or
`--launch-sha256 <ready.json hash>`, in that order. Preparation is a one-time step
performed while the parent runs; never replay a completed stage or remove a failed
stage's evidence to make a retry possible. Read existing stage logs/resources first.
Setup lives at `E:/PROWL/readiness/varied-focus-20261022-a01/`; scientific outputs
will be `E:/PROWL/artifacts/pants_varied_focus_24k_20261022/` with independent copies
at `C:/Users/quinn/PROWL-Backups/pants_varied_focus_24k_20261022/`.

After `--prepare`, save the passing focused regression JUnit XML as `tests.xml`
inside that setup. After the pilot worker exits successfully, inspect all twelve
`pilot/case-*.png` files and save a factual `visual-review.json` with
`accepted: true`, `reviewed_cases: 12`, explicit findings, and image hashes only if
actually reviewed and acceptable. Do not fabricate a review to unblock dispatch.
If any step already started but failed, stop and report; no automatic retry.

The existing native-region executor, MLflow tracker and dashboard API format are
reused unchanged. At dispatch, preserve the old pending card as a historical run
and make this run the new pending/live card in the local monitor registry. Point
the monitor's active journal at the new scientific output, then verify live loss
points, actual step advancement and the hours counter. Do not expose CTs, case IDs,
checkpoints, credentials or a new network service. No fake initial Dice or hours.

## Research rationale, not a guaranteed gain

[Official R-Super training loader](https://github.com/MrGiovanni/R-Super/blob/main/rsuper_train/training/dataset/dim3/dataset_abdomenatlas_UFO.py)
uses randomized tumor-focused views alongside context. This motivates testing a
controlled sampling change, not copying its whole recipe or claiming causality.
[MedFormerPanTS](https://huggingface.co/AbdomenAtlas/MedFormerPanTS) is a separate
teacher/multiorgan candidate; architecture, supervision and training recipe differ.
Its benchmark scores are not directly comparable to our reused70 development set.
Teacher/distillation, lower LR and other experiments remain separate future work.
