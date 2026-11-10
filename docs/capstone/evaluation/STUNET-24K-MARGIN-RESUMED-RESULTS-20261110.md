# Terminal 24k: measured inference-policy results — November 10

Raw Dice: **0.411971**. Fixed 5 mm: **0.428578**. Guard-qualified exploratory selection: **grow0.5_seed-0.5_near5**, Dice **0.432626**.

Highest Dice ignoring safeguards: **grow1_seed-0.5_near5** (0.436645); guard status: False. An ineligible maximum is not a recommended improvement.

All 70 exposed development cases, 36 positive / 34 empty, 45 reference components and five small positive cases retained. Fourteen verified cases reused plus56new cases; 54 fixed reference-free decisions, zero training updates. Provided-pancreas-region evaluation; no independent or leakage-free performance claim. No policy deployed.

| Policy | Dice | Recall | Small recall | Cases / components hit | Empty alarms | FP mL | Guards |
|---|---:|---:|---:|---:|---:|---:|---|
| raw | 0.411971 | 0.499250 | 0.379244 | 34/36; 38/45 | 27/34 | 221.321 | control |
| bias0_near5_min0 | 0.428578 | 0.499250 | 0.379244 | 34/36; 38/45 | 24/34 | 162.869 | False |
| grow0.5_seed-0.5_near5 | 0.432626 | 0.542585 | 0.432125 | 35/36; 39/45 | 23/34 | 208.787 | True |
| grow1_seed-0.5_near5 | 0.436645 | 0.587510 | 0.481857 | 35/36; 39/45 | 23/34 | 258.896 | False |
| grow1_seed-0.5_near10 | 0.436190 | 0.587510 | 0.481857 | 35/36; 39/45 | 23/34 | 259.726 | False |
| grow0.5_seed-0.5_near10 | 0.432307 | 0.542585 | 0.432125 | 35/36; 39/45 | 23/34 | 209.319 | True |
| bias1_near5_min25 | 0.431059 | 0.587937 | 0.481857 | 35/36; 39/45 | 26/34 | 269.666 | False |
| bias0.5_near5_min25 | 0.430951 | 0.542792 | 0.432125 | 35/36; 39/45 | 24/34 | 212.248 | False |
| bias1_near5_min10 | 0.430932 | 0.587937 | 0.481857 | 35/36; 39/45 | 26/34 | 269.801 | False |
| bias0.5_near5_min0 | 0.430931 | 0.542873 | 0.432125 | 35/36; 39/45 | 25/34 | 212.451 | False |
| bias1_near5_min0 | 0.430922 | 0.587953 | 0.481857 | 35/36; 39/45 | 26/34 | 269.845 | False |
| bias0.5_near5_min10 | 0.430915 | 0.542792 | 0.432125 | 35/36; 39/45 | 24/34 | 212.410 | False |

## Interpretation

Selected gain versus raw: +0.020655; versus standing 5 mm: +0.004048. These comparisons share the newly generated MPS raw control. Original CUDA differences are retained per case; they are not attributed to the decision policy.

A failed recall, small-lesion, case/component identity, pancreas, empty-alarm or false-positive-volume guard disqualifies a setting even if its Dice is higher. Selection on these already exposed cases is optimistic. Confirmation on a prospectively fixed later checkpoint and, ultimately, a verified independent cohort remains necessary.

This finite search tunes inference decisions, not learning rate or the training loss. Any later training ablation must preserve a matched control and wait for Lenovo GPU availability.

## Integrity and execution

Checkpoint SHA256: `2cb9ff72c66b67f8bcdcb081c5d3f84735a83830f693ad2990fb8139933da92c`. Request SHA256: `1e8f3ff8b98014af3d560638bd0567fb6bf29ac40fb214deaef7db27154dbbdc`.

Elapsed worker seconds: 6386.7; resource and cleanup verification: VERIFIED_COMPLETE. All 54 policies were independently replayed from each reopened case backup. Final summaries were independently rebuilt from saved case records; all producing pins matched. MLflow stores this as inference-policy work, excluded from training hours.

[Protocol](../operations/STUNET-24K-MARGIN-SCREEN-20261110.md). [Closeout evidence](STUNET-24K-MARGIN-RESUMED-CLOSEOUT-20261110.json).

Method context: [nnU-Net validates component-removal postprocessing](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/how-to/find-best-configuration.md); [Optuna documents exhaustive finite-grid search](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.GridSampler.html). Those sources motivate evaluating decisions rather than assuming that a filter helps; they do not establish a gain for PROWL.
