# PanTS-only longer schedule and EMA: completed review

Reviewed October16, 2026. Governing prospective rules: [frozen specification](PANTS-EMA-72K-20261013.md).
No endpoint, minimum improvement or guardrail was changed after seeing results.

## Completion and evidence

All72,000 updates are contiguous. Completed October15 at18:58:34 MDT, before the reported restart.
Training journal elapsed204494.015s (56h48m14s); supervisor204508.828s, workers reaped.
All386 launch-receipt file pins match. Nine retained checkpoint files and final journal match their
independent C: backups. All ten native evaluations (five milestones × two variants) contain exactly
the same70 development cases:36 lesion-positive,34 reference-empty. No new inference, CT reads,
duplicate audit, test evaluation or training was needed for this review.

Private audit output: `E:/PROWL/readiness/pants-ema-review-20261016-a01/results.json`.
Journal SHA256 `ac1bac3efc83665d355cb839ce2fc09f550dcf31e973e1a090f4895a3a4bac28`.
Reproducer: `scripts/diagnostics/review_pants_ema_72k.py`; five focused decision/pairing tests pass.
MLflow run: `38cdd18be83449da87275f5ef8b12898` (existing live-tracked run, not a new experiment).

## Native-resolution trajectory

Dice is macro-average over all36 positive cases, including zero-overlap cases. Detection means
any overlap on a positive case, not clinical sensitivity. Alarms mean any lesion prediction on
a reference-empty case, not verified clinical false positives.

| Updates | Ordinary Dice | EMA Dice | Ordinary detected /36 | EMA detected /36 | Ordinary alarms /34 | EMA alarms /34 |
|---|---:|---:|---:|---:|---:|---:|
|24,000|0.312373|0.311643|27|28|21|26|
|36,000|0.298621|0.323013|28|29|22|23|
|48,000|0.262819|0.269155|26|26|20|22|
|60,000|0.259812|0.268292|26|26|15|16|
|72,000|0.253297|0.253301|24|24|15|15|

### Longer-training hypothesis: practical benefit REJECTED; H0 NOT REJECTED

Primary ordinary72k minusordinary24k Dice=-0.0590763; paired95% bootstrap interval
[-0.1299551,+0.0050816]. The upper bound is below the predeclared +0.02 practical minimum.
Detection falls27/36→24/36 (-8.33percentage points), failing the allowed -3pp guardrail.
Empty alarms improve21/34→15/34 (-17.65pp), and pancreas Dice improves.817279→.826037
(+.008758), both passing their point guardrails. These improvements do not rescue the failed
primary rule. Eleven positive cases improve,16 worsen,9 tie in lesion Dice.

The interval includeszero: do not claim a statistically established negative Dice effect or
"accept H0 as proven." We reject adopting this longer schedule as the specified improvement,
and fail to reject H0 (gain<=0) under the prespecified interval criterion.

### EMA hypothesis: practical benefit REJECTED; H0 NOT REJECTED

Secondary EMA72k minusordinary72k Dice=+0.0000033621,95% interval[0,+0.0000100863].
This is far below the +0.01 practical minimum; the lower bound is not strictly positive.
Detection, alarms and component detection are identical. All point guardrails pass, but the
minimum-gain rule fails. Only one positive case has a nonzero Dice change.

This rejects the specified terminal EMA benefit, not every EMA setting or checkpoint-selection
strategy. At36k EMA beats concurrent ordinary native Dice by+.024392 descriptively, with one
additional detected positive and one additional empty alarm. That intermediate result is not
an alternate endpoint and does not override the fixed72k decision.

## What the pattern suggests, and what it does not prove

- Late predictions become more conservative: empty predicted volume totals17.803mL→4.128mL,
  but positive detection falls and reference-component detection declines29/45→26/45.
- Small-lesion Dice falls.1666→.0193 (only5 cases), medium.3256→.2983 (24), large.3711→.2663 (7).
  The decline is not confined to tiny lesions. Small-lesion detection falls2/5→1/5.
