# Plan 07 P3 synthetic foundation: handback for Codex review (revision 2)

**From:** Claude. **To:** Codex (contract and integration review). **Decider:** Quinton.
**Date:** 2026-09-28.
**Packet:** `../operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md`, dispatched by Quinton.
**Review addressed:** `CODEX-P3-REVIEW-2026-09-28.md` (changes requested, R1–R5). Quinton asked Claude
to address R1–R5, add regression tests and return an updated handback.

**Status:** R1–R5 addressed on synthetic fixtures, with regressions at the public entry points.
**Ownership is handed back again:** Claude does not edit these files during re-review. P4b does not
start before an accepted contract review and a separate dependency approval. This is a correction
round, not a new phase; the frozen needs, existing decisions and the proposal status of the
span-hit and delivered-evidence metrics are unchanged.

## Environment: not native

The Mac `.venv-prowl` interpreter is a broken symlink inside Claude's Linux VM, so **native tests
were not run.** Everything was developed and tested in a Linux container:
- Python 3.12.3;
- jsonschema 4.26.0, pytest 9.1.1, PyYAML 6.0.3, nibabel 5.4.2, numpy 2.5.1 (the project pins);
- `pyflakes` for linting, container only.

No project dependency, environment or lockfile was changed. The container holds only the P3 files
plus `src/__init__.py` and `pytest.ini` (copied), so **the full suite could not run there.** (Codex's
first native run measured 751 passed.) Codex, please rerun both packet commands natively.

Preflight for this round: the P3 files on the Mac were confirmed byte-identical to the first handback
before any change; HEAD was `21f838c`. Codex's review file was read, not modified.

## R1–R5 resolution

### R1 (P1): identities recomputed on load; duplicate logical records refused

- New `verify_revision` (recomputes `rev:` from work and content hash; with `content_bytes`, also
  checks the hash itself), `verify_rights` (recomputes `rights:` from representation, policy,
  decision, all five permissions and reason) and `verify_event` (`evt:<file>:<ordinal>`).
- They are called where records are loaded, not only in constructors:
  - `replay_events`;
  - `build_corpus`;
  - `may_index`, `may_display` and `may_redistribute`;
  - evaluation and delivered-evidence scoring (rights and representations).
- `_index_unique` now refuses **any** repeated ID: a conflicting record, and also a byte-identical
  duplicate. This covers works, revisions and representations; rights were already limited to one
  per representation, and passages already refused duplicates. `replay_events` refuses a
  duplicated revision record. Repeating the same revision through **distinct events** stays
  allowed, and is tested.
- `verify_corpus_manifest` now also checks that the counts reconcile, and that exclusions are
  sorted, unique and disjoint from members.
- **Regressions** (`test_records`):
  - `test_r1_rights_changed_under_stale_id_rejected_everywhere`: 8 cases (each of the five
    permissions, decision, reason and policy version), through `build_corpus` and all four rights
    functions;
  - `test_r1_codex_probe_display_flip_no_longer_yields_same_corpus`: a properly re-issued decision
    gets a new rights ID and a new corpus ID;
  - `test_r1_rights_moved_to_another_representation_rejected`;
  - `test_r1_revision_changed_under_stale_id_rejected` (content hash and work);
  - `test_r1_revision_content_check_when_bytes_available`;
  - `test_r1_event_identity_is_its_position`;
  - `test_r1_identical_duplicate_logical_records_rejected` (works, revisions, representations,
    rights);
  - `test_r1_duplicate_revision_rejected_in_replay_but_repeated_events_allowed`;
  - `test_r1_manifest_counts_and_exclusions_must_reconcile`;
  - `test_r1_representation_probe_from_codex_review`.

### R2 (P1): evaluation bound to question, accepted query and verified records

- `verify_ranking(ranking, corpus_manifest, query, *, question_id=None, configuration_id=None)`: the
  query is now **required**; it must verify, be `accepted` and match the ranking.
- `evaluate(...)` gains a required `queries` mapping (question → query record). It:
  - refuses duplicate question IDs across label sets;
  - refuses rankings or queries filed under a question with no label set;
  - verifies each ranking against its own label set's question ID (not just the dictionary key), its
    query, the configuration and the corpus;
  - verifies rankings for refusal-labelled questions but does not score them.
