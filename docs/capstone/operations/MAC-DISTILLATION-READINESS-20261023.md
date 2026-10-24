# Mac distillation preparation — October 23

Status: **engineering progress; NOT ready for scientific training**.
User approved autonomous preparation through readiness, stopping before the scientific run.
Windows producing checkout and its active varied-focus run were not modified.

## Verified now

- Source integrated through 9548582; Mac64GB, AC, native MPS available.
- Exact 606,931,502-byte teacher downloaded and SHA256 verified against the existing
  Windows specification (`ff0f0868…d1f`). External unmodified source checked against
  pinned Git blobs. Isolated einops0.8.1; no package replacement in either main venv.
- Existing restricted weights-only/inert-record converter succeeded, exact exported
  tensor reloads, no unrestricted pickle. CPU strict teacher load and two forwards pass.
- Native MPS, CPU fallback disabled: two32³ and two128³ forwards pass, exact repeated
  probabilities and unchanged frozen weights.128³ stage8.73s including startup, sampled
  owned RSS761,167,872B; final MPS driver allocation8,562,524,160B. RSS alone does not
  describe unified GPU memory. This is synthetic compatibility, not teacher quality.
- Actual production SegResNet,144³ invented inputs: one supervised and one zero-KD
  update compared within predefined rtol1.3e-6/atol1e-5; two positive-KD updates saved
  first and next checkpoints. Producer then failed reporting a NumPy float32 to JSON.
  Failure/empty report/checkpoints preserved. Reporting corrected separately, with
  regression tests. No successful producer-report claim or repeated producer run.
- Fresh process restored saved positive-KD checkpoint and performed the next update;
  full nested student state compared to retained expected state within those same
  tolerances.7.12s,1,135,132,672B peak sampled owned RSS, worker reaped. This is not
  bit-exact future MPS continuation or long-run drift qualification.

All model workers had240s/12GiB owned-RSS budgets and were reaped. Teacher checks
also checked final MPS allocation<=12GiB; that post-call check is not a continuous
GPU peak cap. No patient CTs, annotations or scientific updates were used. Five
actual synthetic student updates total across producer and cold check. The new
supervisor now uses the existing `.mps-profile.lock` for future stages. Initial
checks used a dedicated engineering lock with no other Mac trainer present.

Artifacts: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/`.
Each stage retains request, logs/resources and source hashes. Original supervisor
snapshots were recovered and matched to the recorded hashes before subsequent
helper edits; snapshots do not rewrite the original requests. Safe tensor export
hashes are in convert-01/conversion.json; serialization may differ by Torch version,
so exact tensor reload is distinct from matching a Windows serialized-file hash.

## Remaining before ready

1. Obtain frozen12-case training pilot list and current1333train/70development
   membership, native-region/cache metadata and candidate recipe from Windows.
   Do not substitute the old Mac split or silently pick easier cases.
2. Bind those identities to actual local source files and construct a separately
   budgeted Mac pilot. Preserve class19 sigmoid, full-CT teacher preprocessing,
   native world geometry, coverage and teacher-target provenance. Inspect every
   pilot contour and measure actual time, compression and memory before full cache.
3. Fix and qualify any demonstrated pilot problems. Complete target availability
   and storage/runtime projection precede a full scientific recipe.
4. Independently verify backup/restore using the approved internal storage budget.
   User approved the Mac preparation reserve change on October23: **50 GB decimal
   internal free**, at most4GiB new backups within26GiB total backup storage.
   The Mac supervisor now checks these limits before dispatch and records them in
   new stage requests; projected-write checks are available for backup preparation.
   External reserve remains100GiB. Windows limits and historical receipts are unchanged.
   Existing backup usage~19.71GiB. Independent backup/restore remains pending.
5. Select matched Mac no-KD/control recipe with current result review. Unknown
   teacher development membership remains exploratory. No independent claim.
6. Freeze actual runtime, configuration/cohort/source identities, selected/terminal
   native evaluation and launch receipt; return concrete scientific run for approval.

The user authorized the metadata handoff request, and it was sent to “Plan capstone
experiment workflow”: frozen12-case order, current membership/exclusions, candidate
recipe, source hashes and existing coverage/cache evidence. The laptop reports the
metadata archive assembled and undergoing checksum verification; transfer pending.
No new listener, training run, cache-wide generation or paid polling.
Existing long-training .venv312 has torch2.13.0/MONAI1.6.0/MLflow3.15.0/SimpleITK2.5.6;
it needed isolated test/jsonschema dependencies. .venv-prowl synthetic checks have
no MLflow/SimpleITK. Do not conflate their test results with a single qualified
scientific runtime. Initial collection failures are retained in tool history.

Final focused test result:125passed in5.07s using `.venv312` plus the isolated
external test dependencies. Includes loss/targets/checkpoint/geometry/integration/
tracking and five new reporting checks. No model-quality conclusion follows.

Storage-change verification:15 focused tests pass, including projected writes and
exact reserve/backup boundaries. Live preflight passes with91.1GB internal free,
2.07TB external free and21.14GB existing backup files. No new model run or backup
was performed for this policy change.

## Private handoff received and pilot sources bound

October23: received the4,057,125-byte archive using the user-provided private
transfer code. SHA256 `04d5b0521407c19a5fb4d8f664cc43c3b77be2ba7346246041713f00f24761c5`
matched before extraction. The binding diagnostic independently checks every
manifest-listed archive member, membership separation and the fixed12 training
cases. All36 Mac source files (CT, pancreas, lesion) match the producer hashes.
Evidence: external `pilot-local-bindings-01.json`; original archive retained.
No decoded voxel reads, repeated cohort audit, inference or scientific updates.

The existing Windows pilot is CUDA-specific and gated on parent completion. It
remains unchanged. Next: an additive Mac pilot with explicit MPS resource limits,
the same source geometry/preprocessing and12-case order, plus independent backup
verification. Real teacher quality, target-cache feasibility and the matched
scientific control remain unqualified.
