# Learn better lesion outlines from a frozen JHU teacher

Date: October 23, 2026. Priority: next scientific intervention after the current
run is reviewed and this candidate is qualified. Status: **CPU engineering set up;
real-case/GPU qualification pending; NOT launch-ready**. The actual teacher has
passed two synthetic CPU forwards. No patient teacher inference, CUDA distillation
updates or scientific distillation training has been performed.

The user prioritizes knowledge distillation before a separate false-positive
verifier/ensemble experiment. This authorizes planning and additive code, not
changing the live run or bypassing teacher, data-role, resource or launch gates.
Historical reference-only restrictions are superseded for this preparation; the
teacher-assisted research line remains explicitly separate from independent
generalization claims. No scheduled AI checks or automatic launch are enabled.

The user explicitly approves preparing this as **teacher-assisted/exploratory**
because patient-level teacher training membership is unavailable. Potential
teacher exposure to our development cases remains a limitation, not a resolved
overlap finding. This approval does not authorize a scientific launch.

## Question and mechanism

Can our compact student learn more accurate lesion contours from a frozen JHU
teacher's continuous lesion probabilities, while retaining all manual-mask
supervision and not worsening detection or false alarms?

The student still receives CT intensities, not lesion masks or teacher maps as
input channels. Provided pancreas masks continue to define the existing assisted
region, with its established full-annotation coverage checks. Ground-truth lesion
masks remain training targets; they must not choose development/inference crops.
Teacher predictions add an auxiliary training loss. Only the student is needed
at deployment. This is different from an ensemble, which combines models at
inference time.

The current candidate is a conservative, lesion-only distillation intervention:

- Keep the supervised DiceFocal loss unchanged on every annotated target.
- Use a frozen teacher's lesion probability, not its raw channel order.
- Add temperature-scaled Bernoulli KL between that probability and the student's
  lesion-versus-background/pancreas probability. This works without pretending
  the teacher's larger label vocabulary equals our three-class vocabulary.
- Omit KD at voxels where the teacher's binary decision contradicts the manual
  target, or is exactly tied at 0.5. Supervision is NOT omitted there.
- In the proposed uint16 cache, a reconstructed probability within the quantified
  rounding-error bound of 0.5 is treated as tied for KD. Quantization must not
  turn an uncertain decision into eligible agreement. This changes no manual mask.
- Exclude padding from KD. Average nonempty background, pancreas and lesion
  strata equally within a case, then cases equally. This prevents abundant
  background from overwhelming the lesion guidance. A case with no eligible
  teacher voxels contributes zero KD, not an omitted patient.
- Replay precisely the same spatial flips/quarter-turns on teacher probabilities
  and student targets. Do not apply image-intensity augmentation to probabilities.

Draft engineering defaults are maximum KD weight 0.1, temperature 2, and a
1,000-update linear weight ramp. They are **not a frozen scientific recipe**.
This tests the complete specified KD loss, not the separate causal effect of
temperature, ramp, agreement masking or stratification. Teacher mistakes remain
possible; agreement with a binary annotation does not establish calibration.

## Teacher identity resolved; real-data admission still required

