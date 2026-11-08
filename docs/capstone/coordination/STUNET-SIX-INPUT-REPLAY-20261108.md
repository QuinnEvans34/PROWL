# Six exact training-input replays: CPU diagnostic

Six frozen TRAIN addresses replayed exactly: image/target hashes and full augmentation/input traces match saved scientific updates. No model, optimizer, inference or protected data reads. One worker/core, torch threads1, CUDA_VISIBLE_DEVICES=-1; CUDA unavailable and uninitialized. Supervised **60.985seconds / 1,485,688,832bytes peak RSS**, exit0, workers reaped and absent. Limits600s/2GiB; AC/free-space and competing-memory gates held. Live trainer/monitor unchanged.

## Lesion-label survival

| Selection | Training case | Global update | Lesion voxels at128/64/32/16/8 cubed |
| --- | --- | --- | --- |
| smallest | PanTS_00006811 | 12017 | 140 / 20 / 4 / 1 / 0 |
| next_smallest | PanTS_00003513 | 12043 | 102 / 12 / 3 / 1 / 0 |
| median_lower | PanTS_00007105 | 13200 | 2974 / 338 / 34 / 2 / 0 |
| largest | PanTS_00002720 | 13054 | 685055 / 84803 / 10375 / 1243 / 139 |
| ordinary_empty | PanTS_00004336 | 12001 | 0 / 0 / 0 / 0 / 0 |
| corrected_empty | PanTS_00003059 | 12373 | 0 / 0 / 0 / 0 / 0 |

Augmentation preserved all class counts. Each positive augmented patch contains one26-connected lesion component. Its identity was propagated through the exact nearest-slice target map and checked against the downscaled lesion target. The two smallest and median-case patch components disappear entirely at8cube; they survive16cube and every finer scale. The largest survives all five. The8cube term has weight1/31, so this is a concrete coarse-supervision limitation, not proof that it causes current Dice behavior. No changes made.

## Coverage versus supervision

The median-volume case's chosen address is a context view. The native cropped region contains6987lesion voxels; the sampled patch contains2974. This is scheduled partial viewing, not evidence that the complete native region lost annotations. Physical interpolation means native/patch voxel counts need not match (especially for coarse native spacing). This six-case diagnostic does not replace the existing full-field coverage audit.

## Intensity evidence

Support/padding endpoint counts and fractions are saved before and after augmentation. Exact native cropped-region raw-HU clipping counts/fractions are conditioned on background/pancreas/lesion. Both smallest lesions and the largest have zero native lesion voxels outside[-100,250]; median has41/6987 below-100 (42at-or-below), zero above250. This is native-region evidence, not interpolated patch evidence.

Patch endpoint fractions conditional on lesion/pancreas and intensity quantiles were NOT captured. Support-only endpoint fractions include expected background saturation; they should not be interpreted as lesion saturation. No active audit pins were edited and no case was repeated to add metrics.

## Reproducibility

Selection was frozen before array reads from observed traces: earliest eligible address for smallest, next-smallest distinct, lower-median and largest positive native-case volumes; earliest ordinary-empty and corrected-empty. Only six CT paths and six training target archives were opened; array/model allowlist enforced. JSON includes exact request, input/source pins, expected traces, all results with derived fractions, source text, source hashes, actual resource and reaping proof. Synthetic nearest reduction check passed before real reads.

Private evidence: E:/PROWL/readiness/stunet-six-input-replay-20261108-a01. Request SHA256 `0b1a526cc33fb11bc8ddd695b70a0ad638eb1654a01da48a42513e8308a6cf24`. Export JSON SHA256 `f633ac6bf2f4b64fda295dce69eea9e814a3a58464c3a81e8190308ebf06c6b4`. This is nonpromotable input evidence; no H0 verdict, new recipe, or future-run launch.
