# First capstone experiment: readiness checklist

Owner: Quinton Evans; Codex implementation/review. Date: September 28, 2026.
Status: **first run completed; mechanical checks passed, learning gate remains open**. This is daily-plan item 5, not a new numbered plan,
experiment registration, or authorization to bypass G0/G1 or Plan 04.

## September 28 planning update

R0–R8 below remain the first-launch checklist. Current evidence is **1,074 native tests**, three
qualified pancreas candidates and the published/resolved two-case cohort (3/26), with all original
protected memberships preserved. See the [publication handback](../data/LOCALIZER-COHORT-PUBLICATION-2026-09-28.md)
and [current checkpoint](CURRENT-CHECKPOINT.md). D-269 authorized the bounded shared publication
controls; it does not launch training. Phase C is verified for the deterministic recipe; CPU synthetic learning/checkpoint safety now passes; bounded MPS profiling also passes; production binding and the bounded executor now pass; next is the pinned launch decision. The earlier pilot counts
under “Verified starting point” remain historical. Readiness October 2 and smoke review October 4
remain conditional targets, not a gate waiver.

## Smallest useful target

Prepare a **PanTS-only, train-role pancreas-localizer smoke run**. The question is whether
the new capstone path can load verified CT/pancreas targets, perform a bounded learning
step sequence, save/reload an identifiable checkpoint, and produce correctly aligned
full-volume output. It is not a lesion-performance study or the formal autonomous baseline.

This follows Plan 05's localizer-first sequence and Plan 06's smoke classification. A
positive lesion case is useful for later target/cascade verification, but is not inherently
required to train a pancreas-only localizer. Pancreas annotation qualification still is.
Scratch initialization is the proposed first-smoke default to avoid an unnecessary external
checkpoint dependency; it is not a decision against permitted third-party pretraining later.
Architecture, steps, selection, budget and pass bars must be registered before execution.

## Verified starting point

- Scoped Python environment/test foundation; latest native full suite: **410 passes**, two
  upstream warnings. This is not full G0 or scientific validation.
- Approved legacy memberships reproduce exactly: 7,200 training / 1,800 validation / 901 test.
- Pinned acquisitions and extraction evidence exist; publisher-test CT remains unextracted.
- Tested identity guards, metadata join, file/header evidence and deterministic manifest assembly.
- Two-case diagnostic manifest is quarantined; no frozen real cohort or eligible annotation.
- Reviewed voxel audit and four-pair real-data pilot completed. Both sample pancreas masks
  contain 0/1; both lesion masks are empty. Case 2 units remain unresolved.
- Scoped drive/backup setup exists; scientific-run enablement and production source aliases
  remain disabled. These must not be enabled merely because a smoke run is desired.

Evidence: [pilot](../data/VOXEL-PILOT-2026-09-28.md),
[manifest slice](../data/MANIFEST-SLICE-2026-09-28.md),
[metadata](../data/METADATA-ADAPTER-2026-09-28.md),
[metric foundation](../testing/CONTRACT-METRICS-2026-09-20.md).

## Launch gates and concrete evidence

All unchecked items remain open. Existing helpers are foundations, not completed gates.

| Gate | What exists / what remains | Evidence required to close |
|---|---|---|
| R0 Relevant G0 review | Python/UI foundation evidence exists; full readiness is not declared | Reconcile required G0 checks and owning-plan prerequisites; record passed checks and explicit outstanding non-run scope without silently waiving gates |
| R1 Qualified source and targets | S3 qualifies 3/26/31 for the narrow smoke purpose; staged source assurance retained | Reconciled source inventory/manifest under Plan 02, verified geometry and pancreas provenance/allowed uses, approved mapping and explicit issue dispositions; meet G1, not a partial-snapshot exception |
| R2 Frozen protected smoke cohort | **Closed for this smoke:** exact 3/26 cohort published and independently resolved under D-269 | Registered frozen train-role descendant, parent/ancestor hashes, subject/duplicate checks, profile, completion marker, reproducible membership hash; consumer rejects arbitrary ID files, ineligible annotations and altered packages |
| R3 Tested preprocessing and target | **Verified for the two-case full-volume recipe:** image-only parity, binary targets, source-grid restoration and real overlays pass; deterministic patch/sampling adapter and image-only sliding-window path now tested synthetically | Synthetic spacing/orientation/label tests, pancreas-only target definition, train/inference parity, source-space round trip and bounded real-case load; no lesion mask can influence localizer input |
| R4 Initialization lineage | Scratch-only dedicated CPU path verified; production run binding still pending | Explicit scratch record plus tests that no checkpoint is loaded; historical-checkpoint rejection guards. If using pretraining instead: licensed pinned source, hash and tensor-load audit; never old project-trained weights |
| R5 Run and checkpoint identity | Synthetic identity-bound publication/reload/interruption passes; production root/run binding still pending | Immutable run/config/code/environment/cohort records, new non-overwriting destinations, verified checkpoint reload and interrupted-run handling; no unreviewed resume into historical runs |
| R6 Smoke metrics and outputs | Synthetic loss/gradient, empty-metric oracles, inference/restoration and exact CPU reload pass; MPS finite update/reload profile also passes; real-run scope pending | Hand-computed target/empty/failure checks for the selected smoke measurements, finite loss/gradients, declared output shape/classes, source-grid check and checkpoint reload agreement; no generalization claim |
| R7 Storage and compute preflight | Synthetic 96³ MPS profile passes; production checkpoint/backup roots, keeper restore and exact run preflight remain | Verified source resolver, output capacity/free-space floors, single accelerator/writer owner, measured small-fixture memory/timing, hard step/time budget, fail-closed missing-drive behavior and run-relevant keeper/restore checks |
| R8 Run plan and launch review | CAP-EXP-001 planned; exact request prepared, specific launch approval pending | Pre-run CAP-EXP entry with exact IDs/hashes, question/class, seed/config, expected checks, resource/abort rules and artifact paths; explicit review of readiness before launching |

