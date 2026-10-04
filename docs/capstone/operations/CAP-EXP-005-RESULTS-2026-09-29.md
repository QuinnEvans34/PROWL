# CAP-EXP-005 results — September 29, 2026

**Completed as approved under D-286: 288 real updates, no retry or extension.** Learning is visible
on both training and separate development-validation cases, but masks remain substantially oversized.
The experiment mechanics and independent recovery passed. Useful mask quality is not established.

## Learning and localization

| Step | Role | Mean Dice | Mean balanced loss | Fixed ROI screen |
|---|---|---:|---:|---:|
| 0 | Training | 0.0006 | 1.8103 | 0/16 |
| 0 | Validation | 0.0009 | 1.8077 | 0/11 |
| 144 | Training | 0.0647 | 1.1614 | 11/16 |
| 144 | Validation | 0.0845 | 1.1687 | 5/11 |
| 288 | Training | 0.1262 | 1.1143 | 13/16 |
| 288 | Validation | 0.1512 | 1.1438 | 9/11 |

Final Dice ranges: training0.0040–0.2226, validation0.0910–0.3075. All27 predictions are nonempty.
**Zero of27 pass the stricter mask-fit screen** (recall>=0.98, Dice>=0.65, volume ratio<=2).
Median predicted/reference volume ratio is13.08 for training and12.56 for validation. Mean mask
recall is0.9867 and0.9490 respectively. Thus high reference inclusion is accompanied by poor
precision/excess foreground, not adequate contours.

The prediction-only all-component box with requested10mm margin (12mm on the3mm grid before
clipping) covers100% of every training reference and at least99.7518% of each validation reference.
All five ROI-screen failures are due to boxes exceeding25% of processed scan volume: training
5286,5593,6886 and validation7482,7839. They occupy38.9%,33.6%,70.5%,30.0%,27.7% respectively.
A passing ROI screen is provisional: no Stage2 mapping or lesion containment was evaluated.

All27 three-plane overlays were reviewed. They show broad foreground around reference regions;
several failures also show distant foreground. This is a limited processed-grid engineering review,
not exhaustive source-slice review or expert acceptance. Partial/boundary cases3717 and4965 remain
included: their Dice is0.0162/0.0040 and volume ratio116.72/496.02. Case4965's59-voxel processed
reference makes its ratio particularly large; its passing box screen does not prove complete-organ
coverage. Noisy cases8037/8443 also remain included. No post-result eligibility changes occurred.

Both groups improve between144 and288: training Dice0.0647→0.1262; validation0.0845→0.1512.
Median volume ratios also shrink (training27.62→13.08; validation22.55→12.56), though mask recall
falls slightly as predictions shrink. This supports testing more training exposure; it does not
prove that duration alone will fix the objective's high-recall/low-precision behavior. Validation
being slightly higher than training is not a generalization guarantee: the groups are small and
different, and training contains tiny partial references.

## Execution and recovery

- Exactly18 updates per each of16 training members; zero validation members in update history.
- Full27-case evaluations at0/144/288; checkpoints0/96/192/288 retained.
- All27 final native binary NIfTI/PNG/transform-metric packages published and revalidated.
- Total supervised time605.85s (10.10min), including load/backup/recovery; update phase247.46s.
- Peak RSS9,245,540,352 bytes (8.61GiB), within16GiB. No time/storage/memory limit was extended.
- **32 artifacts** (four checkpoints,27 cases,terminal) independently backed up and restored.
- Fresh-process restoration with Python primary-drive reads blocked recovered step288; fixed probe
  max difference **0**. No physical drive-unplug test is claimed.
- Frozen source/environment remained unchanged. The verified implementation baseline is1,170
  native tests; no code changes or redundant full-suite rerun were needed for this execution.

This is an expanded-cohort smoke with18 updates per case, not a controlled comparison to the older
CAP-EXP-004 two-case result (~150 updates per case). It is pancreas-only research. The validation
cohort lacks arterial/thin-slice coverage, and study-as-subject identity remains unverified.
Publisher-test payloads were not used. Case6350 remains held with no replacement.

## Retained evidence

Request SHA: `2fa5f7f20916fb047ddcc54c3aede63e5f1c57566227cec1ef07a1d9756ae456`.
Approval SHA: `578b42bb36e6adfcc87e74716177c82938dcb3f7f6543054c2cbd3082066f258`.
Run directory: `outputs/prowl/expanded-execution-0cb02ead-2908-40f5-a56a-a4077250b4d9`.
Job receipt: `13ebf8e9423d60d62ef105f65eef088331268cff9df9c656d8650216849ef2ed`.
Primary terminal receipt: `3f80d5be10ecfe40d94d9312872ac800a70674cae4e9463ec77672cd73f2e4fa`.
The recovery request and recovery records retain all32 primary/backup/restore references.

