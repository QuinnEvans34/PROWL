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
