# First explicit research workflow — October 17, 2026

**Follow-up:** The real single-question integration and same-ID saved-result reuse now pass.
See [live verification](WORKFLOW-LIVE-CHECK-2026-10-17.md) for cleanup, recovery, route integration,
current service state and the remaining relevance limitation. Earlier not-started statements below
describe the initial implementation checkpoint.

Quinton approved the retrieve → select → validate → save slice after the bounded reasoning diagnostic.
This delivers the local research adapter and visible recovery behavior. It does not close Plan 04/G3,
select Prefect versus another framework, implement the full imaging DAG, or qualify answer relevance.
The original `verified-extracts-v2` generator and its limits remain unchanged. The new panel is separate
from the existing answer/search panels; old saved responses and endpoints remain readable.

## Behavior

- **Retrieve:** save up to five validated passage records from the existing guided query function.
- **Select:** call the existing pinned local generator once and retain its result, including a rejected
  generation. The generator's existing checks remain; the next stage independently verifies publication.
- **Validate:** check exact quotations against the frozen passages. A `generation_rejected` result fails
  this stage, even though its fallback answer has an empty insufficient-evidence shape. A valid model
  abstention, or empty retrieval with no model call, may complete normally.
- **Save:** use the existing immutable `ResearchStore` response writer and verify its result against
  the exact stage artifacts. Only a completed workflow exposes an answer/download through the endpoint.

The UI displays waiting/running/complete/reused/failed states and polls while a request executes.
A failed generation explicitly says it does not establish missing source evidence. An unknown network
outcome keeps the same request ID; checking it does not launch another generation. Only an explicit
**Retry failed stage** action creates a new UUID with `resume_of` pointing to the old attempt.
A valid insufficient-evidence answer is completed, not presented as a generation failure.

Recovery preserves the old run and copies independently verified successful ancestors into the new
run with their source references. A failed/rejected selection is generated again; a save failure can
reuse retrieval, selection and validation. Changed question or producer configuration refuses reuse.
Reuse means the **original search snapshot**, not a fresh query against today's database contents.
The current adapter conservatively requires all binding fields/code identities to match; it does not
attempt reuse across code migrations or changed model policies.

## Records, locking and scope

Default root: `outputs/prowl/research-workflow/` (ignored local artifacts).

```text
worker.lock
<run-uuid>/request.json
<run-uuid>/owner.lock
<run-uuid>/event-0001.json ... event-0008.json
<run-uuid>/retrieve.json
<run-uuid>/select.json
<run-uuid>/validate.json
<run-uuid>/save.json
responses/<run-uuid>.json
```

Each JSON artifact is created once, fsynced and atomically published using the existing writer.
Events bind their sequence, previous hash, manifest, stage state and artifact hash. Artifacts bind the
manifest and ordered upstream hashes; source rows and answer postconditions are revalidated on reads
and recovery. The summary is reconstructed from these records, never trusted as a mutable cache.
Rejected selection evidence remains local; public failure responses contain bounded error categories,
not raw exception messages. This is a versioned `prowl-research-workflow-v1` adapter format, separate
from the future general run/event contracts.

Nonblocking POSIX file locks serialize this workflow directory across threads/processes. They release
on process death; a run without a terminal stage or live owner is reported as interrupted. Recovery
requires a new linked run. There is no automatic retry, cancellation endpoint, cleanup, model sweep,
full-corpus selection or training. These locks do not coordinate unrelated services or provide a
system-wide GPU scheduler. This slice targets the current macOS/Linux local environment.

## Local service

After the existing drive/database/encoder prerequisites are available, start explicitly from the repo:

```sh
.venv-retrieval/bin/python scripts/serve_research_workflow.py
```

Loopback port8015; Vite5180 proxies `/research-workflow`. The UI panel is **Research evidence workflow**.
Routes: POST `/research-workflow/runs` with guided `request_id`/`question_id` and optional `resume_of`;
GET `/research-workflow/runs/<uuid>` for status/history; GET `/research-workflow/responses/<uuid>` for
completed answers; GET `/research-workflow/health` for service identity. Same Origin allowlist, small
JSON limit and guided-question boundary as existing services. Health is not a database/model readiness
probe. Starting the service loads the configured encoder but does not query or generate until requested.
Existing old answer8014 and retrieval8013 services are not prerequisites for this new adapter.

This turn did **not** start the production workflow service or restore the database/demo. All execution
checks below use synthetic passages and scripted local generation results; no actual model API, corpus
write, new download, patient arrays or human-hours credit. Live integration remains the next check.

## Verification

- 18 workflow tests: rejected output versus valid abstention, same-ID idempotency, linked recovery,
  preserved history, corrupt/rehashed artifacts, changed configuration, concurrent instances, abrupt
  process exit, interrupted publication, save failure reuse, invalid quotation and model identity.
- 5 new real HTTP tests: failure/recovery/download plus Origin, unknown route, extra field and conflict
  refusal; 6 unchanged shared HTTP tests also pass. All use ephemeral loopback ports.
- 16 existing guided-store/generator checks pass. Total: **45 distinct Python checks passed**.
- **47 distinct UI checks passed**: initial full suite46, then seven workflow checks after adding the
  case-switch/late-response regression (six overlap). No live network in component tests.
- Actual-browser synthetic HTTP scenario passed, then passed again after the missing-year display and
  screenshot-layout adjustment. It observes running selection, rejected validation, linked retry,
  retrieval reuse, original history unchanged, idempotent POST, downloaded response, completed
  abstention and reload preservation. Zero browser page errors. Final screenshot visually inspected.
- Production build passes on repository Node24.21.0; existing large-chunk advisory remains.

The initial shell selected Node20, which could not start the installed Vitest/jsdom workers; no tests
ran in that invocation. Selecting the existing pinned Node24 resolved it without dependency changes.
Sandbox loopback bind refusals affected11 HTTP setups; the native rerun passed all11. These environment
failures are not counted as passing tests or silently omitted.

Final browser artifacts: `outputs/prowl/testing/workflow-fixtures/b740bd2b-aa99-4211-8c1f-2ea86f0c79fd/`.
Failed run3524eaf9-a218-457f-a4f7-5570528fb099 → recovered run1ced5eba-6a1c-4dab-9790-0d6ce1bb2d04;
separate valid abstentionfcb04701-3c95-4e56-86c4-4da4bbb8e0a7. Screenshot:
`outputs/prowl/testing/workflow-browser/recovery-actual-HTTP-workf-6f3e3-val-and-preserves-both-runs/workflow-recovery.png`.
The browser fixture server is test-only and was stopped by its harness. No test response is a literature
quality result; the prior1/4 reasoning diagnostic and5/7 best experimental clean-answer result remain
unchanged historical evidence.

## Next

Verify the new adapter once with the existing local pgvector collection and pinned8B policy, including
saved-result reuse. Keep that integration check separate from semantic-quality acceptance. Then use
the stage records to address the observed evidence-selection errors with explicit case-level criteria;
do not infer that a completed workflow means a complete or relevant answer.
