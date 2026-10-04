# Plan 07 P3 synthetic foundation: design

**Status:** Implemented on synthetic fixtures. Revised for Codex review findings R1–R5
(`CODEX-P3-REVIEW-2026-09-28.md`); pending Codex re-review.
**Author:** Claude.
**Packet:** `../operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md`.
**Governing records:** D-260 to D-265; `planning/SCOPE.md` sections 5, 10 and 12; `planning/PHASES.md`
P3 and P7.

**What this is:** the deterministic building blocks of the evidence system, proven on invented
data: records and identities, passages, a query gate, evidence-span labels, metrics, and the
delivered-evidence prototype.

**What this is not:**
- no search engine, database, tokenizer or real literature;
- no generated answers;
- the supplied rankings are fixture inputs, so nothing here shows retrieval quality or G6
  readiness.

## Module map (`src/retrieval/`)

| Module | Public API | Purpose |
|---|---|---|
| `records.py` | `canonical_bytes`, `identity_digest`, `validate`, `make_work`, `make_revision`, `verify_revision`, `make_event`, `verify_event`, `replay_events`, `make_rights`, `verify_rights`, `may_index`, `may_display`, `may_redistribute`, `answer_support_eligible`, `build_corpus`, `verify_corpus_manifest` | Identity (recomputed on load), schema checks, event replay, fail-closed rights, corpus assembly with link and hash verification |
| `passages.py` | `normalize_paragraph`, `to_original`, `make_representation`, `verify_representation`, `verify_offset_map`, `verify_representation_source`, `sentence_spans`, `chunk_config`, `make_passages`, `verify_passage` | Normalization with bound, validated offset maps; deterministic sentence chunking |
| `query.py` | `normalize_question`, `classify_scope`, `make_query`, `verify_query` | Allowlisted finding, preserved question, keyword refusal rules |
| `labels.py` | `make_label_set`, `verify_label_set`, `direct_spans`, `contains`, `passage_grade`, `gold_passages`, `gold_works` | Span labels and complete-containment support |
| `metrics.py` | `recall_at_k`, `reciprocal_rank`, `collapse_to_sources`, `make_ranking`, `verify_ranking`, `verified_corpus_records`, `evaluate`, `span_hit_recall` | Official D-085 metrics on verified, bound inputs; provisional span-hit metric |
| `context.py` | `pack`, `delivered_evidence`, `SyntheticWordCounter`, `FixtureCounts` | Whole-passage packing and delivered-evidence scoring from verified records (proposal) |

The 12 JSON Schemas live in `docs/capstone/contracts/retrieval/`. See its README.

## Identity and hashing

- **Canonical JSON:** UTF-8, sorted keys, compact separators, `allow_nan=False`, trailing newline.
  This is the same convention as `src.data.manifest_records`.
- **Identity payloads** allow only strings, integers, booleans, null, lists and objects. Floats are
  rejected there, so an ID never depends on float formatting. Finite floats are allowed only as
  ranking scores. NaN and Infinity are rejected everywhere.
- **IDs:**

  | Record | Identity |
  |---|---|
  | Revision | `rev:` + hash of (work, content hash) |
  | Event | `evt:<source_file>:<ordinal>` (its position) |
  | Representation | `repr:` + hash of (revision, kind, normalization version, text hash, section/paragraph geometry, and per paragraph the original length, original SHA-256 and offset map) |
  | Passage | `psg:` + hash of (representation ID, representation hash, start, end, chunking config) |
  | Rights | `rights:` + hash of its decision content |
  | Query | `qry:` + hash of (finding, original and normalized question, policy versions, outcome) |
  | Corpus | `corpus:` + hash of (allowed origins, ordered member inventory) |
  | Ranking | `rank:` + hash of its full content, including the eligibility policy and eligible count |
- **No timestamps or filesystem paths** in any identity.
- **No circular IDs:** passages never name a corpus; the corpus ID is computed from its members.
- **Identities are recomputed on load,** not only at construction: event replay, corpus assembly,
  permission checks (`may_index`/`may_display`/`may_redistribute`), evaluation and delivered-evidence
  scoring all call `verify_revision`, `verify_event`, `verify_rights`, `verify_representation` and
  `verify_passage`. A record whose content changed while it kept its old ID is refused (R1, R4).
