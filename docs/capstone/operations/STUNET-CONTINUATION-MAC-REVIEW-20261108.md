# Independent Mac review of corrected STU-Net continuation

Reviewed peer commit: `8c9dfbc` on `codex/week05-cuda-readiness`.
Active objective: qualify and launch the newly authorized corrected-label12k phase,
not rerun or restart the completed original12k arm. Human88GiBbackup amendment is
recorded in `STUNET-CORRECTED-CONTINUATION-AUTHORIZATION-20261108.md`.

## Source review and independent CPU checks

Mac inspected the new correction, schedule, input provider, ancestry session,
CPU preparer, training worker, supervisor and storage gate directly from Git.
Original STU-Net producing sources are unchanged in this implementation commit.
No blocking issue was found in the inspected update/restore path; real-device
qualification remains a separate requirement rather than an inference from tests.

- Exact seven-case original lesion hash/count whitelist and training role required.
  Correction reconstructs target from original pancreas, retaining overwritten
  pancreas voxels; ordinary training bindings and development reader are inherited.
- New schedule requires1333members/664positive,3:1focus/context, complete coverage
  slots and global zero-based addresses12000–23999. These addresses feed window
  jitter and augmentation; they are not reset to the first12k's addresses.
- Parent import requires the fixed checkpoint hash, original scientific identity,
  step12000, matching train roles/precision and complete exposure. Model, learned
  heads, optimizer moments, RNG and exposure are compared exactly after import.
  Old and continuation state versions cannot silently substitute for each other.
- New tail warms from4e-8 to2e-5 over500updates, then cosine-decays to0. Updates
  are global12001–24000, with six full70case validations and500step checkpoints.
- Diagnostic observations do not change the existing objective. CPU tests compare
  exact losses/gradients with and without diagnostics. Source groups the actual
  `seg_outputs.` parameters separately from the body for periodic gradient norms.
- Supervisor retains exclusive GPU ownership, exact source/request pins, wall/RSS/
  CUDA bounds, real volume identities, AC,100GiBfree floors,32GiBcache and the
  approved88GiB C-backup cap. Actual growth projection still needs fresh admission.

Mac exported `src`, `scripts` and `tests` from exactly`8c9dfbc` to an ignored
isolated directory, then used the Mac `.venv312` Python with
`CUDA_VISIBLE_DEVICES=-1` and the existing test-dependency path:

```sh
python -m pytest -q tests/test_stunet_errata_20261108.py tests/test_stunet_continuation_20261108.py
```

**26 passed in1.54s**: seven corrections, invalid source/role/count/shape rejection,
coverage/ratio/global-address/LR checks, optimizer/RNG-preserving parent import,
cold-next-update replay, invalid parent/state rejection, unchanged loss/gradients.
These optimizer tests use a tiny synthetic CPU network, not the actual STU-Net
or CUDA. Separately,20existing Mac errata policy/cache/provider tests passed in5.24s.
No real CT/mask/checkpoint arrays, pretrained model or GPU were used by Mac.

## Exact Git-byte source identities

| Source | SHA256 |
| --- | --- |
| `src/data/stunet_errata_20261108.py` | `a543e98888f16efe1fe14441c29b9f7d2c9616b5b1c5bdab9b4f5c0bfa3301e2` |
| `src/data/stunet_continuation_inputs_20261108.py` | `ae8d014d4c80f673dde64b0b53829ee8a5cb9db3f5d46b9a2a0d9083b161a062` |
| `src/training/stunet_continuation_session_20261108.py` | `9f75962559458d788680a27ebf9d9e7d87af522c2893e72e791c8a601ec8c495` |
| `scripts/diagnostics/prepare_stunet_errata_20261108.py` | `eaa7cb658f239ba84f8dbf8d0d80c9f00ec716779d23d94cbd5afa5cac256fa2` |
| `scripts/training/train_stunet_continuation_20261108.py` | `48eeaec7cc766e2f5f8a3da4a318ac8e836245f4f343b9e70717b73dd91f18f8` |
| `scripts/training/supervise_stunet_continuation_20261108.py` | `ec800629d0fe905a7731e174ab241f3a1edcecacd5caa7d59871e6868323403a` |
| `src/operations/stunet_continuation_storage_20261108.py` | `3b99a6418386d94552cbfbf2ff1845ae32d3acda35c96ba2b715d15d9fb20348` |

These are Git LF bytes, not automatically the same serialization as Windows
working-tree/receipt pins. Runtime qualification must verify its actual frozen bytes.

## Remaining execution evidence at this review

