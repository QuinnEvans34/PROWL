# D-305 — bounded training transaction complete; CAP-EXP-007 prepared

The separate144³ training loop, role-safe shuffled sampling, native scoring/export, strict progress
checkpoints, independent record keepers and single-use launch wrapper are implemented.
**1,539 native tests pass** (48 new; two existing upstream warnings), and the final source-matched
MPS rehearsal passed. No real optimizer update or original CT/label array read occurred in D-305.
The prepared request's existing processed cache was fully validated; metadata-only qualification
preflight independently resolved113/40 members. All153 qualified cases and23holds remain unchanged.

## Implemented behavior and verification

- Readiness sessions still reject real updates. Shared model initialization/state validation was
  factored out without weakening its identity/purpose checks; its18 regressions still pass.
- Training identities bind cache, plan, source/environment, sampling/prediction policies and exact
  request-linked authorization. Synthetic identities reject real source descriptors. No prior learned
  checkpoint can start the real launch; fresh seeded weight digest is checked.
- SHA-256 per-pass ordering visits all training members before starting another pass. Each update
  records member/pass/crop trace,loss and LR; evaluation members cannot reach the optimizer.
- Checkpoints validate history, tensor inventories/dtypes, optimizer moments/step, scheduler policy,
  RNG and immutable controls. A session interrupted after optimizer mutation refuses reuse or saving.
- Evaluation restores discrete predictions to original geometry and scores original visible pancreas
  references. Empty/dense failures remain included. All prediction/metric files have completion-last
  receipts; a failed stage/backup leaves an inspectable incomplete attempt.
- Stage-specific reference accounting is derived from the request's approved plan, then independently
  matched to D-294 qualifications and registered storage. Each stage opens once; an incomplete prior
  stage prevents advancing. D-304's consumed requests are not reused.
- Checkpoints, evaluation records and terminal journal are independently kept. Native prediction
  masks are explicitly **derived local scratch, not backed-up mask bytes**. Keepers retain their
  hashes/geometry and the checkpoints needed to regenerate them. This limits the backup claim.
- Launch checks require a separate Quinton approval pinned to the exact request, consume the request
  once and refuse source/environment drift. Worker/recovery have separate single-use start records.
  The supervisor enforces total time,AC,RSS/output/free-space limits; driver and keeper quotas are
  checked inside the workers. No automatic continuation or model promotion exists.

Owned implementation: `src/training/twomm_training.py`, `twomm_training_executor.py`,
`twomm_training_evidence.py`; `src/data/twomm_training_references.py`; diagnostic scripts
`twomm_training_rehearsal.py` and `twomm_training_launch.py`; two new training test modules.
Shared changes are limited to reusable mechanics in `twomm_session.py` and read-only cohort/storage
resolution in `native_localizer_references.py`. Claude's retrieval files were not changed.

## Final native rehearsal

Actual SegResNet,MPS,float32,fallback0,threads2; invented processed volumes96³ and248×248×244
(15,007,744voxels). Three producer updates, checkpoints0/2/3, seven native evaluation cases across
before/mid/after. One independently restored next update and one deliberately interrupted update
were additional synthetic calls. The intermediate and terminal checkpoint plus four evaluation/
terminal record keepers were independently restored with primary reads blocked: six restores.

| Measurement | Observed |
|---|---:|
| Producer worker |33.600914s|
| Recovery worker |12.408999s|
| Summed workers |46.009913s|
| Peak process RSS |2,759,524,352bytes /2.570GiB|
| Peak sampled MPS driver |5,211,226,112bytes /4.853GiB|
| Intermediate and terminal probe maximum difference |0|
| Next-update maximum weight difference |3.725290298461914e-9|
| Next-update loss difference |0|
| Final package files independently rehashed |48|

Native source/environment matched the final request exactly. This is engineering/recovery evidence,
not trained-model accuracy evidence. Interruption injection occurs immediately after an optimizer
boundary; it is not a power-loss/mid-kernel-kill experiment. CPU regressions also cover interruption
during publication/evaluation, incomplete keepers, failed time budget, corrupted state and journal.

Final producer `outputs/prowl/twomm-training-5bf6d23e-dae3-4db9-98f4-b11256181e69`:
`bd80b91f85aa28394695c316348aa29f6fbf7ecf95f5ebd62fdf5dbb0ccaad5a`.
Final recovery, same prefix plus `-recovery`:
`dbdb0f4dadfdd5a9c796e4a615ebc14c18fb224378a797d9753900274b13c142`.
Review `outputs/prowl/twomm-training-review-20260930`:
`9c165e8938151546bc7bd3188861b27e9dc1b14fca3979007f451441e5ddec3e`.
Review contains native test log, summary and no-array-read reference preflight.

Two earlier passing rehearsals are retained, not replaced:

| Stage | Producer suffix | Producer/recovery receipts |
|---|---|---|
| Initial loop/state/recovery |78b22fa9-8c19-480a-bda0-a235b59d6928|`6ab506ae669eeb2984a34ec2fcfd245129b27d9906e1301d82dd515ebae531a9` / `d91be82d7c3db3dd570159811deaa4d43e75596266e23369ce9bda2adf21b4c1`|
| Added evaluation keepers |ce324d6f-d4ae-4610-ac55-59a5326ec661|`ba9e9b0a636a9e06a79467e5e0d82186c82620f2dc8d827581024548cb32f0ae` / `5da994044ec06a7bd30ea0783a4a95dee7d3074e9c5dafd8b97f52d8048287e6`|

Each used three producer updates, one replay and one interruption injection:15 synthetic update
calls across all three rehearsals. No failed native attempt, source-data update or scientific
model promotion occurred. The final repeat binds the last launch-guard revision to native evidence.

## Exact prepared request — not launched

[Launch design](CAP-EXP-007-LAUNCH-PLAN-2026-09-30.md).
Request directory: `outputs/prowl/twomm-training-cd6be21f-7dcf-4bd5-b9da-a704f5f1167f`.
Request SHA-256:
`b13ebbce1731090a65dd5fe6c8327963f8e50203e39c25aa8ee6c88f903d85b3`.
State: `prepared_not_authorized`; no consumed marker or launch approval has been issued.

300updates,113train/40development-validation,144³/2mm, fresh seed42,balanced CE+Dice,
AdamW0.0003,cosine schedule. Checkpoints0/113/226/300; full baseline/final and validation at113/226.
45minutes **total including recovery**,16GiB RSS/driver,4GiB local outputs,AC and100GiB free floor;
existing96MiB-artifact/1GiB-new-per-domain/20GiB-total-backup limits remain enforced.
Nine independent keepers are planned (four checkpoints,four evaluation record packages,terminal).

Reference budget:386 labels,53,708,928compressed/10,774,955,452expanded bytes,no CTs.
Metadata-only preflight resolved exact113/40 qualifications and opened **zero** reference stages.
No source activation/registry edit, held-case promotion, dependency change, commit or push occurred.
Registry SHA remains `46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788`.

Next: Quinton reviews/authorizes this exact request, then launch once and inspect its learning,
coverage,crop-size and per-case results before proposing longer training. If any frozen code or
control changes before launch, this request must fail preflight and be explicitly replaced.
