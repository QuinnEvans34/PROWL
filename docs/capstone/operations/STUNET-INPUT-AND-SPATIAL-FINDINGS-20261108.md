# Training inputs and spatial errors — November 8

Two actionable findings emerged: a prediction-only spatial rule improved the
original 12k development result, and an exact training-input replay demonstrated
lesion disappearance in the coarsest auxiliary targets. Neither finding changes
the running corrected continuation. All results remain exploratory and
exposed-development; pretraining/patient independence is unresolved.

## Saved predictions: spatial context helps more than confidence alone

The [complete component audit](STUNET-SPATIAL-ERROR-AUDIT-20261108.json) examines
the original completed 12k raw predictions on exactly 70 scans/36 positives/
34 empty references/45 lesion components. It reopens the already verified raw
mask representation and the same hash-bound lesion references. No CT, model,
inference, training, protected-test or new probability-volume reads occurred.
Reference masks identify errors for scoring; the deployable candidate uses
only predicted classes and the native affine.

The three rules were frozen before this audit's array reads: retain components
within 10mm of the predicted pancreas; retain components of at least 100mm³;
or require both. Connectivity is 26. Distance is the minimum world-coordinate
voxel-center distance between a lesion component and predicted pancreas,
including nonorthogonal affine geometry. A connected extension touching the
pancreas is retained as a whole. Removed components become background; existing
predicted pancreas is unchanged. Missing predicted pancreas fails open.

| Policy | Positive-case Dice | Recall | Small5 recall | Case hits | Component hits | Empty alarms | FP volume mL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | .371633 | .541016 | .464489 | 35/36 | 41/45 | 27/34 | 382.515 |
| Within 10mm | **.393887** | .541016 | .464489 | 35/36 | 41/45 | 26/34 | 259.280 |
| At least 100mm³ | .371361 | .540052 | .462518 | 34/36 | 38/45 | 24/34 | 380.262 |
| Both | .393529 | .540052 | .462518 | 34/36 | 38/45 | 21/34 | 257.817 |
| Oracle: delete every reference-disjoint component | .455577 | .541016 | .464489 | 35/36 | 41/45 | 0/34 | 125.428 |

The 10mm rule gained .022254 Dice and removed 60,259 FP voxels/123.234mL
(32.22% of FP volume) with no TP loss on this set. Sixteen positive cases
improved, none worsened, twenty were unchanged. The descriptive case-bootstrap
interval for mean Dice difference is [.006974,.046571] (10,000 draws,
seed20261108); unresolved patient linkage prevents patient-independent
inference. It passes the reused eight utility checks on this set. This is a
new exploratory component screen, not a successful result for the earlier
confidence-threshold experiment or a hidden expansion of its threshold grid.

The spatial breakdown explains remaining limits:

| Predicted component group | Components | FP voxels | FP volume mL |
| --- | ---: | ---: | ---: |
| Overlaps reference lesion, within 10mm | 43 | 99,992 | 125.428 |
| Reference-disjoint, within 10mm | 116 | 124,611 | 133.852 |
| Reference-disjoint, farther than 10mm | 78 | 60,259 | 123.234 |

Whole-component filtering cannot remove excess tissue attached to a component
that also overlaps a true lesion. Even a perfect reference-informed component
verifier would reach only .455577 here, below the voxel FP-removal oracle
.648455. That oracle uses unavailable ground truth and is not a forecast.
A learned verifier might address nearby isolated components, but cannot by
itself fix attached boundaries or missed lesions. The size rule loses one case
and three component hits, so we should not treat small components as disposable.

`src/inference/component_proximity_filter_v1.py` implements the prediction-only
candidate without reference inputs. It is not wired into the app or training.
CPU tests cover missing context, physical spacing, removal and preservation;
native mask parity checks include three no-removal cases plus one positive
and one empty case with actual removals. It needs a separately frozen check on
the corrected model and independent evaluation before promotion. Because the
source pipeline used supplied-pancreas regions, this is not an autonomous
full-CT performance claim even though the filter uses predicted pancreas.

## Exact six-input replay: coarsest labels lose small targets

Lenovo froze six already-observed training addresses before reading arrays:
two smallest eligible positive cases, a median and a largest positive case,
one ordinary empty and one corrected empty. All inputs, targets, augmentation
and saved traces matched exactly. One CPU core, CUDA unavailable/uninitialized,
60.985 supervised seconds, 1,485,688,832-byte peak RSS, exit0/reaped. The
[byte-identical export](../coordination/STUNET-SIX-INPUT-REPLAY-20261108.json)
binds selection, source hashes, diagnostics and resource evidence; its SHA256
is `f633ac6bf2f4b64fda295dce69eea9e814a3a58464c3a81e8190308ebf06c6b4`.

