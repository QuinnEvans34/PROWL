# Next bounded slice — 2 mm role cache and patch adapter

Prepared during D-298. No cache construction or new source reads have occurred.

## Contract changes requiring explicit versions

The old expanded cache is RAM-only, caps payload at 512 MiB and requires V2 transform records.
D-297 produces V4 transforms and 3,116,434,900 bytes of float32-image/uint8-label payload.
Do not increase the old cache cap or accept new transform versions through its existing contract.
Implement a new cache contract with a 4 GiB payload ceiling and separately accounted metadata,
serialization and temporary-file budgets. Decide persisted disk versus RAM lifecycle explicitly;
prefer persisted, hash-bound entries so later experiments need not repeatedly decode the source.
Guard the 100 GiB internal-free floor and registered output location before construction.

Bind each entry to exact D-294 member, role, qualification, source hashes, D-297 recipe,
transform record and source-grid geometry. Bind the complete manifest to the D-297 review receipt.
Preserve source observations and all 23 holds. Completion publishes only after all 113/40 entries
are validated; interrupted or partial construction must never resolve as a complete training cache.
Test stale bytes, swapped identities, missing members, duplicate/cross-role entries, wrong transform
version/recipe, corrupted geometry and exceeded budgets. Use synthetic fixtures before real reads.

## Patch adapter

D-298 profiles model/loss kernels with synthetic center crops. It does not qualify the real sampler.
Keep the old 96³ config guard. Add a separately versioned bounded configuration for the selected
patch and adapt the deterministic positive/background sampler with trace/replay tests. Check small
volumes and padding explicitly: D-297's minimum96 recipe must not silently become minimum144.
A sampler/inferer may pad temporarily; retain and invert that operation correctly, exclude padded
extent from acquired-volume metrics, and do not rewrite the qualified transform recipe.
Test train-only optimization, validation rejection, step budgets and deterministic interruption.

## Real build and MPS checks after synthetic acceptance

Freeze a fresh exact cache-build request and source-read capability for the same 306 files and
verified byte counts; all D-297 requests are consumed and cannot be reused. Start with edge/output
cases, then complete the frozen cohort under measured aggregate bounds. Do not publish eligibility
changes or substitute cases. Account for both construction and retained cache sizes.

Bind a fresh model/recipe/patch/cache identity, then perform zero-update MPS profiling of the edge
cases and full cohort. Measure full-volume sliding-window costs, exports and source-grid restoration,
not just patch updates. Verify unchanged weights, production checkpoint save/reload and independent
backup recovery. Only then freeze a finite training request with exact updates/time/storage,
sampling exposures, validation cadence and coverage safeguards for Quinton's launch review.
