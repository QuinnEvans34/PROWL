# Larger-model exploratory screen — November 5

User explicitly authorized autonomous research, downloading a new larger model,
and one bounded experiment after Mac KD completes, with Lenovo coordination.
This authorization supersedes the older no-successor instruction only for this
separately frozen trial. It does not change KD, its pins, budget or selected model.

## Candidate and acquisition

Choose the official **CLIP-Driven Universal Model, Swin UNETR**. The publisher
lists a62.19M backbone; the exact loaded implementation has62,595,315 parameters,
including its conditional heads, compared with roughly14.1M in our student.
It already has pancreas and pancreatic-tumor outputs. This is more useful for an
overnight initial screen than an organ-only backbone with a random lesion head.

- [Official implementation/model links](https://github.com/ljwztc/CLIP-Driven-Universal-Model),
  source revision43c12399cc98a40f447342a8dc2cecae5edae84c.
- [Official checkpoint repository](https://huggingface.co/ljwztc/CLIP-Driven-Universal-Model),
  revision76f0304ff9387c1baccbbc1d9eac78c5c5ccfeed.
- `clip_driven_universal_swin_unetr.pth`:758,907,945bytes;
  SHA256cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07.
- Mac download26.522seconds, exact LFS size/hash verified. Raw source/weights stay
  external in `/Volumes/PROWL-Data/PROWL/teachers/universal-swin-*`.
- CPU restricted load succeeds with `weights_only=True`, no unsafe pickle or
  ignored missing weights.170state entries/63,552,891state elements include buffers.
  Exact upstream DDP/backbone renaming and `strict=True` load pass. No model forward
  or optimizer update occurred during this audit.
- HF card saysMIT; the [upstream source license](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/LICENSE)
  isCC-BY-NC-ND4. Keep upstream source unmodified/external and adapted weights
  private for local noncommercial research. No copied/adapted upstream implementation
  or weights are published with our wrapper/tests/metadata.

Other reviewed options: [SuPreM Swin UNETR](https://github.com/MrGiovanni/SuPreM)
provides a larger general abdominal initialization but requires lesion adaptation;
MONAI's [self-supervised Swin UNETR](https://github.com/Project-MONAI/research-contributions/tree/main/SwinUNETR)
is another transferable backbone. [PanTS](https://github.com/MrGiovanni/PanTS)
and [Pixel2Cancer](https://github.com/MrGiovanni/Pixel2Cancer) task-specific weights
remain alternatives, not an automatic fallback queue. Published benchmark numbers
are not directly comparable with our cohort/recipe.

External pretraining membership/overlap with our exposed development cases is
unknown. This is descriptive feasibility evidence, not independent acceptance,
clinical accuracy, or a calibrated architecture-only comparison.

## Frozen design to implement on Lenovo

The free RTX4060 Laptop has8GiB VRAM. Measured fit is required; the existing6GiB
GPU ceiling is retained. Do not run a second model on the Mac during KD validation.

1. Admit the first four positive cases with explicit millimetre CT/reference units
   and valid retained geometry, in existing70-case development-cohort order. Freeze
   identities/source/reference/header pins before model outputs. No selection by
   Dice, error severity or visual appearance. A proposed four-positive/four-empty
   set was not admitted: no completed empty case has both reference units declared.
   No unknown-unit assumption is carried into this new screen. Empty-case alarm
   rate will be **not measured**; do not invent negatives or impute missing scores.
2. Use CT-only whole-foreground RAS input,1.5mm spacing, HU[-175,250]→[0,1],96³
   windows/48stride/Gaussian blending, batch1, no TTA or reference-driven crop.
   Upstream outputs are32independent sigmoid channels; pancreas11/tumor28 are
   zero-based10/27. Raw threshold is strictly>0.5; the CLI's apparent0.6 option
   is not passed by its actual default inference call. No threshold tuning,
   organ masking, largest-component filtering or other post-processing.
3. Accumulate only the two selected channels on CPU. Preserve full-field coverage
   and restore predictions into the native CT/reference grid with explicit
   orientation/affine/interpolation/units checks. Keep pancreas-including-lesion,
   lesion precedence, per-case Dice/precision/recall/components and false positives
   explicit. No full32-channel probability volumes.
4. Evaluate the untouched pretrained checkpoint, then optionally200fixed head-only
   transfer updates and the same four native cases. For training, inspect only up
   to12predeclared existing qualified train-pilot cases. Freeze eligible cases and
   train/development disjointness first; require at least four strictly admitted
   train cases. If unavailable, training is **NOT_ADMITTED** and only the pretrained
   screen runs. Never substitute the old cached tensors' different HU window/crop.
5. If training is admitted: seed42, upstream1.5mm/HU normalization,96³ train patches,
   equal-weight pancreas-including-lesion and lesion BCE+soft Dice, AdamW1e-4,
   weight decay1e-5. Freeze backbone/organ embedding; train only `precls_conv`,
   `GAP`, `controller`, `text_to_vision`. No KD, validation-based selection,
   restart from another checkpoint or recipe search. Keep initial/final checkpoints;
   final200is the declared endpoint. This tests head-adaptation feasibility, not
   full-backbone convergence or superiority over a24k student.

## Admission, bounds and queue ownership

Before any GPU stage, Mac KD must finish24k plus its complete70-case final native
validation. Require all12validations per arm, selected/terminal backup integrity,
successful treatment supervision/reaped workers, FINISHED MLflow and available
exclusive MPS ownership. The existing read-only result reporter checks these.
`post_kd_trial_permit_v1.issue` then binds the exact report/ready/specification and
one Lenovo request hash. A pending/failed/paused report cannot issue a permit.
The permit is not a launcher: Lenovo separately verifies a fresh one-shot dispatch
marker, AC, storage, memory, geometry, integrity and its exclusive GPU lock.

Lenovo freezes code/environment/model/data/spec pins and exact stage destinations
before dispatch. Overall maximum6hours, including qualification/compute; pilot
maximum600seconds;12GiB owned RSS;6GiB allocated/reserved CUDA;100GiB free onC:/E:;
new output8GiB and new independent backup8GiB, also within the previously approved
64GiB combined backup allowance. Keep all existing artifacts; no cap reset.

Pilot: one actual96³ forward and, only if training is admitted, two finite head updates; verify expected channels,
nonzero finite gradients/changed intended parameters, frozen backbone equality,
initial independent checkpoint copy and strict CPU reload equality. An inference-only
screen requires no optimizer execution. Pilot updates
are engineering, excluded from the200training updates. Stop on failed admission,
resource/integrity/geometry checks; preserve failure and clean all owned workers.
No automatic retry, relaxed gate, second candidate or further successor.

Log a separate MLflow run labeled exploratory/external-exposure-unknown, every
stage/resource outcome, frozen case dispositions, native metrics and independent
backup hashes. Compare pretrained/adapted outputs on exactly the same cases.
Our prior autonomous and supplied-region KD scores remain separately labeled;
different preprocessing/assistance/training does not isolate capacity causally.

## Current evidence

Mac audit: `outputs/prowl/universal-swin-audit-20261105-01/audit.json`.
34CPU tests pass for strict state mapping, post-KD permit refusal/identity and
existing KD closeout regression. The actual audit SHA256 is
111608eb4d5efa46ca1c3227dd6c3a770a49b0e74e9f7cec4766ab469189a553;
all18upstream Python source files are hash-bound.
An initial test invocation omitted the isolated dependency path and found no
pytest; the corrected environment passed. No package installed into the live venv.
No new model GPU execution has been authorized by a completion permit yet.
Lenovo found all12predeclared train cases lack the explicit-unit admission proof;
optional adaptation is therefore NOT_ADMITTED. The four eligible development cases
passed actual header admission. This run is a pretrained model screen, not new
training. Exact frozen case identities and stage pins belong to Lenovo's request.
Lenovo preparation/request and actual dispatch/results are recorded separately;
this specification stays unchanged once bound. Preparation is not a claim of
running or of improved Dice.