Lenovo reports seven real corrections passed with full pancreas coverage and1326
ordinary target bindings unchanged, and is checking nine real inputs (all seven
plus two ordinary controls). Mac has not independently read these arrays. Need
published real-provider evidence, actual CUDA parent-state equality, independently
backed cold-next-update comparison, native positive/empty coverage, resource/reaping
proofs and the final exact launch receipt. Do not infer scientific launch from the
passing CPU suite. A failed gate must be retained and diagnosed rather than waived.

After successful launch, verify one worker, advancing global updates, stored MLflow
metrics, the independent parent reference and one quiet hourly monitor. Capture
parent MLflow/checkpoint lineage and distinguish12000newupdates from24000ancestry;
do not duplicate parent runtime in training-hour totals.

## Qualification, operational recovery and verified launch

Peer`1b301bf`/`ac8db59` published the real provider and CUDA evidence, imported
byte-for-byte here from the final peer revision. Correction45.156s/998,051,840B
ownedRSS and provider27.328s/1,211,224,064B both succeeded/reaped. Actual CUDA
producer100.422s and cold23.843s succeeded/reaped;522state tensors match exactly
on restored state and the next update, maxabs0. Both diagnostic checkpoints have
independent matching backups. Positive/empty native reconstructions are gap-free.

The initial scientific dispatch used the isolated model interpreter for supervision,
which lacks MLflow. It failed before any updates or tracking creation; the failure
and reaping evidence remain intact. Under the already authorized operational fix,
peer`48ea7c5` adds a pre-dispatch supervisor-environment check and separate existing
MLflow supervisor/model worker interpreters. No package installation or qualified
worker change. A new receipt/output root deducts a conservative60s from the original
40h allowance:143,940s remain. Actual tracking-read/import preflight passed without
creating a run. Mac independently reran the expanded **41CPU tests, all pass4.85s**,
including runtime/failed-budget guards and phase-relative dashboard mapping.

Peer`6d484c2` verifies ONE running continuation:

- Artifact`pants_stunet_corrected_continuation_12k_20261108_launch02`;
  ready SHA`d0a291420d0e1ee07e56f1007540797ebb97c9a08ff25cc82111d53f77c4d9f8`.
- MLflow`13c709ae157949988de1d7f8821a03b7` RUNNING. Saved startup observations
  advanced12001→12018→12027→12051;50stored losses exactly match the journal prefix.
  Firstfive scientific inputs/losses/LRs match the qualified producer. No new phase
  Dice exists yet; first complete validation is global14000.
- Owned99079, supervisor48348/wrapper58540, workerwrapper52992/actual32244.
  Peer records creation times and command lines; PID alone is not ownership proof.
- Full parent model/optimizer/RNG/exposure imported exactly and independent E/C
  parent hashes verified. First new500step checkpoint is due at12500; it is not
  falsely claimed as already written at this startup observation.
- AC pass; startup ownedRSS3,103,313,920B, Cfree137,343,881,216B,
  Efree294,380,240,896B, Cbackups69,155,035,711B, Ecache24,713,390,976B.
  Reported GPU6019MiB remains under6GiB; qualification reservedpeak6,203,375,616B.
  Physical100GiBfloors and approved88GiBbackup/32GiBcache limits pass.
- Existing private phone route shows phase-local progress and retains ten historical
  runs. Runtime totals retain actual journal elapsed time; no duplicated parent hours.
- ONE hourly heartbeat`monitor-corrected-stu-net-continuation` ACTIVE, saved prompt
  reread with this exact root/ready/owner and no automatic retry/resume/successor.
  It remains quiet during healthy progress and pauses/reports failure or completion.

Mac imported the published launch, qualification and pin records unchanged and
checked their identity, global/phase arithmetic, parent equality, budget accounting,
resource thresholds and saved monitor target/prompt consistency. This is independent
saved-evidence review, not another live GPU/filesystem/MLflow check from Mac.

All225repository source identities in the peer500pin inventory reconcile to Git:
63exact Git bytes,156uniform CRLF, and six mixed LF/CRLF files. An initial stricter
uniform-EOL assumption rejected those six; peer`f467a43` supplied exact base64 byte
snapshots and line maps. Mac decoded and hashed them, matched each frozen runtime
pin, compared normalized bytes and ASTs to the exact committed sources, and found
no code difference. No producing file was normalized or repinned. See
`STUNET-CONTINUATION-MAC-SOURCE-CHECK-20261108.json` and
`source-snapshots-20261108/`. Actual remote current-byte equality is peer-attested.

Execution card: https://trello.com/c/uQpn9fze . Training is ongoing, not accepted
or complete. Pretraining exposure and formal-comparison limitations remain open.
