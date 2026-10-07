# Duration recovery component audit — DUR-05

## Purpose and authorization

October 7, Quinton selected the bounded diagnosis effort: record the recovery components and
their differences, fix only a demonstrated cause, use a focused recovery check when needed,
and prepare the real-data duration comparison. This contract implements the model-free reporting
part first. The observed N02 failure is real; no cause is inferred from its combined assertion.
The next actual diagnostic must have its own reviewed source/read/call/resource scope.

## Closed producing scope

1. New `src/training/segmenter_duration_recovery_audit_v1.py`.
2. Amend only cold comparison/failure reporting in
   `scripts/diagnostics/segmenter_duration_launch.py`.
3. New `tests/test_segmenter_duration_recovery_audit.py`.
4. This contract.

Routine task handback, AGENTS/queue, Trello and automation updates and reviewed local preservation
are included. Snapshot the original launcher and the 397-producing-pin ledger before changes.
The other 396 paths and experiment history remain unchanged. No session, executor, numerical
recipe, sampler, source/authorization guard, authority, storage or quality-limit amendment.

## Reporting and acceptance

Evaluate all five existing predicates independently: model tree, optimizer tree, progress,
CPU RNG and MPS RNG. Use the existing tree comparison callback and existing progress equality;
the conjunction is unchanged. Record at most 16 differing paths across the report, shape/dtype/
device metadata, mismatch counts and finite maximum absolute differences. Never emit raw tensor,
optimizer or scalar state values. Paths and messages are bounded; JSON is at most 32 KiB, with
nonfinite JSON numbers forbidden. Numerical deltas are explanatory, not acceptance tolerances.

At the native next-update comparison, write the audit atomically before the unchanged refusal.
On cold exceptions, write phase, attempted call counters, completed restores, successful
probability deltas, completed native export checks and the most recent component audit, if any.
Retain the original exception. Initial zero counters must not replace counters after model work.
No report grants native acceptance, successful recovery, model promotion or scientific authority.

## Qualification

Only new invented small-tensor/fake-session tests: each component failure, simultaneous failures,
equal states, structural/nonfinite substitutions, bounded paths/report size, and integration
failure counters. No model construction, forwards, optimizer calls, native 144³ generation,
MPS work, original/cache/target/CT/third-party payloads or existing-suite replay.
One invocation is limited to 90 seconds and 2 GiB sampled owned-process RSS; retain failed attempts.

## Exact next point

Prepare a separate checkpoint-only diagnostic proposal using retained invented N02 evidence.
Bind exact receipts and current code; preserve every consumed N02 marker and partial artifact.
Any retained tensor decode or replay update needs that fresh reviewed diagnostic scope. Do not
repeat the 192-update producer, change numerical tolerances, or enable scientific launch from
the reporting packet. Real-data preparation retains D-335, all six training members, report-only
2514, the original evaluation points, DUR-01 stops, approved storage cap and resource limits.
