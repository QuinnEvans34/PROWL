# Resumable selector Phase 2 — evaluation checkpoints

October 13, 2026. Implemented for review; no real corpus selection launched.
Parent: [Phase 1 design](RESUMABLE-SELECTION-DESIGN-2026-10-13.md).
Tracking: [W02-06](https://trello.com/c/LxvwMa3s).

## Delivered

- New `src/retrieval/resumable_selection.py` evaluates live documents followed by deleted records
  using unchanged Expat metadata and selection-policy functions. Streams one XML record at a time.
- New `scripts/retrieval/select_pubmed_corpus.py` provides explicit fresh/resume CLI, verifies the
  actual macOS catalog volume UUID and handles SIGINT/SIGTERM through rollback/cleanup.
- Exclusive output lock and shared catalog lock; source read-only transaction. Symlinks, foreign
  output members, incomplete replay, nonempty source journal/WAL and mismatched receipts refuse.
- SQLite stores binding, evaluated rows and checkpoint. Batch commits include cursor, counts,
  stage, run UUID, commit sequence and processing time. Count is never used as a rowid.
- Resume verifies identities and ledger/checkpoint invariants before continuing. Already committed
  records are skipped; unfinished batches roll back. Final evaluation stage is `ranking`.
- Status explicitly says `evaluation_complete_ranking_pending`. No summary, selected IDs or export
  files are produced. A second resume at that boundary validates and returns without parsing XML.
- Resource checks retain the specific deadline/disk cause through SQLite interruption. Suggested
  cache is configurable; output page cap, FULL synchronous and DELETE journal mode remain enabled.
  Initial limits match the design: 12h, 256GiB output, 400GiB floor, 32MiB per-connection cache.

Old replay, selector, topic policy and seed-lookup producing files are unchanged.

## Admission interface

Required CLI arguments: `--catalog`, `--mesh-path`, `--mesh-sha256`, `--output`, `--receipts`,
`--packet-path`, `--expected-volume-uuid`, `--cutoff-year`; add `--resume` only for continuation.
Optional resource flags: `--hours`, `--max-gib`, `--free-gib`, `--cache-mib`.
The API accepts batch size (default 1000) and commit interval (default 10 seconds).
The traversal uses an ordered SQLite cursor after the last committed rowid; it does not materialize
an XML batch. This implements the design's keyset seek without repeated LIMIT queries.

The JSON admission packet has version `selection-admission-v1` and an `evidence` mapping with
`seed_freeze`, `information_needs`, and `reserve_exposure`. Each entry has an absolute `path` and
`sha256`. Packet bytes and evidence bytes are bound; human review establishes their meaning.
No real admission packet was created. Tests use clearly invented evidence.

Resume binds catalog stat/schema/metadata/volume, applied ledger and receipt hashes, replay identity/
completion, MeSH/policy/year, local dependency bytes, runtime versions and admission packet. It does
not rehash the entire catalog or prove every page cryptographically. Mutating source data with tools
that ignore the shared lock remains outside that lock's protection.

## Verification

Command: `.venv-prowl/bin/python -m pytest -q tests/retrieval/test_resumable_selection.py tests/retrieval/test_streaming_corpus.py tests/retrieval/test_topic_selection.py`.
Final result: 69 passed. Tests are synthetic/local and do not access the external corpus.

New coverage includes exact uncapped semantic rows against the prior selector, missing rowids,
empty tables, rollback of a partial batch, committed-prefix skipping, crash immediately after table
transition commit, status-write failure after a successful commit, completed-evaluation idempotence,
changed cutoff/volume/catalog/evidence, checkpoint corruption, source/output lock refusal, receipts,
space floor, malformed XML repeated refusal, symlinks, decimal storage limits, nonfinite bounds,
deadline reporting, durability settings and CLI help.

A CLI help test initially failed because argparse wraps prose across lines; the assertion now
normalizes whitespace. Earlier 65-check pass and the intermediate 68-pass/1-failure run preceded
the final corrected suite. No production behavior was changed for the wrapping assertion.

## Review boundary and next phase

Phase 2 completes evaluation recovery only. Ranking, global cap winners, indexes, exports,
verification/publication and final source recheck belong to Phase 3. Phase 4 still requires actual
subprocess signal/abrupt-kill fault tests, extended identity/fault matrix, and bounded performance/
resource measurements; current injected exceptions establish transaction behavior, not physical
power-loss qualification. Whole-ledger quick_check/count verification is intentionally conservative
and may take time on a large resumed ledger; measure before optimizing.

The separate CLI is not a real-run launch packet. Internal invocation logs, temporary-sort-space
accounting and measured output sizing must be finalized with the subsequent stages before real
execution. Current evaluation creates flat output files and no ranking sort. Cooperative resource
checks are not a hard RSS ceiling or an exact disk-growth cap. Raw-data processing and active citation
lookup were not started, stopped or modified by this work.

Next for Quinton's review: Phase 3 — save global ranking and add recoverable exports and verified
completion. Seed review/freeze and the final launch decision remain required before real selection.
