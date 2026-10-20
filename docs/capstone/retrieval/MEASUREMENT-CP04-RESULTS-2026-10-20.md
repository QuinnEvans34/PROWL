# CP04: annotation resolved; source-boundary contact confirmed

## Decision

The requested retained-prediction investigation is complete. Case927 now has an explicit,
verified binary reference and a valid comparison. Case698's persistent contact belongs to the
main predicted component and also appears in the provided pancreas annotation at the CT's first
slice. Keep whole-organ measurements unavailable for this case. No new inference, training,
prediction cleanup, UI promotion or protected evaluation occurred.

The fixed subset now has **five scored of six selected**, with139 still excluded for size.
The unchanged component-selection candidate passes the original relative screen on2/5 scored
cases, but this does not establish acceptable absolute accuracy. In particular, newly scored927
has only5.91% lesion recall. AI-05 remains In Progress.

## Case927: exact representation, not a tolerance adjustment

The source stores only int8 endpoints -128 and127. Its slope and intercept equal the canonical
float32 representations of1/255 and128/255. Applying them produces exactly0 for background and
1.0000000591389835 for foreground. The prior strict0/1 check rejected the latter correctly.
This is consistent with a full-range scaled binary encoding; the original producing writer has
not been identified. It is not evidence of a probabilistic annotation.

The [frozen CP04 plan](MEASUREMENT-CP04-PLAN-2026-10-20.md) and implementation were committed in
1fe91c6 before derivation/scoring. The opt-in decoder requires the exact integer dtype, canonical
scaling, endpoint-only codes, source hashes and CT geometry/units. It rejects intermediate codes
and different scaling rather than rounding near-one values or applying a nonzero threshold.
A new uint8 annotation with identity scaling preserves all11,301 foreground positions, the affine,
and the original/unit-qualified source chain. No original header or voxel file was changed.
Eleven synthetic checks pass, including export preservation and invalid encoding/hash/grid refusal.
Production inference and the strict component comparison remain unchanged.

One comparison of the retained prediction and unchanged largest-union candidate succeeds:

| Target | Reference mL | Raw → candidate mL | Raw → candidate Dice | Candidate absolute error mL |
|---|---:|---:|---:|---:|
| Pancreas extent | 70.474 | 94.494 → 93.658 | 0.83813 → 0.84240 | 23.184 |
| Pancreas parenchyma | 62.870 | 93.494 → 92.657 | 0.78410 → 0.78832 | 29.788 |
| Lesion | 7.605 | 1.001 → 1.001 | 0.10447 → 0.10447 | 6.604 |

Lesion counts are668TP,819FP and10,633FN: recall0.05911 and precision0.44923. All11,301 reference
lesion voxels lie inside the retained inference region; exclusion by that region does not explain
this miss. Other preprocessing/model causes are not isolated by this check. Removing detached
components cannot recover these missed voxels. All original relative screen rules pass because
cleanup improves some false positives without making any checked metric worse; that relative
result must never be presented as reliable-size acceptance.

Updated positive stratum,3/3 scored: mean lesion Dice0.29788→0.41755, unchanged mean recall0.65756,
mean absolute lesion-volume error8.819→5.402mL. Annotation-empty stratum remains2/3 scored with
mean false-positive lesion volume8.737→5.868mL and undefined recall. Case139 remains excluded;
no replacement, retrospective CP03 pass or inflated six-case success denominator.

## Case698: main component meets the available CT boundary

The retained inference region is [45,18,0] to [479,285,99] (upper coordinates exclusive).
The remaining contact is native axis2 low, slice0: this crop face coincides with the CT boundary.
There is no remaining candidate contact at an internal crop face or another CT face.

| Slice0 quantity | Raw prediction | Existing candidate | Provided pancreas reference |
|---|---:|---:|---:|
| Foreground on the CT face | 1,712 | 1,440 | 2,280 |
| Predicted contact overlapping reference | 991 | 991 | — |
| Predicted contact outside reference | 721 | 449 | — |
| Reference face voxels missed | 1,289 | 1,289 | — |
| Lesion-label contact | 0 | 0 | — |