Derived review: `outputs/prowl/cap-exp-005-review-20260929` (all per-case metrics/overlays and
trajectory). Its copies have a separate hash receipt. Every job-receipt member and every referenced
checkpoint/export was checked during post-run review. Separate visual-review evidence is in
`outputs/prowl/cap-exp-005-visual-review-20260929`; receipt SHA
`b032ad0fc44abc6343c40fc08b8c55a8133a879ccccd1c24ed36407af5d02873`.
Original run evidence and consumed request are preserved unchanged.

## Next recommendation

Prepare a controlled duration/schedule-horizon comparison on the **same16/11 cohort**, preserving
initialization, objective, preprocessing, sampling and all cases. A candidate is576 fresh updates
(36 equal cycles); it is **not approved or runnable under the current300-update configuration cap**.
Any extension needs a separately versioned bounded configuration, measured budget and frozen request.
Cosine horizon changes with duration, so describe that explicitly rather than claiming an identical
learning-rate history. Do not change loss, threshold and cohort simultaneously, continue these weights
without a new plan, or discard difficult cases. Longer training is the next hypothesis, not a promise.

Stop here for regroup: no further training was launched, no consumed request was reused, and no
source or literature files were changed. Git publication was outside this run's scope.

## Final per-case evidence

| Case | Role | Dice | Mask recall | Volume ratio | Box reference coverage | Box scan fraction | ROI screen |
|---|---|---:|---:|---:|---:|---:|---|
| PanTS_00000003 | Train | 0.1459 | 1.0000 | 12.71 | 100.000% | 22.45% | Pass |
| PanTS_00000026 | Train | 0.1267 | 0.9603 | 14.16 | 100.000% | 20.58% | Pass |
| PanTS_00002973 | Train | 0.1044 | 0.9574 | 17.34 | 100.000% | 15.37% | Pass |
| PanTS_00003188 | Train | 0.1548 | 0.9997 | 11.91 | 100.000% | 12.02% | Pass |
| PanTS_00003191 | Train | 0.1372 | 0.9908 | 13.44 | 100.000% | 12.03% | Pass |
| PanTS_00003239 | Train | 0.1473 | 0.9969 | 12.53 | 100.000% | 11.99% | Pass |
| PanTS_00003668 | Train | 0.1617 | 0.9975 | 11.33 | 100.000% | 12.06% | Pass |
| PanTS_00003717 | Train | 0.0162 | 0.9527 | 116.72 | 100.000% | 15.85% | Pass |
| PanTS_00004226 | Train | 0.1477 | 0.9762 | 12.22 | 100.000% | 20.25% | Pass |
| PanTS_00004965 | Train | 0.0040 | 1.0000 | 496.02 | 100.000% | 8.66% | Pass |
| PanTS_00005286 | Train | 0.1237 | 0.9685 | 14.66 | 100.000% | 38.94% | Fail |
| PanTS_00005593 | Train | 0.1117 | 0.9936 | 16.79 | 100.000% | 33.61% | Fail |
| PanTS_00006886 | Train | 0.0652 | 1.0000 | 29.66 | 100.000% | 70.48% | Fail |
| PanTS_00007295 | Train | 0.1868 | 0.9978 | 9.68 | 100.000% | 11.79% | Pass |
| PanTS_00008037 | Train | 0.1629 | 1.0000 | 11.28 | 100.000% | 8.89% | Pass |
| PanTS_00008443 | Train | 0.2226 | 0.9967 | 7.96 | 100.000% | 12.36% | Pass |
| PanTS_00001004 | Val | 0.3075 | 0.9462 | 5.15 | 99.752% | 10.73% | Pass |
| PanTS_00002942 | Val | 0.1750 | 1.0000 | 10.43 | 100.000% | 14.24% | Pass |
| PanTS_00003104 | Val | 0.1670 | 0.8691 | 9.41 | 99.815% | 10.21% | Pass |
| PanTS_00004995 | Val | 0.0910 | 0.9971 | 20.92 | 100.000% | 18.95% | Pass |
| PanTS_00005747 | Val | 0.1809 | 0.9955 | 10.01 | 100.000% | 13.56% | Pass |
| PanTS_00007265 | Val | 0.1345 | 0.9114 | 12.56 | 100.000% | 12.72% | Pass |
| PanTS_00007482 | Val | 0.1184 | 0.9290 | 14.70 | 100.000% | 29.95% | Fail |
| PanTS_00007484 | Val | 0.1039 | 1.0000 | 18.24 | 100.000% | 21.34% | Pass |
| PanTS_00007687 | Val | 0.0942 | 0.9745 | 19.69 | 100.000% | 24.89% | Pass |
| PanTS_00007839 | Val | 0.1101 | 0.8232 | 13.96 | 100.000% | 27.71% | Fail |
| PanTS_00008855 | Val | 0.1808 | 0.9935 | 9.99 | 100.000% | 9.77% | Pass |
