# Journal selection R01 — October 13 launch

Quinton approved the concrete23-seed proposal and continuation. Frozen seed manifest:
planning/SEED-FROZEN-V1-2026-10-13.json, SHA256
496009f5d3d70e4a9daffde138ccef2803b8a655c08f022a75a7c26400e444af.
Three records lack MeSH; each question family has at least two seed assignments.
C25 remains a probe; C32/C33 remain background; C36 and new C47–49 included.
Sampling keys drawn once and saved in planning/SAMPLING-KEYS-V1.json and RUNNING-LOG.md.

## Admission

Native checks: correct external UUID22750B93-2F3F-499D-87F5-902981BFAB59, AC/100% battery,
~2.26TB external free,~121GB internal free, no competing lookup/replay/selection process.
All1656 applied entries agree contiguously with manifest and receipt hashes; replay complete.
Code/policy/needs/candidate producing pins unchanged, source lock available, source journal/WAL
absent, new output absent before launch. Actual CLI repeats all enforced source checks.

512 systematic rowid probes read5,421,393 XML bytes in37.87seconds for storage engineering,
not scientific precision estimation. Observed SQLite1,875,968B plus export1,511,184B projects
254.1GiB across the reconciliation universe before later indexes/spill. This invalidates the
original256GiB planning allowance as useful headroom. Final cap768GiB (~3times this estimate)
allows indexes, journal/sort spill and retained partial exports;400GiB free floor stays fixed.
The estimate is not a bound or completion guarantee; caps remain cooperative and can stop the run.
No whole-catalog sizing pass; all512PMIDs conservatively added to exposure exclusions.

Executable admission and immutable exposure/key snapshot:
outputs/prowl/selection-launch-r01/admission.json and reserve-exposure.json.
All original17 explicit pending identifiers mapped through EuropePMC;18 total mappings recorded.
Broader historical/incidentally exposed groups still require reconciliation BEFORE any independent
sampling. Admission explicitly authorizes only stage1selection and blocks development/confirmation
sampling. This is not a claim that exposure reconciliation is complete. The current selector
performs no such sampling. Rights, passages and embeddings remain subsequent stages.

## Actual launch

Owned session90578; Python6127/caffeinate6128 verified alive. Invocation log records started;
no stderr at launch. Initially validating source identity/counts before first evaluation checkpoint.
Do not equate process startup with evaluated records. No duplicate invocation or producing-code edits.
Output: /Volumes/PROWL-Data/PROWL/scratch/literature/selection-journals-v01-r01.
Logs/receipts: outputs/prowl/selection-launch-r01/ (stdout-01.txt,stderr-01.txt,invocation-01.jsonl,
launch-receipt.json,preflight.json,sizing.json). Preserve all.

Uses Phase5 draft command with final --max-gib768; all other options unchanged:
--hours12 --free-gib400 --cache-mib32; fresh invocation-01 log. Twelve hours is an invocation limit,
not a finish estimate or automatic retry authorization. On requested pause verify native identity,
SIGINT once, wait for exit/checkpoint cleanup, then normal eject. Resume only SAME run/admission
with --resume and a fresh internal invocation log after identity checks. Never restart fromzero.

Completion still requires verified exports/summary and native exit, then seed recall review.
Engineering tests remain the102 previously passing Phase4 tests; no production code changed.

## Startup diagnostic after approximately41minutes

Session90578/Python6127 remains native-live, no stderr and no selection.sqlite/checkpoint yet. A2second native stack sample (startup-sample.txt in launch evidence) shows SQLite index traversal waiting in pread. EXPLAIN QUERY PLAN for the initial combined count/max query reports a covering-PMID-index scan. External disk sample observed about0.73MB/s during one interval; drive-level throughput is not process-exclusive. This supports I/O-bound initial validation, not evaluated-record progress or a confirmed deadlock. Left the job running; no duplicate or producing-code change. No defensible completion ETA yet.

## R01 stopped for optimization; R02 replacement

User-requested SIGINT ended session90578/exit1 before evaluation. PIDs absent, lock released, receipts preserved. See SELECTION-PERFORMANCE-2026-10-13.md for tested correction and R02 session48921. Earlier R01-live passages are historical.
