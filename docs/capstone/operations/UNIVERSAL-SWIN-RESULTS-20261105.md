# Larger Universal Swin pretrained screen: completed

**Mean native lesion Dice was0.710754 across the four predeclared positive development cases.** The one permitted inference-only experiment completed successfully. No training or adaptation occurred: all12candidate training cases retained their explicit-unit admission failures. Negative-case alarm rate was not measured.

| Case | Lesion Dice | Precision | Recall | Extra predicted lesion volume, mL | Prior autonomous Dice, same case |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2028 | 0.826177 | 0.839477 | 0.813291 | 0.820159 | 0.464840 |
| 1347 | 0.388500 | 0.381709 | 0.395536 | 2.945671 | 0.476145 |
| 2514 | 0.764949 | 0.673825 | 0.884574 | 1.717585 | 0.083505 |
| 8743 | 0.863391 | 0.879121 | 0.848214 | 0.625126 | 0.815458 |
| Positive-case mean Dice | **0.710754** | | | | **0.459987** |

The mean descriptive difference on these identical four cases is+0.250767; three improved and one worsened. Source CT/reference hashes match the earlier autonomous evaluation. The model, pretraining and preprocessing differ, so this comparison does not isolate architecture capacity. It is not a comparison with the full70-case result or a published benchmark. The cases were selected by existing cohort order and explicit units before predictions, not by model scores.

All4reference lesion components had some overlap. There were4zero-overlap predicted components in total (three on1347 and one on2514). Any overlap is not a clinical detection criterion. Case1347 remains a clear weakness: lesion recall0.3955,precision0.3817, with the largest extra predicted lesion volume. Pancreas-including-lesion Dice by case was0.912259,0.839129,0.905837,0.930992. Combined codes give lesion precedence; the independent raw pancreas prediction is also preserved.

## Interpretation and limitations

The larger externally pretrained model is promising enough to justify a separately planned broader evaluation. This screen does not establish independent generalization, healthy-case specificity, convergence from transfer training, or completion of the project's broader Dice target. External pretraining membership is unknown and these four development cases have been reused. No confidence interval or H0/practical-acceptance verdict was issued; H0 is NOT_TESTED. No additional experiment, threshold search or retry is authorized by this closeout.

The model used whole CT-derived foreground at1.5mmRAS,HU[-175,250],96cube/Gaussian overlapping inference, two selected CPU logit accumulators, strict>0.5 probabilities and no TTA/postprocessing/reference-driven crop. Native restoration uses explicit physical affine and linear probability interpolation. This current-MONAI implementation differs from the upstream original hard-mask inversion, as frozen before outputs. All CT/reference units were explicitly mm. No unknown-unit exception was used.

## Execution and integrity evidence

- One-shot owned18866/supervisor26696 exited0. All10stage workers exited0 and were reaped: CUDApilot, independentCPUrestore, four inference and four separateCPUscore workers. No owned processes or GPU compute owners remained.
- Actual model62,595,315parameters,170state entries. Original publisher checkpoint SHA cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07. Strict independentC checkpoint reload exactly matched canonical state SHA23f0c1b107cb20c71be4323634095c4e305cb9c228df3dbec7bb27f92160c97a.
- Pilot15.922s; independentrestore12.640s. Peak workerRSS2,006,016,000bytes. Maximum saved CUDAreserved4,915,724,288bytes, below6GiB; pilot allocated3,184,069,120bytes. No resource cap was raised.
- Saved evaluation interval365.032seconds, about6.08minutes. Conservative preparation charge3,600seconds remains within the overall21,600second budget; this is inference time, with **zero training hours**.
- Operator independently rehashed all5,442producing pins and all45output/backup file pairs (762,045,416bytes each side). Relative file sets and the producer completion manifest agree. E exFAT and C NTFS volumeGUIDs were rechecked as distinct; previously recorded physical disks1and0 remain the separate output/backup devices. Free-space floors passed.
- MLflow051c194b2e54428aba6b9420129e18b6 is **FINISHED**, labeled inference-only/exploratory/external-exposure-unknown. Allfour stored lesion Dice values and the mean were read back and matched the saved native scores.

Frozen requestSHA4654d46b730abe8c144b1cc57af607d579154b1c96ff707c37861fbce55fadc5; Mac permitSHA b6b76fc7e1667a7b5c3c13e93796e6460105d0f3e8f0023b30e12f8a499f8aba. Private artifacts remain under `E:/PROWL/artifacts/universal-swin-screen-20261105-a01`, with independentC backups. The adjacent sanitized JSON contains per-case/component findings, complete output hashes and operator-closeout evidence. No weights, scan arrays, masks or probability arrays are committed to Git.
