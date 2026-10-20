# Reliability closeout — October 20, 2026

**Outcome:** W03-02's bounded startup/recovery scope is complete, with the historical exit-code-2
cause explicitly unresolved. This is not a claim of permanent storage reliability.

## Investigation and disposition

The retained October19 PostgreSQL logs show lost access to database paths, bad descriptors and an
invalid data-directory lock file immediately before shutdown. October20 host checks found the correct
mounted drive and existing directories, while Docker rejected their bind path. Docker restart restored
access, followed by automatic recovery of the existing database. See the
[readiness report](WEEK3-DEMO-READINESS-2026-10-20.md) for those observations and the UI repair.

The October18 backend exit-code-2 events lack a causal diagnostic in the retained log windows.
No source evidence establishes OOM, corruption, a query defect or the same mount failure as their
cause. They remain **unexplained historical events**, not repaired defects. Current container state
reports no OOM, but it cannot rule out every historical event.

Disposition: retain the original failures and use the recurrence procedure below. Do not repeatedly
restart a failing service, delete its data, reload the corpus, or describe a healthy smoke check as
proof that the old cause is fixed. This satisfies the card's explicit “resolve or disposition”
criterion while preserving the risk in Week 3's quality review.

## Repair

`scripts/retrieval/direct_corpus.py` previously captured and discarded Compose stderr at the CLI
boundary. A failed start now returns a bounded diagnostic identifying the Docker error and advising
inspection of the existing container/drive. Timeout reports **unknown container state**, not a stopped
or ready database. Neither path retries automatically or proceeds to database initialization.

Six focused tests pass: failed start preserves the bind diagnostic and never connects/initializes;
timeout does not retry; success preserves the dedicated project and result; missing/non-UTF8/oversized
diagnostics stay usable and bounded. No ingestion/selection/model logic changed.

## Actual recovery verification

Two clean stop/start cycles were performed using the existing checked CLI:

1. **Retained failed harness attempt:** stop and restart succeeded, but the outage query omitted the
   API schema/UUID and returned400. This was a harness error, not evidence of correct backend-outage
   handling. The `finally` recovery restored the service. No model call.
2. **Corrected attempt:** admitted the full request and first verified its healthy baseline. Stop
   succeeded; the valid query returned503 with the explicit unavailable error. Restart succeeded.
   The repeated query returned200 and its complete payload exactly matched the baseline.

Read-only canonical inventory checks before/after matched all **1,179 passages**. The first attempt's
initial inventory also equals the final inventory. Existing container identity remained the same;
XML-Adventure's container identity, start time and running state were unchanged across both cycles.
No database rebuild, corpus reload, model call or unrelated-container restart occurred in this test.
The corrected post-recovery query took0.397seconds; this is one observation, not a performance result.

Receipts:

- `outputs/prowl/reliability-closeout-20261020/`: first failed harness and successful recovery.
- `outputs/prowl/reliability-closeout-20261020-attempt2/`: admitted cases, complete receipt and DB logs.

The earlier 50 UI checks/build and real answer/citation check remain valid for unchanged UI code;
they were not repeated. `/literature-search/health` identifies the loaded policies and HTTP service;
a successful real source query and canonical inventory are the backend-readiness evidence.

## Operating and recurrence procedure

Use the [current startup commands](WEEK3-DEMO-READINESS-2026-10-20.md#current-operation).
Check existing listeners before launch. Before drive removal: stop the literature API, then the
dedicated database with the checked stop command; confirm the container is stopped before ejecting.
Leave unrelated containers alone.

If the database exits again:

1. Preserve the timestamp, bounded Docker log window and container state (exit/OOM/restart details).
2. Verify the drive's mounted UUID and existing data path; never create a substitute directory.
3. Distinguish missing/stale sharing from a live PostgreSQL error. A Docker restart can affect other
   projects; inventory their running state and restore it if a restart is necessary.
4. Make one reviewed recovery attempt only when identity/resource checks pass. Recheck canonical
   inventory and a real source query; stop on any mismatch or repeated unexplained exit.
5. Reopen W03-02 with that evidence. Block candidate promotion until the recurrence is dispositioned.

No automatic watchdog or restart loop was added. Historical root cause, power-loss durability and
arbitrary drive disconnection remain unqualified. The live policy remains `source-record-answer-v1`;
new volume selection is a separate offline development task.