- **What changes which identity:**
  - changed text changes the revision, representation and passage IDs;
  - a changed chunking config changes passage IDs, and so the corpus ID;
  - a changed rights decision changes the rights ID (and so the corpus ID) and can change membership;
  - a changed offset map, original length or original paragraph hash changes the representation ID.

## Records and relationships

- **Work, revision, event and representation are separate records.** Repeated identical content
  through distinct events is allowed.
- **Duplicate logical records are refused,** including byte-identical ones: works, revisions,
  representations and rights decisions (one per representation), and passages. Nothing is collapsed
  silently.
- **Event replay:** `replay_events` applies events in file-sequence and ordinal order. The last event
  wins, and a delete removes the work.
- **Refused inputs:** unknown files, duplicate positions, unknown revisions, and revisions of another
  work.
- **`build_corpus` checks** every link and content hash: representation, passage slice, work,
  revision and rights. Every input passage becomes a member or a reason-coded exclusion:

  | Exclusion reason | Meaning |
  |---|---|
  | `origin_not_allowed` | Real origins are refused by default in P3 |
  | `work_deleted` | Removed by a delete event |
  | `not_final_revision` | A later event replaced this revision |
  | `work_quarantined` / `work_excluded` | Work status |
  | `work_retracted` | Retraction notice |
  | `rights_not_indexable` | Rights do not allow indexing |

  The counts reconcile exactly, and `verify_corpus_manifest` re-checks that they do (members and
  exclusions sorted, unique and disjoint). Duplicates and dangling references raise errors; nothing
  is repaired.
- **Rights:**
  - Retention, local text storage, local embedding, display and redistribution are five separate
    booleans that must all be present.
  - Indexing needs `local_text_store` and `local_embedding` under an `allowed`/`restricted_local`
    decision. Display is checked separately.
  - Retracted, quarantined or excluded works never become answer support.
  - This is not a legal interpretation engine; rights records are fixture decisions.

## Normalization, offsets and chunking

- **`prowl-norm-v1`, per paragraph:**
  - refuse control and format characters (zero-width, bidi);
  - Unicode NFC, per base-character cluster; a paragraph where that differs from whole-string NFC
    (for example conjoining Hangul) is refused;
  - collapse whitespace runs to one space and trim.

  No case folding, paraphrase or translation, so negation is preserved.
- **Joining:** paragraphs and sections are joined with `\n\n`.
- **Offsets:** half-open Unicode code points into the normalized representation text. Each paragraph
  keeps an `offset_map` of `[norm_start, norm_end, orig_start, orig_end]` segments, so `to_original`
  maps a normalized range back to the original. It also keeps `original_length` and
  `original_sha256` of the original paragraph. All three are in the representation identity (R4).
- **Offset-map rules (`verify_offset_map`):**
  - exact coverage of the normalized paragraph, from 0 to its length, with no gap or overlap;
  - non-empty, non-inverted segments;
  - original coordinates strictly increasing and contiguous between segments; only leading and
    trailing whitespace may be unmapped;
  - bounds within `[0, original_length]`;
  - canonical merged form;
  - a length-changing segment must be one collapsed space or one NFC cluster.

  These structural rules cannot prove *which* original characters a segment came from.
  `verify_representation_source(rep, sections)` proves it by rebuilding from the original paragraphs
  and requiring an exact match; the P5 parser should call it wherever originals are available.
- **Paragraph order:** paragraphs appear in text order, grouped by section in section order, with
  indices 0..n-1 per section, and each section range equals its paragraphs' span.
- **Sentences (`prowl-sent-v1`):** split after `.`/`!`/`?` (plus closing quotes or brackets) when a
  space is followed by a non-lowercase character. Abbreviations can split early; that moves chunk
  boundaries, never text.
- **Chunking (`prowl-chunk-v1`):**
  - Sentences are packed greedily within one section up to `max_chars`, measured on the exact slice.
  - An oversized sentence stays whole and is flagged.
  - `overlap_sentences` trailing sentences start the next passage, but only if that passage can
    still add a new sentence, so no passage is redundant.
  - Passages never cross sections or works.
  - The passage text is always exactly the referenced slice.

## Query gate (fixture-level)

- **Finding:** allowlisted enums only (`CT`, `pancreas`, task, finding state). Coarse count/size bins
  and warning categories are provisional fixture values until Plans 05/08 define them.
- **Rejected:** unknown keys, identifiers, dates, paths, report text, masks, ground truth and D-208
  score bands.
- **Question:**
  - at most 500 characters; control and format characters refused;
  - the original is preserved exactly;
  - an NFC plus whitespace-collapsed form is used only for matching.
