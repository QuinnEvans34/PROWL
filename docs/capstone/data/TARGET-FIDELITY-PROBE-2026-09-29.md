# D-296 target-fidelity investigation

Quinton: “Great, continue and investigate.” Scope: explain D-295 tiny-reference loss without changing
membership, active recipes, source files or model weights. Fresh diagnostic request; never reuse D-295
consumed requests. Read only the qualified pancreas labels for training6110 and validation2727.
Exactly2files,46,320compressed bytes,10,503,092expanded bytes; no CT,lesion or publisher-test input.
Resolve the pinned D-294 bundle and D-295 descriptor/review first; enforce live storage mapping,
source identity/hash, exact byte bounds and <=6M source voxels per label. Preserve role identities.

First run synthetic regressions, including native-grid identity on a flipped affine and a boundary
reference, plus splat coordinate/metric checks. Then freeze code/environment, plan, recipe, capability
and retained source reports. Run once under600seconds/8GiB RSS/64MiB output/100GiB internal-free
supervision. Record a permanent attempt claim before raw reads; retain failure, no automatic retry.

Compare nearest-target3mm,2mm and native1.5mm. At3mm also compare mapping each source foreground center
to its nearest output voxel (foreground-center splat). This is neither conservative voxel-volume
occupancy nor a new approved target policy. Use a zero-valued CT surrogate solely to reuse the existing
geometry implementation. Never call this image-path or real-CT parity qualification. Reproduce D-295
nearest3mm Dice/recall exactly before interpreting alternatives. Record false positives/negatives,
precision,recall,Dice,volume ratio,source support by slice,affines and tensor sizes.

Any alternative remains diagnostic. A validation case has been exposed for preprocessing debugging;
this is development-validation, not a sealed test. Do not optimize thresholds or selectively choose
per-case recipes from these results. Keep native evaluation references and original membership.
Before training, choose/document a coherent target policy with broader tests; no launch in this job.