- Mean training loss over the final2,000 updates of each milestone decreases
  .4428→.4106→.3849→.3704→.3609 while native development lesion Dice deteriorates.
  This is consistent with overfitting or mismatch between the optimized loss and desired
  development behavior. Training loss is not training Dice; changing sampled batches and lack
  of matched checkpoint-specific training-fit measurements prevent a causal overfitting claim.
- EMA alpha.99 emphasizes roughly the latest100 updates, not an average of the entire run.
  A near-zero terminal cosine learning rate makes ordinary/EMA convergence unsurprising.
  It cannot preserve a much earlier good solution through tens of thousands of subsequent updates.
- Best tensor scores remain.396447 ordinary at28k and.406931 EMA at8k. These are not native
  evaluations of those selected checkpoints. Neither replaces the fixed native endpoints.
- The earlier24k-horizon baseline is contextual, not a matched-prefix control: this run stretches
  the learning-rate schedule. Do not generalize this finding to "more training never helps."

## Limitations and cross-laptop findings

Exploratory single-seed, repeatedly reused development cohort, provided-reference-pancreas ROI,
SuPreM pretraining membership unverified. Bootstrap uses paired PanTS case IDs as the frozen
patient unit; repeated-patient independence has not been separately established. Point guardrails
are not statistical noninferiority tests. No clean benchmark or autonomous clinical claim.

The already-fetched Mac crop-variation handoff at origin/main a833ccb reports a separate68-case
autonomous-development diagnostic: reference-crop Dice.422671 versus predicted all-support
crop.225818 (largest-component alternative.246612). All33 positive-case lesions were within
both predicted boxes, so mere inclusion did not remove the gap. These are different checkpoints,
cohort and inference policies from this run, not directly comparable scores or proven cause here.
The handoff also flags seven unresolved spatial-unit cases and an anatomy/annotation concern.
Reconcile those existing records before future autonomous mm-based crop experiments; do not
silently change this completed cohort or demand another broad duplicate audit. Volumetric and
size-band figures here retain the frozen evaluator's affine-unit convention and that caveat.

## Proposed next step — discussion, NOT launch authorization

Do not repeat72k with PANORAMA now: the conditional PanTS success gate was not met. Do not
adopt terminal EMA or extend this run again. Preserve earlier selected checkpoints for investigation.

Recommended next training direction: the existing **train for imperfect pancreas localization**
crop-variation proposal from the other laptop, adapted explicitly to current admission. This
addresses a measured deployment mismatch rather than repeating a duration or positive-data guess.
Hypothesis: varied, expanded/off-center training crops improve fixed-policy autonomous lesion
outlining without losing detection or increasing alarms. It is a new endpoint, not a continuation
of the present provided-ROI hypothesis.

Use PanTS only, original initializer, unchanged loss/model/case sampler, and a matched24k-horizon
control/challenger recipe. Change only training crop distribution: original versus one deterministic
expanded/off-center view per case at50:50. Expand from original CT/labels, not padded144-cube
tensors that have already discarded surrounding anatomy. Keep validation/inference fixed and
retain the old provided-ROI diagnostic separately. No lesion-directed crop selection. Reuse source
admission; qualify only changed crop/cache/sampler/recovery behavior. Freeze numerical success
criteria and resolve autonomous evaluator/cohort compatibility before launching.

Before committing to that training expense, a targeted option is native evaluation of already-saved
best ordinary28k and bestEMA8k, followed by matched training-fit at24k/72k if needed to distinguish
overfitting from continuing underfit. Neither diagnostic has been launched. If the immediate goal
is provided-ROI Dice rather than autonomous robustness, choose a controlled augmentation/regularization
experiment instead; the crop handoff does not yet establish a cause of this run's late decline.

Historical balanced-patch sampling was not successful; current mixed-source case sampling is a
different hypothesis, not globally disproved, but these results do not make it the strongest next move.
No code integration, model promotion, new training, schedules or push were performed in this review.
