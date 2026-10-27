# Current Mac KD launch handoff — October 27

W04-03 remains blocked on complete teacher outputs and actual full-provider GPU
qualification. Scientific launch is already user-authorized after the agreed gates;
there is no new permission blocker and no automatic student-launch chain armed.
This reconciles existing work, without changing the scientific design or active job.

## Correct the historical handoff before use

`MAC-KD-COMPARISON-20261023.md` and its two JSON recipes are historical design
references, not dispatch inputs. They predate the R-Super replacement and corrected
on-demand provider. Preserve their bytes as design evidence. In particular:

- Current teacher: R-SuperPanTSMerlin EMA,26channels,lesion19/sigmoid. Converted
  weight SHA256 `68a3b5b2dc77dbdabb4fc2b8d981c486c131be97379a681b333ae479490161f8`.
  Consume the exact teacher/preprocessing identities from the completed producer
  request, not a manually recreated teacher dictionary or the first MedFormer.
- Both arms must bind the corrected provider
  `900619faa0a5905fca165bebca0c9afd56f9df635cdd7141c4f95a31204a0053`, including
  its7training-label corrections and unchanged development labels. Its throughput
  is `errata-kd-on-demand-1`,prefetch=false. The historical recipes still say
  `equivalent-varied-target-cache-prefetch-1`; that is not the prepared runtime.
- Both old recipe files match after changing only max_weight0to0.1. Exact split
  hashes, region policy and sampling policy agree with the prepared provider.
  Keep the24k horizon,18kfocus/6kcontext,initialization,augmentation and evaluation
  schedule paired. Final operational recipes must record the on-demand provider
  identically in both arms; this is the October25 implementation, not a new factor.
- Prior no-launch-authority and only12locally-bound-case statements are historical.
  Source admission passed1403cases/4209files; the two-case MPS and CPU full-cohort
  checks are complete within their stated scopes. None establishes full GPU readiness.

## Next sequence after teacher completion

1. Inspect the latest continuation's result/resources and process ownership. Require
   complete=true,exact1333membership,successful exit and reaping. Preserve all prior
   failures and cumulative resource accounting. Current07is still running; do not
   use progress counts or individual NPZ presence as a completion receipt.
2. Use `segmenter_generated_target_admission_v1.admit` with the corrected provider,
   the completed producer request/result/resources and qualification_only=false.
   It verifies source/grid/coverage, payload hashes and types. Publish a new admitted
   manifest separately. The old `check_rsuper_target_admission.py` is a six-case
   rehearsal hard-coded to attempt02; do not run it as full admission or overwrite it.
3. Qualify actual full-provider MPS zero/positive-KD updates, production executor,
   teacher-free native evaluation/component sidecars, independent backups and a
   fresh-process restore. Reuse existing modules; tiny CPU fixtures and two-case MPS
   evidence do not substitute. Failed attempts stay preserved; no automatic retry.
4. Measure runtime and actual checkpoint/report/sidecar storage against existing
   caps. Freeze both operational recipes, runtime/source identities, full target
   manifest and distinct outputs/tracking IDs before observing either arm. Resolve
   any mismatch before dispatch; do not silently change budgets or shorten24k.
5. Under existing conditional authorization, launch the matched control then KD
   only when qualified. Verify advancing updates, durable backups and stored metrics.
   Unknown teacher membership keeps results teacher-assisted/exploratory.

The full-manifest publication command is now implemented and synthetically tested
(see below); full-provider GPU qualification/launch receipt wiring remains unfinished. There is no ready-to-run scientific command
in this handoff. Do not invoke older two-case scripts as a substitute.

## Evidence checked now

Read only saved JSON/source; no CT arrays, teacher weights, private evaluation,
model execution or target rewrites. Exact assertions verified paired-design
symmetry, membership separation, split hashes, region/sampling agreement and all329
active repository pins. Retained observations and eight input hashes:
`outputs/prowl/kd-launch-handoff-20261027/reconciliation.json`.
At17:39UTC the teacher had540/1333completed targets. This is progress, not admission.
See `MAC-KD-DURABILITY-20261025.md` for provider/evaluator/recovery evidence and
`MAC-RSUPER-TRAINING-PREPARATION-20261023.md` for actual MPS and backup-boundary checks.

## Full-target admission command — implemented, not run on live targets

`scripts/diagnostics/admit_rsuper_full_targets.py` constructs the existing corrected
provider and requires exact1333train/70development membership. Supply the reviewed
SHA256 values of the completed producer request, result and resources, plus the
prepared provider identity. It rejects incomplete/unreaped generation before
constructing the provider, checks existing storage admission, then invokes the
owning full-target validator with qualification_only=false.

Example syntax (replace all placeholders with verified completed evidence):

