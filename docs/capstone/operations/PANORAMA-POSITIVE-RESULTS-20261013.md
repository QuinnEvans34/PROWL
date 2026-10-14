# Add expert PANORAMA lesions: completed-run review

Date: 2026-10-13. Experiment: CAP-EXP-017. Training and native retrospective completed.

This dated review supplements, and does not rewrite, the frozen
[v2 design](PANORAMA-POSITIVE-EXPERIMENT-20261012.json) and
[exploratory admission amendment](PANORAMA-EXPLORATORY-ADMISSION-20261012.md).
The setup/pending fields in that frozen design describe its preparation-time state.

## Question and decision

At a fixed 24,000-update budget, does adding expert-positive PANORAMA training data improve
native PanTS development lesion outlining without material detection or false-alarm deterioration?

**Reject this intervention under the preregistered practical rule; do not promote the mixed
model over the PanTS-only selected model. Fail to reject H0, rather than accept H0.**

H0 was a nonpositive lesion-Dice difference; H1 was a positive difference. Practical acceptance
required a Dice gain of at least 0.02, a paired 95% interval lower bound above zero, and all
point-estimate guardrails passing. The observed gain is negative, and the false-alarm guardrail
fails. The Dice interval includes zero and meaningful gains: this is not proof that the true
effect is negative or that more lesion data cannot help.

## Execution and comparison integrity

- Completed all 24,000 optimizer updates and all 12 planned validation opportunities, without
  interruption. Training supervisor elapsed 67,764.062 seconds (18h49m24s); workers reaped.
- Run: `pants_plus_expert_panorama_dicefocal_24k_20261012`. Receipt SHA256:
  `604d19b280e90dcf1ca3c3409bfb13a6820592dd192308a410fad38653651233`.
- All frozen producing-file hashes still match. Initial, selected-best, retained 8k/final24k,
  and latest checkpoint hashes match the independent internal backups; final journal matches too.
- Train: 1,678 studies = 1,333 unchanged PanTS + 345 expert PANORAMA studies from 344 source
  subjects. Reference-positive/empty training composition: 1,016/662. No automatic lesion masks added.
- Both arms scored on the identical 70 PanTS development scans: 36 positive, 34 reference-empty.
  The five uncertain development scans remain excluded, never moved to training. Original splits,
  274 declared-import exclusions and technical holds are unchanged. No duplicate audit was repeated.
- Original SuPreM initialization plus fresh head, same 144-cubed architecture, DiceFocal loss,
  AdamW, seed42, 500-update warmup and 24k cosine schedule. No augmentation or postprocessing.
- Parent selected step14k remains selected after all 12 saved scores are recomputed on these70;
  mixed selected step8k. Selection uses positive tensor Dice; primary reporting uses native Dice.
- Native predictions use frozen three-class argmax and provided-pancreas ROI evaluation. No
  test cases, model fitting, checkpoint reselection or threshold fitting in this review.

## Primary: selected-best versus selected-best

| Native metric, identical70-case development set | PanTS-only,14k | PanTS+PANORAMA,8k | Difference |
|---|---:|---:|---:|
| Positive-case macro lesion Dice | 0.405092 | 0.371897 | -0.033195 |
| Positive scans with any lesion overlap | 34/36 (94.44%) | 33/36 (91.67%) | -2.78 percentage points |
| Reference-empty scans with any predicted lesion | 32/34 (94.12%) | 34/34 (100%) | +5.88 percentage points |
| Pancreas macro Dice, all70 | 0.810533 | 0.799845 | -0.010688 |
| Reference lesion components detected | 40/45 | 38/45 | -2 components |
| Reference-empty scans with >=50mm3 predicted lesion | 31/34 | 33/34 | +2 scans |
| Total predicted lesion volume on empty references | 129,020.50mm3 | 154,453.73mm3 | +25,433.23mm3 |

Paired patient bootstrap: 10,000 resamples, fixed seed20261012, percentile95% intervals.

| Difference | 95% interval | Preregistered point guardrail |
|---|---|---|
| Lesion Dice -0.033195 | [-0.102249, +0.028561] | Gain >=0.02 and lower bound >0: fails |
| Detection fraction -0.027778 | [-0.111111, +0.055556] | >=-0.03: passes narrowly |
| Empty-alarm fraction +0.058824 | [0, +0.147059] | <=+0.03: fails |
| Pancreas Dice -0.010688 | [-0.019871, -0.000721] | >=-0.02: passes |

