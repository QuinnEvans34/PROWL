# Bounded localizer executor — completion and launch handback

September 28, 2026. D-274 implementation complete. **1,074 native tests pass** (two existing
upstream torch.jit deprecation warnings). The final synthetic MPS rehearsal, before/after exports,
external checkpoint publication, independent backup and fresh-process restore all pass.
**CAP-EXP-001 has not launched; no real CT optimizer update occurred.**

## What is now implemented

- `src/training/localizer_smoke.py`: exact alternating membership, fixed update horizon and checkpoint
  cadence, image-only full-volume before/after inference, independent metric checks, binary native
  NIfTI exports, three-plane contact sheets, separate mechanical completion and learning indicator.
- `scripts/diagnostics/localizer_smoke_run.py`: immutable request preparation, explicit pinned launch
  authorization, source/environment revalidation, native MPS worker, independent supervisor and
  fresh-process backup recovery. Pending authorization is refused before input payload/model work.
- Version3 run identities bind exact input/source/environment/plan/authorization bytes; checkpoints
  include model, optimizer, scheduler, completed step and case/crop/loss/timing history. Earlier
  version2 bridge identities remain supported, with their verification-only public update gate.
- Terminal bundles retain before/after evidence and a fixed reload probe. Backup verifies the
  original completion receipt and every member, then restores to a new destination on the independent
  internal volume. Recovery refuses primary-volume opens/listings and checks MPS predictions.

There is no automatic resume or extension in this small executor. Failures retain the last complete
checkpoint and partial attempt evidence. Real checkpoints are scheduled at 0/25/50/75/100; up to24
completed updates may be lost between them. Failure paths do not spend an unbudgeted emergency-save
allowance. The prior CPU synthetic interruption/restart evidence remains valid, but does not imply an
automatic MPS resume command here. An interrupted real smoke requires review before another attempt.

The update phase is checked before and after input/update work, and separately observed by the
supervisor. Total wall time, AC, sampled RSS, stage-boundary MPS driver memory, free-space floors,
root continuity, per-area quota and exclusive accelerator ownership remain enforced. Polling and
shutdown are bounded checks, not instantaneous hardware guarantees. Load-and-update time includes
input verification/preprocessing; it is not advertised as isolated accelerator kernel time.

## Final native rehearsal

The final source revision ran on two **invented** 96³ cube volumes, with two updates, one per fixture.
Synthetic descriptors intentionally exercise the same two-slot identity plumbing; they are not CT
measurements or a reuse of real case targets. Run identity explicitly says `training_data: synthetic`.
All rehearsal weights are excluded from CAP-EXP-001 initialization.

Run directory:
`outputs/prowl/localizer-smoke-f3f2512d-8a34-4b72-bf3e-a1bd449e9a3c`

| Evidence | Result |
|---|---|
| Mean full-volume loss | 1.603314 → 1.245815 |
| Mean foreground Dice | 0.016713 → 0.855610 |
| Preset synthetic learning indicator | Passed; this is not CT/generalization evidence |
| Complete checkpoints | Steps0,1,2 plus terminal bundle |
| Native binary masks/contact sheets | Four of each, before/after for both fixtures |
| Whole supervised run including restore | 17.54 seconds |
| Peak sampled worker RSS | 1,394,589,696 bytes (1.30 GiB) |
| Peak boundary MPS driver allocation | 2,479,734,784 bytes (2.31 GiB) |
| Terminal directory including receipt/journal | 64,287,479 bytes |
| Restored fixed-probe maximum absolute difference | 0; within atol1e-5/rtol0 |

RSS and driver allocation overlap; do not sum them. Sampling can miss brief peaks. All four contact
sheets were visually reviewed: after-training predictions overlap the synthetic target, with residual
boundary overprediction visible. The final revision's four PNGs are byte-identical to those reviewed
from the preceding timing-instrumented rehearsal. Native shape/affine/binary semantics are checked
by the terminal validator. These sheets use target-positive slice locations for **display only**;
model inference receives only the image and uses no target-derived ROI.

| Artifact | SHA-256 |
|---|---|
| Final diagnostic receipt | e6079addcf4995873f127f86766167faad147eea641a851228b45759b9037e48 |
| Terminal primary completion | 258c8ce28b8143099880259a1df54a5fdcc79893fe8cef28b8aa8ecdbacb262c |
| Independent backup completion | 2ac44098a952b72bcf48729ee8b1a7b93fbae4eb8baebb69cecb3aa18986f9fd |
| Restored artifact completion | 2826d6b2c2c0ef89443743a4a0bc00683f012329f704f897b9b20ef3c679eb8a |

