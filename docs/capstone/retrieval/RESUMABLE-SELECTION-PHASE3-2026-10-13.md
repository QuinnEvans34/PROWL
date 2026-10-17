# Resumable selector Phase 3 — ranking and verified exports

October 13, 2026. Implemented for review; synthetic evidence only, no real selection run.
Parent: [design](RESUMABLE-SELECTION-DESIGN-2026-10-13.md).
Previous: [Phase 2](RESUMABLE-SELECTION-PHASE2-2026-10-13.md).
Tracking: [W02-06](https://trello.com/c/LxvwMa3s).

## Delivered behavior

The separate selector now continues from evaluation through global ranking, export, verification
and publication. `--evaluation-only` retains an explicit development stop at the Phase 2 boundary.
Earlier Phase 2 descriptions of the default stopping behavior are historical.

Ranking creates indexes after evaluation and commits the at-most-500 WORKFLOW-only winners with
the checkpoint in one transaction. Sort priority is concept count descending, year descending,
PMID length then lexicographic PMID. Saved winners are checked against the ledger on continuation.
Pre-cap evaluation rows remain unchanged; serialization applies the existing capped-out reasons,
disposition and stratum rules. No SQLite integer conversion of PMIDs.

Each export receives a committed attempt ID and separate `attempts/<id>/` directory. Interrupted
exports stay preserved; resume starts a new export from the saved ledger and winners without
parsing source XML again. Files are flushed/fsynced, then sizes, SHA256s and reconciliation counts
are committed as an export receipt before the checkpoint advances to verifying.

Verification reads the files back against deterministic ledger output, checking every record byte,
candidate membership/order, hashes, lengths and counts. Before publication it rechecks source,
policy, implementation, admission and MeSH identity. It stores the exact proposed summary in
SQLite, renames the verified pair into place, syncs directories, and publishes summary.json last.
A crash between pair renames resumes verification using one final and one attempt file. A crash
after summary publication but before the complete checkpoint validates the saved summary and
finishes the checkpoint. Conflicting, missing, truncated or tampered artifacts fail closed.
Completed resume validates and returns the same summary without overwriting valid outputs.

Summary includes identity, applied-ledger digest, counts, output hashes/bytes, attempt history and
resource settings. Selection remains stage 1 with official_selection_frozen=false,
rights_qualified=false and sampling_performed=false. This is no evidence-quality or rights approval.

## Validation

Command:

```sh
.venv-prowl/bin/python -m pytest -q tests/retrieval/test_resumable_selection.py tests/retrieval/test_streaming_corpus.py tests/retrieval/test_topic_selection.py
```

Final result: **84 passed**. Whitespace validation passes. Existing replay, old selector, policy
and citation-lookup source files remain unchanged. No external corpus was read or modified.

New tests cover:

- Byte-identical exports and identical counts versus the original selector, including >500
  WORKFLOW candidates, tied rankings, books, deleted records and a PMID larger than 64-bit range.
- Failed rank transaction rollback; saved winner corruption refused.
- Interrupted export retained and restarted without XML parsing; nested attempts count toward
  the output-directory budget.
- Faults before the second final rename, before summary rename, and after summary publication
  but before checkpoint completion.
- Truncated/tampered exports and modified summaries refused; source receipt mutation during
  verification prevents publication; empty corpus and completed resume are idempotent.
- SQLite temporary-directory setting restored after the isolated run.

An intermediate final-source test appended an invalid blank JSONL record and correctly refused
it during parsing rather than reaching the expected identity error. The fixture now changes valid
JSON whitespace to exercise the intended hash-mismatch path. Earlier 80-check passes and the
83-pass/1-assertion-failure run precede the final result.

## Resource limits and next review

Resource checks now recurse through retained attempt directories. SQLite sorting uses FILE temp
storage directed to the output volume through a checked temp_store_directory setting, restored
on exit. This SQLite setting is process-global: use the isolated single-worker CLI, not concurrent
selectors embedded in a shared Python process. Unsupported SQLite builds fail rather than silently
spill somewhere else. The two database connections retain the configured cache limits and main
ledger page cap; journaling and FULL synchronous behavior remain enabled.

SQLite may unlink spill files while they are still open. They consume free disk space, but a
recursive directory walk cannot include their bytes in the output cap. The free-space floor still
checks the volume; neither periodic check is an exact hard growth bound. Phase 4 must measure and
resolve temporary-spill accounting/headroom before a real launch. Do not present the directory cap
as a complete disk-use guarantee or the cache setting as a hard RSS cap.

The current fault tests inject exceptions at transaction/publication boundaries; actual subprocess
signals, abrupt kills, broader identity/failure tests and performance measurements remain Phase 4.
Internal invocation logging, actual space sizing, seed review/freeze and the concrete real-run packet
remain required before Phase 5 execution. No real admission packet or new corpus job was created.

Next: Phase 4 — expanded recovery validation and bounded performance/resource evidence. Review
this phase before proceeding; no automatic real run follows these tests.
