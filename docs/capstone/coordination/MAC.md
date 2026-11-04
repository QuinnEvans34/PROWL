# Mac work status

- Observed at: 2026-11-04 01:30 UTC (November 3, 6:30 p.m. Mountain).
- Owner / branch: Mac chat, `main`.
- Delivered code/report revision before this status publication:
  `0ea343c8bec5d8b44064506fff580477a078acbb`, matched `origin/main`.
- Peer read: fetched Lenovo revision
  `31031aeca65f4d1264754814c446c17e771c1ba0`; inspected its continuation report
  and commit inventory. Fresh Lenovo chat audit confirmed the same GitHub tip.
  Lenovo source is visible but has not been merged into the active Mac checkout.

## Delivered

- Training accounting collector and `/training` UI: commits `a56d1bd` / `6670612`.
  The reconciled snapshot records547.306 training-session hours across both machines,
  including177.045 historical MLflow estimates, with90.963 teacher-target hours
  separate. This is not human time or GPU-utilization time. See
  [accounting report](../operations/COMBINED-TRAINING-HOURS-20261103.md).
- Native saved-result verification, reviewer identity/save isolation, actual overlay
  review and stakeholder fallback recorded in the
  [Week5 parallel work report](../operations/WEEK-05-PARALLEL-WORK-20261103.md) and
  [review follow-up](../operations/WEEK-05-REVIEW-FOLLOWUP-20261103.md).
- Approved and verified the Lenovo70-case evaluation continuation, commits
  `c8e2dee` / `0ea343c`. Five reused/up to58new predictions and seven explicit
  admission failures remain in the full70dispositions. See
  [scope and dispatch evidence](../handoffs/WEEK-05-AUTONOMOUS70-DECISION-20261103.md).

## Validation and limits

Accounting: eight CPU tests, five UI/service tests, production build and component
visual review passed. No model/CT inference was launched for those UI changes.
Actual native reviewer measurements and isolated save/reopen roundtrip were tested;
the retained production review remains unreviewed. Neither synthetic tests nor
exposed-development model results establish independent clinical/generalization
acceptance. The official stakeholder walkthrough remains pending.

## Active job — Mac KD treatment

- Root: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-treatment-resume-20261103-01`.
- Ready SHA256: `67d10dcfc7f3d1ce14d0a1b736a73da1d4c5fbbf495714455831fe58f4bdd11b`.
- launchd: `com.prowl.mac-kd-treatment-resume-20261103-01`.
- Last verified owners: supervisor15400, worker15806, guardian15809. At01:30UTC
  journal advanced9601→9602, teacher_accessed=true, KDweight0.1.
- MLflow436bb317362b44d8861edfa5c5dd5b8a RUNNING with stored metrics; initial and
  ready independent backups match; no tracking warning. The01:07UTC hourly check
  also verified126pins, last/best/8k backups, exclusive lock, AC/storage/cumulative
  caps and caffeinate. These are timestamped observations, not a live guarantee.
- No teacher restart, competing GPU job, automatic retry or successor authorized
  by this handoff. Follow the
  [current KD runbook](../operations/MAC-KD-LAUNCH-HANDOFF-20261027.md), preserving
  original recipe, receipts, cumulative budgets and explicit user pauses.

## Peer work and pending integration

Lenovo's published continuation at`31031ae` passed13CPU tests, completed source
admission, and verified the first new prediction plus independent backups. Latest
peer audit at01:30UTC reported15predictions completed/scored, current81/252tiles,
two of seven declared failures recorded so far, no unexpected failure. Owner
supervisors32040/13660; worker12184 at that observation. Read the Lenovo-owned
status for subsequent progress; do not treat these counts as final.

Peer code for inspection:
[continuation](https://github.com/QuinnEvans34/PROWL/commit/5e82faf),
[first result verification](https://github.com/QuinnEvans34/PROWL/commit/31031ae),
[Lenovo accounting](https://github.com/QuinnEvans34/PROWL/commit/3a64d03).
The peer audit found two modified tracked files and78untracked historical files;
selective reconciliation is pending. Mac working tree was clean before creating
this coordination guide/status. No active checkout integration has occurred.

## Next action

Lenovo owns continuing the bounded autonomous evaluation and publishing its status,
reviewing its pending source/docs safely, and returning the failure-accounted report.
Mac owns KD monitoring and reviewer/UI integration. Both read the other's published
status at the next session/milestone; fetch and inspect only while jobs are active.
Review peer code separately before any later safe integration. Keep Trello linked
to the corresponding Git evidence rather than inferring completion from commit counts.