- New `verified_corpus_records(manifest, passages, representations)`, used by both `evaluate` and
  `delivered_evidence`:
  - verifies the manifest and every representation, refusing duplicates;
  - verifies every **member** passage against its representation (identity, exact hash-matching
    slice, section bounds);
  - requires each passage's text hash, representation and work to equal its manifest entry.

  Non-member passage records are not used for scoring.
- **Regressions** (`test_metrics`, through `evaluate`):
  - `test_r2_ranking_filed_under_the_wrong_question_rejected`, including a stray question key;
  - `test_r2_duplicate_question_label_sets_rejected`;
  - `test_r2_refused_missing_or_mismatched_query_rejected`: refused, different, missing and
    tampered query records;
  - `test_r2_changed_passage_or_representation_content_rejected`: forged end offset, consistent hash
    with a stale passage ID, altered representation text, a forged offset map, and duplicate or
    missing records;
  - `test_r2_manifest_entry_must_match_the_passage_record`: a manifest entry changed and its corpus
    ID recomputed.

### R3 (P1): delivered evidence from verified geometry and verified text

- **New signature:**
  `delivered_evidence(*, question_label_set, query, ranking, corpus_manifest, passages,
  representations, rights, counter, budget=2000)`.
  The `ranked_passages` and `passage_texts` parameters are **removed**, so the caller can no longer
  supply geometry or text.
- **Order of checks:**
  1. The ranking is verified against the label set's question, the accepted query and the corpus.
  2. The ranked passages are taken from the ranking's items after `verified_corpus_records`.
  3. A text counter receives only `passage_text(verified passage, verified representation)`.
  4. Any counter that is not `FixtureCounts` or labelled `synthetic_counter` is refused before it
     sees text.
- **Display permission** is enforced independently of indexing. Each ranked member's rights ID must
  resolve to a supplied, identity-verified decision for that representation (fail closed).
  Non-displayable passages are skipped with `display_not_permitted` (token count `null`) and never
  delivered.
- The result now carries `query_id`, `ranking_id` and `corpus_id`.
- **Regressions** (`test_context`):
  - `test_r3_forged_passage_end_offset_rejected`: the Codex probe; with budget 1 the honest recall is
    1/3, and the forged record is refused rather than scored as 1;
  - `test_r3_counted_text_is_the_verified_slice_and_altered_text_is_refused`: a recording counter
    sees exactly the three slices; altered text or a forged map is refused before anything is
    counted;
  - `test_r3_display_permission_enforced_independently_of_indexing`: an indexable, non-displayable
    corpus delivers nothing; a stale-ID escalation to display is refused; missing rights fail
    closed;
  - `test_r3_bound_to_verified_ranking_question_query_and_corpus`;
  - `test_r3_counter_must_be_named_synthetic_or_fixture`.

### R4 (P2): offset maps and original provenance bound and validated

- Each paragraph now carries `original_length` and `original_sha256` (of the original paragraph
  text). Those two and the `offset_map` are part of `representation_identity`.
- **New `verify_offset_map`**, called for every paragraph by `verify_representation`:
  - exact normalized coverage from 0 to the paragraph length, with no gap or overlap;
  - non-empty, non-inverted segments;
  - original coordinates strictly increasing and contiguous between segments; only leading and
    trailing whitespace may be unmapped;
  - bounds within `[0, original_length]`;
  - canonical merged form;
  - a length-changing segment must be one collapsed space or one NFC cluster.
- `verify_representation` also checks paragraph order, grouping by section, indices 0..n-1, and
  that section ranges equal their paragraphs' span.
- **Limitation, stated rather than hidden:** structure alone cannot prove *which* original characters
  a segment came from. For example, `[[0,1,1,2],[1,2,2,5],[2,5,5,8]]` is structurally valid for
  `'  A  b c\n'` but wrong. The new `verify_representation_source(rep, sections)` proves provenance by
  rebuilding from the originals and requiring an exact match. The original paragraph hash is bound
  into the identity, so the check is anchored.
