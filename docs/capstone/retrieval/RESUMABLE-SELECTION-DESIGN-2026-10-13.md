# Resumable journal selection — Phase 1 design

Date: October 13, 2026. Status: design delivered for Quinton's review; implementation and real execution pending.
Tracking: [W02-06](https://trello.com/c/LxvwMa3s).
This is engineering Phase 1 within corpus Phase 3, not a restart of the overall AI-expert roadmap.

## Scope and decisions

Keep Expat and the existing `topic_selection.metadata`, `evaluate`, `identity` policy behavior.
Add a separate resumable selector and CLI; leave the completed replay implementation, original
selector, and active citation lookup unchanged. Do not migrate old incomplete selection outputs.
A new run needs a new directory; continuation requires explicit `--resume` on that directory.
No parser replacement, policy tuning, sampling, rights approval, passages, embeddings or training.

Current selector in `src/retrieval/streaming_corpus.py` commits rows every 1,000 records but has
no checkpoint cursor or resume identity. It builds indexes before ingestion and exports directly to
final filenames. Preserve its semantic outputs as the differential reference, not its failure behavior.

## Stage contract

| Stage | Work | Durable transition |
| --- | --- | --- |
| Validate | Acquire locks; validate source, policy, MeSH, implementation and run packet | Initialize identity and checkpoint together in selection.sqlite |
| Evaluate | Stream documents, then deleted records; extract/evaluate each once per committed prefix | Evaluated rows and cursor commit in the same transaction |
| Rank | Build indexes; select global WORKFLOW-only top 500 | Winner set and ranking-complete checkpoint commit together |
| Export | Apply capped-out disposition at serialization; write ordered records and candidate IDs | Finished attempt files and export manifest with hashes/counts |
| Verify | Re-read exports; reconcile ledger counts, order, candidate membership and hashes | Publish summary.json last as the completion marker |

Persisted stages: evaluating_documents, evaluating_deleted, ranking, exporting, verifying, complete.
A stopped process retains its last durable stage; stopped/error is operational status, not a cursor.
Status JSON is informational and may lag a successful transaction. SQLite is resume authority.

## Checkpoint and traversal

`selection.sqlite` contains immutable run identity, evaluated rows, a single checkpoint row,
ranked winners, and export-attempt receipts. Proposed checkpoint fields:

- schema_version, run_id, identity_sha256, stage, commit_sequence;
- last_documents_rowid and last_deleted_rowid (null before the first row);
- committed_documents, committed_deleted, committed_total;
- source row counts and maximum rowids captured during validation;
- ranking_version/winner_count once committed; active export attempt ID once allocated;
- last commit timestamp and cumulative committed processing seconds (diagnostic, not human hours).

Read each source table using `WHERE rowid > ? ORDER BY rowid LIMIT ?`, with an initial query
without the predicate. Never use OFFSET or treat count as rowid. Gaps are valid. Each evaluated
row also records its source table and rowid, with a unique source-position constraint and unique
PMID. A repeated PMID across live/deleted tables is a source inconsistency and stops the run.

Process rows one at a time; do not fetch a batch of full XML into memory. Start with 1,000 rows
per commit and a cooperative 10-second commit interval after a completed record, whichever comes
first. Commit final short batches and end-of-table transitions explicitly. Results, counts, cursor
and commit sequence update atomically; on interruption only the uncommitted tail is repeated.
Resume validates schema, identity and checkpoint/ledger consistency before seeking past the cursor.
No cursor repair by guessing, advancing to MAX(rowid), or skipping a failing record.

Rowids are safe only for the unchanged catalog. VACUUM, replacement, replay updates, or an identity
mismatch refuse continuation even if the logical article set appears similar.

## Identity and source isolation

Hold the catalog's existing writer.lock shared and an output writer.lock exclusive, nonblocking,
for the whole invocation, always in that order. Open catalog read-only in a read transaction;
reject symlink source/output/ledger paths and unsafe preexisting output contents. Locks coordinate
participating tools; they do not protect against arbitrary external writers.

Bind and compare on every resume:

1. Catalog canonical path, external volume UUID, inode, byte size, mtime_ns, schema and metadata;
   SQLite/Python/Expat runtime versions are retained and required to match for initial v1 resumes.
   Device number is recorded diagnostically; UUID is the stable volume identity across remounts.
2. Exact manifest bytes/hash, replay identity and completion receipt; ordered applied-file ledger
   digest over position/name/SHA256/events and exact contiguous correspondence to manifest and
   retained download receipts. Require the full snapshot for this CLI; no production prefix mode.
3. MeSH asset SHA256, year and source kind; both v0 and v0.1 selection-policy document hashes;
   cutoff listing year and all algorithm-affecting settings.
4. Exact source hashes for the new CLI/module and imported local behavior dependencies, including
   topic_selection.py and any reused helpers. Capture the explicit dependency inventory with the
   launch packet. Changed implementation requires a fresh run, not automatic checkpoint rebinding.
5. Frozen seed receipt/hash, information-needs identity, reserve/exposure prerequisite evidence
   and the approved run-packet hash. These are admission/provenance inputs, not new selection rules.

Do not hash the entire 510 GB catalog or reread raw compressed files on resume. Metadata and
ledger binding detect ordinary mutation, not cryptographic proof of every database page. Record
that limit explicitly. Reject active/nonempty source WAL or hot-journal conditions for this frozen
catalog; resolve source recovery separately rather than opening it as an immutable snapshot.
Recheck source identity before publishing completion. No source database writes.

## Ranking and output behavior

Retain all evaluated dispositions and provenance in the disk ledger. Build numeric-order and
ranking indexes after evaluation; index creation is transactional and may restart if interrupted.
Rank eligible WORKFLOW-only candidates globally by concept count descending, year descending,
then PMID length and lexicographic PMID ascending. Missing year remains -1. Never convert PMIDs
to bounded SQLite integers. Save at most 500 winners atomically with the stage transition.

Keep pre-cap rows unchanged. Export applies workflow_capped_out to nonwinning eligible rows,
using the current serializer/reason ordering and count_rows behavior. Journal/book/deletion rules,
all exclusions, candidate membership and numeric PMID ordering must match the existing selector.

Each export attempt uses a new numbered directory and `.partial` files. Interruption restarts
export from the saved evaluated ledger/winner set, not the source XML. Retain failed attempt logs
and files; capacity checks include them. Cleanup, if needed, is an explicit recorded decision.
This deliberately trades repeated sequential export for a simpler reliable first implementation.

Flush and fsync completed attempt files; record their hashes, sizes and counts. Verification streams
them back against deterministic ledger output, checks all reconciliation counts and candidate IDs,
and detects truncation, duplicates, ordering or membership differences. It scans derived outputs,
not the full source catalog. Publish the verified pair to records.jsonl/candidate-pmids.txt, fsync
the directory, then atomically publish and fsync summary.json last. Readers require a valid summary
and matching files; two renames alone are not an atomic pair. A crash between renames is recovered
from the recorded verified attempt, refusing unexplained conflicting final files. A crash after
summary publication but before the SQLite complete flag is reconciled by validating that summary.
Never overwrite an already valid completed result; resume on it validates and exits successfully.

The summary carries semantic identities, ledger digest, counts, output hashes/sizes, run identity,
resources and attempt history. Preserve official_selection_frozen=false, rights_qualified=false,
sampling_performed=false, stage=1 until their separate review processes. Engine/timing/history
fields may differ from the old selector; semantic rows, IDs, counts and their hashes must match.

## Stops and failure handling

- SIGINT/SIGTERM: request a cooperative stop, cancel long SQLite work, roll back an unfinished
  batch, retain committed checkpoint, close connections/release locks, emit a distinct stop reason.
  Do not claim paused or safe to eject until the actual process exits.
- Deadline/free-space/output cap: same rollback behavior; record the specific cause rather than
  only SQLite's generic interrupted error. No automatic restart or limit increase.
- ENOSPC/I/O error/disconnection: stop; use SQLite's normal recovery on explicit resume after
  correct volume returns. Status/log writes may also fail; checkpoint remains authority. Preserve
  an internal invocation log so missing external status is not mistaken for a healthy process.
- XML/policy/identity/schema corruption: fail closed with source position and error, without
  printing article text or silently skipping the record. Diagnose before any retry.
- SIGKILL/power loss: no promise of a final status. Recovery must pass SQLite consistency and
  checkpoint invariants. Durability settings stay enabled; do not use synchronous=OFF/journal=OFF.
- Duplicate launch: fail before evaluation. A stale PID/status is not a live-process check; the OS
  lock is decisive. Never remove a lock file to bypass a held lock.

## Resource proposal and launch evidence

Initial configurable defaults: 12 hours per invocation, 256 GiB total output cap, 400 GiB free-space
floor, 32 MiB cache per SQLite connection, mmap disabled, disk-backed SQLite temporary work, one
worker. These are proposed bounds, not measured capacity or an ETA. Retain current XML byte/depth/
entity limits. Budget includes ledger, journals, indexes, temporary sort space, exports, retained
attempts and logs. Direct temporary files to the accounted output volume and check the internal
log volume too. Periodic checks and SQLite progress callbacks are cooperative, not hard RSS or
exact disk ceilings; reserve headroom and record observed peak RSS. Do not advertise cache size
as a process memory cap. Measure disk/read, parse/evaluate, transaction/index and export time
separately before optimizing. No GPU requirement or parser comparison in this scope.

Before a real run, require:

- Seed lookup reviewed and seeds frozen under SEED-SET rule 4; information needs and reserve/
  exposure controls recorded per the existing Phase 3 sequence.
- Passing synthetic acceptance evidence below; exact command, code/dependency snapshots, catalog/
  MeSH/policy identities and fresh output location in a reviewed run packet.
- A bounded, separately agreed real measurement after those prerequisites, if needed to size
  output/headroom; no full-corpus launch disguised as a benchmark. Confirm chosen limits fit.
- Expected UUID 22750B93-2F3F-499D-87F5-902981BFAB59, actual free space, AC, no competing writer,
  source completion proof and available locks. Keep stdout/stderr, exit evidence and owned session.
- User review of the concrete launch packet; this design alone does not start a real selection.

## Proposed file changes and review sequence

| Phase | Proposed files | Deliverable |
| --- | --- | --- |
| 1 (this change) | This specification; link in PHASE3-SELECTION-2026-10-12.md | Design and acceptance contract |
| 2 | New src/retrieval/resumable_selection.py; new scripts/retrieval/select_pubmed_corpus.py; new tests/retrieval/test_resumable_selection.py | Identity, locks, evaluation checkpoints, explicit resume and CLI |
| 3 | Same new module/CLI/tests | Recoverable ranking, export, verification and completion publication |
| 4 | Same tests; optional new scripts/retrieval/benchmark_selection.py; new results document | Differential/fault tests and bounded performance evidence |
| 5 | New launch packet and runbook update | Exact real-run decision after prerequisites |

Review each phase before the next. Leave streaming_corpus.py, pubmed_catalog.py,
process_pubmed_corpus.py, topic_selection.py and verify_seed_candidates.py unchanged initially.
Reuse policy functions and count reconciliation without changing their producing bytes; bind those
imports. Any necessary additional production-file change must be explained at its phase review.

## Acceptance checklist (implementation evidence pending)

- [ ] Uninterrupted and interrupted/resumed runs produce byte-identical records/IDs and identical
      counts to the existing selector on bounded fixtures; summary operational fields compared separately.
- [ ] Cursor handles rowid gaps, empty tables, final short batches, deleted-without-XML, book records,
      delete/re-add history and very large numeric PMIDs. No duplicates or missing rows.
- [ ] Faults before/after batch commit and table/stage transitions repeat only uncommitted work;
      malformed records never advance the checkpoint. Stale status cannot advance progress.
- [ ] Every bound identity mismatch refuses resume; correct-volume remount succeeds; changed catalog,
      unknown schema, inconsistent checkpoint, missing identity and foreign outputs fail closed.
- [ ] Source/output locks prevent writer conflicts and duplicate selectors; locks release after exit.
- [ ] More than 500 WORKFLOW-only records with ties produce exact global winners and reconciliation;
      index/ranking interruption recovers without re-evaluating XML.
- [ ] Export/write/verify/rename/summary-publication faults recover from ledger; incomplete or tampered
      outputs are never accepted complete. Completed resume is idempotent.
- [ ] Deadline, low-space, cap, ENOSPC, SIGINT/SIGTERM and abrupt termination tests exercise actual
      rollback/recovery boundaries; preserve cause even when external status cannot be written.
- [ ] Memory does not scale with record count; SQL/temp/output accounting and durability settings
      are checked. Performance measurements retain configuration and repeated comparable timings.
- [ ] Existing replay/policy source hashes remain unchanged; affected regression checks pass.
- [ ] Launch prerequisites and evidence packet reviewed before any real selection run.

Phase 1 review decisions: accept separate CLI/module, SQLite as checkpoint authority, rowid cursor
bound to the unchanged catalog, export restart from saved ledger, and proposed configurable budgets.
Next after review: Phase 2 evaluation checkpoints and identity-bound resume.
