# Verifier for CT refiner candidates

The verifier rejected all nine proposed refiner additions on the 70 exposed development scans. It removed seven false candidates and also rejected the two candidates with reference-lesion overlap, including the only newly detected small lesion. Dice, small-lesion detection, and false positives returned to the existing 24k core values. The verifier did not pass.

| Fixed arm | Positive-case mean Dice | Small hits /12 | Positive FP mL | Empty FP mL | Empty alarms /34 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing 24k core rule | .436709 | 7 | 154.519 | 47.292 | 23 |
| 0.50 CT refiner with fixed 5 mm filter | .437819 | 8 | 155.299 | 49.644 | 25 |
| Refiner with locked verifier | .436709 | 7 | 154.519 | 47.292 | 23 |

The newly detected small lesion ranked ninth of nine. On these saved candidates, a threshold low enough to keep it would also admit all seven false candidates. That ranking is a diagnostic of the fixed scorer. The development cases did not set the threshold.

Even perfect candidate rejection would leave some false-positive tissue. A reference-assisted diagnostic that keeps only the recovered small-lesion candidate yields .438035 Dice and 8/12 small hits, but adds 534 false-positive voxels (0.233 mL) on that scan. It is a bound for this fixed refiner output, not a usable decision rule. A pass with these prompts would need a more precise contour as well as better candidate rejection.

## Fitting and test boundary

The exact checkpoint-disagreement archive contained only development scans. The pilot therefore fit an L2 logistic verifier on proxy examples from 72 training-role scans, with another 36 training-role scans reserved for calibration. There were 96 positive crops and 288 hard negatives in fitting, then 48 positives and 144 negatives in calibration. Positives came from small-lesion centers and nearby voxels within the same components. The frozen locator supplied hard negatives at least 8 mm from annotated lesion voxels on lesion-positive training scans and from annotation-empty training scans. The verifier used the same 27 CT and frozen-refiner response features in both phases and in development.

Fitting and calibration used distinct case IDs and CT hashes, excluding the frozen refiner/locator's 108 fitting scans and all development cases. No patient crosswalk or exact out-of-fold disagreement examples were available. The proxy training distribution and nine actual proposals limit inference. A predeclared calibration rule used the next floating-point value above the largest negative score. It kept 1/48 calibration positives while accepting 0/144 negatives. The exact 0.50 refiner additions were reproduced and the locked verifier was applied before considering any change to the incumbent mask. No protected test, GPU job, or deployment was involved.

All 20 supervised stages completed and reaped their workers. Total CPU-worker elapsed time was 306.3 s with 2.62 GiB peak owned RSS. An independent reduction reproduced the threshold and the paired result. The result, estimator, feature tables, and resource receipts match their independent copies. MLflow run `cb8c51407c8b4b839e3594bf95ff7bb6` is FINISHED with metrics and snapshot integrity verified.

[Replay and fitting script](../../../scripts/diagnostics/run_mac_disagreement_verifier_20261111.py). Result SHA-256 `4f2c848b4c35861c27494f4333f4a95399c49a09818ba77dae6e8f10d7ee8510`.
