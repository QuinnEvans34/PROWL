# Saved-prediction follow-up screen — November 8

The user authorizes further tests now while the corrected Lenovo continuation
runs. This is a new exploratory development-set study, informed by the earlier
confidence and component results. It is not independent confirmation or a
retrospective extension of their prospective claims. Freeze this finite grid
before additional native mask/reference reads; publish every result.

Use the same original trained12k checkpoint's existing70 native replay codes,
36positive/34empty references and45 lesion components. Never run the model or
read CT, new training cases, protected test data or external cohorts. Hash-bind
the prior result/request, component records, each mask and both reference masks.
Use references only for scoring. Predicted pancreas and full native affine are
the only anatomical inputs to filtering.

Nine fixed policies:

1. Original raw argmax.
2. Whole raw-lesion components within5mm of raw predicted pancreas.
3. The previously studied10mm rule, retained as the incumbent.
4. The corresponding20mm rule as a looser sensitivity check.
5–7. The10mm rule followed by the three already-retained confidence policies
   .40/.50/.60. Suppressed retained lesion winners use their original nonlesion
   fallback; raw components outside10mm become background. All distances use
   raw predicted pancreas, so confidence cannot silently change the anatomy gate.
8. The10mm rule plus filling fully enclosed background-only holes≤100mm³.
   Any hole containing predicted pancreas is left unchanged. Lesion foreground
   uses26-connectivity, exterior/hole background uses6-connectivity.
9. The10mm rule plus additive physical1mm closing: retain every incumbent
   lesion voxel and add closing voxels only at predicted background, never
   overwrite predicted pancreas. The structuring element uses the full affine,
   not a voxel-radius approximation. No component-size deletion.

The last two probe limited missed-tissue recovery without shrinking known
predictions. They can still create false positives; no improvement is assumed.
They cannot recover disconnected lesions absent from the original predictions.

Report positive-case macro Dice/recall/precision, small5 recall, pancreas Dice,
case and identity-aware component hits, empty alarms, FP volume and FN counts.
Show differences against raw and incumbent10mm. Reuse the original +.02 Dice
versus raw, no lost detected case/component, no small-recall decline, overall
recall/pancreasDice each within−.01, nonincreasing empty alarms/FP volume guards.
Also flag any additional detection/recall/FP harm relative to incumbent10mm.
The maximum observed Dice is a development-screen leader, not a deployed policy
or statistically confirmed winner. No patient-independent or clinical claim.

One CPU worker/thread,≤1800s and≤8GiB owned RSS (below existing12GiB process
ceiling), AC,50GB decimal internal/100GiB external reserves and26GiB total
backup cap. No GPU context, optimizer, MLflow training run, active-source edits,
new schedule or automatic retry. Preserve every attempt; back up/reopen reports
and mask hash proofs independently. Do not retain more full masks: existing
replays plus frozen deterministic rules and output SHA256s are sufficient.
Stop rather than expand budgets or silently omit a case/policy on failure.

The separate coarsest-supervision loss candidate remains CPU engineering only.
Actual CUDA training qualification and a scientific comparison must wait for
the active Lenovo experiment to release its GPU; this screen does not change
that run, its launch receipt, recipe or checkpoint selection.