- **Regressions** (`test_passages`):
  - `test_r4_map_and_original_are_bound_into_identity`: the probe, an in-bounds shift, the length
    and the hash;
  - `test_r4_forged_maps_rejected_even_when_reidentified`: 11 cases, with the ID recomputed so that
    the semantic checks are tested on their own (gaps, overlaps, out of bounds, original gap and
    overlap, unmerged, empty, inverted, lumped);
  - `test_r4_structurally_valid_but_wrong_provenance_needs_source_check`;
  - `test_r4_unicode_and_whitespace_maps_verify_and_round_trip`: 6 cases (decomposed and stacked
    accents, tab/newline edges, NBSP and em space, emoji, blank-line runs), checking every segment's
    text;
  - `test_r4_paragraph_order_and_indices_checked`.

### R5 (P2): verifiable eligible pool and depth

- `supplied-ranking` gains `eligibility_policy` (const `all_corpus_members`) and `eligible_count`.
  Both are in the ranking ID.
- `make_ranking` now takes `corpus_manifest` instead of `corpus_id` and `eligible_pool_size`. It
  derives `eligible_count` from the corpus members, never from the caller, and requires exactly
  `min(50, eligible_count)` items.
- `verify_ranking` checks:
  - `eligible_count` equals the corpus member count;
  - the item count equals `min(50, eligible_count)`;
  - `eligible_pool_exhausted` is set exactly when `eligible_count` < 50;
  - `eligible_count`, `result_count` and `target_depth` are plain ints (bool and float, such as
    `5.0`, are refused; JSON Schema alone accepts `5.0` as an integer).

  No production filtering was invented.
- **Regressions** (`test_metrics`):
  - `test_r5_false_exhaustion_rejected`: the Codex probe at construction; a forged `eligible_count=1`
    with the ID recomputed; and a truthful count with too few results;
  - `test_r5_eligible_count_must_be_a_plain_integer`: `True`, `5.0`, `'5'`, `-1`, `None`;
  - `test_r5_valid_small_and_empty_pools`;
  - `test_r5_depth_fifty_when_pool_is_larger`: a 60-member corpus returns 50; 49 is refused; a
    claimed shortfall is refused.

### Codex probes after the fixes

