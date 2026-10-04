# Step 2: live metadata preflight and per-file inventory

**Date:** September 28, 2026. **Status:** completed metadata-only observation; content qualification pending.
Quinton requested continuing the four-step sequence. This run implements the bounded preflight in
[S2 scope](SOURCE-VERIFICATION-SCOPE-2026-09-28.md); it does not grant source readiness or eligibility.
[Machine-readable review](LOCALIZER-METADATA-PREFLIGHT-2026-09-28.json).

## Result

The registered external volume UUID/APFS identity and canonical source paths passed checks before,
during and after traversal. Production source aliases and scientific-run settings were not activated.

| Observed input | PROWL train | PROWL validation | Total | Bytes |
|---|---:|---:|---:|---:|
| CT | 7,200 | 1,800 | 9,000 | 317,614,413,856 |
| Pancreas mask | 7,200 | 1,800 | 9,000 | 1,365,403,323 |

All 18,000 expected files were present and nonzero-sized, with unique study/kind associations. All
nine CT shard byte totals match their retained extraction receipts. These are presence/size checks,
not proof that the current bytes match the archive or that the annotations are usable.

The scan observed 297,900 directory entries and finished traversal in 541.42 seconds, within the
600-second limit. It observed the names of 901 publisher-test label directories but did not traverse
those directories or inspect publisher-test payloads. Source CT/mask contents were never opened;
all per-file content hashes remain null. No source files were modified.

Among unrelated training labels, 8,999 celiac-artery files were observed. This is a metadata count,
not a finding of corruption or model difficulty, and no extra investigation was launched. Other
structure counts are retained in the evidence. The pancreas count is complete for this scope.

## Implementation and tests

- `src/data/source_metadata_inventory.py`: bounded directory/stat adapter, no payload-open path.
- `scripts/diagnostics/localizer_metadata_preflight.py`: binds pinned local controls to the registered
  source root, checks the volume, invokes the adapter and writes one diagnostic evidence package.
- `tests/test_source_metadata_inventory.py`: **13 passed**, covering no payload opening, publisher-test
  traversal exclusion, missing-file retention, wrong layouts, links, mount failure and resource limits.
- Full native Python suite: **893 passed in 6.96s**, two existing upstream torch.jit warnings.

The initial sandbox attempt failed at macOS disk identity access before source traversal or package
creation. The approved escalation reran the same command with disk-management access and completed.
This did not require changing a mount, registry or source alias.

Recorded limits: 600 seconds, 350,000 entries, 512 MiB process peak-memory check during traversal,
64 MiB evidence-output cap, internal 100 GiB free-space floor. No source write or bulk content read.
The adapter uses the trusted single-writer boundary: observations are point-in-time, not an atomic
snapshot against an adversarial concurrent writer. Missing files are reported; unsafe layouts stop.

## Retained evidence

Package: `outputs/prowl/localizer-metadata-4c93efaa-f102-4bef-bae6-8966b3446d91`.
It contains the exact request, implementation source capture, 18,000 per-file observations, summary
and verification receipt; total 5,779,584 bytes. Four receipt-covered file hashes were independently
rechecked; all passed. Receipt SHA-256:
`201342b56dd420783136a25c6faf278a224b68f904b1b56dd39278e458c1131b`.

The review additionally verified protected-role counts, uniqueness, absence of zero-byte files and
all nine CT shard byte totals. The original scope JSON remains unchanged because its hash is a run
input. This result is a new evidence artifact, not an edit of historical source qualification.

## Next

Step 2 now has live root verification and an exact CT/pancreas path/size inventory. The remaining
content-read scope can be based on actual files rather than inferred directory summaries. Combined
CT/pancreas size is 318,979,817,179 bytes; no time forecast for reading those contents is established
by this metadata traversal. Do not repeat the nine-minute traversal without a reason.

Next prepare the bounded content-verification/qualification job: specify which source-wide integrity
checks are required or supported by retained receipts, the candidate selection and exact files,
positive provenance/use evidence and any narrow resolution rules, then measure read throughput under
a small explicit budget before fixing a larger read limit. No whole-source hash job is implied.
Steps 3/4 remain pending. Existing holds, original membership and difficult-case candidacy are unchanged.
