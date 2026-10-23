# Reliability closeout — October 20, 2026

**Outcome:** W03-02's bounded startup/recovery scope is complete, with the historical exit-code-2
cause explicitly unresolved. This is not a claim of permanent storage reliability.

## October22 bounded development disposition

The newer October22 incident is a confirmed stale Docker share: the Mac volume UUID/files
matched, while Docker rejected that same mount as not a directory. One start was refused;
the user then explicitly approved restarting Docker and restoring XML-Adventure. Both were
restored. XML-Adventure ran for about14minutes and later exited normally (exit0); that later
state is left untouched rather than assuming it needs another restart.

After PostgreSQL recovery, exact inventory/vector readiness passed. The final quality candidate
completed104HTTP requests (51model compositions) with no service failures or fallback. Retained
post-recovery logs contain no new backend exit/FATAL/PANIC; the startup WAL end-of-log message
is preserved. Earlier failed readiness and composition attempts are retained, not counted as
passing. See [October22 quality evidence](RAG-QUALITY-2026-10-22.md).

Disposition: permit the bounded local development-preview promotion after its quality/UI checks;
retain the external-drive dependency and this recurrence procedure. Stop the literature database
before disconnecting the drive. Do not declare the unexplained October21 exit2 cause fixed or
claim durability/uptime acceptance. W03-02 remains open for operational reliability; this explicit
disposition supersedes its blanket candidate-promotion block for the checked October22 version.

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


## October21 recurrence — reopened

The October20 bounded recovery result above remains historical evidence. On October21 at
22:15:42 UTC, literature startup lost its PostgreSQL backend during the database-size check;
Docker logs record backend exit2 and automatic database recovery. The mounted drive UUID and
existing data directory matched. One bounded literature-service restart succeeded. A source-only
query through the UI proxy then returned503 at22:17:43 UTC, alongside another backend exit2.
No further query/restart attempts followed this repeated failure.

The health endpoint returned200 but does not verify a live database query. A separate read-only
connection/size/canonical-inventory diagnostic afterward passed:14 sources,1,179 passages,41 batches,
43,022,003 database bytes; content SHA256
`eae607b2aaeec5e55bb15a71cd0cd49b54e2c110f2989a2b21de4d052d673fd8`.
This does not establish that search works or isolate the cause. Docker reports OOMKilled=false and
RestartCount0; backend recycling is visible in its logs despite the container remaining running.

W03-02 is reopened for recurrence disposition; candidate promotion is blocked. Preserve the corpus
and diagnose the demonstrated database failure before further assistant expansion. Review recording
is independent and remains available. No training, real-case inference or LLM generation was requested;
the source-only path can invoke the existing CPU embedding encoder. Unrelated containers were untouched.

Private evidence: `outputs/prowl/review-navigation-20261021/database-recurrence.log`,
`database-recurrence-state.json`, `database-recurrence.json`, and `database-stage-check.json`.
The source request's503 status was observed, but its body was not retained because the verification
harness raised an HTTPError. No response-body reconstruction or fresh query was used to replace it.
Trello's recurrence comment was confirmed; list movement is tracked separately in the Week3 plan.


## October21 investigation and readiness repair — operational, cause still open

Quinton authorized addressing the recurrence. Before code changes, a staged read-only size/inventory/
exact-vector query passed, as did10 fresh database connections and the exposed source question through
Vite. Thus the intermittent failure was **not reproduced**, and those successes cannot be attributed
to this patch. Container memory and PID-limit event counters showed no limit/OOM events; no specific
storage, pgvector, signal, or client cause is established. PostgreSQL17's
[termination handler](https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/tcop/postgres.c)
can exit2 for SIGQUIT, but our retained logs do not prove that path or a signal sender. No speculative
image upgrade, storage migration, corpus rebuild or automatic retry was made.

Two confirmed defects were repaired: `/literature-search/health` now checks the configured mount,
resource limits, database size, exact frozen inventory and one stored-vector self-distance, returning
503 when unavailable. A200 response identifies `backend=checked` and `generation_checked=false`;
it is a point-in-time backend check, not an Ollama/answer-quality or future-availability guarantee.
No query embedding or generation is invoked by this check. Request/startup stages retain timestamp,
exception type, SQLSTATE and backend PID in local diagnostics without recording question, SQL,
exception message or credential text. Query/inventory validation remains mandatory; no retry is added.

