# W04-01 resource and record checks — October 27

The bounded CPU workflow passes 87 focused regressions. This closes the checks
below; W04-01 and the broader G3 acceptance gate remain in progress.

## Demonstrated issue and repair

Previously, a hash-consistent run could use an unsupported schema version, extra
fields or an invalid recovery parent. Hash-consistent completion events could
contain contradictory failure fields or a non-hex receipt hash. Integrity hashes
alone did not reject these invalid contracts.

`workflow_execution_v1.py` now checks the exact `workflow-run-v1` envelope and
state-specific event fields before reconstructing dependencies and inspecting the
event chain. Recovery parents require canonical UUIDs; output references require
hex hashes. Capacity configuration requires nonnegative integer bytes (rejecting
booleans, strings, negative values and NaN). Existing valid v1 records retain their
format; no migration or rewriting of old attempts occurs. Adapter producer hashes
already include this executor, so new work derives new identities after this edit.

## Qualification matrix

| Boundary | Evidence |
| --- | --- |
| Unsupported run version/extra fields/invalid recovery parent | Rejected by inspect and recovery, with no handler called |
| Extra event fields, contradictory completion/error, non-hex receipt | Rejected despite recomputed integrity hashes |
| Insufficient capacity before execution | Existing test rejects before creating run files |
| Capacity disappears after a handler returns | No publication or downstream callback; attempt remains incomplete if even failure journaling cannot be admitted |
| Output exceeds 8 MiB | Failed stage retained, no published output or descendant |
| Root absent/replaced/symlinked | Existing root checks reject |
| Writer conflict and process interruption | Real synthetic subprocess tests pass; child cleanup and explicit recovery verified |
| Saved-package and literature boundaries | Existing integrity, capture, rights, citation, runtime and selective-reuse checks pass |

All tests use invented data and temporary directories. Disk exhaustion is injected
through filesystem-capacity observations, not by filling the user's disk. Test-only
zero reserves are not a change to the live 50 GB policy.

Command (Node 24 first on PATH, repository root):

```sh
PYTHONPATH=.:tests .venv-retrieval/bin/python -m pytest tests/test_workflow_resource_schema_v1.py tests/test_workflow_execution_v1.py tests/test_workflow_plan_v1.py tests/test_case_evidence_workflow_v1.py tests/test_saved_package_workflow_v1.py tests/test_case_literature_workflow_v1.py tests/test_artifact_store.py tests/test_workflow_service_admission.py -q
```

Result: **87 passed in 6.96 seconds**. Logs are retained under
`outputs/prowl/workflow-resource-schema-20261027/`. The initial baseline had ten
demonstrated validation failures and a flawed capacity test that changed the
executor's configuration after constructing its publisher. That fixture was
corrected to simulate actual free-space loss; original baseline/focused logs remain.

Teacher safety: all 328 repository producing pins in continuation06 matched;
edited executor/test files are not pinned. Teacher supervisor13779 and worker15917
remained active, with514 completed targets and the next case advancing25→50tiles.
No model/data payload integrity claim follows from this repository-pin check.
An initial overbroad hash inspection was interrupted and reaped, then narrowed to
repository files; no teacher process was interrupted. No GPU, model, service restart,
cohort change, training launch or producing-pin edit was made.

## Remaining G3 requirements

These are exact runtime record checks for the bounded runner, not completion of
the proposal's entire versioned run-manifest/stage-registry/configuration schema
integration. The runner accepts trusted registered CPU callbacks; it does not
supervise arbitrary callback memory/time or qualify accelerator work. Keep the
teacher's separate supervisor and GPU ownership mechanism authoritative.

Next: map the existing production stage registry and run-manifest contracts to
this bounded runner before adding training dispatch. Accelerator admission,
cancellation, stale-owner behavior and real full-cohort executor qualification
remain separate gates. Do not mark G3 complete based on synthetic CPU success.
