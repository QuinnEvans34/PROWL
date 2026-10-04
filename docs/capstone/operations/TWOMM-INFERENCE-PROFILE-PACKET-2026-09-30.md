# Next packet — real-cache 144³ inference and native export readiness

Prepared after D-301 synthetic session/recovery. This is an implementation packet, not a frozen
executable request or training launch. Synthetic recovery passed; real full-volume readiness remains.

## Inputs and exact first cases

Use the D-300 final cache only:
`outputs/prowl/twomm-cache-build-80569d7d-94e0-4c52-91ba-1a128dd076ae/cache`.
Completion SHA-256: `b61897ed3176fecd9d8ca143285d9700699c1557537ba15b966a487134342bf7`.
Binding: `outputs/prowl/twomm-cache-readiness-20260930/proposed-binding.json`,
SHA-256 `ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d`.
Final build receipt: `6e287408e137d13d5bb240c7e8f0e6823eda98ed0bedac2a57419f9b6c70c5bc`.
The cache carries all113 train/40 development-validation descriptors, transforms and limitations;
all23 held candidates remain outside. No selection/refill or role changes.

Pilot: the same eight cache-build edge cases, explicitly frozen in this order. Shapes are XYZ;
indices are zero-based in their original role arrays. Full member IDs use `pants:study:PanTS_` plus
an eight-digit number. Keep that full identity in machine records.

| Case | Role / index | Processed shape | Native source shape |
|---|---|---|---|
|6110|optimizer /76|207×162×96|276×215×91|
|2727|evaluator /5|166×156×96|221×208×111|
|5190|optimizer /61|249×205×112|508×418×278|
|7957|optimizer /102|221×193×344|512×446×275|
|6822|optimizer /84|246×152×302|492×303×604|
|8937|optimizer /110|216×196×196|512×464×391|
|6186|evaluator /26|256×182×182|512×363×362|
|1935|optimizer /23|203×177×170|512×447×340|

Together these exercise tiny references, extra144³ padding, the largest processed grid, and large
native grids. After a passing reviewed pilot, a separate request covers exactly the remaining145
(107train/38validation). Accounting must reconcile153 unique original members with zero substitutions.

## Implementation and guards

1. Add a separate supervisor/worker. Requests pin source/environment bytes, D-301 session version,
   adapter configuration, exact cache completion and binding, ordered role/index/member triples,
   outputs and limits. Exclusive consumed marker before inference; refuse request reuse or drift.
   Retain every failed/interrupted attempt; no automatic restart or silent continuation.
2. Use `DiskRoleCache` and `Session.predict_cache`. Identity purpose is `qualified-cache-inference`,
   deviceMPS, seed42, 144³ patch, balanced objective and diagnostic max_steps4 (no updates).
   Instantiate fresh weights; no previous model reuse. All cache reads are verified, one case at a time.
   Cache construction is already complete; do not reopen CTs or source annotations.
3. Use CPU stitching, overlap0.25, constant blending, float32, workers0/threads2, fallback0. Remove
   extra patch padding before V4 restoration. Validate CPU finite two-class probabilities on the
   exact processed grid. Compare model digest before/after every case; require step0 and empty
   optimizer state throughout. No training method is enabled.
4. Restore a discrete single-channel argmax mask with the retained V4 transform. Export uint8 NIfTI
   on exact source shape/affine; reopen and check binary values, shape/affine and serialized hash.
   Test asymmetric padding, anisotropic source geometry and label-independent inference on fixtures.
   Record cache-load, inference, restoration and export times separately, shapes, output bytes,
   foreground counts, sampled MPS driver/live memory and supervisor process RSS.
5. Use a shared MPS lock, AC requirement and100GiB internal-free floor. Pilot cap:20minutes,
   16GiB process RSS/driver,1GiB new output. Continuation provisional cap:20minutes,16GiB,4GiB output;
   reevaluate using measured pilot before freezing continuation. Reserve checkpoint/backup headroom
   before running; preserve the20GiB independent-backup cap and1GiB per-domain new-artifact budget.
6. Publish a step0 checkpoint bound to this actual cache. Back up independently and restore in a
   fresh process with primary reads prohibited. Compare a fixed synthetic probe (no cache dependency
   during recovery), exact weights and identity. D-301 proves nonzero synthetic optimizer recovery;
   this additional check proves production cache binding survives the same path.
7. Completion is written last after output and aggregate verification; no passing receipt on failure.
   Add corruption, wrong-role/index/member, completion drift, consumed request, resource stop,
   interrupted worker and export-geometry tests before real execution.

## Evidence limits and path to launch

This profiles random initialized predictions, not model quality. A native-grid prediction export does
not provide a native-reference accuracy measurement: this cache stores processed targets only. A
training evaluation packet must explicitly provide qualified native references through retained
verified artifacts or a new bounded source-read capability; never score a resampled target as the
original native reference. No unplanned source read is authorized by this packet.

Passing full153 inference, real-bound step0 recovery, exact aggregate resource accounting and preserved
case failures will support the training executor/launch plan. That plan still needs finite exposure,
checkpoint/evaluation schedule, native-reference path, interruption behavior and before/after coverage
metrics. Uniform2mm/144³ remains a candidate recipe until recorded in that exact experiment request.
The development-validation set is exposed; no sealed-test/generalization or promotion claim.
