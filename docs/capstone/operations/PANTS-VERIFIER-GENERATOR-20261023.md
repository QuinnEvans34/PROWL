# Candidate generator with reserved verifier patients

## October25 readiness update — supersedes pending GPU status below

The completed varied-focus parent passed its final retrospective and all closeout
gates. The original frozen five-update producer and independent cold replay now
both PASS. Producer106.047s/1750888448BpeakRSS; cold24.062s/1667858432B; both exit0
and workers reaped. State restoration and next input exact; next-state maximum
absolute difference3.725290298461914e-9, zero mismatches under original bounds.
Independent saved-four checkpointSHA b5325a08f33324c24fbe10649a2af3e0c397aa409fa95199bda3eee10e157b07.
No diagnostics promoted to scientific weights or counted as training hours.

Additive scientific launcher scripts/train_restricted_generator_20261025.py uses
freshSuPreM/800train/24000updates/500warmup/24kcosine, fixedterminal checkpoint,
no development evaluation, original varied views and coverage. Retains initial,
rollinglast and terminal checkpoints with independentCcopies; no checkpoint
selection on533reserved or70dev. Hard96h/12GiBRSS,AC/exclusiveGPU,disk/cache/backup
caps retained. Nonpromotable diagnostic schedule does not replace scientific one.
MLflow tracks real loss/LR/time, marks FINISHED only after successful supervised
completion; failures stay FAILED/no retry. Journal remains authoritative.

Launch preparation: E:/PROWL/readiness/verifier-generator-launch-20261025-a01.
Existing dashboard now supports explicit generator-only cards; before-change files
saved there. Handoff configurations are prepared only, current completed-run
configuration remains active. History retained, no invented Dice/validation cadence,
actual journal-derived time. After scientific dispatch, apply prepared configuration,
reload only the monitor as needed, then verify API/MLflow/backup/advancing updates.

Final receipt is produced by --freeze only after passing integration tests and
qualification recheck. --launch-sha256 EXACT_HASH --explicit-user-launch requires
explicit scientific launch approval; no automatic dispatcher or schedule. The
current instruction is preparation until ready, so no scientific launch is implied
by this document. No additional dataset audits or repeat pilots required.

## Approved resolution: inherited coverage-preserving geometry

User explicitly selected option1: retain existing81/43/71mm margins and proceed
as design-informed/exploratory. The smaller generator-only geometry failure below
is preserved; it is NOT rerun, refitted, or declared passed. No patient exclusion
or reassignment. Coverage relies on the original full1403 admission evidence.
Generator800-only optimization/checkpoint exposure is controlled, while all1333
training annotations contributed to preprocessing design. These are separate
claims; do not call this fully independent held-out preprocessing or clinical
generalization. Existing SuPreM provenance limitations also remain.

An additive GeneratorInputs view first verifies the full original cache admission,
then binds a new800patient control and limits rows/observations/cache-member access
to that role. The shared cache manifest/payloads are not changed. Reserved533 and
development70 are refused for load, optimizer, cache and lookahead access. The
validation membership remains in the session identity for compatibility but is
not accessible through this optimizer provider; a future candidate-evaluation
stage needs its own explicitly bound provider after the generator is frozen.
Prefetch is initially off; activation/shutdown has separate lifecycle tests.
This is not a scientific launcher or evidence of real CUDA qualification.

## Historical generator-only geometry failure (resolution above supersedes blocker)

Evidence geometry-01 under the same preparation directory. Additive geometry
code fits maximum source-index plane extension beyond the original pancreas-only
10mm box using ONLY800generator patients, rounds upward and adds1mm safety.
The resulting56/39/51mm extra margins were persisted in frozen-margin.json BEFORE
reserved-patient coverage assessment. Full existing positive-training inventory
was parsed as metadata, but fit_margin received exactly800generator records and
rejects extra membership. This is a metadata reconstruction, not a fresh mask audit.

All800generator,200calibration and67tuning lesion boxes fit. Of266verifier-fit
patients, PanTS_00002720 does not fit. No development/test files, CT voxels or masks
were read. No margin refit, exclusion, patient reassignment or source change.
27CPU tests pass2.45s including oblique geometry and protected fit membership.
The100%field-coverage gate FAILS for this proposed representation. Stop before
loader integration, candidate generation or scientific launch; do not turn this
failure into a pass by inspecting and fitting held-out labels.

Decision alternatives: (A) retain existing larger validated margins and explicitly
describe the experiment as design-informed/exploratory, with held-out new generator
optimization and checkpoint selection but NOT held-out preprocessing design;
(B) use a lesion-independent extent policy guaranteeing full CT coverage, with
new runtime/sampling qualification and likely substantially more inference work.
Neither alternative is approved by this failed geometry check. Keep all evidence.

User approved planning the additional restricted-cohort segmenter and asked to
start that preparation now. No competing GPU job, automatic launch or scientific
verifier launch is authorized by this preparation. Current24k run remains intact.

## Frozen patient partition

Evidence: E:/PROWL/readiness/verifier-generator-20261023-a01/partitions.json
SHA256 e70e110078d59d35b4171a9711bd2e0ea1ffa9f25aaf405e0d010f31e030fd35.
Seed verifier-generator-20261023-v1; SHA256 patient ordering, proportional
largest-remainder allocation within native total-lesion-volume strata. No model
scores used to assign patients. Volume strata: negative, positive<1mL,
positive1–10mL inclusive, positive>10mL. These are patient-volume strata, not
individual-lesion size categories. New source hashes bound to reused metadata.

| Role | Total | Negative | Small | Medium | Large |
|---|---:|---:|---:|---:|---:|
| Generator optimizer training |800|397|64|230|109|
| Verifier optimizer fitting |266|132|21|76|37|
| Verifier checkpoint selection |67|33|5|20|9|
| Verifier threshold calibration |200|100|16|57|27|

