# Lenovo handoff: train for imperfect pancreas localization

**Prepared:** October 9, 2026  
**Owner:** Quinton + Lenovo training chat  
**Status:** Next-experiment implementation specification; not an executable launch configuration  
**Scope:** One controlled crop-variation experiment on the NEW full segmenter trainer.

## Start here

Training is already running on Lenovo, according to Quinton. Preserve that process, environment,
configuration, dataset membership and checkpoints. Prepare this experiment alongside it and launch it
as the next job when the current run finishes and the checks below pass. This document supersedes the
old setup handoff's assumptions that Lenovo has no data or CUDA setup. Do not reinstall a working
stack or launch a competing GPU job to repeat setup checks.

Quinton will reference this document in the Lenovo chat. That chat should inspect its actual checkout,
CUDA implementation and current run before resolving machine-specific details. Mac cannot currently
verify that runtime remotely. This file does not itself start training or contact another chat.

## The question

**Does exposure to larger, imperfectly centered pancreas regions during training improve raw-CT
end-to-end lesion segmentation, with the localizer and inference policy held fixed?**

We are testing robustness to the crop the segmenter receives. We are not changing network architecture,
adding PANORAMA, training another localizer, changing the loss or tuning inference thresholds in this
experiment. Those would obscure what caused a difference.

## Why this is the next experiment

Mac diagnostics used the same fixed segmenter on the same 33 lesion-positive and 35 reference-empty
development cases. Seven other development cases remain unresolved because CT spatial units are absent.

| Input region | Positive-case lesion Dice | Mean lesion output on empty references |
|---|---:|---:|
| All predicted pancreas support +10 mm | 0.225818 | 21.291808 mL |
| Largest predicted 26-connected component +10 mm | 0.246612 | 13.989806 mL |
| Reference pancreas crop +10 mm, diagnostic only | 0.422671 | 1.527572 mL |

All 33 lesions were entirely inside both predicted-box policies. All 41 lesion components survived the
all-support/reference preprocessing comparison. The all-support crop had median paired physical volume
5.53× the reference crop; the largest-component candidate still had 3.99×. Crop choice therefore matters
beyond simply including the lesion somewhere in the box. Reference-crop scores are oracle-assisted
comparators, never autonomous performance. Empty lesion annotations do not establish verified health.

These are selected development results, not a published PanTS benchmark or a clearance of patient/source
leakage. Full evidence: [checkpoint/crop investigation](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md).

## Preserve the current control and identity

Use `scripts/train_full_segmenter.py` and the `segmenter_full_session_v1` /
`segmenter_full_executor_v1` architecture, with Lenovo's verified CUDA/resume support. Do not switch to
the legacy trainer. Preserve Lenovo edits and record its branch/commit and uncommitted changes before
integrating relevant Mac code; a Mac commit does not automatically appear on Lenovo. Do not pull/reset
or change imported files underneath the active training process.

Relevant Mac commits: `19e8b87` geometry capacity/unit-review support; `2756f0b` matched diagnostic;
`358cd35` experimental largest-component crop policy. These do not prove that Lenovo has the same code.
Keep data, weights, caches and run outputs private; transfer missing code privately or through an
already-authorized repository workflow. No public push or cloud spending is requested here.

Record the current Lenovo experiment's actual initializer, optimizer, loss, precision, seed, sampling,
update budget and validation/checkpoint cadence. Inherit those verified settings for the challenger.
The historical Mac reference was SuPreM initialization, AdamW at 1e-4, 500-step warmup/cosine, 144³ input,
24,000 updates, validation every 2,000 and checkpoint every 500; this is context, not permission to replace
Lenovo's actual working configuration with a Mac YAML file.

For a controlled from-initialization comparison, use the same pinned starting weights and horizon as
the control. Do not silently start from the current run's best checkpoint: that changes training exposure
and creates a fine-tuning experiment. If only fine-tuning is practical, label it as such and use an
equal-duration fixed-crop continuation from the same parent as its control. Never call that comparison
a matched from-initialization result. Do not lower the training horizon to turn this into another micro-run.