The review's probe script calls the pre-revision signatures (`make_ranking(corpus_id=…,
eligible_pool_size=…)`, `delivered_evidence(ranked_passages=…)`). Unchanged, it now stops at its
first probe with `RecordError: rights ID does not match its decision content`. An adapted copy
(same mutations, new signatures; scratch only, not in the repo) gives:

| Probe | Before | After |
|---|---|---|
| Rights changed, stale ID, same corpus | true | rejected: rights ID does not match its decision content |
| Revision hash changed, stale ID | true | rejected: revision ID does not match its content |
| Offset map `[[0,1,9000,9001]]` | true | rejected: representation ID does not match its content |
| Wrong-question ranking | scored (1) | rejected: ranking belongs to a different question |
| Duplicate label set | counted twice (2) | rejected: duplicate question_id in label sets |
| 1 of 5 claiming exhaustion | accepted (1) | rejected at construction (min(50, eligible_count) = 5) and at verification (eligible_count does not match the corpus) |
| Forged passage end offset | recall 1/3 → 1 | rejected: passage text hash does not match its slice |

Each is also an assertion regression in the test files named above.

## Interface changes (breaking, lane-local)

| Function | Change |
|---|---|
| `make_ranking` | `corpus_manifest=` replaces `corpus_id=` and `eligible_pool_size=` |
| `verify_ranking` | `query` is required; optional `question_id=` and `configuration_id=` |
| `evaluate` | new required `queries=` |
| `delivered_evidence` | new required `query`, `ranking`, `corpus_manifest`, `passages`, `rights`; removed `ranked_passages`, `passage_texts` |
| `verify_offset_map` | new; takes the normalized paragraph text |
| `verify_representation_source` | new |
| `verify_revision`, `verify_rights`, `verify_event` | new |
| `verified_corpus_records` | new |

No module outside `src/retrieval/` imports these.

**Schemas.** Three schemas changed:
- `representation`: paragraph `original_length` and `original_sha256`;
- `supplied-ranking`: `eligibility_policy` and `eligible_count`;
- `context-result`: `query_id`, `ranking_id` and `corpus_id`; `skipped.tokens` may be null;
  `skipped.reason` adds `display_not_permitted`.

They stay at **1.0.0** because v1.0.0 was never accepted, and no record was persisted or consumed
outside these tests. **Codex to confirm**, or ask for 1.1.0.

## Files (all inside the allowlist)

"Changed" means changed in this round; the other files are byte-identical to the first handback.

| File | SHA-256 | This round |
|---|---|---|
| `src/retrieval/__init__.py` | `1e2d99a123b8f5baf8d1644b87cf2c3e23327fd7188b28c7ca4996621560a92b` | unchanged |
| `src/retrieval/records.py` | `0f70d4fadac0f1cf211c76be1a9a35df192de893d2552fa4aa4ff10eb19396b7` | **changed** |
| `src/retrieval/passages.py` | `1ab8dc86605eccd769959d5155b71849e28ae015e882f68327fabdff980931ec` | **changed** |
| `src/retrieval/query.py` | `d878e4bb49080bf8d52f899fac0f7f7b132972f78a1c4f65f54fc02b3d811b92` | unchanged |
| `src/retrieval/labels.py` | `c42f33e547c4a89fc69af81316be23349bac4b477c813b0aca5593457995a02c` | unchanged |
| `src/retrieval/metrics.py` | `5f40449c3e647a0e50c0db9ace2d663bb510ecd77aca0a3cfe0516e0cbd5f878` | **changed** |
| `src/retrieval/context.py` | `6798ade703582ea91b0292bd5de2322d3554b1ddd55330a832d74796827420cd` | **changed** |
| `tests/retrieval/test_records.py` | `f27f9c3d2564c267ff857eb0d7609a7a9bdc79fcccf143be2b0e4e06e22de41e` | **changed** |
| `tests/retrieval/test_passages.py` | `e5ec52acd183053e2c0569717fd99a9442b580a74505ff335c680ea82b38c15f` | **changed** |
| `tests/retrieval/test_query.py` | `5689a7960bfe5c8ffa4cf9be8f203137506a6a1636a8862432ac554b573f6c24` | unchanged |
| `tests/retrieval/test_labels.py` | `791f0e36f258b1d42ee17e0e332a48bf2db81510ff3d8d5bb280acce5a6918f2` | unchanged |
| `tests/retrieval/test_metrics.py` | `405c65dff9df6f916aebbb83a00024d975b4628ca60f1a451a923846802c5881` | **changed** |
| `tests/retrieval/test_context.py` | `3d758022b1f04908ffa902386b256d35600c8bb3bb6475d8a0c631a0fb065d78` | **changed** |
| `tests/retrieval/test_pipeline.py` | `ab6bb3a587e5a22ef3ccccc4d64aabcdc466577ef8b03f5e3fddb1e004bc9334` | **changed** |
| `tests/retrieval/fixtures/synthetic_documents.json` | `fcdcf48550b7cc8cbacf3a44ab161bc3f6bda52386c902ba7c4dd6cd39b0050e` | unchanged |
| `tests/retrieval/fixtures/README.md` | `4572bf30247d958d02cbcf2fab4d9109e7f733d334ea78c88a2897e45c9bc29a` | unchanged |
| `docs/capstone/contracts/retrieval/README.md` | `b86c170f4f1fcf1ca85ef3599619841de9716c42feae263a8c7d7ae4c139e990` | **changed** |
| `…/retrieval/context-result.schema.json` | `c8cfbe08a62a268763a5fefd5223fbefa6a55707eb4a5e6451d22e74e0d3b397` | **changed** |
| `…/retrieval/corpus-manifest.schema.json` | `ec348c4ce6fe1768367a0a72712373e5b0457847520165ff58b48f309b208842` | unchanged |
| `…/retrieval/metric-result.schema.json` | `b205f6a522819578342a3c816aa862c4adca11f634a2d783cc29895942e49b97` | unchanged |
| `…/retrieval/passage.schema.json` | `86a9a48694f6d6e21e6c7863695d25adf88d9142c8da4b5035175adf3bd809ea` | unchanged |
| `…/retrieval/query.schema.json` | `a515105d3db97bb0d5e32fa2408236d50ef5a866019cbde8b1a558fd3622b21a` | unchanged |
| `…/retrieval/representation.schema.json` | `0e67ffeef6476dcd03dfd60cadfd7554f1f2363b5a807700b476236f4f3f2c6c` | **changed** |
| `…/retrieval/rights-decision.schema.json` | `79247c250437b489e405b7bf5ac9684b6689da226c3f080c11d1e1c3c74f8a05` | unchanged |
| `…/retrieval/source-event.schema.json` | `baeae66f7ad1697fa8e2dfd203b0422d3ff77efe6ac790d4edc75eab79e23b24` | unchanged |
| `…/retrieval/source-revision.schema.json` | `3baf7278e602252d0b3ef1b32bc36ec9b878a26a7a70d074231c456187c8926e` | unchanged |
| `…/retrieval/source-work.schema.json` | `b7957d27e63512da1019a9481c29de39a090d441722db78f240155ff286d9102` | unchanged |
| `…/retrieval/span-label.schema.json` | `ac8cff5b6dc92ee087ada92c68a9e6b0f428b838bbb164fab360254b8c122aba` | unchanged |
| `…/retrieval/supplied-ranking.schema.json` | `daf48122fd2ad0f1a79f393f1bdd9b8402db630949e7ab4e669be2023c0bb5de` | **changed** |
| `docs/capstone/retrieval/FOUNDATION-DESIGN-2026-09-28.md` | `8473de7252760edffa5399fc9e8d7983e5677c31d5b635b25283523be640223d` | **changed** |
| `docs/capstone/retrieval/CLAUDE-FOUNDATION-HANDOFF-2026-09-28.md` | this file (hash in RUNNING-LOG) | **changed** |

Also appended: the "P3 corrections R1–R5 started" and "P3 corrections handback" entries in
`docs/capstone/retrieval/planning/RUNNING-LOG.md`. No other file was touched. There is still no
conftest, no `lexical.py`, no database driver and no global hooks.

## Test results (container, not native)

```text
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/retrieval -q -p no:cacheprovider
182 passed (repeated 3 times, stable; about 1.8 s)   [was 120]
pyflakes src/retrieval tests/retrieval   -> clean
```

Per file (parametrized cases counted individually):

| File | Tests | Was |
|---|---:|---:|
| records | 38 | 17 |
| passages | 41 | 18 |
| query | 41 | 41 |
| labels | 9 | 9 |
| metrics | 24 | 12 |
| context | 23 | 18 |
| pipeline | 6 | 6 |

Only registered markers are used.

**Not run here:** the full suite (`python -m pytest tests`) and native macOS execution.

## Fault injection for the new guards (33 faults, each reverted; suite green afterwards)

Each guard added in this round was disabled one at a time, and the retrieval suite rerun:

| Area | Guards disabled |
|---|---|
| R1 (7) | rights identity; revision identity; event identity; identical-duplicate refusal; replay duplicate revision; manifest count reconciliation; `may_display` skipping identity |
| R4 (11) | map out of identity; original hash out of identity; coverage; normalized gap/overlap; original contiguity; bounds; empty/inverted; canonical form; single-cluster rule; paragraph indices; source rebuild |
| R5 (4) | eligible count vs corpus; depth in verify; depth in make; strict int |
| R2 (7) | question binding; duplicate questions; stray keys; passage re-verification; representation re-verification; manifest entry match; query state |
| R3 (4) | display enforcement; question binding; rights lookup; counter kind |

All 33 are now caught. **Two were missed on the first run and fixed by adding tests, not by
changing the implementation:**

1. **Representation re-verification removed from `verified_corpus_records`.** Altered text was still
   caught downstream by the passage slice hash. The new cases use a forged offset map with intact
   text: `test_r2_changed_passage_or_representation_content_rejected` and
   `test_r3_counted_text_is_the_verified_slice_and_altered_text_is_refused`.
2. **The counter-kind guard.** The context-result schema enum rejected the result anyway, but only
   after the untrusted counter had seen text. The test now also asserts that the counter was never
   called.

The first round's 10 faults were not re-run as a separate campaign. Their catching tests are
unchanged and pass.

**Oracle correction disclosed:** one R4 case (`[[0,1,2,3],[1,5,3,8]]`, lumping `'b c'` into one
many-to-one segment) was first expected to fail on coverage. It is in fact structurally valid under
the first rule set. Claude added the stated single-space-or-single-cluster rule
(`verify_offset_map`), which is what the normalization actually produces, and expects that message.
This tightened the implementation to a documented invariant; it was not a change made to fit a test.

## Requirement-to-test map (first round, still valid)

| Packet requirement | Tests |
|---|---|
| Explicit schema versions; reject unknown fields, IDs, enums, versions | `test_records::test_schema_rejects_unknown_fields_ids_enums_versions`, `test_every_schema_is_valid_draft_2020_12`, `test_query::test_unknown_or_forbidden_finding_keys_rejected`, `test_finding_values_must_be_allowlisted` |
| Canonical hashing; float and non-finite rules; no timestamps or paths | `test_records::test_canonical_bytes_rules`, `test_pipeline::test_records_are_portable_no_absolute_paths_or_secrets` |
| Deterministic identities; changed text, rights or chunking changes identity | `test_records::test_identity_is_deterministic_and_content_sensitive`, `test_changed_text_rights_or_chunking_changes_identity`, `test_passages::test_chunking_config_validation_and_determinism`, `test_query::test_identity_deterministic_and_tamper_detected` |
| Work/revision/event/representation separation; repeated identical content; replay | `test_records::test_event_replay_last_wins_delete_and_readd`, `test_event_replay_rejects_bad_order_and_links`, `test_superseded_or_deleted_revision_is_not_indexed`, `test_r1_duplicate_revision_rejected_in_replay_but_repeated_events_allowed` |
| Duplicates, conflicts, dangling references rejected | `test_records::test_corpus_rejects_dangling_and_conflicting_records`, `test_r1_identical_duplicate_logical_records_rejected`, `test_metrics::test_cross_corpus_duplicate_and_unknown_items_rejected` |
| Rights: retention/indexing/display/redistribution independent; fail closed | `test_records::test_rights_permissions_are_independent_and_fail_closed`, `test_corpus_reconciles_and_excludes_with_reasons`, `test_r1_rights_changed_under_stale_id_rejected_everywhere`, `test_context::test_r3_display_permission_enforced_independently_of_indexing` |
| Retraction and quarantine never support answers | `test_records::test_retraction_and_quarantine_cannot_support_answers`, `test_pipeline::test_full_synthetic_chain_hand_checked` |
| Link and content-hash verification, not schema shape alone; no circular IDs | `test_records::test_real_origin_refused_by_default_and_tampered_manifest_detected`, `test_passages::test_tampered_representation_rejected`, `test_broken_offsets_or_stale_hash_rejected`, all `test_r1_*`/`test_r4_*` |
| Normalization, offset map, Unicode, whitespace, negation | `test_passages::test_whitespace_collapse_and_offset_map_hand_checked`, `test_nfc_composition_maps_back_to_original_cluster`, `test_refused_characters_and_empty_paragraphs`, `test_cross_cluster_normalization_is_refused_not_mapped`, `test_negation_and_wording_preserved`, `test_unicode_offsets_are_code_points`, `test_r4_*` |
| Deterministic chunking; overlap; oversized; never crossing sections | `test_passages::test_sentence_split_hand_checked`, `test_chunking_hand_checked_overlap_and_no_redundant_passages`, `test_oversized_sentence_kept_whole_and_flagged`, `test_passages_never_cross_sections_and_slices_match` |
| Label bounds, concepts, staleness; uncertain excluded | `test_labels::*` (all five) |
| Complete containment = direct; partial overlap is not | `test_labels::test_complete_containment_is_direct_partial_overlap_is_not`, `test_metrics::test_passage_metric_undefined_when_no_passage_contains_span` |
| Query gate: allowlist, forbidden fields, length/characters, out-of-scope and injection fixtures, negation | `test_query::*` (41 cases) |
| Rankings: identities, score direction, tie policy, depth 50 or complete smaller pool, duplicates, cross-corpus, query binding | `test_metrics::test_ranking_validation_rules`, `test_cross_corpus_duplicate_and_unknown_items_rejected`, `test_r5_*`, `test_r2_*`, `test_pipeline::test_ranking_bound_to_accepted_query_and_evaluation_permutation_invariant` |
| Official recall@k and MRR: packet oracle, k validation, set gold, zero-gold invalid | `test_metrics::test_packet_oracle_recall_and_mrr`, `test_metric_input_validation` |
| Source dedup and renumbering | `test_metrics::test_source_collapse_first_occurrence_then_renumber`, `test_evaluate_hand_computed_report` |
| Refusal items outside means; empty means null, never NaN or 0 | `test_metrics::test_evaluate_hand_computed_report`, `test_empty_answerable_set_is_explicitly_undefined` |
| Passage metrics within configuration only | `test_metrics::test_passage_metric_undefined_when_no_passage_contains_span`, `test_evaluate_rejects_mixed_versions_and_configurations` |
| **Proposed** span-hit recall, labelled, distinct spans | `test_metrics::test_span_hit_counts_each_span_once_across_overlapping_passages`, `test_span_hit_duplicate_containment_does_not_inflate_partial_recall`, `test_evaluate_hand_computed_report` (provisional block) |
| **Proposed** delivered evidence: packet oracle A/B/C 8/7/2 at 10; skip-then-fit; no truncation; no skipped credit; no double count; count/budget validation; counter labelled; verified inputs; display permission | `test_context::*` (all) |
| End-to-end chain with refusal, unavailable and insufficient-evidence fixture states | `test_pipeline::test_full_synthetic_chain_hand_checked`, `test_fixture_outcome_states` (the empty ranking now comes from an empty, all-non-indexable corpus; an empty ranking against a full pool is `unavailable`) |
| Input permutation, no input mutation, deterministic rebuild | `test_records::test_corpus_identity_deterministic_and_permutation_invariant`, `test_pipeline::test_deterministic_rebuild_and_inputs_not_mutated`, `test_ranking_bound_to_accepted_query_and_evaluation_permutation_invariant` |
| No network or drive dependency; no import-time writes; no paths or secrets in source | `test_pipeline` (autouse socket guard), `test_import_has_no_side_effects`, `test_records_are_portable_no_absolute_paths_or_secrets` |

## First-round record (unchanged)

The first round's fault injection (10 faults; the duplicate-span-credit miss and its added test)
and the oracle corrections (offset-map merge; pipeline passage MRR 1/3; two label tests isolated)
are as reported in the first handback (RUNNING-LOG, "P3 handback to Codex"). The worked example in
`test_metrics::test_evaluate_hand_computed_report` gives the same values. Only its call now passes
`queries=`, and its rankings are built from the corpus (all 5 members, as before).

## Deliberate limitations

- Keyword scope rules are a fixture demonstration. They are not semantic safety, not anonymization,
  and not a basis for external calls. RF5 belongs to the future response layer.
- Coarse count/size bins and warning categories are provisional fixture enums.
- Sentence splitting is rule-based; abbreviations can split early (boundaries only, never text).
- Paragraphs where cluster-wise NFC differs from whole-string NFC are refused, not mapped.
- Offset-map structure cannot prove per-character provenance. That needs
  `verify_representation_source` with the original paragraphs, which the P5 parser should call.
- `verify_revision` can check the content hash only when the content bytes are supplied.
- `eligible_count` is verifiable only under the P3 policy `all_corpus_members`. Any future filter
  policy needs its own verifiable inventory, and none is invented here.
- The token counter is synthetic (word count). Production needs a pinned tokenizer and re-reporting.
- Ranking IDs hash finite float scores through Python's shortest round-trip JSON representation. A
  non-Python reimplementation should compare with care.
- The representation schema carries text. Real restricted text must live only in local artifacts,
  never Git.
- Rights decisions are fixture inputs. There is no legal interpretation engine.
- The corpus accepts only `origin=synthetic` by default; there is no real-corpus promotion.

## Proposed shared-interface changes (not made)

1. Decide whether `docs/capstone/contracts/retrieval/` joins `tests/test_contracts.py` and
   `VALIDATION.md` (Codex-owned).
2. Confirm schema versioning for this pre-acceptance revision: 1.0.0 as revised, or 1.1.0.
3. Map these records to the P4b PostgreSQL schema (SCOPE 5.3). They are the canonical artifacts the
   database loads.
4. Real finding bins and warning allowlists from Plans 05/08.
5. D-085 amendment for span-hit and delivered-evidence metrics: still a proposal, untouched.

## Remaining gates (not started)

- **Codex:** contract re-review and native test runs (focused and full suite).
- **P4b** (contract-bound database work) needs an accepted review plus a separate psycopg 3 approval.
- **P4a** (platform infrastructure) needs its own install authorization.
- **Seed candidate review (P2)** is still pending.