```sh
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
  .venv312/bin/python scripts/diagnostics/admit_rsuper_full_targets.py \
  --targets /absolute/completed-generation \
  --output /absolute/new-admission-directory \
  --request-sha256 REQUEST_HASH --result-sha256 RESULT_HASH \
  --resources-sha256 RESOURCES_HASH \
  --provider-sha256 900619faa0a5905fca165bebca0c9afd56f9df635cdd7141c4f95a31204a0053
```

Output is separate from the producer: original payloads remain untouched; symlinks
reference hash-verified NPZs without duplicating the cache. Keep the producer drive
and files available. `manifest.json` is published last through an atomic,
non-overwriting link after fsync; an earlier failure leaves an inspectable directory
without that manifest. Existing output directories cannot be overwritten/retried.
The existing TeacherTargetStore rechecks payload hashes when consuming a window.
`admission.json`, `common-identity.json` and `provider-control.json` retain the
bindings. Successful admission explicitly reports scientific_ready=false.

Synthetic tests verify a1333-case/70-development CLI invocation, existing-store
consumption, later payload-corruption rejection, changed record/provider hashes,
incomplete inputs, separate destination enforcement and interrupted publication.
An actual subprocess rejects incomplete generation before provider/preflight.
Combined admission, backup-boundary and executor-recovery regression:48passed in
4.76s, two upstream Torch deprecation warnings. CPU-only; no CT/model execution.
No full admission was run against teacher07, which is still producing targets.
This command does not launch training or qualify the actual GPU executor.

## GPU qualification input preparation — CPU-only

`prepare_kd_executor_qualification.py` now prepares `preparation.json` from a
completed admission. It does not execute a GPU stage. It requires the reviewed
admission receipt hash, rechecks terminal producer records, binds teacher/common
identity and manifest back to those records, enforces corrected on-demand inputs,
full disjoint1333/70 membership, matching split/region/sampling identities and
paired designs differing only in KD weight. It derives separate operational copies
with the existing on-demand policy; historical recipe files remain unchanged.

```sh
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
  .venv312/bin/python scripts/diagnostics/prepare_kd_executor_qualification.py \
  --admitted /absolute/completed-admission \
  --admission-sha256 VERIFIED_ADMISSION_HASH \
  --output /absolute/new-qualification-preparation
```

The output pins admission/design/source files and records remaining execution
checks. It explicitly says PREPARED_NOT_GPU_QUALIFIED/scientific_ready=false;
there is no worker or launch flag. Existing destinations and destinations inside
the admitted target tree are rejected. No real preparation was created against
partial teacher targets. Later execution must recheck these pins and actual
provider identity, acquire exclusive GPU/resource supervision, enforce its bounded
engineering budget, and preserve failures. Preparation is not permission to bypass
any of these requirements.

Ten metadata-only synthetic tests cover successful binding/source preservation,
receipt/provider/manifest/common/producer tampering, partial qualification,
wrong split despite matching arms, unmatched designs and destination reuse.
Combined regression58passed in6.89s (two upstream Torch deprecation warnings).
No CT arrays, teacher weights or GPU were read by preparation. Synthetic metadata
success does not establish payload validity; full admission and the target store
own those checks. Actual supervised full-provider GPU stages are now implemented below; real
qualification remains pending until targets are complete and MPS is free.


## Supervised GPU stages implemented — NOT launched

`qualify_full_provider_mps.py` provides four individually selected engineering
stages: reference (4 supervised updates), zero (4 zero-KD updates compared to the
reference), producer (4 positive-KD updates through the actual executor, two native
development evaluations and independent backups), and cold (restore the independent
step-3 backup in a fresh worker and compare its next update to the producer).
The engineering horizon limits executor iterations only; the student configuration,
checkpoint identity and learning-rate horizon retain the original 24,000-step recipe.
These are not scientific training updates or a model-quality comparison.

Preparation requires completed admission/preparation evidence, two distinct named
development cases (positive and empty), and fresh output/backup directories. The
request binds source hashes and installed runtime versions. Each dispatch requires
its exact request hash, `--explicit-run`, all preceding successful receipts and
unchanged evidence. No automatic chaining or retry is provided; failed directories
are preserved. Runtime or source drift requires a new preparation.

Illustrative commands only; none were executed against real targets:

```sh
.venv312/bin/python scripts/diagnostics/qualify_full_provider_mps.py \
  --root /absolute/new-external-qualification --prepare \
  --preparation /absolute/completed-preparation/preparation.json \
  --preparation-sha256 VERIFIED_PREPARATION_HASH \
  --backup /Users/quintonevans/PROWL-Backups/new-engineering-backup \
  --positive-dev VERIFIED_POSITIVE_DEV --empty-dev VERIFIED_EMPTY_DEV

.venv312/bin/python scripts/diagnostics/qualify_full_provider_mps.py \
  --root /absolute/new-external-qualification --stage reference \
  --request-sha256 VERIFIED_REQUEST_HASH --explicit-run
```

