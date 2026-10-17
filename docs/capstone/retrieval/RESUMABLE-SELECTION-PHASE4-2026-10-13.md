# Resumable selector Phase 4 — recovery and resource qualification

October 13, 2026. Completed for review on this Mac using invented data only.
Tracking: [W02-06](https://trello.com/c/LxvwMa3s).
Previous: [Phase 3](RESUMABLE-SELECTION-PHASE3-2026-10-13.md).
No real selection, seed modification, raw import, embedding or training job was launched.

## Decisions

Keep Expat, the existing selection policy, one worker, FULL synchronous/DELETE journaling,
32 MiB cache per connection, and the default 1,000-record/10-second evaluation commit boundary.
The bounded measurements do not justify a parser replacement or more complex parallel execution.
Recovery and verified publication add a small measured cost on these fixtures; correctness wins.

The Phase 3 hidden-spill accounting gap is addressed for this single-process execution path.
SelectionBudget now counts both visible output files and open, unlinked regular files owned by
this process. Descriptor enumeration uses /proc/self/fd where present, otherwise /dev/fd; fstat
identifies unlinked files, and device/inode deduplication avoids counting duplicate descriptors.
Unlinked regular files on all devices are conservatively included, not just the output volume.
Enumeration errors fail closed except the already-closed enumeration descriptor (EBADF).

SQLite temporary work remains directed to the output volume. Auxiliary SQLite workers are disabled
with threads=0. An actual 20,000-row SQLite index build over roughly 2 KiB invented keys exercised
real unlinked spill; the test observed nonzero hidden bytes through the budget checks. A separate
unlinked-file test verifies exact accounting despite a duplicate descriptor and triggers the cap.
Peak sampled accounted/unlinked logical bytes are retained in the final selection summary.

These are cooperative, sampled checks, not a quota: a single write/SQLite operation can grow storage
between checks; brief files can disappear before sampling. Logical file length is not physical
allocation. The free-space floor complements logical-byte accounting. Fresh real-run headroom and
output sizing remain Phase 5 requirements. No guarantee against sudden unplugging or physical
power loss follows from passing process-kill tests.

## Recovery and fault evidence

Final suite: **102 passed in 3.51 seconds**, process exit 0.

```sh
.venv-prowl/bin/python -m pytest -q \
  tests/retrieval/test_resumable_selection.py \
  tests/retrieval/test_selection_process_recovery.py \
  tests/retrieval/test_selection_resources.py \
  tests/retrieval/test_streaming_corpus.py \
  tests/retrieval/test_topic_selection.py
```

Retained stdout/stderr, exact command and exit receipt:
`outputs/prowl/testing/selection-phase4-tests-20261013/`.

Nine actual child-process cases cover SIGINT, SIGTERM and SIGKILL at each of:

1. Evaluation with one committed row and a second inserted but uncommitted row.
2. Export with a partial attempt written.
3. Publication after the first final file rename and before the second.

Each child was explicitly terminated and reaped. SIGINT/SIGTERM exercise the CLI's shared signal
handler. SIGKILL exercises normal SQLite recovery without Python cleanup. Resume reacquires locks,
retains only the committed prefix, and produces exact record and candidate bytes matching an
uninterrupted synthetic run. All nine completed; no worker remains owned by the test harness.

Additional coverage extends prior tests with changed implementation, runtime, policy identity,
MeSH bytes and admission packet; ENOSPC injection before batch commit; resource-callback cause
preservation; actual SQLite spill; and descriptor deduplication. Prior coverage retains global cap,
rowid gaps, empty/deleted/book records, very large PMIDs, malformed XML, locks, truncated/tampered
exports, transaction faults, summary publication recovery and source recheck refusal.
ENOSPC is injected rather than deliberately filling the laptop's disk. Signal boundaries are
controlled test hooks; these are process-recovery tests, not an exhaustive filesystem crash proof.

## Bounded performance comparison

Reproduce with:

```sh
.venv-prowl/bin/python scripts/retrieval/benchmark_selection.py --output <fresh-output-directory>
```

The driver creates its own invented source, MeSH and prerequisite fixtures. Internal workers enforce
that fixture layout. It compares the original selector, new 100-row batches, and new 1,000-row batches
at 1,000 and 10,000 records, three repetitions each (18 separate Python processes). Worker timeout:
60 seconds; cooperative per-selector ceiling: 60 seconds; driver checks a 180-second budget between
workers. These are benchmark bounds, not full-corpus settings. Source construction/replay time is
excluded from selection timing. Source/output data stays on the internal test filesystem.

| Records | Variant | Median seconds | Maximum process RSS (MiB) |
| ---: | --- | ---: | ---: |
| 1,000 | Original | 0.4239 | 40.30 |
| 1,000 | New, batch 100 | 0.4438 | 40.23 |
| 1,000 | New, batch 1,000 | 0.4434 | 40.20 |
| 10,000 | Original | 4.2099 | 75.03 |
| 10,000 | New, batch 100 | 4.4602 | 67.77 |
| 10,000 | New, batch 1,000 | 4.3465 | 67.67 |

All compared record hashes, candidate hashes and reconciliation counts match within each fixture
size. New default adds approximately 3.2% elapsed at 10,000 records, including verification. Its
observed retained output is 27,996,242 bytes versus 34,593,703 bytes for the original at that size;
this is not a full-corpus size estimate. Different index/body layouts explain why byte footprint
need not match while public record bytes do. RSS is a fresh-process high-water mark including
imports; these two fixture sizes do not establish a hard memory bound for the real corpus.

For new batch 1,000 at 10,000 records, median instrumented times:

| Operation | Seconds |
| --- | ---: |
| XML metadata extraction | 0.3017 |
| Selection-rule evaluation | 3.6042 |
| Checkpoint saves | 0.0236 |
| Export | 0.1442 |
| Verify exported bytes | 0.1303 |
| Entire ranking/export/verification/publication stage | 0.2975 |
| Source identity checks | 0.0017 |

Timings are nested (finish includes export/verification); do not add every row. Uninstrumented
remainder includes source cursor reads, ledger inserts and orchestration. These are warm/small
synthetic fixtures with fixed variant order and instrumentation overhead, not randomized disk
throughput measurements. They show no reason to change parser or weaken checks, and support keeping
batch 1,000. They cannot predict an external-drive scan rate or completion time for 41M records.

Retained per-worker configs/stdout/stderr, timings, RSS, hashes and startup/final code identities:
`outputs/prowl/testing/selection-phase4-20261013-final/`. All seven startup file pins match after
completion. A prior attempt is preserved at `outputs/prowl/testing/selection-phase4-20261013/`:
the CLI changed during that attempt and the final identity check correctly refused publication.
That attempt is excluded from the final table; no bypass/rebinding was used to complete it.

## Operational additions and scope

The CLI now requires a fresh `--log-path` on a different filesystem device from the catalog.
It fsyncs invocation start, normal finish or caught failure to that internal log so an unavailable
external volume need not erase the only error record. SIGKILL cannot write a final log entry;
process exit and SQLite recovery remain authoritative. Native volume validation still occurs before
selection, and a new log path is required on each invocation. The real packet must verify that the
chosen distinct device is the intended internal drive, not merely some other mounted device.

Changed production files are only the new selector and its new CLI. Original replay, original
selector, policy and active seed-lookup files remain unchanged. New helpers/tests and the bounded
benchmark driver are synthetic tooling. No new dependencies, parser changes, policy adjustments,
durability reductions or source-identity transitions were introduced.

## Next: Phase 5 launch review

Prepare the exact packet only after seed lookup outcomes are reviewed, seeds frozen and reserve/
exposure evidence is ready. Record actual volume/free space, selected output and internal log paths,
MeSH/policy/code/admission identities, proposed invocation limits and concrete pause/resume commands.
Use a separately agreed bounded real measurement if needed for storage/throughput sizing; it must
respect the seed-freeze prerequisite. Review the packet before the first real selection run.
Phase 4 completion is engineering evidence, not authorization to bypass those prerequisites.
