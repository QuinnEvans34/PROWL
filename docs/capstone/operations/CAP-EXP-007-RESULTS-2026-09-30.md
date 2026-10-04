# CAP-EXP-007 — exact run completed; coverage retained, predictions still oversized

D-306 executed the exact request Quinton approved. All300 updates,386 scheduled native evaluations,
four checkpoint boundaries and independent recovery completed within the frozen limits.
**This is a successful training/recovery transaction, not a usable or promoted localizer.**
Validation mean native Dice reached0.098701 and recall0.982700, but only1/40 ROI screens passed.
The next useful experiment is a longer **fresh** run on the same frozen cohort, with an explicit
coverage safeguard and a separately reviewed duration/schedule. No further run is authorized here.

## What ran

All113 training and40 development-validation cases were retained.300updates gave39 cases two
exposures and74 cases three exposures; each of the first two113-case passes visited every training
member exactly once.146 sampling centers were foreground and154 background. No validation case
entered the optimizer. The23 pre-existing holds and original base memberships remain unchanged.

Fresh seed42 SegResNet,144³ patches/uniform2mm,balancedCE+Dice,AdamW0.0003/weight decay0.00001,
cosine schedule to zero at300,MPS float32/fallback disabled,two CPU threads and zero loader workers.
The exact [launch design](CAP-EXP-007-LAUNCH-PLAN-2026-09-30.md) was not edited or extended.
Checkpoints0/113/226/300; full before/after evaluation and40-case validation at113/226.

## Native-grid results

Means are per case. References represent the visible annotated pancreas; they do not establish
whole-organ completeness. Development-validation is not a sealed test set.

| Split / step | Mean Dice | Mean recall | Median prediction/reference volume | Mean acquired-scan crop fraction | ROI screen passes |
|---|---:|---:|---:|---:|---:|
| Train113 /0 |0.001700|0.018415|18.304×|0.9972|0/113|
| Validation40 /0 |0.002053|0.024605|23.693×|1.0000|0/40|
| Validation40 /113 |0.061027|0.959212|31.694×|0.6159|0/40|
| Validation40 /226 |0.082020|0.984972|23.991×|0.4180|0/40|
| Train113 /300 |0.097323|0.978471|18.749×|0.4152|2/113|
| Validation40 /300 |0.098701|0.982700|18.497×|0.4218|1/40|

All153 initial per-case metric records exactly reproduce the D-304 initialized baseline. All final
predictions are nonempty. Validation box-reference coverage is1.0 for all40 cases, but39 exceed the
0.25 acquired-scan crop-size limit. The ROI screen requires both≥0.995 box coverage and≤0.25 size;
it is not contour certification. Training has112/113 coverage passes and2/113 joint passes.
Validation mean volume ratio is180.582×, much larger than its18.497× median because tiny references
remain included. Neither statistic should be interpreted without those cases.

Patch loss stayed finite. First/last25-update median losses were1.438248/1.145623. Those batches
contain different cases/crops, so this is a descriptive optimization trace, not a matched loss test.
The similar final train/validation Dice values do not prove generalization or diagnose overfitting.
Only two or three case exposures were made; the duration is still a bounded diagnostic.

## Retained failures and selected inspection

Eight contact sheets were inspected using verified cached CT/reference arrays and native predictions
projected to the processed grid for display. No original CT/reference file was reread for this review.
This is selected visual inspection, not an exhaustive visual review or clinical interpretation.

- Validation3115:lowest recall0.786705,Dice0.082795; visible missed reference and substantial excess.
- Validation6186:recall0.897549,Dice0.058108; excess foreground remains pronounced.
- Validation6081:near-median Dice0.101; broad surrounding prediction persists.
- Validation1004:best Dice about0.240; still visibly oversized.
- Training7604:recall0.790067 and box-reference coverage0.922077. Its crop misses reference despite
  using30.23% of the scan. This failure is retained; the high average does not erase it.
- Validation6534:the sole validation ROI pass (crop fraction0.239329), but its mask still contains
  extensive extra foreground. Passing the localization screen does not make the contour acceptable.
- Tiny references6110/2727 both retain native recall1.0. Their Dice values remain0.001914/0.000314,
  and volume ratios1044.11×/6362.53×. They stay in every applicable aggregate and future candidate
  accounting; no case was dropped, relabeled or requalified because of these results.

