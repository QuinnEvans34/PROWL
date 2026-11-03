# Four-case exploratory autonomous evaluation with explicit exception

Quinton approved the additive admission exception in the sibling JSON. The
original probability comparison remains FAILED and equivalence UNQUALIFIED.
No tolerance or old receipt changes. This exception admits only the fixed four
exposed-development cases, not training, independent acceptance or general backend
equivalence. Mac knowledge distillation is untouched.

Cases, in fixed order: PanTS_00002028, PanTS_00000909, PanTS_00004681,
PanTS_00006755. All are already selection-exposed development data; no replacements.

1. Restore those four CT files only from verified local training archives, checking
   exact original byte counts and SHA256. Separate CPU preparation ceiling4800s,
   2GiB RSS,256MiB restored CTs; no label/test extraction. Source drive and AC gates
   apply. Do not redispatch an existing restoration.
2. Bind model, CT, reference and metadata identities and runtime to a fresh request.
   Check native geometry and CT mm units. Existing repository policy permits
   unknown reference-mask units ONLY on the exact matching qualified-mm CT grid;
   record this explicitly as matched_mm_ct_grid, never infer CT units from masks.
3. Freeze full-source, runtime, exception, test and input hashes. Reuse the exact
   qualified physical executor/recipe. Run four autonomous cases first, then four
   separately labeled provided-pancreas-region cases, each in a fresh supervised
   process. The controller checks reference hashes; autonomous workers do not even
   read reference bytes for hashing. Their CT-only audit tripwire blocks label reads
   after strict model loading. Assisted workers load ONLY their pancreas reference,
   not lesion reference, before installing the same tripwire.
4. Score saved predictions afterward in separate CPU processes; no model forwards.
   Use existing saved_prediction_scoring definitions: lesion wins overlaps;
   pancreas parenchyma and pancreas/lesion union reported separately. Empty-reference
   Dice/recall are undefined, with prediction/false-positive volume instead.
5. Report26-connected reference components hit by ANY predicted lesion voxel and
   predicted components with ZERO reference overlap. This permissive descriptive
   detection is not voxel recall or clinical detection. Report physical contour
   distances (6-neighbor surface voxel centers, max directed95th percentiles and
   pooled symmetric mean) only on orthogonal native grids. Empty masks yield
   undefined distances; shear yields an explicit unsupported measurement. Component
   native bounds and volume are descriptive, not a clinical longest diameter.
6. Report localizer-mask containment, actual expanded-region pancreas/lesion
   containment and scan fraction separately from segmentation overlap. Cropping
   misses are scientific observations, not exclusions or geometry repairs. Retain
   all four cases in the denominator on any failure; stop on execution/integrity
   failure without retry or silently replacing cases.

Inference/scoring aggregate ceiling4800s; each subprocess at most600s. Same12GiB
owned RSS/6GiB reserved CUDA/8GiB outputs/8GiB independent backups/40GiB combined
C backups/100GiB free C and E floors. Localizer retains its tighter16M resampling
cap,96M source/region voxels,512tiles,144windows/72stride, float32/TF32disabled,
all-support localization. No new training/MLflow run or inflated training hours.

Evidence root E:/PROWL/readiness/week05-four-case-20261102-a01; independent backup
C:/Users/quinn/PROWL-Backups/week05-four-case-20261102-a01.
Restoration owned session93637. Initial51 CPU tests passed14.19s; final52 tests
passed11.61s after the explicit no-reference-hash worker adjustment. Historical
producing pins remain immutable. This document is setup, not a completion claim.

## Launch evidence

Restoration completed normally:1146.375s supervised,52,846,592B peak RSS, exit0,
workers reaped. All four exact CT byte/hash checks pass; all CT headers explicitly
declare mm and references match shapes/affines. Unknown reference header units
are explicitly bound to matching-mm CT grids under the existing policy.