All1333assigned once, no exclusions;70existingdevelopment cases unchanged and
absent from all four roles. Generator never optimizes on, selects checkpoints on,
or calibrates using the533 reserved patients or70development patients. Verifier
optimization sees266 only;67 selects checkpoints;200 selects operating threshold
once after checkpoint freeze. Test-set files are never read. Calibration sample
size is patient-level, not inflated by treating candidates as independent.
Actual candidate class availability and small-component denominators still need
measurement; these patient counts do not guarantee adequate candidate examples.

## Candidate recipe and resource envelope

Proposed fresh SuPreM initialization (not any existing broad-cohort trained
checkpoint); existing SegResNet/3class CT input, DiceFocal, AdamW lr1e-4 wd1e-5,
seed42, fp32/batch1,500warmup/24kcosine,24,000updates,144cube/72stride,
same augmentation and varied focus/context mix. No PANORAMA, teacher KD, or EMA.
Initialize only after verifying the existing pretraining source review; reserved
new fine-tuning exposure does not prove pretraining independence.

Select the fixed terminal24k checkpoint, not a checkpoint chosen on development
or verifier patients. Checkpoint every500updates under a new retention/storage
budget; training-only diagnostics are explicitly nonselection. Generator exists
to produce realistic candidates; no hypothesis claims that training on800 should
beat the broad-cohort segmenter. The final causal verifier comparison is this
same frozen generator alone versus generator+verifier, not two different models.

Proposed hard training cap96h including its diagnostics,12GiB combined ownedRSS,
100GiB free on C:/E:,32GiB combined cache, existing backup cap27917287424bytes,
AC/sleep inhibition, exclusive GPU lock, independent backup and reaped workers.
These are caps, not duration estimates; smaller cohort does not make24k updates
proportionally faster. Full candidate generation over533reserved patients is a
separate bounded inference stage whose duration/storage must be measured first.
No automatic retry/resume or background AI polling. No new resource-limit increase.

## Required implementation/qualification before launch

1. Finish/review current24k run, final native reports, backups, MLflowFINISHED and
   worker shutdown. No dispatch just because a particular step was reached.
2. Build an additive restricted-role provider and independently bound cache index;
   existing FastVariedInputs requires exact complete train membership and source
   control, so do not bypass its guard or mutate its shared manifest. Reuse
   qualified payloads only with new role-aware identities and byte checks.
3. Address inherited annotation-informed margins explicitly. The existing81/43/71mm
   margins were derived using all1333training annotations, including newly reserved
   patients. They cannot silently be advertised as strictly held-out preprocessing.
   Derive train-dependent geometry parameters from800generator patients only using
   existing coverage/geometry metadata where possible; preserve full coverage and
   retain all difficult cases. If old margins are retained, obtain an explicit
   exploratory-scope decision and disclose design exposure. Never expand a reserved
   inference ROI using that patient's lesion mask. Resolved by explicit inherited-
   margin/exploratory approval above; retain the failed smaller-margin evidence.
4. Recompute only the new800patient sampling schedule, verify full bank exposure,
   protected-role refusals including lookahead, no70dev checkpoint selection,
   synthetic geometry/identity regression, then a bounded generator-training pilot.
5. Actual GPU updates/finite gradients, independent checkpoint backup and cold
   restore after current job releases GPU; new source/configuration/role receipt.
6. Freeze resource estimate and scientific configuration, explicit launch review;
   register separate MLflow name and dashboard journal only after actual dispatch.

## Initial partition evidence (historical)

20synthetic CPU tests pass2.36s. Metadata-only exporter verified1333cached metadata
hashes, disjoint membership and deterministic patient strata. It generated no CT
arrays, masks, predictions, weights, MLflow record or ready.json. Preparation
status PARTITIONS_ONLY_NOT_LAUNCH_READY. Generator implementation, real pilot and
checkpoint qualification remain undone; this document is not a launch receipt.

## Latest readiness evidence: real pilot complete, GPU checks pending

Twelve real generator cases pass exact target/window roundtrip and actual
coverage/jitter/context/augmentation checks; all12PNGs visually reviewed and
bound in cpu-pilot-01/visual-review.json. Single-window edge contact is not a
whole-bank clipping test. Through-plane coarse detail persists; no clinical
annotation-correctness claim.132.375supervised seconds/1303130112BpeakRSS/reaped.
No exclusions, model inference or optimizer updates. Existing coverage audit reused.

Additive verifier_generator_executor_v1 selects only the terminal checkpoint and
exposes no evaluation callback.58CPUtests passed27.84s, including protected roles,
executor failure handling, input geometry and qualification admission. Actual
CUDA execution of this new executor has NOT been tested yet.

Prepared procedure: scripts/diagnostics/qualify_restricted_generator.py, frozen
cuda-qualification-01/request.json SHA256
1a9d71af651d8436d2cc8a66ccf1c41752f963b9d1c8297d9f48b818689d4dce.
Do not rerun prepare or modify its pinned sources. After normal current completion,
inspect files/processes, then --stage producer once; require success/reaping before
--stage cold once. Five diagnostic updates/one cold replay,1200s/12GiB per stage;
independentCbackup and originalrtol1.3e-6/atol1e-5. Diagnostic schedule is explicitly
max5/warmup1/horizon5, not the proposed scientific24k recipe; nonpromotable.
No stage is armed or started. A failed stage requires a user decision, not retry.

Scientific resource supervision/MLflow/dashboard integration and final receipt
still require completion after GPU evidence. No launch authority or ready.json
is implied. The current run still owns the GPU at16k native validation.
