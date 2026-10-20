# Native saved-package measurements — bounded development contract

Continue AI-05 under Quinton's October 20 instruction. Add an opt-in `saved-prediction-view-v2`
package, preserving v1 display and the separate prepared-mask preview. V2 binds the original CT,
prediction, result JSON and canonical inference-evidence JSON by byte count and SHA-256. The
manifest's model hashes must agree with the retained inference record; this is recorded model
identity, not an independent audit of checkpoint weights or training cohorts.

Validate CT/prediction native dimensions, affines and explicit millimeter units against both the
manifest and inference transforms. Verify study/CT/prediction identities, completed autonomous
status, no reference inputs, and supported autonomous-cascade-v1 / segmenter-predicted-roi-v2
metadata. Verify the native inference box is half-open and within the source shape. Nonzero labels
outside that box or touching its faces make a size answer unavailable, even if the native CT edges
are clear. Passing these checks still leaves anatomical completeness and segmentation accuracy
unverified; no average comparison or diagnosis follows.

Frozen before test execution: retain exact counts and 1e-9 relative analytic-volume tolerance;
geometry comparisons use absolute 1e-4 (package producer retains its tighter 1e-5). Native measurement
budget: at most 32 million voxels, 64 MiB per compressed CT/prediction, 128 MiB per decoded image,
1 MiB per JSON record. The existing prepared preview retains 16 million / 64 MiB decoded limits.
Read sequentially, cancel stale requests, and expose a measurement failure without calling a model.
No existing package or inference output is overwritten. No reference masks, training, new model
execution or protected evaluation. Reuse one explicitly documented exposed development package only.

Synthetic checks must cover hash swaps, source/model/geometry contradictions, missing result,
reference use, missing mm units, ROI truncation/outside support, v1 compatibility, stale reload and
normal volume arithmetic. Then package and inspect the already exposed October 12 example, retaining
all failures and limits. Do not claim full REQ-X01 acceptance from this implementation.
