# Plan 07 retrieval contracts (P3, provisional)

**Status:** PROVISIONAL v1.0.0, produced by the Plan 07 P3 synthetic foundation (Claude,
2026-09-28). Revised for Codex review findings R1–R5 before any acceptance, so the version is still
1.0.0 (see the handoff). **Pending Codex contract re-review.** They are not yet integrated with the shared
Plan 01/02 contract set, the PostgreSQL schema (P4b) or any producer beyond the synthetic
foundation. Changing any schema after review creates a new version.

All schemas are JSON Schema Draft 2020-12, with `additionalProperties: false` and a
`schema_version` constant. They are validated in `src/retrieval/records.py` with the existing
`jsonschema` dependency.

| Schema | Record | Notes |
|---|---|---|
| `source-work` | Bibliographic work, status and notices | `origin` names synthetic or real routes; P3 corpus assembly accepts only `synthetic` by default |
| `source-revision` | One exact content version of a work | `revision_id` hashes (work, content hash) |
| `source-event` | Ordered add/replace/delete event | Delete events carry no revision |
| `rights-decision` | Per-representation permissions | All five permissions explicit; missing or unknown fails closed |
| `representation` | Normalized text with section/paragraph geometry, offset maps and each paragraph's original length and SHA-256 | Maps and originals are in the identity; holds text, so real restricted text lives only in local artifacts, never Git |
| `passage` | Exact half-open span of a representation | Identity includes the chunking configuration |
| `corpus-manifest` | Ordered members, reason-coded exclusions, counts | ID derived from the member inventory (not circular) |
| `query` | Allowlisted finding plus preserved question and refusal codes | Keyword scope gate is a fixture-level demonstration only |
| `supplied-ranking` | Fixture ranking with score direction, tie policy, eligibility policy and eligible count | **Not** a retriever output; exactly min(50, eligible_count) items; P3 policy `all_corpus_members` |
| `span-label` | Question label set with evidence spans | Direct support requires complete containment |
| `metric-result` | Official D-085 metrics plus a separately labelled proposal | Span-hit recall is `proposed_provisional_not_official` |
| `context-result` | Delivered-evidence prototype, bound to its query, ranking and corpus IDs | Entirely `proposed_provisional_not_official`; synthetic or fixture token counts only; display-denied passages skipped |

Design and conventions: [`../../retrieval/FOUNDATION-DESIGN-2026-09-28.md`](../../retrieval/FOUNDATION-DESIGN-2026-09-28.md).
