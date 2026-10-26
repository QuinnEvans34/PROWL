# CPU workflow recovery — October26,2026

The user explicitly authorized implementing the [bounded CPU work specification](../weeks/WEEK-04-CPU-WORK-SPEC.md)
and committing through completion. The tool-neutral implementation is delivered; this is scoped
Plan04 coding authorization, not a declaration that D-201 or the complete G3 gate has passed.

## Delivered

- Pure deterministic dependency plans reject duplicate/missing stages, cycles and missing producer
  or input hashes. Each stage binds its relevant configuration, parents and producer identity.
- Explicit run/resume creates immutable attempts. Existing artifact publication and owning validators
  govern completion; no scheduler, arbitrary shell command dispatcher or automatic retry was added.
- Reuse independently validates the saved receipt, file inventory/hashes and owning semantic validator.
  Corruption fails closed; configuration changes create new identities without overwriting history.
- Root identity/capacity admission, a process-owned writer lock, atomic exclusive event publication,
  bounded reads and preserved partial artifacts protect this local cooperative-writer workflow.
- The invented case/evidence smoke uses actual ReviewStore manifest validation, tiny native NIfTI
  arrays, exact-source span resolution and an explicitly synthetic bundle. It records no reviewer
  acceptance and performs no model inference or real-source retrieval.

Code: `workflow_plan_v1.py`, `workflow_execution_v1.py`, `case_evidence_workflow_v1.py` under
`src/operations/`; CLI `scripts/diagnostics/qualify_case_evidence_workflow.py`.

## Verification

98 tests passed in2.57s, covering the new planner/executor/smoke, existing artifact store,
literature workflow/boundaries and review store. Two existing FastAPI/Starlette deprecation warnings
remain. No GPU/model/database calls, protected-evaluation reads or live-service restarts were used.

Subprocess tests cover:

1. Kill a worker after evidence bytes are written but before publication. A concurrent writer is
   rejected; the killed process is waited/reaped. Hidden partial output is not consumable.
2. Fail persisted-output validation. The failed attempt and partial files remain preserved.
3. Exit after artifact publication but before the workflow completion event. Explicit recovery
   re-executes that incomplete stage and the publisher verifies identical output/metadata before reuse.

All three recover with native reused, evidence completed and bundle completed. The original run
records remain unchanged. Additional checks reject changed package bytes, mismatched citations,
wrong/replaced roots, malformed graphs, missing registry entries and insufficient capacity.

Standalone CLI evidence: `outputs/prowl/week4-workflow-recovery-20261026/summary.json` and adjacent
stdout/stderr records. The initial plan created no files. First run completed; an explicit identical
continuation reused all3 stages. Changing evidence version preserved native and rebuilt evidence/bundle.
Read-only inspection matched the saved result. This ignored evidence contains invented data only.

Passing increments: `65ea05a` (planner), `d60b863` (executor), `8731502` (connected smoke/interruption).

## Operator commands

Use an existing, dedicated directory for synthetic evidence. The CLI enforces the50GB free-space
reserve. Never point it at a live teacher or training output directory.

```sh
mkdir -p outputs/prowl/my-workflow-smoke
.venv-retrieval/bin/python scripts/diagnostics/qualify_case_evidence_workflow.py plan --root outputs/prowl/my-workflow-smoke
.venv-retrieval/bin/python scripts/diagnostics/qualify_case_evidence_workflow.py run --root outputs/prowl/my-workflow-smoke
```

The command prints the run UUID. Inspect or continue it explicitly:

```sh
.venv-retrieval/bin/python scripts/diagnostics/qualify_case_evidence_workflow.py inspect --root outputs/prowl/my-workflow-smoke --run-id UUID
.venv-retrieval/bin/python scripts/diagnostics/qualify_case_evidence_workflow.py status --root outputs/prowl/my-workflow-smoke --run-id UUID
.venv-retrieval/bin/python scripts/diagnostics/qualify_case_evidence_workflow.py resume --root outputs/prowl/my-workflow-smoke --resume-of UUID
```

Add `--json` for machine-readable output. `plan --resume-of UUID` verifies prospective reuse without
writing. `--evidence-version 2` demonstrates selective invalidation. `incomplete` is recorded
workflow state, not a process-liveness verdict. Status/inspect check record integrity; `plan` with a
parent and `resume` additionally validate artifacts. Inspect a failed attempt before resuming.
A corrupt event/receipt is an explicit blocker, not a license to edit or discard history.

## Scope and remaining gates

This is a POSIX, single-host, cooperating-writer executor with registered trusted callbacks and a
synthetic-only shipped CLI. It is not a general sandbox, Windows executor, real imaging orchestrator,
training launcher or automatic model promoter. Callbacks must declare correct producer/input hashes;
the Python layer cannot prove arbitrary callback purity. ReviewStore's manifest validator is reused
without invoking its storage constructor; this adapter writes no review decisions.

The reusable artifact publisher remains unchanged. All2927 active teacher request pins matched before
implementation; new implementation files are additive. Training code, outputs, budgets, live services
and process ownership were not changed. No claim about current teacher completion follows this check.

Remaining W04-01/G3 work: explicitly resolve D-201's tool-selection trial, qualify production adapters
and their root/cohort/resource boundaries, and demonstrate actual imaging/literature integration.
Do not equate this synthetic package with the broader approved case-package contract. Existing AI
answer quality, independent evaluation, measurement reliability and full KD readiness remain separate.
