# STU-Net seven-case annotation errata review — November 8

**Confirmed: completed launch02 used the original seven positive targets rather than the documented normal-case errata policy.** This is a label-policy integration omission, not a demonstrated cause of aggregate Dice. Original run, receipts, caches, source files and metrics are preserved.

The frozen input binds varied-targets-20261022-a01. Its plan and matching cache JSON record all seven cases as positive, with the exact documented original lesion counts. Cache metadata hashes match the plan, source hash dictionaries match, plan/input/cache-manifest hashes match their bindings. The saved training journal records actual lesion-containing targets for these cases. No CT, mask, NPZ or checkpoint array was read or rehashed.

| Case | Recorded original lesion voxels | Visits | Coverage | Component focus | Context | Lesion-containing patches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PanTS_00000044 | 16 | 8 | 2 | 4 | 2 | 6 |
| PanTS_00001819 | 45 | 8 | 2 | 4 | 2 | 7 |
| PanTS_00003059 | 12 | 9 | 2 | 5 | 2 | 6 |
| PanTS_00003548 | 36 | 9 | 1 | 5 | 3 | 6 |
| PanTS_00005693 | 20 | 11 | 4 | 5 | 2 | 9 |
| PanTS_00007933 | 16 | 8 | 2 | 4 | 2 | 6 |
| PanTS_00007947 | 32 | 9 | 1 | 5 | 3 | 6 |

All seven are training members and none is a development member. They received **62 updates total**, including **46 lesion-containing patches**. The JSON includes each saved step, view kind, lesion voxel count and target hash, plus original lesion hashes and cached-target identities from the frozen metadata. These are metadata/traces, not a new voxel audit.

The actual cohort policy was **671 positive / 662 empty**, not the errata-corrected **664 / 669**; all1,333 members are retained in either policy. No overlay binding appears in input, plan or cache-manifest metadata. A broad marker scan found only the ready receipt pin for the unrelated MLflow tracking-correction test; it is not an annotation correction. The external partial Mac overlay was not bound by this STU-Net input receipt.

Compared against the retained origin/main versions of pants_errata_v1.py, MAC-KD-UPSTREAM-ERRATA-20261023.md and MAC-KD-ERRATA-CORRECTION-20261023.md; exact Git revision and document hashes are in the JSON. The documented policy retains the CT and original pancreas, replaces only the seven whitelisted lesion masks with zeros, regenerates sampling/cache metadata and explicitly binds the overlay. Simply changing class2 to background is not equivalent because legitimate pancreas voxels may have been overwritten. This review uses retained upstream-review documentation, not a fresh publisher verification.

## Implication for the next decision

Correction-first preparation should precede a longer-run launch. The preceding longer-schedule review remains historical analysis of the actual run; its duration proposal must now account for this label-policy difference. Prepare a separate versioned seven-case correction and sampling/input binding, reuse unaffected evidence appropriately, and qualify actual batches and restore behavior before requesting a new scientific launch. Do not repair or silently repin the completed run.

A warm restart from its checkpoint retains the history of incorrect-label exposure; correcting subsequent labels does not erase that history. A fresh corrected run provides a cleaner label-policy baseline. Changing both labels and duration would confound attribution to duration. These are planning implications, not authorization to execute either route.

The seven are absent from the70-case development set, so do not rewrite reported development Dice or claim a corrected score without a new model comparison. There is no evidence here quantifying the effect on .371633 Dice, small-lesion misses or empty-case alarms. Full-model/reference comparisons with Mac KD still require arm-bound matching and disclosure of the training label-policy difference. CAP-EXP-020 remains proposed only.

Verification: all seven metadata hashes/counts and source dictionaries matched; actual journal visit counts equal final exposure records; no affected development members; input/plan/cache identity binding checked. No training, inference, cache repair, pin edits, schedule or monitor changes.
