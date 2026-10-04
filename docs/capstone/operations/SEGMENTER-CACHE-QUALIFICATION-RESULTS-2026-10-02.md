# D-323 — qualified segmenter input cache

The exact six-train/one-validation segmenter cache is published and independently resolved. All seven transforms, target-fidelity records and class counts match the accepted D-321 evidence. All seven cases in the cached input contact sheet were inspected. The native suite passes **2,215 tests**, including 68 new checks (two existing PyTorch warnings; 73.73 s). No model was run on these real inputs and no optimizer updates, cohort changes or global source activation occurred.

Authority: Quinton's “Great, continue on.” after D-322, within the [prospective D-323 plan](SEGMENTER-CACHE-QUALIFICATION-PLAN-2026-10-02.md) and cache portion of the [zero-update packet](SEGMENTER-ZERO-UPDATE-QUALIFICATION-PACKET-2026-10-01.md). Exact train: 3, 26, 2232, 2973, 5821, 6238; validation: 2514. All twelve candidates/five holds, original protected roles and old localizer 153/23 remain unchanged. D-319–322 producing code stays immutable.

## Cache contract and consumer

New files: `src/data/segmenter_cache_v1.py`, `src/operations/segmenter_cache_storage_v1.py`, `scripts/diagnostics/segmenter_cache_qualification.py`, `tests/test_segmenter_cache.py` and `tests/test_segmenter_cache_qualification.py`. The separate cache wrapper reuses unchanged registered cohort/descriptor resolution, read-only triple decoding and accepted physical geometry. It does not broaden D-321's consumed-stage loader.

Schema `segmenter-input-cache-1` stores float32 one-channel normalized image and uint8 three-class target per member, using non-pickle NPY. Binding protects purpose/role/cohort/descriptors, original content hashes and CT units, geometry acceptance/recipe/source transform, original fidelity/components and target class counts. Artifact publication is completion-last with exact member inventory and independent completion/derivation pins. NPY headers are checked for exact bounded shape/dtype/order before loading; object arrays, oversized headers, truncation and trailing bytes are refused.

Consumers require explicit case/role. Inference returns image/transform without target and does not decode the target on that access path; evaluation can return the target. Optimizer access is closed for every member in this readiness slice. Held/missing/wrong-role/stale members fail before array decode. Whole-cache validation checks target bytes and counts without granting optimizer permission.

Tests cover role/purpose/unknown-target denial, class/source/transform drift, forged production/request/runtime/read counts, array corruption/swaps/dtypes/shapes, unsafe NPY headers, completion-last failure, altered immutable artifact bytes, exact storage capability and metadata-refresh constraints. No failed case was replaced or transformed to improve its score.

## Preserved source-identity failure and fresh request

Attempt 1 consumed request `88568c2006b697155b735ac3504cac851b9e367733a9384a413b7beb3fcd650a` and stopped at the first CT's stat guard, before the file open/hash/decode. Zero original arrays were read; no cache artifact was published. Its zero-count reservation, request, worker failure, source snapshots and first test/profile evidence remain retained. The consumed request was not retried.

A bounded 21-path metadata-only job found only the volatile device number changed: **16777243 → 16777239**. All file sizes, inodes, mtime/ctime and modes remained exact; APFS volume UUID and source root stayed consistent. This supports a remount explanation, not a claim that metadata proves content integrity. Receipt `b05746226f9fbd632c55151824b4f3d90fb3d530208ec1daafbd73fb4e9d9ba1` preserves both observations. An initial inline stat probe omitted `expected_bytes` and stopped with `KeyError`; corrected scoped metadata job supplied the retained expected size. No contents were read by either metadata probe.

Only the new D-323 wrapper applies that pinned device refresh. It refuses every other observation/path/hash/inventory difference, preserves old producing code/evidence, and requires unchanged original content hashes during the fresh read. Nine additional regressions and the full native suite pass. Separate attempt-2 profile/request/build/replay directories preserve the failed first attempt.

Fresh request `d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364` completed once. All **21 original hashes matched**: 145,701,969 compressed hash bytes, the same compressed decode bytes, 544,986,944 expanded bytes. All seven real transforms and complete fidelity records equal their accepted predecessors. Source mount/root before/after and runtime/code pins remain stable. Both source requests are consumed.

## Resources and independent replay

|Stage|Worker seconds|Peak worker RSS|Evidence|
|---|---:|---:|---|
|Fresh largest-grid synthetic mapping/cache|1.209|1.875 GiB|40,547,328 native voxels; array replay exact|
|Real seven-case build and registered ancestry|193.053|3.413 GiB|Exact source budget; all seven cache pairs verified|
|Cold registered cache replay|156.701|0.986 GiB|No original arrays; all seven roles/counts/transforms exact|

