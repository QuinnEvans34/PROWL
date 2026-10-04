# Next diagnostic — restore pancreas/lesion class separation

**Proposal only. No new training or analysis request is frozen or launched.** CAP-EXP-013's exact48-update request is consumed. Keep its terminal48 result as primary; do not extend it, change its thresholds, select an intermediate checkpoint using validation, or remove difficult cases.

The useful next question is why the model loses the pancreas class so early while predicting large regions as lesion. More duration could help, but this run alone does not establish that. First quantify the objective's class competition, then select one controlled rebalance for a fresh same-cohort comparison.

## What is already established

- All six training members received eight exposures. Cached target counts contain both pancreas and lesion labels; seven original target pairs matched frozen hashes, geometry and counts. Validation never optimized.
- Native terminal training lesion macro Dice0.030886/recall0.994807 and validation0.025448/0.974468 exceed the before baseline. Lesion predictions are35–835 times the reference volume; all seven native pancreas-class counts are zero.
- Saved tensor histories already have pancreas Dice/recall0 at step6. Training pancreas-class predicted counts are381 at6,1 at24 and0 at48, with no pancreas TP at those boundaries; validation has20,0,0, also no TP. This is not solely a native export artifact.
- Saved case3 probabilities retain a finite pancreas channel: mean0.394 at0,0.279 at6,0.266 at24 and0.249 at48. It wins8 tensor voxels at6 and none at24/48. Terminal maximum pancreas margin against the other channels is−0.082887. This is argmax class suppression, not a literal zeroed/nonfinite channel. These probability statistics describe case3 only.
- Current CE weights are `[1,1,256]`, with a weighted voxel mean, plus the mean Dice loss over present foreground classes. From frozen target counts, pancreas occupies only1.11–1.99% of the weighted CE denominator in training; lesion occupies3.31–54.92%. These are denominator shares, not measured gradient contributions. The loss balance is a plausible cause, not a proved causal conclusion.
- Independent cold replay reproduces all seven terminal native predictions exactly. Source pins, initial weights, task/head, original references and inverse geometry remain fixed. These checks argue against a simple label/export substitution explanation; they do not certify the whole learning recipe.

## Phase A — bounded zero-update objective and gradient audit

Prepare a separately pinned read-only analysis consumer. Use the accepted cache with fresh role/purpose/ancestry checks and existing same-run checkpoints; do not read original CT/targets. Reuse current numerical producers unchanged where possible. Any new objective is a separately versioned candidate, not a mutation of the accepted v3 loss.

First test classwise CE, weighted denominator and present-foreground Dice calculations against small invented exact oracles. Include tiny positive, boundary, overlapping lesion precedence and invented-negative cases. Preserve absent-class behavior and all target counts. Check analytical gradients against autograd and reject nonfinite terms; no optimizer step.

Freeze a small real analysis scope: six training members at steps0,6,24,48, at most24 forward/backward evaluations for the current objective, zero optimizer calls and no model/optimizer mutation. Validation is excluded from recipe choice. Bound actual MPS/CPU memory, time, derived read bytes and record output after a synthetic maximum-shape rehearsal. A separate exact analysis request is required before these extra model evaluations; none occurred in D-328.

For each case/boundary, report each class's weighted CE contribution, normalization, CE and Dice scalar terms, output-logit gradients by true class, and final-head gradient magnitudes/directions from each term. Record probability competition conditional on true pancreas/lesion/background, including class1-versus-class2 confusion. Do not assume target denominator shares equal parameter-gradient shares. Preserve full class counts and tiny2973/boundary6238.

## Phase B — choose one loss-balance candidate

Use training-only audit evidence and invented qualification to select one candidate that gives pancreas an explicit useful learning signal while preserving tiny-lesion learning. Possible candidates include lower lesion weighting, stronger pancreas weighting, or a class-normalized CE reduction. These are alternatives to examine, not approved settings. D-322's synthetic results explain why256 was originally selected; they do not prove it is suitable for real CT or permit silently reverting to an older loss.

Compare objective values and gradient behavior under a predeclared small candidate set. Record the exact reduction, class weights, Dice handling and selection reason. If a candidate changes the reduction, version and test it separately. Do not tune duration, learning rate, geometry, jitter, cohort or threshold in the same comparison.

The candidate must pass meaningful invented class-separation/tiny-lesion checks and actual144³ MPS resource/checkpoint recovery qualification. Synthetic qualification is necessary for mechanics; it cannot establish real learning quality.

## Phase C — fresh controlled real comparison

Only after qualification, prepare a new exact fresh-scratch run on the same6/1 cohort, seed42,144³,provided-pancreas ROI, zero jitter, AdamW0.0003,48updates and0/6/24/48 cadence. Change only the chosen loss-balance factor. Native evaluation requires a fresh14-target scope; CAP-EXP-013's consumed scope cannot be reused. Account for existing storage occupancy and new keeper/restore/retry space without resetting older ceilings. Freeze a new request and obtain its separate launch approval.

Keep terminal48 primary. Compare both pancreas and lesion native Dice/recall, lesion FP volume/precision, all cases/components and union metrics against D-325 and CAP-EXP-013. The pancreas class must recover meaningful overlap; high lesion recall alone is insufficient. Predeclare numeric comparison screens before launch, including retention of tiny2973 and boundary6238. Report the single validation case separately without using it to choose the candidate.

If class separation improves, discuss longer duration and broader qualified training/validation cohorts next. If it does not, use the measured gradients/confusions to decide the next named factor. No automatic extension, eligibility filtering, model promotion, specificity/generalization claim, autonomous cascade or formal model registration follows from this proposal.
