# Import performance investigation — October 11, 2026

Quinton explicitly authorized using the otherwise-idle laptop's resources to accelerate import.
The laptop has 64 GiB physical RAM. Native stack sampling of the owned importer showed 2,257
samples in `pread`, including SQLite overflow-page reads during deletion of existing rows; CPU
usage was low. This identifies database read waits in the sampled interval, not a GPU workload.

The existing import used `INSERT OR REPLACE` and a 32 MiB SQLite page cache. The proposed change
uses an UPSERT that updates all stored fields for an existing PMID and inserts new PMIDs, plus a
configurable cache (`--cache-mib`, default 32, accepted range 32..8192). The intended live value is
4096 MiB. SQLite allocates cache pages as needed; this setting is not a total-process RAM cap.
Durability settings, journaling, source hashes, per-file transactions, deletion/re-addition handling,
manifest order, and selection rules remain unchanged. Internal rowids remain stable for updates;
PMID and stored record fields, not internal rowids, define catalog identity.

Sources: [SQLite cache sizing](https://www.sqlite.org/pragma.html#pragma_cache_size) and
[UPSERT semantics](https://www.sqlite.org/lang_upsert.html).

The owned original process was gracefully interrupted and allowed to finish rollback (exit 130).
A separate stack sample confirmed rollback writes while stopping. It left 1,607 files committed;
no completed file is scheduled for replay. Source 1608 is the next pending input.

Validation: 63 focused selector/catalog/streaming checks passed, including row preservation and
all-field update behavior, unchanged durability settings, rollback/resume and global selection
conformance. Nine streaming checks passed again after adding per-file elapsed-time/event-count
logging. Logs append only after successful commit; the applied SQLite ledger remains authoritative.

The performance experiment uses isolated APFS copy-on-write clones of the stopped catalog and
1,000 ordered actual events from the next source file. Every variant begins from the same catalog.
It compares the old 32 MiB configuration, UPSERT with 4096 MiB, an old-method repeat after warming,
and the old replacement method with 4096 MiB. Touched record contents, tombstones and the applied
ledger are hashed for equivalence; internal rowids are intentionally not compared. These partial
workload clones are not complete snapshot catalogs and cannot be consumed for selection. Only
benchmark-created clones are removed after use. OS cache effects and this small workload limit
any generalization of a timing ratio to the remaining full files.

Evidence packet: `outputs/prowl/streaming-cache-20261011/`, including before-source copies,
process samples, benchmark source/progress/results and subsequent transition/launch records.

## Results and adoption

| Variant | 1,000-event elapsed time |
| --- | ---: |
| Original replacement, 32 MiB, first run | 132.521 s |
| UPSERT, 4096 MiB | 118.390 s |
| Original replacement, 32 MiB, repeat | 133.080 s |
| Original replacement, 4096 MiB | 132.299 s |

All four affected-record/tombstone/applied-ledger hashes match exactly:
`6e048c851dacabf2e329f11ca48003af90c000bfb24495233d37fd6dbfe66bd3`.
Benchmark completed with exit 0; all four temporary clones were removed. The UPSERT variant was
about 11% lower elapsed time. Cache size alone did not materially improve this small workload.
This is evidence for a modest improvement, not a demonstrated full-corpus speedup or ETA. The
4 GiB cache provides more working-set headroom for the real continuation; its benefit across
larger files is still unmeasured. Peak RSS numbers in the benchmark are process-wide cumulative
high-water marks, not independent per-variant memory measurements.

At 13:10 MDT, the old/new identity transition was recorded after verifying all 1,607 committed
source hashes against receipts under the writer lock. Existing catalog contents were not migrated
or rebuilt. `cache-transition-20261011.json` preserves provenance beside the catalog, with a local
copy in the evidence packet. The optimized continuation was dispatched with `--cache-mib 4096`,
`--file-seconds 3600`, `--hours 12`, `--max-gib 768`, `--free-gib 400`. Source 1608 is first; 49 remain.
Full import and selection are still incomplete. Current-file status records cache size; committed
file timings appear in the catalog's `replay-metrics.jsonl`. Updated source snapshots are in `after/`.
