# D-321 — shared segmenter geometry and loader qualification

**Complete:** the new role-safe triple loader and shared physical forward/inverse mapper passed synthetic tests and a fresh read-only qualification on every frozen member. All seven passed the preregistered recipe screens; all14 native/nearest-round-trip sheets were reviewed. Accept this exact recipe for the provided-pancreas-ROI engineering subset. No model was executed, training launched, case removed, negative inferred or source setting activated.

Authority: Quinton's “Great, continue to the next.” and standing autonomy, recorded before source reads in [D-321 plan](SEGMENTER-GEOMETRY-QUALIFICATION-PLAN-2026-10-01.md). [Exact attempt02 request](SEGMENTER-GEOMETRY-EXACT-REQUEST-attempt02-2026-10-01.md) was issued before consumption. [Next learning/recovery packet](SEGMENTER-LEARNING-RECOVERY-PACKET-2026-10-01.md).

## Implementation and scientific scope

New `src/data/segmenter_geometry_v1.py` and `src/data/segmenter_geometry_loader_v1.py`, diagnostic runner and three test modules. Registered D-320 inputs are fully rederived before source access; bare manifests/descriptors cannot authorize reads. Explicit optimizer/evaluator role, exact purpose/target state, exact triple observations/hash/grid and scoped capability are checked. Entire triple read ceilings are reserved before opening. Source symlinks/traversal/nonregular files, changed identities/geometry, missing targets and held/wrong-role cases are refused. Existing bounded hash/gzip CRC/header/expanded-payload parser and approved semantic binary decoding are reused without changing their producing code.

Mapper: source→RAS→pancreas-only10mm ROI→1mm physical sampling→uniform aspect-preserving scale→144³ deterministic symmetric pad. Zero jitter, HU[-100,250], linear image/continuous probability interpolation and nearest target/component interpolation. Integer-center/half-open-edge, ceil-cover and odd-padding conventions are explicit. Supports signed-permutation axis-aligned grids; oblique/shear is explicitly refused. Native class2 lesion overrides class1 pancreas; no lesion clipping to the pancreas mask and no lesion-driven box repair. Portable records bind source/ROI/all grids, spacing, physical extents, scale/pad, recipe and inverse. Independent pinned transform validation rederives every field.

Continuous probabilities are restored before source argmax; outside ROI is background[1,0,0]. The real continuous probe uses one-hot **reference** tensors, with no network. Its recall is a geometry result, not model performance. Separate nearest-label/component round trips preserve all source components and loss counts. All seven real lesions have one connected component; multi-component behavior is synthetic evidence only. Native arrays/tensors were discarded after each case; no retained training cache or prediction masks were published.

## Native fidelity and review

Preregistered minimums: nearest native lesion and each component recall0.90, union recall0.95, every component surviving without displacement, analytic landmark error≤1e-5mm, exact native probability grid and normalized sums. The one-hot reference continuous-inverse native argmax also requires lesion recall0.90. All7/7pass, with no threshold changes after seeing results.

|Case / role|Native lesion voxels|Tensor lesion voxels|Nearest native lesion Dice|Nearest lesion/component recall|Nearest union recall|Continuous-reference argmax lesion recall|Acquired-grid ROI fraction|Effective tensor spacing mm|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|3 train|1,055|5,337|0.9760|0.9848|0.9870|0.9839|4.174%|1.000|
|26 train|7,244|14,143|0.9712|0.9678|0.9773|0.9765|3.901%|1.007|
|2232 train|3,867|5,822|0.9810|0.9772|0.9866|0.9648|5.213%|1.028|
|2973 train|124|399|0.9354|0.9919|0.9711|0.9516|4.228%|1.153|
|5821 train|3,399|5,053|0.9789|0.9694|0.9888|0.9612|1.902%|1.049|
|6238 train|7,412|6,097|0.9627|0.9683|0.9797|0.9663|5.716%|0.910|
|2514 validation|1,880|4,012|0.9899|0.9920|0.9962|0.9787|5.606%|1.000|

Every native lesion voxel is inside its fixed pancreas-derived ROI. No components lost/displaced. Max landmark error5.684e-14mm. The144³ tensor is not uniformly1mm across cases: physical scale yields0.910–1.153mm effective spacing. Native round trips are not exact: retain their changed counts/borders. Case2973 remains a124-voxel one7.5mm-slice target;123native voxels are retained nearest,118through continuous-reference argmax. No new native resolution is inferred from interpolating that thick slice.