Limits: serial/two threads, 1,800 s, 8 GiB RSS, 512 MiB artifact area including failed attempts/controls, 32 MiB local job evidence and 100 GiB free floor (artifact medium also keeps its stronger reserve). Supervisors cover native allocations; actual peak worker RSS is reported rather than treating sampled supervisor RSS as peak. First and second synthetic profiles are retained separately.

Invented largest-grid boundary/disconnected fidelity losses remain recorded: one component recall 0.25, total lesion recall 0.625. Resource/cache replay success does not qualify those invented targets or erase sampling loss. Real target fidelity remains the unchanged D-321 acceptance, not model accuracy. Seven serialization pairs occupy 104,511,232 B with NPY headers; real raw tensor payload is 104,509,440 B. Complete cache has **16 members / 104,576,736 B (99.732 MiB)**, excluding its small publication receipt/events.

|Case|Role|Tensor class 1|Tensor class 2|
|---|---|---:|---:|
|3|Train|69,216|5,337|
|26|Train|73,470|14,143|
|2232|Train|59,092|5,822|
|2973|Train|55,013|399|
|5821|Train|84,955|5,053|
|6238|Train|85,459|6,097|
|2514|Validation|93,150|4,012|

Class 1 is pancreas parenchyma excluding class 2; class 2 is lesion, including outside-pancreas reference voxels. Tiny 2973 and source-boundary 6238 remain present. All seven derived-cache orthogonal views were inspected: no cache-specific empty target or obvious axis/padding anomaly. This is mechanical review, not expert annotation adjudication. Views are in `outputs/prowl/SEGMENTER-CACHE-REVIEW-20261002/cached-inputs.png` with per-plane records and visual-review hash.

## Immutable evidence and storage boundary

New scoped [cache capability](SEGMENTER-CACHE-STORAGE-CAPABILITY-2026-10-02.json) uses the unchanged registered artifact root, exact area `segmenter-input-cache`, exact artifact ID `segmenter-input-cache:D323:6b2df995-409a-424f-9e39-cc9f244220fc`, APFS UUID and frozen 536,870,912 B quota. Registry hash remains `46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788`; access/global source configuration remain unchanged. Cache is derived local scratch; no independent keeper copy is claimed.

|Record|Persisted SHA-256|
|---|---|
|Cache storage capability|`06a7220773ac5572a18c8ca3f5c995d2bce8be007cc68d90f5fb901414466087`|
|Fresh synthetic profile receipt|`63332c33b4fead3fd1a9905432f4210b9fe6aeb78de275f911cd082d2af2d03e`|
|Cache binding|`cdd7c7071cc70663d6f2779b1e9b68890995f85d60d1a9bd561b61918ec275b6`|
|Cache artifact completion|`90b8cc94fec1dd68dc70ed03e6037635e566481bd8d2f4918d7d2cc3827983a6`|
|Fresh build evidence receipt|`18f6e98bae555242d70e67bf4679437830fc324f7e01d95148b893705f5ea9dd`|
|Cold replay receipt|`7265284cd374b7fedbbd9ee71c1eded5338fb6366fe8404e0fb5004abbfd2cd7`|
|Cache acceptance|`8b21315b14e38a6f582964a274d430ce768af9fb8348c8858c9ece62221125f3`|
|Sealed review receipt|`f7440f39dbb92d6d746a8f10a7ecdef7c0511bdc163a8ea3c22a72f35d849e5f`|

Review `outputs/prowl/SEGMENTER-CACHE-REVIEW-20261002`: **42 covered members / 797,102 B**. Acceptance lives there as `accepted-cache.json`. Direct audit checks 28 diagnostic members and 18 physical artifact files, every receipt/event/member hash, all array shapes/dtypes/values/counts, unchanged original content/transform/fidelity pins and source accounting, registry/code pins and actual area quota. It uses saved metadata and derived cache only; no original-source reads or cache/training assembler import for its count/byte oracles. All first-attempt and metadata faults are preserved. Sealed review/source/next-packet pins rechecked; no independent keeper copy of the whole review is claimed.

## Next

[Real-input inference packet](SEGMENTER-REAL-INFERENCE-PACKET-2026-10-02.md), SHA-256 `80d827195ac72b9022972b819aa68b2ebb450735e2eb9c8eb987f6237007685f`: separate fresh step-0 task, all-seven zero-update MPS/native exports and task-specific independent recovery. Native model scoring needs a fresh fourteen-target original-reference scope; cached targets are not original native truth. No CT rereads are needed for cache inference.

Historical checkpoint hash inventory/import denial and a real optimizer/sampler/evaluation transaction remain before a short exact training request. D-322's learned synthetic weights cannot initialize the real task. One positive validation reference/no verified real negatives remains engineering only. No pending training launch, automatic extension, formal jitter/cascade promotion or new qualifications.
