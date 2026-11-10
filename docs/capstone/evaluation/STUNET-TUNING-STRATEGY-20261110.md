# STU-Net 24k error analysis and tuning strategy — November 10

Quinton requests a deep review of the **terminal 24k checkpoint**, with the best
18k checkpoint as a separate comparator, following the professor's suggestion
to investigate hyperparameter optimization and the Dice/false-alarm tradeoff.
The already authorized 24k→36k continuation is a separate experiment and must
not be modified to mix these factors. A Dice of0.50 is a target, not a forecast.

## What the present evidence establishes

The peer completion records terminal Dice about0.4120 and selected18k0.430517.
The published preceding20k/22k values were0.408581/0.412172. These three late
measurements are approximately flat; they do not establish a permanent learning
ceiling, but neither do they show continuing improvement through24k. The longer
phase restarts a learning-rate schedule and uses new sampling/augmentation
addresses on the same patients. It tests that continuation recipe, not extra
steps in isolation or additional independent patients.

The original12k study found:

- Fixed0.40/0.50/0.60 **suppression of existing lesion argmax winners** did not
  improve positive-case Dice. This does not test every decision rule: it cannot
  add tissue that argmax missed, even if the lesion score is the close runner-up.
- The prediction-only5mm component policy gave0.371633→0.394938, with the
  measured case/component hits and recall preserved and FP volume down32.55%.
  These are exposed original12k development results, not measured24k results.
  Do not add this gain to0.4120 or0.4305 to predict the new result.
- Very small targets disappeared at the8³ auxiliary target in3/4deliberately
  selected positive training patches, while full-resolution labels survived.
  That head has only1/31of the loss weight. This supports a controlled ablation,
  not a conclusion that this explains the entire shortfall.
- A100mm³ component deletion rule lost a case and three reference-component
  hits. Avoid tuning only false positives or imposing aggressive size cutoffs
  without tracking the lesions they remove.

See the [original spatial results](../operations/STUNET-POSTPROCESS-RESULTS-20261108.md)
and [input replay findings](../operations/STUNET-INPUT-AND-SPATIAL-FINDINGS-20261108.md).

## First deliverable: terminal versus selected, with the full curve retained

Use full14k/16k/18k/20k/22k/24k native reports and frozen source identities. Bind
the selected and terminal checkpoint hashes, ready receipt and report backup
attestations. The Mac audit verifies saved metadata arithmetic; it does not
pretend to reread Lenovo's checkpoint or backup bytes.

`scripts/diagnostics/review_stunet_tuning_20261110.py` checks all70cases,36positive,
34reference-empty and45reference components, legal overlaps, native geometry,
stable references, summaries and report/checkpoint bindings before deriving:

- Macro lesion Dice on36positive cases; pooled/micro Dice separately.
- Per-case precision, recall, FP/FN voxel counts and physical FP/FN volume.
- Small/medium/large **total case lesion-volume** groups, complete misses,
  component overlap, worst cases and the18k→24k/22k→24k paired changes.
- Full-native voxel specificity and reference-empty case specificity separately.
- Raw checkpoint Pareto frontier: Dice/recall higher and FP volume/empty alarms
  lower. A different operating point may be useful without having the highest Dice.
- Reference-only error oracles: perfect FP removal, perfect FN recovery and a
  finite error-budget table. Required FP removal to reach0.50 assumes **zero TP
  loss** and a uniform fractional removal rate per case. It is a diagnostic
  requirement, not an attainable confidence threshold or deployment result.

No images, arrays, optimizer updates or MLflow writes occur in this audit. It
refuses incomplete or wrong-run exports and will not overwrite a previous report.

## Specificity must have a clear denominator

With27/34reference-empty scans showing any predicted lesion, the no-alarm fraction
is7/34=20.59%. At18k,29/34alarms gives5/34=14.71%. This strict case measure can
improve even when positive-case Dice declines. A tiny blob and a large false
alarm count equally here; report component count and FP volume as well.

Voxel specificity is TN/(TN+FP). Large background volumes can produce an excellent
voxel specificity despite alarms in most empty scans. Full-native background in
this provided-region evaluation further limits its interpretation. Do not use
it as the sole optimization objective or describe it as clinical specificity.
Reference-empty does not establish clinical absence of disease.

Positive-case **any-reference-overlap detection**, positive-case any predicted
lesion, and clinical detection are different quantities. Keep their labels
distinct. Improving only the34empty scans changes the headline positive36Dice
by exactly zero. Reducing false tissue on positive scans can improve that Dice.

## Test inference settings before another expensive training study

1. Qualify **raw and fixed5mm** separately on terminal24k and selected18k. Preserve
   the primary terminal result even if the selected comparator does better.
2. Inventory saved masks and full probability/logit fields. The original12k
   four-bit replay codes preserve only raw/.40/.50/.60 decisions. They cannot
   support arbitrary thresholds, calibration or a corrected24k study. Counts
   alone cannot determine the spatial effect of a filter.
3. If full fields are missing, measure and freeze one bounded inference/cache
   request. Prefer a single probability reconstruction per case followed by CPU
   policy evaluation, rather than running the network for every trial. Bind
   checkpoint, geometry, classes, source hashes, raw parity and independent
   replay/storage requirements before choosing a representation or executing.
   If MacMPS reconstruction differs from the originalCUDA counts, report the
   new same-Mac raw control and paired policies explicitly. Preserve the
   original publishedCUDA score; do not attribute a backend difference to tuning
   or silently relax a failed numerical admission gate.