G3 remains required before expensive baseline training. Plan 10 permits bounded component
smokes when their independent gates pass; it does not grant a shortcut around G1 or protected
data roles. Full NSD/detection/CI/operating-curve implementation is needed for later claims,
not for calling a wiring smoke successful. Define that smoke's metrics precisely nonetheless.

## Implementation order from here

1. **Bounded data follow-up design.** Select a small deterministic set from the exact approved
   training list, including source-positive tumour flags for later lesion inspection and
   separately identified anomaly candidates. Record selection provenance, exact file list,
   memory/time/disk budget and stop criteria before running. A source flag is a selection
   clue, not proof of foreground voxels. Do not extend to a full scan by default.
2. **Close interpretation gaps.** Verify source annotation provenance and intended uses;
   inspect actual foreground values. Resolve or explicitly quarantine unknown-unit cases.
   Do not invent units, foreground codes, biological identity or manual-label provenance.
   Publish append-only resolutions and a NEW manifest, preserving the diagnostic package.
3. **Complete Plan 02 source/cohort path.** Reconcile required source coverage and duplicate
   candidates, implement/test frozen cohort publication and resolution, then prove repeat
   builds and train-only consumer enforcement. Full G1 remains open until its evidence exists.
4. **Build the small imaging/run slice.** Test preprocessing/localizer target, initialization
   and run/checkpoint records using synthetic fixtures first. Classify reusable historical
   functions; do not launch scripts/train.py merely with corrected drive paths. Its --split,
   --train-ids and --val-ids interfaces are not the approved cohort-ID consumer contract.
5. **Preregister and smoke.** Agree the exact recipe and numeric limits, record the CAP-EXP
   game plan, verify all R0–R8 evidence, then run the bounded experiment. Log every attempt,
   including interruption, failure, null learning and negative results.

Steps 2–3 are the current critical path to real training. Synthetic work in step 4 can be
prepared in parallel conceptually, without implying multi-agent dispatch or authorization
for Plan 04 shared workflow machinery.

## Explicitly separate from this first smoke

- PANORAMA G2 gates PANORAMA/mixed-source runs; it need not precede PanTS-only training.
- Retrieval/vector DB, literature ingestion, the completed UI and a confirmed radiologist
  meeting are not prerequisites to this imaging smoke.
- The full two-stage cascade, held-out baseline and controlled model comparison come later.
- No publisher-test reads or model/threshold selection. Training smoke metrics are not
  validation/test results. Disclose historical evaluation use in later reporting.
- Plan 04 explanation is complete; coding/spike authorization is still separate. Obtain it
  before implementing workflow runners/locks/stages, including code disguised as a smoke helper.
- No paid compute, remote upload, automatic Git commit/push or all-night job is authorized here.

## Decisions not to make prematurely

Do not choose model experimentation winners, relax affine tolerances, classify the 101 size
flags as corrupt, or infer a general lesion mapping from two empty masks. Preserve the base
7,200/1,800/901 memberships even when a case is quarantined: record eligibility separately;
do not silently rebalance or replace protected members.

Before the first launch, Quinton and Codex should review the proposed scratch localizer smoke,
actual qualified cohort size, quantitative pass/stop criteria and resource estimate together.
This checklist does not reserve an experiment number or record a run as completed.

## Completion checklist

