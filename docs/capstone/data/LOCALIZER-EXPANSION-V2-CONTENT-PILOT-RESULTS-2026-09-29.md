# First expanded content pilot — D-292 results

**Batch-01 completed within its limits, and all16 alignment sheets were reviewed.** The evidence
supports continuing the remaining standard content batches. These16 candidates are not yet formally
qualified or published into a new training cohort; the existing16/11 runtime remains unchanged.

## What passed

Exactly16 new training cases/32 CT-pancreas files:56,122,150,199,202,261,430,756,767,795,804,1250,
1282,1369,1396,1462. All source identities matched the retained inventory; gzip EOF/CRC and file
SHA-256 were recorded. Decoded shape, datatype, units and affine matched pinned header evidence.

All16 CT arrays are finite and declare mm. All16 native CT/target grids match. Every target is
nonempty with semantic values exactly0 and1, accepted by the existing approved binary policy.
Fifteen target headers lack units; the matching mm CT grids supply evidence for later scoped
CT-grounded qualification. No source header was rewritten. No automated blocking content holds
were raised in this batch. No duplicate CT hashes occurred within the batch; cross-batch/retained
reconciliation remains required before cohort freeze.

## Limited visual review and retained difficult cases

Codex inspected all16 ten-panel sheets: plain/overlay pairs at five target-related planes per case.
No gross CT/target displacement was identified on these planes. This is engineering alignment review,
not every-slice inspection, independent expert annotation acceptance or clinical interpretation.

Five masks contact the inferior canonical source-array face: **56,150,1250,1396,1462**. Exact
boundary contact was confirmed from retained mask bounds and header orientation/shape, without new
source reads. Preserve these as visible-target/coverage observations; do not claim full-organ coverage
or silently exclude them. Several scans show noise or coarse reformats, also retained in review notes.
Case1282 has a nonaxial/coarse appearance in the reformats; no axis-permutation failure was observed
on its reviewed planes. These observations do not prove every contour boundary is correct.

## Measured costs and verification

| Measure | Observed | Limit |
|---|---:|---:|
| Wall time |41.53s|1200s|
| Peak process RSS |3,675,488,256bytes /3.42GiB|16GiB|
| Compressed source bytes |570,362,545|1GiB|
| Expanded source bytes |1,514,852,372|4GiB|
| Evidence package bytes |10,602,285|256MiB|
| Source files |32|Exact32|

Resource use leaves headroom for the same-sized standard batches, not proof that larger singletons
or all cases in RAM are safe. The old64M voxel scope is unchanged; the five larger cases still need
the separate tested diagnostic extension. No model inference, optimizer update or qualification ran.

Twelve new tests cover exact pilot selection, substituted/duplicate/held/wrong-role members, altered
header evidence or budgets, inactive batches and decoded-header mismatch. Existing bounded-reader,
gzip, semantic-decoding and resource checks also passed. **1,242 native tests passed**, two existing
upstream warnings,32.39seconds. Source/environment were unchanged through the frozen run.

## Immutable evidence

Request: `outputs/prowl/localizer-content-v2-request-66be7717-2baa-45c0-acb3-0143cc2d7a8f`;
SHA-256 `989fd4666440548783d945ecbb3a7ad14f4ffd285d4efcaa143b64adc4456702`.
Consumed result: `outputs/prowl/localizer-content-v2-164a85ed-78aa-4a2e-99bd-33be442a7393`;
receipt SHA-256 `80baf3b1d63e1c8b2097f791f39b074e95d15b897425879f56812d9bfd281009`.
Limited review: `outputs/prowl/localizer-content-v2-pilot-review-20260929`;
receipt SHA-256 `341fd097a43259ed2eca388b5edbc2d469580e06db9467ad14393def4c9efe90`.
Every result receipt member was independently rehashed before review. The review binds each case
record and PNG hash and retains boundary contacts, observations and the test log. The original result's
`visual_review: pending` is historical; this separate append-only review records completion.

## Next

Recommend enabling the **nine remaining standard batches** (02–07 and12–14) with the same caps,
independent frozen requests and per-case review. They contain127 new candidates. Stop and retain
failures; never silently replace cases or automatically retry consumed requests. Then address the
five larger singletons with resource verification. Fourteen unresolved new CT-unit cases and old6350
remain candidates and cannot receive positive physical-geometry qualification without evidence.

At this checkpoint16/148 new candidates have content/review evidence;132 remain (127 standard,
5 large). All176 total candidate identities remain preserved. Next comes evidence completion,
case-specific qualification/issue preservation, immutable cohort publication and a versioned loader/
resource profile before another training run. No new training request or Git publication is pending.
