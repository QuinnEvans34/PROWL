# Phase C bounded preprocessing verification

Recorded before execution, September 28, under Quinton's explicit loader/preprocessing request (D-270).
Consume only the frozen `cohort:pants-localizer-smoke-0001:v1`: cases 3/26, four original CT/pancreas
files, 23,331,170 compressed bytes. No additional candidates, lesion masks or test payloads.

Use the reviewed cohort completion and S3/manifest pins in the read capability. Verify the registered
volume and source binding; no arbitrary paths/ID lists or global source activation. Recheck original
stat identity and exact bytes before decoding, geometry against the qualified descriptor, explicit CT
mm units, the retained paired-grid mask-unit interpretation, finite CT and D-259 binary target values.

Recipe v1: RAS, 3 mm spacing, trilinear CT / nearest target, HU [-100,300] to [0,1], symmetric zero
padding to at least 96³. HU clipping/scaling precedes resampling, so interpolation padding is zero
in normalized intensity space rather than 0 HU. No crop, reference ROI, augmentation, persistent cache or workers. Train and
inference use the same image transform; inference receives no mask. Recipe is an engineering smoke
starting point, not a frozen training hyperparameter or an annotation-quality filter.

Pass/fail: supported evidence/root/bytes/grid; one finite image channel in [0,1]; same-grid binary
nonempty target; exact train/inference image equality; restoration to original source shape/affine;
finite restored values and binary nearest-restored target; no gross displacement in three-plane
engineering contact sheets. If a positive target disappears, stop and review the recipe, not the
case's qualification. Report source/processed/restored foreground counts and round-trip Dice as
resampling diagnostics; do not use them as model performance or expert contour-acceptance claims.
Synthetic axis-permutation/reflection landmarks must restore exactly; anisotropic/oblique fixtures,
probability interpolation, missing/held/changed inputs and unsupported cache/crop behavior are tested.

Budgets: CPU only, two Torch threads, sequential cases, zero data-loader workers; 600 seconds including
cohort replay; supervised worker RSS ceiling 4 GiB checked every 0.25 seconds (polling is not an
instantaneous allocation hard limit). Parent is a small stdlib supervisor. At most 32 MiB compressed
and 256 MiB expanded per source file; 20 million source / 8 million output voxels per case. Total
source read scope is four files, at most 64 MiB. Save reports and four contact sheets only, at most
64 MiB, in a new ignored local diagnostic directory; preserve failures. Maintain 100 GiB internal
free space. No arrays written back, no model/accelerator work, no public images or training launch.

A completion receipt requires successful worker exit, verified saved hashes, source/target checks and
recorded supervisor outcome. Visual assessment follows as a separate reviewer judgment; file generation
alone is not visual acceptance. The historical transforms and D-259 implementation bytes stay unchanged.
