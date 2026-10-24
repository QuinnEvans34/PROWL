# Revised Mac teacher pilot results — October23

**Execution and coverage passed; teacher usefulness not accepted. No scientific training launched.**

One authorized revision02 run completed all12 fixed training cases and869 tiles. The earlier failure remains preserved. All318 prepared source/input pins still match. The final successful worker path includes a frozen-teacher state equality check. Exit0, supervisor receipt present, workers reaped; no pilot or guardian process remained at inspection.

Elapsed 2582.73s (43.05min); peak sampled owned RSS 3,768,172,544 bytes (3.51GiB). Per-tile MPS allocation checks did not fail; a continuous GPU peak was not recorded. Probability caches total 9,618,106 bytes. This selected cohort cannot establish full-cohort compression or timing.

Every actual preprocessed grid matched its projection; every native region had full probability support and zero out-of-field voxels. Both prior boundary-deficit cases passed. This qualifies this bounded execution, not a full scientific launcher or target-cache admission.

## Quality diagnostics

All12 saved three-plane figures were actually inspected. They are physically scaled, but do not constitute exhaustive component/extreme-slice review. Supplied annotation agreement is being measured; no clinical interpretation or annotation correction was performed.

| Case | Dice | Recall | Reference voxels | Predicted voxels | Components detected |
| --- | ---: | ---: | ---: | ---: | ---: |
| PanTS_00002720 | 0.060 | 0.031 | 189621 | 6145 | 1/1 |
| PanTS_00003615 | 0.640 | 0.472 | 58501 | 27801 | 1/1 |
| PanTS_00000691 | 0.000 | N/A | 0 | 8112 | 0/0 |
| PanTS_00003059 | 0.000 | 0.000 | 12 | 10 | 0/1 |
| PanTS_00000246 | 0.109 | 0.061 | 264178 | 33427 | 1/1 |
| PanTS_00008658 | 0.401 | 0.278 | 17911 | 6908 | 1/7 |
| PanTS_00003777 | 0.090 | 0.821 | 819 | 14088 | 1/1 |
| PanTS_00004735 | 0.721 | 0.903 | 1302 | 1962 | 1/1 |
| PanTS_00002498 | 0.461 | 0.909 | 4599 | 13538 | 1/1 |
| PanTS_00001193 | 0.659 | 0.562 | 6681 | 4713 | 2/2 |
| PanTS_00005832 | 0.233 | 0.510 | 1405 | 4749 | 1/1 |
| PanTS_00006222 | 0.747 | 0.639 | 29747 | 21135 | 1/1 |

Positive-case macro Dice 0.375; macro recall 0.471. These are exposed training/potentially teacher-seen diagnostics, not independent performance.

11/18 annotated26-connected components had any overlap;2/9 components under1mL were detected. Seven components had no positive eligible KD voxels under the existing conservative quantized rule. The multi-component case detected1/7, and the12-voxel lesion was missed. The single annotation-negative case had8,112 predicted lesion voxels. No population specificity claim follows from one negative case.

The component/stratum audit read only the completed probability files and24 hash-verified training masks. No CT voxels or models were loaded for this audit. It records q>=.9 contradictions, q<=.1 suppression and per-component eligible counts. Quantization adds threshold uncertainty; no confidence calibration is claimed.

## Decision and next experiment

Do not generate the full teacher cache or start KD training yet. Successful coverage does not resolve severe underprediction, missed small components and false positives. Agreement masking would preserve manual supervision, but does not establish that these targets add useful information.

Next recommended bounded investigation: compare the candidate single-pass inference with the pinned upstream reference behavior on a prospectively fixed small subset spanning a strong case, a missed tiny lesion and a severely underpredicted large lesion. First identify executable preprocessing/inference differences from source; qualify any actual reference executor before dispatch. Keep weights, annotations, source geometry and cases fixed. Do not tune a threshold, exclude cases, or change the KD loss merely to improve this pilot score. No such additional run is launched here.

## Evidence

External root: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/`.
- `patient-pilot-02/request.json`, `source.zip`, `process.json`, `guardian-ready.json`, `resources.json`, `result.json`, all12 case reports/figures/probabilities.
- `pilot-02-probability-review.json`: source/probability/image hashes and component/stratum summaries.
- Existing public `pilot-review.json` now records the inspected representative images while leaving full-review acceptance false.

No failed artifacts overwritten, no retry, no automatic follow-up, no MLflow scientific run or UI promotion.
