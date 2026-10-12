# Week 1 architecture and test-evidence closeout

Reviewed October 12, 2026. W01-01 reconciliation is complete; this is not full-product acceptance.
This current 43-requirement overlay supersedes the October 6 map for present status, while preserving
that historical record and the approved requirement wording.

## G0 disposition

- **G0-design: delivered/approved.** Plan 01 records all six architecture acceptance items checked;
  context, component, data-flow, identity, invalidation and contract examples exist. Plans 02–12
  retain the shared design vocabulary. No new architecture approval or rewrite is needed.
- **G0-verification: partial, not a fresh complete pass.** The September 19 foundation records a
  clean locked Python installation, all 37 historical tests classified/passing and 30 core contract
  checks. September 20 records the UI foundation. These are dated evidence, not a current-tree
  certificate. Later focused tests validate their named slices only.
- **Remaining setup gap:** a current clean-environment install/collection and dependency/coverage
  reconciliation is not established for the expanded tree. The default shell Node failed current
  jsdom/undici setup; bundled Node passed the saved-view tests. Record supported Node and Python
  environments and current collection/skip inventory before a new full G0/G8 verification claim.
  This engineering follow-up belongs to REQ-E03/E10 and the Week 2 review; product features still
  scheduled for later weeks do not block closure of this evidence-mapping task.

## Requirement-to-evidence and check map

All 43 original IDs occur exactly once below. A linked test means an executable check exists, not
that it was rerun today or fully satisfies the requirement. For manual/planned checks, use the
original baseline Verification column as the protocol; the remaining acceptance names the missing
artifact. Ownership: Mac development + Quinton unless explicitly assigned to the other laptop/chat.

