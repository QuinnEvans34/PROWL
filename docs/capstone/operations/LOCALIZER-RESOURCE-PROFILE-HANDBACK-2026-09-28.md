# Localizer MPS resource profile handback

September 28, 2026. **Local MPS is feasible for the proposed tiny localizer smoke at 96³.**
The bounded synthetic profile passed with no automatic CPU fallback, OOM, monitor stop or reload
mismatch. This is a narrow feasibility result; full-capstone compute decision D-210 remains open.
[Pre-execution workload and limits](LOCALIZER-RESOURCE-PROFILE-PLAN-2026-09-28.md), authorized by D-272.

## Actual workload and results

Scratch binary SegResNet, 4,700,914 parameters, fp32, batch 1, 96³ patches; seed 42, AdamW,
LR 0.003, weight decay 1e-5, cosine horizon 40, two CPU threads, zero workers/cache. These are
profile settings, not a finalized scientific training recipe. MPS is required and worker environment
sets `PYTORCH_ENABLE_MPS_FALLBACK=0` before importing torch. Explicit CPU sampling, stitching and
checkpoint serialization are intended operations, not automatic unsupported-operation fallback.

Nine updates total: two warm-ups, six timed updates, one resumed update. Finite loss/gradients/
parameters passed. The invented volumes match the retained processed dimensions of cases 3/26 but
contain no source voxels. All arrays were generated in memory; no raw data or external drive read.

| Measurement | Observed result |
|---|---:|
| First / second warm-up update | 3.5066 / 0.7666 s |
| Six timed updates, median | **0.73616 s/update** (about 1.36 updates/s) |
| Timed update range | 0.73564–0.73730 s |
| Full-volume inference, 136×96×98 | 0.47533 / 0.37206 s; median 0.42369 s |
| Full-volume inference, 108×96×134 | 0.37430 / 0.37236 s; median 0.37333 s |
| MPS → CPU checkpoint-state transfer | 0.03970 s |
| Internal checkpoint write + fsync | 0.02166 s |
| Checkpoint hash + read | 0.03524 s |
| Model/optimizer/scheduler restore to MPS | 0.04993 s |
| Checkpoint size | 56,504,807 bytes (53.89 MiB) |
| Maximum probability difference after reload | **0.0**, allowed atol 1e-5, rtol 0 |
| Resumed update | 0.83181 s, finite loss/gradients |
| Total supervised worker duration | 14.190 s |

Raw timed samples: 0.73584433, 0.73592942, 0.73730233, 0.73563788, 0.73689346, 0.73638442 seconds.
Timings synchronize MPS. Updates include CPU sampling, transfer and finite checks, but not real-source
read/preprocessing. Inference is image-only sliding-window logits, 25% overlap, four windows per
volume, MPS prediction/CPU stitching. Softmax, restoration, output publication and visual review are
not included in those full-volume times. Checkpoint timing is one internal-disk observation, not an
external-storage benchmark; OS cache was uncontrolled. Two inference repeats/six updates are a short
smoke profile, not a long thermal/endurance run. No claim of exact resumed MPS training trajectory.

## Memory and supervision

Mac17,9, 64 GiB unified memory; AC power checked before and during the job. No competing Python
training process was observed at preflight; unrelated applications' GPU use is not ruled out.
A persistent nonblocking profile lock prevented cooperating profile jobs from overlapping.
This does not yet implement a common production accelerator lease across all workflows.

- Peak worker RSS sampled by the parent: **790,626,304 bytes (0.736 GiB)**.
- Highest stage-boundary MPS driver allocation: **2,479,734,784 bytes (2.309 GiB)**.
- Highest stage-boundary live tensor allocation: **181,850,624 bytes (0.169 GiB)**.

These are different overlapping measurements; do not add them as independent physical usage.
MPS samples are after synchronized stages, not a complete within-operation peak trace. The 16 GiB
MPS allocator budget plus stage checks and 16 GiB RSS polling cap passed. Supervisor polled every
0.25 s, checked free space and AC power, and enforced a 600 s deadline. No stop was triggered.
Internal free space at preflight was about 151.6 GiB, above the 100 GiB floor.

