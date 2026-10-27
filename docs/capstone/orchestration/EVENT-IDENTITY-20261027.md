# Offline stage event identity and observations

October 27, 2026. W04-01 remains in progress. New offline CPU attempts now bind
`offline-workflow-event-v2` in their immutable request. Each stage event records a
fresh UUID, exact run UUID, attempt 1 and UTC observation time in addition to the
existing ordered hash chain, stage state and output/error evidence. Explicit resume
creates a new run; this runner has no within-run retries.

Inspection rejects a mismatched version/run, duplicate event ID, invalid timestamp
or attempt number even when the record and following chain are rehashed. Removing
new fields cannot downgrade an event within a request that requires v2. Existing
legacy requests/events remain readable and reusable without modification or invented
observations. These hashes detect integrity inconsistencies; they are not signatures
or protection against an actor rewriting every record together.

The machine-readable contract is
`docs/capstone/contracts/offline-workflow-event-v2.schema.json`. It describes persisted
records including the integrity hash and state-specific reference/error fields.
Structural schema validation does not replace chain, dependency, artifact or lineage
validation in the executor. This deliberately uses an offline-specific name rather
than claiming to implement the entire approved Plan04 event contract.

Registered run summaries copy recorded stage start and completion observations.
Reused stages receive their actual reuse completion observation, without inventing
a start time. Durations remain absent: UTC wall-clock observations are not monotonic
elapsed measurements. Sequence/hash order remains authoritative if the system clock
changes. Failed stages retain their error and do not receive a completion timestamp.

## Verification

- 162 combined CPU regressions passed in 15.91 seconds.
- The final event-contract suite passed all 11 checks in 0.37 seconds, including
  one additional failed-stage schema check after the combined run.
- Coverage includes new/reused event schemas, rehashed invalid identity/version/time,
  duplicate IDs, rejected downgrade, unchanged legacy resume, and failed-stage
  reference exclusion. Existing subprocess cancellation, publication interruption,
  recovery and adapter tests also passed.
- Evidence: `outputs/prowl/workflow-event-identity-20261027/` (`focused.txt`,
  `regression.txt`, `event-contract-final.txt`, `teacher-safety.json`).
- All 328 repository teacher pins match. The same supervisor13779/worker15917
  continued, with527/1333 targets completed and fresh tile progress; no resource or
  guardian failure record. No GPU dispatch, teacher mutation or service restart.

## Remaining work

CPU-safe next work is full lifecycle/provenance coverage (run, lock and cancellation
request events; registry/DAG binding), followed by a consolidated G3 evidence review.
The current version covers stage events only. No historical missing event should be
fabricated. Broader imaging adapters and actual training checkpoint cancellation,
recovery and accelerator cleanup remain unqualified; full-provider GPU work waits
for complete teacher targets and its own admission gates. D-201 already selected the
repository fallback in TOOL-SELECTION-RESULTS-20261026.md; older pending wording is
historical. Do not repeat that framework trial.
