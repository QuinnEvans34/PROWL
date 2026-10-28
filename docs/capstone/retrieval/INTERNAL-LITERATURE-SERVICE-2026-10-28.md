# Internal literature service integration

Scope: W04-04 availability work while teacher target generation runs. Keep the
existing answer model, exact retrieval, corpus, source checks and 50 GB internal
reserve. No teacher pause, inference, Docker Desktop restart or unrelated container
change. This addresses drive-mount outages, not proven answer-generation latency.

1. Add an explicit internal-storage configuration alongside the preserved external
   configuration. Validate local paths, volume identity, private credentials and
   dedicated database/container identity. Internal mode must not depend on the
   external drive or its 408 GiB allocation; external mode retains that gate.
2. Build a separate internal working database from hash-verified frozen batches.
   Verify complete corpus inventory, then compare public search results with the
   earlier internal benchmark. Preserve the old external data and test database.
3. Connect the existing preparation button and search service to the new profile.
   Keep model loading blocked while the teacher owns the accelerator. Verify wrong
   mounts/configurations fail closed and readiness cannot mistake an old backend
   for the configured one.
4. Exercise search, stop/start of only the new database, health recovery and the
   actual UI Find sources path. Verify startup with external mount checks unavailable
   synthetically; do not unplug the teacher's drive. Inspect UI and preserve results.
5. Record evidence and rollback instructions, update Trello and commit. Stop at a
   failed integrity/resource check; do not switch the application before qualification.

Completion: active UI source search uses the verified internal database, survives
its restart, and preserves teacher ownership. Real single-call summary quality,
full training qualification and independent RAG acceptance remain separate work.

## Results

Completed October28. Active preparation profile is the ignored/private
`infra/retrieval/.env.local-expert.json`; legacy `.env.ingestion.json` is unchanged.
Dedicated container `prowl-literature-internal-db-1`, loopback55435, data at
`outputs/prowl/literature-internal/data`. Original external and benchmark databases
remain stopped and preserved. No Docker Desktop restart; warpaths-neo4j stayed up.

Verified14papers/1179passages,14,341,811database bytes. Full frozen corpus inventory
matches. Eight public queries return identical ordered top-five IDs before and
after restart. Tests:20Python configuration/preparation/service checks and3UI
readiness/plugin tests pass. Internal mode tested without external mount access;
wrong identity/path/project/port and sub50GB reserve rejected. The teacher's drive
was not disconnected as a test.

The verified old search PID53268 was stopped and replaced through the preparation
helper with an explicit internal config. Existing study/general-extract answer
policy retained. Service identity is a digest of the storage configuration, not a
credential value; readiness requires an exact identity match. Actual stop of only
the internal DB made database/search readiness false; Prepare restored both to
true while GPU busy remained true and answer model loaded remained false.

Real headless Research UI: Check status passed; Find sources returned HTTP200,
five actual passages, generation=not_called; Sources rendered correctly and Ask
question stayed disabled after the teacher-busy status check. Inspected screenshot.
Evidence: `outputs/prowl/internal-literature-20261028/` initial.json,
restarted.json, service-recovery.json, ui-response.json and sources.png.
Teacher advanced to723/1333 during work. No live summary quality claim.

## Operation and rollback

Use the existing Prepare AI expert button. It starts the configured existing
container/search service; it does not recreate missing data or restart Docker
Desktop. While teacher owns GPU, it restores search only. Internal corpus data,
encoder and frozen evidence are local; teacher scans/targets remain external.
Back up/rebuild this working database using verified frozen batches, not a copied
live PostgreSQL directory. `qualify_internal_literature.py --load --output NEW_PATH`
is restricted to the dedicated internal profile; omit --load for verification.

Rollback, if required: stop only the verified literature search process and
internal DB; retain both data copies. Preserve the internal config under a new
private filename, then place the unchanged legacy config at the active private
profile path and restart through Prepare. External-drive and Docker mount checks
must pass; do not report rollback readiness before health identity and inventory
checks succeed. Neither old nor new database should be deleted for rollback.

## Remaining CPU work order

1. Exercise the prepared single-call summary's partial/gap/failure/cancellation
   presentation in both Research and Workbench. Reuse current tests; add coverage
   only for demonstrated missing scenarios. Stop when the candidate is ready for
   one bounded real-model window; synthetic success is not answer acceptance.
2. Review full-target admission/qualification against the latest qualified affine
   continuation. Ensure geometry provenance, exact cohort and cumulative budget
   survive the handoff; add only a demonstrated missing connection. No incomplete
   target manifest, GPU qualification or scientific launch while teacher runs.
3. At the authorized GPU window, compare real single-call answers for support,
   completeness, citation quality, refusal and latency, then perform human review.

## Follow-up: honest readiness failures

The UI previously retained its successful readiness message after a later status
failure. It now hides that stale message during checks and after errors, and shows
it again only after recovery. Read-only status requests have a 15-second browser
timeout; explicit preparation retains its longer startup allowance. The last known
GPU-busy restriction remains conservative if a later check fails.

Preparation now diagnoses an existing service on port8016 whose storage identity
differs from the active configuration. It fails with an actionable message rather
than waiting for the generic readiness timeout; it never kills an unknown process.
Synthetic mismatch and UI failure/recovery tests pass:17 Python and4 UI/plugin
tests. Live read-only status confirms storage/database/search/model service ready,
answer model unloaded and GPU busy. Teacher10 continues at725/1333 with advancing
tiles;341 protected repository hashes match. No GPU or teacher changes.
