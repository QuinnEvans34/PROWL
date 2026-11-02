# Week 5 autonomous CUDA execution — November 2

This follow-on implements Quinton's request to get the autonomous localizer test
running on the other laptop. It supersedes the preparation-only dispatch wording
in WEEK-05-CUDA-BASELINE-HANDOFF-20261102.md for the bounded qualification and
initial development evaluation below, once their gates pass. It does not authorize
new training, final-test access, policy search, retries or interrupting Mac KD.

## Inputs already delivered

Use the verified private packet at
E:/PROWL/transfer/week05-cuda-baseline-20261102-a01/extracted/week05-models-provenance.
The sibling receipt.json records archive SHA256
90b1f308de6be6e3abe38992d463a393798111798bdec74d5506bde0a887fec2,
34,975,283 bytes and all16 verified payloads. Both models already loaded strictly
on CPU. All70 development identities matched; the five proposed cases' CT/metadata
hashes matched. Reuse these checks; recheck pins before execution, not full audits.
The current segmenter is the exported control step20000, not historical segmenter
weights mentioned in checkpoint-review.json. control-provenance.json governs it.

## 1. Finish the actual Windows executor

Continue the existing codex/week05-cuda-readiness branch and physical-region bridge.
Add the smallest separately versioned worker and request/evidence path that connects
CT-only localization to physical144 windows/72stride and native reconstruction.
Preserve existing reproduction paths and all producing pins. Bind the exact
localizer normalization and all-support selection policy; do not silently enable
largest-component selection. Preserve the control's HU[-100,250] normalization,
source-index margins with separate ceil operations and native probability blending.

Use existing Windows supervision, exclusive CUDA lock, resource admission and
owned-process cleanup. Prediction gets only CT, models and configuration; reference
masks must be inaccessible to it. Keep scoring and any provided-region diagnostic
in separate, explicitly labeled stages. Empty localization or invalid geometry is
an explicit outcome, never repaired from reference annotations.

Focused CPU tests must exercise request binding, geometry/native reconstruction,
reference-access refusal, invalid/empty localization, cancellation, timeout and
worker cleanup. Reuse existing tests and synthetic workers. Stop this block when
these pass and a runnable bounded qualification command exists; no extra framework.

## 2. Freeze and qualify one case

Retain the laptop's proposed diagnostic PanTS_00001070. Bind CT/metadata identities,
weights, source/environment hashes, policy, exact output schema and fresh output root.
Write explicit numeric per-case/total time, RAM/VRAM and storage ceilings using
applicable qualified Windows limits; never waive them. Preserve AC and drive gates.

Resolve the missing same-recipe cross-device reference before calling the pipeline
qualified. First inspect whether a retained current-control native prediction can
serve as a matched provided-region reference: exact case, checkpoint, region,
preprocessing and output representation must match. An old resized-crop prediction
or a Dice summary cannot substitute. Specify the existing applicable numerical
comparison rule before observing new outputs; if none applies, report the proposed
rule for review rather than inventing a passing tolerance afterward.

If no valid retained reference exists, prepare the exact bounded Mac request and
minimal output needed, and report that dependency promptly. Continue Windows CPU
integration while blocked. Do not pause Mac KD or claim this gate passed. Real
Windows diagnostic execution is authorized after its local safety/request gates
pass, with results retained as qualification evidence pending cross-device checks.
One attempt only; preserve and diagnose any failure before proposing continuation.

Qualification must verify source/native shape and affine, units, probability/class
mapping, finite output and coverage/reconstruction, in addition to numerical checks.
A failed scientific prediction is an observed result; a broken coordinate transform
is an execution failure. Record both honestly and separately.

## 3. Launch the bounded development batch after qualification

Use the already proposed fixed four cases, without outcome-based substitutions:
PanTS_00002028, PanTS_00000909, PanTS_00004681, PanTS_00006755.
Freeze their identities and exposure flags before inference. These are exposed
development cases, not independent acceptance. Keep all failures in the denominator.
Once all qualification and admission gates pass, execute this one bounded evaluation
without waiting for another routine confirmation. Do not expand to all70 cases yet.

Report pancreas localization containment/crop size separately from pancreas and
lesion segmentation overlap. Report lesion misses/recall, false positives and empty-
reference behavior where applicable, native geometry, latency and peak resources.
Do not infer lesion-level detection from voxel recall or silently change metric
definitions; reuse the repository metric specification. Run a separately labeled
matched provided-region diagnostic only within the frozen budget to distinguish
localization errors from segmenter limitations. Do not credit it as autonomous.

Finish with preserved per-case outputs/failures, integrity receipts, cleanup proof
and a concise interpretation. No model-quality threshold is a prerequisite for
reporting an honest baseline; qualification means the implementation is trustworthy,
not that the model is good. No tuning or repeated selection on these outputs.

## Coordination and stopping conditions

Start implementation now. Commit small changes and push the readiness branch when
safe; do not merge over live producing pins. Keep W05-09/W05-01 status accurate.
Record progress and blockers in the laptop chat so the Mac can inspect them.
At the missing-reference gate, give the exact dependency and runnable request rather
than stopping with only a generic readiness statement. Stop on failed safety,
integrity or geometry checks. After the four-case result, return for review before
expanding scope. Mac KD continues throughout unless Quinton separately approves a
reference-generation pause.
