# D-283 exact expanded input/preprocessing verification

Run one pinned, supervised read-only job for the frozen D-282 16 train/11 validation cohorts.
The user requested proceeding with the next loader/preprocessing step. No optimizer/model forward,
new candidate, lesion input, held case 6350, publisher-test payload, source rewrite or alias activation.

## Controls and budget

Freeze request, scoped capability, v2 recipe, complete producing-source snapshot, environment and
header-only geometry projections before reads. Re-resolve and replay the completed external cohort
bundle with independently retained completion/input/current-manifest pins before opening raw files.
The preparation may use retained staging metadata for projections but execution cannot substitute
that staging copy for the registered published artifact.

Read the exact 54 CT/pancreas files once, one case at a time, with explicit optimizer/evaluator roles.
Limits: 1 GiB cumulative compressed reads, 4 GiB cumulative expansion, 128 MiB compressed/512 MiB
expanded per file, 64 million source voxels, 8 million processed voxels, 16 GiB RSS, 1,200 seconds
including metadata replay, 256 MiB evidence, 100 GiB internal free floor. Two CPU threads, workers 0,
no cache. A separate parent process monitors time/RSS/output/free space and terminates its worker
on breach. Preserve incomplete attempts; no automatic retry or limit increase.

## Recipe and acceptance

Explicit v2 preserves the v1 transform recipe: RAS orientation, 3 mm spacing, HU [-100,300] to [0,1],
minimum 96-cube zero padding, trilinear CT/nearest-neighbor pancreas, no target-dependent image crop
or augmentation. The larger source limit and pre-allocation geometry projection are explicit v2
controls; old v1 implementation/configuration remains unchanged.

For every member verify exact compressed bytes and inventory identity, complete gzip CRC, native
same-grid CT/pancreas geometry, CT-declared mm with matched mask grid, finite single-channel images,
strict binary nonempty source and processed targets, and exact image equality with versus without
the target. Restore the transformed reference to source geometry and verify shape, affine, binary
values and nonempty foreground. Record foreground counts and round-trip Dice for every member.
Round-trip Dice measures resampling loss, not model accuracy. It is descriptive; values below 0.75
trigger closer review, not automatic source exclusion or a retroactively chosen pass threshold.
A disappearing target is a recipe failure and stays visible in the results.

Record load/transform/total times, observed peak memory and complete role/member accounting. Source
hash/stat/permission or budget failure stops the job with a retained incomplete record. Transform
failures are recorded per case and remaining cases may be inspected within the original budget;
there is no passing input-readiness claim if any frozen member failed.

Produce one three-row sheet per successful case: source reference and restored reference at the same
median foreground axial/coronal/sagittal planes, then processed reference at its own median planes.
Canonicalize source display axes without resampling; label panels clearly. Review all 27 sheets,
with particular attention to 4965/3717 coverage, 8037/8855 large noisy scans and any low round-trip Dice.
This is limited engineering transform review, not contour certification. Preserve all originals and
qualified difficulty observations. Only after this evidence passes should resource profiling and a
new scratch training plan follow; no training is part of this request.

## Recorded execution revision — display helper correction

The first request `c9b07b7666f61777013193a0d8fbc7e25efa6a6da1456a0ad875f3f6f48f90f8`
stopped after first-case processing while rendering its sheet: `nibabel.affines.voxel_sizes`
received a serialized list instead of a NumPy affine. Preserve incomplete package
`expanded-preprocessing-41bcb797-9a69-44e8-ba04-21da7f6c8c20`; 180.92 seconds, worker exit 1,
peak sampled RSS 1,848,770,560 bytes. No complete case report or full input-readiness claim.

Correct the display conversion and exercise the full three-row sheet on an invented flipped-axis
case before a new single-use request. Also make the already manually verified live-decoder/approved-
implementation hash comparison an explicit loader guard with a mutation test. Source cases, recipe,
geometry/permission rules and resource limits remain identical. Under D-283's authorized completion
scope, Codex selects one recorded corrected attempt after native verification, not an automatic retry
or enlarged budget. The earlier failed request remains consumed and must not be rerun.
