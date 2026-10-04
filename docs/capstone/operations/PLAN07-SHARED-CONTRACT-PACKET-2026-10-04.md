# Retrieval 1.0.0 shared offline contract packet — draft

D-343 accepts the integration choice. **This concrete packet is a draft; code is not dispatched.**
Authority: October3 approval entry in [RUNNING-LOG](../retrieval/planning/RUNNING-LOG.md).
Accepted P3 evidence: [Codex re-review](../retrieval/CODEX-P3-REREVIEW-2026-09-28.md), September28,
182 native tests then; current unchanged P3 plus S2 gives313 native retrieval passes.

## Exact proposed scope

Add `tests/test_retrieval_contracts.py` as a separate `contract`-marked offline section and
`tests/fixtures/shared_retrieval_contracts_v1/` containing12 hand-authored invented positive records,
a provenance README and schema/fixture hash manifest. Keep `tests/test_contracts.py`'s exact10
Plan01/02 names, paths and current assertions unchanged. Existing `pytest -m contract` then selects
both sections without extending its legacy name set. No new dependency, source file, real text,
runtime import, database, metric producer or retrieval schema change.

Proposed existing-document edit: `docs/capstone/contracts/retrieval/README.md`, by the contract owner
after coordinating the single writer. Replace only stale “pending Codex contract re-review” wording
with September28 accepted-synthetic status and a link to the exact re-review. Preserve provisional
scope and all schema/P3 limitations. Describe shared integration as complete only after its checks
pass. D-344's policy acceptance does not relabel existing provisional producers or their old outputs;
that migration needs a separate Claude-owned packet.

All12schemas use Draft2020-12, FormatChecker and schema_version1.0.0. Offline controls validate each
schema and positive, reject omitted required identity fields, wrong version/type/enum, unknown
fields, unsafe offsets/paths where represented and malformed nested data. Rights controls reject
missing permissions; query/ranking/label/context controls preserve status, IDs, positive token
counts and applicable denominator shapes. The existing lane runtime tests remain responsible for
content identities, exact representation slices, relationship bindings, rights semantics and derived
metric arithmetic; JSON Schema alone cannot prove those.

## Exact schema pins at drafting

| Schema | SHA-256 |
|---|---|
| context-result | c8cfbe08a62a268763a5fefd5223fbefa6a55707eb4a5e6451d22e74e0d3b397 |
| corpus-manifest | ec348c4ce6fe1768367a0a72712373e5b0457847520165ff58b48f309b208842 |
| metric-result | b205f6a522819578342a3c816aa862c4adca11f634a2d783cc29895942e49b97 |
| passage | 86a9a48694f6d6e21e6c7863695d25adf88d9142c8da4b5035175adf3bd809ea |
| query | a515105d3db97bb0d5e32fa2408236d50ef5a866019cbde8b1a558fd3622b21a |
| representation | 0e67ffeef6476dcd03dfd60cadfd7554f1f2363b5a807700b476236f4f3f2c6c |
| rights-decision | 79247c250437b489e405b7bf5ac9684b6689da226c3f080c11d1e1c3c74f8a05 |
| source-event | baeae66f7ad1697fa8e2dfd203b0422d3ff77efe6ac790d4edc75eab79e23b24 |
| source-revision | 3baf7278e602252d0b3ef1b32bc36ec9b878a26a7a70d074231c456187c8926e |
| source-work | b7957d27e63512da1019a9481c29de39a090d441722db78f240155ff286d9102 |
| span-label | ac8cff5b6dc92ee087ada92c68a9e6b0f428b838bbb164fab360254b8c122aba |
| supplied-ranking | daf48122fd2ad0f1a79f393f1bdd9b8402db630949e7ab4e669be2023c0bb5de |

Stop on pin drift, an occupied new path, required schema migration or ownership conflict. After
dispatch, run both shared test modules, the `contract` marker gate and the complete retrieval suite;
show the exact diff and fixture pins. No launch or commit permission is bundled. No implementation
or test in this packet was created during M5.
