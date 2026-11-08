# Standing rule: future segmentation postprocessing

**Owner authorization:** November8,2026, Quinton requested “implement this in
the future on all of our models,” log it durably and make it a standing rule.
This applies to future pancreas/lesion segmentation models, including scratch,
transfer and KD students. It does not apply to the literature assistant or
unrelated models.

## Required future default

Every future segmentation integration must plan and explicitly bind policy
`predicted-pancreas-proximity-5mm-v1`: retain a predicted lesion component only
if its minimum world-coordinate voxel-center distance to the same-scan
**predicted** pancreas is≤5mm. Use26-connectivity and the full native affine;
never replace millimetres with a voxel count. Removed components become
background; predicted pancreas is unchanged. No confidence or size deletion is
part of this standard. Keep immutable raw outputs alongside filtered outputs.

Use the shared entry point
`src.inference.standard_segmentation_postprocess_v1.postprocess(prediction, affine)`
and bind [the versioned configuration](../../../configs/inference/segmentation-postprocessing-v1.json)
in new evaluation/inference receipts. Canonical labels are0background,
1pancreas,2lesion; other class mappings need an explicit verified adapter.
For lesion-only models, use a separately qualified same-scan predicted-pancreas
output in the identical world grid. Never substitute an annotation or oracle.
If predicted pancreas is unavailable, keep raw predictions and record
`applied=false/predicted_pancreas_missing`; do not delete every lesion or
mislabel the output as filtered.

## Required evidence for each new model

- Report matched **raw and fixed5mm** results on the identical admitted cases,
  preserving separate mask hashes, checkpoint/config/source identities and
  policy version. Show Dice, recall, small-lesion/case metrics, case/component
  identities, empty-case alarms and FP burden. Bind the model's metric/cohort
  definitions; do not compare unrelated denominators.
- Qualify native geometry, class mapping, predicted-pancreas validity,
  reproducibility/backups and the model's existing detection/recall/utility
  guards before using the filtered output as its presented default. The standing
  requirement is to integrate and test this fixed rule for every model, not to
  conceal a model for which it harms detection. Record any failed guard or
  applicability exception and retain raw fallback for review.
- Keep raw checkpoint selection and filtered inference effects distinct unless
  a new prospective study explicitly freezes another selection rule. Attribute
  a postprocessing gain to postprocessing, not model learning or architecture.
- Do not tune the5mm radius independently for each new development result and
  still label it this version. Any different policy needs a new version and
  explicit exploratory-versus-confirmatory reporting.

This rule is prospective. Do not change the active corrected STU-Net run,
historical receipts/scores, frozen evaluator/selection, teacher probability
targets, training labels or losses. Additional scientific execution still needs
its own valid scope, resource admission and qualified receipt. The current
research evidence does not establish independent-patient or clinical safety.

## Evidence and durability

The [nine-policy screen](../operations/STUNET-POSTPROCESS-RESULTS-20261108.md)
measured original12k exposed-development Dice.371633→.394938, unchanged recall
.541016 and35/36case/41/45component hits, FPvolume−32.55%. This was only+.001051
beyond10mm and does not prove5mm is optimal for all future models. All630saved
output hashes replayed exactly; no new model training produced that gain.

This policy is linked from the root agent instructions, evaluation index and
two-machine coordination entry point. New experiment/model reviews must check
it before freezing evaluation and inference configuration. Both machines use
the same policy ID/configuration and publish raw/filtered evidence separately.
