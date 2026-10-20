# CP05: retained lesion error and preprocessing audit

Continue under Quinton's October20 request. Diagnose fixed cases927 (missed lesion),514/698
(annotation-empty false positives) using existing raw and unchanged CP01 predictions. No new
model forward, checkpoint load, training, calibration sweep, protected arrays or UI promotion.

Before analysis, freeze these questions:
1. Of reference lesion voxels, how many are assigned background, pancreas or lesion? What fraction
   of false-positive lesion lies inside the provided pancreas? Report exact3x3 confusion counts,
   lesion components and physical volumes; retain empty recall as undefined.
2. Do source-handoff label decoding and lesion-priority mapping agree with CP04's explicit binary
   interpretation? Compare the whole927 reference byte-for-byte after source decoding.
3. Do local geometry, orientation, tiles, interpolation, blending and restoration helper ASTs match
   the pinned source functions? Check the ROI and normalization paths against received source;
   run a bounded independent artificial-ramp comparison including axis flips/permutations and
   coarse spacing. This is numerical preprocessing evidence, not CUDA/MPS model equivalence.
4. On927, does the source ROI match the retained job, and are missed lesions spatially within the
   provided region? Inspect a native CT slice at the reference lesion's largest-area plane with
   reference lesion, reference pancreas, predicted pancreas and predicted lesion clearly separated.
   Use pre-existing698 review; no broad or selected-best-case search.

Verify source bundle member hashes and original/package/candidate/derived annotation bindings.
Never import the training package or instantiate a session; source inspection or selected pure
functions only. Code used for diagnostics must be pinned. Synthetic confusion tests precede actual
arrays. No claim of matching the latest remote checkout; the audit targets the received producing
handoff and the fixed step6000 implementation.

Limits: the same32M-voxel/64MiB compressed/128MiB decoded input limits; integer/chunked label
handling avoids full scaled float64 arrays. Only three selected cases; source hashes/metadata
and existing metrics for other cases. Analysis600s/8GiB per child,30minutes total,512MiB external
artifact growth,100GiB internal free floor. Use installed Pillow for native review figures.

Complete with exact error decomposition, source match/difference evidence, bounded checks,
uncertainties and the smallest justified next experiment. Do not alter thresholds or assume model
failure if producer/device parity is still unverified. Preserve all old attempts; update Trello,
weekly specification, handoff and coherent commits.
