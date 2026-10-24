# Mac teacher input audit — October 23

Scope: diagnose the existing teacher pilot, not qualify scientific training. Five
fixed exposed training cases: 2720 (large underprediction), 3059 (tiny miss), 691
(annotation-negative), 6222 (stronger agreement), 8658 (multiple components).
No labels changed, cases excluded, thresholds tuned or full target cache generated.

## Verified input checks

The bounded CPU audit completed in 46.83 seconds, peak owned RSS 2,977,677,312 bytes,
exit 0 and workers reaped. All 318 original pilot pins matched before the audit.
For all five cases:

- Hash-verified CTs decoded identically through nibabel and SimpleITK, including
  exact voxel intensities; RAS world affines agreed within absolute 1e-4.
- Actual pinned upstream reorientation/resampling functions, followed by its CPU
  equivalent clipping/normalization order, exactly reproduced legacy preprocessing.
  This does not establish CUDA reduction or complete inference equivalence.
- Masks matched source shape/affine and strict scaled binary decoding. All selected
  lesion masks contained exact semantic 0/1 values; the negative mask was empty.
- No lesion touched a source-array boundary. This is not a clinical completeness
  assessment of the scan or annotation.
- The revised centre-covering grid changed common-grid normalized values by maximum
  absolute 0.00626–0.01228. Its effect on predictions remains unmeasured.

Initial audit-01 stopped on case 6222 because the audit calculated standard
deviation after centering. That was an audit implementation difference. Its logs,
source snapshot and resource receipt are preserved; audit-02 computes both mean
and standard deviation before centering, as upstream does. Initial invocation also
failed before any audit due to missing jsonschema on the default import path;
the existing isolated dependencies were then used. No environment package changed.

## Inference differences and relevance

| Difference | Finding | Interpretation |
| --- | --- | --- |
| Weight selection | Release README example selects raw weights; our pilot explicitly selected EMA. | Direct matched probe warranted; EMA training configuration does not establish best inference variant. |
| Two-stage inference | CLI enables it, but its default organ list excludes pancreas; stage two pastes only corresponding lesion channels. | Enabling it alone is not an established pancreatic fix. |
| Padding | Actual upstream synthetic probe maps 65×130×140 to 65×130×204, padding the wrong axis. | None of the 12 revised pilot grids needs padding; not this pilot's cause. Do not copy this bug. |
| Window repetition | Upstream repeats an edge window for case 2498: 160 versus 140 unique windows on the revised grid. Other 11 counts agree. | Cannot explain the widespread failures. Count equality alone does not prove complete executor equivalence. |
| Gaussian blend | Normalized kernels differ by maximum absolute 0.00577; corner ratio 1.09788. | Real numeric difference; prediction impact unmeasured. |
| Accumulation | Upstream bfloat16; candidate float32. | Unqualified numerical difference, not automatically an error. |
| Output mapping | Released 26-label order agrees with pancreatic_lesion at index 19; sigmoid and first segmentation head agree with source. Strict state loading is retained. | No demonstrated channel-selection error. |
| Postprocessing | Release example includes predicted-organ masking; our probabilities do not. | Could affect false positives, but masking cannot restore missed lesions and may remove valid extensions. |

## Annotation and resolution observations

Saved axial component start/middle/end views were inspected for the five cases;
the tall multi-component sheet is an overview, not expert adjudication or an
exhaustive voxel review. The large case visibly has broad annotation extent and
small prediction overlap. The tiny case is only 12 native voxels, about 0.00557 mL.
In case 8658, the six missed components include 4, 8, 12 and 14 voxel components,
as well as 77 and 502 voxel components. Do not equate each connected component
with a clinically separate lesion, or erase small components to improve metrics.

Lesion masks are mostly or completely disjoint from pancreas masks in these
positive examples. This is a representation fact, not proof of mislabeled data.
Any gland-assisted crop must retain the pancreas/lesion union. The existing pilot
uses full-CT teacher inference and overlays lesions after pancreas labels.
Annotation correctness, acquisition differences and teacher training membership
remain unresolved; hash and geometry checks cannot establish them.

## Evidence and verification