## Retained evidence and verification

Package: `outputs/prowl/localizer-resource-3eeec52b-d8e6-4451-9db1-f2453558adff`.
Receipt SHA-256: `8e44b3de1703f76c3b52e21433820af80d0cdf5122f985a93292e6197256a9fe`.
Six covered files / **56,550,730 bytes**, plus receipt; all hashes and byte counts independently
verified. Includes precompute source/plan/Git/hardware capture, installed package environment,
raw stage timings, worker log, supervisor measurements and serialized diagnostic state.
Checkpoint SHA-256: `99694757466f701742e80d410c91cf9ec4697ac0b4b00756e1563bd9441d33cd`.
The checkpoint is explicitly diagnostic, not a published production run artifact.

New script: `scripts/diagnostics/localizer_resource_profile.py`; new supervisor/timing tests:
`tests/test_localizer_resource_profile.py`. Twelve focused tests pass. Full native suite:
**1,046 passed**, two existing torch.jit warnings, 11.70 s. `git diff --check` passes. No changes to
the CPU session/checkpoint contract, dependencies or Claude files. The retained CPU source captures
and earlier diagnostic outputs remain intact. This profile passed on its first attempt.

## Provisional two-case smoke budget

For planning only, assuming one source case is loaded/preprocessed for every update (no cache):

| Component | Planning calculation |
|---|---|
| 100 updates | 100 × (0.73730 s max observed MPS update + 1.13999 s max prior case load/preprocess) = 187.73 s |
| Two full-cohort checks | Four case loads plus two inference passes of each shape = 6.26 s, excluding restoration/publication |
| Four checkpoint cycles | 0.59 s using internal transfer/write/read/reload observations only; external cost not established |
| Startup allowance | 60 s, informed by the prior roughly 42 s supervised loader/preprocessing diagnostic |
| Subtotal / plus 25% contingency | 254.57 / **318.22 s (5.3 minutes)** |

Prior input timings come from the separate preprocessing receipt
`286a454c890637b228cb879b698e5b019571e50d465b27c34797316c7deae446`; they are not newly measured
or labeled cold storage. This is a rough engineering estimate, not a promised completion time.
The real input bridge must reuse a verified dataset instance rather than repeat full cohort resolution
every update. Current output/backup storage and final restoration/publication still need verification.

**Recommended candidate limits:** at most 100 optimizer updates, 10 minutes for updates, 20 minutes
end-to-end, 16 GiB RSS/MPS limits with AC power monitoring, one accelerator owner, 1 GiB output reserve
and the existing 100 GiB internal free-space floor. Checkpoint every 25 updates, preserve every attempt,
and stop at the first limit. A 1 GiB reserve covers the estimated four roughly 54 MiB checkpoints,
retry space and small predictions/control records. These limits must be frozen in the actual run plan,
with external-space/backup checks; no silent budget extension or launch is authorized here.

The evidence supports staying local for this smoke. There is no measured reason to buy remote compute
or lower the 96³ patch size. It does not justify increasing batch size, cohort or experiment horizon.

## Next implementation

1. Bind the real frozen cohort and preprocessing output to the MPS training path with recorded
   configuration, source/environment identity and explicit device policy.
2. Extend verified production run/checkpoint publication to a narrowly authorized artifact area,
   test MPS checkpoint recovery there, measure that storage path and verify a separate keeper restore.
   The current cohort-only storage capability and CPU-only checkpoint identity remain unchanged.
3. Write the CAP-EXP smoke plan with exact settings, criteria, cadence and limits, then review launch
   readiness. Source qualification and the difficult-case policy are unchanged. No real training began.

The earlier Phase E outline is partially satisfied by this profile, not wholly completed. MLflow
export, full run-schema integration and broader capstone benchmarking remain separate work.