- [x] Current evidence and remaining gates consolidated against Plans 02/05/06/09/10.
- [x] Smoke scope separated from formal baseline and later integration work.
- [ ] R0–R8 supported by executable evidence and reviewed for the exact run.
- [ ] Experiment registered before compute; every attempt recorded afterward.
- [ ] Results used to choose the next experiment with explicit retained/changed factors.

Next concrete deliverable: the bounded positive-case/anomaly follow-up selection and audit
budget. No further source reads or model execution occurred while writing this checklist.


Latest Phase D evidence: [localizer learning/recovery handback](LOCALIZER-LEARNING-HANDBACK-2026-09-28.md).
Earlier next-action prose above is historical. Current next deliverable is bounded MPS profiling and
production run/checkpoint binding, followed by the concrete launch review; R7/R8 remain open.


Resource profile completed: [MPS handback](LOCALIZER-RESOURCE-PROFILE-HANDBACK-2026-09-28.md).
Median 0.736 s/update at 96³ supports local tiny-smoke feasibility. The provisional 100-update
projection is roughly 5.3 minutes with 25% contingency and stated omissions; candidate limits are
10 minutes of updates / 20 minutes total. These are not a frozen run budget or launch approval.
Next: production input/run/checkpoint binding and keeper restore, then CAP-EXP launch review.


## Latest September 28 bridge/recovery evidence

[The qualified-input bridge and independent checkpoint recovery passed](LOCALIZER-RUN-BRIDGE-HANDBACK-2026-09-28.md)
under D-273. R3/R4 now have real qualified-case forward/scratch-unchanged evidence; R5/R7 have a
production primary, independent backup and fresh-process MPS restore for a synthetic trained checkpoint.
The global registry remains unchanged. R6's real-run terminal evaluation/export and the bounded real
update loop still need wiring; R8's concrete [CAP-EXP-001 design](CAP-EXP-001-LAUNCH-PLAN-2026-09-28.md)
is written, but actual launch is unapproved. Finish that already-scoped executor before requesting
launch permission. No more broad qualification or storage investigation is on the immediate path.


## Current executor completion (supersedes older wiring-pending status)

[D-274 handback](LOCALIZER-EXECUTOR-HANDBACK-2026-09-28.md): R6 has full executor/evaluation/export
coverage, metric oracles and native synthetic end-to-end evidence. R7 has independently restored
terminal bundle evidence, including masks/metrics/source controls. R8 has a concrete immutable
CAP-EXP-001 request with exact source/environment matching the final rehearsal.1,074 tests pass.
Remaining activation is the specific launch decision plus immediate live root/power/quota/input
rechecks. A real trained keeper and CT learning outcome can only be established by that launch.
No literature completion, expanded cohort or new broad investigation is required for this smoke.


## D-275 first-run outcome (current)

[CAP-EXP-001](CAP-EXP-001-RESULTS-2026-09-28.md) has executed exactly once. R8 launch is complete;
R6/R7 now have real trained checkpoint/export/backup recovery evidence. The learning acceptance
criterion failed: both final pancreas masks are empty despite lower loss. Do not equate readiness
or mechanical completion with a useful trained localizer. Next review a bounded same-case learning
diagnostic before expanding the cohort. No second run is launched or implied by this checklist.

## D-276 investigation outcome

The [read-only optimization investigation](CAP-EXP-001-OPTIMIZATION-FINDINGS-2026-09-28.md) is complete.
All100 training crops contained pancreas; original endpoint metrics reproduced. Probability and
loss decomposition supports a controlled CE class-balance comparison as the next question. The
[CAP-EXP-002 proposal](CAP-EXP-002-PROPOSAL-2026-09-28.md) keeps other factors fixed and requires
objective-aware implementation/verification before its own launch. No new training or useful-localizer
claim follows from these diagnostics. Native suite now1,079 passes; existing warnings unchanged.


## Overnight follow-up — D-277 through D-279

The first-smoke mechanics are now exercised by four retained real experiments. The original
empty-mask failure remains recorded; balanced CE, then a lower LR, then a longer matched-schedule
run improved mean training Dice to 0.446. The last run completed all 300 updates, independent
backup/restore and visual review; 1,089 native tests pass. Training is stopped for the night.

This meets the weak learning indicator and verifies the bounded data-to-checkpoint route, not a
useful-contour or generalization gate. Final masks remain 3.4–3.6× reference volume on two repeatedly
optimized training cases. Do not promote them to independent validation, broaden eligibility by
implication, or mark the full capstone trainer/Plan 06 complete. Next: explicit fit/localization
criteria and a controlled follow-up, then qualified training diversity and separate validation.
See [morning handoff](MORNING-HANDOFF-2026-09-29.md) and
[final run evidence](CAP-EXP-004-RESULTS-2026-09-28.md).