External root: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/`.
`input-audit-01/` preserves the failed audit; `input-audit-02/` contains the successful
request, five case reports/figures, result, resources and window probe. No protected
test cases were opened. The window probe executes the actual pinned upstream
split-index/kernel functions on metadata/synthetic inputs, without a model.

41 existing geometry/supervision/binary-label tests passed in 15.02 seconds. An
initial test command referenced a nonexistent geometry test filename and collected
no tests; the corrected command used `test_mac_pilot_revision.py` and
`test_binary_label_policy.py`. Tests and CPU parity do not establish teacher quality.


## Matched raw-weight probe

One user-authorized bounded MPS inference used raw weights on fixed case2720,
preserving the candidate pipeline, source files, threshold and annotations. Saved
EMA probabilities are the comparison, with their uint16 quantization limitation.
No other case or weight variant was tried.

| Metric | Saved EMA | Raw |
| --- | ---: | ---: |
| Dice | 0.060480 | 0.043713 |
| Recall | 0.031220 | 0.022366 |
| Predicted voxels | 6145 | 4417 |
| Reference voxels | 189621 | 189621 |

Raw weights do not fix this large-lesion failure. This is not a population-level
EMA/raw comparison. Execution:112tiles,306.21seconds,2,331,279,360-byte peak owned
RSS,exit0/workers reaped. Native reconstruction had zero out-of-field voxels;
frozen teacher state equality passed. Bounds:1200seconds,12GiB owned RSS,12GiB
post-tile MPS allocation,200tiles; shared MPS lock and AC enforced. Evidence:
`raw-weight-probe-01/` request, raw probabilities, result and resources.

## Conclusion and next decision

No demonstrated CT decoding, axis, strict binary decoding or class-channel error
in these checks. Corrected geometry addresses a real earlier bug, but does not
make the teacher useful. Padding and raw-versus-EMA selection do not explain the
large failure; repeated edge windows affect only one revised pilot grid.

Do not start KD or silently change annotations. The remaining useful engineering
comparison is a fixed-case reference of resampling extent and probability blending,
with the same EMA weights and a common native evaluation region. Keep this bounded;
do not run an open-ended search for a better pilot score. If those differences do
not materially explain the failure, stop treating this teacher as a qualified KD
source and review annotation provenance/teacher suitability before more target
generation. Clinical correctness of the supplied outlines requires appropriate
review, not agreement with this model. Full upstream/CUDA parity remains untested.


## Final bounded extent/blending comparison — completed

This supersedes the pending comparison above. User authorized continuation. One
new EMA forward pass on case2720 used the legacy grid; identical window outputs
fed three accumulators. The saved revised-grid result supplied the extent
comparison. No case expansion, threshold tuning, label changes or training.

Before dispatch, nonconstant synthetic predictions exactly matched the existing
candidate accumulator and the actual pinned upstream one-pass bfloat16 function.
Inputs with different upstream window multiplicity are explicitly rejected by
this diagnostic. This case has identical candidate/upstream window order.

| Configuration | Dice | Recall | Predicted voxels | False-positive voxels |
| --- | ---: | ---: | ---: | ---: |
| Saved revised grid, candidate float32 | 0.060480 | 0.031220 | 6145 | 225 |
| Legacy grid, candidate float32 | 0.059866 | 0.030893 | 6082 | 224 |
| Legacy grid, upstream kernel, float32 | 0.060320 | 0.031136 | 6135 | 231 |
| Legacy grid, upstream kernel/bfloat16 | 0.060418 | 0.031189 | 6149 | 235 |

All use189621 reference voxels and the same native evaluation region; no unavailable
voxels excluded. Coverage:3135750/3135750,zero boundary extension/out-of-field.
Against legacy candidate blending, upstream float32 changes77 threshold decisions
(max probability difference.005869); upstream bfloat16 changes111(max.011921).
The legacy candidate result, quantized identically, exactly replays the original
pilot's saved probability array:zero changed voxels. That supplies an additional
same-case reproducibility check, not a general MPS/CUDA equivalence claim.

Execution112tiles/315.23seconds/2,612,576,256B peak owned RSS/exit0/reaped. Frozen
teacher state exact;323 request pins verified afterward; recorded supervisor and
worker absent. Bounds1200seconds,12GiB RSS,12GiB post-tile MPS allocation,128MiB
outputs,200tiles; exclusive shared MPS lock/AC/guardian enforced. Full native
coverage was checked with a synthetic probability field before model execution.

Evidence: external `extent-blend-probe-01/` request (including synthetic checks),
resources, result, native-probabilities.npz and final-verification.json. Script:
`scripts/diagnostics/compare_mac_teacher_blending.py`. Baseline quantization and
CPU-normalization/MPS-forward/native-world reconstruction limitations remain;
this is not a complete upstream CUDA CLI reproduction.

### Decision

The tested extent/kernel/precision differences do not explain the large-lesion
failure: recall remains3.09–3.12%. Together with the failed raw-weight improvement,
this ends the planned pipeline-tuning investigation. Do not generate full teacher
targets or start KD from this candidate. No claim that all annotations are correct,
all possible backend differences are excluded, or the teacher fails every case.

Next priority is teacher/task and annotation provenance review: confirm what the
release was trained/evaluated to delineate and compare with our supplied lesion
scope, using existing evidence first. Small component fragments need separate
review; component counts are not automatically clinical lesion counts. If there
is no documented mismatch to resolve, a different qualified teacher or continued
supervised student work is more defensible than further tuning to this exposed
case. The KD deliverable remains planned, but this teacher is not qualified.

## October23 follow-up: backend parity attempt and expected model identity

User requested renewed investigation of whether integration explains poor teacher
performance. The release [model card](https://huggingface.co/AbdomenAtlas/MedFormerPanTS/blob/main/README.md)
identifies MedFormerPanTS as the segmentation-only baseline. The
[paper, section2.5](https://arxiv.org/html/2510.14803v1#S2.SS5) compares that approach
with report-supervised R-Super. The latter's headline improvements should not be
attributed to this checkpoint. Published cohort results also cannot be compared
directly with our small exposed diagnostic cohort. Neither distinction proves the
local inference is correct or explains the severe case2720 miss.

A fixed probe selected one128-cube from each of existing training cases2720 and6222,
centered on the annotation centroid and clamped to the teacher grid. Plan: identical
EMA weights and float32 inputs on CPU/MPS, four forwards,1200s/12GiB owned RSS,
shared MPS lock/AC. Annotation-centered selection is an oracle diagnostic, not a
new full-volume accuracy evaluation. No source labels or thresholds changed.

**Attempt stopped before the first forward completed:** peak sampled owned RSS
13,348,388,864B exceeded12GiB. Supervisor terminated the worker after13.81s; exit-15,
workers reaped. No prediction or backend comparison was produced. No retry, budget
increase, partial success claim or scientific launch. Evidence preserved in
`teacher-backend-parity-01/` request/resources/worker log. Producing script:
`scripts/diagnostics/compare_teacher_backends.py`.

Next useful reference is a bounded upstream CUDA run on an already exposed case,
only after the laptop's existing training releases the GPU. First request a
read-only feasibility report: current GPU ownership, frozen code/checkpoint identity,
upstream runner readiness, and fixed-case source availability. Do not dispatch
training/inference or change active pins during that check. A later reference
should preserve exact input identity and distinguish upstream prediction behavior
from candidate postprocessing/reconstruction. Full upstream parity remains open;
this memory failure is not evidence of a model-quality or data-quality failure.

## Teacher selection review — report-supervised release identified

Official [Merlin demo](https://github.com/MrGiovanni/R-Super/blob/main/rsuper_train/Merlin_demo.md)
explicitly distinguishes the two checkpoints. We did not install an unrelated
architecture, but selected the mask-only baseline rather than the report-supervised
model whose improvements motivated this investigation.

| Release | Supervision | Current local status |
| --- | --- | --- |
| AbdomenAtlas/MedFormerPanTS | PanTS masks only | Existing tested baseline; unqualified as KD teacher |
| AbdomenAtlas/R-SuperPanTSMerlin | About0.9K PanTS lesion masks plus1.8K Merlin lesion reports | Metadata reviewed; weights not downloaded/tested |

[Report-supervised model card](https://huggingface.co/AbdomenAtlas/R-SuperPanTSMerlin)
revision `eab1a7e9f421740bf8f3f834d1f69d17cbe3a8aa` names
`merlin_pancreas_pants_release/fold_0_latest.pth`,606,931,502bytes,
server-advertised LFS SHA256
`38535f10430265e431ca3ffa7fe3ff15efed5bccb65ba909b6e3ce18af11e459`.
This is an advertised identity, not a locally verified checkpoint hash.
The label YAML exactly matches the baseline, and all constructor fields used by
our FrozenTeacher match. New config explicitly sets report_volume_loss_basic0.1
versus0.0 and references the PanTS baseline as pretraining. Architecture/config
agreement does not prove safe loading, tensor compatibility or inference quality.

Metadata-only evidence saved externally in `teacher-selection-review-01/`:
API metadata, pinned README/config/labels and review.json. No weights downloaded,
source imports, inference, teacher replacement or training performed. New card
metadata has no explicit license field; do not inherit the baseline's model-card
license automatically. Protected development membership remains unresolved for
both teachers; a comparison would remain exploratory.

Recommendation: safely acquire/convert the report-supervised checkpoint into a
separate bundle, verify strict loading/output mapping, then compare on the same
fixed12 exposed cases and corrected-label interpretation, with unchanged inference
settings and preserved baseline. This tests checkpoint choice; it must not be
confused with validating backend equivalence or independent model acceptance.
The full upstream CUDA baseline reference remains complementary for diagnosis.

Quinton authorized a message to “Plan capstone experiment workflow”; the read-only
GPU/source/checkpoint/runner feasibility request was sent successfully. Explicitly
no inference, training, active-run edits, installations or schedules requested.

### Completed candidate test

The metadata-only status above is historical. R-SuperPanTSMerlin was subsequently
acquired, safely converted and tested on the same12 cases. See
[completed pilot](MAC-RSUPER-MERLIN-PILOT-20261023.md): average Dice improved,
but missed components and high-confidence false positives remain. No KD launch.