Frozen request SHA256 f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd,
330 producing/input/runtime pins. Full-native maximum tile counts80/140/70/126
are within512. Owned48699/supervisor43452 dispatched once. First2028 autonomous
pass observed advancing at1/60windows. Completion/scoring/backups remain pending.

## Completed results and interpretation

Owned48699 exited0. All8 inference and8 separate scoring workers passed and were
reaped; supervisor43452 is absent and GPU has no compute owners. Final330pins match.
The summary independently verified95 existing output/receipt/backup pairs; summary
and closeout also have matching independent copies. Summary SHA256:
99ac2b4009e342daab4cd791dd4e16fb6f4fe6588bf040875539038f84d58ad2.
Evidence summary.json and closeout.json live under the evidence root above.

Evaluation controller reported832.062s (13.87min) before final backup; supervised
worker time749.454s. Longest worker78.297s, peak owned RSS3,231,510,528B and peak
reserved GPU1,021,313,024B. Free space at closeout:C167,657,574,400B and
E367,997,878,272B. All limits respected. No training hours added, no retry, no
additional cases or training, no Mac KD interruption.

| Case | Autonomous lesion Dice | Provided-region lesion Dice | Autonomous FP mL | Provided FP mL | Lesion components hit (both arms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| PanTS_00002028 |0.464840|0.309254|10.418882|20.143966|1/1|
| PanTS_00000909 |undefined: empty reference|undefined: empty reference|11.554000|1.105000|0/0|
| PanTS_00004681 |0.000000|0.000000|6.095071|1.700386|0/1|
| PanTS_00006755 |0.075096|0.108811|6.771811|5.280530|1/2|

Mean Dice over the SAME3 positive-reference cases:autonomous0.179978556,
provided0.139355084. The empty-reference case remains in the four-case denominator
for false-positive reporting; its Dice is not replaced by0 or1 and it is not called
clinically healthy. The per-case data do not support a consistent Dice improvement
from substituting the provided pancreas region. This is NOT a comparison against
the historical full-development Dice, which uses a different cohort.

Both arms preserve100% of all annotated pancreas and positive lesion fields on
these four cases. No reconstruction gaps. Autonomous expanded crops occupy
72.79%,74.15%,81.92%,67.16% of each CT, versus39.30%,24.67%,49.59%,26.88% for
provided regions. Autonomous tiles60/75/60/72 versus24/16/30/20 in the assisted arm.
Thus actual clipping does not explain the missed components here; broad regions
and differing window placement remain possible contributors, not proven causes.

Both arms overlap2/4 annotated lesion components under the explicit any-voxel
definition. Autonomous has35 zero-overlap predicted components; provided has13.
Fewer components do not imply uniformly lower false-positive volume:2028 worsens
with the provided region. Lesion voxel recall for2028/4681/6755 is respectively
0.900995/0/0.211380 autonomous and0.881555/0/0.255761 provided.

Pancreas+lesion union Dice (same case order):autonomous
0.810913/0.852504/0.626223/0.279202; provided
0.702563/0.922054/0.822582/0.299760. Separate parenchyma Dice is retained in scores.

Lesion Hausdorff95(mm) for2028/4681/6755:autonomous127.236/119.414/125.307;
provided131.351/114.513/63.802. Symmetric mean surface distance(mm):autonomous
23.008/83.116/40.960; provided49.433/44.658/13.562. These are distances across ALL
predicted lesion surfaces, including false-positive components, not a boundary-only
quality score for correctly matched lesions. Empty-reference distances remain
undefined. Native component bounds, volumes, surface metrics, localizer containment,
and each resource record are preserved; no clinical diameter is asserted.

No model-quality H0 was tested or accepted in this engineering/exploratory check.
The original cross-device probability comparison remains FAILED and UNQUALIFIED,
unchanged. The scoped exception was exercised once. Next actions require review;
no expanded cohort, parameter search, scientific training or backend acceptance
is implied by successful execution.
