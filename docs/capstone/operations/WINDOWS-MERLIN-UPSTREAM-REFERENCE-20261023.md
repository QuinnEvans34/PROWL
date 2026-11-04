# Windows Merlin upstream CUDA reference — preparation only

## Latest: authorized corrected import audit found a distinct compatibility blocker

User authorized isolated batchgenerators repair and exactly one corrected CPU
audit. Installed batchgenerators0.25.1 with --no-deps into the new separate
batchgenerators-dependencies-01 directory; neither previous dependency files nor
live venv changed. import-audit-01 remains intact. New additive runner
audit_merlin_reference_imports_v2_20261023.py pins its sources/dependencies and
records evidence under import-audit-02, same180s/4GiB limits and CUDA hidden.

The corrected attempt passed the former missing batchgenerators import, then
FAILED in upstream-pinned timm0.6.12: timm.models.maxxvit.MaxxVitConvCfg is a
mutable dataclass default for conv_cfg, rejected by the current Python runtime.
This is a distinct import compatibility failure, not a CT/model quality result.
33.640seconds,855552000BpeakownedRSS,exit1,workers reaped. No model construction,
forward, CT read, CUDA dispatch or numerical reference result. No third attempt,
dependency patch, source modification or substituted timm version was made.

Current training advanced to17647/24000; supervisor60980/worker51832 live.
493active,495KD and502generator repository pins still match. Remaining decisions:
qualify a separate upstream-compatible Python/runtime environment, or explicitly
approve a versioned dependency adaptation and document its deviation. Either
needs a new bounded attempt; do not silently patch dataclasses or call the current
bundle ready. GPU gates and original diagnostic resource limits remain unchanged.

The sections below preserve the first preparation/audit history.

Status: acquisition and safe CPU conversion complete; upstream import audit failed;
no inference executed. Current varied-focus training retains exclusive GPU use.
User-authorized scope: exposed training case PanTS_00002720 first, then
PanTS_00006222 only after successful bounded completion. No scientific/KD launch,
concurrent GPU use, automatic retries, schedules or edits to existing pinned files.

## Acquired identity

Separate bundle: E:/PROWL/teachers/rsuper-merlin-eab1a7e9-reference.
Evidence: E:/PROWL/readiness/merlin-upstream-reference-20261023-a01.

- R-SuperPanTSMerlin revision eab1a7e9f421740bf8f3f834d1f69d17cbe3a8aa.
- Source checkpoint merlin_pancreas_pants_release/fold_0_latest.pth,
 606931502bytes, verified SHA256
 38535f10430265e431ca3ffa7fe3ff15efed5bccb65ba909b6e3ce18af11e459.
- Unmodified R-Super source revision45fea075a805797e78e002e9880330f4241afb1a:
 93source/license/config files,1178904bytes, each checked against its Git blob.
 Missing training/dataset/utils.py now present in this separate bundle.
- Acquisition completed353.344seconds;97downloaded files total including release
 metadata/checkpoint. Existing isolated einops copied; live venv untouched.
- timm0.6.12 and huggingface-hub0.25.2 installed with --no-deps into the separate
 cli-dependencies directory only. No dependency installation into the live venv.
- The Merlin model card has no explicit license field. Do not inherit baseline
 MedFormerPanTS MIT metadata. Source license remains distinct; private preparation.

Safe conversion uses the existing restricted weights_only/inert-record extraction,
not arbitrary pickle execution. Both raw/EMA exports exactly reload;26channels,
lesion19, independent sigmoid;300state entries/37886548elements.
Conversion:15.485seconds,1001537536BpeakownedRSS,exit0/workers reaped;
CUDA not initialized, no model constructed/forward or CT reads.
Windows EMA serialized SHA256:
4640e10540b48ccb1e5dca1348b93673d1067a16ffcb1e8a7bfd29e431f110ec.
This differs from the reported Mac serialized export hash. Original checkpoint
bytes match; cross-machine tensor-by-tensor or canonical tensor-hash parity has
not been checked. Do not treat serialized-file inequality alone as tensor inequality.

## Preserved import failure

import-audit-01 failed after76.765seconds,839204864BpeakownedRSS,exit1,
workers reaped. predict_abdomenatlas imported, but importing model.dim3 failed:
nnformer_utils imports batchgenerators.augmentations.utils.pad_nd_image and
batchgenerators is absent. This unrelated architecture is eagerly imported by the
upstream package. No model was constructed and no inference occurred.
No retry, source patch or custom replacement was attempted. A corrected isolated
dependency preparation/import attempt requires approval under the no-retry rule.
Exact upstream environment compatibility is not established; available runtime
is not the upstream requirements.txt torch2.1.0 environment.

## Comparison and proposed execution constraints

Mac comparison JSON retrieved read-only from PROWL commit5ef62a8 and retained as
mac-reference-5ef62a8.json. Both cases' CT/pancreas/lesion recorded hashes match
local admitted metadata. Actual files exist and roles are train. No fresh voxel
reads, duplicate audit or test-set access. Actual file-byte checks belong to later
bounded execution admission, not an inferred fresh hash check here.

Upstream preprocessing uses RAI, XY B-spline then XYZ nearest resampling with
legacy rounded extents and CUDA mean/std normalization. Prediction uses bfloat16
full-channel accumulation; CLI defaults to two stages and no rotation TTA.
The Mac snapshot uses extent-preserving grid sizing, CPU normalization and
lesion-only float32 accumulation, single pass/no TTA. These are pipeline factors;
results cannot be labeled a pure CUDA-versus-MPS comparison. Exact invocation,
EMA safe loading, pancreas second-pass selection, precision and native probability
reconstruction must be frozen before dispatch; no unchanged-CLI claim yet.
The upstream loader uses torch.load then strict=False. The legacy checkpoint must
not be loaded unsafely; use a separately admitted tensor-only compatible artifact
with strict key/tensor verification, documenting that input adaptation.

Proposed hard caps remain30min/case,12GiBcombinedRSS,6GiBGPU,2GiBoutputs total,
existing disk floors; no retries or budget expansion. FullCT inference only;
annotations may score outputs, never select inference crops. Save native
probabilities/geometry/Dice/recall/FP/FN and hashes. Full26channel upstream buffers
may exceed the cap; do not replace them silently with the custom Mac algorithm.

At closeout the scientific run was17550/24000updates, supervisor60980/worker51832
live. Must finish24k, final native validation, backups, worker reaping and
MLflowFINISHED, then acquire exclusive GPU lock. No reference stage is armed.
493active,495KD,502generator-qualification repository pins checked unchanged.
No live trainer/dashboard/MLflow changes or merge. Remaining blockers: GPU owner,
failed dependency admission, then execution adapter/limits/geometry qualification.
