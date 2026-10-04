# D-300 — complete real 2 mm cache

Completed September 30, 2026. The full **113 training / 40 development-validation** cache is built,
reopened and verified. All153 members and23 holds remain unchanged. No model forward or optimizer
updates occurred. The cache remains project-local reproducible scratch, not an independently backed-up
keeper or authority to launch training.

## Execution

| Job | Cases | Fresh source files | Cache construction | Total worker time | Peak process RSS |
|---|---:|---:|---:|---:|---:|
| pilot | 8 | 16 | 22.693 s | 29.381 s | 10.967 GiB |
| remainder | 145 | 290 | 199.333 s | 205.540 s | 7.904 GiB |
| assembly | 153 | 0 | 8.446 s | 17.311 s | 1.262 GiB |

Both fresh source requests read exactly306 CT/pancreas files in aggregate:
5,152,089,856compressed /13,196,550,237expanded bytes. The eight-case pilot passed before the145-case
remainder was enabled. Each source file was read once under the newD-300 budget, with source content,
physical units, geometry, role, purpose qualification, live binary policy and volume identity checks.
AllD-297 requests remain consumed; none was reused.

The final assembly read only the two verified cache parts. Every serialized final image/label hash
matches its source cache part exactly. Every target count matches retainedD-297 preprocessing
reports, and all loaded transforms/descriptors match the independently pinned expected binding.
No further filtering, recipe change or visual adjudication occurred; the prior153 reviewed sheets
and source limitations remain applicable.

## Storage, resource and consumer checks

Final cache: **3,117,120,477bytes (2.903GiB)**, including manifest and NPY
serialization. Tensor payload remains3,116,434,900bytes; overhead is685,577bytes.
Retained outputs across both parts and assembly total6,239,632,296bytes
(5.811GiB), within the9GiB aggregate limit. The100GiB internal-free floor held.
All per-job20minute/16GiB limits and AC checks passed. No automatic retry/deletion occurred.

Fresh synthetic96M-source/15,163,200-output rehearsal passed under the current code/environment,
5.264seconds and4.755GiB RSS. Native suite: **1,388 passed**, two existing warnings,35.49seconds.
New tests cover D-300 scope refusal, preserved single-read/role controls, exact8/145 partition,
prior evidence corruption and aggregate storage accounting.

The final full-inventory/hash/array open took1.784seconds immediately after
assembly. Representative per-role reads were12–16milliseconds. These are **OS-cache-warm observations**,
not cold-device benchmarks or full training throughput. Publication/open already verifies every
member. Sampler replay and reversible padding were additionally checked on one member per role;
validation sampling was refused. This does not qualify full-cohort MPS inference, restored predictions
or production checkpoints.

## Exact retained identity

- Final cache directory: `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL/outputs/prowl/twomm-cache-build-80569d7d-94e0-4c52-91ba-1a128dd076ae/cache`.
- Cache completion SHA-256: `b61897ed3176fecd9d8ca143285d9700699c1557537ba15b966a487134342bf7`.
- Full expected binding: `outputs/prowl/twomm-cache-readiness-20260930/proposed-binding.json`.
- Binding SHA-256: `ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d`. The previously proposed binding was used unchanged.
- D-300 capability SHA-256: `b05a556bb1d041ff3142d075861f80f066ffa539b254888f9ca3498adc219778`.
- Assembly result receipt SHA-256: `6e287408e137d13d5bb240c7e8f0e6823eda98ed0bedac2a57419f9b6c70c5bc`.
- Review root: `outputs/prowl/twomm-cache-build-review-20260930`.
- Review receipt SHA-256: `e101da6268aebba5b214c5d350db4967b644d3f5dc88d8ddd749e707364c39aa`.

The review pins all three result receipts, fresh requests, native test log, resource rehearsal and
reproduction helpers. All result member hashes were checked after completion. Individual requests,
claims, immutable control snapshots, worker/supervisor logs and both cache parts remain retained.
`complete.json` is mandatory but not sufficient alone: the consumer also needs the independent
completion pin and expected binding pin, and validates every entry.

## Next implementation

Connect this exact cache to the separately versioned144³ session/inference/checkpoint contract.
Start with synthetic save/reload and interruption tests, then freeze a zero-update MPS request
for edge cases and the full113/40 cohort. Measure native full-volume inference and source-grid
restoration/export costs while proving weights unchanged. Temporary patch padding must be removed
before V4 restoration, and ROI size must use acquired scan volume.

Production checkpoint identity must bind cache, recipe, sampler, patch policy and fresh run;
verify independent backup recovery before finalizing a finite training request. D-298 measured
synthetic update cost only; it does not set the real run duration or increase the adapter's300-step
ceiling. No new training request is frozen or launched at this checkpoint.
