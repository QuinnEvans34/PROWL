# D-304 — native-reference scoring implementation and first full baseline

Quinton requested continuation after full153 inference readiness. Implement the target-only reader
and96M native metrics from the training completion packet, test with synthetic references, then freeze
an8-case scoring pilot and145-case continuation. Their requests are separately single-use and bind
D-302/D-303 prediction artifacts, unchanged initial weights, cache/cohort/recipe, new target-only
capability, current source/environment and exact membership. No CT rereads, model forwards or updates.

The capability permits one153-label pass in8+145 disjoint batches:21,942,279 compressed bytes and
4,398,868,031 expanded bytes. Root/volume, published bundle/qualification, target hash/role/geometry,
and exact approved binary decoder remain verified. All original holds/observations remain. New file
read budgets forbid duplicate labels and CT access through this reader. Original sources stay untouched.

Each job:20minutes,16GiB process RSS,128MiB new output,AC and100GiB internal-free floor. No new
checkpoints or backup-domain writes are needed; results are reproducible metric records referencing
the independently preserved input/run evidence. Pilot measured costs must pass before continuation.
Request/batch and worker-stage markers prevent replay; failure retains controls/logs, never completion.

Synthetic checks include96M grids, dense predictions over4M voxels, empty and fragmented predictions,
tiny boundary references, signed/permuted anisotropic geometry, exact confusion/box counts, bad arrays,
wrong role/decoder/source/geometry, and target-only reads with CT fixture deliberately absent.
Native metrics use slab counts/reductions, with acquired-scan crop denominator and10mm rounded margins.
Optional connected-component details are not computed; no foreground-density cutoff drops a case.

Retain all per-case metrics and explicit training-fit versus development-validation summaries. Empty
prediction coverage contributes zero to aggregate coverage rather than disappearing. Results describe
the initialized model only; they neither certify contours nor prove trained performance. No threshold
selection, cohort filtering, checkpoint warm start, real training or promotion. After this slice, the
remaining task is the separate training executor and its synthetic transaction/recovery rehearsal.
