# D-299 — persisted 2 mm cache and 144³ adapter

Completed September 30, 2026 under Quinton's “Great, move onto the next” following D-298.
The separate cache and patch contracts now pass synthetic qualification. No real source reads,
real cache publication, optimizer updates, source changes or eligibility changes occurred.

## Implemented

- `src/training/twomm_cache.py`: separate `twomm-cache-1` contract. Persisted non-pickle NPY
  float32 images and uint8 labels; exact independently supplied binding and completion SHA pins;
  V4 recipe/transform validation; unique explicit train/validation roles and exact descriptors.
  Binding includes the cohort completion and D-297 review pins, each full source/qualification
  descriptor, original/processed geometry and retained observations. Wrong or changed records fail.
- Payload ceiling 4 GiB; serialization plus metadata overhead ceiling 64 MiB; 100 GiB free-space
  floor checked before each write. Caller must supply an authorized existing empty directory and
  enforce the storage registry. This low-level contract does not activate or select a storage root.
- Publication writes and fsyncs individual files, verifies serialized arrays, then writes completion
  last. A failed/interrupted directory remains incomplete; no automatic resume or overwrite. Opening
  checks the full inventory and every array, and later reads recheck content hashes. Arrays are read
  one case at a time rather than retaining the whole cohort in RAM. Returned data is independently owned.
- `src/training/twomm_adapter.py`: separate `twomm-adapter-1` with exact144³, balanced loss and inherited
  diagnostic ceiling of300 steps. It provides no optimizer or training-launch API. The old96³ and
  512MiB/V2 consumer contracts remain unchanged.
- Stateless seed/member/completed-step crop selection, train-only sampler and reversible symmetric
  patch padding. Centers are chosen on the processed grid before extra patch padding. Existing
  preprocessing padding is still eligible background; this is **not** acquired-voxels-only sampling.
  Sampling policy is explicitly versioned `processed_grid_pancreas_background_equal_v2`.
- Temporary padding is capped at16M voxels before allocation. Padding traces retain original shape;
  removal verifies the trace and restores that grid exactly. D-297's minimum96 recipe stays unchanged.
  A future inferer must remove temporary padding before V4 source restoration and acquired-volume metrics.

## Verification and retained evidence

**1,379 native tests pass**, two existing upstream warnings,35.37seconds. The34 added cases cover
partial publication, stale bytes, missing/swapped/symlinked arrays, manifest membership, descriptor and
transform drift, duplicate/cross-role binding, payload/serialization/free-space limits, defensive reads,
step/role refusal, config versions, temporary-volume limits and odd/asymmetric padding inversion.

The standalone rehearsal (`scripts/diagnostics/twomm_cache_rehearsal.py`) builds an invented two-role
cache, reopens it from persisted bytes at four simulated interruption boundaries and exactly replays
its next crop each time. Validation sampling is refused. Padding reversal is exact. This verifies
sampler replay, not optimizer-state/checkpoint recovery or next-update equivalence.

- Rehearsal: `outputs/prowl/twomm-cache-synthetic-269e8f11-3813-4860-bc5f-82738863408b`.
- Rehearsal receipt: `af078cfe5c4ae99341322b31cbcb8037017a216b3a88cb4d7050ae7b8d7e7350`.
- Readiness evidence: `outputs/prowl/twomm-cache-readiness-20260930`.
- Readiness receipt: `dd2b8d9c0763f69116c89a461d4b320d85abbd225552bfb8e1473f840d55e694`.

## Real-cohort preparation without new source reads

Verified retained D-297 review and case-report hashes, then assembled a **proposed** binding for the
same113 train/40 development-validation members. SHA:
`ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d`.
This is not a frozen build request, a new qualification decision or a production cache.

Payload remains3,116,434,900bytes (2.902GiB). All153 temporary144-padding projections fit16M;
maximum14,672,632voxels (7957). No additional filtering or recipe adjustment is needed on these shapes.
Full source verification, live purpose permissions and registered-root/resource checks still belong
to the fresh real build job; externally pinned expected records do not substitute for those checks.

## Next bounded step

Implement a supervised, single-use cache-build request using this binding and a fresh scoped source
capability. Start with edge/output cases, inspect retained output and resources, then finish113/40
under explicit aggregate bounds. Preserve consumed D-297 requests. Measure actual disk overhead,
construction RSS/time and cold/warm resolver performance; do not extrapolate from synthetic timings.

After cache completion: connect the versioned adapter to zero-update MPS inference, qualify temporary
padding/source restoration, verify unchanged weights and production checkpoint identity/independent
backup recovery. Then choose a finite training budget and freeze a concrete launch request.
No final training recipe, increased update budget or automatic model launch is implied here.
