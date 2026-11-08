# Saved-prediction follow-up results — November 8

The fixed nine-policy CPU screen completed all70 scans. The best observed
development Dice was **.394938** for retaining lesion components within5mm of
raw predicted pancreas, versus raw .371633 and the incumbent10mm .393887.
That is +.023305 over raw and only +.001051 beyond10mm. Recall and all existing
case/component hits were preserved on this exposed development set. No model
was retrained, no application default changed and no policy was deployed.

## Full grid, including unsuccessful candidates

| Policy | Positive36 Dice | Recall | Small5 recall | Case hits | Component hits | Empty alarms | FP volume mL | Raw utility guards |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Raw | .371633 | .541016 | .464489 | 35/36 | 41/45 | 27/34 | 382.515 | Control |
| Within5mm | **.394938** | .541016 | .464489 | 35/36 | 41/45 | 26/34 | 257.992 | Pass |
| Within10mm | .393887 | .541016 | .464489 | 35/36 | 41/45 | 26/34 | 259.280 | Pass |
| Within20mm | .393724 | .541016 | .464489 | 35/36 | 41/45 | 27/34 | 303.837 | Pass |
| 10mm + confidence.40 | .393590 | .539551 | .464160 | 35/36 | 41/45 | 26/34 | 257.332 | Fail small recall |
| 10mm + confidence.50 | .392355 | .527151 | .444756 | 35/36 | 41/45 | 26/34 | 242.289 | Fail small/overall recall |
| 10mm + confidence.60 | .389788 | .487631 | .401335 | 34/36 | 39/45 | 23/34 | 193.654 | Fail Dice/detection/recall |
| 10mm + enclosed holes≤100mm³ | .393887 | .541016 | .464489 | 35/36 | 41/45 | 26/34 | 259.280 | Pass; no effect |
| 10mm + additive physical1mm closing | .393766 | .541297 | .464489 | 35/36 | 41/45 | 26/34 | 260.158 | Pass vs raw; worse Dice than10mm |

All pancreas Dice guards passed. Small5 means cases with total annotated lesion
volume below1mL; it is not a component-size denominator. Empty34 are excluded
from headline Dice but included in the reported total FP volume. Case/component
detection means any reference overlap, not clinical adequacy.

The5mm policy removed60,751 FP voxels/124.522mL from raw (32.55% of FP volume),
with zero TP removal; FN stayed84,240 voxels. The tighter radius removed only
492 additional FP voxels/1.288mL beyond10mm. Similar Dice over5–20mm suggests
a broad useful anatomical rule here, not evidence that5mm is a universal optimum.
Do not continue narrowing radii against this same set to manufacture a larger
gain or claim this tuned-development result is independent confirmation.

The1mm closing recovered54 TP voxels but added721 FP voxels relative to10mm,
so Dice slightly declined. Small enclosed-hole filling produced no changes
under the frozen background-only/pancreas-preserving rule. Confidence cuts
continued to delete useful lesion tissue even after distant components were
removed. The.60 combination lost the case hit at7868 and reference-component
hits7636/component2 and7868/component1. All outcomes, including these failures,
remain in the [machine-readable results](STUNET-POSTPROCESS-RESULTS-20261108.json).

## What can be used next

Keep the prediction-only proximity filter as the leading inference candidate.
`component_proximity_filter_v1.filter_prediction` already accepts an explicit
physical radius;5mm can be checked without a new model architecture or weights.
The current default remains10mm and the helper is not wired into production.
Before promotion, freeze the candidate and evaluate on the corrected selected
model and a suitably independent cohort. The original pipeline uses supplied
pancreas regions, so this does not establish autonomous full-CT performance.

These filters still cannot recover disconnected missed lesions or correct
large overpredicted boundaries attached to a true lesion component. Recall
remains about54%. The next learning experiment remains the separately prepared
coarsest-supervision ablation, motivated by exact training-input replay; it
needs matched CUDA/backup/cold qualification and a scientific launch receipt
after the active Lenovo job releases its GPU. Do not mix that factor with the
spatial policy and attribute the combined result to training alone.

Lenovo's latest read-only snapshot at2:36p.m.Mountain was global14000,
2,000new updates, validating11/70cases and545/3963tiles, MLflowRUNNING/same
worker. No completed corrected full70 report existed then. Current training,
pins, recipe and hourly monitoring were untouched; no partial Dice is reported.
At2:46p.m.Mountain the same worker was still advancing through native validation,
MLflow remainedRUNNING, and no complete corrected report was available.

## Engineering evidence and scope

The [finite grid](STUNET-POSTPROCESS-SCREEN-20261108.md) was committed in
`d715238` before this screen's new array reads, explicitly informed by earlier
development results. Code/tests are in`3930284`. It is a new exploratory
follow-up, not a retrospective extension of the earlier confidence study.
Only existing replay codes, predicted pancreas, full affines and the same
hash-bound reference masks were read. References were used only for scoring.
No CT/model/GPU/optimizer/MLflow training activity, protected data or new
external cohort was involved.

Single-thread supervised execution finished in158.400s, peak ownedRSS
3,950,100,480B, exit0/workersreaped/no cleanup errors, within1800s/8GiB and
unchanged storage/AC/memory-pressure gates. Raw masks/counts and the10mm
incumbent reproduce exactly. All per-case reports, source request and resource
records have independent verified internal-drive backups. The separate
verification reopens independent raw replay backups, regenerates all630
candidate mask hashes and reproduces the complete summary; its actual
resources/status are in the adjacent JSON receipt. Nine focused CPU tests cover
geometry, holes, additive closing, fixed-grid fallbacks, denominator admission
and identity-preserving detection guards. No automatic deployment or successor.

MLflow analysis run `e787e84db21d44308385e14f776047fe` is FINISHED, with108
policy metric readbacks matching exactly. It was logged after execution as
`inference_policy_analysis`, explicitly excluded from training hours. Source
screen and verification artifacts use separate namespaces; the initial
same-name result artifact collision is documented in the artifact proof and
both correctly named results are hash-verified. Consistent database snapshots
and all final reports have verified independent backups. No old record was
deleted or scientific score changed during tracking closeout.

Primary evidence:
`/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108/postprocess-screen-01`.
Backup:
`/Users/quintonevans/PROWL-Backups/stunet-postprocess-screen-20261108-01`.
Unknown pretraining exposure and patient linkage remain explicit; neither this
screen nor its reused guards establish patient-independent generalization.