| Requirement | Current evidence | Existing check / planned protocol | Remaining acceptance / scope |
|---|---|---|---|
| REQ-P01 — Support an autonomous scan-to-review workflow | [Evidence](../imaging/SAVED-PREDICTION-VIEWER.md) | [Executable check](../../../tests/test_autonomous_cascade_v1.py) | Saved CT-to-view slice delivered; durable reviewed end-to-end package remains Week 7. |
| REQ-P02 — Remain annotation-assist/research use, not diagnostic | [Evidence](../retrieval/GUIDED-FIXTURE-DEMO.md) | [Executable check](../../../tests/test_guided_evidence_fixture.py) | Approved refusal/research wording in fixtures; release-wide claim audit remains Week 8–10. |
| REQ-P03 — Support accept/edit/reject review action and record the decision | [Evidence](../implementation/08-review-interface.md) | [Executable check](../../../ui/tests/reviewState.test.js) | Display state tests are not durable accept/edit/reject history. Append/reload/revision/idempotency remains Week 7. |
| REQ-P04 — Extend the existing UI rather than rebuild from zero | [Evidence](../imaging/SAVED-PREDICTION-VIEWER.md) | [Executable check](../../../ui/tests/ReviewWorkspace.test.jsx) | Existing NiiVue reused; saved-route browser checks delivered. Broader retained-workflow regression remains at integration. |
| REQ-P05 — Distinguish prior foundation from new capstone work | [Evidence](../operations/PRECOURSE-RETROSPECTIVE-2026-10-03.md) | Manual/planned: baseline verification protocol | Prior/capstone boundary documented; final report/source audit remains Week 10. |
| REQ-P06 — Do not reuse a model trained during the preceding project | [Evidence](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) | [Executable check](../../../tests/test_segmenter_initialization_audit_v1.py) | Per-candidate initialization/source audit still required; external pretraining membership uncertainty is not cleared. |
| REQ-D01 — Use PanTS and eligible PANORAMA imaging data | [Evidence](../data/PORTABLE-COHORT-2026-10-12.md) | [Executable check](../../../tests/test_portable_cohort.py) | PanTS package delivered; eligible PANORAMA integration/handback belongs to Week 3 and other laptop/chat. |
| REQ-D02 — Group splits by patient/subject identity | [Evidence](../data/PORTABLE-COHORT-2026-10-12.md) | [Executable check](../../../tests/test_protected_identity.py) | Original roles enforced; study-as-subject fallback does not prove biological uniqueness. |
| REQ-D03 — Track source, label, and annotation provenance | [Evidence](../data/PANTS-SOURCE-USE-REVIEW-2026-09-28.md) | [Executable check](../../../tests/test_annotation_contract_v2.py) | Source assertions retained; individual anatomy/units and future source provenance remain open. |
| REQ-D04 — Exclude declared overlapping/imported PANORAMA sources | [Evidence](../implementation/03-panorama-integration.md) | [Executable check](../../../tests/test_panorama_acquisition.py) | Acquisition checks do not prove final overlap exclusions. Source-specific exclusion counts/fixtures remain Week 3. |
| REQ-D05 — Detect duplicates/overlaps and document residual risk | [Evidence](../data/PORTABLE-COHORT-2026-10-12.md) | [Executable check](../../../tests/test_protected_identity.py) | Protected group/duplicate controls exist; cross-source known-pair/manual audit and residual uncertainty remain. |
| REQ-D06 — Remap source labels deterministically | [Evidence](../implementation/03-panorama-integration.md) | [Executable check](../../../tests/test_segmenter_source_values_v1.py) | PanTS decoding checks are bounded; PANORAMA label mapping and real overlay remain Week 3. |
| REQ-D07 — Preserve immutable originals and version derived artifacts | [Evidence](../contracts/artifact-layout.md) | [Executable check](../../../tests/test_artifact_store.py) | Versioned artifact controls exist; all release producers still need immutable-output audit. |
| REQ-D08 — Freeze cohorts before model comparison | [Evidence](../data/PORTABLE-COHORT-2026-10-12.md) | [Executable check](../../../tests/test_portable_cohort.py) | 1,333 train/75 validation package verified locally; Lenovo execution and later comparison freeze remain separate. |
| REQ-M01 — Localize pancreas before detailed segmentation | [Evidence](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) | [Executable check](../../../tests/test_autonomous_cascade_v1.py) | Real CT-only cascade delivered; useful localization quality remains unproven. |
| REQ-M02 — Produce pancreas and suspected-lesion contours | [Evidence](../imaging/SAVED-PREDICTION-VIEWER.md) | [Executable check](../../../tests/test_saved_prediction_view.py) | Native contours/display delivered; seven failures and poor segmentation quality remain visible. |
| REQ-M03 — Report pancreas and lesion segmentation separately | [Evidence](../../evaluation-autonomous-cohort.md) | [Executable check](../../../tests/test_saved_prediction_scoring.py) | Separate native metrics delivered; final frozen evaluation remains Week 8. |
| REQ-M04 — Evaluate patient-level detection and specificity | [Evidence](../implementation/06-evaluation-and-model-experimentation.md) | [Executable check](../../../tests/test_metric_goldens.py) | Golden metric mechanics exist; empty references are not verified healthy controls. Detection/specificity validation remains. |
| REQ-M05 — Distinguish provided-region reference from autonomous results | [Evidence](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) | [Executable check](../../../tests/test_fixed_cohort_evaluation.py) | 68 matched mode comparisons retained; no clean generalization claim. |
| REQ-M06 — Use full-volume inference for evaluation | [Evidence](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) | [Executable check](../../../tests/test_autonomous_cascade_v1.py) | Full CT localization/native restoration demonstrated; preserve 75 requested denominator and seven failures. |
| REQ-M07 — Run at least one controlled, evidence-selected model comparison | [Evidence](../implementation/06-evaluation-and-model-experimentation.md) | [Executable check](../../../tests/test_fixed_cohort_evaluation.py) | Matched comparison tooling exists; controlled preregistered candidate decision remains conditional W02-03 / Week 6. |
| REQ-M08 — Preserve flexibility for calibration, post-processing, architecture, ensemble, or distillation | [Evidence](../implementation/06-evaluation-and-model-experimentation.md) | Manual/planned: baseline verification protocol | Method flexibility retained; select candidate after error analysis. No automatic sweep. |
| REQ-M09 — Analyze false alarms and relevant subgroups | [Evidence](../imaging/SOURCE-DISPOSITION-2026-10-12.md) | [Executable check](../../../tests/test_saved_prediction_scoring.py) | Per-case errors/source issues retained; subgroup counts, uncertainty and verified controls remain Week 6–8. |
| REQ-M10 — Avoid multi-lesion-destructive default processing | [Evidence](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) | [Executable check](../../../tests/test_segmenter_predicted_roi_v2.py) | All-support default retained; largest-component diagnostic is not default. Full matching/measurement acceptance remains. |
| REQ-R01 — Build a versioned PubMed/PMC evidence corpus | [Evidence](../retrieval/STREAMING-CORPUS.md) | [Executable check](../../../tests/retrieval/test_streaming_corpus.py) | 1,656-file catalog complete; selection, rights-approved passages and rebuild acceptance remain W02-06/07. |
| REQ-R02 — Construct queries from structured findings and reviewer question | [Evidence](../retrieval/GUIDED-FIXTURE-DEMO.md) | [Executable check](../../../tests/retrieval/test_query.py) | Synthetic guided/query boundaries exist; real finding/question adapter remains Week 5. |
| REQ-R03 — Retrieve passages with citation identifiers | [Evidence](../retrieval/TOPIC-SELECTION-V0.md) | [Executable check](../../../tests/retrieval/test_passages.py) | Offline passage contracts exist; real versioned index/citation retrieval remains W02-07/08. |
| REQ-R04 — Generate only from retrieved evidence or refuse | [Evidence](../retrieval/GUIDED-FIXTURE-DEMO.md) | [Executable check](../../../tests/test_guided_evidence_fixture.py) | Saved fixture answer/refusal delivered; live evidence sufficiency, partial/conflicting responses and groundedness remain. |
| REQ-R05 — Measure recall@k and mean reciprocal rank | [Evidence](../implementation/07-literature-retrieval.md) | [Executable check](../../../tests/retrieval/test_metrics.py) | Metric checks exist; frozen 30/30 question sets and held-out retrieval report remain Week 6–8. |
| REQ-R06 — Measure response groundedness and refusal accuracy | [Evidence](../implementation/07-literature-retrieval.md) | [Executable check](../../../tests/retrieval/test_metrics.py) | Fixture checks do not measure real groundedness/refusal accuracy; actual judgments/report remain Week 6–8. |
| REQ-R07 — Keep evidence support secondary to the imaging workflow | [Evidence](../weeks/WEEK-02-WORK-PLAN.md) | Manual/planned: baseline verification protocol | Imaging-first queue active; continue weekly critical-path review. |
| REQ-E01 — Implement a tested, restartable workflow DAG | [Evidence](../implementation/04-workflow-orchestration.md) | Manual/planned: baseline verification protocol | Individual transaction/replay recovery exists; integrated stage DAG failure/resume remains Week 4. |
| REQ-E02 — Keep stages config-driven and auditable | [Evidence](../data/PORTABLE-COHORT-2026-10-12.md) | [Executable check](../../../tests/test_fixed_cohort_evaluation.py) | Pinned consumer/config boundaries delivered; complete workflow config/lineage remains Week 4. |
| REQ-E03 — Use unit, integration, and regression testing | [Evidence](../testing/FOUNDATION-2026-09-19.md) | [Executable check](../../../tests/test_contracts.py) | Historical baseline + current focused evidence exist; current clean install/full collection/coverage reconciliation remains open. |
| REQ-E04 — Integrate predictions, measurements, evidence, and review in UI | [Evidence](../imaging/SAVED-PREDICTION-VIEWER.md) | [Executable check](../../../ui/tests/saved-browser/saved-prediction.spec.js) | Saved prediction and guided fixture slices delivered; full case-package transport parity, measurements and durable review remain Week 7. |
| REQ-E05 — Conduct stakeholder review | [Evidence](../implementation/11-stakeholder-validation.md) | Manual/planned: baseline verification protocol | Protocol exists; actual suitable-role session or conducted fallback remains Week 7. Quinton owns outreach. |
| REQ-E06 — Maintain professional user/developer documentation | [Evidence](../weeks/WEEK-02-WORK-PLAN.md) | Manual/planned: baseline verification protocol | Living plans/run instructions updated; fresh release setup/user walkthrough remains Week 8–10. |
| REQ-E07 — Record data licenses, source versions, and corpus rights | [Evidence](../data/PANTS-SOURCE-USE-REVIEW-2026-09-28.md) | [Executable check](../../../tests/retrieval/test_records.py) | Narrow source-use review exists; per-passage rights and public-release clearance remain open. |
| REQ-E08 — Reserve Week 9 for buffer/stabilization | [Evidence](../weeks/PROJECT-DELIVERY-OUTLINE-2026-10-09.md) | Manual/planned: baseline verification protocol | Week 9 stabilization reserved; manual weekly schedule check. |
| REQ-E09 — Reserve Week 10 for delivery/presentation | [Evidence](../weeks/PROJECT-DELIVERY-OUTLINE-2026-10-09.md) | Manual/planned: baseline verification protocol | Week 10 delivery reserved; manual weekly schedule check. |
| REQ-E10 — Make formal runs and reported artifacts traceable and reproducible | [Evidence](../data/PORTABLE-COHORT-2026-10-12.md) | [Executable check](../../../tests/test_portable_cohort.py) | Local deterministic package/consumer delivered; remote and clean-environment full-system reproduction remain. |
| REQ-E11 — Protect keeper, review, and release evidence through explicit retention and tested recovery | [Evidence](../operations/CAP-EXP-014-RESULTS-2026-10-03.md) | Manual/planned: baseline verification protocol | Historical bounded restore evidence retained; N4 relevance and final distinct-domain release restore remain open. |
| REQ-E12 — Select local or rented compute from measured feasibility and preserve platform/data/cost boundaries | [Evidence](../implementation/10-reproducibility-and-operations.md) | Manual/planned: baseline verification protocol | Measured prior jobs retained; future compute allocation needs current fit/budget. Training owned by other laptop/chat. |

