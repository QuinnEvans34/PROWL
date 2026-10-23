# Varied lesion-focused views — qualification amendment and one-run launch

October22: user approves autonomous completion of qualification and getting the
agreed scientific run started tonight. This authorizes ONE fresh24k run named
**Varied lesion-focused views without losing coverage**, not schedules, automatic
restarts/resumes, new cohorts, a second experiment or relaxed data/metric guards.

Scientific recipe/hypothesis remain the original
[varied-focus plan](PANTS-VARIED-FOCUS-24K-20261022.md). The frozen lossless target
cache/prefetch path and all prior coverage/pilot proofs are reused. No additional
data audit, target conversion, exclusion or native cohort evaluation is required.

## Why the numerical qualification needs a controlled comparison

The original loader itself produces final-state drift beyond rtol1.3e-6/atol1e-5
across33independent GPU updates, despite identical inputs, seeds and counters.
That original-repeat maximum.00015291665 exceeded the original-fast maximum
.00012248009. This is not a statistical noise model or a new acceptance threshold.

The installed MONAI SegResNet uses three parameter-free trilinear upsampling
modules, factor2, align_cornersFalse. PyTorch2.11 explicitly lists CUDA trilinear
backward as unavailable under strict deterministic execution. Merely enabling
deterministic algorithms cannot qualify this unchanged architecture. References:
[PyTorch deterministic algorithms](https://docs.pytorch.org/docs/2.11/generated/torch.use_deterministic_algorithms.html),
local MONAI `networks/blocks/segresnet_block.py` and `networks/blocks/upsample.py`.

The amended proof has complementary parts, not an exception that skips the failure:

1. **Actual input equivalence:** existing all12full-region/windows/augmentation
   comparisons, all33ordinary GPU batches/traces and full24kschedule replay.
2. **Controlled numerical equivalence:** both33update arms use strict deterministic
   CUDA/cuDNN/cuBLAS. Only the three trilinear adjoints run through the native
   PyTorch CPU backward operator; CUDA forward, shape, interpolation and parameters
   stay unchanged. This adapter is QUALIFICATION ONLY, installed equally in both
   arms. Require the original rtol1.3e-6/atol1e-5, never a raised tolerance.
3. **Independent deterministic cold replay:** restore the candidate's penultimate
   checkpoint from C:, require exact restored state/input and the same next-state
   bound after one update. Independent backup hash must match E:.
4. **Actual-production cold replay:** restore the already saved ordinary-CUDA
   candidate checkpoint from C:, with NO adapter or deterministic-mode change.
   Require exact restored state/input and the original one-update state bound.
   Existing actual executor33updates/two native cases and worker cleanup are reused.
5. **Performance admission:** the actual-production benchmark8.370727->3.008545s
   (2.782317x) must exceed the unchanged1.10gate. Controlled CPU-adjoint timings
   are not a forecast for scientific training. Native evaluation cost remains.

Earlier nondeterministic qualification stays recorded as FAILED. The paired proof
does not claim bitwise reproducible independent long scientific GPU runs. Launch
readiness requires all complementary checks and immutable evidence, not a renamed
old pass. No engineering update contributes to scientific Dice or dashboard hours.

## Preserved wrapper failure and correction

The first deterministic wrapper expected align_cornersTrue; the actual model uses
False. It rejected the model BEFORE any CT read or optimizer update. Evidence under
`E:/PROWL/readiness/varied-deterministic-20261022-a01` remains unchanged, exit1,
workers reaped,16.437seconds. This was a wrapper admission error, not data failure.

Under the user's autonomous implementation instruction, separately versioned v2
adapter/runner match the actualFalse setting. Eight tests pass, including exact
native CPU forward/backward, double-precision gradcheck and actual frozen SegResNet
geometry/parameter identity. V1 files/pins are preserved. V2 reference budget is
1200seconds minus16.437already consumed; other stages each1200seconds,12GiBcombined
owned RSS, AC, storage floors/caps and single-GPU ownership. No unbounded retries.

## Handoff

- Qualification root: `E:/PROWL/readiness/varied-deterministic-20261022-a02`.
- Runner: `scripts/diagnostics/qualify_varied_deterministic_v2.py`, stages reference,
  producer, cold, production-cold. Inspect files/owned process before each stage;
  never redispatch an existing stage. Request pins freeze all producing code.
- Launcher: `scripts/train_varied_qualified.py`. Configuration/parent evidence and
  dashboard handoff copied exactly from prior prepared setup; nine launch tests pass.
- Once all checks pass: freeze new ready.json, use its EXACT SHA256 with
  `--launch-sha256 HASH --explicit-user-launch`. The current user instruction supplies
  one-run launch authority. No old receipt is relabeled or repinned.
- Scientific model must contain the three original nn.Upsample modules and original
  CUDA numerical mode. The launcher rejects the qualification adapter or enabled
  deterministic flags. Fresh SuPreM,24k,original1333/70, noEMA/PANORAMA/LRchange.
- Verify actual advancing updates, independent initial backup, stored MLflow loss
  and phone APIs; update only existing local dashboard configs, retain old history
  and private access. Keep AI schedules paused.96hscientific cap includesvalidation.

## Qualification results and dispatch

All four a02 stages completed successfully with workers reaped:

| Stage | Supervised seconds | Peak owned RSS bytes | Result |
| --- | ---: | ---: | --- |
| Original-path reference, 33 updates | 375.563 | 2,831,933,440 | Complete |
| Faster-input producer, 33 updates | 179.734 | 2,556,391,424 | All inputs and full model/optimizer state exactly equal |
| Independent deterministic cold replay | 25.563 | 1,801,617,408 | Exact restoration, next input and next state |
| Actual ordinary-CUDA cold replay | 22.828 | 1,711,439,872 | Exact restoration/input; maximum next-state difference 1.862645149230957e-9 |

Both cold checks pass the original rtol1.3e-6/atol1e-5. The deterministic E:/C:
checkpoint SHA256 matches:7dc8447cbe790267ece409e1251d893a83999e83456f33b92791a1baf7fa350c.
No numerical tolerance was relaxed. Earlier failed evidence remains failed and
preserved. Qualification updates are nonpromotable and excluded from training hours.

Final readiness freezes3,275producing files at
`E:/PROWL/readiness/varied-deterministic-20261022-a02/ready.json`, SHA256
`1269337a16c04fc0b9a62d142945afd649011886c004d55b0a41af96947ce49e`.
The ONE approved scientific launch was dispatched through owned session69209.
MLflow run `a84c0a6ae0cb424ca182350425adc7aa` was created.

### Launch verification,20:46MDT

Same owned session69209 remains active: supervisor60980, worker51832 (venv
wrappers62292/47468). Scientific journal and phone API advance10->17->25->36;
status API subsequently shows38updates,120.984seconds,loss1.144696593284607.
MLflow SQLite readback confirms RUNNING and storedtrain/loss at1and25;step25
loss1.1886061429977417. No tracking-warning file or terminal resource report.

Initial checkpoint E:/C:SHA256 matches:
`342691bd730908646ee8874f0530203e5e1cf96ec9decfaa069fd0f097072a17`.
Scientific artifact root:`E:/PROWL/artifacts/pants_varied_focus_24k_20261022`.
Independent root:`C:/Users/quinn/PROWL-Backups/pants_varied_focus_24k_20261022`.

Only the two existing local monitor configuration files changed after their old
hashes were verified; prior values preserved in`dashboard-before-launch.json`.
Existing server18840/28440 and private access stayed unchanged. Authenticated
browser at the existing phone URL visibly shows the live25stepcard, no invented
Dice, sixhistoricalruns and208.80hours. API subsequently confirms36steps and exact
total arithmetic751607.078historicalseconds+115.484new=751722.562;7experiments,
totals_complete=true. First Dice follows2kupdates plusfull70native evaluation.

No extra scientific run, retry/resume or schedule. All3,275producing pins remain
frozen; keep AC/app/data drives connected. Earlier pending handoff text is history.
