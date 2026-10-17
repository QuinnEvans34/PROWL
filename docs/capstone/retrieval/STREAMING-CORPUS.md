# Streaming PubMed catalog and topic selection

Implemented October 10, 2026. This path replaces preview size limits for processing; it does not
freeze an evaluated corpus or qualify text rights. The original preview commands remain available.

## Behavior

`scripts/retrieval/process_pubmed_corpus.py` has two commands:

- `replay`: verify the manifest and download receipts, hash each unapplied compressed file, and
  apply records in manifest order to a disk-backed v2 catalog. Each source file is one transaction.
  Replacements, deletions, retained deletion metadata and re-additions retain existing semantics.
  A failed/interrupted file rolls back; rerunning the same command skips committed files. Native
  process termination may leave a SQLite rollback journal, which SQLite recovers on opening.
- `select`: check the verified MeSH hash and read a consistent catalog snapshot. Evaluate one record
  at a time into a disk ledger. Use indexed global WORKFLOW ranking, retain only the 500 winning
  IDs in memory, and export all final records in numeric PMID order. Numeric sorting uses digit
  count plus text, avoiding SQLite's signed-integer limit. Duplicate live/deleted identities fail.

Replay requires matching manifest, receipts and producing code on resume. It saves its manifest
and implementation identity beside the database. Complete selection requires a completed full
snapshot and checks its replay receipt against the catalog's actual prefix and manifest. The
explicit `--allow-prefix` switch is for development capacity trials only.

Selection writes `records.jsonl`, `candidate-pmids.txt`, hashes and reconciliation counts.
`summary.json` is written last: without it, results are incomplete. `selection.sqlite` is an
**intermediate pre-cap ledger**, not the final selected corpus; consume the exports bound by the
summary. Failed selection attempts stay inspectable and restart in a **new output directory**;
selection itself does not yet resume. Replay does resume.

SQLite uses a 32 MiB page cache and no memory mapping. Record parsing remains capped; corpus rows
are not accumulated in Python. Indexes avoid whole-corpus in-memory ranking and sorting. Counts
retain distinct categories in memory. Time and disk checks are cooperative, including during SQL
work and replay batches; directory checks run at most once a second and can overshoot by work
between checks. SQLite also enforces a database page ceiling. These are not a hard process-RSS
watchdog or a filesystem quota. Outputs should use dedicated folders on the external drive.

## Commands

Resume the currently selected 1,200-file prefix:

```sh
.venv-prowl/bin/python scripts/retrieval/process_pubmed_corpus.py replay \
  --source /Volumes/PROWL-Data/PROWL/scratch/literature/pubmed-2026-20261009 \
  --output /Volumes/PROWL-Data/PROWL/scratch/literature/catalog-streaming-20261010 \
  --through 1200 --hours 12 --max-gib 768 --free-gib 400
```

Do not start this again while the current writer is running. Once it stops and all raw receipts
are present, omit `--through` to continue the same catalog through all 1,656 files. A missing receipt
fails before replay rather than silently producing a shorter snapshot. The processing time budget
is per invocation, not cumulative across manually requested resumes.

After full replay, selection can use:

```sh
.venv-prowl/bin/python scripts/retrieval/process_pubmed_corpus.py select \
  --catalog /Volumes/PROWL-Data/PROWL/scratch/literature/catalog-streaming-20261010/catalog.sqlite \
  --mesh-path /Volumes/PROWL-Data/PROWL/scratch/literature/mesh-2026-20261010/desc2026.xml \
  --mesh-sha256 449792ed59ba4d60035e44724352f7361ec0dc945b67dcd821a50ff32f81bcdb \
  --cutoff-year 2026 \
  --output /Volumes/PROWL-Data/PROWL/scratch/literature/selection-streaming-full-20261010 \
  --hours 24 --max-gib 768 --free-gib 400
```

This is an example invocation, not a launched selection or guaranteed completion window. Reassess
capacity from the finished catalog. Preserve the final snapshot, seed verification, reserve/exposure
controls and freeze sequence before evaluation; rights qualification precedes vector loading.

## Validation and measured capacity

Seven focused streaming tests pass, alongside the 53 existing selector/catalog checks. Tests cover:

- Exact row/count/hash equivalence to the bounded selector, with more than 500 WORKFLOW candidates,
  ties across years/PMID lengths, journal exclusions, books, replacements and deletions.
