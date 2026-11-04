# Mac work status

**Latest operational update — November4:** User-requested KD pause completed at
14029updates. All owned workers exited, independent checkpoint/backups match,
GPU lock released, MLflow intentionally KILLED/operator_paused=true, hourly
monitor PAUSED. No resume until later user authorization. The earlier running
snapshot below is historical; see the latest pause entry in the
[KD runbook](../operations/MAC-KD-LAUNCH-HANDOFF-20261027.md).

Latest completed14k lesion Dice0.332939 versus same-step control0.294552;
pancreas Dice0.713754;33/36positive cases overlapped and34/34reference-empty
cases alarmed. Interim descriptive results only; false positives remain unresolved.

- Observed at: 2026-11-04 01:39 UTC (November 3, 6:39 p.m. Mountain).
- Owner / branch: Mac chat, `main`.
- Delivered code/report revision before this status publication:
  `e252c692d34375bef23d75a13048789a064f3766`, matched `origin/main`.
- Peer read: fetched Lenovo revision
  `edae4c385fb6fb38a94cdef51d52d3c3874f08d1`; read its LENOVO.md, archival
  reconciliation report and commit groups. Lenovo explicitly records reading Mac
  `e252c69`, including accounting/training-page, reviewer and approval work.
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

## Most recent job — Mac KD treatment (now paused)

- Root: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-treatment-resume-20261103-01`.
- Ready SHA256: `67d10dcfc7f3d1ce14d0a1b736a73da1d4c5fbbf495714455831fe58f4bdd11b`.
- launchd: `com.prowl.mac-kd-treatment-resume-20261103-01`.
- Last verified owners: supervisor15400, worker15806, guardian15809. At01:30UTC
  journal advanced9601→9602; at01:39UTC it advanced9669→9670, with
  teacher_accessed=true and KDweight0.1.
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
published peer status at01:36UTC reported16predictions completed/scored,
two of seven declared failures recorded so far, no unexpected failure. Owner
supervisors32040/13660; worker identities change between cases. Read the Lenovo-owned
status for subsequent progress; do not treat these counts as final.

Peer code for inspection:
[continuation](https://github.com/QuinnEvans34/PROWL/commit/5e82faf),
[first result verification](https://github.com/QuinnEvans34/PROWL/commit/31031ae),
[Lenovo accounting](https://github.com/QuinnEvans34/PROWL/commit/3a64d03).
The peer's two modified tracked logs and78untracked historical files are now
published in six reviewed groups, plus status/reconciliation documentation. Read
[the immutable reconciliation report](https://github.com/QuinnEvans34/PROWL/blob/edae4c385fb6fb38a94cdef51d52d3c3874f08d1/docs/capstone/operations/LENOVO-ARCHIVAL-RECONCILIATION-20261103.md).
It records identical working bytes for all80files,294active repository pins
matching before/after,68Python files parsed/compiled and53focusedCPU tests passed.
No data/weights/databases/transfer codes staged. Historical top-level one-shot
scripts remain archived provenance, not reusable launch instructions; old log
line-ending warnings are preserved and documented. This publication does not
requalify historical science or certify all old launchers on current dependencies.

GitHub fetch/read succeeded at01:39UTC even though the final remote-chat status
request was unavailable. Last Lenovo job observation remains01:36UTC; do not infer
that failed chat connectivity stopped its durable job. Mac has read the peer's
publication; no active checkout integration has occurred.

## Next action

Lenovo owns continuing the bounded autonomous evaluation, publishing meaningful
status changes and returning the failure-accounted report. Its historical source
publication is complete; later integration still needs review when safe.
Mac owns the explicit KD pause/recovery handoff and reviewer/UI integration. Both read the other's published
status at the next session/milestone; fetch and inspect only while jobs are active.
Review peer code separately before any later safe integration. Keep Trello linked
to the corresponding Git evidence rather than inferring completion from commit counts.
