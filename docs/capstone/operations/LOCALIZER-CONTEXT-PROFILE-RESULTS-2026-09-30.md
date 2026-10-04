# D-298 — synthetic MPS physical-context comparison

Both bounded profiles completed on September 30. Recommend **144³ at 2 mm** as the candidate
for the next versioned adapter/cache checks: it preserves the previous 288 mm physical input
span. This is a resource recommendation, not a final training recipe or evidence of better learning.
The original 96³ production guard remains unchanged. No real source reads or optimizer updates.

| Synthetic profile | 96³ | 144³ |
|---|---:|---:|
| Nominal input span at 2 mm | 192 mm | 288 mm |
| Median update, six measured after two warmups | 0.8253 s | 2.6839 s |
| Median same-volume sliding-window inference, two repeats | 2.1263 s | 3.1594 s |
| Maximum sampled MPS driver allocation | 2.306 GiB | 4.822 GiB |
| Maximum sampled MPS live allocation | 0.163 GiB | 0.202 GiB |
| Supervisor-observed peak process RSS | 0.870 GiB | 0.982 GiB |
| Total process time | 14.960 s | 34.235 s |
| Reload probability max difference | 0 | 0 |

The larger patch costs about 3.25× per update and 1.49× for this single invented inference volume.
These short profiles do not predict full-cohort throughput, sustained thermal behavior or training
memory with the 2.9 GiB cache resident. MPS samples were taken at synchronized stage boundaries;
they are not allocator high-water measurements, and process RSS excludes some GPU allocations.
The driver memory ceiling was also configured before work. All recorded budgets passed.

## Scope and validation

Same production scratch SegResNet initialization, balanced CE/foreground Dice, AdamW at 0.0003,
seed42, no MPS fallback. Each profile used eight updates on invented data, two forwards of the same
192×160×192 synthetic volume, save/reload and one resumed synthetic update. Finite losses, gradients,
parameters, shape and CPU-stitched outputs passed. Restore is same-process model/optimizer/scheduler
reload, not independently backed-up production recovery or next-update equivalence.

The profiler uses a separate synthetic center crop. It does not qualify the production sampler,
which still rejects144³. No architecture/receptive-field equivalence follows solely from matching
input span; spacing changes the physical scale of fixed convolution kernels too. The later experiment
must identify cohort, resolution, patch/context and exposure as changed factors.

Native suite: **1,345 passed**, two existing warnings,36.04seconds. An initial sandbox run had1343
passes and two failures because `/bin/ps` was unavailable in existing supervisor tests. Native rerun
resolved both without weakening checks. Eight new tests cover disallowed sizes, preservation of the
production guard and exact copied center crops for both profile sizes.

## Retained evidence

- 96³: `outputs/prowl/context-resource-ac98050c-86a0-4773-9edc-50d2d371126c`; receipt `7b7a3e16af84a9da9335b129873d00982c975217ef1de8fc724ce36bc3b83d9d`.
- 144³: `outputs/prowl/context-resource-c8259a06-2ebb-4e08-9fd6-27fd31be1755`; receipt `b15f13002ea8a0cb9ace3a610fe9b483710cdc4aa909dba87791e43b3518e014`.
- Comparison and both test attempts: `outputs/prowl/context-profile-review-20260930`; receipt `23270b4b45b9069cc803f58d9c6f9af8ba9782f40ddc914f8ba69aa42cbc5c33`.

All profile receipts and member hashes were verified, and captured source text matches current files.
The parent supervisor retains request/source text, package environment, exact limits, all timing
samples, checkpoints and failures. No dependencies, old data consumers or Claude files were changed.

## Next

Implement the [bounded cache/adapter packet](TWOMM-CACHE-IMPLEMENTATION-PACKET-2026-09-30.md) on
synthetic fixtures. Existing cache has a512MiB cap and V2 transforms; it cannot consume D-297's V4
cohort. Use a separate version, explicit budget, exact role/identity/hash binding and all-or-fail
publication. Keep preprocessing minimum96 unchanged; temporary patch padding needs its own verified
trace and inversion. Then freeze fresh real cache-build/zero-update profile requests and demonstrate
independent checkpoint recovery before preparing a training launch request.
