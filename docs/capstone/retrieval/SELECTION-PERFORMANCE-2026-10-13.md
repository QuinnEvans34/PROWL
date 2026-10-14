# Selection performance correction — October 13, 2026

## R01 pause and root cause

Quinton requested immediate pause and optimization, with the laptop available for12hours before
school. Command-verified Python6127 received SIGINT. Session90578 exited1 with intentional
SQLite interruption at source_identity's SELECT count(*),max(rowid) FROM documents.
Python6127/caffeinate6128 absent; output lock available. No selection.sqlite or evaluated prefix
existed. R01 receipts and output preserved, including exact producing code snapshots. Nothing
already evaluated is discarded by the fresh R02 namespace.

The combined count/max query traversed the covering PMID index. A native sample showed disk
pread waits; observed drive throughput0.68–0.73MB/s. A standalone count also exceeded a bounded
15second probe. By contrast max(rowid) completed immediately and two1000record XML ranges took
0.28–0.41seconds; raw64MiB read took2.35seconds. Small/warm probes do not establish full-corpus speed.

## Implemented changes

- Enginev2 uses the completed, identity-bound replay counts as expectations and independently
  counts every row during the necessary evaluation pass. Excess counts fail immediately; short
  counts fail at table end, BEFORE ranking/export. Empty-table consistency, metadata, manifest,
  contiguous applied ledger/receipt hashes, source identity and final export checks remain.
  This moves count verification into useful work; it does not claim a fresh startup recount.
- Optional1–12 CPU evaluation workers, using spawn with bounded64record/~2MiB chunks and at most
  twice the worker count queued. Parent consumes results in source order and retains exclusive
  responsibility for SQLite writes/checkpoints. Workers receive no SQLite connections or locks.
- Cooperative shutdown cancels queued work and joins workers. Parent-death watchers reap orphan
  compute workers after hard parent kill. Native signal tests verify child PIDs disappear.
- CLI exposes --workers. R02 uses12workers and4096MiBcache PER connection (two connections, up to
  about8GiB of cache budget) on the18CPU/64GiB laptop. Cache benefit at full index size is an
  engineering expectation, not a claimed measured speedup from the small benchmark.
- Status now explicitly reports initial source validation. Existing evaluation checkpoints remain
  every1000records or10seconds, single writer, synchronous FULL and normal SQLite recovery.

The original replay/metadata parser/policy files are unchanged. GPU acceleration is not applicable
to this XML/string/SQLite workload. No training, embeddings or scientific sampling was started.

## Measurements and qualification

121 tests passed in7.61seconds: differential exports (including workflow cap), count discrepancy
refusals, worker bounds, and18actual signal/stage combinations across1/2workers. SIGINT/SIGTERM/
SIGKILL cases recover exact baseline bytes and verify no orphan workers. Initial test failures
from deliberately modified fixtures with stale replay counts/status-injection stage were retained;
fixtures were reconciled, and explicit bad-count refusal tests preserve that coverage.

CPU-only8000real-record benchmark, output hashes identical:

| Workers | Seconds | Records/second |
| --- | --- | --- |
| 1 | 18.15 | 441 |
| 4 | 4.78 | 1675 |
| 8 | 2.74 | 2921 |
| 12 | 2.04 | 3924 |

Source fetch for that set:6.82seconds/78.7MB XML. This is about8.9x CPU evaluation improvement,
not8.9x whole-pipeline speedup. Full read/evaluate/SQLite-write8000record benchmark:
12workers/4096MiBcache12.73seconds (~628/s), singleworker4096MiBcache22.65seconds (~353/s),
12workers32MiBcache2.74seconds (~2916/s). Later runs benefit from source OS cache: DO NOT infer
32MiB is faster than4096MiB or use warm throughput as full-run ETA. All bodies hash identically.
Benchmark outputs capped256MiB on external storage,400GiB free floor,240second deadline.

Updated source_identity ran in0.615seconds with both count expectations/maxrowids and1656ledger
entries bound. MeSH parsing is separate and remains required. Evidence in
outputs/prowl/selection-performance-20261013/, with retained read-paths/startup-v2/cpu-results/
io-results/test logs and bounded benchmark scripts.16,000 benchmark PMIDs conservatively excluded
from independent sampling; private generated bodies remain ignored output artifacts.

## R02 operational plan

New output /Volumes/PROWL-Data/PROWL/scratch/literature/selection-journals-v01-r02.
Logs/admission/preflight under outputs/prowl/selection-launch-r02. No use of --resume on the empty
pre-evaluation R01. R02 binds the new implementation, same frozen seeds/needs/policy/MeSH/catalog.
12workers,4096MiBcache/connection,768GiB output cap,400GiB floor,11.58hour invocation ceiling.
Target budget expiry around06:49MDT October14, retaining about15minutes before the stated window
ends. Limits are cooperative; actual transport still requires confirmed process exit and eject.
No automatic restart after deadline. Time spent in MeSH loading shifts expiry slightly.

Native launch session48921/Python29970/caffeinate29971. Confirm actual evaluation checkpoint
before claiming evaluated progress. No reliable full-run finish promise: uncached throughput and
later global indexing/export/verification costs can outlast the window. Progress is resumable.
Independent evaluation sampling remains blocked on outstanding historical exposure reconciliation.

Actual checkpoint confirmed: 202000 records committed, stage evaluating_documents, processing seconds 52.44137095619226. R02 launch receipt retained. This is actual useful work, not just a live-process assertion.

## October 14 transport stop

R02 reached its invocation deadline and exited 1 with the explicit recorded reason
`Selection invocation deadline reached`. Owned session48921 is finished; native inspection
found no selector or replay process. The committed checkpoint retains39,215,457 documents
of41,236,834 total source records (95.1% of evaluation), cursor40,839,149, commit39,564.
Deleted records, global ranking, export and final verification remain pending. This percentage
is evaluation progress, not overall completion. Resume the same R02 output with unchanged
identity and `--resume` after the drive is reconnected; do not restart from scratch.

User requested school transport and removal of scheduled tasks. All three import-check
 automations were deleted through the app. Verified volume UUID22750B93-2F3F-499D-87F5-902981BFAB59;
macOS successfully ejected physical disk4. Safe to disconnect. Evidence is retained in
`outputs/prowl/selection-launch-r02/transport-stop-20261014.json` and invocation logs.
No unattended runtime credited as human hours.

## October 14 school resume

User reconnected the drive and requested completion. Verified matching volume UUID,2.1TB free,
and no native selector/replay before launching same R02 with `--resume`, unchanged producing
code/admission,12workers,4096MiB cache,768GiB cap/400GiB floor and12h invocation ceiling.
Owned session74856/Python66663/caffeinate66664 is LIVE. Logs: invocation-02.jsonl,
stdout-02.txt,stderr-02.txt in outputs/prowl/selection-launch-r02. Initial observed state is
validating_source, with no error. New committed progress is not yet confirmed; checkpoint
validation counts existing ledger rows before evaluation resumes. Do not launch a duplicate.
Battery82% at launch; user advised to connect power. Prior session48921 remains finished.