| Training case | Actual patch lesion voxels at 128³ → 64³ → 32³ → 16³ → 8³ |
| --- | --- |
| 6811, smallest | 140 → 20 → 4 → 1 → **0** |
| 3513, next smallest | 102 → 12 → 3 → 1 → **0** |
| 7105, median native-case volume | 2,974 → 338 → 34 → 2 → **0** |
| 2720, largest | 685,055 → 84,803 → 10,375 → 1,243 → 139 |

Identity-aware patch component tracking confirms disappearance, not merely
declining voxel counts. Paired augmentation preserved all full-resolution class
counts. This is coarse nearest-neighbor target aliasing, not demonstrated crop
loss: full-resolution labels survive. Four deliberately selected positives do
not estimate the cohort-wide rate. The coarsest loss carries only 1/31 (3.23%)
of the total auxiliary weighting, so this is a plausible, limited training
factor rather than a proven explanation for the entire Dice deficit.

Native-region HU statistics were conditioned on reference class. Of the four
positive samples, three had no lesion voxels outside [-100,250]; case7105 had
41/6,987 lesion voxels (0.587%) below -100 and none above250. This does not
support a widespread lesion-clipping problem in these examples. Expected
background clipping is much larger. Augmented/interpolated patch endpoints
were recorded for supported voxels and padding, but not conditioned on lesion
class; per-class patch quantiles were not captured. Do not confuse those two
measurements or infer that every data source/pretraining normalizer is correct.

The saved-prefix audit covers 1,983 new updates and all 1,333 training cases:
734 patches (37.01%) contain lesion voxels, 266 positive-source patches do not,
and the sampled voxel mix is 95.45% background/4.21% pancreas/.342% lesion.
All seven corrected cases were visited. Coverage/context sequencing matches the
frozen plan; component jitter starts at global15971. These are repeated patch
exposures, not independent cases or a sampling bug. All four periodic saved
scientific diagnostics were empty patches, which explains why saved logs alone
could not establish small-target survival.

## One proposed training factor; current continuation stays fixed

Prepare a controlled **coarsest-supervision ablation**, comparing current weights
[16,8,4,2,1]/31 against [16,8,4,2,0]/30. The full-resolution target, nearest
reduction, CE/Dice formula, architecture and all five outputs remain. Keep a
zero-weight graph connection to the coarsest head so its gradient is zero,
not absent. `src/training/stunet_supervision_candidate_v1.py` is an isolated
CPU-tested candidate, not a live trainer or launch receipt. Its baseline loss
and all five logit gradients match the exact pinned original implementation.

For a future scientific arm, reuse the same completed-original12k parent
weights/optimizer/RNG, corrected664/669 training membership, frozen input
addresses/seed/augmentation, continuation LR schedule, 12k additional updates,
six full70 validations and existing checkpoint selection. The already-running
corrected continuation is the intended control; audit exact ancestry and
evaluation binding again before use. Keep raw postprocessing in both training
arms so the loss factor is not mixed with the proximity filter. Compare selected
and terminal Dice, recall, component identities, small-case recall and FP burden;
no gain is assumed. Do not change normalization or sampling in that same arm.

Actual CUDA updates, gradient/state checks, independent checkpoint backup/cold
restore, resource/storage/runtime admission, a frozen receipt and explicit
scientific launch authority remain required. No new training was launched and
no active source pin was edited. The proximity rule is a separate inference
candidate and must be reported separately from any learning gain.

At **2:31 p.m. Mountain**, the current corrected run had completed 2,000 new
updates/global14000 and was validating: 7/70 cases,332/3963 tiles. There was no
completed full70 report, so no new corrected Dice/recall/FP result is claimed.
MLflow/workers/dashboard remained healthy. Existing hourly checks continue;
the first complete report and later series remain pending evidence.

## Engineering and preserved attempts

The Mac audit completed70 cases in67.359s, peak ownedRSS3,218,964,480B, exit0,
workersreaped. Six frozen audit pins and75 independent report-backup pairs match.
The first preflight omitted an already-installed isolated dependency path and
failed before any worker/array read. Its request/source/failure remain intact;
additivev2 uses that directory, with no package or producing-source edits.
This is a new user-authorized CPU analysis, not a reset/retry of the completed
four-hour inference experiment.

Twelve focused synthetic CPU tests pass. Actual saved-mask parity and exact
baseline-loss/gradient checks are recorded in
[candidate checks](STUNET-AUDIT-CANDIDATE-CHECKS-20261108.json). These establish
engineering behavior, not CUDA training readiness or clinical effectiveness.
Peer saved-log and six-input exports are imported byte-for-byte from commits
35b9530 and76c6ebf, not merged into the producing runtime. No new MLflow run,
schedule, policy deployment or GPU inference was created for this work.
