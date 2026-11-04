# MACHINE work status

- Observed at: UTC timestamp.
- Owner / branch: machine chat and published branch.
- Delivered code revision: exact hash before this status publication; note remote
  push verification separately in the handback.
- Peer read: exact peer revision actually inspected and what was learned; state
  unavailable/stale when no fresh read was possible.

## Delivered since the previous handoff

Concrete behavior/result, code commits and report links. Distinguish implemented,
tested, running and completed. Cite immutable revisions for reports on another branch.

## Validation and limits

Checks actually run, outcomes, evidence location/hash and what remains unverified.
Do not equate synthetic tests with real GPU or quality acceptance.

## Active jobs and ownership

For each current job: state, observation time, output root, receipt SHA256, verified
supervisor/worker identity, actual journal progress, tracking and independent backup
status. Note exactly what was checked. Do not embed secrets or patient images.
If no job is running, state that with the verification time. Retain explicit pauses.

## Git and integration

Pushed work, uncommitted/untracked inventory and reasons for anything left pending.
Name peer changes read versus reviewed/integrated. Never imply fetch merged code.

## Blockers and next action

Known failures, needed decision/dependency, owner of the next step and any authorized
bounded continuation. No new launch/retry authority is created by this file.
