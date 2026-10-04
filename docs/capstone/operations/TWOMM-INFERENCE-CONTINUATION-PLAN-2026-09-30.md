# D-303 — remaining145 inference and full153 reconciliation

Quinton requested continuation after the passing D-302 pilot. Implement a separate versioned
continuation runner/request; preserve the eight-case runner and consumed pilot unchanged. Bind the
passing pilot receipt `5764b267a2f2cfef95e327804364b5b4228f51c2359274e1c4b18c0e54f3d76f`,
D-300 full cache completion and binding, fresh source/environment, and the exact complement of the
pilot in original optimizer/evaluator arrays. Order is optimizer then evaluator, original index order.
Expected remaining107train/38validation; no refill, eligibility change or source reads.

Same zero-update144³ inference, native-grid exports, unchanged model checks and independently
restored step0 checkpoint as the pilot. Initial weights must match between the two batches.
Budget:20minutes shared across worker/recovery/final verification;16GiB RSS/driver,4GiB local output,
AC and100GiB internal free floor. Independent stores retain20GiB total backup cap and1GiB new bytes
per domain, shared across stages. No automatic deletion, fallback, restart or training extension.

Test exact complement/counts/roles, missing/duplicate/reordered cases, pilot ancestry/hash changes,
old-schema refusal, new request consumption, resource limits, interruption cleanup and full153
reconciliation. Run the full native suite before freezing. Only then prepare and execute one request.

Recheck all completion member hashes and all153 export geometries after the run. Preserve all prior
case observations and23 held candidates. Record measured times/memory, remaining native-reference
measurement and executor needs, and an actionable next training packet. These initialized predictions
qualify runtime/geometry, not learning, accuracy or generalization. No training request is launched.