- Interruption after 256 writes, full file rollback, successful resume, and no replay of committed files.
- Single-writer exclusion, missing receipts, source hash failure and free-space refusal.
- MeSH pin mismatch, incomplete/contradictory completion receipts and changed manifest refusal.
- Failed selection withholding its summary and successful processing beyond 10,000 records.

Actual capacity trials (aggregate reporting only; no article text inspected):

| Trial | Records | Wall time | Peak process RSS | Catalog size |
| --- | ---: | ---: | ---: | ---: |
| First-file replay | 30,000 | 10.65 s | 71,876,608 B | 237,658,112 B |
| First-file selection, including MeSH loading | 30,000 | 55.44 s | 125,550,592 B | — |
| Largest verified compressed file at trial time (`pubmed26n1065.xml.gz`) | 30,000 | 22.96 s | 83,263,488 B | 571,817,984 B |

The first file consists of older records and all 30,000 were excluded by date; this demonstrates
processing and reconciliation, not relevance or corpus coverage. The largest-file trial is an
isolated capacity catalog, not a valid snapshot. These measurements do not establish a full-run
ETA or prove the maximum memory/disk requirements of every source record.

Receipts, `/usr/bin/time -l` resource reports and producing source copies are under
`outputs/prowl/streaming-corpus-20261010/`. Existing preview catalogs are preserved. No training,
embeddings, generation, sampling or human-hours credit was part of these tests.

## October 10 active import

The verified 1,200-file prefix import was dispatched in owned exec session `12630`, with
`caffeinate -i`, 12 hours, 768 GiB output budget and 400 GiB free-space floor. Monitor
`catalog-streaming-20261010/replay-status.json` and local `replay-1200-resources.txt`; do not launch
another writer. Raw downloading remains a separate existing job. The remaining 456 manifest files
are not included in this invocation. Full snapshot completion and full selection remain pending.

October 10, 15:12 MDT continuation: first 1,200-file invocation finished successfully (exit 0) at
15:05 MDT after 17,190.50 seconds wall time. Catalog contains 35,999,999 records and occupies
411,332,247,552 bytes; maximum process RSS was 368,476,160 bytes. Raw acquisition is complete:
1,656 verified files / 73,344,775,960 bytes. Free external space at continuation: 2,351,104,000,000 bytes.
The same catalog was resumed without `--through` in owned session `39641` to process the remaining
456 files. Same 12-hour invocation / 768 GiB directory / 400 GiB-free scope; code/manifest resume
binding and single-writer lock remain enforced. Session `12630` is finished; do not treat it as live.
New local receipts: `replay-remaining.json` and `replay-remaining-resources.txt` in the existing packet.
Full snapshot and full topic selection remain incomplete at dispatch.

October 10, 20:37 MDT timeout recovery: session `39641` stopped at 20:11 MDT with a per-file
600-second deadline on source 1463. Confirmed 1,462 contiguous committed files against download
receipt hashes; incomplete source 1463 was not committed. Remaining 194 files are already downloaded.
A tested change adds `replay --file-seconds` (default 600, range 1..7200), forwards it to the existing
parser, and reports the current in-progress file. Continuation uses **3600 seconds per file** with
the same 12-hour invocation, 768 GiB output and 400 GiB-free scope. This deadline includes downstream
SQLite work while consuming parser events, so the timeout alone does not demonstrate malformed XML.
61 focused catalog/selection/streaming tests pass. Schema, selection and replay ordering are unchanged.

Before resumption, the exact old code/manifest identity and all 1,462 applied receipt hashes were
checked under the writer lock; external volume UUID matched. Preserved old/new identities, stopped
status and ledger digest in `timeout-transition-20261010.json` beside the catalog and
`outputs/prowl/streaming-corpus-timeout-20261010/transition.json` before updating the resume binding.
Old code copies and the one-time migration script are retained in that packet. No successful file
is replayed. Use `--file-seconds 3600` for this continuation. Logs: `replay-result.json` and
`replay-resources.txt` in the timeout packet. A longer allowance is not a completion or ETA guarantee.

