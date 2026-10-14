# Bounded selector resume validation

## Problem and decision

The October14 school resume spent8837.886seconds in `PRAGMA quick_check` without evaluating
another record. Native samples showed SQLite checkTreePage/pread; intentional interruption
confirmed the exact call. This is a whole-ledger structural check, not a constant-cost resume
check. SQLite documents O(N) complexity: https://www.sqlite.org/pragma.html#pragma_quick_check.
The following count/max query also traversed the saved prefix. Tiny recovery tests did not
qualify either operation's cost at39.2million rows.

User approved separating routine continuation from deep auditing, preserving source identity,
transaction recovery and final reconciliation, adding bounded validation and better reporting.
The selected tradeoff is explicit: fast resume does NOT certify every historical database page.
Interior corruption or missing rows can be detected later rather than before continuation.
No claim that the interrupted deep integrity check passed.

## Implementation

Engine v3 retains the same XML evaluation, policy, MeSH, ranking rules, resource floors,
SQLite FULL/DELETE durability, source locks and single output writer.

- Routine validation compares exact bindings and checkpoint schema/stage/totals, verifies the
  existing source-table/source-rowid index, and probes each table's highest saved source row.
  Counts must fit the source universe and cursor must fit the source boundary. No quick_check
  or full recount runs in normal resume.
- Records and checkpoint still commit in one SQLite transaction. SQLite's ordinary recovery
  runs on database opening; no journal deletion, forced recovery or identity bypass.
- Actual per-source ledger counts are reconciled against checkpoint counts while reading all
  records for export AND byte verification. Missing interior rows prevent final publication.
  Ledger PMID/body disagreement also prevents publication. This is not a full physical audit.
- `--audit-only --resume` explicitly runs quick_check plus full count reconciliation, without
  processing or publishing. Its default120second phase limit can be explicitly increased to
  at most3600seconds. It is NOT resumable, and may exceed that budget on the large drive.
- `--prepare-resume --resume` validates and exits with ready_to_resume. It does not evaluate,
  rank or export. Startup phases each default to120seconds (`--validation-seconds`). Deadlines
  are cooperative, including SQLite progress callbacks, not hard OS-level I/O cancellation.
- Phase status identifies source identity, checkpoint, audit, evaluation, export index build,
  workflow index build, winner selection, export and byte verification. SQL progress callbacks
  refresh elapsed time about every5seconds; blocked I/O can delay refresh. No invented percentage.

## Explicit existing-run transition

Normal resume rejects the old implementation. An explicit `--prepare-resume --transition-from`
requires the exact prior identity SHA and v2 engine. All source, runtime, policy, MeSH and
admission fields must match; only the selector module and CLI implementation hashes may change.
It is restricted to evaluation before any winners/export attempts. In one transaction it stores
original binding/checkpoint in implementation_transition and updates binding/checkpoint identity.
It does not alter saved rows, cursors, counts or commit sequence. A failed transaction rolls back.
Old producing source copies are retained and verified against the old binding.

R02 expected old identity:6bc94b8a07d370c1c88987aa00f7d64b36be3066188ae2df43b6bf94955ec6a5.
Once migrated, resume normally WITHOUT transition-from. Never regenerate the admission or
sampling keys, or overwrite historical logs. No actual evaluation launch is authorized by this
preparation step; user requested notification when ready.

## Remaining work and performance limits

A read-only EXPLAIN on the actual ledger confirms the boundary probe uses the existing covering
index and LIMIT1. The former count query uses that index but must still count its full range.
The export and workflow indexes do not yet exist: their builds must read the full ledger.
After construction, export ordering and workflow selection use those indexes. Export and
verification remain full traversals by design. This change fixes restart cost; it does not
promise that remaining ranking/export will finish quickly. Index creation is transactional;
an interrupted unfinished build repeats. Partial export attempts remain preserved and restart
as a new attempt under the existing design. Progress stages now disclose those operations.

## Validation

135 tests pass in8.37seconds: serial/parallel equivalence,18 real signal/stage/worker combinations,
transaction rollback, identity refusal, bounded validation, explicit audits, damaged header,
missing interior row blocked before publication, PMID/body mismatch, migration rollback and
exact final bytes after migration. Evidence: outputs/prowl/selection-resume-v3-20261014/.
No training, embeddings, independent sampling, new relevance decisions or human runtime credit.

## Actual preparation result

Preparation session42532/PID91627 finished exit0, ready_to_resume, in8.883954seconds including
MeSH load/source checks/transition/checkpoint validation. Exact prior identity matched; old
binding and checkpoint retained atomically. All checkpoint fields other than implementation
identity are unchanged:39,215,457 committed, cursor40,839,149, commit sequence39,564.
Readiness receipt and old source copies retained in the evidence folder. No evaluation, ranking,
export or deep audit was run. Future command uses ordinary --resume with current v3 bytes and
same admission/output; omit --prepare-resume and --transition-from only when continuation is
requested. Leave paused until that request.
