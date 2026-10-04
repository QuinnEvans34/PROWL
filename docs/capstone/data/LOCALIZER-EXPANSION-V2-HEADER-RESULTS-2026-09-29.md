# Expanded candidate header preflight — D-291

All148 new candidates/296 files were inspected successfully using bounded header reads. **All148
CT/pancreas pairs match in header shape and affine.** This is header-level evidence only: no voxel
arrays were decoded, content CRC/hash integrity was not established, and no qualification changed.

| Observation | Training | Development validation |
|---|---:|---:|
| New candidates inspected |112|36|
| CT declares mm |103|31|
| CT units unknown |9|5|
| Pancreas target units unknown |106|35|
| Cases over64M voxels |4|1|
| Estimated expanded array bytes |9,806,065,515|2,508,909,903|

Fourteen CT unit issues remain unresolved. Unknown target units are a separate evidence question;
they may be interpreted only through a positively verified matching mm CT grid under the established
policy. No header, image or target was rewritten. No case was silently removed or replaced.

The five resource exceptions are1935 (77.81M voxels),3206 (72.36M),6822 (90.04M),8937 (92.89M),
and validation6186 (67.28M). These are larger valid-looking header grids, not evidence of corruption.
Their admissibility to a new consumer requires resource verification; existing64M limits stay intact.
The original28 candidates are untouched, including the existing unit hold on6350.

## Execution and verification

Elapsed23.68seconds; peakRSS56,983,552bytes (54.3MiB). Read1,212,416compressed bytes (4096/file),
well below20MiB, and decoded only348-byte headers. The compressed prefixes can include array data
in compressed form; no voxel arrays were decompressed or interpreted. Exact pre/post stat identity
and registered mount checks passed. No unresolved-format cases or header grid mismatches occurred.

New runner: `scripts/diagnostics/localizer_candidate_headers_v2.py`; old28-case runner unchanged.
Ten new tests cover correct sizing, selection/role/path substitutions, duplicate membership, source
identity drift, symlink traversal, truncation/unsupported formats and read-limit accounting. The first
test pass exposed a Nibabel-specific unsupported-header exception; it was handled before freezing
or executing the real request. Final native suite: **1,230 passed**, two existing warnings,32.26seconds.

Frozen request: `outputs/prowl/candidate-headers-v2-request-2415af05-a1dd-4a3c-9adf-ce04b7605819`;
SHA-256 `795b5932282591767cc6aaa6adf08001d948ca9af981285e552100360f046863`.
Consumed result: `outputs/prowl/candidate-headers-v2-551775cb-f388-44e0-9453-b49b181c9621`;
receipt SHA-256 `8c9538785427e54ffce6334425ee0a8cccf9a720aa933c69ab8a25b27446f828`.
All receipt members were independently rehashed before summarizing. Derived scripts, test log and
verification are retained in `outputs/prowl/candidate-headers-v2-review-20260929`.

## Next bounded action

The [content plan](LOCALIZER-EXPANSION-V2-CONTENT-PLAN-2026-09-29.md) and exact JSON account for
all148 cases in15 proposed batches:10 standard batches and5 larger singletons. This is not content
execution or qualification. Next implement/test the batch consumer, freeze a first standard pilot,
inspect content and alignment evidence, then continue supported batches. The5 larger cases require
an explicit tested diagnostic resource extension; they remain in candidate accounting meanwhile.

Training still waits for positive case-specific qualification, new immutable role cohorts and a
versioned consumer/resource profile. No model inference, optimizer updates or Git publication ran.
