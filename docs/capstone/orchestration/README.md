# PROWL workflow orchestration

**Status:** Walkthrough accepted September 20; coding authorization pending; tool spike not run  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/04-workflow-orchestration.md`](../implementation/04-workflow-orchestration.md)

**October17 bounded research slice:** Quinton authorized and received the explicit local
retrieve/select/validate/save adapter with UI stage status and linked recovery. See
[implementation/results](../retrieval/EXPERT-WORKFLOW-2026-10-17.md). This is scoped authorization
and evidence for that research slice; the broader framework selection and G3 remain open.
The older coding-authorization status above/below applies to that broader Plan04 scope.

This directory defines orchestration behavior independently from Prefect or any fallback runner.
The DAG coordinates scientific components, but artifact validity remains controlled by PROWL's own
schemas, hashes, lineage, and completion records.

## Documents

| Document | Purpose | Status |
|---|---|---|
| [`STAGE-REGISTRY.md`](STAGE-REGISTRY.md) | Named workflows, stage dependencies, owners, inputs/outputs, retry and resource classes | Approved design baseline |
| [`STATE-AND-RECOVERY.md`](STATE-AND-RECOVERY.md) | State authority, events, idempotency, atomic publication, interruption, retry, locks, and resume | Approved design baseline |
| [`TOOL-SELECTION.md`](TOOL-SELECTION.md) | Prefect-vs-runner selection bar and bounded spike; Airflow exclusion | Approved candidate plan; spike not run |

Quinton accepted the walkthrough on September 20. Explicit implementation authorization remains
required before Plan 04 code or installation. Prefect-first evaluation is approved, including tested
temporary local machinery, but D-201 remains open until the spike. See the governing plan's
**Required explanation gate**.

## Governing rules

1. A workflow tool coordinates; it does not define scientific truth.
2. Stages exchange artifact references, not large scientific objects.
3. Published artifacts are reusable only after independent PROWL validation.
4. Every attempt and state transition is preserved even when a later retry succeeds.
5. Imaging, literature, integration, and release workflows are independently runnable.
6. No medical data or source path is sent to Prefect Cloud or another managed control plane.
7. Dry-run planning precedes expensive or destructive work.
8. Apache Airflow is outside the capstone design.

## Machine-readable artifacts planned during implementation

- revised `docs/capstone/contracts/run-manifest.schema.json` and example;
- `docs/capstone/contracts/workflow-event.schema.json` and example;
- stage-registry and workflow-configuration schemas/examples;
- synthetic failure/recovery fixtures under `tests/fixtures/orchestration/`;
- G3 evidence under the versioned capstone evidence layout selected in Plan 10.
