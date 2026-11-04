# Mac work status

- Observed at: 2026-11-04 21:16 UTC.
- Owner / branch: Mac chat, `main`.
- Delivered code: KD recovery `af0e442`, baseline metadata reader `41ff9c7`;
  the enclosing commit publishes the baseline review evidence.
- Peer read: fetched Lenovo `d290d43cdcbc2a9dc541ac722977d98e3985ecc8`, read
  LENOVO.md and its completed baseline metadata. Export SHA256
  `3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6`
  matches the published identity. No peer source merge occurred.

## Delivered

- Qualified and resumed the Mac KD treatment from the verified independent
  step14029 pause checkpoint. Two producer plus one cold MPS engineering updates
  passed existing restore/input/state gates; they do not count as scientific
  updates or training hours. All prior attempts and original cumulative budget
  remain preserved. See the [KD runbook](../operations/MAC-KD-LAUNCH-HANDOFF-20261027.md).
- Training-hours collector now follows the new continuation; eight accounting
  CPU tests passed. Existing `/training` UI and history remain available. Hours
  are training-session durations, not human effort or GPU-utilization hours.
- Previous reviewer, retrieval, approved baseline scope and stakeholder work:
  [Week5 parallel work](../operations/WEEK-05-PARALLEL-WORK-20261103.md) and
  [review follow-up](../operations/WEEK-05-REVIEW-FOLLOWUP-20261103.md).
- Completed hash-bound autonomous baseline metadata admission and error queues:
  [report](../operations/WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.md),
  [case-level evidence](../operations/WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.json).
  Twenty CPU tests passed; actual exported counts, metrics, components and coverage
  reconciled. No inference or image review was performed.

## Active Mac KD treatment

- Root: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-treatment-resume-20261104-01`.
- Ready SHA256: `7cf54250da7f109723f48678fcbfc3763b953170618a9f0215c3862a417bc3f7`.
- launchd: `com.prowl.mac-kd-treatment-resume-20261104-01`.
- Verified owners: supervisor46745, worker47349; exclusive MPS lock held.
- Scientific journal advanced14030→14123; teacher_accessed=true, KDweight0.1.
- MLflow `a23104d649a24c7fb0b19e0e1b9ca09b` RUNNING with stored loss, supervised
  loss and KD loss; no tracking warning. Initial checkpoint and ready independent
  backups match. Initial checkpointSHA
  `c1bb0914ff9120e65800a4e15ae430e5db34ef0a3dcb380f50688e68f127190b`.
- At dispatch140969seconds cumulatively charged,204631seconds remaining from
  original345600seconds. AC connected; storage and admission gates passed.
- Hourly monitor ACTIVE and bound to this root/ready hash. No automatic retry,
  competing GPU job, scientific change or successor is authorized by this status.

Latest completed14k lesion Dice0.332939 versus same-step control0.294552;
KD pancreas Dice0.713754,33/36positive cases overlapped and34/34reference-empty
cases alarmed. Interim descriptive results only; false positives remain unresolved.
Teacher exposure is uncertain; supplied-region KD is not the autonomous baseline.

## Peer result and next action

Lenovo a03 completed63scores plus seven declared admission failures, five reused
and58new predictions. Its closeout verifies710output backup pairs,12preparation
backup pairs,294repository pins and worker cleanup. Its GPU is idle. Numerical
probability equivalence remains UNQUALIFIED under the approved bounded exception;
all70cases are exposed development, not a held-out acceptance set.

Mac admitted the saved metadata: positive-case lesion Dice0.371202,30/32positive
overlap,31/31reference-empty alarms,35/40components hit and394FPcomponents.
Regions retained all annotations; five missed components remain for visual review.
Six unit-admission and one resource-limit failure remain in the70-case denominator.
The review preserves58reference-unit assumption flags, undefined empty-reference
Dice and exposed-development/UNQUALIFIED scope. No G3/model acceptance is claimed.
Lenovo acknowledged reading Mac recovery `af0e442` and remains idle.

Next: inspect saved native images for missed-component cases4681,8769,6755,2889
and2235, then high-FP cases, without another inference run. Reviewer integration
and the official aunt stakeholder walkthrough remain pending.

Each owner publishes meaningful changes to its own status; fetch/read peer work
without merging beneath active jobs. Keep Trello linked to Git evidence.
