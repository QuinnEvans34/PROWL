# Terminal24k: secondary attached-voxel clipping results

Six additional prospectively frozen CPU policies, reusing the primary study’s exact native codes. Combined search:60 settings; all70 exposed development cases retained (two pilots reused, 68 newly scored). No additional model pass, CT voxel read or training update.

| Secondary policy | Dice | Recall | Small recall | Case/component hits | Empty alarms | FP mL | Guards |
|---|---:|---:|---:|---:|---:|---:|---|
| clip_bias0.5_near10 | 0.419192 | 0.516217 | 0.432125 | 35/36; 39/45 | 26/34 | 198.971 | False |
| clip_bias0.5_near20 | 0.430541 | 0.542026 | 0.432125 | 35/36; 39/45 | 26/34 | 211.958 | False |
| clip_bias0.5_near5 | 0.350313 | 0.380566 | 0.342044 | 35/36; 39/45 | 25/34 | 162.463 | False |
| clip_bias0_near10 | 0.415422 | 0.475593 | 0.379244 | 34/36; 38/45 | 25/34 | 154.370 | False |
| clip_bias0_near20 | 0.427739 | 0.498491 | 0.379244 | 34/36; 38/45 | 25/34 | 163.572 | False |
| clip_bias0_near5 | 0.341483 | 0.342534 | 0.289163 | 34/36; 38/45 | 24/34 | 122.650 | False |
| raw | 0.411971 | 0.499250 | 0.379244 | 34/36; 38/45 | 27/34 | 221.321 | control |

Best guard-qualified setting across all60: **grow0.5_seed-0.5_near5**, Dice **0.432626**; gain versus raw +0.020655, versus standing5mm +0.004048.

Highest Dice ignoring guards: **grow1_seed-0.5_near5**, 0.436645; guard pass: False.

Selection remains optimistic on already exposed development cases. Failed recall/detection/pancreas safeguards cannot be traded for a higher headline score. No policy deployed and no independent/leakage-free claim.

[Primary54-policy result](STUNET-24K-MARGIN-RESUMED-RESULTS-20261110.md). [Prospective addendum](../operations/STUNET-24K-VOXEL-CLIP-ADDENDUM-20261110.md).
