# D-302 — execute the eight-case cached inference pilot

Quinton: “Great, move onto the next pilot plan.” This authorizes implementation, tests and the exact
zero-update pilot described in the [packet](TWOMM-INFERENCE-PROFILE-PACKET-2026-09-30.md).
Codex owns the new export module, pilot runner/tests, and optional cache-load/inference timing in the
D-301 session. Claude's lane, source labels, membership and historical consumers stay unchanged.

Use the packet's exact eight role/index/member triples, fixed final cache/binding pins, seed42 and
144³ session. Freeze source/environment controls and a fresh single-use request only after tests pass.
Check raw-source access denial, immutable request controls, changed cache rejection, resource stops,
interrupted worker failure preservation, anisotropic/flipped native geometry and asymmetric patch
unpadding. No label-derived image crop or training update is permitted.

Supervisor budget is shared across profile and fresh-process recovery:20minutes,16GiB process
RSS/driver,1GiB new local output,AC power and100GiB internal-free floor. Stage-end driver samples are
not allocator-peak measurements. Independent store ceilings are frozen before work and shared across
checkpoint/backup/restore: max1GiB new bytes per domain and20GiB aggregate backup cap. No deletion.

Read all153 cache entries for initial integrity verification; only eight enter the model. Load one case
at a time. Save native uint8 binary predictions and records; check actual source shape, float32 NIfTI1
sform representation of the retained affine, millimeter units, foreground counts and hashes. Reopen
all exports before completion. Record separate cache-read, inference, restoration/export timings and
exact unchanged model digests. These random initialized masks do not measure localization quality.

Save an actual-cache-bound step0 checkpoint, independently back it up, then restore in a fresh process
with primary reads blocked. Compare exact weights and a fixed generated-fixture probability probe
(max difference1e-5). No native references are read or scored. The request is consumed before work;
failed attempts are retained and need a new explicit request, never an automatic rerun.

After review, report whether the remaining145 can fit the proposed20minute/16GiB/4GiB continuation.
That continuation needs its own tested request path; the pilot runner permits only the eight cases.
No real training request or model promotion is implied.
