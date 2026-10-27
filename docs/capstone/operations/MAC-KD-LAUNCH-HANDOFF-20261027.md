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
