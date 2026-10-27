# Registered CPU configuration contract — October27

New registered CPU runs validate a dedicated
`offline-workflow-configuration-v1.schema.json` contract before creating invocation
files or calling handlers. This closes the configuration-schema gap for the three
existing adapters: saved-package, case-literature and prepared-inputs. Full pipeline
registry/configuration alignment remains separate; no new stage or dispatch is added.

## Behavior

The contract fixes the version, workflow allowlist, nonnegative integer byte reserve,
allowed sensitivity, registry structure and exact plan/stage fields. Unknown fields,
commands, unsupported resource classes and nonempty undeclared stage configuration
are rejected. The unchanged registry schema is resolved locally; validation performs
no network lookup or dynamic command import.

Semantic validation reconstructs the dependency plan with the existing planner and
compares ordering, parent hashes, derivations and artifact IDs. It then checks exact
stage membership, dependencies and input names against the chosen registry workflow.
A structurally valid or consistently rehashed plan cannot substitute a different
workflow's stages or undeclared inputs.

New resolved configurations carry an explicit version. Prior unversioned records
are accepted only by the read path, validated through a detached versioned view and
never rewritten. Unknown explicit versions still fail. Inspection/recovery and run
summary export validate configuration meaning in addition to existing integrity and
provenance bindings. The live CLI's default50GB reserve is unchanged; tests retain
explicit zero-reserve temporary fixtures.

## Evidence

- **199 CPU regressions passed in18.84s**, including19 new configuration checks.
  The focused49-test run also passed. No earlier failed run in this change.
- New tests reject extra/version/workflow/policy/row/config/derivation/parent/order/
  registry errors, a consistently rehashed undeclared input, and invalid current
  policy before invocation files or callbacks. Legacy reads are nonmutating.
- Actual CLI: plan created no workflow files; first run completed2/2 stages; explicit
  resume reused2/2. Both new configurations validate and lifecycle records are terminal.
- Two actual earlier unversioned CLI runs inspected successfully, with every existing
  file hash unchanged. This is compatibility evidence, not a migration.
- Logs and receipts: `outputs/prowl/workflow-configuration-20261027/` including
  `regression.txt`, `legacy-inspection.json`, CLI output and `teacher-safety.json`.
- Teacher attempt07 remained active at531/1333 with new tile progress; all329
  repository producing pins match. No GPU work, data rebuild, service restart or
  teacher code/recipe modification occurred.

## Remaining W04-01 work

The three ready CPU adapters now have versioned configuration, registry, event and
run-summary contracts. This does not turn their handoffs into the approved entire
imaging/retrieval graph. Remaining integration must bind the owning production
components and receipts, including full target admission and actual executor recovery.
Do not add placeholder training stages or repeatedly rerun completed metadata work
while waiting for teacher targets. The current [G3 review](G3-EVIDENCE-REVIEW-20261027.md)
retains the broader gate as open.