[Inspection notes](../../../outputs/prowl/CAP-EXP-007-review-20260930/inspection-v2.md) and the eight
contact sheets are in the review package. Numerical metrics use the acquired native grid; the
nearest-neighbor projection is only for display. No threshold/component policy was changed.

## Execution, integrity and recovery

| Item | Verified result |
|---|---:|
| Worker time |1969.790s|
| Total supervised worker + recovery |1984.920s /33.082min, below45min|
| Peak process RSS |6,053,740,544bytes /5.638GiB|
| Peak sampled MPS driver |5,152,505,856bytes /4.799GiB|
| Original pancreas-reference reads |386|
| Compressed / expanded reference bytes |53,708,928 /10,774,955,452|
| New original CT reads |0|
| Checkpoints + evaluation record packages + terminal keeper |4+4+1=9|
| Independent restores with primary reads blocked |9|
| Restored terminal prediction probe maximum difference |0|
| Sealed package files independently rehashed |805|
| Native exports rechecked |386|
| Local sealed-package member bytes |263,716,041|

All per-case count arithmetic, retained decoder counts, source-reference hashes, role memberships,
source-grid geometry/crop fractions and update exposures were independently checked from retained
records. This review did not perform an extra source-label pass. The runtime also verified the
frozen source/environment after execution. No resource limit, model update, checkpoint or recovery
failure was reported. The consumed request must not be rerun or silently continued.

The nine keepers protect checkpoints, evaluation records and the terminal journal. Native prediction
mask bytes and review figures remain derived local scratch, explicitly not independent mask backups.
Their hashes and producing model/control identities are retained. Recovery claims are limited to the
keepers actually restored.

Production source and dependencies did not change during this run. The D-3051,539-test native
baseline remains the source verification; no redundant software test rerun was needed. Postprocessing
found optional Matplotlib absent and used the existing contact-sheet helper instead, without installing
a dependency or changing the training environment. That visualization issue did not affect the run.
No model promotion, new qualification, source activation, commit or push occurred.

## Immutable references

Request directory:`outputs/prowl/twomm-training-cd6be21f-7dcf-4bd5-b9da-a704f5f1167f`.
Request SHA:`b13ebbce1731090a65dd5fe6c8327963f8e50203e39c25aa8ee6c88f903d85b3`.
Approval:`outputs/prowl/CAP-EXP-007-APPROVAL-2026-09-30.json`;
SHA:`a37e461c3be0a82a0729b8f77252facfc873d5e84d72b2f1573d798b5ebd18fa`.

Execution:request prefix plus`-execution`;
completion SHA:`a7dd38662304d20bf8fc9bd9801a6ba692d1f74b9ff176b5434dd377a933b975`.
Terminal checkpoint:`twomm-training-cd6be21f-7dcf-4bd5-b9da-a704f5f1167f:step:300`;
primary receipt:`f7f48677a3fadf00a8d280d149089aaef2aea9e99a76c3b91d1800eb36f574bf`;
backup receipt:`29fc13699f771e100d48eb0bfdbd17fd9e14a5df087d88ad14bbfa5d763edbb9`.

Review:`outputs/prowl/CAP-EXP-007-review-20260930`;
Current `receipt-v2.json`:`d2c92cd5a5a13c1f431ae40664db19d5ad41fcca7a47105ad892d2edb0953187`.
Original review receipt `eb1f0775393c47dd1f2d85b21b2a2ce2df05a5f413f96b9db6f650220fdf30fe`
is preserved. Revision2 corrects display slice metadata to the actual median-reference indices
and clarifies that7604's misses are outside its selected central planes; no image/model/metric changed.
The review retains its verification scripts/log, all386 case records, exposure/loss history,
summary and eight selected contact sheets. Native original references were not copied into this package.

## Recommendation

Keep the same qualified cohort and input/prediction policies for a longer fresh duration/schedule
comparison. The useful question is whether the model can remove excess foreground while retaining
coverage. CAP-EXP-006 previously lost coverage as Dice improved, so freeze checkpoints and explicit
coverage review/stop criteria before increasing the budget. Do not interpret this short broader run
as a controlled comparison against CAP-EXP-006:cohort,spacing,context and case exposures differ.
The present adapter still caps updates at300; any longer run requires a separately tested bounded
budget and exact launch request. No automatic extension or next-run approval is implied.
