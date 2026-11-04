# Reject false alarms without losing small lesions — parallel preparation

User approved preparation on Windows while Mac prepares distillation. This
supersedes only the original plan's requirement to wait for KD results. It does
not authorize GPU work during the active varied-focus run or a scientific launch.
Original frozen sources/specifications remain unchanged. This is NOT launch-ready.

## Critical dependency: honestly held-out generator predictions

The current and previous broad PanTS segmenters learned all 1,333 training
patients. Splitting these patients now into verifier fit/calibration partitions
does not erase the segmenter's exposure. The 70 development patients must not
be repurposed for verifier fitting or threshold tuning. Teacher predictions have
unknown exposure and are not an independent substitute.

Therefore a leakage-controlled verifier cannot simply start from these models'
training predictions after the current run. There is no demonstrated clean
candidate archive yet. Do not fabricate a no-exposure declaration.

Recommended lower-compute alternative to several full OOF segmenters: one fresh
candidate-producing segmenter on a prospective, stratified subset of the 1,333
training patients, with disjoint verifier-fit and calibration patients reserved
before that segmenter sees any labels. Generator checkpoint selection also stays
inside its permitted training partition. Freeze patient identities, positive/size
strata counts and sample-adequacy review before launch; no split generated here.
The generator must never see fit/calibration patients through optimization or
checkpoint/threshold selection. Verifier fitting must not see calibration labels.

This requires an additional segmenter training run, not merely cheap preprocessing.
Its partition size, horizon and resource budget need a user decision before
execution. Full out-of-fold generation is an alternative, but costs multiple
segmenter fits; calibration patients must remain excluded from every generator
whose predictions feed the fitted verifier. Do not silently authorize either.

## Proposed verifier intake (not yet frozen)

- Use 26-connected components of the frozen segmenter's existing hard native
  lesion prediction, preserving its multiclass decision rule. No GT-created
  candidates, minimum-size deletion or replacement of missed lesions with GT crops.
- Inputs: CT and predicted lesion probabilities on the same geometry; candidate
  support and valid-padding channels may be needed. GT supplies labels only.
- Candidate positivity: any overlap with an annotated lesion, conservatively
  preserving partially overlapping and tiny candidates. Log overlap fractions
  separately. One merged candidate may cover several GT components; report both
  candidate labels and GT-component recall, not a one-to-one matching claim.
- Patch extent must include complete predicted component plus physical context.
  Resolve multiview aggregation versus resizing only after metadata size review;
  never truncate a large candidate to force it into a fixed cube. Tiny candidates
  and cases with zero candidates stay in accounting.
- Proposed deployment rule is whole-component retention by verifier score. This
  is an explicit simplification from the earlier soft-probability suggestion,
  pending pilot review; it can remove false components but cannot trim the false
  boundary of a retained component. Threshold zero reproduces baseline exactly.
- No network architecture, training duration or operating threshold is frozen.
  Patient-balanced fitting and representative patient-level calibration are
  required; abundant easy negatives must not dominate the training objective.

## Ordered gates

1. Finish and review current native24k results; preserve its checkpoints and logs.
2. Approve leakage-safe generator strategy and budget, freeze identities/roles.
3. Qualify and train generator separately; generate role-safe native candidates
   with source/checkpoint/prediction/geometry hashes and complete-patient receipts.
4. Audit candidate sizes/labels on training-only partitions, choose input design,
   review bounded positive/false-positive/tiny/large/empty real-case pilot.
5. Implement verifier network/session, CPU tests, bounded GPU finite-gradient
   updates, independent checkpoint backup and cold restore; measure costs.
6. Freeze fitting/checkpoint selection using fit-internal roles. Use separate
   training-only calibration to choose the most selective threshold satisfying
   all sensitivity guards; baseline/no filtering remains a valid result if no
   useful threshold qualifies. Do not repeatedly optimize against development.
7. Explicitly approve one scientific verifier run; MLflow separate run/machine tag,
   frozen generator identity, losses/runtime/threshold and native paired metrics;
   update existing private dashboard only once real journal output exists.

Primary H0 and practical criteria remain those in the original verifier plan:
negative alarm improvement <=0; support requires paired95%CI lower>0 and >=.10
absolute improvement (at least four of34), no extra positive-patient miss, no loss
of <1mL GT-component recall, positive native Dice delta>=-.01 and no larger empty
voxel burden. Missing component evidence is not a pass. Report all denominators,
positive Dice and inference costs; no claim of clinical safety or independent
teacher generalization. This experiment targets alarms, not necessarily .50 Dice.

## Engineering completed in this preparation

Additive candidate_verifier_v1 provides conservative component extraction,
aligned training labels, score-accounting checks, baseline-identity gating and
provenance checks including indirect calibration exposure. Synthetic tests only;
receipt authenticity still needs validation against the actual generator history.
No CT/mask reads, candidate cache, GPU job, network model, launch receipt, MLflow
record or dashboard change was made. Existing coverage evidence will be reused.
