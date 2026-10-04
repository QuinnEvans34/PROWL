# Localizer adapter, synthetic learning and recovery handback

September 28, 2026. The CPU synthetic learning/recovery slice passes. Quinton's explicit request
is recorded as D-271. This advances Phase D; it does not close production run readiness or launch
real-data training. [Pre-execution plan](LOCALIZER-LEARNING-PLAN-2026-09-28.md).

## Implemented

- `src/training/localizer.py`: existing SegResNet builder, scratch-only CPU float32, one input/two
  output channels, 4,700,914 parameters, GroupNorm, no dropout; AdamW, foreground soft Dice + CE,
  cosine step schedule and finite gradient/parameter checks. No old checkpoint discovery.
- Training patches: bounded multiples of eight, up to 96³; deterministic choice from seed/completed
  step/member, equal foreground/background-center probability, image/target alignment, symmetric
  zero-padding and trace. This is pancreas sampling, not lesion sampling. Empty reference uses CE
  only; reference-empty foreground Dice is null, with predicted foreground count retained.
- Image-only full-volume sliding-window prediction uses the same patch shape, 25% overlap and CPU
  stitching. No target argument or target-derived inference crop. Existing probability restoration
  is tested against the recorded native grid. Real adapter shape 96³ is tested; learning uses 16³.
- `src/training/localizer_checkpoint.py`: exact synthetic run/config/code/environment/input identity,
  safe weights-only deserialization, model/optimizer/scheduler/CPU RNG and completed-step state,
  semantic validation into a fresh session, explicit completion pin and non-overwriting shared
  artifact publication. Corruption, missing moments, changed configuration/parents and inconsistent
  schedule/step are rejected. No fallback optimizer or implicit latest-file resume.
- `scripts/diagnostics/localizer_learning_check.py`: retained precompute source/environment/config
  records, intentional subprocess SIGTERM after step 4 checkpoint, fresh-process resume, independent
  uninterrupted trajectory, final reload, hashes and local tracking report. No service dependency.

Restart support is a **completed optimizer+scheduler step on CPU**. Stateless sampling removes the
need to serialize a mutable sampler; dropout, workers, augmentation and cache are absent. This is
not a mid-update recovery promise or a bitwise MPS guarantee. If an update fails, discard that session
and restart from an explicitly pinned complete checkpoint. Partial publication attempts stay retained
and unresolved. The store's cooperative lock and pinned receipts are the existing shared controls.

## Measured diagnostic

Successful package: `outputs/prowl/localizer-learning-d1716414-bc04-4ffd-9dbd-ab5e22f21dc5`.
Receipt SHA-256: `18a4a2f3a66a56b83875d8c0e48a0075cb63174f0c1ce004dc4061c7d4b8a6d0`.
All **15 covered files / 113,094,278 bytes** verified independently after completion (plus receipt and
store lock). Source/config/environment captured before compute; synthetic diagnostic is non-promotable.

| Observation | Result |
|---|---:|
| Fixed-fixture loss | 1.485633 → 0.703371 |
| Invented-cube foreground Dice | 0.073350 → 0.919831 |
| Completed trajectory | 20 optimizer steps |
| Total computation, including comparison | 40 updates: child 4, resumed 16, uninterrupted oracle 20 |
| Worker termination | SIGTERM, exit -15, after completed step 4 checkpoint |
| Resumed vs uninterrupted weights/predictions | Bitwise equal on this CPU fixture |
| Final checkpoint reload predictions | Bitwise equal |
| Diagnostic timed interval | 3.342 seconds, excluding parent import/source-capture startup |
| Parent / child peak RSS | 883,195,904 / 691,421,184 bytes; separate process peaks, not simultaneous total |

Step-4 receipt: `3004f2b851fe3cfdfe65efd61e4d707e4133c3522fd86ab116b911ac4d33273b`.
Step-20 receipt: `073080d394c1b28c64b5b66ca7968ba111da5b4858251ba1459297abf7be5322`.
These metrics concern an intensity-coded invented cube, not anatomy or generalization. They establish
that this loss/model/update path can learn a known signal. No raw CT, lesion or test payload was read.

## Failures preserved and tests

First diagnostic package `outputs/prowl/localizer-learning-a04795a9-193f-43c1-8ec8-fa01451ceb0a`
failed at its first save after four synthetic updates: the script passed a relative artifact root.
The shared store correctly refused it. Failure, worker traceback and precompute capture remain.
The corrected runner uses the verified checkout's absolute output path and a new package/run ID.

Focused tests: **21 passed**. Full native suite: **1,034 passed**, two existing torch.jit warnings,
11.98 seconds. Command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Coverage includes scratch seeds, actual learning/gradients, aligned 96³ padding and varied-volume
sampling, empty metrics, odd-shaped image-only inference/restoration, checkpoint reload and continuation,
wrong identity, corruption, missing optimizer moments, wrong step/scheduler/RNG, nonfinite weights,
non-overwrite collision and interrupted publication/retry preserving the earlier checkpoint.
The first full suite exposed two old metadata-unit-test failures because process-lifetime peak RSS
now included preceding model tests. Their resource observation is now isolated to a fixed synthetic
64 MiB; the explicit one-byte limit rejection remains. Production memory guards are unchanged.
`git diff --check` passes. No dependency, historical trainer or sealed data-policy change.

## Remaining before real training

1. **Production run binding:** consume the verified dataset descriptors/transform records through
   this adapter and construct the real run identity from the frozen cohort, recipe, captured source
   and environment. Current checkpoint identity deliberately accepts only CPU synthetic diagnostics.
   Add and verify a scoped production run/checkpoint root capability; do not widen the existing
   cohort-only capability or turn on generic scientific roots.
2. **MPS validation and resource profile:** explicit MPS device path, finite learning/update and
   reload tolerance, measured 96³ memory/throughput, CPU-stitched full-volume inference, bounded
   checkpoint timing/disk and independent keeper restore. No silent CPU fallback. CPU-only fixture
   results do not forecast accelerator or real-volume throughput.
3. **Freeze and review the smoke:** exact patch/sampling/learning-rate/schedule/step/time/memory
   limits, checkpoint cadence, power/drive conditions and CAP-EXP notebook entry. The candidate
   96³ adapter and 50/50 centers are engineering defaults, not evidence of optimal training choices.
4. **Tracking scope:** canonical local records work independently of a service. MLflow export and
   full Plan 06 run-schema integration remain; no tracking-service integration is claimed here.

The next useful task is the bounded MPS/profile and production run-binding slice, then a concrete
launch review. Claude P2 choices remain pending and independent. No commit, push, external write,
real-data training, model download, literature change or messaging occurred.