The backup contains the terminal checkpoint, source/config/identity controls, metrics, masks and
contact sheets, plus original primary completion and journal. Intermediate checkpoints stay primary;
raw data are not mirrored. Existing D-273 storage areas and independent UUID checks were reused;
global source aliases/scientific roots remain disabled.

### Earlier retained rehearsals and test correction

1. `localizer-smoke-ce9c92bf-aeba-432b-ab16-dab007da9fe6`: first complete end-to-end success,
   receipt `126e7e95a7e2c3c3eda13708e413f554eeae32e3dbd6b1f4908d58574c8af1db`.
2. `localizer-smoke-802cd2b0-7ef9-4289-8052-ee453999e85b`: verified added timing/driver reporting,
   receipt `7c6b5292df0b58ecd22ba9eb13f9e5f0605655f66ec8df8f2c074e39ee7301ea`.
3. Final run above additionally verifies update-phase supervision. These are engineering rehearsals,
   not three scientific experiments. All complete attempts remain preserved.

The new persistence-fault test initially called the existing resolver without its required validator.
The tested failure behavior had passed up to that assertion; the test call was corrected, then the
full suite passed. Final tests cover a failed checkpoint retaining step0, no false terminal completion,
a slow input exhausting the update budget **before** optimizer work, wrong/pending authorization,
case ordering, metric oracle/empty handling, export validation and explicit learning-null outcomes.

Native verification command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Final result: **1,074 passed**, two known warnings,13.81s. `git diff --check` passes. No dependency,
Git commit/push, raw-source modification, training-role change or retrieval planning-file edit.

## Concrete real launch request

[Launch design](CAP-EXP-001-LAUNCH-PLAN-2026-09-28.md): scratch pancreas localizer, qualified cases3/26,
100 alternating updates,96³/batch1/fp32 MPS, seed42, AdamW0.003/cosine100. Before/after full-volume
metrics and native exports; checkpoints every25 and independently restored terminal keeper.
Limits600s update phase/1,200s total,16GiB memory,1GiB new output per domain, AC and existing floors.
This smoke asks whether the real input/training/preservation path works and shows tiny-set learning;
it cannot establish generalization or lesion quality.

Prepared directory:
`outputs/prowl/localizer-launch-request-f0943201-0e6d-4c7d-b140-61c7bb4f1efa`

| Control | SHA-256 |
|---|---|
| Request | 9b54a25d3ad014ca325464d35046496357f2e7969c9f4b2ddbd04e1ba2196452 |
| Resolved input record | b70adb8f3eb679f4ffc747384e58f1c821a42267e02946287fc3b436fcad79a6 |
| Source capture | dc800a48e856b8a2cce11b4790424789989468e7115bf2c9da44f5abe877355c |
| Environment capture | 2c7b2cf2158b183f766b14e2edcadc9b8db52287edd4e2eff8fe96f9322c8426 |
| Executable plan | f9f1f91cd97c0f7080607db0774a9961342687908e899f1fb4bfa192e0eb3415 |

Preparation resolved cohort metadata, not source voxels. Its source/environment bytes match the final
native rehearsal exactly. `outputs/prowl/localizer-launch-request-verification-2026-09-28.json`
records this check and refusal of `authorization-PENDING.json`. No approved authorization was created.
Earlier request `localizer-launch-request-b8756c5a-fa82-4506-8e6a-7924c71a995d` is retained but
superseded after deadline-check code changed; do not launch it.

**Next action is Quinton's specific launch decision**, as agreed in D-273. Upon approval, record a
new authorization binding these exact controls and the one-run scope; preserve the pending file.
The new record adds real optimizer permission to the already scoped storage envelope. It is not
an amendment pretending D-273 itself allowed training. Immediately recheck source/environment,
cohort/purpose permissions, power, mounts and quotas; changed bindings require a new request.
Use the launch CLI with both request and new authorization hashes. Then review the retained result,
including null learning/failure, and propose the next experiment. No additional broad investigation
or completed literature system is required before this small launch.

## Claude P2 review

[Separate written review](../retrieval/CODEX-P2-OUTLINE-APPLICATION-REVIEW-2026-09-28.md) verifies the
five handback hashes and preserves reported decision provenance. P2 remains unfrozen/unsigned.
Main changes: distinguish analogical detection-reader evidence from direct contour-review coverage;
avoid claiming all four recommended titles prove automation bias; reconcile the one-transfer/two-
attempt download wording; separate proposed/provisional/verified coverage counts. Recommendations
on all nine new candidates, eleven reserves and C-25 are included for Quinton's discussion.