These are exploratory case-resampling intervals, not seed-to-seed uncertainty or statistical
noninferiority. Checkpoint selection on reused development data is not accounted for. Reference-empty
means no lesion annotation, not independently verified healthy; the alarm metric is relative to
those annotations. Any-overlap detection is lenient and is not clinical diagnostic sensitivity.

## Mandatory final24k comparison

| Native metric, final24k versus final24k | PanTS-only | Mixed |
|---|---:|---:|
| Positive macro lesion Dice | 0.319538 | 0.331492 |
| Positive scans detected | 26/36 | 28/36 |
| Reference-empty scans with any prediction | 18/34 | 20/34 |
| Pancreas Dice | 0.827748 | 0.828443 |
| Reference lesion components detected | 28/45 | 30/45 |
| Empty-reference alerts >=50mm3 | 13/34 | 12/34 |
| Total empty-reference predicted lesion volume | 15,536.49mm3 | 11,611.51mm3 |

Final Dice is slightly higher with PANORAMA: delta+0.011954, paired95%CI[-0.049570,+0.071232].
The mean gain is below0.02 and its interval crosseszero. Two additional empty-reference alarms
again breach the+0.03 guardrail: the same decision rule also rejects this secondary comparison.
Detection delta+0.055556 (CI[-0.055556,+0.166667]); alarm delta+0.058824
(CI[-0.088235,+0.205882]); pancreas delta+0.000696 (CI[-0.004393,+0.006131]).
Lower empty predicted volume and fewer50mm3 alerts at the endpoint are interesting secondary
signals, but do not erase the any-alarm result or change the preregistered primary endpoint.
The two models therefore have different trajectories, not a universal ordering at every step.
The mixed selected checkpoint is still better at outlining than its own final checkpoint.

Both70-case native reports completed, with workers reaped, zero optimizer updates and zero test
reads. Evaluation times:488.766s selectedbest and441.390s final. Matched tensor final Dice is
0.316652 versus0.332806; it is distinct from the native scores above.

## What we learned, and what remains a hypothesis

1. **More positive data under this fixed recipe did not improve the selected model.** This is
   evidence about this combined intervention, not a universal statement about dataset size.
2. **Equal updates did not mean equal PanTS exposure.** Mixed training used 19,055 PanTS updates
   and 4,945 PANORAMA updates; baseline used24,000 PanTS updates. Each mixed member was seen14–15
   times rather than approximately18. Positive/empty updates were14,543/9,457 (60.60% positive),
   compared with an approximately50:50 baseline cohort. These differences were declared in the
   design; they are possible explanations, not newly discovered protocol violations or proven causes.
3. **Selection and training horizon matter.** Mixed tensor Dice peaked at8k (0.375233) and ended
   at0.332806; parent peaked at14k. Longer training is not monotonically better here. A falling
   development curve alone does not distinguish overfitting, schedule effects or source interference.
4. **False alarms remain the central weakness.** At its selected checkpoint, the mixed model
   predicts lesions on every reference-empty development scan. A high positive-case Dice alone
   would not solve the original problem, even if the primary Dice had improved.
5. **Several factors moved together.** PANORAMA adds PDAC-specific data, source/acquisition and
   annotation differences, a pancreas-plus-lesion union training crop, and positive prevalence.
   We cannot attribute the result solely to lesion count or model capacity.

No clean external generalization claim: development is reused and PanTS-only; residual undeclared
overlap and SuPreM pretraining membership remain uncertain under the approved exploratory exception.
Neither model is clinically validated. We have not measured PANORAMA generalization.

### Paired errors and ensemble implications

Of36 positive scans,14 improve,21 worsen and1 is tied in Dice. By reference lesion-volume band:

| Band | Cases | PanTS-only Dice | Mixed Dice |
|---|---:|---:|---:|
| Small, under1cm3 | 5 | 0.164142 | 0.065838 |
| Medium,1–10cm3 | 24 | 0.429395 | 0.410400 |
| Large, over10cm3 | 7 | 0.493877 | 0.458501 |

All three band means fall; the largest drop is in the very small subgroup (only5 cases), not
evidence of a reliable size-specific causal effect. Detection overlaps on32 positive scans;
parent alone detects2, mixed alone detects1, and both miss1. There is some complementary error,
but very little extra case detection and no new alarm-free empty scan from the mixed selected model.
A union of these binary detections would reach35/36 and still alarm on34/34 empty references;
an intersection would reach32/36 and alarm on32/34. These are arithmetic summaries, not fitted
ensembles or voxel-mask ensemble scores. Averaging probabilities could behave differently and
has not been tested. A useful ensemble would need a much more specific false-positive strategy.

