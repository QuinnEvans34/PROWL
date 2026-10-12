# Topic-selection implementation — v0.1 current

October 10, 2026. Continues Quinton's request to implement the approved topic-selection rules from
the old-chat handoff. Governing text: [SEARCH-AND-SELECTION.md](planning/SEARCH-AND-SELECTION.md),
policy v0 / revision 9. That policy text and its terms are unchanged.
Tracking: [W01-31](https://trello.com/c/nMzTPlCq).

October 10 follow-up: Quinton approved journal records for the first corpus. The current engine
uses [v0.1](planning/SEARCH-AND-SELECTION-V0.1.md), the preserved v0 rules plus explicit book-record
exclusion. Book records stay in the catalog and reconciliation counts; deleted books remain deleted.
Identity records include `policy_version: v0.1` and both policy document hashes.
Validation after this amendment: 53 focused tests passed, including live/deleted book accounting,
book-to-journal re-addition, journal-to-book replacement and invalid book identity refusal.
The 48-test result below records the earlier v0 implementation. No real selection was run for v0.1.

## Delivered

- `src/retrieval/topic_selection.py` implements stage-1 bibliographic selection: exact matched XML
  paths, NFKC/whitespace/casefold normalization, `str.isalnum()` tokens, case-sensitive CT/MDCT/CECT/AI,
  per-unit phrases, listed wildcard/hyphen rules and reader-study concept deduplication.
- MeSH loader requires the 2026 descriptor input and resolves every named descriptor exactly once.
  Tree explosion requires equality or a dot-delimited descendant. Animals/Humans remain exact check
  tags. Source SHA256, resolved UIs and tree numbers are recorded. Invented test descriptors are
  explicitly labeled synthetic; real IDs are not guessed. External entities and unsafe XML are refused.
- Exact publication types, retraction links, animal-only, language and ordered date rules preserve
  all applicable reason codes. Deletion takes precedence. Missing dates/language do not exclude;
  future years are flagged. CORE qualifier presence is informational, not an inclusion condition.
- The WORKFLOW-only cap applies after hard exclusions. Ordering is W-concept count descending,
  year descending with undated last, then numeric PMID ascending. There is no availability-based refill.
- Per-record outputs retain extracted metadata, block/branch matches, dispositions, reasons and
  source provenance. Counts cover the full preview universe, including deleted PMIDs, and report
  overlaps, publication types, qualifier subgroups and no-MeSH candidate indexing status.
- The candidate list is numeric-PMID order, one PMID plus newline per line, with its SHA256.
  Records include policy/code/MeSH/runtime and catalog input identities.
- Catalog v2 preserves deletion tombstones and last-known metadata. Old v1 output is read-only for
  search; building into it refuses. Rebuild at a new path instead of inventing missing deletion history.

## Preview entry point

```sh
.venv-prowl/bin/python scripts/retrieval/preview_topic_selection.py \
  --catalog /path/to/new-v2-catalog.sqlite \
  --mesh-2026 /path/to/verified-desc2026.xml \
  --cutoff-listing-year 2026 \
  --output /path/to/new-selection-preview
```

This is a local, bounded development preview, not the official selection freeze. It accepts at most
10,000 total live-plus-deleted records and 64 MiB cumulative retained XML; exceeding either stops
without producing a truncated candidate set. These are input bounds, not a whole-process RSS guarantee.
The cutoff year must come from the snapshot's final update listing date. Verify the actual MeSH 2026
source before a real run; a CLI filename/year argument does not establish publisher authenticity.

The command opens a consistent read-only catalog snapshot and writes into a new directory:
`records.jsonl`, `candidate-pmids.txt`, and `summary.json`. Existing output is not overwritten.
`summary.json` is written last; an interrupted export without it is incomplete and must not be consumed.
No sampling salt, seed freeze, held-out labels, full-text rights, embeddings or database loading is
created or inferred. Candidate without an abstract remains a stage-1 candidate.

## Validation and limits

53 focused tests passed with invented inputs, including the approved journal-first amendment:

```sh
.venv-prowl/bin/python -m pytest -q \
  tests/retrieval/test_topic_selection.py tests/retrieval/test_pubmed_catalog.py
```

Tests exercise applicable section-12 stage-1 oracles (historical E5b excluded), token/unit boundaries,
dates and metadata retention, MeSH resolution/explosion, exclusion precedence, workflow sorting/cap,
candidate hashes, deletion/re-addition/rollback, old-catalog refusal and end-to-end preview export.
E27's stage-1 invariant is tested; its representation/rights decision belongs to stage 2.
No real literature was selected or exposed for labeling in this implementation turn.

The initial v0 gap is resolved by the approved v0.1 amendment: `PubmedBookArticle` receives
`record_type_excluded`, with no guessed journal-field mappings. Known books, excluded books and
deleted books are counted separately. Unknown record types and invalid book identities still stop.
Book inclusion remains a possible future policy change.

MeSH 2026 acquisition and real-file compatibility are now
[verified](MESH-VERIFICATION-2026-10-10.md), including every required descriptor and hierarchy group.
The new [streaming path](STREAMING-CORPUS.md) has passed differential checks and real-file capacity
trials; its first 1,200-file import is running. The old preview retains its ten-file/2 GiB limits.
Next: finish acquisition and ordered replay, then run full selection. Seed verification/freeze and reserve/exposure controls must be settled before selection evaluation.
Then run versioned selection and perform the separate representation/rights step before retrieval/UI use.
PostgreSQL plus pgvector remains the selected vector store; this preview does not replace it.
