# D-201 local tool selection — October26,2026

**Decision: use the small repository runner for PROWL's local DAG.** The user authorized
continued autonomous implementation. The approved selection plan permits this fallback after a
failed mandatory Prefect criterion. This selects the tool; it does not declare G3 complete.

## Measured result

Prefect3.9.0 was installed with jsonschema in a new isolated Python3.12.13 virtual environment under
`outputs/prowl/prefect-selection-20261026/`. Application/training environments and requirement files
were unchanged. The environment freeze contains104 distributions. No GPU, model or real scan was
used. The trial finished in266.23seconds, within the original four-hour ceiling.

The diagnostic `scripts/diagnostics/spike_prefect_local.py` runs source → manifest → summary tasks
through the existing ArtifactStore. Prefect caching/result persistence and retries are disabled;
task returns contain references, not scientific arrays. Profiles/state live in the trial directory,
no API URL/cloud credential is passed, analytics/API logging are disabled, and no UI was requested.
The temporary local API service is framework execution machinery, not an optional UI.

| Trial / criterion | Observation |
| --- | --- |
| Clean graph | All3 artifacts completed and validated;8.11048s measured around the flow call after imports,10.07398s whole process. **Fails the existing under5s tiny-graph limit.** |
| Identical rerun | All3 artifacts independently validated and reused;3.37674s flow,4.48714s whole process. Passes timing on this rerun; does not erase the clean-run failure. |
| Local lifecycle | Both processes exited0 and were reaped; no processes remained in either owned process group. No always-running server installed. |
| Installation impact | Isolated installation successful; no live-environment compatibility claim or shared dependency changes. |
| Remaining interruption/configuration/missing-root/state-loss trials | Not run after mandatory timing failure; not asserted failed or passed. Optional UI not tested. |

The timing difference is consistent with first-use local setup; the trial did not isolate database
migration from other startup costs. This is not evidence of poor scientific correctness, a general
Prefect benchmark, or a claim that every Prefect run takes8seconds. We did not relax the clean-run
limit or turn this capstone selection into a framework-tuning project.

Evidence: ignored `outputs/prowl/prefect-selection-20261026/` contains install/environment/settings,
stdout/stderr, process/cleanup receipts and `decision.json`. Original failures and results are retained.
The probe remains diagnostic only; Prefect is not a production dependency.

Official references consulted for direct task invocation and isolated configuration:
[Prefect tasks](https://docs.prefect.io/v3/concepts/tasks) and
[settings/profiles](https://docs.prefect.io/v3/concepts/settings-and-profiles).
Selection is based on local measurements and the repository contract, not vendor claims.

## Consequence

Continue the existing tool-neutral plan/executor/artifact publisher. PROWL's records and independent
validators remain authoritative. No scheduler, framework database, web UI or cloud service is needed.
Existing interrupted-workflow tests remain valid; they are not Prefect test results.

Still required before full G3: production stage registry/schema alignment, imaging and literature
adapter qualification, accelerator admission/cancellation boundaries, and complete operator evidence.
The selected runner is not automatically qualified for arbitrary callbacks, Windows, model training
or every approved stage. The four-hour spike was a ceiling, not a requirement to spend four hours
once a mandatory criterion failed.
