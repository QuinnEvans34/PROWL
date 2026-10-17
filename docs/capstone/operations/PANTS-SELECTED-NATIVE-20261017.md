# Selected PanTS checkpoint evaluation and crop-variation planning

User authorized October17: native-score ordinary28k and EMA8k, then use results to plan crop variation.
This is evaluation only, not approval to train a successor or merge incoming code.

## Fixed evaluation contract

- Ordinary weights from `best-raw.pt`, step28,000; EMA weights from `best-ema.pt`, step8,000.
- These are the independently selected maximum tensor-Dice checkpoints within each variant.
  They differ in training duration; their comparison cannot isolate the causal effect of EMA.
- Same frozen70 development cases (36positive/34reference-empty), existing native scorer,
  three-class argmax, no postprocessing/TTA, provided-reference-pancreas ROI.
- Restore the combined checkpoint against the expected configuration/cohort/initialization identity.
  For EMA, explicitly install its averaged weights during inference, not its underlying raw weights.
- Reuse qualified tensors and source label hashes; no full CT preparation, duplicate audit or test reads.
- Separate MLflow diagnostic records linked to parent `38cdd18be83449da87275f5ef8b12898`.
- Private request and reports: `E:/PROWL/readiness/pants-selected-native-20261017-a01/`.
  New evaluator `scripts/diagnostics/evaluate_selected_ema.py` pins itself and original launch evidence.
  Eighteen existing EMA/decision tests pass; existing raw/EMA CUDA evaluation qualification is reused.
- Sequential supervised workers, onehour/model,12GiB RSS,100GiB freeC/E,256MiB output ceiling,
  AC check/CUDA lock, no retry. No prediction volumes exported or source/checkpoint writes.

The frozen72k duration and terminalEMA practical hypotheses remain rejected, with both nulls not
rejected. These selected-checkpoint diagnostics cannot revise those verdicts.

## Crop-variation planning implications

The Mac handoff already fetched at origin/main a833ccb is the starting design, not an executable
configuration or authority to launch. No merge is necessary just to read its specification.

### Question and controlled intervention

Does learning from imperfectly centered, expanded pancreas crops improve lesion outlining under
a frozen CT-only localizer/crop policy, without worsening detection or empty-reference alarms?

Keep PanTS training membership, source initialization, model, loss, optimizer, case sampler and
tensor shape fixed. Proposed horizon24k with its original24k cosine schedule. Change only training
crop distribution:50% original view,50% one deterministic expanded/off-center view per case.
Use the handoff's proposed1–2× extent scale with base-box containment and stable per-case seed.
No lesion-directed box selection or silent redraw when targets disappear. The view must be built
from original CT/labels, never by padding the existing144³ tensor and claiming new surrounding anatomy.

### Control selection

The ordinary28k orEMA8k model may be a diagnostic reference, but neither is a matched24k control.
Do not initialize only the crop challenger from one of these trained models and compare it against
a fresh-initialization control. Use the existing original24k-horizon control only if its producing
recipe/cohort/evaluation are demonstrated compatible. Otherwise plan a matched new control and
challenger; make that extra compute explicit before launch. A paired fine-tuning alternative must
start both arms from the same checkpoint for equal updates and be labeled a different experiment.

### Evaluation and scope

Primary endpoint: fixed terminal native lesion Dice under the same frozen autonomous localizer,
crop policy and scoring cohort. Retain provided-ROI Dice as a separate diagnostic. Choose and freeze
numerical minimum gain/uncertainty/guardrails before launching; do not inherit a favorable score
from today's posthoc selection as the control threshold. Record misses, reference-empty alarms,
lesion components, failures and size subgroups alongside Dice. No official-test evaluation.

Mac autonomous diagnostics used68/75 cases and a different segmenter, whereas this evaluation
uses70/75. Seven reported unknown-unit CTs and one anatomy/annotation concern need reconciliation
from existing evidence. Do not silently change cohorts, assert mm from an unknown unit, or compare
aggregate scores from unmatched sets. Reuse settled source-overlap decisions and exclusions.

The targeted setup work is code compatibility review, fixed localizer/endpoint binding, original
cache reuse plus a separate expanded-view cache, survival/storage checks for changed views, and
variant-sampler checkpoint recovery. No environment reinstall or broad duplicate re-audit.

## Results

Completed October17. Both70-case reports complete; both workers reaped; supervisor73080 exited0.
Ordinary worker576.390s/peakRSS2,569,146,368B; EMA598.578s/2,554,871,808B. No training updates.

| Native development measure | Ordinary28k | EMA8k |
|---|---:|---:|
|Positive-case lesion Dice|0.399545|0.406650|
|Positive cases detected|33/36|33/36|
|Reference components detected|37/45|38/45|
|Reference-empty cases with any lesion prediction|33/34|34/34|
|Reference-empty cases with >=50mm3 predicted lesion|30/34|34/34|
|Total predicted lesion volume on34 empty references|49.911mL|97.490mL|
|Pancreas Dice|0.811866|0.808478|
|Small-lesion Dice (n5)|0.126769|0.176852|
|Medium-lesion Dice (n24)|0.445249|0.427111|
|Large-lesion Dice (n7)|0.437686|0.500639|

MLflow ordinary `293346f5cd3c4e7fba06208cea291183`; EMA `cd079e24e08c431385f0d3eece182b29`.
Checkpoint SHA256 ordinary `3b26e5d13a64c849472ed53bdcade56f0e99a526bdd4a3222bcb2114cbcbf3d2`;
EMA `6e2a3eedc62049c4b591e30535cb3d65bf725ed928734f3fdebc054dc3153948`.

EMA's descriptive Dice gain is+.007105, with identical positive-case detection, one extra detected
component, one additional empty-case alarm, and1.953× empty predicted volume. The >=50mm3 counts
show that these alarms are not solely isolated single-voxel outputs. This is not a causal EMA test:
step8k versusstep28k and development selection differ. Neither selected model is promoted.

Both selected models outperform terminal72k nativeDice.2533 and detection24/36, but terminal
alarms15/34 are lower. The earlier original24k-horizon run's selected14k nativeDice.405092,
detection34/36 and alarms32/34 remain a contextual comparator on the same70 cases; today's
selected models do not show a clear overall advance over it. This does not revise any frozen
duration/EMA hypothesis. All metrics remain provided-ROI, reused-development diagnostics.

Size/physical-volume metrics retain the original affine-unit assumption; the Mac unit caveat
above remains unresolved for successor planning. Small-lesion subgroup evidence is onlyfive cases.

## Result-informed recommendation

Proceed to *specifying* crop variation, not automatically launching it. The segmenter demonstrably
can outline lesions better than the terminal72k model suggests, but high-Dice selected checkpoints
still overpredict heavily on empty references. Crop variation is motivated by the separate Mac
predicted-crop mismatch, not proof that it fixes those alarms or this run's late degradation.

For the cleanest first test, use ordinary weights with the original24k schedule and a compatible
fixed-crop control, changing only the training crop distribution. Keep EMA optional observational
only if defined identically in both arms; do not bundle changed averaging into the intervention.
Use fixed autonomous terminal evaluation as primary, provided-ROI performance as secondary,
and both alarm incidence and predicted volume as explicit reported safety tradeoffs. Existing
no-training/no-merge authorization boundary remains; user agreement on the concrete specification
precedes setup/launch. No additional training-fit diagnostic is required merely to repeat known work.