4. A useful next decision parameter is a **lesion-vs-best-nonlesion logit bias**:
   positive values can recover low-margin lesion candidates; negative values
   suppress them. This differs from removal-only confidence filtering. Test
   it with the prediction-only spatial rule and modest component settings,
   preserving the raw predicted-pancreas context. A common positive temperature
   applied to all logits leaves argmax unchanged; temperature alone cannot
   improve an otherwise unchanged argmax segmentation.

Proposed finite search, **not an execution permit**: lesion bias
{-1,-0.5,0,0.5,1}, component proximity {5,10,20}mm, minimum component volume
{0,10,25}mm³:45combinations plus raw on terminal24k. Retain raw/fixed5mm on18k
as the predeclared comparator, rather than selecting a checkpoint separately
for every policy. The actual score-generation representation, tie handling,
pancreas-preservation rule, probability precision, memory/storage/time admission
and guard thresholds require a qualified request before array evaluation.

For only45cheap combinations, an exhaustive grid is clearer than claiming
Bayesian optimization is necessary. Optuna becomes more valuable for a larger
continuous space or expensive training trials. Use a small finite study first;
do not keep expanding it against this cohort until one score exceeds0.50.

## Where Optuna fits the training work

The existing `scripts/tune_optuna.py` is a **historical SegResNet/SuPreM whole-box**
search, with1.5mm/crop-native16, DiceFocal and a positive-only validation list.
It is not a current STU-Net launcher. Its focal-gamma parameter is not present
in the current STU-Net CE+foreground soft-Dice loss. Do not run it unchanged.
Optuna4.9.0 already exists in the Mac `.venv312`; no installation was needed.

Current source recipe: FP32 AdamW, weight_decay1e-5; original12k peakLR1e-4;
corrected12k phase peakLR2e-5 with500-update warmup and cosine decay to zero.
Loss is per-scale mean CE + foreground soft-Dice, with five-scale weights
[16,8,4,2,1]/31. Cohort664positive/669empty after the seven target corrections;
schedule preserves coverage and a3:1focused/context mix. Record actual exposure,
not just that nominal ratio.

Recommended bounded progression:

1. First test the already prepared coarsest-head ablation against its matched
   control: [16,8,4,2,0]/30 versus[16,8,4,2,1]/31. Hold all other factors fixed.
   This is not an adjustment to the live36k run. Original-parent replay is needed
   for a matched comparison; a24k warm-start test answers a different question.
2. Prepare a new STU-Net-specific Optuna adapter. A first small space should
   target peak learning rate5e-6…4e-5(log) and CE-versus-Dice weighting0.5…2(log),
   retaining weight decay, augmentation, sampling, patch geometry and the chosen
   supervision setting. Do not search five poorly supported factors at once.
3. Each trial must start from the exact same checkpoint/optimizer/RNG state,
   corrected input plan and sampling addresses. If using the terminal24k parent,
   label it **warm-start fine-tuning**, not fresh transfer or continuation of a
   shared optimizer across trials. Restoring AdamW state while changing its LR
   is different from resetting the optimizer; freeze that choice explicitly.
4. Proposed first study cap: at most12proxy trials,1,000new updates each, common
   full70native evaluation at the endpoint, with pruning initially off. Such
   short prefixes intentionally do not cover every patient/window and can
   misrank long-training behavior. Admit actual wall/storage budget from measured
   timings first; a trial-count limit alone is not a resource limit. Fully qualify
   and evaluate at most two finalists on a common longer horizon before a model
   decision. Qualification and reruns count against a cumulative cap.

For inference tradeoffs, retain Pareto results for Dice and FP burden, then apply
case/component, small-lesion recall, overall recall and pancreas safeguards.
Reject improvements that merely erase lesions. For training, a single-objective
Dice study can retain all other metrics and filter feasible finalists; report
infeasible outcomes instead of silently changing penalties. Optuna supports
multi-objective studies, but its normal `Trial.report/should_prune` does **not**
support multi-objective pruning. Do not combine those APIs as if it did.

Every trial should retain parameters, parent/input/code identities, failed/pruned
status, complete metrics and resource evidence in a dedicated Optuna SQLite study
and MLflow experiment. Use a fixed sampler seed and serial trials; that alone
does not guarantee deterministic GPU training. No unsafe pickle fallback, shared
live-source edits, budget reset, automatic retries or competing Lenovo GPU job.

## Interpretation and verification boundaries

All70development cases have already influenced model/policy selection. A new
split of them is not an untouched confirmation cohort. Patient grouping is
unresolved; case-level resampling is descriptive and may understate uncertainty.
Do not claim independent generalization, calibrated disease probability or a
leakage-free result. Keep protected tests and unapproved external image/mask
cohorts out of tuning. A later confirmation needs an eligible independent cohort
or a prospectively recorded evaluation boundary with defensible patient grouping.

Success for this work is a measured tradeoff and reproducible model decision,
including a clear negative result if0.50is not achieved. Inference tuning changes
output decisions; training tuning changes learned weights. Report them separately.

Primary references reviewed November10:

- [Optuna multi-objective tutorial](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/002_multi_objective.html).
- [Optuna trial reporting/pruning contract](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html).
- [Optuna reproducibility FAQ](https://optuna.readthedocs.io/en/stable/faq.html).
- [Reinke et al., metric-related pitfalls, Nature Methods2024](https://www.nature.com/articles/s41592-023-02150-0).
