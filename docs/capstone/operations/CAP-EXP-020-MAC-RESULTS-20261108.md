# Mac STU-Net confidence-threshold results — November 8

All 70 fixed development cases completed. **None of the three confidence
thresholds improved positive-case Dice or passed the prospective utility rule.**
Retain raw argmax; no application setting, model weight or training recipe was
changed. This is a useful negative result for a global confidence cutoff on the
original completed 12k checkpoint, not evidence that false positives are harmless.

## Fixed comparison

The original trained 12k checkpoint, supplied-pancreas regions, native geometry,
128-cube/64-stride reconstruction and FP32 remained fixed. Each case had one
network inference pass; raw and .40/.50/.60 policies shared its probability field.
Only raw lesion winners could be removed. All 70 cases, including the successful
two-case native qualification, were retained: 36 reference-positive scans,
34 reference-empty scans and 45 reference lesion components. No optimizer
updates, protected-test reads, new model selection or threshold deployment.

| Policy | Positive36 macro Dice | Macro recall | Small5 recall | Detected positive cases | Detected components | Empty alarms | Total FP volume, mL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw argmax | .371633 | .541016 | .464489 | 35/36 | 41/45 | 27/34 | 382.515 |
| .40 | .371252 | .539551 | .464160 | 35/36 | 41/45 | 27/34 | 380.566 |
| .50 | .369335 | .527151 | .444756 | 35/36 | 41/45 | 27/34 | 361.439 |
| .60 | .371409 | .487631 | .401335 | 34/36 | 39/45 | 26/34 | 268.796 |

FP volume here sums all 70 scans. Headline Dice averages the same 36 positive
scans; removing alarms solely on empty scans does not raise that metric.
Small5 means five cases with total annotated lesion volume below 1mL, not a
component-size subgroup. Counts of any overlap are not clinically sufficient
detection criteria.

The .40 policy removed 1,917 FP voxels and 229 TP voxels. At .50 those counts
were 19,028 and 2,397. At .60 they were 87,682 and 10,037: FP volume fell 29.73%,
but recall fell 5.34 percentage points and Dice declined .000224. The .60 policy
lost the previous case hit on PanTS_00007868 and component hits on
PanTS_00007636/component2 and PanTS_00007868/component1. All candidates missed
the required +.02 Dice gain and reduced small-case recall; .50 also failed the
overall-recall guard, and .60 failed recall and identity-preserving detection
guards. Pancreas and false-alarm guards passed for every candidate.

## What this establishes

The 100-bin voxel-weighted ranking AUC among raw lesion winners was .721237.
Higher confidence therefore carried useful descriptive information about
reference overlap, but did not separate correct and incorrect tissue well
enough for these fixed global cutoffs to improve the defined outcome. This is
not calibrated disease probability or patient-level statistical independence.
It does not examine confidence on missed voxels outside the raw lesion class.

The earlier perfect-FP-removal Dice oracle (.648455) assumed ground-truth
knowledge. This experiment demonstrates why that oracle is not a threshold
forecast: confidence suppression also deletes correct lesion tissue. A global
cutoff cannot recover a missed raw lesion voxel. Do not expand the grid after
seeing these results and present that search as the same prospective experiment.

A later separately specified study could examine saved spatial errors and
component/context features or loss/sampling changes. This result does not
authorize another GPU run. The corrected-label Lenovo 12k-to-24k continuation
remains a separate experiment and was not interrupted or changed.

## Execution and verification

The screen's identity-aware supervisor completed in 6,131.492 seconds
(1h42m11s), exit0, with all workers reaped and no cleanup errors. Peak owned RSS
was 3,757,654,016 bytes; observed MPS driver peak was 6,463,586,304 bytes, under
the explicitly approved 8GiB limit. The original cumulative four-hour ceiling
was preserved. Earlier failed 6GiB attempts and the passing allocation-lifecycle
qualification remain unchanged. No old artifact or backup was deleted.

The [independent closeout receipt](CAP-EXP-020-MAC-CLOSEOUT-20261108.json) records
all producing pins, the rederived summary, reopened independent packed-mask
backups and all 280 decoded mask hashes, three SQLite integrity checks, stored
metric readbacks, checkpoint ancestry and released exclusive MPS lock. The
read-only verifier loads saved codes and metadata only; no CT, reference-mask,
model or inference replay is needed. Its initial reporting attempt encountered
the expected undefined Dice comparisons on empty-reference scans while
formatting a maximum; that failure is preserved, and the additive report repair
excludes undefined values without modifying production results or scores.

MLflow inference-policy run `89ddde292d9c47a9862a2f7f68332eea` is FINISHED.
Inference is excluded from training hours. Primary results and a consistent
tracking-database snapshot have independent internal-drive backups. The
completed one-shot launchd registration is removed after verification; its
configuration and logs remain preserved. The confidence monitor pauses after
this verified closeout; Lenovo's hourly training monitor is unchanged.

Source root:
`/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108/screen-03`.
Independent backups:
`/Users/quintonevans/PROWL-Backups/stunet-confidence-mac-20261108-03`.
Request SHA256:
`57fb08fed8f05d89021a889fb15355f764ed87a51b8cc4baf87cd6b504cb0ebc`.
Checkpoint SHA256:
`ed000e1ce25829c29f1efea7bf7a5f3684cddf43b0dbcdc5d9f47e8afc8bfa55`.

Unknown pretraining exposure and unresolved patient linkage remain. These are
exploratory exposed-development findings on a provided-region pipeline, not an
independent test, an autonomous full-CT benchmark or a clinical validation.