All14 sheets inspected on selected axial/coronal/sagittal source planes; no unshown components, gross orientation/crop-frame shift or vanished lesion. Nearest quantization is visible. Case6238'snativeZ=0/source-boundary context remains, including1,603lesion voxels outside pancreas. Outside-mask lesion counts431/54/3/147for26/2232/2973/5821 remain unclipped. Plane selection can differ slightly between native and restored masks; direct integer/native metrics and independent physical landmarks establish the mapping. This is technical selected-plane review, not exhaustive all-slice or expert annotation certification.

One positive validation/no verified negatives supports engineering only, not generalization, false-positive performance or autonomous cascade acceptance. The registered6/1/all12/fiveholds and original7200/1800/901 membership are unchanged. Four unknown empties remain held,5641'sannotation relationship remains unresolved and unread. Old153localizer members/23holds and176candidates remain fixed.

## Resource, attempts and evidence

75new tests / **2,062native passes**, two existing upstream torch.jit deprecation warnings,72.04s. Targeted75pass in0.29s. Coverage includes independent coordinate/world-ramp oracles, deliberate axis/crop-offset/stale-transform faults, anisotropy/ceil/oddpad/six faces, lesion-invariant ROI, sparse/multiple/outside-mask/negative fixtures, loader-before-open refusals, source substitution and bounded failure accounting. Old producing source/schema and roots pins remain unchanged.

Fresh metadata replay156.530s/0.964GiB RSS. Eleven invented native-projection/worst-size fixtures:13.973s/4.567GiB RSS; supervisor14.241s. Tiny/fragmented/boundary adversarial fixtures can lose foreground, and those losses remain recorded; profile resource success does not grant their invented cases real qualifications or establish scientific fidelity. Dense/boundary synthetic sheets reviewed separately. Largest consumed native40,547,328voxels and intermediate2,173,770voxels fit the envelope.

Exact real request consumed once:21files,145,701,969compressed hash bytes,145,701,969compressed decode bytes,544,986,944expanded bytes. Fresh registered replay is included in183.580s worker time; supervisor183.849s,4,480,679,936B/4.173GiB RSS. Limits1,800s/8GiB/64MiB;33covered output members,8,978,634B includingreceipt. Native references reused from the same arrays; no additional source pass. Source mount identities and runtime/code pins stable. No model/GPU/optimizer or eligibility changes.

The original producer printed a canonical JSON hash while storing compact JSON. Two launch invocations were rejected before consumption/source reads (one manually wrong pin, one producer's canonical pin). Corrected producer and reader now use persisted bytes, covered by a regression test. Old unconsumed request and both failures are retained. Fresh attempt02 scope/profile/request were reissued under corrected code; no consumed request was retried.

|Evidence|Persisted SHA-256|
|---|---|
|Fresh scope receipt|`0161966208296a3342f55f1683566c98c103cc17b88f0d1a015f8c65655ab47f`|
|Fresh synthetic profile receipt|`5cdef929038946ae6fded20e041ae94bc21c1ac5ad32dec285d7a23518ee46fb`|
|Exact consumed request|`07d3bb4f8e49220a721b5d79efb66595f0f22350ca1a1f75c25c9d34195cc476`|
|Complete real evidence receipt|`5c958ac1877c52c2eefd55e3cfe0824428322ca72dbd12ad52043c02e1d8fe1f`|
|Diagnostic recipe hash|`2382855d8414a5d52a9f80813eb00093835adc3cd21690fd787b58aa6017d488`|
|Acceptance record|`b3ff4db94b49f1ea9b44d57afd975c17f16309c9929df35fa3e0d9f7e67e7384`|
|All14-sheet review|`158aab94d348e9aad6c513131b7d5208604e2c9d6c64c09449e15b5ac76d2bec`|

Fresh runner verification passes without source-array reads. Independent saved-evidence script directly checks53members across scope/profile/run, file hashes and exact scope, old roots/code, retired request, physical edge/extent/scale/pad/landmarks, original native counts/components against D-318, integer Dice/recall and every gate. It imports neither mapper nor screen and reads no source arrays. Sealed review receipt `d0d94625e916040a7ba008d4cb4bb2a2b881f5bbf5b143218a22b7779e83c042`:35covered members/451,678B, including all attempts, final tests/profile/run/verification logs, code/prospective request snapshots, visual/acceptance records and next packet. Direct sealed-review/acceptance/producing-code checks pass. No independent keeper copy is claimed for this geometry package.

## Following work

[Fresh segmenter learning/recovery packet](SEGMENTER-LEARNING-RECOVERY-PACKET-2026-10-01.md): independent three-class model/loss/optimizer/sampler and scratch lineage, CPU synthetic sparse/multiple/negative learning, actual MPS rehearsal, transactional save/reload/interruption and independent keeper recovery. Then a separately qualified real cache/zero-update model/export job with new reads, followed by a measured short exact smoke launch. No pending training request, automatic extension, formal baseline/jitter or localizer promotion.
