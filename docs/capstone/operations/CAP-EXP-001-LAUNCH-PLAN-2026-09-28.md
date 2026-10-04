# CAP-EXP-001 — two-case scratch pancreas-localizer smoke

**Status: executor implemented and synthetically verified; ready for specific launch review, not launched.**
September 28, 2026. The prelaunch bridge/recovery verification is a separate diagnostic, not this
experiment. D-273 does not authorize real optimizer updates. A reviewed, hash-pinned launch authorization must bind this plan and its exact input/source/environment
controls before real training starts. That successor record adds this one real run to the existing
D-273 storage envelope; it does not mutate D-273 or enable global scientific roots. No rehearsal weights
or historical project checkpoint may initialize CAP-EXP-001.

## Question and decision

Can the qualified two-case pancreas-only path execute a bounded MPS training run, learn a measurable
signal on those same cases, preserve its outputs and recover its final checkpoint from independent
backup? This is a wiring/learning smoke, not validation of generalization, lesion detection or clinical
contour quality. Cases are a convenience subset from the retained investigation; no population claim.

If mechanics pass and learning is observed, next expand qualification into a new frozen cohort and
plan a development experiment. If mechanics pass but learning is not observed, retain that result and
review optimization/sampling/geometry before proposing a new run. Never extend this run automatically.
No result changes original membership or makes a difficult case ineligible.

## Frozen input and model choices

| Field | Exact choice |
|---|---|
| Cohort | `cohort:pants-localizer-smoke-0001:v1`; cases PanTS_00000003 and PanTS_00000026 only |
| Completion pin | `37a4f6a8e248200de579a31631d740b5009b0836147b382aff50212084cb632c` |
| Manifest pin | `12ba8fe0a7013db13d06b0e0ea87ea949f167896bee9d2712b2d1d0f18d83220` |
| S3 qualification receipt | `7018583fa42310a4a179efc0d5570eebb605a4b2d49c2f9883c33315b43872b2` |
| Read capability | D-270 SHA `0e0a05279dead8c365a3359f35da260aacdcca20c98400ddb820242a1ed80473` |
| Preprocessing file SHA | `3bdc8ae7f60039b6a3e4e8a3ae2629255af4f3519ff83814145f7988d2242f94` |
| Input/target | One normalized CT channel; binary pancreas under approved D-259; no lesion mask |
| Geometry | RAS, 3 mm, HU [-100,300]→[0,1], nearest target interpolation, zero-pad minimum 96³ |
| Model | Scratch MONAI SegResNet, 16 initial filters, GroupNorm 8, blocks (1,2,2,4)/(1,1,1), two logits, dropout off |
| Device | Native MPS, fp32, fallback disabled; unavailable/unsupported MPS stops the run |
| Randomness | Seed 42; scratch initialization, stateless crop key (seed, completed step, member ID) |
| Sampling | One 96³ patch/update; equal foreground/background-center probability, recorded crop origin; center class does not imply whole-patch class |
| Member order | Alternate 3,26 starting with 3; 50 updates/case if all 100 complete |
| Workers/cache/augmentation | 0 / none / none; one verified dataset instance, recheck source bytes at each consumed load |
| Loss | Foreground soft Dice loss (smoothing 1e-5) + mean voxel CE, unit weights; empty reference contributes CE only |
| Optimizer | AdamW, LR 0.003, weight decay 1e-5, betas (0.9,0.999), eps 1e-8; no accumulation or clipping |
| Schedule | CosineAnnealingLR, T_max 100 optimizer updates, eta_min 0; scheduler after optimizer |
| Horizon | Exactly 100 maximum updates, subject to earlier stop conditions; no early selection/extension |

These optimization values aim to test tiny-set learning. They are not a claim of optimal pancreas
training or a commitment for subsequent baseline comparisons. The protected validation/test
roles are not changed or consumed (parents remain 7,200 train / 1,800 validation / 901 test).

## Measurement and evidence

Before update 1 and after the final completed update, run image-only full-volume inference on both
training cases: 96³ sliding windows, batch 1, 25% overlap, constant blending, MPS predictor and CPU
stitching. No target-derived inference crop, true-pancreas ROI or target channel.

Report each case and the equal-case mean:

- Full-volume foreground Dice from two-channel argmax against the preprocessed target. Empty reference
  is null with foreground counts; both frozen targets are expected positive. No patch Dice headline.
- Full-volume loss using the same CE + soft Dice definition, with documented CPU reduction. If
  derived from stitched probabilities, use log(clamp(probability,min=1e-7)) and record that evaluation
  definition separately from training logits loss; do not silently compare different reductions.
- Predicted/reference foreground voxel counts and physical volumes, finite output checks, raw update
  losses and times, case/crop records, checkpoint references and stop reason.