October 11, 11:13 MDT continuation: timeout-recovery session `95114` finished with SQLite
`interrupted` after 43,248.56 seconds (approximately the 12-hour cooperative limit). Status at
08:38 MDT retains 1,598 committed files; 58 remain. Free external space is 2.26 TB. This timing is
consistent with the run deadline; the generic SQLite interruption does not retain a distinct budget
cause. Resumed unchanged code/catalog in owned session `18193`, starting with source 1599 under
the same 12-hour / 3600-second-per-file / 768 GiB / 400 GiB-free scope. New execution logs are in
`outputs/prowl/streaming-corpus-resume-20261011/`. No duplicate job or completed-file replay.

October 11 performance continuation: user requested acceleration. Session `18193` was intentionally
interrupted and fully rolled back/reaped (exit 130), preserving 1,607 committed sources. Native stack
sampling identified read waits in SQLite replacement. [Performance report](IMPORT-PERFORMANCE-2026-10-11.md)
records isolated clone tests: UPSERT +4 GiB cache took 118.39 s versus 132.52/133.08 s for original
32 MiB replacement on identical 1,000-event inputs; all resulting record hashes matched. Cache-only
trial took132.30 s, so cache alone is not a demonstrated speedup here. 63 focused checks passed.

Continuation now uses `--cache-mib 4096` in addition to the existing runtime/storage flags. The old
32 MiB default remains for small/preview workloads. Journaling and durability settings are unchanged.
An exact old/new code identity transition was retained before rebinding the same catalog. Evidence
and current execution logs: `outputs/prowl/streaming-cache-20261011/`. Per-file committed timing/event
metrics are now appended to `replay-metrics.jsonl` beside the catalog. No completed-file replay,
sampling, training, or full-selection launch. A roughly11% benchmark reduction is not a new ETA.
Optimized continuation is owned exec session `4809`; prior `18193` is finished. Monitor this one
writer and its current packet; no duplicate launch.

October 11, approximately 16:55 MDT recovery: status still claimed source1628 running with1627
committed, but owned session4809 was no longer available and native process inspection found no
importer. Prior result/resource logs were empty; exit reason and actual exit time are unknown.
Do not interpret the stale status timestamp as ongoing processing time. Dispatched unchanged
recovery/resume in owned session49545 with the existing12h/3600s/4096MiB/768GiB/400GiB scope.
New logs: `outputs/prowl/streaming-recovery-20261011-1655/`. Normal SQLite journal recovery and
manifest/code/applied-prefix guards run before further work. Full completion remains pending.

October 11, 20:07 MDT overnight monitoring: user requested checks while asleep. Created three
one-time thread automations for 23:00 October 11 and 01:00/04:00 October 12, America/Denver:
`prowl-import-check-11-pm`, `prowl-import-check-1-am`, `prowl-import-check-4-am`.
Each checks native process activity alongside receipts, leaves healthy work running, and may safely
resume a stopped importer under the existing identity/lock/resource guards. New failures require
diagnosis; no duplicate writer or repeated-failure loop. Completion requires all 1,656 applied
entries and matching receipt hashes. Meaningful recovery/completion is logged here and in Trello.
At 20:03 MDT the native importer PID17707 was alive, with 1,643 sources committed and source1644
in progress. Independent ten-hour `caffeinate -i -t 36000` runs in owned session24105 to keep idle
sleep prevented even if the importer exits; it does not prevent lid-close sleep. Keep AC, the drive,
and Codex available overnight. No morning completion guarantee, selection, embeddings, or training.

October 11, 23:01 MDT completion verification: import completed at approximately 22:37 MDT
(final status mtime 2026-10-12T04:37:23Z). Owned session49545 returned exit0; native process
inspection confirms the importer is absent. All1,656 SQLite applied entries are contiguous and
exactly match manifest names and download receipt SHA256 values. Manifest binding matches;
status is complete/snapshot_replayed and agrees with the final result receipt. Verification uses
the small applied ledger and metadata, not a full database scan or raw-file rehash.
Final reported counts:41,226,017 documents and10,817 deleted PMIDs; database510,130,282,496bytes
(510.13GB). Final invocation20577.13s wall time, maximum RSS5,487,607,808bytes.
Evidence: `outputs/prowl/streaming-recovery-20261011-1655/completion-verification.json` plus
preserved result/resource logs. No recovery needed. Raw download and full catalog replay are
complete; topic selection, rights qualification, embeddings and vector loading remain pending.
Later overnight checks should treat this as completed and avoid restarting or repeating verification
unless new evidence indicates a problem. No human project hours credited for unattended runtime.