## Recommended first crop recipe: CV01

Freeze this recipe before the long run. It is a proposed experimental setting, not an optimized range.

- Keep the existing reference-pancreas bounding box and 10 mm margin as the **base training box**.
  Reference masks are legitimate training supervision. Never use lesion boundaries to choose the box.
- Keep one original view and create one deterministic expanded/offset view per training case.
- For the expanded view, draw one scale uniformly from `[1.0, 2.0]`, shared across the three box axes.
  Expand each native-axis box extent by that factor around its center. Physical geometry remains governed
  by the actual affine; do not assume isotropic native voxels or alter the source header.
- On each axis, choose the center offset uniformly within the extra half-width introduced by expansion.
  This gives off-center views while containing the entire base box. Round bounds outward and clip to the
  source volume; assert the resulting box still contains the original base box.
- Derive the case's variant deterministically from a recorded experiment seed and stable case ID, using
  a stable digest or stored draws—not Python's process-randomized `hash()`.
- Keep the same case sampler. After choosing a training case, choose original/expanded view with 50/50
  probability from checkpointed RNG. Record case exposures separately from variant exposures.
- Keep 144³ tensor shape, HU normalization, interpolation, labels, loss and optimizer unchanged.
  This initial experiment changes training crop distribution, not the network or inference policy.

This is a finite two-view-per-case augmentation bank, not unlimited random jitter every update. It is
intentionally small enough to implement, cache and explain. The scale range can produce up to 8× box
volume before source-boundary clipping, allowing broader context like the observed predicted crops.
It does not reproduce every localization error, and its effectiveness remains an empirical question.

### Source data and cache requirements

Read the larger region from the original CT and labels, or from an independently qualified cache that
retains that region and geometry. **Do not enlarge, pad or jitter the existing final 144³ reference-crop
tensor and claim it contains the surrounding abdomen.** That information has already been discarded.

Use a separate versioned augmentation/cache namespace. Bind each variant to case ID, source hashes,
actual crop bounds, recipe/seed and transform. Do not overwrite or silently rebind the current run's
cache. A cache keyed only by case ID is insufficient when there are multiple views per case.

Audit proposed variant sizes and storage before building the full bank. Measure preparation cost on a
small representative training subset, then prepare admitted variants once rather than reopening and
resampling the source CT on every optimizer step. Reuse existing trustworthy base-cache evidence where
supported. Preserve a byte budget and independent checkpoint backup; use actual Lenovo free space.
The 64M intermediate-grid support is available on Mac, but CUDA/host fit must be measured on Lenovo.

Expand and offset CT and labels with the same physical transform. Record lesion component survival
and tensor voxel counts. Do not silently skip cases, redraw a crop until a lesion survives, or fall back
to the reference crop based on a lesion mask. If the fixed recipe loses components or does not fit,
report the failure and revise the recipe globally before the long launch; preserve that failed audit.
Containing the native box does not guarantee a small lesion survives resampling to 144³.

## Cohort and inference boundaries

Use the frozen 1,333-train/75-development memberships only if they match the current Lenovo admission.
Otherwise report the exact difference before claiming comparability. Preserve original split files,
case/source identities, exclusions, reviewed target states and SuPreM development-use limitations.
Never reconstruct the training cohort from a directory glob. Do not introduce test cases or new datasets.

Build augmentation variants for training members only. Development scoring uses fixed transforms and
fixed policies, never random validation crops or optimizer exposure. Predictions take CT only; references
enter a separate scorer afterward. Do not select an inference crop, component, margin or threshold from
a development case's reference mask.

Keep the current all-support +10 mm autonomous policy as the primary comparison; largest-component +10 mm
may be reported as a frozen secondary policy. Do not change policy between control and challenger.
Keep reference-crop evaluation as a separate diagnostic to detect a tradeoff in the old training domain.

