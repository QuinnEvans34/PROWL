# Segmenter source verification — D-316

October 1, 2026. **All36 files present and identity-checked; all12 lesion grids match their qualified CT grids.** No source arrays, real Stage2 qualifications, cohort publication or model updates.

## Results and limits

The protected proposal remains8 train/4 validation. All24 CT/pancreas compressed hashes match retained references; lesion3/26 also match their prior diagnostic hashes. Ten other lesion hashes are newly observed identities, not matches to pre-existing lesion truth. Current source-root/volume identity and pre/post file observations pass. All12 lesion headers are valid supported3D NIfTI-1 and agree with the corresponding qualified mm CT shape/affine. Every candidate stays in the ledger; no refills or new holds.

Five lesions (26/2973/2232/6238/5821) use signed int8 scaling: slope0.003921568859368563, intercept0.501960813999176. Strict binary checking must use semantic values after scaling; stored-byte thresholding would be wrong. Six lesion headers declare unknown spatial units (those five plus5641). Context comes only from their exact matched, positively qualified mm CT grid. Headers were not rewritten. This establishes geometric context, not lesion completeness or purpose permission.

All lesion payloads are native int8 with352-byte offsets. Total projected lesion payload238,260,930bytes; including headers/offsets238,265,154bytes. This is a measured content-read envelope, not evidence of foreground. The legacy124-voxel hint for2973 and zero hints for6110/4965/2727/7265 remain unverified. Empty/negative status has not been measured or inferred. Full compressed hashing is not a new full gzip CRC check; M2 decompresses only348 header bytes per lesion.

|Case|Protected role|Native grid|Lesion compressed bytes|Scaling|Spatial units|
|---|---|---|---:|---|---|
|3|train|495 × 349 × 40|30,594|identity|mm|
|26|train|512 × 362 × 81|67,458|scaled int8|unknown|
|6110|train|276 × 215 × 91|23,706|identity|mm|
|2973|train|512 × 366 × 60|49,270|scaled int8|unknown|
|2232|train|444 × 352 × 95|65,942|scaled int8|unknown|
|6238|train|512 × 402 × 197|179,593|scaled int8|unknown|
|5821|train|508 × 318 × 237|168,344|scaled int8|unknown|
|4965|train|468 × 360 × 129|94,981|identity|mm|
|2514|validation|394 × 268 × 89|41,753|identity|mm|
|5641|validation|512 × 434 × 208|213,959|identity|unknown|
|2727|validation|221 × 208 × 111|22,407|identity|mm|
|7265|validation|435 × 354 × 153|102,955|identity|mm|

## Requests, budgets and measured resources

- M1 attempt01: request`c9ef8c58…`, consumed before candidate observation. Sandbox blocked macOS DiskManagement at volume verification. Failure/request/log preserved; no retry of consumed request or bypass.
- Fresh M1 attempt02 request`0ce9ca20…`: all36 exact regular files, sizes match companions, no holds. 1.8673s,107,102,208bytes RSS (0.100GiB). Zero payload/header reads. Limits90s/512MiB/1MiB output; native volume check used.
- M2 request`7042885d…`: all36 compressed identities,12 lesion headers;7.6179s,107,184,128bytes RSS (0.100GiB). Hashed276,002,660compressed bytes; additional49,152compressed header bytes, total276,051,812bytes. Read ceilings276,002,660+786,432;600s/1GiB/4MiB output. No array decompression/loading.

M1 complete receipt`9a1e5c9c16100b4039e99bad100bc9ac74cdc1342ab5860da4be01d100a247f7` at `outputs/prowl/SEGMENTER-SOURCE-M1-attempt02-20261001`. M2 receipt`bec0f3b3f292d187b3bc741be6fa38b8aa355f199c1cf3375657364705421108` at `outputs/prowl/SEGMENTER-SOURCE-M2-20261001`. Both independently rehashed in fresh processes; code/runtime/retained metadata pins rechecked. Consumed scopes must not be reused.

## Implementation and verification

New isolated diagnostic: `scripts/diagnostics/segmenter_source_verification.py`; new test module: `tests/test_segmenter_source_verification.py`. No old consumer or shared schema edits. Descriptor-based canonical directory walks reject symlinks and nested devices; exact observations surround source reads. Metadata payload opens are forbidden. Frozen requests bind code/runtime/source capability and input hashes. Exclusive consumption, read/time/RSS/output guards, retained failure ledgers and completion-last receipts cover each attempt.

Thirty-three new synthetic checks cover exact stat outcomes, symlink/root traversal, identity replacement/mutation, truncated hashes, header caps and unsupported grids/types/offsets, receipt tampering, exclusive requests, changed companion propagation and resource failures. Initial full-suite run had four fixture failures because previous tests raised the process RSS high-water mark above the invented job's limit. Fixture allowances were corrected without changing real budgets; both attempts retained. Native rerun1,869passed/two existing torch.jit warnings,67.41s. After the sandbox-blocked source attempt, the only code change was a fresh M1 output identity;33targeted checks passed again. Final unchanged-revision native rerun: **1,869 passed**, two existing warnings,62.30s. Logs and pins are retained in the sealed review evidence.

## Next exact implementation slice

[Content and native-alignment packet](SEGMENTER-CONTENT-ALIGNMENT-PACKET-2026-10-01.md): synthetic resource/fault qualification, then a fresh four-case source-content pilot (3/26/2973/5641), review, and separately frozen eight-case continuation. All24 companion content metadata records were recovered from hash-bound retained evidence, so there is no need for a separate new sizing read. Across all36 proposed array files, total expanded size953,056,392bytes; largest case184,878,112bytes. Each source batch must separately budget full hashing plus full decoding; existing M1/M2 capabilities do not authorize arrays.

Next still needs content/CRC/scaled values/component/overlap counts and reviewed native sheets, explicit lesion-purpose dispositions, preserved annotation transitions and a frozen subset. Then shared pancreas-only ROI geometry/fidelity, fresh three-class synthetic learning/recovery, zero-update MPS profile and a short exact training request. No Stage2 permission or training has started; current153localizer members/23holds and original7200/1800/901 remain unchanged. Component-reference diagnostic and Claude's lane stay separate.
