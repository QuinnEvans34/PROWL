# Segmenter initialization audit — v1 contract

**Status:** SUP-01 invented implementation; October6,2026.
**Module:** [segmenter_initialization_audit_v1.py](../../../src/models/segmenter_initialization_audit_v1.py).
**Approved scope:** [qualification packet](../operations/SUPREM-INITIALIZATION-QUALIFICATION-PACKET-2026-10-06.md).
**Governing boundary:** [Plan05 model lineage](MODEL-LINEAGE-AND-TRAINING.md).

## Purpose and scope

Validate an explicitly pinned initialization plan against supplied invented CPU tensor states,
then return a complete cloned state containing the source backbone and the fresh destination head.
Validation happens before cloning. No live model is changed, no file/container is decoded and no
optimizer/RNG/training event occurs. Actual SuPreM source/license/data relationship and tensor
compatibility remain unqualified. A pass is a component-mechanics result with
`execution_authority='none'`, not a source acceptance or launch permit.

The declaration uses the source-compatible SegResNet architecture:1input,16initial filters,
GroupNorm8,down[1,2,2,4]/up[1,1,1],zero dropout,32source outputs and3destination outputs.
The full installed-factory signature is supplied in pinned controls and tested with complete
invented networks. The auditor does not instantiate MONAI or independently infer architecture
from tensor names. Callers must supply a reviewed full signature and stable input tensors/controls;
re-hashing a deliberately incomplete declaration does not establish factory completeness.

## API

```python
prepare_initialization(
    source_state, fresh_destination_state, *,
    candidate_manifest, expected_candidate_sha256,
    policy, expected_policy_sha256,
    historical_inventory, expected_inventory_sha256,
) -> tuple[dict | None, dict]
```

On pass, the first value is a complete new mapping of detached CPU tensor clones. On validation
refusal, it is `None`. The second value is the report described below. Input mappings may be plain
dicts or `OrderedDict`s, as produced by `state_dict`; JSON controls must be plain dicts/lists and
primitive JSON values. Unknown fields, invalid types, implicit casts and unsupported inputs refuse.
Unexpected runtime/allocation failures propagate; validation refusals use stable reason codes.

Helpers: `architecture(out_channels=3)` returns a new declaration;
`limits()` returns fixed bounds; `control_sha256(value)` computes bounded canonical JSON identity;
`describe_state(state)` returns `{signature, sha256, tensor_bytes}` after tensor validation.
Helpers attest neither provenance nor execution rights. They raise `ValueError` on invalid inputs.

## Canonical identities and bounds

Control SHA-256 uses UTF-8 JSON, sorted keys, compact separators, `ensure_ascii=False`,
`allow_nan=False`, followed by one newline. No URI/file is resolved. Invalid Unicode, non-JSON
values, excessive nesting or bytes refuse rather than coercing a value to text.

Limits are fixed and cannot be relaxed by a policy:

| Bound | Value |
|---|---:|
| Tensor count per state |1,024|
| Key size |512Unicode characters and512UTF-8 bytes|
| Logical tensor content per state |67,108,864bytes (64MiB)|
| JSON control encoded size |1,048,576bytes (1MiB)|
| JSON depth / total visited nodes |16 /8,192|
| JSON members per object/list |4,096|
| Inventory rows |256|

Nonempty tensors must be ordinary dense contiguous `torch.Tensor` values on CPU, dtype
`torch.float32`, rank0–5. Reject sparse, quantized, negative/conjugate views, non-CPU and other
types/layouts. Header/count/aggregate-size checks precede finite-value scans and hashing, which
precede cloning. A huge expanded view can fail its logical size without allocating a huge buffer.
All tensor values must be finite. Autograd metadata is not imported; outputs are detached clones.

