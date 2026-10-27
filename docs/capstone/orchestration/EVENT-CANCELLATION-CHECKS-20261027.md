# Bounded CPU workflow event and cancellation checks

October27. **152 regressions pass in16.15s**, including15 new event/cancellation
checks. This change affects the offline registered CPU workflows only; the teacher
and training supervisors retain their separate cancellation and cleanup protocols.

## Behavior

The registered workflow wrapper now handles SIGINT/SIGTERM cooperatively while
the executor runs. It records the first request and lets the current bounded stage
finish publication and validation. Before starting or reusing another stage, the
executor writes an immutable `cancelled.json` record and returns `state: cancelled`.
The approved run-manifest summary reports `status: cancelled`; unstarted stages
stay pending, never skipped or falsely completed.

The cancellation record has the `workflow-cancellation-v1` tag, run/request
identity, last event sequence/hash, signal reason and timezone-qualified observation
timestamp. It uses the existing exclusive durable record writer. Inspection verifies
that it terminates the exact event prefix at a stage boundary. Extra events,
contradictory terminal states or altered boundary fields cannot be accepted merely
by recomputing that record's integrity hash.

An explicit resume creates a new attempt, revalidates completed artifacts and
preserves the cancelled attempt byte-for-byte. There is no automatic retry or
resumption. If a stage fails while cancellation is pending, failure takes precedence.
If the final stage completes and no work remains, the run remains complete.

SIGKILL, storage loss or abrupt interruption may still leave an incomplete attempt.
They are not fabricated into successful cooperative cancellation. If storage cannot
admit the cancellation record, no later stage starts and the existing incomplete
records remain the evidence. The callback model has no universal hard-timeout
guarantee: a hanging callback cannot be made cooperative by setting a signal flag.

## Verification

- Actual synthetic subprocesses receive SIGINT and SIGTERM during the first
  registered saved-package handler. Both exit cleanly after that stage, retain the
  downstream stage as pending, publish cancelled summaries and release locks.
- Explicit resume reuses the first stage and completes the second; original run
  records remain unchanged. Child waits are bounded and every owned child is reaped.
- A request before the first callback starts no callback.
- Changed cancellation sequence/hash/reason/time/extra fields are rejected.
- Event gaps, unsatisfied dependencies, impossible transitions and wrong request
  identity are rejected even when the changed record's own hash is recomputed.
- Pending cancellation does not hide a real stage error; completed final work is
  not relabeled cancelled. Original process signal handlers are restored afterward.
- The137 prior workflow, admission, supervision, handoff and publisher regressions
  also pass.

Evidence: `outputs/prowl/workflow-cancellation-20261027/focused.txt`,
`regression.txt` and `teacher-safety.json`. All328 repository teacher producing
pins matched; the same supervisor13779/worker15917 remained active with518 targets
complete at the check. No teacher signal, lock takeover, model run or live-service
restart occurred.

## Operator use and remaining G3 scope

For an offline registered CLI run, Ctrl+C requests a safe stage-boundary stop.
Inspect its returned state or saved run manifest; process exit alone does not mean
the workflow completed. Use the existing explicit `resume --resume-of RUN_UUID`
after reviewing the attempt. Do not apply this procedure to the teacher process;
its dedicated pause/resume protocol remains authoritative.

The primitive `Executor` accepts an optional cancellation callback; signal handling
is installed by `execute_registered`, not globally at import. The standalone older
synthetic CLI retains its prior abrupt-interruption behavior.

These checks close the bounded CPU cancellation gap. The full Plan04 event vocabulary
(per-stage event IDs/timestamps, lock events, cancellation-request events and complete
registry provenance) is not yet implemented by the compact v1 event log. No fields
were retrospectively invented for old attempts. Full G3 and actual training checkpoint
cancellation/accelerator cleanup qualification remain open.
