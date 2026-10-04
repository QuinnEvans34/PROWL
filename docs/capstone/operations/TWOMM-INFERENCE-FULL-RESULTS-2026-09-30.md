# D-303 — all153 cached cases pass inference, export and recovery readiness

The distinct145-case continuation passed, completing all113train/40development-validation cases with
the earlier eight-case pilot. Exact original role/index/member triples reconcile with no omissions,
duplicates, replacements or changed initial weights. All23 source/target holds remain outside the
frozen cohort; no eligibility decisions changed. Zero real optimizer updates and zero raw source reads.

## Continuation measurements

| Measure | Result |
|---|---:|
|Cases|107train +38development-validation =145|
|Profile worker, including cache checks/checkpoint/backup|409.212s (6.82min)|
|Fresh-process independent recovery|4.418s|
|Initial153-entry cache integrity verification|2.109s|
|145 cache reads, warm|2.508s total|
|Full-volume144³ inference|246.120s total;0.823–5.268s per case|
|Native-grid restoration|114.816s total|
|Export and first reopen verification|29.142s total|
|Peak profile worker RSS|3,254,910,976bytes (3.031GiB)|
|Peak recovery worker RSS|729,071,616bytes (0.679GiB)|
|Maximum stage-end driver sample, including recovery|1,429,913,600bytes (1.332GiB)|
|Continuation package before final receipt|158,269,466bytes (150.94MiB)|

Worker totals exclude the parent's final verification and preflight. All work passed the shared20minute,
16GiB,4GiB-output limits, AC requirement and100GiB internal-free floor. Sampled driver values are not
allocator peaks. The eight-case pilot's4.498GiB process peak remains the higher observed value across
the full cohort. Cache timings describe warm reads, not cold-device performance.

Native exports preserve source shape, float32 NIfTI1 sform representation of source affine,
millimeter units and binary uint8 content. Export hashes/foreground counts and unchanged model digests
were checked after every case. These are initialized predictions, not trained-model accuracy evidence.
Native references were not opened or scored.

## Independent recovery and complete reconciliation

The continuation's step0 checkpoint binds the actual cache/input/source/environment identity. It was
published and independently backed up under the existing registered volume/cap checks. A fresh
process prohibited primary-drive reads and restored to a new destination. Weights match exactly,
optimizer state remains empty, and the fixed generated-fixture probability probe differs by0.
This is process-level primary-read blocking, not a physical disconnect test.

After completion, all31 pilot plus306 continuation receipt members were independently size/hash
verified. All153 native exports were reopened and semantically rechecked; that final combined geometry
verification took18.882s, apart from the hash pass. Combined membership/roles and identical initialization
were independently recomputed, and original cache completion/binding pins still match.
The parent also wrote a153-member aggregate record before completion. No active process remains.

1,460 native tests pass (23 new; two existing upstream warnings). Tests cover exact complement,
protected roles, duplicate/missing/reordered/substituted cases, changed pilot evidence, request reuse,
old-schema refusal, changed controls/limits, interruption cleanup and aggregate initialization/membership.
The native test log is retained in the review package. Scoped whitespace checks pass.

Only the new continuation runner/tests and planning/status documents were added/updated for D-303.
The eight-case pilot runner, earlier consumers, data source files and Claude's retrieval lane remain unchanged.

## Exact retained records

Continuation directory:
`outputs/prowl/twomm-session-continuation-1e8f209b-a692-4d26-9ff7-3470ead10427`.

- Request: `73b50472f6786860744fdb6eb51e61b28b91d8c85f36df704db306351f46d1d2`.
- Completion: `e72ebedd2b318b629282f389adfb03b0bae9bc4b4af6212bafcb5e0cd00fcd64`.
- Parent pilot completion: `5764b267a2f2cfef95e327804364b5b4228f51c2359274e1c4b18c0e54f3d76f`.
- Shared initial weight digest: `365306b1aec77681bd651a1e87ca7902b10efffef38607f1618303220d20954e`.
- Restore artifact: `restore:6fd4314c-f872-4ec6-acab-b6f8da03bfae`.
- Restore completion: `26c9fa4b555170568a39abc7316dc5798f952559c735c0a3b2dd4b192a06e701`.

Review package: `outputs/prowl/twomm-inference-full-review-20260930`.
Review receipt: `c45220c6c03168c8355091be07a9b7dd2f0ff0945529bee1f0c67cdb770803ab`.
It retains summary, aggregate153-member record and full native test log. The one continuation attempt
passed; its request and both worker-stage markers are consumed. Do not rerun it or the pilot.

## Next work is training completion

The full cohort now passes the model-input/inference/export path. The
[training completion packet](TWOMM-TRAINING-COMPLETION-PACKET-2026-09-30.md) identifies the remaining
bounded implementation: target-only native-reference access and metrics, then a separate authorized
training executor with progress/checkpoint/recovery and a frozen finite experiment request.

Important finding: older native metrics refuse grids above64M or predictions above4M foreground
voxels. The new96M native metric path must score dense bad predictions instead of excluding them.
A target-only reader can avoid CT rereads: one153-label pass is21,942,279 compressed bytes,
4,398,868,031 expanded bytes, read one at a time. Those are retained metadata counts; no new read
capability or job was executed in this step.

The packet proposes300 initial updates within the current adapter ceiling, with exact exposure and
before/after coverage diagnostics. Its45minute envelope and schedule remain proposals until the
finished loop is rehearsed and the exact request frozen. No real training is pending or launched by
D-303, and no model/recipe promotion or generalization claim follows from this readiness result.
