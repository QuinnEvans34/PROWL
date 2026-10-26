# Week 4 CPU work specification

October26,2026. Companion to [the weekly plan](WEEK-04-WORK-PLAN.md).
Purpose: deliver useful workflow recovery code while teacher-target generation
occupies the Mac accelerator. This document specifies the next implementation;
it does not claim it has been built or qualified.

## Recommended implementation

Build a small, tool-neutral dependency/recovery layer and a bounded case-evidence
package smoke workflow. Use the existing artifact publisher and component validators.
Do not build a scheduler, a new labeling application, or a replacement training runner.

Existing reusable code:

- `src/operations/artifact_store.py`: checked publication, independent receipt
  identity, root checks, capacity admission and writer locking.
- `src/retrieval/research_workflow.py`: literature-specific attempts, event-chain
  validation and explicit recovery. Preserve its public behavior; it is not a
  general imaging DAG.
- `src/review/store.py`: durable review decisions against exact package identity.
- Existing native-package validators and synthetic fixtures: reuse their actual
  contracts rather than inventing another scientific output format.

Before implementation, inspect the active teacher request's exact producing pins.
Prefer new modules/tests; do not modify any pinned dependency. Imports are allowed
only where they do not start work or mutate running-job state.

## Code blocks and acceptance

| Block | Proposed code | Observable acceptance / stop |
| --- | --- | --- |
| 1. Dependency plan | New `src/operations/workflow_plan_v1.py` with stage IDs, dependency IDs, explicit input/producer/configuration identities and deterministic ordering. Pure functions first. | Reject cycles, missing dependencies, duplicate IDs and undeclared inputs; show why a stage must run or may be reused. Planning creates no run/output files. |
| 2. Execution and recovery | New `src/operations/workflow_execution_v1.py`, using existing publication and validation contracts; append-only attempts, explicit resume lineage, no automatic retry. | Failed or interrupted stage blocks descendants; verified upstream output is reused on explicit resume. Tampered output cannot be reused. Changed relevant inputs/configuration invalidate only affected descendants. Original attempts remain intact. |
| 3. Connected smoke workflow | New `scripts/diagnostics/qualify_case_evidence_workflow.py`: synthetic native package validation → synthetic cited-evidence validation → package assembly/validation, using owning validators. Review decisions remain human actions, not automatic acceptance. | Actual validators consume the outputs. Two identical runs reuse valid outputs; injected mid-write process termination leaves no consumable partial; resume finishes the same logical package. No model, database or real CT required. |
| 4. Operator view | CLI `plan`, `run`, `resume`, `inspect` and `status` for this bounded fixture workflow. JSON plus concise human-readable stage summaries. | Shows exact failed stage, reason, reused stages and next permitted action. Status/inspect are read-only; no arbitrary shell execution from configuration. Missing roots/capacity/lock conflicts stop before stage execution. |

Proposed filenames may be adjusted to existing repository conventions after inspection.
Keep tests alongside the new modules in dedicated workflow test files. Use subprocess
tests for interruption and concurrent writers; mocks alone cannot prove durability.
Successful process exit is insufficient: every reusable output needs its owning
validator and recorded identity. Separate exact-byte corruption from a new legitimate
configuration; never overwrite old outputs to make reuse pass.

## Test and resource boundaries

Use invented inputs, temporary local directories, bounded subprocess timeouts and
small file budgets. Run focused tests first, then the existing artifact/research/review
regressions affected by imports or adapters. Verify workers are reaped. Do not invoke
teacher/student inference, Ollama, training, corpus rebuilding or live service restarts.
Do not read private evaluation material or scan arrays for this qualification.

If the publisher cannot be reused safely without changing active pins, stop that
adapter and finish pure planning/tests; report the exact dependency. Do not fork the
publisher into a second competing implementation. A substantive failed gate is a
result to preserve, not permission for an unbounded rewrite.

## What this closes, and what it does not

This supplies bounded cross-stage recovery evidence toward W04-01. Synthetic success
does not qualify real imaging/training integration or close all of G3. The original
Plan04 Prefect-first selection trial/D-201 remains unresolved. These tool-neutral
contracts and tests should serve either adapter; do not silently declare the repository
runner selected, claim Prefect failed, or install a framework into the training environment.
Report the selection decision and remaining production adapters separately at handoff.

AI benefit is reliable evidence packaging and actionable failure reporting. New answer
generation, scan-normality comparisons and latency claims require their own later live
checks. Reference comparisons and training-feedback commitments remain in the weekly plan.

## Autonomous execution order and handoff

Implement blocks1–4 sequentially, committing coherent passing increments and updating
W04-01. Continue through bounded verification without waiting for routine design choices.
Pause only for a missing required input, a frozen-code conflict, or a decision that changes
scientific scope. Do not stop merely because one test fails; diagnose within this scope.

Finish with one short results report: working commands, evidence paths, tests, injected
failure/resume result, preserved limitations and remaining Week4 gates. Then Quinton can
review a small demonstration rather than a new infrastructure framework. No autonomous
schedule or promise of a fixed number of hours is created by this specification.

## Implementation handoff — October26

The user explicitly authorized autonomous implementation after this specification. All four bounded
blocks are delivered and tested; see [results and operator commands](../orchestration/CPU-WORKFLOW-RECOVERY-20261026.md).
98 focused/existing regressions pass, including real subprocess interruption and recovery. The shipped
CLI is synthetic-only; production adapters and D-201/G3 remain separate gates.
