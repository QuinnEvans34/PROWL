# Shared retrieval offline contracts — complete

Quinton approved the exact packet in the October4 Claude log; D-348 records the dispatch.
Added `tests/test_retrieval_contracts.py` and `tests/fixtures/shared_retrieval_contracts_v1/`:
12 hand-authored invented positive JSON records, a provenance README and schema/fixture pins.
No runtime producer was used to construct the fixtures, and no retrieval runtime is imported by
this test module. Placeholder identities/text are shape controls, not accepted content identities.

**118 new checks** cover all12 Draft2020-12 schemas/positives, exact versions and pins, missing/
malformed identities, unknown fields, nested types/ranges/offset shapes, explicit rights permissions,
query-state conditions, ranking limits and preserved metric/context status/token-counter constraints.
They use the existing jsonschema dependency/FormatChecker; references are not fetched.

| Verification | Result |
|---|---|
| Both shared modules (`tests/test_contracts.py tests/test_retrieval_contracts.py`) | **173 passed in1.48s**:55 existing +118 new |
| Shared offline `tests -m contract` gate | **198 passed /3041 deselected in4.12s**, two existing torch.jit deprecation warnings |
| Full native retrieval suite | **313 passed in3.67s**, no skips; sizing_v1 identity814b89c5 and all21pins still match |

After Claude delivered v1.1, [the other Codex chat's native N2 review](CODEX-S2-V1.1-NATIVE-REVIEW-2026-10-04.md)
passed144sizing/326retrieval tests, no skips. This chat reverified all22pins and identitydf585e2b,
then repeated the contract gate against the changed tree: **198passed/3054deselected in4.11s**,
the same two existing warnings. The313result above remains the original revision's evidence;
it is not substituted for the326result. Both shared modules'173checks are unchanged.

The legacy Plan01/02 module, names and fixtures stayed byte-identical. All12 retrieval schema hashes
match the accepted packet. Shared contract README now cites September28 synthetic acceptance and
October4 offline integration; its old pending re-review phrase is removed. Claude's implementation,
lane tests/planning and metric/context producer labels are unchanged.

The existing schemas do not prove relationship/offset semantics, hash truth, rights provenance or
derived counts/arithmetic. Retrieval runtime tests remain necessary; this is not a database, corpus,
real tokenizer, G6 or clinical scope gate. D-344's policy acceptance has not migrated producers or
changed schemas. No real labels, original data, download, install or database execution occurred.

This expands the tested contract section; it is not a new full-project/portable-tree test pass.
Native sizing1.0 results cannot be transferred to a changed code identity. The delivered1.1 now
has its own N2 result. The [binding packet](PLAN07-S1-S2-BINDING-PACKET-2026-10-04.md) remains
incomplete pending the bounded-diagnostics interface and its exact qualification.