Prefer the [MedFormerPanTS release](https://huggingface.co/AbdomenAtlas/MedFormerPanTS)
for the first teacher, rather than simultaneously introducing additional report
data from [R-SuperPanTSMerlin](https://huggingface.co/AbdomenAtlas/R-SuperPanTSMerlin).
The release describes PanTS-trained segmentation and lesion-probability export.
The release is now acquired and strictly loaded locally:

- Model revision `b854c8248af1e21f729dc2dfd489bd400472cf65`, file
  `release/pants_pancreas_release/fold_0_latest.pth`, 606,931,502 bytes;
  SHA256 `ff0f0868db15f99285e218e0468a2717c1a79a421357eb37171ecd5f3bb75d1f`.
- Unmodified external R-Super architecture source at commit
  `45fea075a805797e78e002e9880330f4241afb1a`. Source Git blob identities and
  downloaded SHA256 values were checked. No upstream code was copied into this
  repository. Its isolated einops dependency does not modify the live venv.
- The legacy checkpoint contains serialized module records. Initial inspection
  deliberately rejected them. A separate restricted `weights_only=True` loader
  maps an explicit allowlist to inert records, extracts tensors, and rejects
  unknown objects; no unrestricted pickle fallback or legacy model execution.
  Both raw/EMA tensor exports were exactly reloaded and checked.
- Both actual segmentation heads have **26** channels. Sorted published labels
  place `pancreatic_lesion` at zero-based channel **19**, with independent sigmoid,
  not three-class softmax. The generic config's 42 is not the actual head size.
  Strict loading has no missing or randomly initialized parameters.
- Prospectively selected **EMA teacher**: tensor SHA256
  `10853b9d568240294b499cd424bd5fd8baa93c6032a89cbfda9fff6a4ff996d3`;
  37,886,548 parameters, 300 state entries, release epoch 100. This is not student
  EMA and not a ten-fold ensemble. The release training log uses EMA evaluation;
  the current upstream prediction CLI defaults to raw unless EMA is requested.

The [model card](https://huggingface.co/AbdomenAtlas/MedFormerPanTS/blob/b854c8248af1e21f729dc2dfd489bd400472cf65/README.md)
declares MIT, while the acquired [R-Super source license](https://github.com/MrGiovanni/R-Super/blob/45fea075a805797e78e002e9880330f4241afb1a/LICENSE)
is CC BY-NC-ND 4.0. These are distinct assets/licenses. Keep the downloaded source
unmodified and local; public redistribution/product use needs separate review.
Neither licensing metadata nor a fold filename establishes patient membership.

Acquisition lives at `E:/PROWL/teachers/medformer-pants-b854c824/`; safe conversion
at `E:/PROWL/readiness/distillation-teacher-conversion-20261023-a01/`. The failed
initial inspection is retained at `distillation-teacher-inspection-20261023-a01`.

Before any teacher targets are admitted:

1. Preserve the acquired binary, safe tensor exports and resolved source/mapping
   pins above. Actual inference policy and scientific recipe still require
   real-case admission; loading a checkpoint is not a teacher-quality result.
2. Resolve teacher training membership against existing manifests and published
   release/fold evidence. Reuse prior dataset overlap work; do not restart a CT
   duplicate audit. A teacher trained on public PanTS may have seen our custom
   development patients even when our student did not.
3. **User approved:** since protected membership cannot be excluded, label subsequent
   development comparisons **teacher-assisted/exploratory, potentially teacher-
   exposed**. They cannot establish independent generalization. Decide this
   evidence scope is exploratory; do not reshuffle the cohort or read the test
   set to obtain a more favorable result.
4. Verify CT preprocessing, native affine/orientation/spacing, probability
   reconstruction, semantic channel mapping and real support on a bounded pilot.
   Equal shapes or matching metadata hashes alone do not prove alignment. No
   silent nearest-shape resizing or thresholded hard-label cache substituted for
   continuous probabilities.
5. Review teacher versus manual contours and student errors, including tiny
   lesions, large/extensive lesions, boundary cases and annotation-negative cases.
   If the teacher is not useful on these cases, stop and revise the proposal;
   publication performance is not an admission test.

Published [PanTS benchmark scores](https://github.com/MrGiovanni/PanTS) use their
own evaluation setup. They are not interchangeable with our 70-case development
Dice. Neither 0.50 nor 0.60 is promised by distillation.

## Matched comparison and hypothesis

Choose and freeze the student/control recipe after reviewing the current
**Varied lesion-focused views without losing coverage** run. Do not silently
choose an unmatched historical best score as the baseline. A completed control
may be reused only if cohort, initialization, sampling, augmentation, resolution,
loss, optimizer, schedule, evaluation and checkpoint selection all match; otherwise
run a prospective supervised-only control. Record that choice before the KD run.

Proposed fixed factors: the existing 1,333 PanTS training / 70 development cases,
fresh SuPreM student, seed 42, 24,000 updates, existing full-coverage pancreas-
assisted representation and augmentation, original optimizer/schedule and full
70-case native validation every 2,000 updates. No PANORAMA, architecture change,
EMA-student intervention, altered sampler or ensemble in this comparison. The
only scientific change is the declared auxiliary teacher-guidance loss. Weight
zero must reproduce the supplied supervised objective exactly and later pass an
actual matched optimizer-path comparison.

Primary endpoint: native lesion Dice averaged across **all 36 positive
development cases**, including misses, at the best scheduled complete native
validation (2k through 24k; earliest checkpoint wins an exact tie). Apply the same
selection rule to the control. Terminal-24k results are secondary, not a replacement
primary if they look better. Detection, annotation-negative patient alarm rate,
empty-case predicted lesion burden, pancreas Dice, positive-case macro voxel
recall and size-stratified results are mandatory accompanying outcomes.

Let delta be KD selected native positive-case macro Dice minus the matched
supervised-only selected result:

- **H0:** delta <= 0; adding this teacher guidance does not improve outlining.
- **H1:** delta > 0.
- Reject H0 only if the lower bound of a paired patient bootstrap 95% interval is
  above zero. Use 10,000 resamples, seed 20261023; resample the same patients in
  both arms. Otherwise **fail to reject H0**, not “accept no effect.”
- Practical success additionally requires delta >= 0.02 and every guard below.
- Practical rejection: a guard fails, or the upper interval bound is below the
  +0.02 practical target. Otherwise the practical outcome is inconclusive.

Inherited point-estimate guards versus the matched control: patient detection
delta >= -0.03; annotation-negative alarm fraction delta <= +0.03; pancreas Dice
delta >= -0.02; empty-case total predicted lesion voxel burden does not increase;
positive-case macro voxel recall delta >= -0.03. Proposed additional guard: native
<1 mL lesion-component detection recall delta >= -0.03, with component matching
rule and denominators frozen before the run. Report zero denominators as not
estimable, never as a perfect score. Small-group uncertainty must be displayed.
These are research decision thresholds, not clinical safety guarantees or formal
statistical noninferiority claims.

The interval describes patient variation for this single seed/selected models,
not seed-to-seed reproducibility. Repeated development-set use and selecting a
checkpoint on that same set cause optimism not removed by this bootstrap.
Teacher exposure, if unresolved, is a further limitation. No protected test reads.

## Implementation, resources and readiness sequence

1. **Done in CPU engineering:** separate loss, protected-role target admission,
   exact spatial replay, native probability cache/geometry, strict frozen teacher,
   KD Session/checkpoint restore, executor facade and MLflow metric adapter.
   Existing live training sources are unchanged. Modules use explicit versioned
   `teacher_*`, `segmenter_teacher_*` and `segmenter_distillation_*` names.
2. Resolve the teacher-admission items above; freeze the comparison and exact
   loss configuration. No development-set hyperparameter sweep hidden in setup.
3. Implement separate teacher inference and geometry adapter, then bounded real
   pilot after the live GPU run is complete. Proposed pilot: 12 training cases
   spanning the listed difficult groups, identities selected/frozen in advance.
   Reuse existing source/coverage evidence; do not exclude hard failures.
4. Measure teacher inference time, CPU/GPU memory, target-storage size and student
   throughput before choosing native/region/window target storage. Offline teacher
   outputs can avoid a second model on the GPU at every update, but a dense
   fine-resolution probability cache may exceed storage limits. A cache strategy
   is unresolved, not implicitly approved. Keep the existing 32 GiB combined cache,
   12 GiB owned RSS, 100 GiB free-space floors and backup limits unless explicitly
   amended; freeze a measured wall-time/GPU-memory budget before production.
5. The versioned KD Session exists; scientific launcher remains gated/pending,
   with no global monkeypatching of the current objective. Target records bind source CT/geometry, teacher weights,
   config, mapping, preprocessing, grid and control hashes. Training target
   admission rejects all development/test roles. Independent teacher evaluation,
   if later approved, is a separate evaluator and cannot feed optimizer targets.
6. Qualify real window alignment, all scheduled target availability, coverage,
   finite losses/gradients, teacher immutability, zero-KD control equivalence,
   independent checkpoint backups and cold restoration. Checkpoint identity must
   bind teacher/target manifest/loss policy/ramp counter as well as existing RNG,
   sampler, optimizer and model state. No automatic retries or failure overwrite.
7. Freeze new producing-code/config/teacher/target hashes, launch receipt and
   resource limits. Only then seek/bind explicit one-run launch authority.
   MLflow must record supervised, KD and total loss separately, actual KD weight,
   eligible/conflict counts, teacher identity, native metrics and measured timing.
   Register the human title on the existing private phone dashboard; retain history
   and journal-derived training hours. No MLflow RUNNING record until dispatch.

The original foundation was not a real teacher loader or KD Session; those have
now been added as described below. No scientific launcher or completion watcher
is armed. Synthetic test success is not full training readiness.
Historical foundation test attempt: **83 passed, zero failures/errors/
skips**, 80.015 supervised seconds, peak owned RSS 841,965,568 bytes, exit 0 and
workers reaped, within the 120-second/2-GiB CPU-only limits. Producing hashes match
the test request. Tests cover zero-weight control identity, finite gradients,
teacher detachment, agreement/stratum/padding rules, malformed targets, protected
roles, provenance pins, every flip/quarter-turn combination and replay against
the existing augmentation function. No CUDA context was initialized in the loss
test process. Evidence:
`E:/PROWL/readiness/distillation-foundation-20261023-a01/{request,result,resources}.json`,
`tests.xml` and `worker.log`. These are unit tests, not a real-model update, teacher
quality result, end-to-end restore test or a scientific training-time measurement.

## October23 engineering readout and next exact handoff

Actual frozen EMA teacher: two repeated 32-cube synthetic CPU forwards were exact,
all weights and global RNG unchanged, strict tensor loading passed, no CUDA
initialization. Supervised duration 14.547 s; peak owned RSS 921,264,128 bytes;
exit 0/reaped. `distillation-engineering-20261023-a01/model-01/` binds the teacher
identity SHA256 `86178c975d93beedcf862df3ae8f5ca14f91caddb3e43dfc5380d39f03ebcb61`.
This proves architecture/runtime compatibility, not real lesion accuracy or 128-cube
GPU feasibility. Safe tensor conversion separately took 14.391 s / 1,001,205,760 B.

Final engineering regression: **124 passed, no failures/errors/skips**, 32.891 s
supervised, peak owned RSS 883,683,328 B, exit 0/reaped; all tested source pins
unchanged. Evidence: `distillation-engineering-20261023-a01/verification-01/`.
Tests include zero-KD exact optimizer equivalence, positive-KD saved-state/next-
update restoration, role and immutable-identity rejection, quantization/tie rules,
all spatial augmentations, world-coordinate affine/oblique/flip/spacing mapping,
tiling and padding, explicit no-coverage failures, tracker metric cadence/failure
handling and refusal to dispatch a pilot while its parent is incomplete. Student
optimizer/restore tests use a tiny synthetic network, **not** the actual CUDA
SegResNet. MLflow tests use a fake client, not a new live training record.

Earlier `tests-01` passed 101 tests. `tests-02` retained one fixture failure (119
passed): a 32-cube test incorrectly retained the default stride 64 and hit the
window/stride guard before its intended malformed-output assertion. Only the
fixture stride was corrected; no production tolerance or gate was weakened.
Historical test requests remain preserved and identify their exact source versions.

Candidate teacher intake is explicit: full CT, RAI orientation preserving
obliquity, 1 mm spacing using the upstream XY B-spline then XYZ nearest sequence,
HU [-991,500], global sample-standard-deviation normalization. Student intake is
unchanged. One-pass 128-cube/64-stride edge-anchored Gaussian blending accumulates
only the lesion channel on CPU, followed by slabbed RAS-world linear reconstruction
onto the existing native provided-pancreas region. No manual lesion selects
teacher tiles. Uncovered native centres fail; boundary-cell extension is counted.

This is a **declared inference candidate**, not reproduction of all upstream
defaults: no second predicted-organ pass, no TTA or hard component/organ gate;
CPU normalization reductions, float32 accumulation, deduplicated edge tiles and
correctly indexed symmetric padding are explicit. The upstream code supports
single-pass inference, but numerical equivalence to its default two-pass output
is not claimed. Real-case usefulness/contours and costs must pass before choosing
it for scientific distillation. If it fails, preserve evidence and revisit the
teacher policy; do not silently change it mid-cache or exclude difficult patients.

Storage metadata only (no CT audit): 1,333 native regions contain 15,181,877,307
voxels. Raw uint16 targets need 30,363,754,614 B; existing caches occupy
22,957,418,839 B. Their sum exceeds the unchanged 32-GiB combined cap. Remaining
capacity is 11,402,319,529 B: payload compression would need to be below roughly
37.55% of raw size, with additional room for manifests and overhead. Compression
has **not** been measured. Quantized probabilities are continuous (not binary)
with a rounding-error bound of 0.5/65535 plus float32 epsilon. No full cache has
been authorized or generated, and no old cache is deleted to make room.

Preparation command (metadata only; exclusive output, do not rerun once present):

```powershell
.venv-prowl-windows/Scripts/python.exe scripts/diagnostics/prepare_distillation.py --prepare
```

It writes `E:/PROWL/readiness/distillation-preparation-20261023-a01/preparation.json`,
not a `ready.json` or scientific authority. It pins the candidate control, teacher,
source, metadata, 12 reused difficult training cases, draft loss and resource plan.
It does not freeze a control selection before reviewing the ongoing run.

Next, after normal current-run completion, full native validation, independent
backups, reaped workers, MLflow FINISHED and review of the current result:

```powershell
.venv-prowl-windows/Scripts/python.exe scripts/diagnostics/prepare_distillation.py --pilot
```

The prepared pilot has a 90-minute hard watchdog, 12-GiB owned RSS limit, 6-GiB
observed GPU-reservation gate, 100-GiB C:/E: free floors, unchanged combined cache
cap, 2-GiB pilot-cache cap, 256-million-voxel allocation preflight, 1,500 tiles/case
and 10,000 total. GPU OOM also fails, without retry. It takes the existing exclusive
GPU lock and will not run alongside training. It is not dispatched now. No retry,
resume or automatic successor occurs; partial outputs are retained on failure.
Every pilot CT is training-role checked, source geometry is checked independently
between ITK and admitted NIfTI, and twelve probability/contour PNGs and per-case
timing/storage/coverage summaries must be actually reviewed. Teacher training-case
Dice is only a diagnostic, never the experiment's development score.

After that pilot: resolve measured cache/time feasibility, review all images,
qualify complete target availability without repeating the source/duplicate audit,
run actual CUDA student zero-KD/control and positive-KD cold/backup checks, and
freeze the matched scientific recipe/receipt. Scientific launch, MLflow RUNNING,
and dashboard switch require that qualification plus explicit launch approval.

## Completion without spending AI credits on routine polling

The user declines periodic AI checks because of credit use. Existing heartbeat
`launch-the-qualified-varied-lesion-view-experiment` stays **PAUSED**. This turn
does not install a timer, scheduled task, watcher or new network endpoint.

A future small local process can poll journal/result files without model/API
calls, or receive a completion signal from a supervisor. It cannot by itself
promise to wake this chat; that is a separate product integration. A local status
notice and deterministic one-run dispatch are distinct from an AI review.

If separately approved and implemented, a handoff must bind one exact parent and
one qualified successor receipt. Require normal parent completion of all updates,
complete final native validation, verified independent backups, reaped workers,
MLflow FINISHED and free GPU lock. Atomically consume a one-shot authority marker;
verify all pins/resources before launch; record an immutable launch claim before
dispatch. On crash or uncertain dispatch, reconcile existing processes/journals
and stop for review, never blindly retry/resume or launch a second experiment.
Failures/cancellations require a decision, not an automatic next run. It should
leave the dashboard showing the actual state and notify once on meaningful
completion/failure, not generate paid AI turns while training is unchanged.

This is a proposed low-credit design, **not an armed queue**. No unqualified
experiment will begin merely because the current trainer finishes.

## Research basis

[Hinton et al.](https://arxiv.org/abs/1503.02531) motivate softened teacher targets;
they do not establish our optimal KD weight or temperature.
[Pancreatic teacher-student segmentation research](https://arxiv.org/abs/2008.10652)
uses a different multi-phase/data/teacher setup; it supports investigation rather
than a transferable Dice forecast. The agreement guard and stratification above
are our prospective engineering choices, not claims that JHU used this exact loss.

Next separate experiment:
[Reject false alarms without losing small lesions](PANTS-FALSE-POSITIVE-VERIFIER-20261023.md).
