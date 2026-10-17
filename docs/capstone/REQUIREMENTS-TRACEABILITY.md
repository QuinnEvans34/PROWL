# Requirements traceability

**Status:** Active planning baseline  
**Sources:** Approved Proposal v3.8 and Technical Appendix v3.1  
**Last reviewed:** 2026-10-12 (evidence overlay; baseline requirements preserved)

This table makes completion auditable. A requirement is not complete until its implementation
artifact and verification evidence exist.

Current evidence and remaining acceptance for every requirement are in the
[October 12 closeout map](weeks/WEEK-01-CLOSEOUT-2026-10-12.md). The original statuses below
are the planning baseline, not current completion claims. G0-design is delivered; full current-tree
G0-verification remains partial.

## Product and scope

| ID | Requirement | Plan | Required artifact | Verification | Status |
|---|---|---|---|---|---|
| REQ-P01 | Support an autonomous scan-to-review workflow | 01, 04, 05, 08, 12 | End-to-end run package | Unseen full-volume case completes without ground-truth ROI | Planned |
| REQ-P02 | Remain annotation-assist/research use, not diagnostic | 01, 08, 12 | UI copy, docs, risk/ethics record | Claim review across UI/API/report/presentation | Planned |
| REQ-P03 | Support accept/edit/reject review action and record the decision | 08 | Validated review request, append-only event, durable receipt, and history UI | Append/reload/revision/idempotency round-trip against exact prediction identity | Design in progress |
| REQ-P04 | Extend the existing UI rather than rebuild from zero | 08 | Current-state map and scoped UI changes | Regression test of retained workflows | Planned |
| REQ-P05 | Distinguish prior foundation from new capstone work | Master plan, 12 | Lineage table and final report section | Artifact/source audit | In progress |
| REQ-P06 | Do not reuse a model trained during the preceding project | 05, 06, 10 | Initialization audits, historical-checkpoint denylist, and new localizer/segmenter model manifests | Registry/run manifest contains permitted initialization only | Planned |

## Imaging data and cohorts

| ID | Requirement | Plan | Required artifact | Verification | Status |
|---|---|---|---|---|---|
| REQ-D01 | Use PanTS and eligible PANORAMA imaging data | 02, 03 | Source manifests and unified manifest | Count/reconciliation report | In progress |
| REQ-D02 | Group splits by patient/subject identity | 02, 03 | Identity mapping and frozen cohort files | No subject spans protected partitions | In progress |
| REQ-D03 | Track source, label, and annotation provenance | 02, 03 | Manifest/provenance schema | Required-field and source-stratification tests | In progress |
| REQ-D04 | Exclude declared overlapping/imported PANORAMA sources | 03 | Versioned exclusion list | Load-time assertion and excluded-count reconciliation | In progress |
| REQ-D05 | Detect duplicates/overlaps and document residual risk | 02, 03 | Duplicate report | Known-pair fixtures plus manual review sample | In progress |
| REQ-D06 | Remap source labels deterministically | 03 | Versioned mapping configuration | Voxel fixture and real-case overlay test | In progress |
| REQ-D07 | Preserve immutable originals and version derived artifacts | 01, 04, 10 | Artifact layout and run manifest | Hash/immutability and rerun checks | In progress |
| REQ-D08 | Freeze cohorts before model comparison | 02, 06 | Cohort definition and membership hashes | Repeat build produces identical membership/hash | In progress |

## Imaging and evaluation

| ID | Requirement | Plan | Required artifact | Verification | Status |
|---|---|---|---|---|---|
| REQ-M01 | Localize pancreas before detailed segmentation | 05 | Localization prediction, ROI-policy record, and cascade bundle | Full-volume no-oracle integration test | Planned |
| REQ-M02 | Produce pancreas and suspected-lesion contours | 05 | Source-space probability/mask prediction set and NIfTI manifests | Schema/grid/label validation | Planned |
| REQ-M03 | Report pancreas and lesion segmentation separately | 06 | Versioned metric specification plus per-study/aggregate result tables | Metric schema rejects aggregate-only or ambiguous aliases | Planned |
| REQ-M04 | Evaluate patient-level detection and specificity | 06 | Mask-evidence operating grid, frozen policy, confusion counts, and uncertainty | Golden confusion-matrix/curve fixtures | Planned |
| REQ-M05 | Distinguish provided-region reference from autonomous results | 05, 06 | Distinct prediction-mode records and side-by-side result schema | Report wording/lineage audit | Planned |
| REQ-M06 | Use full-volume inference for evaluation | 05, 06 | Image-only full-volume run manifest and spatial-coverage evidence | Input/output spatial coverage assertion | Planned |
| REQ-M07 | Run at least one controlled, evidence-selected model comparison | 06 | Immutable preregistration, changed-factor audit, paired comparison, and terminal decision | Matched cohort/config audit; preregistered accept/reject/inconclusive bar | Planned |
| REQ-M08 | Preserve flexibility for calibration, post-processing, architecture, ensemble, or distillation | 06 | Post-G4 candidate matrix and D-205 selection decision | Method chosen only after baseline error analysis | Planned |
| REQ-M09 | Analyze false alarms and relevant subgroups | 06 | Per-study results, deterministic review cases, and error/subgroup report | Source/phase/size/quality/failure breakdown with counts and uncertainty | Planned |
| REQ-M10 | Avoid multi-lesion-destructive default processing | 06, 09 | Component/matching contract and raw/derived prediction identities | Multi-component matching and largest-component rejection fixtures | Planned |

## Literature retrieval and generated response

