# Windows physical cascade execution preparation

Implements the follow-on execution scope from remote main168185a without merging
over existing producing files. Current branch:codex/week05-cuda-readiness.

The new CT-only path connects the existing full-volume localizer transform to
all predicted support, source-index physical margin expansion,144/72 physical
tiles, native-center three-class probability reconstruction and native export.
It does not call the old single144cube resize path. Localizer and segmenter use
their distinct bound intensity windows. Float32 is retained; CUDA TF32 is disabled.
No ground-truth mask is an inference input or an empty-localization fallback.

`scripts/diagnostics/qualify_physical_cascade_20261102.py` provides exact-schema
request freezing, model/source/runtime pins, one-shot dispatch, Windows Job Object
supervision, exclusive CUDA ownership, memory/time/storage/free-space/AC checks,
independent backups and cleanup evidence. The CT-only audit policy is installed
after strict weights_only loading. It permits the named CT, own output and narrow
runtime/source roots; it is a tripwire rather than an OS sandbox.

Frozen proposed diagnostic ceilings:600s supervised worker including startup,
1800s aggregate qualification ceiling (one attempt currently authorized),12GiB RSS,
6GiB CUDA reservation,2GiB output and2GiB backup,40GiB aggregate backup ceiling,
100GiB free on C/E,96M source/native-region voxels and512 physical tiles maximum.
The exact localizer recipe retains its16M resampling ceiling. These are refusal
limits, not targets; no crop narrowing, patient exclusion or automatic retry.

Focused tests passed30/30 (13.88s), evidence
E:/PROWL/readiness/week05-cuda-baseline-20261102-a01/cpu-executor-03.xml.
They cover real synthetic full chain, empty/invalid localization, physical tiling,
exact agreement with the existing control predictor across tile edges, native
orientation/export composition, reference-read refusal, request restrictions,
duplicate refusal, and actual Windows normal/failure/timeout/cancellation cleanup.
Earlier27/29-pass reports are preserved. All270 prior verifier repository pins
were rechecked unchanged before commit. This does not establish real GPU parity.

Only PanTS_00001070 is authorized for this diagnostic launcher. Exact CT restoration
is a separate600s CPU/2GiB stage from the already verified training archive; no
whole-cohort audit or test/label extraction. Its log/resources live in the existing
Week5 readiness directory. It must finish and header-unit checks must pass before
preparation. All failed stages are preserved; do not repeat a started stage.

Commands, usable only in order after verifying absence of prior stage evidence:

```powershell
.venv-prowl-windows/Scripts/python.exe scripts/diagnostics/qualify_physical_cascade_20261102.py --prepare E:/PROWL/sources/pants/week05-diagnostic-20261102-a01/PanTS_00001070.nii.gz
# Use the exact request_sha256 printed above, not a guessed or historical value:
.venv-prowl-windows/Scripts/python.exe scripts/diagnostics/qualify_physical_cascade_20261102.py --run-sha256 <exact-request-sha256>
```

A successful diagnostic records LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING,
not scientific acceptance, a Dice result or batch readiness. Scoring is separate.
The four fixed cases remain blocked on numerical-reference/admission qualification;
the current launcher cannot expand to them. See WEEK-05-MAC-REFERENCE-REQUEST-20261102.md
for exact minimal input/output dependency and the pre-result numerical proposal.
No Mac KD interruption, training launch, dashboard-hour increment or schedule.
