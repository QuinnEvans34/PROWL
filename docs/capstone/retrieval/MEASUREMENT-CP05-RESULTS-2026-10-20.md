# CP05: retained class confusion and source audit

## Outcome

The local audit did not demonstrate a preprocessing or class-mapping mismatch with the received
producer source. The retained errors are principally **pancreas-versus-lesion discrimination**:
case927 assigns98.53% of missed lesion voxels to pancreas, while514/698 assign some provided
pancreas voxels to lesion despite empty lesion references. Component removal or a provided-pancreas
restriction cannot correct both directions. No threshold or segmentation change was made.

This finding does not prove CUDA/MPS model-output equivalence or identify the training cause.
The next discriminating check is the original producer's already-saved raw step6000 case metrics,
using the same checkpoint, split and class definitions. A concrete metadata-only request is
[prepared](MEASUREMENT-PRODUCER-COMPARISON-REQUEST-2026-10-20.md); explicit cross-chat authorization
has been requested and is pending. No extra inference is needed to read that report.

## Fixed retained-case decomposition

Rows are original raw predictions. Counts are voxels; provided pancreas is a reference/assistance
mask, not independent clinical truth. Empty annotations do not establish healthy patients.

| Case | Reference lesion | True lesion hits | Missed as pancreas | Missed as background | False lesion inside provided pancreas | False lesion outside provided pancreas |
|---|---:|---:|---:|---:|---:|---:|
| 927 | 11,301 | 668 | 10,477 | 156 | 491 | 328 |
| 514 | 0 | 0 | 0 | 0 | 1,265 | 958 |
| 698 | 0 | 0 | 0 | 0 | 3,192 | 7,931 |

Case927 contains one26-connected reference lesion, bounding indices[264,102,85] to[297,132,109]
(exclusive upper bound). Of10,633 missed voxels,10,477 are predicted as pancreas. CP04 already
verified all reference lesion voxels lie within the inference region. The unchanged component
candidate leaves all lesion counts identical on this case. It cannot recover missed tissue.

After the existing component selection,514 retains1,265 inside-reference and183 outside-reference
false lesion voxels;698 retains3,192 inside-reference and4,625 outside-reference false lesion
voxels. Simply restricting output to the provided pancreas would leave these inside-reference
errors and could discard actual lesion beyond the pancreas annotation. No such filter was run.
Recall for empty lesion references remains null.

Manually reviewed the native CT plane with greatest reference-lesion area on927 (first argmax,
z94,734 reference-lesion voxels). The reference-lesion outline is largely inside the predicted
pancreas label, while the predicted-lesion outlines cover little of it. The selection rule was
fixed before rendering; this was not a search for a visually favorable example. The PNG remains
private. This is an engineering contour review, not an anatomical/diagnostic certification.

## Source and preprocessing checks

All36 files in the received October20 source-only bundle match its SHA256 manifest. This audit
compares that preserved handoff, not an assumed latest remote checkout. The checkpoint was not
loaded and no training module, session, optimizer or real model was instantiated.

| Check | Evidence and result | Limit |
|---|---|---|
| Class semantics | Source target assigns pancreas1, then lesion2 with priority; native scoring uses the same lesion-priority target. UI extent1+2 remains intentionally distinct from class1 parenchyma. | Does not establish anatomical annotation accuracy. |
| Binary decoding | Executed only the source's pure `target_content`/binary-decoder functions. Whole decoded original lesion arrays match local references exactly on927/514/698.927 has11,301 foreground voxels, matching CP04's exact-encoding adapter. | Source uses its explicit semantic1e-6 policy; the app adapter remains the narrower canonical-encoding rule. No production policy change. |
| Architecture declaration | Source SegResNet architecture dictionary equals local declaration:3classes,16filters,GroupNorm8,down1/2/2/4,up1/1/1. | Source/loader review, not newly checked model activations or checkpoint state. |
| Geometry and reconstruction |11 helper functions/classes have identical Python ASTs: geometry, orientation, starts, tiles, extraction, blending, physical geometry, coordinates, sampling, native destination and reconstruction. Used policy values agree. | Not a proof of entire runtime/dependency/device equivalence. |
| Normalization | Source float32 image orientation, clip[-100,250], +100, /350 agree. UI CT window[-100,300] is a display setting, not the model input normalization. | Three artificial ramp inputs, not every possible input. |
| Synthetic pipeline comparison | Source pure ROI/crop/numerical functions and local pipeline yield identical7 sampled windows and restored labels across3 artificial cases:anisotropic/coarse spacing, permutation/flip/shear, identity. | Small windows16/stride8 with a deterministic artificial probability callback; no learned model or CUDA/MPS parity claim. |
| Actual ROI selection | Source and app source-box functions exactly match the retained inference boxes on927/514/698. | A matching ROI does not guarantee whole-organ source coverage. |
| Class decision | Both implementations use class softmax, positive weighted probability reconstruction and lower-index argmax tie handling. | Saved packages contain argmax labels, not probability maps; no confidence/threshold conclusion follows. |

The source decoding includes all original foreground positions; the annotation representation
repair did not manufacture a new missed-lesion problem. No evidence from this block supports
changing image orientation, normalization, class labels or the component threshold.

## Verification and provenance

The [plan](MEASUREMENT-CP05-PLAN-2026-10-20.md) and portable error-review helper were committed in
9de0e26 before real analysis. Six new synthetic tests verify lesion priority, class decomposition,
empty-reference semantics and invalid grid/label/geometry rejection. Three additional independent
source-vs-local numerical comparisons pass (seven total artificial windows). All six raw/candidate
error rows reconcile against retained TP/FP/FN and class totals. Original source, package and
candidate hashes checked; no writes to prior outputs.

One bounded analysis/render child exited0 in3.87s; sampled process-group RSS983,187,456B (~0.92GiB),
reaped. Zero model calls or weight loads. New artifacts remain below512MiB on PROWL-Data; internal
free-space floor100GiB preserved. No training, protected arrays or live UI/service changes.

Private evidence: `/Volumes/PROWL-Data/PROWL/artifacts/measurement-cp05-20261020/` contains source
manifest/AST/synthetic results, per-case errors/decoding/source bindings, reviewed927 PNG and
arithmetic/source-architecture review. Pinned orchestration and execution receipt are in
`outputs/prowl/measurement-cp05-20261020/`. The source-bundle functions were extracted as explicit
pure AST definitions; the training package was never imported.

## Next decision

Compare saved original raw step6000 counts for these exact three cases before deciding that the
Mac adapter, checkpoint or class confidence needs a change. If counts differ materially, isolate
producer/device/configuration differences before tuning. If they agree, the next bounded model
experiment should evaluate missed lesions and empty-reference false positives together, with
probability evidence if available. A stronger rejection threshold might suppress false positives
while worsening927's miss; neither direction is justified from hard labels alone.

Keep current UI coverage/measurement guards. AI-05 remains In Progress; no reliable measurement
release, formal evaluation acceptance or new training authority follows from this audit.
