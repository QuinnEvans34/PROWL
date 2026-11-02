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

## One real CUDA diagnostic completed

The single authorized attempt finished normally. Request SHA256
`dc37f20affd1e071c46208ebbd8b34052aa09a704718df235de4385a48a726b3`
at E:/PROWL/readiness/week05-physical-qualification-20261102-a01/request.json.
Owned28799 supervisor39792/worker18172 exited0; workers_reaped=true and process
identities absent after completion. No remaining CUDA compute applications.
Preserve all request pins and evidence; do not repeat this diagnostic.

Exact CT restoration took274.547supervised seconds/44,638,208B peakRSS/reaped;
the native header explicitly uses mm and agrees with the expected426x301x157grid.
Real CUDA execution took89.406supervised seconds including startup; inner
inference/export73.984s,60physical windows,2,167,230,464B peak ownedRSS and
1,021,313,024B maximum reservedGPU. No limit was increased.

Localizer selected1,692,423 native voxels. The expanded closest-RAS ROI bounds
are[0,44,0] to[425,301,157], about85.2% of the original CT voxel count. This is
a large region, not evidence of accurate pancreas localization. There are zero
reconstruction gaps WITHIN that region; no annotation-coverage claim was tested.
No reference masks were accessed and no Dice, lesion recall or hypothesis verdict
was calculated. Empty/incorrect scientific outputs would not be hidden by the
engineering success status.

Native prediction and localizer masks round-tripped exactly; all three float32
probability channels round-tripped exactly in the205,780,028byte ROI array.
Nine independent E/C backup pairs were rehashed after worker completion and match.
Evidence status is LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING, not qualified.

Retained outputs in output/ under the request directory:
- prediction.nii.gz SHA6567fe103be9f88ee3f3efd5cd6f8c1643704ad774840de509b0a99a9a265d15
- localizer.nii.gz SHA471a38046762bcf1d58315b6e22228257e6db0e053bf96a2467690aa44854703
- region-probabilities.npy SHA58999e3423af1ae5d31819a5b13cbc95bd77bf5d4ec96d8f4535bbce8282bba3

The remaining admission dependency is the exact reference described in
WEEK-05-MAC-REFERENCE-REQUEST-20261102.md plus review of the predeclared numerical
proposal. No four-case batch was dispatched. Continue from the preserved output,
not a repeated inference, when the reference becomes available.