| ID | Requirement | Plan | Required artifact | Verification | Status |
|---|---|---|---|---|---|
| REQ-R01 | Build a versioned PubMed/PMC evidence corpus | 07 | Search/source snapshot, per-document rights records, stable passages, and corpus manifest | Identifier/version/license/count/rebuild reconciliation | Planned |
| REQ-R02 | Construct queries from structured findings and reviewer question | 07, 08 | Allowlisted structured-finding and deterministic query contracts | Accepted/forbidden-field and deterministic query fixtures | Planned |
| REQ-R03 | Retrieve passages with citation identifiers | 07 | Lexical/vector/hybrid index manifests and ranked passage records with locators/component scores | Every eligible result maps to exact rights-approved corpus passage/source | Planned |
| REQ-R04 | Generate only from retrieved evidence or refuse | 07 | Sufficiency decision, atomic claim/citation response, and extractive/refusal fallback | Unsupported/invented claim/citation and adversarial refusal fixtures | Planned |
| REQ-R05 | Measure recall@k and mean reciprocal rank | 07 | Frozen 30-development/30-held-out question/relevance set and per-question retrieval report | Golden metric fixtures and held-out access audit | Planned |
| REQ-R06 | Measure response groundedness and refusal accuracy | 07 | Answerable/unanswerable response set, claim judgments, and evaluation report | Claim-to-passage rubric, citation integrity, required-concept scoring, and refusal confusion matrix | Planned |
| REQ-R07 | Keep evidence support secondary to the imaging workflow | Master plan, 07 | Critical-path schedule | Retrieval delay cannot block imaging evaluation | Active |

## Engineering, interface, and quality

| ID | Requirement | Plan | Required artifact | Verification | Status |
|---|---|---|---|---|---|
| REQ-E01 | Implement a tested, restartable workflow DAG | 04 | DAG/stage definitions, run manifests, and stage-attempt events | Injected failure/resume test; idempotent rerun | Design in progress |
| REQ-E02 | Keep stages config-driven and auditable | 01, 04, 10 | Resolved config and artifact metadata | Hash/lineage audit | In progress |
| REQ-E03 | Use unit, integration, and regression testing | 09 | Strict suite/marker configuration, risk-linked check matrix, fixtures/oracles, runnable commands, and immutable test-run evidence | Clean-environment fast/integration/local-real/browser/release reports with explicit skip audit | Design in progress |
| REQ-E04 | Integrate predictions, measurements, evidence, and review in UI | 08 | Canonical view model, static/FastAPI adapters, state model, and representative fixtures | Transport parity plus success/failure/refusal/stale critical-flow test | Design in progress |
| REQ-E05 | Conduct stakeholder review | 11 | Approved living protocol/outreach tracker, actual session notes, prioritized findings and role limitations | Completed session or conducted suitable-role/asynchronous fallback; planning alone is insufficient | Planned |
| REQ-E06 | Maintain professional user/developer documentation | 12 | Setup guide, user guide, architecture/evaluation docs | Fresh-environment walkthrough | Planned |
| REQ-E07 | Record data licenses, source versions, and corpus rights | 02, 03, 07, 10 | License/version registry | Release checklist audit | In progress |
| REQ-E08 | Reserve Week 9 for buffer/stabilization | Master plan, 12 | Release plan | No new feature work in Week 9 | Locked |
| REQ-E09 | Reserve Week 10 for delivery/presentation | Master plan, 12 | Delivery checklist | No new feature work in Week 10 | Locked |
| REQ-E10 | Make formal runs and reported artifacts traceable and reproducible | 01, 04, 09, 10, 12 | Root-independent artifact/run/environment records and bounded reproduction recipes | Clean-environment imaging/retrieval/review reproduction plus release identity audit | Design in progress |
| REQ-E11 | Protect keeper, review, and release evidence through explicit retention and tested recovery | 10, 12 | Retention classes, backup catalogs, checksum evidence, and restore records | Distinct-failure-domain consumer-level restore drills after setup and before G8 | Design in progress |
| REQ-E12 | Select local or rented compute from measured feasibility and preserve platform/data/cost boundaries | 06, 10 | Representative benchmark, schedule projection, and D-210 record | Critical-path estimate includes overhead and 25% contingency; any remote path has explicit approval and matched smoke | Design in progress |

## Status protocol

- `Planned` — mapped to a plan, artifact, and test.
- `In progress` — implementation or validation has started.
- `Verified` — evidence exists and is linked from this table.
- `At risk` — the artifact or test is unlikely to meet its scheduled gate.
- `Deferred` — only valid for optional scope, with a recorded decision.


## October 17 user-authorized measurement-aware extension

Required for final delivery, after core RAG acceptance. Source: Quinton's explicit instruction;
see [extension plan](retrieval/MEASUREMENT-AWARE-EXPERT-PLAN.md). Original baseline requirements above
remain intact; these rows are new commitments, not assertions about the original proposal wording.

| ID | Requirement | Plan | Required artifact | Verification | Status |
|---|---|---|---|---|---|
| REQ-X01 | Verified pancreas/lesion measurements and validated expert adapter | Step 10 / AI-05 | Versioned measurements, units, validity and lineage | Geometry fixtures, reviewed cases, frozen tolerances, invalid-mask checks | Required; queued after core acceptance |
| REQ-X02 | Eligible published reference comparisons | Step 11 / AI-06 | Rights-cleared reference records and comparison provenance | Supported comparison plus mismatched/absent reference cases | Required; queued after X01 |
| REQ-X03 | Plain-language measurement-aware explanations in viewer | Steps 11–12 / AI-06–AI-07 | Cited explanations and versioned UI/API | Claim/number/unit checks, case isolation, refusals and separate final assessment | Required; not started |
| REQ-X04 | Human-reviewed feedback consumable by training workflow | Step 12 / AI-07 | Review ledger, eligible export and loader integration | Zero-update loader dry-run; unreviewed/protected-role rejection | Required; no training launch |