- Restore class probabilities to each native source grid using the recorded affine transform, then
  argmax. Save native pancreas masks and aligned contact sheets for engineering review. Do not treat
  this as expert contour certification. Native-grid Dice, if reported, is secondary and labeled.

**Learning observed:** mean final full-volume loss at most 90% of initial AND mean foreground Dice
improves by at least 0.10. These are preset smoke indicators, not scientific significance thresholds.
Report discordant per-case behavior and all metrics even if the indicator fails. **Mechanics passed**
is separate: finite execution, correct role/geometry, bounded resources, complete receipts and backup
consumer recovery all pass. A timeout/interruption is an incomplete attempt, not a passed 100-step run.

## Resources and stop conditions

- At most 100 optimizer updates, 600 seconds in the update phase, 1,200 seconds end-to-end; first limit
  reached wins. One accelerator owner, AC power throughout, no concurrent profile or training worker.
- 16 GiB RSS polling and 16 GiB MPS allocator/driver limits, with overlapping measurements disclosed.
  Stop for failed monitoring, OOM/nonfinite state, unsupported operation, lost source/output mount,
  changed file/manifest/recipe, quota breach, power loss or checkpoint/backup verification failure.
- Reserve 1 GiB new output capacity on primary and 1 GiB within the shared backup allocation. Keep
  max(100 GiB,10% device) external headroom; internal free floor 100 GiB and total backup cap 20 GiB.
  No deletion or automatic budget extension. Report resource peak sampling limitations.
- Prior provisional forecast: about 5.3 minutes with 25% contingency, before measured production
  publication/recovery overhead is incorporated. The bridge handback supplies the actual storage
  observations. The 20-minute overall ceiling provides room for those checks; it is not a promise.

## Checkpoints, recovery and storage

Primary area: registered `prowl_artifacts/localizer-runs`, not a path guessed from legacy scripts.
Backup/restore: `prowl_backup/localizer-keepers` and a fresh `localizer-restores` destination, on the
registered independent internal volume. Global scientific roots remain disabled.

Save scratch step0, then complete checkpoints at 25/50/75/100. On an error or forced stop, retain
the last complete checkpoint and every partial attempt; do not attempt an unbudgeted emergency save.
Up to 24 completed updates can be lost between checkpoints. No automatic resume is implemented
for this bounded executor; a stopped attempt needs review before any new run.
Every checkpoint has a new artifact identity; preserve old complete and partial attempts. Save model,
optimizer, scheduler, completed step, RNG policy/state, exact run/input/config/source/environment
identity and update history. The terminal bundle additionally holds before/after metrics, native
masks, processed-grid contact sheets and the fixed reload probe. Restore only from an explicit pinned receipt;
no latest-file discovery, fresh-optimizer fallback or automatic restart. New attempt IDs preserve
interruptions. MPS continuation is within declared tolerance, not promised bitwise.

Copy terminal checkpoint and decision-supporting small controls/metrics to independent backup, verify
hashes/completion semantics, restore into a new destination in a fresh process with primary reads
refused, load on MPS and compare fixed-input probabilities at atol1e-5/rtol0. Backup failure means
preservation remains incomplete, even if learning succeeded. Raw data are not mirrored; source loss
still requires the documented recovery/qualification path. Intermediate checkpoints remain primary.

## Exact launch activation and acceptance checklist

- [ ] Quinton approves this specific launch; record a successor capability permitting this plan's
  real optimizer updates. The current D-273 capability deliberately permits verification only.
- [x] Implement the bounded executor and terminal evaluation/export path, exercise synthetic
  native MPS end-to-end and independent backup recovery. `localizer_smoke_run` checks the explicit
  launch authorization before entering the update loop; the old bridge remains verification-only.
- [x] Implement immutable request preparation and exact source/config/environment binding.
  `--prepare` captures the resolved inputs, plan, source text, Git dirty-source record and installed
  environment without CT payload reads. `--launch` refuses pending authorization or changed controls.
  Smoke is non-promotable; no existing checkpoint reuse. Prepare again if any bound input changes.
- [ ] Re-resolve cohort/current purpose permissions and verify source continuity, root UUID/device,
  quotas/free space, AC and accelerator ownership immediately before launch and on explicit resume.
- [ ] Start a new run/attempt, capture every stage/result/failure, preserve terminal artifacts and
  record the backup restore result. Update CAP-EXP-001 in the notebook even on failure or null learning.
- [ ] Review learning curves, both cases' native alignment and checkpoint usability; record the next
  question and retained/changed settings. No automatic expansion or second experiment.

The executor is complete. See [implementation evidence](LOCALIZER-EXECUTOR-HANDBACK-2026-09-28.md)
for the final native rehearsal and prepared request. Runtime activation is the remaining user decision.
An authorization file is a local execution record of that decision, not a cryptographic signature
or permission for an agent to approve its own launch. No CAP-EXP-001 optimization has occurred.
