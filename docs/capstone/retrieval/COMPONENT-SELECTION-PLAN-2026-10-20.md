# CP01: development comparison of component selection

## Frozen scope and candidate

Quinton requested this comparison on October20. This packet is committed before opening the
development lesion annotation or running the comparison. Pancreas assistance and prediction
geometry/component outcomes have already been inspected; this is an exploratory development
screen, not a blind validation or an independent acceptance case.

Use the unchanged, retained step6000 prediction for the previously selected first-sorted exposed
development case only. Its prediction SHA-256 is
`75fcf8e07d9a8c2650ce842004ad160e4879912debfcd8df944c778416e2ca49`.
Keep the original package intact. Do not run inference, training or another case for this screen.

Candidate **largest-union-26-v1**:

1. Form foreground from predicted labels1+2; use26-neighbor connectivity in the native grid.
2. Retain the unique largest component by voxel count, preserving its original1/2 labels exactly.
3. Set other components to background in a separate derived candidate. Do not fill holes,
   smooth, dilate, relabel, or impose a distance/size cutoff. Equal-largest ties, empty foreground,
   or a largest component with no pancreas-label voxels make selection unavailable.
4. The selector receives only the prediction. Pancreas/lesion references and the provided
   assistance mask are evaluation inputs only, never selection inputs.

This candidate can delete real disconnected lesions or disconnected parts of the pancreas.
The comparison must explicitly detect that, rather than assuming largest means correct.

## Inputs, target semantics and exact arithmetic

Verify the original package files against their existing pins, and match the provided pancreas
to the admitted assistance hash. Discover the same development case's `pancreatic_lesion.nii.gz`
beside the pancreas annotation; record its bytes/hash before decoding. This local annotation's
identity is newly recorded, not independently matched to a Windows lesion hash. Require identical
native shape/affine within1e-5 absolute, explicit mm units, finite binary reference arrays and
the existing32M-voxel budget. Do not resample mismatched annotations to make them pass.

Report three separate targets, matching lesion-priority source target construction:

- Pancreas extent: prediction1+2 versus reference pancreas OR lesion.
- Pancreas parenchyma: prediction1 versus reference pancreas AND NOT lesion.
- Lesion: prediction2 versus reference lesion.

Also report reference overlap and lesion support outside the provided pancreas, so the
assistance-only comparison from the earlier audit is not confused with these target definitions.
Volume is voxel count × absolute native affine determinant /1000, in mL. Use exact integer
confusion counts; report Dice, precision, recall, signed/absolute volume error and relative error
when reference volume is nonzero. Undefined denominators are null, never invented zero or one.
For every26-connected reference lesion component, report original/candidate true-positive voxels,
coverage fraction and whether any overlap was lost. Any-overlap detection is not adequate size
agreement. Report each removed prediction component's reference pancreas/lesion overlap.

## Decision rules frozen before lesion review

This is a conservative **advance-to-broader-testing** screen; it cannot qualify release.
All of the following must hold:

- Candidate has no CT/crop-face contact and no foreground outside the recorded inference box.
- No correct labeled voxel is removed for any of the three targets (exact integer condition).
- No reference lesion component loses overlap or becomes undetected.
- Dice and absolute volume error do not worsen for any nonempty reference target
  (float comparison tolerance1e-12). For an empty reference, candidate false-positive count
  must not increase; keep the empty-reference status visible.
- At least one target has fewer false-positive voxels.

If any rule fails, retain the failed candidate and report the loss; do not revise connectivity,
keep extra components after seeing the annotation, or loosen limits in this attempt. Stop at
the failed screen and identify the next hypothesis. If all pass, label it eligible for a separately
frozen broader development comparison, still not a reliable measurement or clinical acceptance.
No automatic UI promotion in either outcome. A separate absolute-accuracy acceptance packet,
multiple exposed development cases and human outline review remain necessary.

## Verification and outputs

First test synthetic geometry, true disconnected lesions, diagonal connectivity, ties, missing
labels, empty references, exact count/volume arithmetic and immutable input behavior. Then run
one actual comparison. Retain a separate candidate NIfTI, JSON counts/per-component evidence,
file identities, rule decisions and readable results under a private output directory. No original
mask, model, UI measurement policy, source annotation or split membership changes. Commit code,
plan and a non-image results summary; update AI-05 and the weekly dashboard.