Later stages use the same command with `zero`, `producer`, then `cold`, after
inspecting each completed stage. Each has a 1,200-second watchdog, 12-GiB owned RSS
limit, sampled 12-GiB MPS allocation limit, 2-GiB output and 4-GiB backup caps.
Existing AC, disk-reserve and exclusive-MPS gates remain enforced. Backups must be
on a separate filesystem under PROWL-Backups; writes are fsynced and hash-verified.
MPS fallback is disabled. Existing parent-loss supervision and process reaping are
used; a receipt requires successful exit, reaped workers and unchanged evidence.
Sampled MPS allocation is explicitly not a continuous device peak.

CPU validation: combined regression 69 passed in 11.92s, with two upstream Torch
JIT deprecation warnings. The numerical exercise uses tiny synthetic CPU models
and the same four-stage implementation; the production CLI creates separate
workers. Synthetic subprocess tests check success, nonzero exit and timeout/reaping.
The follow-up orchestration suite, including runtime-drift rejection, passed
11 tests in 6.92s (70 distinct tests across these checks). The first numerical test had
an incorrect final assertion path in its fixture; that assertion was corrected,
without changing the four successful stage computations or numerical tolerances.
No real provider arrays, teacher model, GPU stage or scientific training was run.
Actual MPS equivalence, performance, native geometry and cold recovery still need
qualification; successful synthetic receipts do not satisfy these gates.

Teacher check during this work: 548/1,333 targets completed; supervisor1351 and
worker2683 remained live; all329 repository producing pins matched. No producing
files or teacher recipe were changed.


## October27 continuation authorization and readiness check

User now authorizes finishing target generation, verifying admission, then running
the real GPU qualification when the GPU is free. This supersedes the preceding
turn's do-not-launch instruction for these bounded engineering stages only;
it is not an instruction to bypass admission or launch scientific training.

Read-only check: launchd07b remains running (supervisor1351/worker2683),548/1333
completed, current case PanTS_00007575 advanced from25 to75/96tiles. All329 repo
producing pins match. AC power,87GiB internal and1.9TiB external free; no terminal
result/resources or guardian-failure receipt. Generation is incomplete, so no
admission/preparation or GPU qualification was attempted. Existing hourly teacher
monitor remains the mechanism for generation checks; it does not launch students.

Completion order: require terminal1333-case result, successful resources/reaping
and released MPS ownership; verify admission with exact producer hashes; prepare
matched full-provider inputs; freeze a fresh engineering request with verified
positive/empty development identities and independent backup; dispatch and inspect
reference, zero, producer and cold separately. Preserve any failed stage and stop
for diagnosis. A completed target count alone does not satisfy admission, and a
synthetic test pass does not satisfy real GPU qualification.


## Separate-process CPU recovery proof

`tests/test_kd_cross_process_qualification.py` now runs the actual four-stage
exercise through the qualification dispatcher and existing guardian/watchdog,
with a new CPU process for every stage. Invented16³arrays and a tiny Conv3d replace
real data and the model; no production resource gate or scientific recipe changed.
The test uses isolated output, synthetic admission, and a local test backup rather
than claiming independent-device storage qualification.

Reference, zero, producer and cold each exited0 and were reaped; four distinct
worker PIDs were verified absent afterward. Cold consumed the independent file copy
of step3 and reproduced the producer's step4 full state under the unchanged
rtol1.3e-6/atol1e-5 criteria. Three predecessor receipts bound the cold dispatch,
and source target bytes were unchanged. The original same-process numerical test
and synthetic failure tests remain useful but are not substituted for this proof.

Result:1 passed in20.56s, two upstream Torch deprecation warnings. Per-stage
supervised durations were4.063/4.065/4.066/4.064seconds; maximum sampled owned RSS
492,175,360bytes. Each test worker was capped at60seconds/2GiB. Evidence retained
under outputs/prowl/testing/kd-cross-process-20261027-01, including receipts,
resource reports, logs, checkpoints and backups. No actual GPU qualification,
full-provider array reads or scientific training occurred. Teacher07 remained
live at555/1333; all329 repository producing pins matched.


## Final resource admission before a stage receipt

Code review found that the last output/result write can occur after the supervisor's
last resource tick. Dispatch now repeats the existing preflight after successful
worker exit/reaping and before validating/publishing its success receipt, while
exclusive ownership is still held. No cap or resource policy is weakened.

Two synthetic failure cases inject final output-cap/storage loss after worker
completion. The completed result/resources remain available, no success receipt
is emitted, repeating the same attempt is rejected and its successor cannot run.
Combined qualification orchestration, numerical exercise and fresh-process recovery:
15 passed in27.55s, two existing Torch warnings. Evidence:
outputs/prowl/testing/kd-final-admission-20261027-01. No GPU stages launched.
Teacher07 remains live at557/1333/current100/210tiles;329 protected repository
hashes match. The modified qualification module is outside those producing pins.
