# W04-01 / G3 evidence review — October27

**Disposition: bounded CPU workflow delivered; full G3 remains open.** This review
maps retained evidence to the approved Plan04 completion gate; it does not replace
that gate or equate synthetic execution with a qualified imaging/training pipeline.
D-201 already selected the repository runner. No further framework trial is needed.

## Completion-gate reconciliation

| Approved criterion | Evidence and disposition | Work still required |
| --- | --- | --- |
| D-201 tool selection | **Complete:** [measured fallback selection](TOOL-SELECTION-RESULTS-20261026.md), decision record and isolated cleanup | None; do not repeat selection |
| Versioned manifests, events, registry and configuration | **Partial:** approved run-manifest v1, strict offline registry, stage-v2/lifecycle-v1 schemas, immutable context binding all exercised | Full pipeline/configuration contract alignment; offline schemas are deliberately scoped, not the entire Plan04 vocabulary |
| Plan/run/resume/inspect/status | **Pass for shipped CPU adapters:** [operator commands](CPU-WORKFLOW-RECOVERY-20261026.md), registered CLIs, mutation-free planning and read-only inspection | Training-specific operator/recovery handoff |
| Imaging and literature smoke twice | **Partial:** invented native/evidence smoke, saved-package and case/literature handoffs complete then reuse verified outputs | Full intended imaging/retrieval subgraphs, rather than only downstream handoff adapters |
| Injected mid-write failure and recovery | **Pass for bounded publisher/executor:** killed subprocess, persisted validation failure and publication-before-event crash preserved; explicit recovery passes | Actual expensive-stage checkpoint continuation remains separate |
| Relevant configuration invalidates only affected descendants | **Pass for bounded DAG:** source retained, changed evidence/config descendants rebuilt; old outputs unchanged | Each future production adapter must declare its correct relevant inputs/configuration |
| Invalid cohort/hash/schema prevents training | **Partial:** [target admission rejection](PIPELINE-ADMISSION-COVERAGE-20261027.md), strict registries and [prepared-input handoff](PREPARED-INPUTS-HANDOFF-20261027.md) | Actual full-provider executor and launch receipt must consume these validated identities; no placeholder training stage |
| Missing/replaced roots and capacity stop before compute | **Pass for bounded adapters:** existing root identity and capacity fault tests; mid-stage capacity loss blocks publication/downstream | Full production preflight artifact and per-stage resource forecast |
| Exclusive accelerator/artifact locks and stale-owner handling | **Partial:** real isolated CPU processes prove conflict, signal termination, kernel-lock release and reacquisition; publisher conflict tests pass | Real full-training cleanup/checkpoint recovery; lock availability alone is not proof a GPU worker is gone |
| Framework/local projection loss preserves authority | **Pass for selected runner's tested scope:** no external framework database dependency; new synthetic summary-loss test inspects/reuses verified outputs without regenerating old summary | Loss of authoritative request/events/context/receipts is corruption, not a supported disposable-state recovery |
| No overwritten artifacts or arbitrary legacy cohort acceptance | **Pass for current adapters:** exact source pins, cohort order/role checks, corruption refusal and immutable publication | Audit each remaining production adapter at integration |
| Operator guide and G3 evidence linked | **Partial:** scoped operator guides and retained evidence linked below | One final production handoff with remaining gates resolved before claiming G3 complete |
| Decisions, risks, traceability, Plans05–08 handoffs | **Updated for this scope:** current review linked from weekly plan, traceability, risks and orchestration index | Scientific acceptance and full imaging/training readiness stay open |

“Pass for bounded” is not a waiver of the broader acceptance criterion. Full G3
has no claimed percentage or overall passing score.

## Evidence actually checked

Retained logs/receipts were found and hashed into
`outputs/prowl/g3-review-20261027/evidence-index.json` (nine named files). This is an
inventory of existing evidence, not a rerun of every historical experiment.

- [CPU recovery](CPU-WORKFLOW-RECOVERY-20261026.md): dependency/invalidation,
  actual subprocess interruption and unchanged attempt recovery.
- [Registry/manifest bridge](REGISTRY-MANIFEST-ALIGNMENT-20261027.md) and
  [prepared-input handoff](PREPARED-INPUTS-HANDOFF-20261027.md): actual CLI completion,
  verified reuse and references; saved on-demand preparation is not a materialized CT cache.
- [Lifecycle/provenance](LIFECYCLE-PROVENANCE-20261027.md): final179 regression passes,
  real SIGINT/SIGTERM, lock/release failures, rehashed invalid records, actual2/2 CLI
  completion/reuse and immutable provenance. These tests overlap earlier counts;
  counts are not added as independent experiments.
- Review follow-up:17 lifecycle tests pass in2.28s, including one new fault injection
  that deletes only a generated summary in a temporary invented run. Inspection and
  explicit resume reuse2/2 stages with zero callbacks; remaining original records
  are unchanged and the new attempt receives its own valid summary.

No scan, private evaluation, model-quality test, GPU qualification or live reviewer
acceptance was performed by this review. Existing failed attempts stay retained.

## Practical next work and stopping conditions

1. Keep the authorized teacher continuation healthy and finish target generation.
   Completion requires all1333 validated targets and successful/reaped final evidence,
   not merely the last progress count.
2. The remaining CPU paperwork is exact configuration/full-registry contract mapping
   for the next real adapter. Add an adapter only when its owning component and input
   receipt are ready; avoid placeholder stages or another scheduler.
3. Once targets are complete, verify the final provider-bound target manifest and
   qualify the actual matched-training executor, recovery and resource admission.
   Stop at any geometry, integrity, budget or cleanup failure. Full scientific launch
   remains subject to the existing frozen comparison gates, even with prior launch
   authorization.

For W04-01, retain In Progress. The CPU slice can be demonstrated now; the remaining
critical path is connecting qualified scientific components, not extending the generic
runner indefinitely. Measurement reliability and independent RAG acceptance remain
separate deliverables.
