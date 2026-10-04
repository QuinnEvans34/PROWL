**October1 update:** Quinton approved this sequence underD-313. See [012launch plan](CAP-EXP-012-LAUNCH-PLAN-2026-10-01.md). Original recommendation below preserved.

# Proposed next comparison — midpoint class-mean balance

**Recommendation for Quinton's next decision;not authorized,implemented or request-frozen.**
[011 stopped result](CAP-EXP-011-RESULTS-2026-10-01.md) shows strong shrinkage and17/40ROI screens,
but mean recall0.948096fails coverage. D-312 is complete;neither consumed request may be resumed.

Test one midpoint between the original50/50and011's25/75class-mean weights:

```text
Mixed classes: CE = 0.375 * mean(foreground CE) + 0.625 * mean(background CE)
Sole class:    CE = full-strength sole-class mean CE
Loss:         CE + unchanged foreground Dice; omit Dice for empty references
```

This retains75%of original foreground CE pressure and increases background pressure25%;011
retained50%and increased background50%. It is a bracketed,interpretable choice rather than an
extensive weight sweep or fitted optimum. It does not have to make every frozen uniform-logit
shift favor shrinking;preserving scarce target pixels is part of the objective. Native parameter
optimization and coverage must decide whether it works.

Start again from exact independent-backup007step300 **model/AdamW state**,not011step150 or010step300.
Keep0.00001/300new updates/sampler300–599/113train/40development-validation/144³/2mm/seed42/batch1/
architecture/padding/inference/argmax/metrics/10mm margin fixed. Compare010at150/300and011at150;
011has no300comparison. Use a new explicit loss/adapter/state/run version and machine-readable
changed-factor record. No simultaneous LR,sampling,support masking,crop or cohort change.

Retain0/150/300evaluation and **all existing stops**,including mean recall>=0.95/minimum>=0.65,
>=38/40boxes retaining>=0.995and no mean drop>.03frombest previous active boundary including0.
Do not relax the0.95floor because011missed it narrowly;its drop guard failed independently.
Retain the prospective parent-relative utility bar median volume<=13.872506x/ROI>=10/40/
mean recall>=0.962700/all40boxes>=0.995. Report paired native records and regressions rather than
comparing loss scalars. Mandatory views include6186/3115/6534/2727and,if completed,6110/7604/7684.
Preserve all153members/23holds and expose stopped/unread prefixes accurately.

After a new decision,require arithmetic/finite-gradient/sparse/empty-learning checks,old-codec
refusal and native invented checkpoint/interruption/independent recovery. Then fresh40-reference
zero-update parent qualification with all40native masks exact,900s/16GiB/1GiB. Only successful,
source-matched qualification allows a fresh233-label/noCT/300-update request,45min including
recovery/16GiB/4GiB/AC/exclusiveMPS/100GiB free. Recompute exact bytes/storage/mount receipts;
old read scopes are consumed. Bind the new approved design to final immutable requests before
one launch. No new approval is implied by this proposal.

This remains exploratory development on repeatedly used40-case validation;one retained control
and a single treatment do not establish generalization or formalG5. Untouched holdout remains
untouched. No automatic continuation,model promotion,Git publication or Claude dispatch.