A state signature maps every raw key to `{shape: [int,...], dtype: 'torch.float32'}`.
The state hash concatenates, in sorted-key order, canonical
`{name,shape,dtype}` bytes and that tensor's dense CPU byte view. It includes names, shapes,
dtypes and contents, independent of mapping insertion order. This uses the native float32 byte
representation, consistent with the current Mac scratch hash; no cross-platform numerical
equivalence is claimed. The caller's declared original-file hash is distinct from this tensor hash.

## Exact control fields

Each object below is closed: only the listed fields are accepted. Hashes are64lowercase hexadecimal
characters; integers exclude booleans. A `reference` object is exactly `{reference,sha256}` with
nonempty bounded text beginning `invented:` and a valid hash. Source locator/citation strings are
bounded nonempty text; they are recorded assertions, not fetched evidence.

### Candidate manifest

| Field | Required value/shape |
|---|---|
| `schema_version` |`segmenter-initialization-candidate-1`|
| `evidence_domain` |`invented_weights_only`|
| `classification` |`licensed_third_party_general_pretraining`, representing invented test evidence|
| `file` |`{uri,sha256,bytes}`; URI begins `invented/`, has no empty/dot/traversal components, colon or backslash; bytes is1–67,108,864|
| `source` |`{repository,artifact,revision,citation,retrieval}`; retrieval is a reference object|
| `rights` |`{status,code,checkpoint,data}`; status=`permitted`, each remaining value is a reference object|
| `overlap` |`{status,evidence}`; status=`reviewed_separate`, evidence is a reference object|
| `architecture` |Exact source32-output architecture, with integer channel/group/block fields|
| `state_signature` |Complete declared raw source tensor signature|
| `state_sha256` |Expected raw source tensor-content hash|

Invented rights/overlap records exercise the refusal mechanism. They do not resolve the actual
SuPreM checkpoint's terms or protected evaluation relationship. Real evidence domains, real file
URIs and real evidence references refuse in this first version. File bytes are declared identity
metadata and are not measured from a serialized payload by this component.

### Policy

| Field | Required value/shape |
|---|---|
| `schema_version` |`segmenter-initialization-policy-1`|
| `evidence_domain` |`invented_weights_only`|
| `architecture` |Exact destination3-output architecture|
| `seed` |Integer42|
| `head_keys` |Sorted list `['conv_final.2.conv.bias','conv_final.2.conv.weight']`|
| `namespace` |`identity` or `uniform_module`|
| `candidate_file` |Same exact `{uri,sha256,bytes}` as the candidate manifest|
| `limits` |Exact `{max_tensors:1024,max_key_bytes:512,max_tensor_bytes:67108864,max_control_bytes:1048576}`|
| `fresh_state_signature` |Complete declared fresh destination signature|
| `fresh_state_sha256` |Bound fresh destination content hash, including both head tensors|

The full fresh hash, not merely the seed label, binds the head values. Callers remain responsible
for proving their generation history; the auditor neither seeds nor independently regenerates them.

### Historical inventory

Top-level fields are `{schema_version,evidence_domain,files}`, with version
`segmenter-initialization-inventory-1` and domain `invented_weights_only`.
Each row is exactly `{uri,sha256,bytes,category,weight_import_allowed}`. File fields have the same
invented URI/hash/byte rules; every `weight_import_allowed` must be the boolean `False`.
Categories are `prior_project_checkpoint_import_denied`,
`capstone_diagnostic_checkpoint_import_denied`, or
`third_party_weights_not_approved_for_this_run`. Exactly one URI row must match the candidate's
full identity. It must be a third-party candidate row. A prior/capstone row with the same hash
denies that source even under another name. Duplicate URIs, unknown categories or changed import
flags refuse. This is a new invented control schema; the actual D-326 inventory stays untouched.

## Tensor mapping and replacement

Validate all three control hashes and their structures before accessing any tensor state.
The candidate-file policy and inventory must agree. Source and fresh actual signatures/content
must equal their pinned declarations. Matching names/shapes with changed values is insufficient.

