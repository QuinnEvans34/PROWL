# Orchestration tool selection

**October26 decision:** D-201 selects the repository runner after the isolated Prefect3.9.0
clean-graph trial exceeded the unchanged five-second limit. See [results](TOOL-SELECTION-RESULTS-20261026.md).
The candidate/spike plan below is retained as historical criteria; general G3 remains open.

**October 17 literature implementation checkpoint:** Quinton authorized continued development through
completion-spec Step 3. The [bounded research workflow and rebuild qualification](../retrieval/LITERATURE-WORKFLOW-CLOSURE-2026-10-17.md)
is complete using the existing sequential repository adapter. This scope retains that runner without
a new framework trial/dependency; it does not claim Prefect failed or close general D-201/G3.
Corpus/query identities, storage admission and remaining literature recovery/rebuild checks now pass.
Earlier general implementation-gate statements remain historical for this authorized slice; broader
imaging orchestration and the general tool-selection trial remain separate.

**Status:** Approved candidate plan; spike not run and D-201 remains open  
**Version:** 0.1 approved design  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/04-workflow-orchestration.md`](../implementation/04-workflow-orchestration.md)

## Decision to make

Select the smallest local orchestration tool that improves retries, state visibility, and workflow
composition without replacing PROWL artifact identity, requiring a managed service, or becoming a
second infrastructure project.

## Candidate disposition

| Candidate | Disposition | Reason |
|---|---|---|
| Prefect 3, direct local execution with optional self-hosted local UI | Time-boxed preferred candidate | Python-native tasks/flows provide dependencies, state, retries, timeouts, logging, and optional local visibility while existing functions/CLIs can remain component boundaries |
| Small PROWL repository runner | Required fallback | Full control and minimum dependencies; must implement topological execution and operator behavior against the same registry/events/validators |
| Apache Airflow | Rejected; no spike | Quinton does not want Airflow, and its scheduler/database/application surface is disproportionate to a single-user local research workstation |
| Prefect Cloud or another managed control plane | Rejected | Medical data and machine paths remain local; correctness cannot depend on an external service |

Official references used for the planning assessment:

- Prefect tasks: <https://docs.prefect.io/v3/concepts/tasks>
- Prefect caching behavior: <https://docs.prefect.io/v3/concepts/caching>
- Prefect local self-hosted server: <https://docs.prefect.io/v3/how-to-guides/self-hosted/server-cli>
- Airflow installation/operational surface: <https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html>

These links describe tool capability. PROWL tests, not vendor documentation, decide whether the
candidate satisfies this project's contract.

## Non-negotiable selection criteria

The selected approach must:

1. run locally on the capstone macOS/Python environment without a cloud account;
2. execute without cloud credentials or a manually maintained server; temporary local services are
   acceptable under the September 20 clarification only with tested lifecycle and known state locations;
3. call stable Python functions or CLIs without moving scientific logic into decorators;
4. pass artifact references rather than large arrays/models through task return storage;
5. let PROWL derivation hashes and validators decide reuse;
6. preserve every failed/retried attempt in the PROWL event contract;
7. support bounded retry, cooperative cancellation, and checkpoint-aware recovery;
8. remain inspectable after its own UI/database state is unavailable;
9. fail before compute on invalid cohorts, roots, configuration, or artifact hashes;
10. add proportionate dependency, start-up, maintenance, and learning cost.

## Four-hour Prefect spike

### Fixture graph

```text
validate_fixture_source
        |
        v
build_fixture_manifest
        |
        v
summarize_fixture_manifest
```

Each stage writes a tiny schema-valid artifact through the tool-neutral publisher. The second stage
supports deterministic failure injection after partial write and before completion publication.

### Required trials

| Trial | Evidence required |
|---|---|
| Clean execution | Ordered task/stage state, PROWL events, logs, and three valid artifacts |
| Identical rerun | All three outputs independently validate and record `reused`; no component executes |
| Mid-write process failure | Partial cannot be resolved as an artifact; failure and quarantine evidence persist |
| Recovery | New linked run reuses stage one and resumes at stage two |
| Relevant config change | Stage two and descendant derive new IDs; unaffected stage one remains reusable |
| Missing root | Failure occurs in preflight before stage execution |
| Local state unavailable | Prior artifacts remain inspectable and reusable from PROWL records |
| No managed server/cloud | Direct local run needs no cloud credentials or manually maintained server; any temporary local endpoint/state is documented, lifecycle-tested, and scientific payloads stay local |
| Optional local UI | If tested, it exposes useful state without receiving medical payloads |
| Test harness | Unit/integration tests do not require an always-running server |

### Acceptance bar

Select Prefect only if all non-negotiable trials pass within four focused hours and:

- installation/import does not break the chosen PyTorch, MONAI, MLflow, FastAPI, or test environment;
- wrappers remain thin enough to run through the fallback runner unchanged;
- framework overhead is negligible beside real work and under five seconds for the full tiny graph
  after interpreter start, excluding an optional UI server;
- local files/SQLite used by Prefect can be redirected outside source and scientific artifact
  directories;
- Prefect's cache/result behavior is either disabled for scientific stages or demonstrably unable to
  bypass PROWL validation;
- the operator can understand run, failure, retry, reuse, and recovery from PROWL evidence alone.

Any failed non-negotiable criterion rejects Prefect for the capstone. A fix may be attempted only
inside the original four-hour budget. The result is recorded even if the candidate is rejected.

## Fallback runner boundary

The fallback is not a second design. It implements the frozen interfaces already used by the spike:

- load and validate registry/config;
- select a named workflow and topologically sort it;
- resolve inputs and derivation hashes;
- run preflights and independent reuse validation;
- acquire/release locks;
- execute one stage at a time by default;
- append events and atomically update the run summary;
- classify retry/cancel/failure and create a linked recovery run;
- publish only validated artifacts.

It does not implement a web UI, cron scheduler, distributed workers, remote agents, or a general
workflow language.

## Decision record after spike

Quinton accepted the walkthrough and reaffirmed this selection approach on 2026-09-20.
Prefect is still a candidate, not a final selection. The four hours cover tool evaluation, not
building all tool-neutral safety infrastructure. Verify that its execution visibility and reduced
coordination work justify its dependency/state overhead. No installation or coding was authorized
by the documentation-update request.

D-201 must include:

- candidate/version and exact environment;
- start/end time and whether the four-hour limit was respected;
- pass/fail result for every trial and criterion;
- dependency/install impact;
- artifact/event/recovery evidence IDs;
- measured overhead and operator observations;
- selected tool, fallback status, limitations, and migration consequence.