Both6- and26-connectivity identify the same105,667-voxel main predicted component, including
all1,440 surviving contact voxels. The reference is one101,922-voxel component, with2,280 voxels
at the same face. Removing the candidate's remaining contact would discard991 voxels supported
by the provided annotation. This is not the detached-fragment mechanism seen in case29.

Candidate/reference foreground counts inward from that face:

| Native slice | Candidate union | Reference | Overlap |
|---|---:|---:|---:|
| 0 | 1,440 | 2,280 | 991 |
| 1 | 1,544 | 2,280 | 1,031 |
| 2 | 1,639 | 2,280 | 1,048 |
| 3 | 1,740 | 2,156 | 1,275 |

Reviewed the native CT overlays at slices0/1/3 and orthogonal context at indices275/152/17.
The contours agree with the numerical finding: annotation and candidate extend to the available
source edge, with both missed-reference and extra-prediction regions. CT slices0/1/2 are different
(151,160 and151,232 pixels change between consecutive slices), while those reference planes are
identical; the repeated reference counts do not arise from identical leading CT planes. The reason
for repeated annotation planes is unproven. This engineering review does not certify anatomy or
claim that the reference is independent truth: that pancreas mask also supplied the inference ROI.

The available CT does not establish whole-pancreas coverage. It is not appropriate to fix this
by clipping edge voxels or expanding an internal crop beyond the available source. Whether source
acquisition, dataset preparation or annotation history caused the limited extent remains unresolved.
Retain the honest coverage refusal for total-organ size.

## Verification and retained evidence

18 new synthetic checks pass:11 encoding/export checks and7 face/overlap checks. Verified all6
new target/variant arithmetic rows,96 face/inward-plane rows, foreground membership/export,
reference coverage and source/package/candidate hashes. Rendering uses native indices, physical
pixel aspect ratio, CT window -100 to300, and fixed reference/union/lesion legends. Two local PNGs
were inspected. Raw/derived masks and all images remain private on PROWL-Data.

The bounded numerical child completed derivation/scoring/boundary reports, then exited1 because
matplotlib was unavailable:15.01s,1,129,086,976B sampled peak RSS, reaped. That failure is retained.
A separate render-only Pillow script used already-installed dependencies and exited0; successful
numerical work was not rerun. The render-only process did not have a sampled RSS receipt, so the
numerical child's peak is not a resource measurement for the entire block. New artifacts are under
1MiB before final receipt additions; no model calls, training or UI service changes.

Private evidence:
- `/Volumes/PROWL-Data/PROWL/artifacts/measurement-cp04-20261020/`: source/producer bindings,
  explicit binary derivation receipt,927 comparison/components/ROI counts,698 face/component
  report, leading-plane diagnostic, two reviewed PNGs and updated summary/arithmetic review.
- `outputs/prowl/measurement-cp04-20261020/`: pinned analysis script, original execution/log
  including the unavailable-renderer failure, and separate render-only source.
- CP03's failed comparison and all old sources/predictions remain unchanged. Generic wording in
  the reused CP01 comparison identity is historical; CP04's source-binding and derivation receipts
  supply the verified current provenance.

## Next implementation decision

Keep the present measurement guard and do not promote component selection as an accuracy fix.
The next controlled model-quality investigation needs to preserve both lesion sensitivity and
false-positive control: case927 demonstrates major missed lesion tissue, while514/698 demonstrate
false-positive lesions in annotation-empty cases. Begin with a retained-output lesion error review
and the current model's preprocessing/label mapping before selecting a calibration or model change.
Separately carry source-boundary coverage status into any future measurement acceptance contract;
a correct count of visible mask voxels is not necessarily a whole-organ measurement.