## Reusable verification records and commands

- [Python foundation](../testing/FOUNDATION-2026-09-19.md): historical clean install, 37-test baseline,
  marker policy and 30 contract checks. Preserve its dated results.
- [UI foundation](../testing/UI-FOUNDATION-2026-09-20.md): historical component/browser/build evidence.
- [Portable cohort](../data/PORTABLE-COHORT-2026-10-12.md): 58 focused Python checks and real metadata
  package audit, without rerunning real inference or training.
- [Saved viewer](../imaging/SAVED-PREDICTION-VIEWER.md): 7 Python, 12 UI and 3 real browser checks,
  native screenshot inspection and successful build. Browser tests require its documented local server.
- [Guided response](../retrieval/GUIDED-FIXTURE-DEMO.md) and [import runbook](../retrieval/STREAMING-CORPUS.md):
  delivered fixture/catalog evidence, not live retrieval quality or a loaded vector database.

Reproduce affected checks from the repository root (UI commands from `ui/`):

```sh
.venv-prowl/bin/python -m pytest -q tests/test_contracts.py
.venv-prowl/bin/python -m pytest -q tests/test_portable_cohort.py tests/test_fixed_cohort_evaluation.py tests/test_protected_identity.py
.venv-prowl/bin/python -m pytest -q tests/test_saved_prediction_view.py
# ui/: use a Node runtime compatible with the installed jsdom, as in the viewer record
node node_modules/vitest/vitest.mjs run tests/savedPrediction.test.jsx
node node_modules/@playwright/test/cli.js test --config playwright.saved.config.js
npm run build
```

These are reproduction instructions, not new test runs in this documentation-only closeout.
No summed historical test count, statement/branch percentage, training readiness or release pass is claimed.

## Handoff and real remaining work

- **Current source blockers:** W02-02 retains seven unknown-unit cases and upstream head-study
  annotation provenance. No silent exclusions or unit assumptions.
- **Week 2 review:** W02-05 must track the environment/collection follow-up and all remaining project
  areas. W01-05 human hours still need Quinton's input; no machine runtime is credited.
- **Then AI expert:** W02-06 selection → W02-07 permitted passages → W02-08 bounded pgvector slice.
  Catalog completion is not a populated retrieval index. W01-04 legacy N4 recovery relevance must
  be decided before depending on that storage workflow.
- **Later product gates:** PANORAMA handback, integrated restartable DAG, model-quality evaluation,
  full case-package adapters, durable review events, real retrieval evaluation, stakeholder session
  and final reproduction/restore evidence remain assigned to their original component plans/weeks.

No code, dependency, data, model, hours or release policy changed in this closeout. Existing checks
were inspected by path and retained result; the new map's ID coverage and local links were checked.
