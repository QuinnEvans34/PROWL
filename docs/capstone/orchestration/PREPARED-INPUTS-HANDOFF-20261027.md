# Frozen cohort and prepared-input evidence handoff

October27: read-only handoff delivered for the current Mac recipe. **This recipe
uses corrected on-demand inputs, not a fully materialized prepared CT cache.**
Neither the older seven-case cache nor the laptop's fast-cache policy is substituted.

## Implementation and boundaries

`prepared_inputs_workflow_v1.py` defines two registered CPU stages:

1. `cohort` checks independently supplied file pins, exact train/development order,
   nonempty unique disjoint membership, the control's cohort-file bindings, native
   metadata pin inventory and focused-count membership. It retains the existing
   canonical provider identity.
2. `prepared` checks the saved preparation report against that identity, exact row
   order, counts, correction roles, on-demand policy, successful/reaped completion,
   zero reported CT reads/optimizer updates and schedule totals. The existing
   `coverage_slots` validator checks each row's declared coverage feasibility.

These are validators for a saved evidence handoff, not replacements for the owning
provider, source/cohort qualification or cache-payload validators. They do not
recompute the patient permutation or reread native metadata, correction arrays,
CTs or teacher targets. The report's zero-read claims describe its historical
preparation; this handoff itself also reads metadata only. Hash checks establish
consistency with explicitly pinned inputs, not independent scientific acceptance.

The output records `training_authorized: false`, `scientific_ready: false`,
`cache_payloads_revalidated: false` and teacher-target qualification as
`not_evaluated`. A complete target inventory and actual full-provider GPU executor
qualification remain necessary. The corrected labels and current recipe are unchanged.

The new workflow uses the existing executor, artifact publisher, stage registry and
approved run-manifest bridge. Source directories are read-only to this code; outputs
go to a separate dedicated root. No scheduler, provider construction, optimizer,
service restart or GPU dispatch is added.

## Verification

**137 tests passed in16.13s**, including13 new checks for valid reuse/source
immutability and invalid membership/order, metadata inventory, coverage feasibility,
totals, completion, scope, provider identity, policy and changed file pins.

The real saved records from `rsuper-full-provider-20261025-02` and cohort lists from
`rsuper-training-sources-01` passed the CLI:

- Plan created no workflow files.
- Run completed both stages; explicit resume revalidated and reused both.
- Saved source file hashes were identical before and after.
- Both summaries passed the unchanged approved run-manifest v1 schema.
- Membership was1333 train/70 development; the report retained18000 focused and6000
  context updates. These are prepared schedule totals, not newly executed updates.

Evidence is under `outputs/prowl/prepared-inputs-handoff-20261027/`: explicit local
input references, CLI stdout/stderr, summary hashes, regression logs and teacher-pin
check. No case-level payloads were copied into Git or project-management comments.
All328 repository teacher pins matched. The same supervisor/worker remained active;
teacher progress reached518/1333 during this work.

## Operator use

Create an input-reference JSON object with exactly `control`, `result`, `resources`,
`train` and `development`. Each value contains the explicit local `path` and trusted
file-byte `sha256`. Use the retrieval Python environment; the dedicated output root
must already exist and pass the existing50GB storage reserve.

```sh
PYTHONPATH=. .venv-retrieval/bin/python scripts/diagnostics/qualify_prepared_inputs_handoff.py plan --root OUTPUT --inputs REFERENCES.json
PYTHONPATH=. .venv-retrieval/bin/python scripts/diagnostics/qualify_prepared_inputs_handoff.py run --root OUTPUT --inputs REFERENCES.json
PYTHONPATH=. .venv-retrieval/bin/python scripts/diagnostics/qualify_prepared_inputs_handoff.py resume --root OUTPUT --inputs REFERENCES.json --resume-of RUN_UUID
```

`inspect --root OUTPUT --run-id RUN_UUID` is read-only. Reuse always rechecks the
source records. No old run is repinned or rewritten.

## Next gate

This links existing frozen membership and preparation evidence into the bounded
DAG. It does not execute all `build_cohorts`/`build_prepared_cache` duties in the
approved full pipeline. Keep W04-01 open for the remaining production integration,
event/cancellation contracts and eventual training handoff. Avoid rebuilding already
qualified data while the teacher runs; the next training dependency is the completed
target manifest and real executor qualification, not another metadata preparation run.