- **Refusal rules (`prowl-scope-kw-v1`):** keyword/regex rules for RF1-RF4 and RF6-RF9, plus
  identifier/path detection. RF1-RF3 require a case-specific referent ("this patient/lesion/case"),
  so questions about study populations stay answerable.
- **Limitation:** keyword rules demonstrate the contract on fixtures. They do not prove semantic
  safety or anonymize free text. RF5 (unsupported claims) belongs to the future response layer and is
  not implemented here.

## Labels and metrics

- **Label spans:** (representation ID, representation hash, start, end, grade, concept IDs).
  - A hash mismatch makes the label stale; it must be remapped into a new label version.
  - Uncertain spans are excluded from primary gold.
  - An answerable question needs at least one direct span and at least one declared concept.
  - Refusal questions carry neither.
- **Direct support = complete containment.** Partial overlap counts only as partial evidence.
- **Official metrics (D-085):**
  - **Rankings:** exactly `min(50, eligible_count)` items, ordered by score and then passage ID.
    `eligible_count` is persisted and bound to the corpus under the P3 policy `all_corpus_members`
    (every member is eligible; P3 has no filtering, and none is invented). `eligible_pool_exhausted`
    is set exactly when `eligible_count` < 50. Counts must be plain integers, not bool or float (R5).
  - **Binding (R2):** `verify_ranking` requires the query record; the query must be accepted and
    match. `evaluate` takes `queries` (question → query) as well as `rankings`, and checks that each
    ranking names its own question, query, configuration and corpus. Question IDs must be unique;
    rankings or queries for unknown questions are refused. Before scoring, every representation and
    every member passage is re-verified (identity, exact slice) and must match its manifest entry.
    Rankings for refusal-labelled questions are verified but not scored.
  - **Source level:** collapse to the first occurrence of each work, then renumber.
  - **Passage level:** relevance is configuration-specific. A question with no passage fully
    containing a direct span is excluded from passage means and counted in `n_undefined`.
    Passage-level scores are marked `within_configuration_only`.
  - **Edge cases:** an empty answerable set gives `null` with a reason, never NaN or 0; `k` must be a
    positive int and never a bool; duplicate IDs fail.
  - **Query binding:** every ranking is bound to its query record; a refused query can never carry
    an evidence ranking.
- **Proposed span-hit recall@k:** distinct direct spans fully contained in at least one top-k
  passage, over distinct spans. Reported under `provisional`, with status
  `proposed_provisional_not_official`.

## Delivered-evidence prototype (proposal)

- **Inputs (R3):** the question's label set, its accepted query, the ranking, the corpus manifest,
  passages, representations and rights. The ranking is verified against the question, query and
  corpus; passages and representations are re-verified against the manifest; the ranked passages are
  taken from the ranking, never from a caller-supplied list. The result records `query_id`,
  `ranking_id` and `corpus_id`.
- **Display permission** is enforced separately from indexing. A ranked passage whose (verified)
  rights decision does not allow snippet display is skipped with `display_not_permitted` and a null
  token count, and never delivered.
- **Packing (`prowl-pack-v1`):** add whole passages in rank order when they fit; otherwise skip and
  continue. Never truncate.
- **Counts** come from an injected, named counter. `SyntheticWordCounter` (labelled
  `synthetic_counter`) or validated fixture counts. **Not a model tokenizer.** Counts and the budget
  must be positive ints. A text counter only ever receives the verified passage slice; any other
  counter kind is refused before it sees text.
- **Scoring:** a span is delivered only if it is completely contained in a packed passage. Spans and
  concepts are counted once each.
- **Budget:** the 2,000-token budget is the provisional D-265 setting.

## Open integration decisions (for Codex / Quinton)

1. Whether these schemas join the shared contract set (and `tests/test_contracts.py`), or stay
   lane-local until P4b.
2. The PostgreSQL mapping (P4b): the per-configuration embedding tables and the published-build view
   follow SCOPE 5.3; these JSON records are the canonical artifacts it loads from.
3. The real finding bins and warning categories (Plans 05/08).
4. The D-085 amendment for span-hit recall and delivered-evidence metrics (still a proposal).
5. A production tokenizer for part B (a pinned reference/generator tokenizer; needs authorization).
6. Real-text normalization: PubMed XML section mapping, abstract labels and structured abstracts.
   This needs the P5 parser packet.