## Proposed next experiment — not approved or launched

**Keep the added lesion diversity, restore positive/empty training balance.**

Question: with this same admitted mixed cohort and recipe, does a 50:50 positive/reference-empty
sampler reduce alarms without sacrificing lesion outlining or detection?

- Only intervention: replace uniform full-cohort permutation with a reproducible two-bucket
  sampling schedule, 12,000 positive and12,000 reference-empty updates. Within each bucket use
  deterministic shuffled cycles; retain all studies and log exact source/class/member exposure.
  PANORAMA remains approximately17% of all updates (345/1016 of the positive bucket), rather
  than20.6%. This is a sampling-policy test, not an isolated estimate of class prevalence.
- Reuse all admitted tensors, exclusions, source decisions and70-case evaluation membership.
  Same original SuPreM/fresh head, seed, architecture/loss/optimizer,24k horizon,12selection points,
  native evaluator and no postprocessing. Do not silently warm-start from either trained model.
- Proposed primary H0: balanced sampling does not reduce native reference-empty alarm fraction
  relative to the current mixed selected model; H1: it reduces it. Proposed practical bar:
  at least4 fewer alarm scans (>=4/34 reduction), paired95% upper bound for alarm delta below0,
  and no more than0.02 Dice loss,0.03 detection-fraction loss or0.02 pancreas-Dice loss.
- Keep positive tensor-Dice checkpoint selection unchanged, so sampling remains the experimental
  change. Report final24k versus final24k as mandatory secondary and also show the PanTS-only
  benchmark. A win over mixed alone is not a win over the better PanTS-only baseline.
  Guardrails are point estimates, not proof of noninferiority; even30/34 alarms remains unsuitable
  as a clinical operating point. This would be an incremental research win only.
- This proposal targets our false-positive problem explicitly; it is not a claim that imbalance
  caused the prior result. Freeze the exact hypothesis and decision rule with Quinton before launch.
- Setup work is narrow: sampler implementation/determinism+restore tests and a small changed-path
  smoke; implement/test the already-agreed live MLflow logging. No broad data requalification,
  duplicate search, new data download or cache reconstruction. Estimated training about19hours
  from the two completed runs, not a completion guarantee; existing resource/AC safeguards remain.

Later alternatives: exposure-matched source addition, augmentation, or a separately designed
detector/segmenter. Do not combine these changes in the next sampling test. An ensemble needs
measured complementary errors and a separately registered combination/validation plan; this run
does not establish an ensemble benefit.

## Evidence and tracking

Authoritative immutable evidence aliases:

- `artifacts/pants_plus_expert_panorama_dicefocal_24k_20261012/`: resolved recipe, input/source/cohort
  controls, final result, `execution/history.jsonl` and retained checkpoints.
- `readiness/panorama-positive-run-20261012-a01/`: frozen receipt, production qualification,
  parent70-case rescoring, pipeline terminal resources and journal.
- `readiness/panorama-positive-review-20261013-a01/`: post-run `audit.json`, sequential native
  evaluation reports/resources and `results.json` with paired comparisons and per-case changes.
- MLflow local SQLite store: both completed scientific histories imported, human-readable run
  names, 24,000 per-step loss/LR/elapsed metrics each, separate tensor/dev75 and tensor/dev70.
  Native reports are imported into separate native/dev75 and native/dev70 metrics. Timestamps explicitly mean import time;
  original steps and recorded elapsed seconds are preserved, not invented wall-clock timestamps.
  Raw images, labels, native prediction files and checkpoint payloads are not copied to MLflow.
- PanTS-only MLflow run `67d11609cc78406b86145f13e24ec61b`;
  PANORAMA-added run `c038332411df4f38bf52d650810c77c0`.
- Backfill/comparison focused tests:14passed. Repeat-safe import checks source journal identity,
  stored metric histories and exact readback; refuses conflicting/duplicate metric steps.
  Full native-inclusive reimport verified72,278 baseline and72,147 mixed metric points,
  addingzero newpoints to the same run IDs. Receipts and test XML are in the review evidence folder.

No next training run or AI monitoring schedule has been started. Live training-time MLflow logging
is still a before-next-run task, not a property of these backfilled runs.