Seven development CTs have unresolved spatial units: `PanTS_00006011`, `PanTS_00005780`,
`PanTS_00001823`, `PanTS_00002935`, `PanTS_00005370`, `PanTS_00006901`, `PanTS_00006115`.
They remain in 75-case accounting; do not silently interpret their coordinates as mm. Mac has a tested
CT-hash-bound unit-review mechanism but has not fabricated reviews for these cases. Also preserve the
flagged anatomy/annotation concern for `PanTS_00001389`. Do not alter an active run's cohort; disclose
these issues and reconcile unresolved admission questions for the successor before claiming clean data.

## Minimum checks before the long launch

Reuse existing successful CUDA, checkpoint and loader checks when their relevant code is unchanged.
Add only checks needed for the new sampler, geometry and cache behavior:

1. **Geometry/cache:** original and expanded variants differ as specified, use matching CT/label grids,
   restore to native coordinates, retain required target support, cannot collide in the cache and remain
   reproducible for a given case/seed. A synthetic case must demonstrate use of anatomy outside the base
   crop. Check boundary and tilted-affine behavior.
2. **Short actual CUDA integration:** use a few representative admitted training cases to exercise both
   variants at the intended tensor size. Confirm finite losses, genuine parameter updates, throughput,
   peak host/VRAM usage, checkpoint writing and backup. Mark it an integration run, not scientific evidence.
3. **Resume:** restore case/variant choices, progress and RNG from a checkpoint and compare the next
   update with an uninterrupted reference under the existing justified tolerance. Sampler changes make
   this relevant even when ordinary optimizer resume was already tested. Reject incompatible identities.
4. **Evaluation:** the same frozen checkpoints/cases can produce CT-only outputs and separately scored
   native metrics, with failures and empty references accounted for. Reuse the Mac evaluator if porting
   it is extra work; evaluation tooling need not hold up a qualified long training run.

After these checks pass, write the concrete resolved config/command and start one successor run at the
next available training slot. Existing user intent is to keep long experiments moving; do not turn routine
implementation choices into another approval chain. A genuine unresolved data/recipe decision should be
stated specifically, with unaffected preparation continuing.

## Evaluation and success criteria

Compare control and challenger at the same completed-update horizon and with the same model-selection
rule. Use terminal checkpoints as the primary matched comparison; report best-checkpoint diagnostics
separately with their selection history. Preserve existing periodic training validation. Evaluate the
fixed autonomous cohort at completion; do not run a full cascade on every optimizer step.

Report paired lesion Dice/recall on positive references, pancreas+lesion union Dice, lesion output volume
on reference-empty cases, missed lesion components, crop/transform failures, all 75 case outcomes and
runtime. Show case-level gains and regressions, not only a favorable mean. If only 68 cases are qualified
for autonomous inference, say 68/75 explicitly. Reference-empty is not synonymous with clinically healthy.

The hypothesis is improved autonomous Dice without sacrificing lesion recall or materially increasing
false positives. No numerical improvement is promised. If metrics trade off, report the tradeoff; do not
promote solely on Dice or decide a new operating threshold after seeing the result. Development results
are not untouched-test performance, JHU equivalence or proof of no source/patient overlap.

## Compact handback to Quinton / Mac

- Actual code commit/patch and environment; current run status and preserved artifact locations.
- Exact control/challenger initialization hashes, cohorts and relevant config differences.
- Final crop recipe, variant identities, source/cache locations, preparation/storage measurements and
  fidelity failures or exclusions. Explain any deviation from CV01.
- Relevant test results; CUDA fit/throughput; checkpoint/variant-resume evidence and stop command.
- Run ID, exact launch command, target updates, cadences, resource limits and backup location.
- At completion: checkpoint hashes and the paired evaluation report with failures/limitations.

Keep machine-local paths and data in the private runtime handback, not in published source. Do not
message another chat automatically; Quinton will relay the handback. Unattended training/preparation
time is not human project time.