The dedicated Compose service now logs connection/disconnection and verbose error metadata with
application/PID/SQLSTATE correlation. Statement/parameter logging was not enabled; existing two10MiB
Docker log limits remain. The client identifies itself as `prowl-literature`. One controlled container
recreation applied the settings while preserving the original bind directory and exact canonical
inventory. XML-Adventure's container identity/start time were unchanged. The first API launcher
incorrectly resolved the virtualenv Python symlink and failed on missing jsonschema before DB/model
work; this attempt is retained, and the corrected launcher uses the virtualenv path directly.

38 focused HTTP/readiness/lifecycle tests pass, including unavailable/recovered backend responses,
no retries/generation, metadata privacy, size cap, inventory mismatch and invalid-vector refusal.
Live proxy checks passed: backend health200 in0.358s, source query200 in0.365s and one local-model
inflammation-versus-cancer answer summarized in6.453s. All six citation references match their five
retrieved source passages. Manual response inspection confirmed the smooth-versus-abrupt duct
contrast, MRCP qualification, calcification context, cancer-favoring findings and explicit no-single-
feature limitation. This is an exposed smoke check, not independent acceptance or a latency benchmark.
No new backend exit appeared in the retained post-restart window.

Private evidence: `outputs/prowl/database-repair-20261021/` contains the staged query, fresh-connection
results, pre-change source result, restart/inventory receipt, both launcher logs, live verification and
bounded PostgreSQL log/state. W03-02's move to Week3 In Progress and latest evidence comment are
confirmed. Its historical completion checkbox remains stale because the connected write tool does
not expose clearing it; the card is operationally **open**. Root cause/recurrence disposition and
candidate-promotion gate remain open. The local UI is usable now; readiness/diagnostics are repaired,
but a permanent database fix is not claimed. No training, inference or held-out evaluation occurred.

## October22 — orphan-process restart reproduced and contained

The answer diagnostics encountered two further recycle events at 23:58:16 and 00:06:49 UTC.
Each logged an unexpected child exit2, followed by termination of all PostgreSQL workers. The
container remained running and OOMKilled was false. These are service failures, not answer failures.

A controlled experiment used the already-pinned PostgreSQL/pgvector image in two temporary,
network-disabled containers with 128MiB tmpfs data, 256MiB memory and one CPU. No project data,
credentials or published ports were used. In the first, PostgreSQL was PID1. A detached shell child
(`(sleep 1; exit 2) ... & exit 0`) reproduced the same sequence at00:08:25 UTC: child PID81 exited2,
all workers terminated, automatic recovery. With Docker `--init`, PostgreSQL was PID7 and the same
orphan exit caused no restart; readiness remained successful. Both probe containers were stopped
and removed. Probe logs were observed in the tool transcript, not saved as standalone artifacts.
A separate `ps` inspection failed because that binary is absent from the image; it did not affect
the orphan/readiness test.

This behavior follows PostgreSQL17's [child cleanup implementation](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/postmaster/postmaster.c):
unrecognized child exits reach CleanupBackend, which handles an exit other than0/1 as a crash before
checking BackendList membership. A PID1 postmaster can therefore mistake an adopted orphan for a
failed database backend. This reproduces a concrete failure mechanism; the original recurring child
was not traced, so its exact creator remains unproven. The previous shell healthcheck and equal
three-second inner/outer timeouts were a plausible source, not a proven attribution.

`compose.literature.yaml` now uses `init: true`, an exec-form healthcheck, pg_isready's own two-second
limit and a ten-second outer limit. The unchanged dedicated service was recreated once with the
existing bind path. Source/model/credential files were not changed. The API then verified the exact
14-paper/1,179-passage/41-batch inventory and vector probe. Host mount, source content hash and
published port remain unchanged. No unrelated container was restarted. Continued answer testing
will check for recurrence under model load; this is not an unlimited uptime guarantee.