`identity` permits no `module.` keys. `uniform_module` requires every source key to have exactly
one leading `module.`; strip it once. Mixed/repeated prefixes, collisions, invalid keys and undeclared
prefixes refuse. Container guessing and `torch.load` are outside this API.

After normalization, source and destination inventories must match completely. Every non-head
source shape/dtype must equal its destination shape/dtype. Only the exact head pair differs:

| Tensor | Source | Destination / returned value |
|---|---|---|
| `conv_final.2.conv.bias` |`[32]`|`[3]`, copied from bound fresh state|
| `conv_final.2.conv.weight` |`[32,16,1,1,1]`|`[3,16,1,1,1]`, copied from bound fresh state|

Final-block normalization transfers with the backbone. There is no broad `conv_final` exemption,
no partial load, source-head reuse, implicit dtype conversion, optimizer/history import or fallback
to scratch. An unqualified source refuses. Selecting scratch is a distinct named configuration.

Only after all checks pass are output tensors cloned. Both inputs, controls and CPU RNG remain
unchanged. Returned tensors do not alias either input. The caller may strict-load this complete
mapping into a fresh disposable invented model; this component does not mutate/publish a model.

## Report and refusal semantics

The report always contains these fields:

```text
schema_version, evidence_domain, execution_authority, status, reason,
control_sha256, source_file, source_signature, destination_signature,
normalized_source_signature, source_state_sha256, fresh_state_sha256,
initialized_state_sha256, head_before_sha256, head_after_sha256,
loaded_keys, replaced_keys, missing_keys, unexpected_keys, mismatched_keys
```

Version=`segmenter-initialization-audit-report-1`, domain=`invented_weights_only`,
authority=`none`. Status is `pass`/`refused`; reason is null on pass or a stable validation code
on refusal. `control_sha256` is `{candidate,policy,inventory}` with verified hashes or null when
not reached. `source_file` is copied identity metadata or null. Signatures/hashes are populated only
when their respective validations complete. Missing/unexpected/mismatched lists are sorted raw
destination/normalized-source names; malformed tensor headers may refuse before inventory
diagnostics are available. On refusal loaded/replaced lists are empty, initialized/head-after
hashes are null and no replacement mapping is returned. No partial success is reported.

On pass, loaded keys are every destination non-head key, replaced keys are the exact head pair,
initialized-state hash covers the returned complete state, and head-before/after hashes match.
The report contains JSON-only values and roundtrips without tensor payloads. Canonical sorted-key
JSON may be used by a caller for report identity; `control_sha256`'s control-size/depth bounds are
not a separate full-report serialization promise.

Representative refusal codes include `control_pin_mismatch`, `real_evidence_refused`,
`source_classification_denied`, `rights_unqualified`, `overlap_unqualified`,
`historical_or_capstone_hash_denied`, `candidate_not_in_inventory`,
`tensor_inventory_mismatch`, `tensor_shape_or_dtype_mismatch`,
`source_state_binding_mismatch`, `fresh_state_binding_mismatch`, `tensor_size_limit`,
`non_cpu_tensor`, `unsupported_tensor_type`, `nonfinite_tensor` and namespace/type/schema codes.

## Qualification evidence and next boundary

[Targeted tests](../../../tests/test_segmenter_initialization_audit_v1.py) use small invented
fixtures for refusal boundaries and full32/3-output networks for complete transfer and strict load.
No network forward/backward, optimizer, accelerator, file decode or real tensor is involved.
Results and actual resource measurements belong in the
[SUP-01 handback](../operations/SEGMENTER-INITIALIZATION-AUDIT-RESULTS-2026-10-06.md).

The existing scratch v5 initial hash/import-denial/session/checkpoint behavior is preserved.
Further work needs actual source/version/license/overlap review, an exact file/serialization/read
budget, a separately qualified reader and a new pretrained consumer/recovery identity. No actual
checkpoint load, training or request is enabled by this contract. All original memberships, holds,
failed experiments and fixed backup ceiling remain unchanged.
