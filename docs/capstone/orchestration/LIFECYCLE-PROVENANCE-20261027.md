# Registered CPU workflow lifecycle and provenance

October27. New registered offline runs now retain an append-only lifecycle chain
alongside their stage events. This closes the bounded CPU lifecycle/provenance
slice of W04-01; it does not close all imaging/training G3 obligations.

## Delivered behavior

- `run_planned`, actual `lock_acquired`, `run_started`, observed `cancel_requested`,
  actual `lock_released`, and `run_completed`, `run_cancelled` or `run_failed`.
- Each event includes UUID, run identity, UTC observation, sequence/previous hash,
  host/PID/adapter identity and exact context, registry and plan hashes. The schema
  is `docs/capstone/contracts/offline-workflow-lifecycle-v1.schema.json`.
- The immutable executor request now binds those provenance hashes. Inspection and
  recovery verify the saved registry/configuration/environment/context against that
  request. Rehashing altered context files alone cannot authorize reuse. Existing
  legacy runs retain their original behavior; missing historical fields are not added.
- Resolved configuration and environment files use exclusive, fsynced publication.
- Inspection exposes lifecycle terminal status and whether lock release was observed,
  separately from completed stage artifacts. A missing release/terminal record is
  not fabricated into cleanup or success. Export requires a valid terminal lifecycle.
- Actual lock conflict records planning/failure only; it never claims lock ownership.
  Release is recorded after closing the workflow lock descriptor. If that record
  cannot be written, the original stage exception is preserved and no terminal
  summary is published. This is the workflow-root lock, not the teacher GPU lock.
- Cancellation records the reason when polled at a safe stage boundary, not an
  invented signal-arrival time. Real stage failure and final-stage completion retain
  their existing precedence. No in-run automatic retry was introduced.

The lifecycle chain and stage chain serve different scopes and are bound through
the run request/context; they are not a single global wall-clock ordering. Integrity
hashes are not authentication against an actor rewriting every file. Durations remain
unmeasured; UTC observations cannot establish monotonic elapsed time.

## Qualification

Final combined suite: **179 passed in17.03s**. Actual synthetic CLI plan wrote no
workflow files; run completed2/2 stages; explicit resume reused2/2. Both runs retained
valid terminal lifecycle chains with observed lock release. Original attempts stay
unchanged. Real subprocess SIGINT/SIGTERM tests verify cancellation event order and
reason; existing interruption/recovery and accelerator-conflict tests also pass.

New tests cover rehashed invalid lifecycle order/identity/process/binding, modified
registry/context/environment rejection before reuse callbacks, pre-lock failure,
failed-stage cleanup, absent terminal observations, schema state-specific fields,
and release-journal failure without masking the original stage error or retaining
the lock. The first focused run retained one expected-message assertion failure:
provenance checking now caught config mutation earlier. The specific configuration
error message was restored; no acceptance criterion was weakened.

Evidence: `outputs/prowl/workflow-lifecycle-20261027/`, including initial/focused/
final-regression logs, actual CLI JSON, immutable CLI records and teacher-safety.json.
All328 repository teacher pins matched throughout. No teacher source, recipe,
GPU execution, service or schedule was changed.

## Teacher safety observation

During this work, attempt06 stopped at529/1333 after its existing AC guard raised
`RuntimeError: AC power required`. Resources report6549.370012 supervised seconds,
exit1, workers reaped, peakRSS4053221376bytes and zero process-sample timeouts.
Supervisor13779 and worker15917 are absent. AC was connected again at the final
check. Attempt06 and its outputs remain intact; this work did not launch a retry.
A verified same-recipe continuation must charge this attempt against the original
budget and revalidate completed targets before generation resumes.

## Remaining W04-01

Consolidate the existing bounded evidence against G3 before adding more machinery.
The full Plan04 vocabulary also names retry/quarantine and training-specific events;
these adapters neither retry automatically nor dispatch training. They do not claim
that pinned artifact-writer internals emit lifecycle records. Full imaging adapter
coverage, actual full-provider executor admission, checkpoint cancellation/recovery
and accelerator cleanup remain separately qualified work. Teacher targets and a
verified continuation are the immediate training dependency. D-201 is already closed
by the repository fallback selection; do not repeat its framework trial.
