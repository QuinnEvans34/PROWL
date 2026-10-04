# Decision register

**Status:** Active  
**Last reviewed:** 2026-09-18

This register prevents exploratory notes and older drafts from silently becoming requirements.

## Status meanings

- **Locked** — stated by the approved proposal/appendix or required by a non-negotiable constraint.
- **Provisional** — current default, reversible after a documented comparison.
- **Open** — evidence or design work is still required.
- **Deferred** — explicitly outside the current critical path.
- **Superseded/rejected** — retained to explain why an older plan is no longer active.

## Locked decisions

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-001 | PROWL is an annotation-assist and review workflow, not a diagnostic system. | Approved proposal and appendix | No diagnosis, subtype, prognosis, or treatment claims. Human review remains explicit. |
| D-002 | Proposal v3.8 and Appendix v3.1 outrank older plans. | Approval baseline | Conflicting old Markdown is evidence only. |
| D-003 | No model trained during the preceding project will be reused as the capstone model. | Approved proposal/appendix | Prior checkpoints may be reference comparators; capstone baselines are newly trained and versioned. |
| D-004 | Existing pipeline code and UI scaffolding may be adapted. | Approved proposal/appendix | Reuse must be labeled as foundation; new work and evidence remain distinct. |
| D-005 | The minimum architecture is file-based, versioned, and reproducible. | Approved appendix A2.2 | A relational database or managed service is optional, not a prerequisite. |
| D-006 | Imaging and literature pipelines remain separate until review integration. | Approved appendix A2 | Prevents patient data from becoming a retrieval corpus and isolates failures. |
| D-007 | Original imaging data remains immutable and off-repository. | Approved appendix/storage guardrails | Derived artifacts must be reproducible from source version plus configuration. |
| D-008 | Splits are grouped by patient/subject identity, never by slice or study when a subject has multiple studies. | Approved appendix and known PANORAMA structure | Identity resolution precedes cohort creation. |
| D-009 | Evaluation is autonomous and full-volume; provided-region results are reference-only. | Approved proposal/appendix | No ground-truth ROI or patch-only evaluation in capstone headline results. |
| D-010 | Pancreas and lesion performance are reported separately. | Approved appendix | No aggregate score may hide lesion failure. |
| D-011 | Patient-level sensitivity and specificity are shown as an operating tradeoff. | Approved proposal/appendix | Do not select one favorable threshold without the curve/context. |
| D-012 | PANORAMA labels, exclusions, provenance, duplicates, and patient grouping are test-enforced. | Approved proposal/appendix | Mixed-source training is blocked until reconciliation passes. |
| D-013 | The evidence assistant cites retrieved support or refuses. | Approved proposal/appendix | Unsupported free-form generation is out of scope. |
| D-014 | Retrieval evaluation includes recall@k and MRR; response evaluation includes groundedness and refusal behavior. | Approved appendix | A good-looking demo is not sufficient evidence. |
| D-015 | The existing interface will be extended, not treated as greenfield. | Approved Week 7 wording | UI plan begins with current-state and data-contract review. |
| D-016 | Week 9 is protected buffer/stabilization and Week 10 is delivery/presentation. | Approved schedule | No new stretch scope in either week. |
| D-017 | PROWL is a single-user research workstation for the capstone. | Quinton approval, 2026-09-08 | Multi-user authentication, concurrent editing, PACS integration, and clinical deployment are outside the committed architecture. |
| D-018 | PROWL begins with file-first, versioned artifacts; a database is added only after a measured need is recorded. | Quinton approval, 2026-09-08; Appendix A2.2 | Schemas and integrity constraints are technology-independent; no database migration blocks the scientific critical path. |
| D-019 | One versioned case-package schema is shared by static files and FastAPI. | Quinton approval, 2026-09-08 | Transport cannot change the scientific meaning or shape of a prediction delivered to the UI. |
| D-020 | Review events are append-only and tied to immutable prediction versions. `Edit` means correction required; browser voxel editing is not implied. | Quinton approval, 2026-09-08 | A revision creates a new event; predictions and prior reviews are never overwritten. |
| D-021 | A study is the atomic imaging-data member; a subject is the protected grouping key; “case” is downstream workflow/UI language. | Quinton approval of P02-01, 2026-09-08 | Repeated PANORAMA studies stay distinct while every study from one subject receives one protected role. |
| D-022 | PanTS uses one source-scoped subject per study with `study_as_subject_fallback` and `unverified_unique` assurance. | Quinton approval of P02-02, 2026-09-08; no patient identifier in source metadata | PROWL can group PanTS reproducibly without claiming proven biological-patient uniqueness. |
| D-023 | The first capstone PanTS cohort family reproduces the accepted 7,200 train, 1,800 validation, and 901 publisher-test memberships exactly. | Quinton approval of P02-03, 2026-09-08 | Comparison continuity is preserved; a different split requires a new version and explicit rationale. |
| D-024 | Duplicate manifest keys and duplicate cohort-member records are hard failures. | Quinton approval of P02-04, 2026-09-08 | Deduplication occurs only through an explicit versioned repair artifact, never silently during a protected build. |
| D-025 | Training/development/smoke cohorts descend only from frozen train-role parents; validation/test descendants are evaluation-only. | Quinton approval of P02-05, 2026-09-08 | Parent-role validation blocks wrong-parent sampling before publication or training. |
| D-026 | Imaging-target status is target-aware (for example `pancreatic_lesion` or `pdac`), uses `positive`, `negative`, or `unknown`, and names its evidence. | Quinton approval of P02-06, 2026-09-08; PANORAMA contract clarification, 2026-09-08 | A `non-PDAC` source label cannot silently become “no pancreatic lesion,” and missing evidence cannot become negative. |
| D-027 | Legacy split files are denied by default; only individually registered, hash-verified migration inputs may enter capstone cohorts. | Quinton approval of P02-07, 2026-09-08 | Historical outputs remain preserved while contaminated or ambiguous lists cannot be selected by filename. |
| D-028 | The primary PANORAMA contribution uses the expected 382 import-clean expert-manual PDAC lesion masks after pinned-archive reconciliation and QC. The expected 196 automatic PDAC masks remain a separately named optional arm. | Quinton approval of P03-01, 2026-09-08 | Expert and machine lesion supervision cannot be silently pooled; a machine-label experiment must remain independently selectable and reported. |
| D-029 | PANORAMA PDAC-positive evidence maps one way to `pancreatic_lesion=positive`; `non-PDAC` maps to `pancreatic_lesion=unknown` unless separate evidence proves the broader target negative. | Quinton approval of P03-02, 2026-09-08 | Non-PDAC studies cannot enter a standard lesion-negative loss merely because PDAC is absent. |
| D-030 | Eligible repeated PANORAMA studies are retained and grouped by source subject. Any future PANORAMA evaluation partition is subject-grouped and subject-weighted. | Quinton approval of P03-03, 2026-09-08 | Acquisition variation is retained without allowing a repeated subject to cross protected roles or dominate evaluation. |
| D-031 | After the defined quality audit, PANORAMA machine pancreas masks may be used as disclosed `crop_reference` and `training_target` annotations, but never as headline `evaluation_reference` truth. | Quinton approval of P03-04, 2026-09-08 | Pancreas provenance remains separate from lesion provenance; failed or unresolved quality strata stay quarantined. |
| D-032 | All 274 source-declared NIH/MSD imports are excluded before other PANORAMA eligibility rules; the expected 1,964-study/578-PDAC remainder is asserted. The three clean manual/non-PDAC anomalies begin quarantined. | Quinton approval of P03-05, 2026-09-08 | Known overlap and contradictory records cannot silently enter a source pool or cohort. |
| D-033 | Cross-source duplicate control uses declared exclusions, exact source and decoded hashes, then a versioned approximate CT fingerprint calibrated on at least 20 planted transformations. Approximate matches generate review candidates only. | Quinton approval of P03-06, 2026-09-08 | Cross-role candidates require adjudication; an approximate score alone cannot merge identities or exclude a study. |
| D-034 | PANORAMA is a training source rather than the headline validation/test source. Primary evaluation remains on the accepted protected PanTS cohorts unless a new untouched source partition is explicitly frozen before use. | Quinton approval of P03-07, 2026-09-08 | PANORAMA smoke checks and source-aware diagnostics are permitted, but reused development data cannot be described as independent external validation. |
| D-035 | PANORAMA voxel work is blocked until actual CT and label snapshots are mounted and pinned. The invalid 14-byte historical sample remains quarantined and is never repaired or replaced under the same identity. | Quinton approval of P03-08, 2026-09-08 | Metadata planning may proceed, but geometry, mapping, duplicate scanning, and training eligibility require live snapshot evidence. |
| D-036 | Plan 04 runs locally without Prefect Cloud; an optional self-hosted local UI is observational and never required for correctness. | Quinton approval of P04-02, 2026-09-08 | Medical data and machine paths remain local, and loss of an orchestration UI cannot invalidate scientific state. |
| D-037 | Orchestration stages exchange validated artifact references and small status values, never large scientific payloads through framework result storage or caching. | Quinton approval of P04-03, 2026-09-08 | CTs, models, predictions, and indexes retain PROWL-owned versioned storage and validation. |
| D-038 | Only PROWL derivation identity and independent artifact validation may authorize reuse. | Quinton approval of P04-04, 2026-09-08 | Framework cache state can be displayed but cannot certify a scientific artifact. |
| D-039 | Attempts are written and validated on the destination filesystem, then published atomically there; failed partials are quarantined. | Quinton approval of P04-05, 2026-09-08 | External-drive publication cannot silently degrade into an unsafe cross-volume move. |
| D-040 | Automatic retries are limited to classified transient failures; scientific and contract failures fail closed, and training resume is checkpoint-aware and explicit. | Quinton approval of P04-06, 2026-09-08 | Deterministic defects cannot be hidden by repeated work or accidental duplicate training. |
| D-041 | Workflows execute sequentially by default and use exclusive accelerator and artifact-writer locks; parallelism is permitted only for proven-independent stages. | Quinton approval of P04-07, 2026-09-08 | The single research workstation and external-drive bandwidth remain stable and writes cannot conflict. |
| D-042 | Imaging, literature, integration, and release remain independently executable workflows joined only by exact selected artifact IDs. | Quinton approval of P04-08, 2026-09-08 | One workstream's failure does not invalidate another's complete artifacts. |
| D-043 | The orchestration operator contract includes mutation-free `plan` plus `run`, `resume`, `inspect`, and `status` operations. | Quinton approval of P04-09, 2026-09-08 | The operator can understand roots, inputs, outputs, reuse, locks, and expensive stages before work begins. |
| D-044 | GitHub records code/review/release identity and Notion communicates milestones, blockers, and evidence links; neither controls scientific execution. | Quinton approval of P04-10, 2026-09-08 | Project-management state cannot become a competing runtime authority. |
| D-045 | Plan 04 walkthrough accepted on September 20; separate explicit coding authorization remains required. | Original instruction September 8; Quinton confirmed understanding and requested documentation updates September 20 | Explanation is complete. No installation, spike, schemas, runner, or stage-wrapper implementation is authorized by this documentation request. |
| D-046 | The localizer is trained as a dedicated background/pancreas task; lesion labels, lesion-derived channels, and pancreas-plus-lesion target unions are excluded. | Quinton approval of P05-02, 2026-09-09 | The localization claim is genuinely pancreas-only and target construction receives a lesion-invariance test. |
| D-047 | The autonomous baseline is established on registered PanTS train-role data; PANORAMA is a separately controlled Plan 06 option after G2. | Quinton approval of P05-03, 2026-09-09 | Multi-source value or harm remains measurable instead of being hidden in the baseline. |
| D-048 | Stage 2 training regions use pancreas-only training annotations, physical margin, and bounded frozen jitter; autonomous inference uses only predicted regions and provided-region reference uses pancreas-only reference regions. | Quinton approval of P05-04, 2026-09-09 | Lesion extent cannot tell the segmenter where to look, and predicted-region error can be decomposed honestly. |
| D-049 | A deterministic high-recall ROI policy is selected on a frozen development localization cohort using effective containment before crop cost/runtime. | Quinton approval of P05-05, 2026-09-09 | Threshold, component, and margin rules are measured and frozen before formal baseline evaluation. |
| D-050 | Stage 2 begins with aspect-preserving scale-to-fit plus symmetric padding; it cannot center-crop overflow or independently stretch axes. | Quinton approval of P05-06, 2026-09-09 | The whole selected region remains visible; a larger cube or fixed-spacing ROI inference is the measured fallback. |
| D-051 | Source affine/world coordinates are authoritative, and continuous probabilities are restored to the source grid before discretization and physical measurement. | Quinton approval of P05-07, 2026-09-09 | UI, evaluation, and measurement artifacts share the original CT grid and a serializable transform history. |
| D-052 | Unsafe autonomous cases publish explicit failure or warning records; no reference box, silent whole-volume segmentation, blank-mask substitution, or prior model repairs them. | Quinton approval of P05-08, 2026-09-09 | Difficult cases remain visible and cannot disappear from denominators. |
| D-053 | Pinned, licensed, audited third-party abdominal pretraining may initialize a capstone model; every preceding-project checkpoint and unverifiable initialization is prohibited. | Quinton approval of P05-09, 2026-09-09 | New capstone models can use defensible general pretraining while a historical hash denylist enforces the no-reuse promise. |
| D-054 | Localizer and segmenter have separate immutable model versions; a cascade bundle identifies both plus all prediction-relevant preprocessing and ROI policy. | Quinton approval of P05-10, 2026-09-09 | Component changes necessarily create new prediction identity and remain reproducible. |
| D-055 | Source-space raw masks and required probabilities are preserved; derived post-processing is separately identified and never overwrites raw output. | Quinton approval of P05-11, 2026-09-09 | Operating points and multi-lesion-safe processing can be reevaluated without rerunning inference or erasing evidence. |
| D-056 | Plan 05 exports candidate features but does not choose the reviewer-ordering score or lesion operating point. | Quinton approval of P05-12, 2026-09-09 | D-208 stays open until Plan 06 analyzes baseline curves, calibration, interpretability, and reviewer need. |
| D-057 | Training fixtures and train-role development evidence precede a frozen development-validation baseline; publisher-test evaluation waits until model and operating-policy selection are frozen. | Quinton approval of P05-13, 2026-09-09 | Iterative learning cannot silently convert the strongest remaining evaluation role into tuning data. |
| D-058 | Model training and experimentation are a continuous project workstream rather than activities confined to Weeks 5–6. | Quinton instruction, 2026-09-09 | Training may overlap documentation, data, retrieval, and UI work once each run's safety dependencies pass; Weeks 5–6 remain formal baseline/comparison milestones, while Week 9 permits stabilization reruns only and Week 10 cannot introduce a result-changing experiment. |
| D-059 | Every capstone run is classified before compute as smoke, diagnostic, exploratory, controlled, confirmatory, or stabilization; completed runs cannot be relabeled for stronger evidence. | Quinton approval of P06-02, 2026-09-09 | Claim strength and preregistration requirements remain explicit, preventing retrospective promotion of favorable runs. |
| D-060 | Evaluation uses registered cohort IDs and immutable membership hashes; convenience subsets are seeded role-valid descendants, never arbitrary paths or first-N selection. | Quinton approval of P06-03, 2026-09-09 | Paired comparisons and holdout claims use exact reproducible membership. |
| D-061 | Source-space raw probabilities and masks are evaluated/preserved first; every post-processing or operating policy creates a separately versioned derived prediction set. | Quinton approval of P06-04, 2026-09-09 | Policy effects remain attributable and raw multi-lesion evidence can be reevaluated. |
| D-062 | Segmentation reports precisely named pancreas-parenchyma, pancreas-region, and lesion-positive Dice conventions; empty ground truth never silently inflates the primary lesion mean. | Quinton approval of P06-05, 2026-09-09 | The mutually exclusive label semantics and eligible denominators remain visible across runs. |
| D-063 | Every requested study receives a terminal status; completed-case sensitivity/specificity is paired with end-to-end detection sensitivity, negative-clearance rate, coverage, and failures. | Quinton approval of P06-06, 2026-09-09 | Abstention cannot improve apparent performance, and a technical failure is not mislabeled an anatomical false positive. |
| D-064 | Mask-evidence target status is the primary internal detection reference; other report/metadata definitions remain separate, and D-208 freezes the development-selected score/threshold/policy before publisher-test use. | Quinton approval of P06-07, 2026-09-09 | Reference meaning and operating-policy changes cannot masquerade as model gains. |
| D-065 | Tumor-wise evaluation preserves all lesion components and uses deterministic one-to-one source-grid matching under a preregistered criterion; largest-lesion-only output is prohibited as its default. | Quinton approval of P06-08, 2026-09-09 | Multiple lesions can contribute independently and uncertain external conventions receive named sensitivity analysis rather than false compatibility claims. |
| D-066 | Evaluation reports counts and uncertainty using Wilson intervals for proportions, subject/study-cluster bootstrap for continuous metrics, and paired bootstrap for matched differences. | Quinton approval of P06-09, 2026-09-09 | Small cohorts and heterogeneous per-case changes remain visible instead of being reduced to unstable point means. |
| D-067 | The autonomous baseline is decomposed into localization, effective containment, conditional Stage 2 segmentation, end-to-end performance, and same-segmenter pancreas-only provided-region reference. | Quinton approval of P06-10, 2026-09-09 | D-205 can target the stage actually responsible for the highest-value failure. |
| D-068 | The required controlled comparison is selected only after G4 using user impact, failure prevalence, mechanism, identifiability, feasibility, reuse, and risk evidence. | Quinton approval of P06-11, 2026-09-09 | Early experiments may nominate candidates but do not preempt the proposal's evidence-selected model-experiment decision. |
| D-069 | A controlled experiment freezes hypothesis, intervention unit, endpoint, guardrails, matched cohort, fixed factors, horizon/selection rule, budget, uncertainty, and decision bar before compute. | Quinton approval of P06-12, 2026-09-09 | Coherent compound interventions remain allowed only when the claim concerns the complete block and all coupled changes are disclosed. |
| D-070 | Continuous model work uses an ordered information-value queue, smallest-falsification ladder, safe background compute, weekly evidence review, and preserved terminal results. | Quinton approval of P06-13, 2026-09-09 | “Always training” produces decisions and reusable evidence rather than an unauditable collection of checkpoints. |
| D-071 | Release model and operating policy are frozen on development evidence before one publisher-test execution; only documented correctness/operational repairs may rerun the complete affected evaluation. | Quinton approval of P06-14, 2026-09-09 | Publisher-test results estimate the selected system and cannot trigger model or threshold tuning. |
| D-072 | Every evaluation publishes immutable machine-readable per-study/component evidence plus a derived human-readable report; project-management summaries are never scientific authority. | Quinton approval of P06-15, 2026-09-09 | Reports, UI fields, and presentations trace to one reproducible result identity. |
| D-073 | Literature retrieval remains independently runnable and cannot block the autonomous imaging workflow; the UI exposes a real unavailable/refusal state until retrieval passes G6. | Quinton approval of P07-01, 2026-09-09 | Retrieval failure cannot turn a valid imaging result into a failed or fabricated review. |
| D-074 | The first corpus is limited to CT pancreas/lesion imaging, contour and measurement interpretation, annotation/review workflow, and relevant AI limitations. | Quinton approval of P07-02, 2026-09-09 | Diagnosis, subtype, prognosis, and treatment questions are out of scope and become refusal tests. |
| D-075 | Evidence queries use only an allowlisted non-identifying structured finding and reviewer question. Images, masks, reports, direct identifiers, dates, institutions, and model-generated diagnoses are prohibited. | Quinton approval of P07-03, 2026-09-09 | Patient data cannot enter the literature corpus, query, generation prompt, or third-party service. |
| D-076 | PubMed records and available abstracts form the broad corpus base; full text enters only through PMC Open Access or another exact license permitting the intended use. Text stays local/off-Git. | Quinton approval of P07-04, 2026-09-09 | Free access is not treated as redistribution permission; release artifacts publish manifests and citations rather than restricted text. |
| D-077 | NCBI acquisition uses approved services, tool/email identification, batching, caching/retry, current rate limits, and secret storage for any API key; article-page scraping is prohibited. | Quinton approval of P07-05, 2026-09-09 | Corpus acquisition remains respectful, reproducible, and recoverable. |
| D-078 | Every source representation receives a machine-readable rights record; unknown full-text rights exclude that text while retaining allowed metadata and links. | Quinton approval of P07-06, 2026-09-09 | One unverified document cannot contaminate the distributable corpus. |
| D-079 | Corpus builds freeze search protocol, cutoff, query translation, selection rules, retrieval time, source inventory, and content hashes. | Quinton approval of P07-07, 2026-09-09 | Search drift cannot silently change passage IDs, evaluation, or citations. |
| D-080 | Canonical work identity reconciles PMID, PMCID, DOI, content versions, duplicates, corrections, and retractions while preserving representation-level provenance. | Quinton approval of P07-08, 2026-09-09 | Duplicate indexing cannot inflate retrieval, and material notices remain visible. |
| D-081 | Passages are normalized without paraphrase and carry stable section/sentence/offset locators and content hashes; a chunking change creates a new corpus version. | Quinton approval of P07-09, 2026-09-09 | Every citation can resolve to the exact supporting source text. |
| D-082 | Historical September 9 direction: SQLite FTS control and LanceDB first, with Chroma/FAISS fallbacks. Superseded for Plan 07 by D-260 and D-264. | Quinton approval of P07-10, 2026-09-09; September 28 amendments below | Current engine is literature-only PostgreSQL + pgvector; the prototype lexical control is PostgreSQL FTS with ts_rank_cd. |
| D-083 | The baseline embedding model runs locally and is pinned by model/version/hash with complete vector-recipe and environment identity. | Quinton approval of P07-11, 2026-09-09 | An external embedding service is optional only after a measured need and Plan 10 boundary review. |
| D-084 | Lexical and dense candidates remain separately observable; rights/metadata filters, per-source caps, deterministic fusion/reranking, component scores, and final rank are recorded. | Quinton approval of P07-12, 2026-09-09 | Retrieval failures can be attributed instead of hidden behind one opaque score. |
| D-085 | Retrieval reports recall@1/3/5/10 and MRR on labeled answerable questions plus latency, empty-result, duplicate-source, and source-diversity diagnostics; development selects and held-out verifies. | Quinton approval of P07-14, 2026-09-09 | Generated prose cannot substitute for direct retriever evaluation. |
| D-086 | Evidence responses consist of atomic claims mapped to retrieved passage IDs and pass a deterministic sufficiency check; ranked passages or refusal are the safe fallbacks. | Quinton approval of P07-15, 2026-09-09 | A citation-shaped response with unsupported content is treated as a defect. |
| D-087 | Groundedness, citation support/precision, answer completeness, and refusal accuracy use frozen rubrics; unsupported clinical claims fail the release gate. | Quinton approval of P07-16, 2026-09-09 | Fluency cannot compensate for missing evidence or unsafe scope. |
| D-212 | The capstone extends the existing viewer-first React/NiiVue workspace incrementally and captures a visual/interaction baseline before changing domain flow. | Quinton approval of P08-01, 2026-09-09 | Week 7 is not consumed by a risky greenfield rewrite. |
| D-213 | Components consume one validated internal view model; static and FastAPI repositories adapt the same case-package contract and legacy `results.json` stays behind a historical adapter. | Quinton approval of P08-02, 2026-09-09 | Transport-specific fields cannot change scientific meaning or spread across the component tree. |
| D-214 | Package schema/version, identity, relative-reference, file-metadata, and cross-record validation precede scientific rendering; missing or invalid fields never become zeros or blank successful contours. | Quinton approval of P08-03, 2026-09-09 | Corrupt evidence cannot be beautified into a plausible result. |
| D-215 | `operational_review` is reference-free; only `validation_demo` may expose a separately labeled optional reference/evaluation block under its required reveal policy. | Quinton approval of P08-04, 2026-09-09 | Ground truth cannot shape ordinary review or be mistaken for an autonomous input. |
| D-216 | Package loading, analysis, evidence, review persistence, and viewer presentation use orthogonal explicit states with request/artifact identity fencing on case changes. | Quinton approval of P08-05, 2026-09-09 | Late responses and coupled booleans cannot corrupt the active review. |
| D-217 | Ordinary review begins from unmarked multiplanar CT when possible; prediction follows, while 3D remains reversible supporting context rather than the sole scientific inspection or measurement view. | Quinton approval of P08-06, 2026-09-09 | Derived display meshes cannot imply evidence or resolution they do not contain. |
| D-218 | CT, prediction, reference, and discrepancy are distinguished by text/source/anatomy/state as well as color, and direct canvas actions have equivalent named controls. | Quinton approval of P08-07, 2026-09-09 | Review meaning cannot depend on color perception or pointer-only canvas use. |
| D-219 | A versioned case-package revision decouples measurements from optional reviewer ordering. Ordering requires a frozen policy identity/value/label/limitations; neutral deterministic order is used until D-208 resolves. | Quinton approval of P08-08, 2026-09-09 | An unresolved score cannot become a placeholder patient-risk signal or suppress valid measurements. |
| D-220 | The interface offers bounded, versioned evidence-question intents rather than an open-ended chat box; prohibited diagnosis/treatment intents receive an immediate scope refusal. | Quinton approval of P08-09, 2026-09-09 | The literature tool remains evaluable and cannot drift into clinical chat. |
| D-221 | Evidence renders explicit retrieving/sufficient/insufficient/limited/failed/unavailable states, claim-to-passage support, source metadata, and passage/refusal fallback. | Quinton approval of P08-10, 2026-09-09 | Decorative citations cannot hide unsupported prose. |
| D-222 | `accept` means usable as proposed for annotation assistance, `edit_required` means useful but needing correction outside the browser, and `reject` means unusable/unsafe as a proposed annotation; none asserts diagnosis or ground truth. | Quinton approval of P08-11, 2026-09-09 | Review actions have stable non-clinical meanings. |
| D-223 | Review submission requires compatible reason codes, an `other` note, and exact target confirmation; failed/localization-failed results may be rejected with an appropriate reason. | Quinton approval of P08-12, 2026-09-09 | The corrections record cannot contain empty decisions or mislabeled technical failures. |
| D-224 | Review success appears only after a local append-only writer returns a verified durable receipt; write failure preserves the draft and never displays saved state. | Quinton approval of P08-13, 2026-09-09 | Browser state cannot masquerade as durable capstone evidence. |
| D-225 | G7 uses the local FastAPI/file writer for persistence. Static-only review export remains explicitly `exported—not recorded` until imported; browser storage is convenience only. | Quinton approval of P08-14, 2026-09-09 | The static demo remains honest about browser filesystem limitations. |
| D-226 | A review revision appends a new event naming its predecessor; the UI derives current state from and displays the immutable chronological chain. | Quinton approval of P08-15, 2026-09-09 | Corrections cannot erase history. |
| D-227 | Package, prediction, evidence, and review identities are checked for staleness; incompatible drafts are blocked and old reviews remain attached only to their original result. | Quinton approval of P08-16, 2026-09-09 | A human decision cannot silently transfer to different weights, thresholds, or evidence. |
| D-228 | Ordinary controls/content target WCAG 2.2 AA; the full task is keyboard-operable with visible focus, live status, non-color cues, and companion controls/text for NiiVue. Approved viewports are 1440×900, 1280×720, and a bounded 1024-pixel fallback. | Quinton approval of P08-17, 2026-09-09 | Canvas-heavy interaction and desktop resizing cannot make the core workflow unusable. |
| D-229 | Plan 08 requires reducer/adapter/component tests, one real-browser critical flow, automated accessibility checks, and manual keyboard/contrast/zoom/viewer review; Plan 09 selects exact tooling. | Quinton approval of P08-18, 2026-09-09 | Visual inspection alone cannot certify the interface, while tool setup remains proportionate. |
| D-204 | The autonomous localization baseline is a newly trained dedicated binary pancreas localizer followed by a newly trained pancreas/lesion segmenter. | Quinton approval of P05-01, 2026-09-09 | A full CT is localized without oracle or lesion input; single-stage full-volume inference remains an evidence-triggered Plan 06 alternative rather than the initial baseline. |
| D-209 | Retrieval success is defined by a frozen 60-question set: 30 development and 30 held-out, each containing 20 answerable and 10 unanswerable/out-of-scope questions balanced across five approved families. | Quinton approval of P07-13, 2026-09-09 | Relevance labels and rubrics are completed before tuning; the held-out set cannot select the index, ranker, thresholds, or response policy. |
| D-230 | Capstone verification standardizes on a clean Python 3.12 environment and Node 24 LTS; Plan 10 records exact environment identities. | Quinton approval of P09-01, 2026-09-09 | Historical or system environments cannot become the reproducibility baseline by accident. |
| D-231 | Runtime and development/test dependencies remain separate; the initial Python test layer is pytest, pytest-cov, jsonschema format validation, and httpx, with additions requiring demonstrated need. | Quinton approval of P09-02, 2026-09-09 | Test support is sufficient without silently bloating the runtime environment. |
| D-232 | All 37 historical Python tests receive a preserved clean-environment baseline and an explicit retained/adapted/superseded/invalid classification before reorganization. | Quinton approval of P09-03, 2026-09-09 | Existing regression knowledge cannot be silently deleted or weakened. |
| D-233 | Strict test markers define a fast ordinary default with no network, external drive, licensed data, MPS, browser download, or expensive model requirement. | Quinton approval of P09-04, 2026-09-09 | Routine verification remains predictable and fails on unknown test scope. |
| D-234 | Pure logic and contracts use exact positive/negative schema, canonical-serialization, hash, and cross-record invariant tests. | Quinton approval of P09-05, 2026-09-09 | Incompatible but superficially plausible records fail before expensive work. |
| D-235 | Image geometry is tested first with generated NIfTI/affine fixtures, then with explicitly selected local-real overlays and round trips; requested real-data prerequisites fail clearly rather than silently skip. | Quinton approval of P09-06, 2026-09-09 | Synthetic precision and real-library behavior are both covered without making the fast suite data-dependent. |
| D-236 | Software verification and scientific model evaluation remain separate; tests cover execution, lineage, finiteness, shape, and controlled learnability while Plan 06 owns performance claims. | Quinton approval of P09-07, 2026-09-09 | Legitimate experimental variation cannot masquerade as a software regression. |
| D-237 | Metric implementations are checked against independently hand-computed golden cases, including empty, positive, negative, multi-lesion, failed, abstained, and clustered cases. | Quinton approval of P09-08, 2026-09-09 | Production metric code cannot validate itself. |
| D-238 | UI unit/component testing uses Vitest, React Testing Library, user-event, and jsdom; NiiVue is mocked only at this layer and assertions target user-visible state. | Quinton approval of P09-09, 2026-09-09 | Fast UI tests remain stable without pretending mocked WebGL proves rendering. |
| D-239 | One Playwright Chromium critical path with axe checks complements manual Chrome/Safari NiiVue, keyboard, zoom, and alignment review. | Quinton approval of P09-10, 2026-09-09 | Real-browser evidence stays proportionate to a single-user Mac workstation. |
| D-240 | Producer/consumer parity is tested across static/FastAPI case packages, Python/React schemas, training/inference preprocessing, evidence responses, review append/reload, and report derivation. | Quinton approval of P09-11, 2026-09-09 | Individually passing components cannot hide boundary incompatibility. |
| D-241 | Deterministic failure injection covers orchestration interruption, retries, stale cache, mount/disk loss, writer conflict, partial append, resume, and framework-state loss. | Quinton approval of P09-12, 2026-09-09 | Long-running workflows prove recovery behavior before real failures. |
| D-242 | Retrieval tests separate corpus/query/rights contracts, known-relevance retrieval metrics, and claim/citation/refusal integrity; live NCBI results and generative judges are excluded from the required fast oracle. | Quinton approval of P09-13, 2026-09-09 | Network drift or fluent output cannot conceal retrieval defects. |
| D-243 | Only generated/synthetic and non-sensitive golden fixtures are committed; local-real fixtures use root aliases and content-hashed manifests, while CTs, labels, article text, checkpoints, notes, and absolute paths stay out of Git/CI. | Quinton approval of P09-14, 2026-09-09 | Test evidence cannot become a privacy, license, size, or portability incident. |
| D-244 | Every assertion declares exact, tolerance-based deterministic, seeded/statistical, or manual semantics with recorded rationale. | Quinton approval of P09-15, 2026-09-09 | MPS variability receives honest bounds rather than impossible bitwise claims or unexplained looseness. |
| D-245 | Requirement/risk/contract coverage is the quality gate; line and branch coverage for pure capstone modules is diagnostic and has no repository-wide target percentage. | Quinton approval of P09-16, 2026-09-09 | Easy high-coverage code cannot hide untested leakage, geometry, metric, or persistence risks. |
| D-246 | Minimal GitHub Actions begins only after local fast suites pass and uses Python 3.12, Node 24, least permissions, locked installs, and synthetic/public controls; local Mac evidence remains authoritative for MPS, real data, NiiVue, and release. | Quinton approval of P09-17, 2026-09-09 | Public CI adds portability evidence without receiving protected artifacts or overstating Linux/CPU coverage. |
| D-247 | Every formal test run records machine-readable results, counts, durations, environment/code/config/fixture identities, and relevant hashes; unexpected skips, XPASS, collection errors, or unowned warnings fail release. | Quinton approval of P09-18, 2026-09-09 | A green summary cannot omit unavailable or unexecuted requirements. |
| D-248 | Verification uses staged gates: fast before material change acceptance, relevant integration/local-real before publication or expensive runs, and the full matrix before G7/G8. | Quinton approval of P09-19, 2026-09-09 | Testing remains timely without postponing all integration until stabilization. |
| D-249 | High-impact fixes receive regression tests when feasible; flaky-test quarantine requires an issue, owner, reproduction effort, expiry, and exclusion from required pass claims. | Quinton approval of P09-20, 2026-09-09 | Failures become durable knowledge rather than recurring surprises or indefinite exceptions. |

### Plan 10 and living-notebook approval — September 18

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-250 | P10-01 through P10-24 are approved as the storage, artifact, retention/recovery, environment, preflight, and compute design. | Quinton's full Plan 10 approval, 2026-09-18 | Record `Approved design; gated`; exact roots/capability tests, backup target/budget, encryption choice, and environment evidence remain pending. No bulk migration, deletion, reformat/encryption, paid compute, or remote upload is authorized merely by design approval. D-210 remains open. |
| D-251 | Plan 10 readiness is staged: foundation setup, per-experiment readiness, and full delivery/reproduction readiness before G8. | Quinton approval of the walkthrough refinement, 2026-09-18 | Bounded setup produces its own readiness evidence; safe early imaging work does not wait for a completed retrieval/UI system. Each run's scientific and operational gates still apply, and D-045 still requires the Plan 04 explanation and explicit implementation authorization. |
| D-252 | `docs/experiments.md` remains the living notebook: plan every experiment before execution, record every attempt/outcome, and explain the evidence behind the next experiment. | Quinton instruction accompanying Plan 10 approval, 2026-09-18 | New `CAP-EXP-NNN` entries link immutable experiment/run/evaluation evidence and motivating parent experiments. Preserve old text and future ideas, but replan selected ideas under current cohort/holdout/no-model-reuse rules. Keep failed/null results and append corrections; never rewrite the original hypothesis or bar after results. |

### Plan 11 lightweight stakeholder process — September 18

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-253 | Plan 11 remains one living outreach/session/findings document. Quinton owns scheduling; a radiologist is preferred, with a role-appropriate expert/proxy or asynchronous fallback. Prepare a 30–45-minute task walkthrough, confirm/fallback by Week 5, conduct the main review in Week 7, and implement only Quinton-approved bounded findings. | Quinton's full approval of the Plan 11 walkthrough, 2026-09-18 | Outreach cannot block data, training, retrieval, or initial UI development. Actual feedback may inform later code. Record the real participant role and limitations; neither a planned meeting nor proxy feedback counts as completed radiologist or clinical validation. Actual session/fallback evidence remains required for the stakeholder deliverable. |

### Plan 12 approval and implementation-start reconciliation — September 18

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-254 | P12-01 through P12-12 are approved: incremental integration, exact release identity, one-way held-out evaluation, defect-driven invalidation, required test evidence, role-honest stakeholder feedback, safe packaging/recovery, and explicit delivery sign-off. | Quinton's full Plan 12 approval, 2026-09-18 | All twelve numbered designs are approved. No release, scientific result, verified runtime, or submission is implied. Follow `IMPLEMENTATION-START.md` for the bounded starting sequence. |
| D-255 | G0 has design and executable-verification checkpoints. Approved designs permit scoped environment/fixture/test setup that produces verification evidence; full G0 still requires both. G2 gates PANORAMA/mixed-source work, not PanTS-only baseline preparation/training with its own prerequisites. | September 18 prerequisite reconciliation under D-047/P05-03, D-251, and approved P12-01/P12-03; no scientific scope change | Remove circular startup gates without waiving real data, test, resource, or Plan 04 explanation/authorization requirements. Retrieval and stakeholder availability do not block unrelated early imaging work. |

### Local drive encryption choice — September 18

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-256 | Keep `PROWL-Data` in its current unencrypted APFS configuration; encryption is not a setup prerequisite. | Quinton's explicit direction, 2026-09-18 | No encryption, reformat, or filesystem conversion is requested. Root/capability verification and independent backup target/budget remain pending. Source-rights, privacy, and any future remote-transfer safeguards are unchanged. This resolves the encryption choice left open at D-250. |

### Unusable old drive and acquisition priority — September 19

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-257 | Treat `JHU-PanTS` as unusable for source and backup purposes; fresh PanTS/PANORAMA acquisition is the active route, prioritized alongside or immediately after the clean test foundation. | Quinton reports no read/write access and requests fresh downloads, 2026-09-19 | Do not wait for or attempt old-drive recovery. Verify the new drive, independent backup target/budget, source pins/rights, integrity, and space before bulk transfer. Preserve retained controls and historical results. See `operations/DATA-ACQUISITION-QUEUE.md`. No training, reformat, deletion, paid compute, or remote upload is implied. |

### Bounded storage setup approval — September 19

| ID | Decision | Rationale/source | Consequence |
|---|---|---|---|
| D-258 | Create the new `PROWL/` workspace on the verified external volume and `PROWL-Backups/` on the internal SSD. Approve the sub-16-MiB filesystem/control-restore diagnostic and a 20-GiB backup cap with a 100-GiB internal free-space floor. | Quinton explicitly approved the presented setup and checks, 2026-09-19 | Preserve all existing recovery files. Back up selected records/keepers, not raw datasets or caches; never delete evidence automatically to fit the budget. After successful checks, verify publisher source pins/rights/integrity/space before downloads. This authorizes neither production Plan 04 code nor reformatting, drive-disconnect tests, historical migration, training, or paid/remote compute. |

Execution evidence: [September 19 storage setup](operations/STORAGE-SETUP-2026-09-19.md).
The bounded checks and initial synthetic restore passed; the approved roots/backup budget are
configured. PanTS archive acquisition started; extraction, source registration, scientific runs,
production Plan 04 code, and full operations qualification remain outside that completed checkpoint.

## Provisional defaults

### September 18 user-directed recovery and calendar update

- The official ten-week course begins **2026-10-05**, confirmed by Quinton. September 7 remains the
  planning baseline. Relative week commitments and the Week 9/10 scope protections are unchanged.
- Quinton accepts downloading PanTS again if `JHU-PanTS` is unavailable. Recovery of that drive is
  optional and is removed from Plan 10's prerequisites. A fresh source snapshot must be pinned and
  reconciled against retained metadata and accepted base split hashes; old raw-byte equivalence is
  not asserted without comparable source checksums.
- The suspect old drive is excluded from backup assumptions. A healthy independent destination must
  be selected for keeper/review/release evidence. Bounded internal-SSD copies are a candidate after
  capacity review; a second folder on `PROWL-Data` is not an independent backup.
- Later in the September 18 session Quinton approved the full Plan 10 design and staged readiness
  (D-250/D-251), and reaffirmed the living experiment notebook (D-252). Setup/tests are still pending;
  design approval does not assert physical readiness or settle the remaining deployment choices.

| ID | Default | Why it is the current default | What could change it |
|---|---|---|---|
| D-102 | Use a local, reproducible vector index for the retrieval prototype. | Keeps corpus and evaluation controllable; no service dependency. | Scale, latency, persistence, or filtering requirements shown by the retrieval plan. |
| D-103 | Treat PubMed abstracts and permitted PMC text as the initial corpus. | Clear identifiers and citation path; matches approved scope. | Licensing/access review or question-set coverage demonstrates a different boundary is needed. |
| D-104 | Preserve old experimental results and checkpoints as reference evidence, not initialization targets. | Maintains scientific history while honoring the no-reuse commitment. | Only the professor can change the approved no-reuse boundary. |
| D-105 | Keep the imaging critical path independent from retrieval progress. | Retrieval is supporting scope. | No expected change; integration remains at the UI contract. |
| D-106 | Evaluate Prefect 3 locally first, with a four-hour selection trial and contract-compatible repository-runner fallback. | P04-01 approved September 8; reaffirmed after walkthrough and alternatives discussion September 20 | Temporary local services are acceptable if understood/tested; no cloud or manually maintained server required. This clarifies P04-02/D-036, not a final tool selection. Test safety, independence, and actual benefit; D-201 remains open until evidence selects the tool. |

## Open decisions

| ID | Question | Options to evaluate | Required evidence | Deadline |
|---|---|---|---|---|
| D-201 | What runs the workflow DAG? | Small in-repo runner; Prefect; another local orchestrator | Required stages, retry/state semantics, setup cost, testability, provenance, resume behavior | End of Week 1 |
| D-202 | Which pgvector configuration and embedding configuration meet Plan 07 requirements? | Exact search plus representative HNSW first; expansion to other index/precision settings only on measured triggers; named embedding candidates still need approval | P4a platform/resource/filter/exact-reference evidence, P4b contract/rebuild evidence and P8/P9 embedding/retrieval evaluation; D-260 already selects the engine | Before published index build and configuration freeze |
| D-205 | Which model comparison is run in Week 6? | Architecture, initialization, cascade choice, false-alarm method, ensemble/distillation if justified | Week 5 baseline error analysis and preregistered decision bar | After G4, before compute |
| D-208 | What is the reviewer ordering score? | Calibrated lesion probability, volume/probability rule, learned gate, composite | Baseline curve, calibration, interpretability, user need | After Week 5 baseline |
| D-210 | Is rented/cloud compute needed? | Local MPS; available CUDA machine; rented GPU | End-to-end timing, upload/storage burden, reproducibility, cost ceiling | Before first run local estimates cannot support |
| D-211 | Literature persistence answered by D-260; any broader relational scope remains unapproved | Literature: rebuildable PostgreSQL operational layer. Imaging remains file-first | Broader scope requires a new measured need and explicit decision; D-401 remains intact | Revisit broader scope only if justified |

## Deferred work

| ID | Item | Revisit condition |
|---|---|---|
| D-301 | Tumor-type classification | Core complete, tests pass, Weeks 9–10 untouched, and labels/claims are appropriate. |
| D-302 | Level 5 multi-structure model | Core autonomous workflow complete and evidence shows surrounding anatomy is the best use of remaining time. |
| D-303 | Managed vector service | Local index demonstrably fails a requirement. |
| D-304 | Cloud persistence or object storage | Local workflow or compute portability demonstrably requires it. |
| D-305 | Browser-based contour editing | Stakeholder prioritizes it after the committed review-event workflow works. |
| D-306 | Johns Hopkins external submission | Benchmark-compatible autonomous package passes internal gates and schedule permits. |

## Superseded or rejected decisions

| ID | Older idea | Why it is not active |
|---|---|---|
| D-401 | Mandatory Postgres/Neon architecture | Approved appendix explicitly makes relational persistence optional and file artifacts sufficient. |
| D-402 | Mandatory synthetic-report extraction/supervision | Investigation found PanTS reports are template-derived and not independent evidence; approved scope instead uses external literature retrieval. |
| D-403 | MSD Task07 as an independent second dataset | Investigation found it is already represented within PanTS; PANORAMA is the approved second imaging source. |
| D-404 | Level 5 as committed capstone scope | Removed during proposal refinement; model experimentation remains flexible. |
| D-405 | Previous course checkpoint as the capstone starting model | Conflicts with the approved no-reuse boundary. |
| D-406 | Largest-connected-component filtering as the default lesion cleanup | It destroys additional lesion components and is incompatible with tumor-wise sensitivity. Any future use must be explicit and metric-specific. |
| D-407 | Apache Airflow as the capstone workflow orchestrator | Quinton explicitly rejected Airflow on 2026-09-08. The proposal requires DAG behavior, not this product; Plan 04 evaluates Prefect locally with a small repository runner fallback. |

## How to add a decision

### September 28 literature database approval

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-260 | PostgreSQL + pgvector for Plan 07 literature only; canonical versioned files remain authoritative and the database is rebuildable. | Quinton's explicit architecture approval and accepted handoff; operations/POSTGRES-PGVECTOR-DECISION-2026-09-28.md | Supersedes earlier SQLite/LanceDB engine direction, not imaging file-first contracts or D-401's project-wide boundary. Planning approved; no installation, acquisition, Tier 2 expansion or implementation launch. |

### September 28 explicit binary-decoding approval

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-259 | Approve `pants-semantic-binary-atol1e-6-v1`: after NIfTI scaling, validate every voxel within absolute 1e-6 of 0/1, relative tolerance zero, and return a new binary array; reject all other/nonfinite values. | Quinton's explicit September 28 approval; see data/BINARY-DECODING-APPROVAL-2026-09-28.md | Originals preserved. No automatic allowed uses, disease negatives, training launch, bulk rewrite or release authorization. Historical candidate policy remains distinct for replay. |

### September 28 Plan 07 planning-set approval and integration

Authority: Quinton confirmed the approved planning set in the integration conversation and
directed Codex to execute the handoff in the final approval entry of
[`retrieval/planning/RUNNING-LOG.md`](retrieval/planning/RUNNING-LOG.md).
[`SCOPE.md section 12`](retrieval/planning/SCOPE.md) groups A/B are approved as labelled;
group C execution permissions are not granted. This supplements D-260, not the historical
proposal/appendix. The exact reviewed planning hashes are in the integration handoff.

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-261 | Approve NLM 2026 PubMed baseline plus ordered updates to a pinned cutoff as the intended acquisition route, followed by local versioned selection; retain E-utilities for bounded checks. | L-03, confirmed by Quinton September 28 | Clarifies D-077 approved services. Add/replace/delete event provenance and replay required; no run S/A/B signed, no download authorized. |
| D-262 | Freeze embedding arrays as canonical hashed artifacts; rebuild the operational store by loading those exact artifacts. | L-08, confirmed by Quinton September 28 | Regeneration after loss creates a new artifact/build identity and affected evaluation must be reverified. No model selected or pull authorized. |
| D-263 | Approve external PROWL-Data literature database placement as a direction to test under P4a, with the shared-failure-domain and backup limits in SCOPE 5.7. | L-09, confirmed by Quinton September 28 | Live DB and canonical literature share external_primary. No mount/root activation or storage-layout selection yet. Shared 20 GiB backup cap/100 GiB internal floor unchanged; literature allocation awaits measurement/approval. |
| D-264 | Approve the revised Plan 07 design and phases, PMC Cloud XML route with per-article rights, Docker and PostgreSQL ts_rank_cd prototype candidates, two-stage selection/confirmation reserve/inspected-PMID ledger, and the separate encrypted held-out-container lifecycle. | SCOPE 12A and L-04/L-10/L-11/L-12/L-15, Quinton September 28 | Files authoritative; imaging unchanged; no global Docker change, installation, database start, container creation, acquisition, dependency or Plan 04 coding permission. P3 needs the revised packet and Quinton dispatch. L-13/L-14 models remain proposed. P1 needs and P2 seeds remain Quinton's work. |
| D-265 | Approve SCOPE 12B as provisional experimental controls: English with missing-language retention/flag; 2000–cutoff with missing dates retained/flagged; WORKFLOW cap 500 after hard exclusions; seed recall >=90%; confirmation/census >=60% relevant+partial and >=40% relevant; 3 policy revisions, 2 confirmation rounds; starting context budget 2,000 tokens; Tier 1 and database+recovery ceilings 100 GiB each. | SCOPE 12B, Quinton September 28 | Change by recorded decision. Ceilings are not reservations/expected sizes or run signatures. Runtime <=15% of recorded RAM (~9.6 GiB), synthetic hybrid p95 <=500 ms at 100k passages, <=10% synthetic MPS slowdown remain proposed trial bars to measure in P4a, as explicitly qualified in the approved table. |

**Proposed D-085 amendment — decision pending:** add span-hit recall@k and separately
reported delivered-span recall, concept coverage and token count under a named/pinned
tokenizer and context budget. Source/passage recall@1/3/5/10 and MRR remain official.
Span coordinates use immutable normalized representation hashes and half-open Unicode
code-point offsets; direct credit requires complete containment. Synthetic implementation
may demonstrate the proposal under the dispatched P3 packet, but cannot promote these
metrics to official selection/release criteria. See PHASES P7 and SCOPE section 10.

Add the question before implementing the choice. Record the selected option, evidence, date, affected
plans, and migration impact. If a locked decision appears wrong, stop and reconcile it with the
approved sources or professor rather than silently overriding it.


### September 28 protected membership and purpose-specific qualification

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-266 | Keep original membership permanent, make permission purpose-specific, and allow training only through a frozen, positively qualified subset. Preserve original source data and accepted base split membership; retaining a case never automatically grants permission to consume it. Qualified unusual cases remain available for later appropriately planned experiments. | Quinton explicitly reaffirmed the previously agreed principle and instructed Codex to lock it on September 28, 2026. | Policy approved. Exact schema representation, source-completeness scope, qualification evidence and implementation packet still require specification/review. No case promoted, hold resolved, split reassigned, G1 waived or training launched by this decision. |

Implementation planning: [membership and eligibility design](data/PROTECTED-MEMBERSHIP-AND-ELIGIBILITY-PROPOSAL-2026-09-28.md)
and [training readiness phases](operations/TRAINING-READINESS-IMPLEMENTATION-PLAN-2026-09-28.md).
The principle is settled; subsequent planning defines its enforcement rather than reopening it.


### September 28 qualification versus model difficulty

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-267 | Qualification establishes interpretable, permitted, purpose-correct inputs, not easy examples. Do not exclude cases solely for low contrast, noise, artifacts, unusual anatomy, target size, verified protocol/spacing variation, documented annotation uncertainty or poor model performance. Record those characteristics for sampling and evaluation. | Quinton explicitly approved this clarification and requested documentation on September 28. | Unsupported target meaning, unusable geometry, protected roles and unresolved applicable holds still block the affected use. Verified nonempty pancreas is an initial pancreas-present smoke selection condition, not universal eligibility. Tiny-set fitting is a wiring/learning check, not generalization evidence. Later matched with/without-qualified-unusual training comparisons use the same ordinary/unusual evaluation groups under protected-role rules. Exact groups, uncertainty treatment and budgets remain to be specified. |

See the [qualification checklist](data/LOCALIZER-QUALIFICATION-CHECKLIST-2026-09-28.md).
D-267 supplements D-266; neither decision promotes any actual case or authorizes a run.


### September 28 staged qualification approval

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-268 | Adopt staged qualification: broad source and split verification, detailed qualification of every consumed case, then expansion through new frozen cohorts. Difficult cases remain candidates throughout under D-267; original membership and purpose-specific permissions remain governed by D-266. | Quinton explicitly approved this recommendation on September 28, 2026. | Verification strategy approved. Exact required inventory/integrity/duplicate checks, schema changes, read scope and resource budget must be specified in the implementation packet. No blanket exemption from G1/source-integrity requirements, real-case promotion, source job or training launch. Unrelated annotations need not all become eligible before a pancreas-only smoke. |

The [qualification checklist](data/LOCALIZER-QUALIFICATION-CHECKLIST-2026-09-28.md) records the
approved staging direction and remaining technical specifications. Do not reopen D-266–D-268 as
unsettled principles; resolve their concrete implementation and evidence requirements.


### September 28 bounded publication implementation authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-269 | Implement the shared artifact publication controls needed by S4 and the cohort registry/resolver; publish and verify the exact two-case localizer cohort after tests pass. | Quinton replied “Great, move onto the next” immediately after the handback named shared Plan 04 publication controls and their coding authorization as the next step. Codex stated this narrow interpretation before work. | Cohort artifact writes on the registered PROWL-Data artifact root, using a separate hash-pinned scoped capability over the unchanged setup registry. No Prefect spike/install, whole-DAG dispatch, literature work, source activation, raw-source change, training, deletion, Git push or global scientific-run enablement. |

The [scoped capability](operations/COHORT-PUBLICATION-CAPABILITY-2026-09-28.json) pins the current
registry and volume. It permits the cohort artifact area only; it does not silently broaden setup-only
root access for other consumers. The Plan 04 explanation gate was already completed on September 20.


### September 28 localizer loader/preprocessing authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-270 | Implement the dedicated frozen-cohort loader and deterministic pancreas-only preprocessing; verify the two consumed cases through a scoped read-only source binding and bounded native diagnostic. | Quinton explicitly requested “move onto the next with the loader and preprocessing.” | Exact frozen 3/26 cohort, four CT/pancreas files; no lesion input, raw rewrite, generic source activation, persistent cache, model training or literature decision approval. Codex selected a versioned engineering recipe (RAS, 3 mm, HU [-100,300], zero-pad minimum 96³, no crop/augmentation) and will report its measured effect before a training recipe is frozen. |


### September 28 localizer learning/recovery implementation authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-271 | Implement the dedicated localizer model-input adapter, synthetic learning and checkpoint save/reload/recovery slice. | Quinton explicitly requested these three next steps. | New CPU synthetic diagnostics and tests, internal retained evidence and shared non-overwriting publication controls. No real CT training, MPS launch, production checkpoint-root activation, pretrained weights, literature approval or external messaging. Engineering settings are recorded in the plan/handback; real smoke recipe and resource limits remain to freeze. |

See [plan](operations/LOCALIZER-LEARNING-PLAN-2026-09-28.md) and
[handback](operations/LOCALIZER-LEARNING-HANDBACK-2026-09-28.md).


### September 28 bounded resource profiling authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-272 | Run the bounded localizer resource profile on native MPS with synthetic 96³ patches and shape-matched full volumes, measuring compute, memory and diagnostic checkpoint reload. | Quinton explicitly requested resource profiling after the learning/recovery handback. | Nine total updates, four full-volume passes, 600 s deadline, 16 GiB limits, 256 MiB internal diagnostic output cap, AC monitoring and no automatic CPU fallback. No real-data training, external write/source read, production root activation, remote compute or literature decision. Result supports local feasibility for the tiny smoke; full D-210 remains open. Candidate real-run limits are recommendations pending the concrete run plan. |

See [resource profile evidence](operations/LOCALIZER-RESOURCE-PROFILE-HANDBACK-2026-09-28.md).


### September 28 qualified-input MPS connection and recovery authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-273 | Connect the frozen qualified cohort to MPS; verify production checkpoint publication, independent backup and consumer recovery; finalize the smoke launch plan. | Quinton explicitly requested all three steps after the resource profile. | Exact cases3/26/four source files for forward-only verification, separately labeled synthetic optimizer rehearsal, scoped new primary/checkpoint and internal backup/restore areas under the pinned registry/UUIDs. At most1GiB new bytes per domain, existing20GiB backup cap/100GiB internal floor,600s/16GiB verification limits. No real-data optimizer update or global root activation. Final training-loop/evaluation coding is within the requested connection scope; actual launch remains a separate review after it is complete. |

[Capability](operations/LOCALIZER-RUN-CAPABILITY-2026-09-28.json),
[verification](operations/LOCALIZER-RUN-BRIDGE-HANDBACK-2026-09-28.md), and
[CAP-EXP-001 launch design](operations/CAP-EXP-001-LAUNCH-PLAN-2026-09-28.md).


### September 28 bounded executor completion authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-274 | Finish the bounded training loop, before/after evaluation, native exports, terminal checkpoint preservation and a concrete pinned launch request; review Claude's P2 handback. | Quinton explicitly requested “finish the bounded training loop and before/after eval” with necessary supporting work and Claude review. | CPU regressions and bounded synthetic MPS end-to-end verification in the existing D-273 storage areas, 600 s / 16 GiB / 1 GiB new bytes per domain per rehearsal. Preserve attempts and independently restore the terminal bundle. Actual CAP-EXP-001 launch remains the final specific review under the agreed D-273 sequence. No real optimizer update, global root activation, literature download/signature, new seed approval or external message. |

[Executor plan](operations/LOCALIZER-EXECUTOR-PLAN-2026-09-28.md),
[evidence](operations/LOCALIZER-EXECUTOR-HANDBACK-2026-09-28.md), and
[Claude P2 review](retrieval/CODEX-P2-OUTLINE-APPLICATION-REVIEW-2026-09-28.md).

### September 28 exact CAP-EXP-001 launch authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-275 | Launch the exact prepared CAP-EXP-001 request once, then inspect before/after results and independent backup recovery. | Quinton: “Yes, run the exact prepared run. Great work on everything else.” | Request SHA `9b54a25d3ad014ca325464d35046496357f2e7969c9f4b2ddbd04e1ba2196452`; cases3/26, scratch,100 updates,600s update/1,200s total,16GiB, existing1GiB scoped storage envelope. No extension, automatic retry, checkpoint reuse or global roots activation. |

Recorded authorization: `outputs/prowl/CAP-EXP-001-AUTHORIZATION-D275.json`, SHA
`d7d5adfb333a1bb79364676b1a460f465eb1871d58c2d5a0d768ef9ee5520207`.
Prepared controls were rechecked unchanged before launch; the pending record remains preserved.

### September28 optimization investigation authorization

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-276 | Investigate CAP-EXP-001 optimization using retained checkpoints, exact crop replay, probability/loss decomposition and local logit-gradient diagnostics. | Quinton requested “Investigate the optimization behavior and anything else that you deem necessary/important.” | Exact two qualified cases and retained five checkpoints, read-only model/source access, no optimizer updates or new training run. Native diagnostic600s/16GiB/256MiB internal output under existing root/power constraints. Preserve original experiment and publish separate findings. |

See [bounded plan](operations/LOCALIZER-OPTIMIZATION-INVESTIGATION-PLAN-2026-09-28.md).

### September28 overnight implementation and bounded experiments

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-277 | Implement and verify the proposed loss-balance comparison, prepare its exact controls, execute a bounded CAP-EXP-002 experiment, and continue only with evidence-supported reliable work within the local project. | Quinton: “You have free reign to work for as long as you want. Dont feel the need to check back ... implement as much as you can reliably.” This follows the explicit CAP-EXP-002 recommendation. | Preserve earlier runs; freeze each concrete experiment before compute. Initial real comparison remains two qualified train cases,100 updates,600s update/1,200s total,16GiB,1GiB new bytes per domain. No paid/remote compute, source rewrite, cohort expansion without qualification, publisher contact, literature decisions, automatic unbounded training, or destructive cleanup. Further work must retain bounded plans/results and stop when evidence or resources warrant review. |

### September28 controlled overnight follow-up selection

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-278 | After CAP-EXP-002's overprediction/null learning result, test LR0.0003 against0.003 with the balanced objective and all other factors fixed. | Codex's bounded experimental choice under Quinton's explicit D-277 overnight autonomy; not represented as a separate user-selected recipe. | CAP-EXP-003 fresh scratch100 updates, same two cases, same seed/crops/horizon;600s update/1,200s total,16GiB and existing storage limits. Verify route/config binding and native operation, freeze controls and log results before any further choice. |

### September28 final overnight duration comparison

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-279 | Test300 fresh updates of the lower-LR balanced recipe after CAP-EXP-003 passed the minimal indicator but retained large false-positive regions. | Codex's bounded experimental choice under Quinton's D-277 overnight autonomy. | CAP-EXP-004 only; same cases/seed/loss/LR, cosine horizon300 matched to update budget. Cadence75 keeps five checkpoint/evaluation stages. Existing600s update/1,200s total,16GiB,1GiB/domain limits stay unchanged. No continuation of old weights or automatic extension. Final planned overnight training action, then review/handoff. |

### September 29 stronger localization and cohort progression

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-280 | Implement stronger localization diagnostics, address excess foreground with controlled evidence, then prepare varied qualified training and separate validation cohorts. | Quinton explicitly requested this next sequence on September 29. Numerical engineering targets and experimental settings are Codex choices under this scope, not permanent user-approved clinical criteria. | Preserve historical runs/memberships; first read-only CAP-EXP-004 diagnostic is two cases/two forwards, 600 s/16 GiB/256 MiB local output. Freeze each further experiment before compute; new cases require positive purpose-specific qualification and role-aware cohort resolution. No publisher-test tuning, source rewriting, literature edits or external messages. |

[Target and sequence](operations/LOCALIZATION-TARGET-2026-09-29.md).

### September 29 role-safe cohort expansion implementation

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-281 | Continue the role-safe qualification/cohort implementation and bounded candidate evidence work defined after D-280. | Quinton: “Great, continue onto what you think is best.” | Preserve old contracts/runs; add explicitly versioned train-target/validation-reference qualification and operation-checked cohort consumers. Exact candidate content job remains bounded by the recorded packet and must be tested/pinned before source reads. No automatic promotion, publisher-test use, source rewrite, silent candidate replacement or training before qualified inputs and a frozen run. |

### September 29 evidence-bound expansion publication

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-282 | Bind D-281 evidence into purpose-specific qualification and frozen separate development cohorts. | Quinton: “Great, move onto the next now.” after the qualification/freeze recommendation. | Exact 28 candidates; preserve all original membership, case 6350 hold and difficulty observations. Metadata-only publication under existing cohorts capability; no source reads, training, release clearance or silent replacement. [Scope and assessment](data/LOCALIZER-EXPANSION-QUALIFICATION-2026-09-29.md). |

### September 29 expanded input and preprocessing verification

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-283 | Implement and verify the expanded role-safe loader and versioned preprocessing, then run the bounded 27-case input diagnostic. | Quinton: “Great, lets move onto the next then.” after the D-282 freeze and next-loader recommendation. | Exact frozen 16 train/11 validation; 54 CT/pancreas files, no held-case substitution. Preserve v1; pin/test controls before source reads. 1 GiB compressed/4 GiB expanded total, 16 GiB RSS, 20 minutes, 256 MiB evidence, 100 GiB internal free floor. No model training, source rewrite, final-test payload, literature work or Git publication. |

### September 29 expanded runner integration

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-284 | Continue expanded scratch-runner integration, bounded processed RAM reuse and resource/checkpoint qualification. | Quinton: “Great, move to the next.” after D-283. Implementation choices by Codex. | Preserve v1 and exact frozen 16/11 roles; synthetic updates only during verification, real cohort forward-only. 512 MiB cache, 54 source files, 20 minutes/16 GiB/256 MiB evidence. Freeze next run separately; no CAP-EXP-005 launch inferred. See operations/EXPANDED-RUNNER-PLAN-2026-09-29.md. |

### September 29 expanded launch machinery

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-285 | Finish expanded loop, localization metrics, native prediction exports and interruption handling; test and freeze exact CAP-EXP-005 request. | Quinton explicitly requested these tasks after D-284. | Synthetic execution only in this preparation slice; preserve frozen 16/11 and old runtime. Proposed real run:288 fresh updates,600s update/1200s total,16GiB RSS. No real launch, source mutation, literature edits or Git publication. |

### September 29 CAP-EXP-005 launch

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-286 | Launch the exact frozen CAP-EXP-005 request once. | Quinton: “Yeah, go for it.” in response to the exact-run approval question. | Request SHA `2fa5f7f20916fb047ddcc54c3aede63e5f1c57566227cec1ef07a1d9756ae456`;288 updates,16 train/11 validation,600s update/1200s total,16GiB. No automatic retry/extension, source changes or test-set use. |

### September 29 sustained localizer experiment

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-287 | Implement and verify the bounded sustained-run extension, then freeze and launch CAP-EXP-006 once. | Quinton: “Great. I agree. Good call. Move onto the next experiment then.” following the sustained-training recommendation. Exact run parameters selected by Codex. | Same16/11, fresh initialization,2400 updates/150 per train case, stretched cosine horizon;50min update/60min total,16GiB, unchanged storage/input caps. Checkpoint backups during training, full-role evaluation and independent final recovery. No additional runs, automatic resume/extension, eligibility changes, test data, retrieval edits or Git publication. See operations/CAP-EXP-006-LAUNCH-PLAN-2026-09-29.md. |


D-287 outcome: CAP-EXP-006 completed2400 updates; result is a tradeoff, not an accepted localizer
improvement (validation Dice gain passes but recall/box-coverage safeguards fail). All35 artifacts
independently restored, probe difference0; no pending run or automatic continuation. See
[results](operations/CAP-EXP-006-RESULTS-2026-09-29.md). The next audit/cohort recommendation is
not authorization for another training experiment.

### September29 coverage inspection

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-288 | Inspect CAP-EXP-006 coverage failures and evidence needed for the next experiment. | Quinton: “Great, continue with the inspection and anything else you deem important.” | Codex-selected bounded CPU audit of saved005/006 predictions versus original qualified27 source pairs;54 source files,20min/16GiB,256MiB evidence. No training, model inference, policy tuning, source rewrite, eligibility change, test-set use or Git publication. See operations/CAP-EXP-006-COVERAGE-INSPECTION-PLAN-2026-09-29.md. |


D-288 outcome/amendment: native-grid audit confirms validation recall failure (0.9492→0.4594),
with no checked source/export geometry mismatch. After the frozen source job completed, a separate
metadata-only derivation exposed padding in the legacy crop-size denominator. Codex added tested
source-crop geometry and evaluator fields under the user's “anything else you deem important”
instruction; no historical result is rewritten or new ROI policy selected. No additional raw reads,
inference or training followed that correction. See the inspection report and source-crop correction.
The128/48 candidate budget/policy is a Codex proposal, not an approved executable cohort.

### September 29 broader candidate preparation

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-289 | Implement reproducible 128 train/48 development-validation candidate selection and prepare a separate probability audit. | Quinton: “Great, continue on.” after D-288; exact candidate budgets and hybrid policy are Codex implementation choices from the written proposal. | Metadata only for selection; retain all28 prior candidates including held6350. No new source-array reads, eligibility promotion, optimizer updates, threshold adoption, retrieval edits or Git publication in this preparation slice. |

D-289 outcome:128/48 metadata candidates published and independently replayed; all28 prior candidates
retained, case6350 still held.1,211 native tests pass. Probability-audit implementation plan written,
not executed or frozen as a runnable request. See operations/LOCALIZER-CANDIDATE-EXPANSION-RESULTS-2026-09-29.md.

### September29 probability diagnostic

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-290 | Implement/test, freeze and execute the fixed CAP-EXP-006 terminal probability audit; prepare new-candidate header checks. | Quinton: “Great, continue” after D-289; exact diagnostic execution scope selected by Codex from the prepared plan. | Existing27 qualified cases only for inference, zero optimizer updates.20min/16GiB/54 files, fixed thresholds, no policy adoption. Header job preparation only for new148 candidates; no qualification or new training inferred. |

D-290 outcome: probability audit completed with exact27-case terminal parity, unchanged weights and
zero updates. Fixed threshold0.01 yields mean validation recall0.6047, insufficient recovery with
increasing crop/foreground size; no threshold selected.1,220 native tests pass. Header job prepared
for148 new cases/296 files, not executed. See operations/CAP-EXP-006-PROBABILITY-AUDIT-RESULTS-2026-09-29.md.

### September29 expanded candidate headers

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-291 | Implement/test, freeze and execute the prepared148-case/296-file header preflight; use observations to plan qualification batches. | Quinton: “Great, continue on.” after D-290. | New candidates only; bounded gzip prefixes and348-byte headers, no voxel arrays.15min/512MiB/20MiB compressed reads/8MiB evidence. No qualification, hold removal, source changes, model inference or training. |

D-291 outcome:296 headers successfully read for148 new pairs; all header grids match.14 CT unit
issues and5 grids over64M voxels remain explicit. No array decoding or qualification.1,230 tests.
The15-batch content proposal is planning only, including a proposed96M-voxel diagnostic scope for
five large singletons; current runtime limits are unchanged. See data/LOCALIZER-EXPANSION-V2-HEADER-RESULTS-2026-09-29.md.

### September29 first expanded content pilot

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-292 | Implement/test, freeze and execute batch-01 content/alignment evidence; inspect all16 sheets and measured resources. | Quinton: “Great, move to the next.” after D-291. | Exact16 new train cases/32 files only. Existing20min/16GiB/64M limits; no other batches,96M activation, qualification, cohort publication, model inference or training. |

D-292 outcome: first16-case/32-file pilot complete; all finite CTs, matching grids, nonempty strict-
binary targets. All16 limited alignment sheets reviewed; five boundary contacts retained.41.53s,
peak3.42GiB,1,242 native tests. No eligibility promotion or training. Remaining nine standard batches
and five larger singletons are the next recommendation, not already-active requests. See
data/LOCALIZER-EXPANSION-V2-CONTENT-PILOT-RESULTS-2026-09-29.md.

### September29 remaining content batches

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-293 | Complete nine remaining standard batches/127 candidates, then five separately gated larger cases; review and reconcile evidence. | Quinton explicitly requested this continuation after D-292. | Separate frozen requests, sequential source jobs, unchanged standard budgets. Large singleton96M diagnostic scope only after synthetic resource rehearsal; current model consumer unchanged. No qualification or training eligibility changes. |

D-293 outcome: nine standard batches/127 candidates and five large singletons complete; every job
within budgets. Synthetic96M rehearsal passed before large jobs. All124 available sheets reviewed,
eight empty references retained without coverage acceptance. All176 identities/roles reconciled;
15 CT-unit holds (including6350),8 empty-reference holds, no exact compressed-CT duplicates.153
without automated content holds is not a qualified cohort.1,264 native tests pass. No eligibility
changes or training. See data/LOCALIZER-EXPANSION-V2-CONTENT-RESULTS-2026-09-29.md.

### September29 broader role qualification and freeze

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-294 | Bind D-293 and retained evidence to visible-reference purpose qualifications, preserve all candidates/issues, and publish/replay new role cohorts. | Quinton: “Great, continue on.” after the recommendation to qualify supported cases, freeze roles and profile the expanded inputs. | Expected 113 train/40 development-validation; 23 holds remain, no replacement. Private research use only. Current16/11 consumer unchanged; no source arrays or training in this publication slice. |

Scope and per-case limitations: data/LOCALIZER-EXPANSION-V2-QUALIFICATION-2026-09-29.md.

D-294 outcome:113 training/40 development-validation members positively qualified, published and
independently resolved from the registered cohort area. All176 candidates remain;15 CT-unit and8
empty-reference holds persist, no replacement. All23 D-282 issues and28 annotation identities retained.
Visible-reference scope, difficult/large cases and per-case observations preserved.1,284 native tests.
Lookup and process-local exact-byte/schema validation reuse remove repeated metadata cost without
accepting stale/mutated records; independent processes start unvalidated. No source arrays or training.
See data/LOCALIZER-EXPANSION-V2-FREEZE-RESULTS-2026-09-29.md and the v2 consumer packet.

### September29 broader input/preprocessing readiness

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-295 | Implement/test versioned113/40 input consumer and bounded preprocessing, review transformations and measure resources. | Quinton: “Great, continue onto the next” after D-294 and the306-file loader/preprocessing recommendation. | Exact frozen cases/roles, unchanged3mm image recipe;96M/slab restoration only after synthetic qualification. Preserve holds and old16/11 runtime. No model inference/training or source mutation. |

Execution and resource scope: data/BROAD-LOCALIZER-PREPROCESSING-JOB-2026-09-29.md.

D-295 outcome: exact153 members/306 files verified; all153 limited transformation sheets reviewed.
1,307 native tests pass. Successful jobs total448.307s,peak6.57GiB; measured tensor payload1.07GiB.
No model forwards or updates. Initial callback-report failure occurred before source access; retained
and explicitly recovered under attempt02 after tests/rehearsal. All15 successful requests consumed.
Tiny-boundary cases6110/2727 retain substantial round-trip loss; preserve membership and investigate
representation before training rather than treating nonemptiness as scientific acceptance. Current
qualification/holds and old16/11 runtime unchanged. Results: data/BROAD-LOCALIZER-PREPROCESSING-RESULTS-2026-09-29.md.
Next packet: operations/BROAD-LOCALIZER-RUNNER-PACKET-2026-09-29.md; no launch request.

### September29 tiny-reference investigation

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-296 | Investigate tiny-boundary reference loss with synthetic checks and one new two-label diagnostic comparing3mm,2mm,1.5mm and3mm foreground-center splat. | Quinton: “Great, continue and investigate.” after D-295 findings. | Exactly6110/2727 pancreas labels, no CT/model/source mutation; preserve membership and current recipe. Alternative representations are diagnostic, not adopted training policy. |

Plan: data/TARGET-FIDELITY-PROBE-2026-09-29.md. No training launch request.

D-296 outcome: two-label probe exactly reproduced D-295. Nearest2mm recall0.90441/0.88235;
native1.5mm exact for these1.5mm sources.3mm center splat expands volume2.721×/2.588× and is not
adopted. No CT/model reads/updates;11.806s,1.26GiB;1,312 native tests. All153 header-only projections:
2mm requires up to15.046M output voxels,15 cases exceed current8M;~3GiB payload upper bound.
Recommend a separately qualified uniform2mm candidate/16M output envelope before final broad cache;
this recommendation does not adopt a new training recipe. All membership/holds unchanged. Request
consumed. Results: data/TARGET-FIDELITY-RESULTS-2026-09-29.md.

### September30 uniform2mm candidate qualification

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-297 | Test a separate uniform2mm/16M-output candidate and qualify the exact113/40 cohort through new bounded preprocessing requests. | Quinton: “Great find, continue on.” after the D-296 recommendation. | Synthetic largest-output rehearsal and pilot before continuation;all153 members/23 holds and current3mm recipe preserved. No model forward/training or automatic adoption. |

Execution plan: data/TWOMM-LOCALIZER-PREPROCESSING-JOB-2026-09-30.md.

D-297 outcome: all 153 cases/306 files numerically verified and 153 sheets reviewed. Uniform 2 mm
improves Dice in 148 and recall in 147; all regressions preserved. 1,337 native tests; 6.664 GiB CPU
peak, 2.902 GiB tensor payload. Recommend next bounded runner/resource checks; no final recipe
adoption, cache publication, model forward or training. All 15 requests consumed. See
[data results](data/TWOMM-LOCALIZER-PREPROCESSING-RESULTS-2026-09-30.md) and
[runner packet](operations/TWOMM-RUNNER-READINESS-PACKET-2026-09-30.md).

### September 30 — synthetic physical-context profile

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-298 | Compare 96³ and 144³ synthetic MPS resource cost for the 2 mm candidate using the existing model/loss. | Quinton: “Great work. Lets keep moving” after D-297 and the runner recommendation. | Separate profiler; existing production patch guard unchanged. Two sequential bounded profiles, no real inputs/updates. Cache and real-data profiling remain separate. |

Plan: [context profile](operations/LOCALIZER-CONTEXT-PROFILE-PLAN-2026-09-30.md).

D-298 completed: 96³/144³ synthetic MPS profiles pass; median0.8253/2.6839s per update,
sampled driver2.306/4.822GiB and exact reload probes. 1,345 native tests. Recommend144³ for the next
adapter/cache qualification, not final training adoption. No real reads/updates. See
[results](operations/LOCALIZER-CONTEXT-PROFILE-RESULTS-2026-09-30.md).

### September 30 — persisted cache and patch adapter

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-299 | Implement separate persisted2mm cache and144³ adapter contracts, qualified on synthetic fixtures; prepare real binding from retained evidence. | Quinton: “Great, move onto the next” after D-298. | No raw reads, real cache build or optimizer updates.4GiB payload/64MiB overhead; original consumers unchanged. Fresh real build request remains next. |

Outcome:1,379 native tests; persisted synthetic two-role cache and four exact crop replays.
All153 retained real shapes fit temporary padding ceiling; proposed binding preserves113/40 and23holds.
Sampling excludes extra patch padding but not existing preprocessing padding. See
[full results](operations/TWOMM-CACHE-ADAPTER-RESULTS-2026-09-30.md).

### September 30 — real cache construction

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-300 | Build the persisted uniform2mm cache through fresh scoped reads:8-case pilot then145remaining; assemble full113/40 from verified shards. | Quinton: “Great, move onto the next” after D-299. | Exact306files; per-job20min/16GiB; total9GiB project-local scratch outputs and100GiB free floor. Synthetic rehearsal/pilot checks precede continuation. No model or optimizer updates. |

[Execution plan](operations/TWOMM-CACHE-BUILD-PLAN-2026-09-30.md).

D-300 completed: all113/40 cached through8-case pilot and145remaining;306 exact source files.
Final assembly preserves all serialized hashes and target counts without raw rereads. Final cache
2.903GiB;1,388 native tests; peak10.967GiB. All3requests consumed. No model/optimizer updates.
Cache is reproducible project-local scratch; independent checkpoint recovery and zero-update MPS
remain next. [Exact pins and evidence](operations/TWOMM-CACHE-BUILD-RESULTS-2026-09-30.md).

### September 30 — versioned 144³ session readiness

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-301 | Implement the 144³ readiness session and verify synthetic checkpoint recovery on native MPS. | Quinton: “Great, continue onto the next” after D-300. | Synthetic updates only; real cache inference contract, no training launch. Separate state version, scoped independent stores and bounded rehearsal. |

[Plan and limits](operations/TWOMM-SESSION-PLAN-2026-09-30.md). Real zero-update cohort profile remains a subsequent gate.

D-301 completed:1,406 native tests; actual144³ MPS synthetic step2 checkpoint independently restored
with primary reads blocked. Prediction delta0; next-update weights7.45e-9; peakRSS1.028GiB.
No real inputs/updates. [Results](operations/TWOMM-SESSION-RESULTS-2026-09-30.md) and
[next real-cache profile packet](operations/TWOMM-INFERENCE-PROFILE-PACKET-2026-09-30.md).

### September30 — real-cache eight-case inference pilot

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-302 | Implement, test and execute the exact eight-case2mm/144³ cache pilot with native exports and actual-cache-bound independent recovery. | Quinton: “Great, move onto the next pilot plan.” | Zero optimizer updates; no raw source reads. Shared20minute/16GiB/1GiB-output limits, preserved100GiB free floor and backup caps. Remaining145 need a separate request. |

[Plan](operations/TWOMM-INFERENCE-PILOT-PLAN-2026-09-30.md).

D-302 completed: all eight cached cases pass144³ inference/native exports; actual-cache-bound step0
independently restored with probe delta0. 1,437 native tests;57.423s summed workers,4.498GiB peakRSS;
31 package members rehashed. No real updates/raw reads. Request consumed. Remaining145 projected
~8.2minutes including reserve, still a separate tested/frozen request.
[Results](operations/TWOMM-INFERENCE-PILOT-RESULTS-2026-09-30.md).

### September30 — full-cohort inference continuation

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-303 | Implement/test and execute a distinct145-case zero-update continuation, then reconcile all153 cases with the passing pilot. | Quinton: “Perfect, continue on.” after D-302. | Exact107train/38validation complement;20min/16GiB/4GiB-output, unchanged backup/free-space caps. No raw reads, optimizer updates, cohort changes or training launch. |

[Plan](operations/TWOMM-INFERENCE-CONTINUATION-PLAN-2026-09-30.md).

D-303 completed: all145 remaining cases pass;153 unique113/40 members reconciled,153 native exports
and337 package members independently checked. Continuation409.212s plus4.418s recovery,3.031GiB RSS,
probe delta0;1,460 native tests. No raw reads/updates; requests consumed.
[Results](operations/TWOMM-INFERENCE-FULL-RESULTS-2026-09-30.md).
[Next packet](operations/TWOMM-TRAINING-COMPLETION-PACKET-2026-09-30.md) proposes native-reference
scoring and training-loop completion;300updates/45minutes are proposals, not a launch decision.

### September30 — original native-reference scoring

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-304 | Implement/test the target-only native-reference reader and96M-safe metrics; execute one153-label scoring pass through8-case pilot then145. | Quinton: “great continue on” after D-303 and the training completion packet. | Fresh single-use capability/requests;20min/16GiB/128MiB per job. No CT reads, model forwards, optimizer updates, filtering or changed qualifications. |

[Scoring plan](operations/NATIVE-REFERENCE-SCORING-PLAN-2026-09-30.md).

D-304 completed:153 original labels scored in8+145,zero CT/model/update work.1,491 native tests;
79.258s summed jobs,peakRSS5.817GiB. All113/40 retained, including three predictions over old4M
foreground cap and five native grids over old64M cap. Initialized mean native Dice0.001700/0.002053,
ROI0/113 and0/40; no learning claim.175 package members and saved count arithmetic verified.
Both read requests consumed. [Results](operations/NATIVE-REFERENCE-SCORING-RESULTS-2026-09-30.md).
Next is the separate training executor; future reference evaluation needs a new stage-specific scope.

### September30 — bounded 144³ training transaction

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-305 | Implement the separate144³ training identity/loop, deterministic shuffled passes, native evaluation, progress/checkpoint and independent recovery; rehearse on invented data and prepare the exact CAP-EXP-007 request. | Quinton: “Great, continue on” after D-304. | Synthetic updates only during implementation. Existing153 qualified members/23holds and readiness-only API preserved. A fresh separately pinned Quinton launch approval is required for real updates. |

[Transaction plan](operations/TWOMM-TRAINING-TRANSACTION-PLAN-2026-09-30.md).
[CAP-EXP-007 design](operations/CAP-EXP-007-LAUNCH-PLAN-2026-09-30.md).
The bounded implementation uses a fresh baseline in the new identity; prospective references total
386 label-only reads across0/113/226/300. Native prediction masks remain reproducible local scratch,
explicitly not independent backup keepers; checkpoints, evaluation records and terminal journal are
kept independently. No source reads or real launch is implied by this implementation decision.

D-305 completed:1,539 native tests; final source-matched synthetic workers46.010s,peakRSS2.570GiB,
exact intermediate/terminal probes,next-update weights3.73e-9; six independent restores and48 package
files verified. [Results](operations/TWOMM-TRAINING-TRANSACTION-RESULTS-2026-09-30.md).
CAP-EXP-007 request prepared,not authorized/launched:
`b13ebbce1731090a65dd5fe6c8327963f8e50203e39c25aa8ee6c88f903d85b3`.
300updates/113train/40validation/144³/2mm/45min total;386 label reads prospectively scoped,
zero original source-array reads or real updates in D-305. Next is exact launch approval.

### September30 — exact CAP-EXP-007 launch approval

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-306 | Launch the exact prepared CAP-EXP-007 request once, then verify and inspect its results and independent recovery. | Quinton: “Great, I approve this exact run.” | Request SHA `b13ebbce1731090a65dd5fe6c8327963f8e50203e39c25aa8ee6c88f903d85b3`;300updates,113/40,144³/2mm,45min total,16GiB memory,386 label reads/no CT reads. No extension, restart, threshold tuning or promotion. |

The frozen design/request remain unchanged. A separate request-bound approval is recorded in
`outputs/prowl/CAP-EXP-007-APPROVAL-2026-09-30.json`. Preserve failed/interrupted attempts and all
prior evidence. The launcher must recheck code/environment and enforce the approved resource limits.

D-306 completed:300updates on113/40,33.082min,5.638GiB RSS/4.799GiB driver;386 exact label reads,
zero new CT reads. Native final Dice0.0973/0.0987 and recall0.9785/0.9827, but ROI2/113 and1/40;
foreground remains excessive. Training7604 coverage failure and tiny references retained. Nine
keepers independently restored with primary blocked,probe delta0;805 files/386exports checked,
eight selected sheets inspected. No source changes or model promotion;1,539-test baseline remains.
[Results](operations/CAP-EXP-007-RESULTS-2026-09-30.md). Consumed request; no next run authorized.
Recommend a separately planned longer fresh duration/schedule comparison with coverage safeguards.


### October 1 — fresh 1,200-update broader-cohort experiment

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-307 | Prepare, verify and run the fresh CAP-EXP-008 duration/schedule diagnostic on the existing 113/40 cohort. | Quinton: “Great, it sounds like you know what needs to come next. Run the experiment now.” This follows Codex's explicit 1,200-update recommendation in STRATEGY-REGROUP-2026-10-01. | Routine bounded implementation and exact request preparation are included; no repeated approval is required for this experiment. Fresh seed42, 144³/2mm, fixed model/loss/sampler; checkpoints0/300/600/900/1200; 90min total,16GiB,4GiB local evidence,426 label reads/no CT reads. Freeze coverage guards before launch. No extension, different cohort, promotion, paid compute, source changes, Claude dispatch or Git publication. |

[Exact design](operations/CAP-EXP-008-LAUNCH-PLAN-2026-10-01.md).
Codex-selected delegated details: stop at a completed boundary from300 if mean validation recall<.95,
minimum recall<.65, fewer than38/40 boxes cover>=.995, or mean recall falls>.03 from the best earlier
active checkpoint. A stopped run preserves actual counts, completed read prefix and independent
recovery. Adapter/training versions2 implement the bounded1200 horizon; version1 remains capped300.
The launch authorization will be bound to the final request SHA after native tests/rehearsal. This
records Quinton's instruction to run the proposed experiment, not a claim that he reviewed bytes
that did not yet exist. Preserve the existing dirty source snapshot as a non-promotable diagnostic.

D-307 exact request frozen after1,566 native tests and final source-matched synthetic MPS/recovery:
`outputs/prowl/twomm-training-ec57d6ba-4027-4f3b-876e-c505d21023be`, SHA
`294c26b867903a99f8598ee6f904639073864f3f9f83f220eac31f8ea73e624e`.
The request-bound authorization in `outputs/prowl/CAP-EXP-008-APPROVAL-2026-10-01.json` implements
Quinton's instruction to run this proposed experiment; no additional human signoff is asserted.
Synthetic producer/recovery receipts `8c7068658a434fd06fbebc27f7f4a41a4d5c199c1c2d54f438dee547a953491b` /
`7689c73454cefff64ae48d80c71f4485935c8517addcd4f88045c1ffedc8387a`; exact prediction probes,
next weights3.73e-9, interrupted-update reuse refused. Real launch follows this exact request once.

D-307 attempt01 consumed the request above but failed before original label bytes/updates: one
cached inference export and step0 keeper only. All153 label metadata records differ solely in
macOS device number16777239->16777243; registered APFS UUID/inodes/sizes/times unchanged.
A bounded replacement under the same user-authorized experiment will freeze the live mount
observation and use a versioned UUID-verified temporary device observation, preserving all original
records and content/stat checks. The original/default reader stays strict. This is routine recovery
of the authorized operation, not permission to rerun a consumed request or change dataset content.
[Failure evidence](../../outputs/prowl/CAP-EXP-008-review-20261001/attempt01-failure.json).

D-307 attempt02 frozen after1,574 native tests and final source-matched MPS/recovery. Request `twomm-training-068616f8-c4f1-491c-b415-e0542ddb328a`, SHA `843fd09a1a7a7283a989c8644ea86cfe591b1a49f5f2dde90812b13eab283ba9`; authorization SHA `63097f48e9d07d75994c40a2666743b28e8afd37eaeb768b34fade3002872131`. Same scientific recipe/budgets; frozen metadata-only mount receipt `a79e2a218a5f395229dfa61cfa6040d09b8c0a50499146ef7e654195bb8dadbc`. Attempt01 remains consumed/preserved.

D-307 finished as a verified `stopped_coverage_guard` transaction at actual300/planned1200 updates.
Mean validation recall0.911146<0.95 and minimum0.055399<0.65 triggered the frozen stop;all40 boxes
cover reference. Native Dice0.077905,median prediction/reference23.738x,ROI2/40;38/40 Dice scores
decreased relative to D-306. No600/900/1200 stage or post-update full training evaluation ran.
22.729min total,5.200GiB RSS/4.799GiB driver;193 label reads,no CT reads. Five keepers independently
restored with primary blocked,terminal probe0;415 files/193 exports verified,seven sheets inspected.
Source/environment unchanged;1,574 native tests. [Results](operations/CAP-EXP-008-RESULTS-2026-10-01.md).
Both requests are consumed and preserved;153 members/23 holds unchanged. No run remains authorized
or pending,extension or promotion. The schedule diagnostic does not answer benefit beyond300 or G5.
Codex recommends discussing a fresh schedule comparison before another longer run; this is a
recommendation, not a new approval or permission to relax the failed coverage safeguards.

### October1 — retained-model optimization investigation

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-308 | Investigate the CAP-EXP-007/008 learning-rate schedules and other plausible optimization/inference causes using retained records, qualified cache and independently backed-up models. | Quinton: “Great, I agree. Investigate the learning rate schedule and anything else that could be giving us issues.” | CPU patch/scheduler/loss checks, then at most16 frozen-model MPS forwards under the separate600s/16GiB/128MiB envelope. No original source or primary-drive reads, real optimizer updates, training launch/continuation, qualification change, threshold selection or model promotion. |

[Bounded audit plan](operations/CAP-EXP-008-OPTIMIZATION-AUDIT-PLAN-2026-10-01.md). Existing consumed
requests remain consumed. Routine diagnostic implementation and read-only native verification are
within this instruction; no additional human signoff is asserted. Preserve attempt logs and separate
observations from causal claims. A next training recipe remains a proposal until separately prepared.

D-308 complete:all300 patches replayed;installed scheduler matches600 recorded entries.008's
first300 applied LR sum is1.894489x007's,no ordering defect.295 patches contain foreground,median
target0.303% and extra padding32.64%;balanced CE's median per-voxel class-coefficient ratio329.
Two independently backed-up step300 models received16 frozen MPS forwards;six native masks exact,
weights unchanged,Gaussian6186 probe no rescue.47.901s,2.945GiB RSS/1.461GiB driver;zero original
CT/label reads,primary-drive reads or real optimizer updates.1,574-test production source unchanged.
[Findings](operations/CAP-EXP-008-OPTIMIZATION-FINDINGS-2026-10-01.md);23-member audit receipt
`8ae38155aa54a126ba55539a99c5fc4ca0dae175f0fe4f818ca1a9974a53fc86`.

Codex proposes a fresh600-update diagnostic matching007's first300 applied rates,then300 updates
at fixed0.00001,with the same cohort/loss/sampling and coverage safeguards. Schedule duration must
be decoupled from update budget;the old cosine would rise again if blindly stepped beyond300.
[Next design](operations/LOCALIZER-SCHEDULE-NEXT-PROPOSAL-2026-10-01.md) is NOT approved,implemented,
request-frozen or launch-authorized. It is a recommendation within this investigation,not a new
Quinton decision. No active/pending training request,extension,promotion or change to153/23holds.

### October1 — matched-prefix/low-rate-tail diagnostic

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-309 | Implement, verify and execute CAP-EXP-009 once: fresh600-update diagnostic matching007's first300 applied rates,then300 at fixed0.00001. | Quinton: “Great, lets do the diagnostic.” | Same113/40,144³/2mm,model/loss/sampler/prediction;0/300/450/600 checkpoints/evaluations;prefix parity and existing coverage safeguards.60min/16GiB/4GiB output,386 label reads/no CT reads;independent recovery. No extension,resume,promotion,qualification change,Claude dispatch or Git publication. |

[Launch design](operations/CAP-EXP-009-LAUNCH-PLAN-2026-10-01.md). Routine implementation and
request freeze are within this approval;no repeated permission is required to run the diagnostic.
Prefix model tolerance1e-6 and exact40 native-mask parity are predeclared. Preserve failed/stopped
attempts and bind the authorization record to the final request SHA;no assertion that Quinton
reviewed bytes not yet prepared. Prior v1/v2 behavior remains unchanged.


D-309 native preflight completed; **real launch held**, not a completed real experiment.
[Results](operations/CAP-EXP-009-PREFLIGHT-RESULTS-2026-10-01.md): CPU first300 applied rates/weights
match, but original/original native synthetic repeats differ by0.000178389 in weights after2updates
despite identical histories and one exact validation mask. Final new/original difference0.000080405.
The1e-6 fresh-prefix qualification fails; the preparation gate refuses a real request. No original
CT/label reads, real updates, request consumption, eligibility or promotion.1,621 native tests pass.
Stopped-prefix keepers and a separately labeled invented tail probe independently recovered with
primary blocked: probe0,next weights1.862645e-9.80 final files rehashed;439 retained files indexed,
audit receipt f30b0e65c05cd1368afd5db02dbc14c1c7013b014df695badbf9779c069c26e9.

Codex recommends the [parented-tail design](operations/LOCALIZER-PARENTED-TAIL-PROPOSAL-2026-10-01.md).
It imports the007step300 model/AdamW state and proposes300 new low-rate updates with explicit ancestry
and absolute sampler offset. This recommendation is **not a new Quinton decision** or permission to
resume a consumed request. D-309 approves the fresh design only; a parented experiment awaits review.

### October1 — parented low-rate-tail diagnostic

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-310 | Implement, qualify and test a new child experiment from CAP-EXP-007 step300, preserving model/AdamW state and testing300 new updates at fixed0.00001. | Quinton: “Great, yes test the low rate tail, and anything else you think is necessary.” | Same113/40,144³/2mm,absolute sampler indices300–599;zero-update40-case parent qualification first;new checkpoints0/150/300 and existing numeric coverage floors active from0. Fresh233-label training scope,zero originalCT reads;45min/16GiB/4GiB output,independent recovery. No consumed request resume,auto-extension,promotion,cohort filtering,Claude dispatch or Git publication. |

[Parented-tail design](operations/LOCALIZER-PARENTED-TAIL-PROPOSAL-2026-10-01.md) is approved by this
instruction. CAP-EXP-010 names the new child experiment; CAP-EXP-009's fresh design stays held.
Routine implementation, synthetic/native verification, exact source/runtime/request freeze and
single bounded launch are covered. Bind authorization to the prepared request without asserting
that Quinton reviewed bytes before they existed. No repeated launch confirmation is required.
Native parent import/inference must qualify before any real update; preserve every failure.

D-310 implementation and qualification pass:1,652 native tests (two existing torch.jit warnings);
source-matched native invented recovery next weights1.862645e-9/probes0. Real zero-update qualification
read40 references/noCT, reproduced all40 native007masks exactly, and independently restored three
keepers with primary blocked/probe0.126.535s worker,141.998s including recovery;4.931GiB peakRSS.
Qualification receipt `3f2c561741c58784de081f9ea4166b855ab16d0015ce515e9e15ab9868a0e45b`.

Exact300-new-update request `outputs/prowl/twomm-training-a2593f26-59b6-4582-947d-582bfed6928f`, SHA
`f37f07ad891ea29406e099f1b46d15188e4eb748dcbd295f31fc6b263a796562`, is frozen and authorized
under D-310. This binding applies Quinton's existing design/launch approval; it does not claim he
reviewed newly generated request bytes. Recheck all40 native masks at child0 before any update;
233 fresh reference reads/noCT,0/150/300 boundaries,45min including recovery. One launch only.
Production source SHA `0c857972139c44f561d0c338c6dbdf922920abd9b967423bc9b905c2ed5f08fc`;
runtime SHA `dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.


D-310 complete: CAP-EXP-010 ran300 new updates at0.00001 from exact007step300 model/AdamW state,
absolute sampler300–599,logical600. All40 native masks requalified before updates. Validation Dice
0.098701→0.110417,recall0.982700→0.975863,median volume18.497→16.541x,ROI1→2/40. All40 Dice improve
and masks shrink;all active coverage guards pass,useful-shrinkage target fails. Training Dice0.108541,
recall0.979678,ROI2/113;3115 recall0.706283/7604 box0.860597 retained. No model promotion.
25.600min,5.888GiB RSS/4.853GiB driver,233 reference reads/noCT. Seven keepers independently restored
with primary blocked,probe0;501files/233exports verified,ten paired sheets viewed.300 actual crops
exactly replayed fromcache (290 positive/10 empty). Source/runtime unchanged;1,652-test baseline.
[Completed evidence](operations/CAP-EXP-010-RESULTS-2026-10-01.md), execution receipt
`84a16cc4e39409140404e8639daead08abce7fce9fee9f400effdccef548eee8`.
Both qualification/training requests consumed;no active/pending run,extension,resume or promotion.
Same153members/23holds.009 fresh replay remains held. Codex proposes a fixed-patch objective/
negative-exposure audit before selecting a new loss comparison;this is not a new Quinton approval,
recipe change or exact launch request. No Git publication or Claude dispatch occurred.

### October1 — frozen-model foreground and negative-exposure audit

| ID | Decision | Authority | Boundary |
|---|---|---|---|
| D-311 | Implement, verify and run the bounded foreground/objective audit proposed after010, then document findings and discuss the next training decision. | Quinton: “Great, check that now. Continue on.” | Eight fixed training-only144³ patches,007/010 independent-backup models,at most16 forwards;600s/16GiB/128MiB,AC/exclusiveMPS. No original/primary reads,optimizer updates,source rewrite,loss adoption,cohort changes,promotion,Git publication or Claude dispatch. |

[Exact audit plan](operations/LOCALIZER-FOREGROUND-AUDIT-PLAN-2026-10-01.md) clarifies selection
before new logits and defines current/voxel-mean/capped50/fixed50 CE arithmetic plus the same
foregroundDice. The native-support subset is a diagnostic counterfactual only.50 is illustrative,
not an approved training weight. Verify synthetic normalization/derivatives before frozen native
execution. Methods/inputs/selection/models/source/runtime must be pinned; bind D-311 to the final
request and run once. No repeated confirmation is needed for this read-only audit.

D-311 exact request SHA `dff832472a74618b6e3ca5a689811863b04f397ab91715796f3bf4757981b02a`
was frozen after27invented math tests and bound to Quinton's existing audit authorization; one
native launch completed.16forwards,zero updates/original source reads,primary reads blocked,
both independent-backup weight digests unchanged.17.396s total,1.823GiB RSS/1.371GiB driver.
Native current-loss decomposition matches within7.19836e-8;20execution/42review files verified.
Execution receipt `e90e8b1b72a7d83ff93f5068237b5083e37afbadd2491c2a0bd2d70ed8e02f7f`;
full review receipt `d4b1f0bc0c0be5a0acde60e1b878bf5df538c3e070d71097680f4af4cf59e74c`.
[Results](operations/LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md) retain the exact selection,
scalar evidence, resource limits and documentation timing deviation. Source/runtime unchanged;
production baseline1,652tests,153members/23holds unchanged. Request consumed;no pending audit/run.

Current loss favors uniform foreground shrinkage7/8 in each model;the six-voxel cropped5286patch
favors expansion. Cap50 reverses that direction while reducing its foreground CE+Dice contribution
about4514x in010. Padding dilutes background pressure without reversing the observed signs.
Codex therefore proposes a gentler0.25foreground/0.75background class-mean CE plus unchangedDice,
with sole-class behavior unchanged. Explicitly post-hoc scalar arithmetic favors shrinkage8/8,
preserves50–53%foreground pressure and passes five invented independent derivative checks.
This is not an adopted loss,optimal weight,model-parameter gradient or authorized training design.
[Next discussion proposal](operations/LOCALIZER-CLASS-MEAN-REBALANCE-PROPOSAL-2026-10-01.md)
keeps007parent/AdamW state,300new updates/sampler300–599/0.00001/cohort/geometry/guards fixed for
one loss-factor comparison. Quinton's next design decision precedes versioned production code,
native qualification and a fresh exact request. No promotion,Git publication or Claude dispatch.

### October1 — class-mean balance experiment

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-312|Implement, qualify and run CAP-EXP-011 with0.25foreground/0.75background class-mean CE plus unchanged foregroundDice.|Quinton: “Great, continue with that. Great work.”|Same007step300 model/AdamW parent,113/40,144³/2mm,300new updates at0.00001,sampler300–599;sole-class mean CE unchanged. New version/identity,synthetic/native recovery and40-mask qualification before a fresh233-reference training request. Existing coverage/utility criteria,45min/16GiB/4GiB;one launch,no extension,promotion,filtering,Git publication or Claude dispatch.|

This accepts [the specific class-mean proposal](operations/LOCALIZER-CLASS-MEAN-REBALANCE-PROPOSAL-2026-10-01.md),
including the bounded implementation, qualification and training sequence. It is an exploratory
matched comparison against010's retained control,not formalG5 or an optimal-loss claim. Bind this
existing approval to each final source/runtime-bound qualification/training request after verification;
do not repeatedly ask for launch permission or assert Quinton reviewed bytes before they existed.
Old loss/checkpoint versions and consumed requests remain immutable. Source data,153members/23holds,
padding/sampling/thresholds and held009fresh replay remain unchanged.

D-312 implementation gates pass:1,706native tests (54new,twoexisting torch.jit warnings), explicit
version5 objective/checkpoint/control record;unchanged sampler/data/model source. Source-matched
native invented transaction recovers seven keepers with primary blocked,probes0,nextweights
1.862645e-9,interrupted update refused. Producer31.510s/recovery13.934s,peakRSS2.424GiB.
Producer receipt `b13dbafd8a0053f5e35b4ccf32b45022f4b2b1c2344124071c203f5c5879a566`, recovery
`bcce7d590d033ae8e0a480bb4b23bfce3dae23e3bca6cbdd933058899b23f21f`.
Zero-update qualification request `outputs/prowl/twomm-training-3ec13a6e-9f5d-4e03-9198-a18b79cf5b09`,
SHA `7575c72690540ff8992ccc45d6986a9296294b694d703b695e46102cc2ec2923`, is bound to existingD-312:
40pancreas references/4,912,185compressed/988,609,695expanded bytes,noCT,900s/16GiB/1GiB.
SourceSHA `99a64ed0b4c68df4857bffc9c3be0f2685fd9359ea46f940dc79e23714c3fd07`;runtime unchanged
`dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.
This binding applies Quinton's design/sequence approval,not a claim that he reviewed generated
request bytes. Native40-mask qualification and independent recovery precede any real011updates.

D-312 real zero-update qualification passed:all40native masks exactly match007,three keepers
independently restored with primary blocked/probe0;97execution files/40exports rechecked.
126.544s worker/140.925s including recovery,4.530GiB RSS/1.410GiB driver;40label reads/noCT.
Qualification receipt `337187433952cf7aff0031cbf8db1cd37f4485930b7cf4c5c5fbf1864ab88d8c`.
New exact300-update request `outputs/prowl/twomm-training-6b94ab00-5a6e-4457-aa4a-fc434305daf0`, SHA
`562733c43722a5d3588f9f282ea0d26eb7431a8803a06c803f14ae3c31c2ef20`, is frozen and authorized
underD-312:233references/31,766,649compressed/6,376,087,421expanded bytes,noCT,2700s including
independent recovery,16GiB/4GiB. Source/runtime remain99a64ed0/dd1b62c4. One new launch;initial40
parent masks must requalify before updates;no automatic extension or promotion.

D-312 finished with required coverage stop at150new updates/logical450. Mean validation recall
0.948096<0.95 and drop0.034604>0.03from parent trigger stop;minimum0.672303/all40boxes pass.
Updates151–300and terminal113train evaluation were prevented. Native Dice0.140680,median volume
12.853x/30.509%below parent,ROI17/40. Versus010matched150all40Dice improve/masks shrink,38recalls
decline.6110/7604/7684not newly evaluated.6186minimum/3115/tiny2727regressions retained;6534's
ROI screen pass does not certify its lower-recall contour. No loss change or gate relaxation follows.
80actual label reads/noCT,10.801min,5.231GiB RSS/4.853GiB driver;five independent keepers/probe0,
192executionfiles/80exports verified,six sheets viewed,33review members sealed.1,706-test source
baseline/runtime unchanged since freeze,153members/23holds unchanged. Both real requests consumed;
no active/pending run,resume,extension or promotion. [Results](operations/CAP-EXP-011-RESULTS-2026-10-01.md).
Execution receipt `77fbe303affeda26694d94e74f4c3deec7eb0cf3811e20021191b83c972cd780`;review
`b5f08446451a64381d0131775d1c2d4e279a13aa327850cf5f96437028ccd9f9`.
Codex recommends [one gentler37.5/62.5midpoint](operations/LOCALIZER-GENTLER-BALANCE-PROPOSAL-2026-10-01.md)
with same007parent/rate/sampler/cohort/geometry/guards. It is a proposal,not Quinton's new design
decision or authorization. No Git publication or Claude dispatch occurred.

### October 1 — gentler class-mean comparison approved

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-313|Implement, qualify and run CAP-EXP-012 with0.375foreground/0.625background class-mean CE plus unchanged Dice.|Quinton: “Great, I think that is the best move as well. Lets continue on.”|Same independent-backup007step300 model/AdamW,113/40,144³/2mm,300new updates at0.00001,sampler300–599;sole-class CE unchanged. Version6, arithmetic/learning/codec tests and native invented independent recovery, fresh40-mask zero-update qualification, then exact233-reference bounded request and one launch. All previous coverage/utility rules and45min/16GiB/4GiB limits retained. No continuation,promotion,filtering,Git publication or Claude dispatch.|

This accepts the entire sequence in [the midpoint proposal](operations/LOCALIZER-GENTLER-BALANCE-PROPOSAL-2026-10-01.md).
Bind existing design approval to final immutable source/runtime-bound requests after verification;
this does not assert Quinton reviewed request bytes before they existed. Compare retained010at150/300
and011only at150. The latter stopped and has no300outcome. Preserve old versions and consumed requests,
153members/23holds, sealed holdout and held009replay. Prospective [launch plan](operations/CAP-EXP-012-LAUNCH-PLAN-2026-10-01.md).

D-313 implementation verified:1,763native tests pass(57new,twoexisting torch.jit warnings).
Independent loss formula/gradient, sparse/empty learning, parent preservation/absolute sampler,
interruption/refusal and version isolation tested. Exact factor check:only adapter/session common
mechanics gain gated version6 support,eight new production modules;old data/model/loss code unchanged.
Only loss_id changes scientifically against010;plan fields match aside from required versions.
SourceSHA94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d;
runtimeSHA dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31.
Native invented recovery is now running;no real012qualification request or updates yet.

D-313 qualification exact request bound to existing design approval: `outputs/prowl/twomm-training-febb98c7-41e0-45b7-9025-25d878b8a96c`,
SHA `49afaf63e44fb057ad55c5dd999f27e6e5211d6d4ca12623e3b026aa53934406`; approval SHA `736d364ec9a49c0ce0b932232cbaf63eb508d2e8e47717dd01c0ee10e4cddfe8`.
40fresh pancreas labels/4912185compressed/988609695expanded bytes,noCT;
900s including recovery,16GiB RSS/driver,1GiB output,AC/exclusiveMPS/100GiB free.
Source `94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d`,runtime `dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.
Binding applies approved D-313 design after verified gates;not a claim of prior user review of generated bytes.
One launch only; no extension, promotion or guard relaxation.

D-313 native invented qualification passed:seven independent keeper restores, primary reads blocked,
exact prediction probes,nextweights1.862645e-9, interrupted optimizer mutation refused for save/reuse.
Producer31.471s/recovery14.672s,producerRSS2.496GiB. Producerreceipt
`d2ea23a202cedc1b317d6e16eb452872a94f99128f780f425bdfa6f37cdb5c83`, recoveryreceipt
`3e409b2d4fac128ba2a5eac89ece919d07582a59b9b46b9f8885b503217621fb`.

D-313 real zero-update qualification passed:all40native007masks exact,three independent keepers restored,primary blocked/probe0;97files/40exports rechecked. Worker129.394s,total144.740s,RSS4.673GiB,driver1.410GiB.40label reads/noCT. Qualification receipt`bcb8064fe24f86ff55885ca18442d18a2bf4cdda0d1864632efd1ac354057f12`. Source/runtime unchanged;fresh training preparation follows.

D-313 training exact request bound to existing design approval: `outputs/prowl/twomm-training-a0636d70-2ea5-4e5f-9167-db28bff562ba`,
SHA `06cecda421626271eeb6fae5f02679d7fc9650b5afd0861ce39fce5ed0612218`; approval SHA `4ea46c04f41c22c8fafa89f86a3ddaf75a31c7d9e9effc611406d08cfe772920`.
233fresh pancreas labels/31766649compressed/6376087421expanded bytes,noCT;
2700s including recovery,16GiB RSS/driver,4GiB output,AC/exclusiveMPS/100GiB free.
Source `94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d`,runtime `dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.
Binding applies approved D-313 design after verified gates;not a claim of prior user review of generated bytes.
One launch only; no extension, promotion or guard relaxation.

D-313 CAP-EXP-012 complete:300newupdates/logical600,37.5/62.5CE+sameDice,exact007model/AdamW parent,
0.00001/113/40/144³/2mm. Native validationDice0.129078,meanrecall0.962519,
minimum0.674440,medianvolume14.2596x/22.907%belowparent,ROI15/40,
boxes39/40. Every0/150/300stop passes,but utility fails volume/meanrecall/all40boxes;no promotion.
Against010at300all40Dice improve/masks shrink,38recalls decline.3115newvalidationboxfailure,
756/6822newtrainingboxfailures,7604persistent;150trainingrecall.4630isworst andonlytrainingDice regression.
TrainingDice.126738/recall.968681,ROI36/113,boxes110/113. All113members retained,combined600
exposures78five/35six times;155foreground/145backgroundcenters.300crops exactly match010.
Actual233labelreads/noCT;25.312min,RSS6.252GiB/driver4.853GiB,seven independent
keepers restored/primaryblocked/probe0.502executionfiles/233exports,13selectedpairedsheets and
trajectorychart reviewed,52reviewmembers rehashed.1,763-testsource/runtime unchanged.
Executionreceipt`2ca47e685f28d8007c34db51410482dc77b5b34da56598f4a645314ef1991926`;reviewreceipt`9f69df5f1d80acf845f89fde52fa6cc4b06a5ca9ac9a78f055b3e8be097e78a6`.
[Results](operations/CAP-EXP-012-RESULTS-2026-10-01.md). Both requests consumed;no pendingrun/extension/
promotion/eligibilitychange/Gitpublication/Claudedispatch.153members/23holds unchanged.
Next recommendation is a timeboxed retained-prediction structure/box-extent audit and smallStage2
qualification planning,not another weight guess or approved job. Fresh reference scoring requires
new scope;oldreadrequests may not be recycled.


### October 1 — retained structure audit and Stage 2 planning

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-314|Timebox the retained native-prediction component/box audit and prepare the small Stage 2 qualification packet.|Quinton: “Great, continue with that.” after the D-313 recommendation.|Compare completed 010 and 012 at child step 300 on all 40 development-validation members plus retained training failures 150/756/6110/6822/7604/7684. CPU only; frozen retained exports/records, no CT or original target arrays, inference, updates, component-policy adoption or model promotion. Native references would require a new read scope. Stage 2 work here is planning; lesion qualification and real reads are not inherited from localizer permission. Preserve 153 members/23 holds and all sealed evidence.|

Owned new files: bounded structure helper, diagnostic script/tests, one local audit output directory,
operations audit plan/results and Stage 2 qualification/implementation packet. Update only shared
checkpoint/decision/notebook navigation. Acceptance: independently checked component arithmetic,
26-connectivity/ties/empty/dense/physical bounds, frozen exact input pins, one-shot request consumption,
all requested cases visible and old masks unchanged. Audit has no target truth per component;
hypothetical largest-component box cost is not a validated ROI or pancreas-containment result.
Prospective plan: [structure audit](operations/LOCALIZER-STRUCTURE-AUDIT-PLAN-2026-10-01.md).


D-314 diagnostic readiness: 26 new synthetic/helper/runner checks pass. Dense 96-million-voxel
CPU profile passes in 1.362 seconds, peak RSS 604,438,528 bytes. Exact retained-only request
`outputs/prowl/LOCALIZER-STRUCTURE-AUDIT-20261001/request.json`, SHA
`f5d455d9eb514f213c11cb8be1be84a90c22e6d4a03870a6954bbcda58de2054`, pins 92 masks,
21,606,141 compressed bytes and 2,436,199,082 uint8 voxel payload bytes, 1,200 seconds/8 GiB/50 MiB.
Original-reference/CT reads, model inference/updates and adopted cleanup remain prohibited.
Exact scope binds Quinton's approved D-314 diagnostic after preparation; it does not claim he
reviewed these generated bytes. Full native suite is running before the one-shot audit.
Stage 2 packet prepared: [qualification/cascade slice](operations/STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md).
No Stage 2 eligibility, read request or training authorization follows from that planning document.


D-314 complete: 92 retained native masks/46 paired cases (all40 validation + train150/756/6110/6822/7604/7684),
010/012 child300,26-connectivity/10mm. CPU33.239s,RSS1.464GiB; no original arrays, forwards or updates.
012 largest foreground share median99.394%, mean crop31.684%→hypothetical21.961%;30/40boxes change,
size-only15→31/40,not new ROI passes. Main region remains median13.328×reference; count-only guaranteed
excess median92.69%.3115/756/7604boxes unchanged;6822's smaller box cannot repair existing containment.
Five012/eight010 validation count-only component recall lower bounds are0;actual overlap unmeasured.
1,789native tests pass(26new,twoexisting warnings); initial sandbox ps restriction preserved in test log,
complete native rerun passed.96M dense synthetic profile1.362s/0.563GiB.184selected inputs and audit
source modules rehashed unchanged. Requestf5d455d9 consumed;executionb58ff84c;review63fb49bb,
105files/3,046,235bytes. [Audit results](operations/LOCALIZER-STRUCTURE-AUDIT-RESULTS-2026-10-01.md).
[Stage2 packet](operations/STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md) prepared including
bounded synthetic purpose records/metadata proposal, then lesion qualification/shared geometry/synthetic
learning/real zero-update/exact smoke/matched provided-predicted modes. No realStage2 permission/cohort/
reads/model/job. [Component coverage proposal](operations/LOCALIZER-COMPONENT-COVERAGE-PROPOSAL-2026-10-01.md)
needs new scoped reference-read decision;largest-only remains diagnostic. No pending training, promotion,
consumer/cohort change,Git publication orClaude dispatch.153members/23holds unchanged.


### October 1 — Stage 2 synthetic purpose records and metadata proposal

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-315|Implement Phase A's separate segmenter-purpose qualification/cohort contracts on invented evidence and produce the retained-metadata candidate proposal.|Quinton: “Amazing work, continue.” after D-314's recommended next step.|New versioned dual-target records, synthetic resolver tests and metadata-only candidate/hold accounting; proposed 8 train/4 validation list, not a real cohort. No source arrays/stat jobs, real Stage 2 permissions, cohort publication, model execution, downloads or training. Old localizer rules/consumers and original membership/153 members/23 holds remain unchanged. Component-reference proposal still needs a separate fresh-read scope.|

Owned files: new `segmenter_qualification_v1.py`, `segmenter_cohort_v1.py`, retained inventory CLI,
new tests and dedicated schemas if needed. Generic manifest/annotation formats already support two
structures; preserve them and the existing localizer schemas. New purposes are explicitly
`pancreas_lesion_segmenter_training` and `pancreas_lesion_segmenter_validation` under a distinct policy.
Records must bind both annotations/all three inputs, exact evidence hashes, issues and original roles;
empty lesion masks do not infer negative status. Tests must reject stale/changed/omitted evidence,
wrong roles/purposes, unsupported units/mapping, duplicate/overlapping membership and silent refill.
Metadata reads are bounded to pinned retained JSON/CSV/split bytes; no legacy file path is resolved.
Packet: [Stage 2 qualification/cascade](operations/STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md).


D-315 complete: separate dual-target segmenter qualification/cohort/paired-lesion-inventory contracts,
47 new synthetic tests; full native 1,836 passes/two existing warnings. Old source snapshot remains
CT/pancreas-only; no shared schema widening. Four shared data modules/two old schemas match D-294 pins.
Retained metadata proposal exactly replays in a fresh process:176 candidates/153 localizer-qualified/
23 held, plus historical31/78/266 contexts retained. New Stage2 qualifications0; original7200/1800/901 unchanged.
Proposed train3/26/6110/2973/2232/6238/5821/4965; validation2514/5641/2727/7265. Six train/two validation
positive legacy hints; zero hints are not verified negatives. Current40validation has only two positive
hints, so a later broader lesion-positive validation proposal is needed for stable performance estimates.
31,571,267 metadata bytes,1.307s/0.326GiB RSS,zero source stat/array calls or models. CandidateJSON
2f38464f;metadatareceipte83c27e1;sealedreviewb25f3e20,15files/483,620bytes. All input/code pins verified.
[Results](operations/STAGE2-METADATA-RESULTS-2026-10-01.md) and
[contracts](data/STAGE2-PURPOSE-CONTRACTS-2026-10-01.md). Proposed next:
[M1 source stat/availability](operations/SEGMENTER-SOURCE-VERIFICATION-PROPOSAL-2026-10-01.md), then
fresh headers/content, purpose dispositions/cohort freeze/shared geometry. No M1 capability/request/run
or real Stage2 permissions issued here. Component-reference job still needs separate fresh scope.
No training/promotion,old consumer or eligibility change,source rewriting,Git publication orClaude dispatch.

### October 1 — bounded segmenter source verification

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-316|Implement, test and execute the proposed M1 exact metadata verification, then fresh M2 compressed identity/lesion-header verification; prepare measured M3 content scope.|Quinton: “Great, verify the files and continue onto the next.” after D-315.|36 exact source files, protected 8 train/4 validation proposal; M1 metadata only, M2 full compressed hashes plus 12 bounded headers. No arrays, Stage 2 permission/cohort, model or training; no component-reference scope or global source activation.|

Prospective [bounded implementation/run plan](operations/SEGMENTER-SOURCE-VERIFICATION-PLAN-2026-10-01.md).
Budgets: M1 90s/512MiB/1MiB output; M2 600s/1GiB/4MiB output with exact source bytes frozen after M1.
Missing/changed/unsupported files stay accounted for; no substitution, inferred negative status or eligibility promotion.

D-316 complete: all36 exact source paths exist;24 CT/pancreas hashes and two prior lesion hashes match.
Ten new lesion identities observed;12 native lesion grids match qualified mm CT. Five scaled int8,
six unknown label-unit contexts supported through byte-bound matched qualified CT; no header rewriting.
M1 fresh attempt1.867s/107,102,208B RSS,zero payload reads; M2 7.618s/107,184,128B RSS,
276,002,660hash+49,152header compressed bytes. No arrays or full new gzip CRC verification.
First M1 sandbox attempt consumed/failed at native volume check before candidate observations; retained.
Fresh M1 request0ce9ca20/receipt9a1e5c9c, M2 request7042885d/receiptbec0f3b3 complete and consumed.
Final native1,869passes/twoexisting warnings;33new checks. Initial four full-suite fixture RSS failures
corrected without raising real job limits; all attempts preserved. Old modules/schemas unchanged.
Reviewb90cbf06,22members/91,259bytes; independent fresh-process receipt/code/runtime/input verification.
[Results](operations/SEGMENTER-SOURCE-VERIFICATION-RESULTS-2026-10-01.md).
[Next packet](operations/SEGMENTER-CONTENT-ALIGNMENT-PACKET-2026-10-01.md) prepares synthetic resource
qualification and fresh4-case content pilot3/26/2973/5641 before eight-case continuation. New proposal
33853ca3 pins953,056,392expanded bytes across36 original array files, with exact companion sizing
replayed from24 prior byte-matched content records. No source-array request/qualification/cohort
or training issued here. Current153members/23holds and original7200/1800/901 unchanged.

### October 1 — segmenter native content/alignment pilot

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-317|Implement/test bounded native three-input content diagnostics, qualify resources on synthetic largest-case inputs, then execute and inspect the four-case pilot.|Quinton: “Great, continue to the next.” after D-316's content-pilot recommendation.|Train3/26/2973, validation5641;12 exact files, full hash+decode185,422,674 compressed bytes/317,547,616 expanded bytes,900s/8GiB/64MiB output. No real permissions/cohort/training. Prepare remaining8 separately after pilot review.|

[Prospective plan](operations/SEGMENTER-CONTENT-PILOT-PLAN-2026-10-01.md); [content/alignment packet](operations/SEGMENTER-CONTENT-ALIGNMENT-PACKET-2026-10-01.md). Preserve original roles/targets/components and every failed attempt; no automatic replacement, negative inference or lesion-driven ROI repair.

D-317 complete: new diagnostic reader/supervised four-case source transaction and native review;
41new checks/1,910native passes,twoexisting warnings,65.16s. Largest512×434×208 synthetic path
15.406s/890,830,848B RSS,all dense/empty/392fragmented/boundary checks. First targeted factory-spacing
failure fixed before profile/request; all attempts preserved. Fresh pilot requestb27b26ab consumed:
12arrays,185,422,674compressed hash+decode and317,547,616expanded bytes;6.777s/1,034,420,224B RSS.
All4 geometry/content checks and sheets technically reviewed; counts1055/7244/124/47190,one26-connected
component each;outside-pancreas-mask0/431/3/47190. All4 lesion extents fit retained pancreas-only boxes,
replayed from hash-bound metadata with no new source reads.5641 disjoint masks require source annotation
relationship review,not automatic clipping/union/exclusion.2973 single7.5mm slice remains fidelity challenge.
Source receipt2f972c5c(38members/2,851,981B),profile14eaa7e0(13members),reviewb4cc90d5(19members/91,382B);
visual328b501b,boxdcd1ee85. Source/records/code/runtime/oldD315implementation pins independently verified.
[Results](operations/SEGMENTER-CONTENT-PILOT-RESULTS-2026-10-01.md).
[Remaining-eight packet](operations/SEGMENTER-CONTENT-CONTINUATION-PACKET-2026-10-01.md)/proposal7fb32a63
prepared,not executable/frozen:train6110/2232/6238/5821/4965,validation2514/2727/7265;24files,
366,582,646compressed/635,508,776expanded bytes. Separate new consumer/request required; pilot stays
consumed/fixed. No continuation arrays,realStage2 permissions/cohort,model updates ortraining.153localizer
members/23holds,176candidates and original7200/1800/901 preserved. Old consumers/schemas unchanged.

### October 1 — segmenter eight-case content continuation

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-318|Implement/test a separate continuation, qualify the corrected native context renderer synthetically, execute/review the eight remaining cases and reconcile all12 candidates.|Quinton: “Great, continue on” after D-317.|24 exact files;366,582,646combined compressed bytes/635,508,776expanded bytes;900s/8GiB/64MiB. Original pilot remains fixed/consumed. No real purpose permissions/cohort or training.|

[Prospective plan](operations/SEGMENTER-CONTENT-CONTINUATION-PLAN-2026-10-01.md). Preserve empty references as unknown, all components/outside-mask observations and source annotation questions. Separate downstream disposition/paired-inventory/annotation-transition proposal required.

D-318 complete: 21 new checks / 1,931 native passes, two existing warnings, 66.81 s. New renderer
qualified at 512×434×208 on dense/empty/392-fragmented/boundary data: 14.450 s / 0.830 GiB RSS.
Fresh request f378e8d3 consumed once, source receipt eeb5d3b0: exact 24 arrays,
366,582,646 compressed hash/decode / 635,508,776 expanded bytes; 12.343 s / 0.912 GiB RSS.
All eight checks and sheets reviewed, all twelve reconciled: six train/two validation nonempty
candidates and four unknown empties. All eight nonempty extents fit retained pancreas-only boxes,
replayed without another source read. Case6238 source-boundary contact retained;5641 annotation
relationship remains open;2973 single7.5mm-slice fidelity remains explicit. No clipping/refill/negative
inference. Profile56ceb670, sealed reviewfb483be6 (24members/143,111B); ledgerc471a6e2,
visual63be6bb7, box00d6222a, proposal a37de84e. Old shared code/schema/source pins verified.
[Results](operations/SEGMENTER-CONTENT-CONTINUATION-RESULTS-2026-10-01.md) and
[next purpose-disposition packet](operations/SEGMENTER-PURPOSE-DISPOSITION-PACKET-2026-10-01.md).
No real Stage2 permission/cohort/training or pending source request;153localizer members/23holds,
176 candidates and original7200/1800/901 unchanged. No old transition widened or issue cleared.

### October 1 — real segmenter purpose-disposition slice

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-319|Implement/test and publish a replayable twelve-case paired inventory and purpose-disposition ledger with separate annotation/issue transition checks.|Quinton: “Great, move onto the next.” after D-318.|Retained metadata only; preserve every predecessor and original role. Proposed seven positives/five holds require actual checks. No source arrays, cohort, model or training launch.|

[Prospective plan](operations/SEGMENTER-PURPOSE-DISPOSITION-PLAN-2026-10-01.md) and [exact local-use assessment](data/SEGMENTER-PURPOSE-USE-2026-10-01.md). Keep5641 annotation-held and four empty references unknown; no refill or negative inference. Old localizer transition/consumers and schemas remain unchanged.

D-319 complete: twelve paired lesion inventories, seven positive purpose qualifications
(six train3/26/2973/2232/6238/5821; one validation2514) and five holds. Four empties remain unknown;
5641 remains annotation-relationship held. No refill/negative inference/source reads/model/cohort.
All184 predecessor annotations/247issues, pancreas records, subjects/snapshots/179studies and
original9901 protected memberships preserved. New manifest196annotations/260issues;3/26 old pending-use
issues remain attached to quarantined predecessors, with explicitly reviewed distinct successors.
25new checks/1,956native passes, two existing warnings,67.43s. Publication7334b71e (fourmembers/
26,756,709B), inputs9f45cdf7, manifest31c7239d, transition62447d63; independent fresh replay
57.591s/0.958GiB,exit0. Time wrapper's supplementary sysctl failed after successful publication;
receipt verified and publication not repeated. Sealed review81ee950a (19members/245,703B) retains
all test/fixture/telemetry attempts. Old ten shared source/schema pins unchanged.
[Results](operations/SEGMENTER-PURPOSE-DISPOSITION-RESULTS-2026-10-01.md) and
[next cohort-freeze packet](operations/SEGMENTER-COHORT-FREEZE-PACKET-2026-10-01.md).
One positive validation reference supports engineering only; no generalization estimate.153localizer
members/23holds and176candidates unchanged. No source/model activation or pending training request.

### October 1 — segmenter frozen role-cohort slice

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-320|Implement/test a metadata-only adapter, publish exact6/1 segmenter cohorts with original protection parents, and independently replay them from registered storage.|Quinton: “Great, move to the next.” after D-319.|Full purpose/transition rederivation;12 candidates/fiveholds and all history preserved. Exact capability; no source arrays/model/training or source activation.|

[Prospective plan](operations/SEGMENTER-COHORT-FREEZE-PLAN-2026-10-01.md). One positive validation case is an engineering reference only. Preserve all old localizer consumers and schemas.

D-320 complete: registered6/1 executable children with original7200/1800 protection parents;
test901/full9901protected manifest unchanged. All12candidates/fiveholds,184predecessor annotations/
247issues retained; no refill/negative inference. Complete D-319 purpose/transition rederivation
required before publication/resolution. Exact new capability0b89b9a9, provider/roots unchanged.
31new checks/1,987native passes, two existing warnings,70.56s. Seven covered artifact members/
28,722,760B; completion73e7e034,plan49b11f37,code03f0d1e4,descriptorscd52c555. Publication
263.044s/1.004GiB; fresh registered replay155.396s/0.962GiB,exit0. Independent byte/case/role/CT
oracle passes; reviewf6897492 (27members/207,038B), all attempts preserved. No independent keeper
copy, source arrays/model updates/launch or global source activation. One positive validation
reference remains engineering only. [Results](operations/SEGMENTER-COHORT-FREEZE-RESULTS-2026-10-01.md)
and [next shared geometry/loader packet](operations/SEGMENTER-GEOMETRY-LOADER-PACKET-2026-10-01.md).
Old153localizer members/23holds and176candidates unchanged; no pending training request.

### October1 — shared segmenter geometry and loader qualification

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-321|Implement/test the shared physical ROI/three-class mapper and registered-cohort triple loader, profile invented worst-size cases, freeze and execute one exact read-only seven-case fidelity request and review all outcomes.|Quinton: “Great, continue to the next.” after D-320, with standing autonomy to complete the next bounded implementation.|Fresh21-file CPU geometry scope only after tests/resource qualification; exact6/1/all12/fiveholds unchanged. No training/model updates or source activation.|

[Prospective qualification plan](operations/SEGMENTER-GEOMETRY-QUALIFICATION-PLAN-2026-10-01.md). Initial144³/1mm/10mm/zero-jitter geometry is a diagnostic candidate, not an accepted recipe. Prospective per-component/lesion recall0.90 and union0.95 engineering fidelity screens preserve all cases on failure.

D-321 complete: shared portable physical mapper and registered role-safe triple loader;75new/
2,062native tests, two existing warnings,72.04s. Real exact6/1all7screens pass; all14native/nearest
sheets reviewed. Provided-pancreas10mm/1mm intermediate/144³/zero-jitter recipe accepted only for
engineering subset; nearest lesion recall0.9678–0.9920,union0.9711–0.9962,continuous-reference
argmax0.9516–0.9839. Tiny2973retains123/124nearest,118/124continuous;6238boundary and every
outside-mask reference retained. No model performance/negative/autonomous claim or case filtering.
Fresh scope01619662/profile5cdef929;11synthetic fixtures13.973s/4.567GiB, losses truthfully retained.
Exact request07d3bb4f consumed once:21files,145,701,969hash/145,701,969decode/544,986,944expanded
bytes;183.580s/4.173GiB,receipt5c958ac1(33members). Original wrong/canonical transport pins rejected
before consumption; producer/reader corrected to persisted-byte hashes, regression and fresh
scope/profile/request retained.53producer members independently verified with no new source reads.
Acceptanceb3ff4db9/recipe2382855d; reviewd0d94625(35members/451,678B),all attempts and snapshots.
Old code/schemas/roots and6/1/all12/fiveholds/history unchanged;153localizer/23holds unchanged.
No retained tensor cache/independent keeper claim, training/model updates or pending launch.
[Results](operations/SEGMENTER-GEOMETRY-RESULTS-2026-10-01.md),
[next learning/recovery packet](operations/SEGMENTER-LEARNING-RECOVERY-PACKET-2026-10-01.md): fresh
three-class synthetic learning/CPU+MPS transaction and independent recovery, then new exact real
zero-update cache/model/export qualification and measured short launch. Original requests are not
reusable; formal baseline jitter and autonomous cascade remain separate.

### October1 — fresh segmenter synthetic learning/recovery

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-322|Implement/test separate scratch three-class session/objective/input/checkpoint transaction, then qualify synthetic CPU learning and native MPS independent keeper recovery.|Quinton: “Great, continue to the next.” after D-321.|Invented arrays only; frozen6/1/all12/fiveholds and old producers fixed. Separate bounded segmenter storage capability; no real source/model updates, imports or training launch.|

[Prospective plan](operations/SEGMENTER-LEARNING-RECOVERY-PLAN-2026-10-01.md) freezes synthetic criteria, configurations/resource/recovery limits before diagnostics. Unweighted voxel CE plus present-foreground Dice is a diagnostic candidate, not a formal baseline objective. Actual full144³MPS mechanics and small24³CPU learning remain distinct evidence.


D-322 complete: separate synthetic scratch three-class model/input/objective/sampler/session,
strict checkpoint transaction and independent segmenter backup/restore.85new/2,147native tests,
two existing warnings,75.61s. Unweighted and16×CE/120steps collapse all lesions;256×/120steps
retains three but misses disconnected lesions;256×/360steps gives disconnected Dice0.64below0.65.
All four original-bar failures retained. Fresh256×/480steps passes all positive Dice/recall1,
all five components,negative lesion FP0,pancreas Dice0.9954–1.0;loss ratio0.010739. Original numeric
bars unchanged; objective v3 is synthetic engineering acceptance,not optimal real/formal baseline.
CPU interruption/restart and prediction exact,55.086s/0.880GiB. Native144³MPS three committed steps,
dirty fourth optimizer call refused;25.458s/2.950GiB RSS/4.879GiB driver. Cold native recovery
9.812s/2.772GiB/4.949GiB driver;probe0,nextweights1.49e-8,nextloss0,native inverse exact.
All six current CPU0/30/480 and MPS0/2/3checkpoint payloads independently backed up/restored with
external primary reads blocked.216physical files/30diagnostic members byte-checked. Failed-trial
weights remain local scratch. Scoped capabilitya2741671;global registry/old producers unchanged.
Reviewb85ceed55 (63members/494,485B),acceptance8a061fdb;failed tests/trials/helper/verifier faults
and source snapshots preserved.2,407synthetic optimizer calls excluding unit tests;zero real arrays/
updates.6/1/all12/fiveholds,original protected roles and153localizer/23holds unchanged.
[Results](operations/SEGMENTER-LEARNING-RECOVERY-RESULTS-2026-10-01.md),
[next zero-update qualification](operations/SEGMENTER-ZERO-UPDATE-QUALIFICATION-PACKET-2026-10-01.md):
new role-safe cache/fresh21-file build,all7unchanged-weight MPS/native exports,separate14-target
original-reference scoring and real-input checkpoint recovery. No real cache/pending launch or
new source request;old D-321 consumed. Historical checkpoint inventory/import-denial audit remains
before real training;synthetic trained weights are not real initialization. One validation positive/
no negatives supports engineering only;formal jitter/cascade/generalization remain separate.


### October 2 — qualified segmenter input cache

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-323|Implement/test role-safe persisted segmenter cache, qualify synthetic resources, then freeze and execute a fresh exact seven-case cache-build scope and independently resolve the cache.|Quinton: “Great, continue on.” after D-322, with standing bounded-work autonomy.|New 21-file read capability after qualification; no model/optimizer updates, imports, cohort changes or global source activation.|

[Prospective cache plan](operations/SEGMENTER-CACHE-QUALIFICATION-PLAN-2026-10-02.md). Old D-321 request remains consumed; producing code stays immutable. Real-input inference/export and original-reference scoring remain subsequent bounded transactions.


D-323 complete: separate role-safe three-class persisted cache/consumer,68new/2,215native tests,
two existing warnings,73.73s. Exact6/1all7input views reviewed;transforms/fidelity/counts equal D-321.
Tiny2973/boundary6238and all12/fiveholds preserved;optimizer closed,inference has no target. Cache
16members/104,576,736B,rawpayload104,509,440B,completion90b8cc94,bindingcdd7c707,cap06a72207.
First consumed88568c20request stopped before first file open/hash/decode;zero arrays/cache. Exact21
stat-only proofb0574622finds only volatiledevice16777243→16777239,same APFS UUID/otherfields. Old
observations/code preserved;wrapper accepts only pinneddevice refresh,not hash/path/inode/time changes.
Fresh profile63332c33,requestd84cdcdc consumed once:21original hashes match,145,701,969B hash/same
decode,544,986,944Bexpanded;193.053s/3.413GiB. Cold replay156.701s/0.986GiB,zero rawreads/model.
28diagnostic/18physical files independently checked,acceptance8b21315b;reviewf7440f39(42members/
797,102B),all attempts/snapshots retained. Cache/review derivedlocal,no independent keeper claim.
Roots/D-319–322 producing code andoriginalprotected roles/153localizer/23holds unchanged.
[Results](operations/SEGMENTER-CACHE-QUALIFICATION-RESULTS-2026-10-02.md),
[next real-input inference packet](operations/SEGMENTER-REAL-INFERENCE-PACKET-2026-10-02.md): separate
scratchstep0task,all7zero-update MPS/native exports/task keeper recovery,then fresh14-target original
scoring. Both D-323 source requests consumed;no model/update/pending training/global activation.
Historical import inventory/real optimizer transaction remain before exact short launch;synthetic
learned weights cannot initialize realtask. One validation positive/no negatives is engineering only.

### October 2 — real-input scratch segmenter inference

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-324|Implement/test the distinct step0 inference codec, synthetic MPS/native export profile, then one fresh exact7-image cache inference and independent semantic keeper recovery.|Quinton: “Great, continue on.” after D-323; standing bounded-work autonomy.|No optimizer/imports/original source arrays, cohort changes or source activation. Separate14-target scoring and training transaction remain.|

[Prospective plan](operations/SEGMENTER-INFERENCE-QUALIFICATION-PLAN-2026-10-02.md). Protect all native masks plus checkpoint/controls/probe on independent storage; local sheets and input cache remain scratch. Freeze quota ceilings before first publication; recovery probability tolerance1e-6/native codes exact. Existing D-319–323 producers remain unchanged.

D-324 review found the first recovery audit hook checked absolute path prefixes but Python's
`open` audit event omits `dir_fd`, so it did not prove denial of component-by-component directory
walks. Earlier recovery records remain intact; no primary read was observed, but their denial claim
is limited. Add a separate guarded-recovery layer: audit path components and file/list descriptors,
and resolve `os.open(...,dir_fd=...)` using macOS F_GETPATH before opening. Re-run both synthetic
and real independent recovery under the original absolute quota ceilings; no producer/request
code edits, inference repeat or model updates. Supplemental source and receipts remain separately
pinned. Twelve new absolute/component/descriptor/symlink/independent-domain tests pass.

D-324 complete:2,287native/72new tests,2existing warnings,73.53s. Fresh7cache images,144³MPS,
all native exports/7sheets,zero updates/sourcearrays/imports;weights3ee49a53unchanged.177.563s/
5.312GiB RSS/1.400GiB sampled driver. All12members/202,895,580B independently protected;
rawnative136,244,888B. Descriptor-aware guard fixes initial absolute-only audit limitation.
First supplementalpipe failure retainedb82ef16e; repaired14guard tests. Attempt02 syntheticrestore
passes;duplicate realcopy refused by2payload+2MiB retry reserve,partial e1a6ff1a preserved.
No quota increase/reset/deletion. Attempt03 fresh cold existing-independent-copy replay validates
all12against backup and model/nativeprobe:delta0/nativeexact,3.463s/1.877GiB,no registeredwrites.
Frozen1GiB additional-domain quotas unchanged;89physical/47jobfiles+18cachefiles checked.
Acceptance7cb2ba5d,review11a11afe(28members/1,407,176B). All6/1/all12/fiveholds,153/23,
originalroles/D-319–323 producers/registry unchanged. Both inference requests consumed,nonepending.
[Results](operations/SEGMENTER-INFERENCE-QUALIFICATION-RESULTS-2026-10-02.md),
[next original-native scoring](operations/SEGMENTER-NATIVE-REFERENCE-SCORING-PACKET-2026-10-02.md):
fresh14-target stats/hash/decode/metrics scope,then historicalimport inventory and realoptimizer
transaction before exact shortlaunch. NativeDice notyet scored;onevalidation/no negatives engineering.

### October 2 — original-native segmenter scoring

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-325|Implement/test/qualify target-only native scoring, freeze and run one fresh14-target scope, protect and recover all scoring/source/control evidence.|Quinton: “Great, score them now. Continue on.”|No CT/model forwards/updates/imports/eligibility or global activation. D-319–324 producers and registry immutable.|

[Prospective plan](operations/SEGMENTER-NATIVE-SCORING-PLAN-2026-10-02.md). Original lesions take precedence including outside-pancreas voxels; all reference components and prediction failures remain scores. New64MiB domain capability/absolute ceilings include publication retry reserve; no D-324 quota reset. Original truth arrays remain scratch, numeric/provenance records independently protected. Real training remains a separate transaction.

D-325 complete: original-native step0 baseline accepted; all seven cases and fourteen original
pancreas/lesion references, no CT/model forward/update/import. 72 new / 2,359 native tests pass,
two existing warnings,90.63s. Training macro lesion Dice0.001779/recall0.012986; one validation
Dice0.000061/recall0.000532. Three train lesions have zero overlap; validation one TP voxel.
Tiny2973, boundary6238 and all original components/outside-pancreas voxels remain in denominators.
First9525baef request failed its transport/canonical hash guard before original payload reads;
consumed failured0ed2d57/source5274f03b retained. Canonical-byte repair tested before fresh
requeste24cef49 completed once:183.935s/1.951GiB RSS; fourteen hashes and exact1,265,220B each
hash/decode,272,494,704B expanded. Five protected members/101,447B cold independently restored
with primary denied,1.140s/75.45MiB; original64MiB domain ceilings retained. 27physical/27jobfiles
independently audited. NumPy/Python macro floating difference≤1.39e-17 recorded and review corrected,
integer counts/per-case formulas exact; scores unchanged. Acceptancef4bfcaf0/review945d1e50,
14members/98,480B. D-319–324 code/registry/6/1/all12/fiveholds/153localizer/23holds unchanged.
Both source requests consumed,no training request/promotion. Results and next transaction packet:
[Native scoring results](operations/SEGMENTER-NATIVE-SCORING-RESULTS-2026-10-02.md);
[real training transaction proposal](operations/SEGMENTER-REAL-TRAINING-TRANSACTION-PACKET-2026-10-02.md).
Historical import denial/new qualified optimizer consumer/sampler/evaluation/interruption/keeper
qualification precede a separate exact short launch. Existing optimizer gates remain closed.

### October 2 — real segmenter transaction qualification

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-326|Implement and synthetically qualify the separate real-task optimizer/cache/sampler/checkpoint/evaluation transaction and bounded historical byte-hash inventory.|Quinton: “Great, continue on.” after D-325.|No real optimizer updates, original source arrays, weight imports, membership changes, global activation or automatic launch. Accepted D-319–325 producers stay fixed.|

[Prospective plan](operations/SEGMENTER-TRAINING-TRANSACTION-PLAN-2026-10-02.md). Exact short real training is prepared only from measured readiness and retains a separate launch decision.

D-326 complete:96 new/2,455 native tests, two existing warnings,84.52s. Historical203 files/
8,240,982,194B pure-byte inventory;17,021 tensor-cache payloads excluded,no weight imports.
Separate qualified6/1 input boundary/session/sampler/checkpoints pass. CPU6 committed/exposure1
all6:18.019s/1.586GiB; cold0/2/3/6 exact probabilities/nextweights:8.484s/1.194GiB.
MPS3 committed/dirty4th refused:47.014s/5.271GiB/4.887GiB driver; cold0/2/3 probability0,
nextweights1.68e-8/nativeexact:22.324s/4.463GiB. Producer MPS4 invented calls plus separate
recovery1; CPUproducer13 plus recovery1. Seven checkpoints/two probes independently restored.
Real7-cache bridge169.576s/1.248GiB, zero forwards/updates/original arrays; roles/targetcounts exact.
Supplemental invented144³ step0 old/new probabilities/native masks exact,3.407s/2.954GiB;
initialweights3ee49a53 supports D-325 before baseline under unchanged policy/cache/geometry.
FirstCPUrequest retired unconsumed/source preserved before completion-bound resume strengthening.
Restricted review DiskManagement unavailable; source/reason retained, native audit then passed:
339physical/60jobfiles,96producing pins/registry exact; primary518,961,193B/independent
11,283,770,932B within new qualification-only frozen ceilings,no older quota reset/deletion.
Acceptancef7a2f6d9,review2a1c24de(18members/251,150B). D-319–325/6/1/all12/fiveholds/153/23
unchanged. Real updates remain denied; all qualification requests consumed,nonepending.
[Results](operations/SEGMENTER-TRAINING-TRANSACTION-RESULTS-2026-10-02.md);
[next completion packet](operations/SEGMENTER-SHORT-RUN-COMPLETION-PACKET-2026-10-02.md):
real executor/approval dispatcher,cadence/interruption,trained export/fresh14-target final scoring,
keeper/resource rehearsal before freezing a separate48-update candidate request. Rate0.0003/
48updates remain prospective; no exact real launch,extension,eligibility,cascade/jitter/promotion.

### October 3 — short segmenter executor and launch preparation

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-327|Implement/test the bounded short segmenter executor, trained native evaluation/export evidence and keeper/cancellation path; run full invented MPS rehearsal/cold recovery; prepare the exact48-update real request.|Quinton: “Great, continue to the launch executor etc.”|No real updates/original payload reads/imports/eligibility or source activation. Separate exact launch approval remains required.|

[Prospective plan](operations/SEGMENTER-SHORT-LAUNCH-PLAN-2026-10-03.md). D-319–326 accepted producers/registry/cohorts/holds immutable; original14-target stat-only preparation allowed.

D-327 complete:119 new/2,574 native tests, two existing warnings,92.03s. Full invented144³48-update
producer257.567s/5.495GiB RSS/4.879GiB sampled driver; exposure8 all6,0/6/24/48checkpoints and
all7native exports/scores/views. Cold14-artifact restore50.571s/4.360GiB with primary Python reads
blocked; four probes and7 native predictions exact,nextweights1.49e-8.48invented producer calls
plus1invented cold6→7call; zero real optimizer calls/original payloads throughout. Real cold adds0calls.
387protected physical/29jobfiles audited;111source pins/registry exact. Two read-only review-helper
faults preserved/corrected; no producing code/request changes.14target stats unchanged; real cache
ancestry replayed,no forwards/updates.6/1/all12/fiveholds/localizer153/23 unchanged, no quotareset.
Review09d78ecc (41members/662,196B),acceptance158a5d17,readinesse423cc91. Exact CAP-EXP-013
request `outputs/prowl/CAP-EXP-013-PREPARED-20261003/request.json`, SHA
`eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9`, remains UNCONSUMED/NOT LAUNCHED.
Freshseed42/144³/zerojitter/v3CE256+Dice/AdamW0.0003/48updates; terminal primary;30min total,
20min producer/5min cold/12GiB RSS+driver; final14target hash/decode1,265,220B each/272,494,704B
expanded,zeroCT.14required protected artifacts including selected7image bundle. New real areas
empty;2GiB primary and14,892,449,687B independent whole-root frozen ceilings, separate exact user
approval still required. Learning screens frozen before launch: all6original-native cases/components,
D-325 before baseline,2514separate; no extension/selection/eligibility/formal model promotion inferred.
[Results](operations/SEGMENTER-SHORT-EXECUTOR-RESULTS-2026-10-03.md); [exact launch review](operations/CAP-EXP-013-LAUNCH-REVIEW-2026-10-03.md). Next is the separate exact launch decision.

### October 3 — exact CAP-EXP-013 launch approval

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-328|Launch the exact prepared CAP-EXP-013 once, then independent cold recovery, native before/after scoring and inspection.|Quinton: “Yes, full approve. Continue on.” in response to the exact D-327 launch review.|48 committed real updates,6train/1evaluation-only,0/6/24/48 cadence,30min total/20min producer/5min cold/12GiB RSS+driver; final14-target scope. No CT rereads, imports, continuation, automatic extension, eligibility changes or promotion.|

Request SHA `eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9`. Preserve D-327 producing sources, exact request, absolute storage ceilings and prior evidence. Launch only after current stat-only target/source/runtime/storage/power checks pass. [Frozen review](operations/CAP-EXP-013-LAUNCH-REVIEW-2026-10-03.md).

D-328 complete: exact CAP-EXP-01348realupdates on6train/1evaluation-only,exposure8each,
0/6/24/48checkpoints/evaluations. Native lesion train/validation Dice0.030886/0.025448 and
recall0.994807/0.974468 pass frozen initial signal, BUT all7native pancreas-class counts/overlap0,
lesion volumes35–835×reference; no promotion. Saved tensor pancreas overlap0 bystep6; case3
pancreas probabilities finite but no argmax winners at24/48. Denominator shares suggest possible
loss imbalance,not measured gradients/proved cause. All cases/components/original references retained.
Producer367.416s/4.755GiB RSS/4.879GiB sampled driver; cold32.464s/4.119GiB with primary Python
reads blocked,four probes/7native exact,14artifacts independently restored;0coldoptimizer/originalreads.
403.118s(6.72min) total supervised.14original targets exactly1,265,220B hash/same decode/
272,494,704B expanded;zeroCT.387physical/29jobfiles,111source pins/registry exact; producingcode
unchanged,2,574-test qualification baseline unchanged.7technical views checked;no runtime/review faults.
Requiredpayload583,004,143B,primary583,047,635B/independent13,911,176,703B within unchangedfrozen
ceilings,no quotareset/deletion. Approval9f48d34c,producer23cf88bd,recovery744cf4cc;review633c7e09
(43members/658,643B),acceptance846c4aca.6/1/all12/fiveholds/localizer153/23 fixed. Requesteec73450
and both real jobs consumed;no pending run/continuation/autoextension/imports/source activation/formal registration.
[Results](operations/CAP-EXP-013-RESULTS-2026-10-03.md); [next proposal](operations/CAP-EXP-013-CLASS-COLLAPSE-FOLLOWUP-2026-10-03.md): bounded training-only zero-update objective/gradient audit, then select/qualify one loss-balance factor for a fresh same-cohort48-update comparison. No new analysis or training request is frozen/authorized.

### October 3 — bounded class-competition audit

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-329|Implement, qualify and execute the separately frozen training-only zero-update CE/Dice/head-gradient audit of CAP-EXP-013.|Quinton: “Great, continue on” after the class-collapse follow-up recommendation.|Six training cases at0/6/24/48;24 forwards/48 separately counted CE/Dice head VJPs; no optimizer calls, original payload opens, validation model evaluations, producing source changes, membership changes, imported initialization or new training.|

[Prospective plan](operations/SEGMENTER-LOSS-AUDIT-PLAN-2026-10-03.md) specifies the numerical reductions, role boundary, resource/read ceilings and independent numeric preservation. The head-only eval-mode clone measures final-convolution gradients, not full-backbone or AdamW updates. The original proposal's24 evaluations are24 paired-term diagnostic transactions;48 VJPs are explicit, with no third query for their sum. Native invented144³ rehearsal qualified:6 forwards/12head VJPs plus2logit-oracle queries,0updates,9.288s/1.036GiB RSS/1.571GiB sampled driver; analytical max error3.64e-12. Profile receipt4cb924ce. Exact real audit request SHA `6f4fdbc801aa996a60dd0e8228c2d455e35872ef5933043f8cd6dd24214e170a`, limited to900s/12GiB/32MiB local numeric output. The request must pass current native tests/source/runtime/ancestry checks before consumption. No changed-loss real training is authorized.

D-329 prelaunch correction: the first wrapper printed `digest(canonical(request))`, while the saved
`source.put` encoding omits canonical's newline. The prelaunch SHA check refused it before consumption,
real cache resolution or model evaluation. Preserve the unconsumed first request (actual SHA d39688dc)
and profile, plus the refusal record. The isolated wrapper now prints the persisted bytes' hash; a new
regression covers this. New attempt02 profile receipt4d3a09e5; exact persisted real request
`97e75261e9200d1d9dbb8bccebcd06be4dddf836ec66e5083947d41765497fb6` at
`outputs/prowl/SEGMENTER-LOSS-AUDIT-attempt02-20261003/request.json` supersedes the unconsumed
first diagnostic request. This is a reviewed pre-consumption correction, not an automatic retry of a
consumed job. Accepted111 producers and CAP-EXP-013 remain unchanged.

D-329 complete:26new/2,600native tests (98.72s),24training-only case/checkpoint observations,
24forwards/48head VJPs,zerooptimizer/original payload opens/validation evaluations; all saved model,
optimizer,RNG/progress transactions unchanged. Real worker200.359s,202.195supervised,1.666GiB RSS/
1.571GiB sampled driver. Four payloads188,625,652B, full cache verification104,576,736B; six unique
persisted pairs89,579,520B, repeated four times358,318,080B logical model consumption. No quotareset.
All24 total pancreas bias gradients point downward under plain descent; CE exceeds Dice head norm
11.53–84.09×. CE mean pancreas bias0.378→0.190 vs opposing Dice−0.000939→−0.002756; causal
and full-backbone/AdamW conclusions remain unsupported. Training-only predeclared fixed-logit weights
[1,16,256]/[1,32,256]/[1,64,256] change early bias direction in0/12,6/12,12/12 observations.
Provisional64pancreas candidate only; current objective remains v3. Bias reconstruction6.11e-8;
no new model/cache/original reads for this arithmetic screen. Synthetic learning/recovery and a fresh
separately approved exact real request remain required.

Native tests record558a022d, profile4d3a09e5, consumed request97e75261, auditd78be296,
interpretatione3f509b1, candidates25d43660; independent numeric manifest254a28f1,56files/810,813B.
NewD32916MiB numeric-only capability retains the earlier global ceiling; whole-root13,911,176,703→
13,911,987,516B. Primary Python reads denied during independent readback; no OS security claim.
Prelaunch print-hash refusal and subsequent read-only NumPy serialization fault retained/fixed;
no consumed audit rerun, optimizer calls or accepted producer edits from repairs.111producer pins/
registry/cohorts/allholds fixed. No pending training, imports, extension, promotion or registration.
[Results](operations/SEGMENTER-LOSS-AUDIT-RESULTS-2026-10-03.md);
[next qualification packet](operations/SEGMENTER-LOSS-REBALANCE-QUALIFICATION-PACKET-2026-10-03.md).

### October 3 — dispatch of provisional pancreas-weight qualification

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-330|Implement and qualify the isolated v4 `[1,64,256]` candidate through the synthetic learning gate, then conditional native MPS/recovery.|Quinton: “Great, continue to the next” after D-329's results and next qualification packet.|No real inputs/optimizer calls, accepted producer edits, old request reuse, imports, eligibility changes or real launch. Two480-update invented CPU trajectories, original learning bars, exact interruption/restart; stop before MPS if learning fails.|

[Prospective qualification plan](operations/SEGMENTER-BALANCED-QUALIFICATION-PLAN-2026-10-03.md)
and [packet](operations/SEGMENTER-LOSS-REBALANCE-QUALIFICATION-PACKET-2026-10-03.md) define the
new loss/task/schema, CPU budgets and unchanged pancreas/tiny-lesion/negative screens. The synthetic
transaction is separately versioned from the accepted v1 implementation; old producer pins and
checkpoint decoding remain untouched. Provisional numerical mechanics do not accept a real recipe.

D-330 complete with a **failed learning gate**:38new/2,638native tests(93.01s), isolated provisional
v4 numerical/transaction checks pass. Frozen CPUrequest7ee8240c consumed; two480-update trajectories,
960synthetic calls total,30update SIGTERM/fresh450restart exactmodel/optimizer/RNG/progress/predictions.
55.846s total,maxworker0.728GiB; zero real inputs/calls/originalarrays/imports. Sparse/multiple/boundary
lesion Dice/recall0;outside0.470588/0.333333;pancreas0.955–0.968,negativeFP0,lossratio0.258607.
All4positive lesion Dice/recall bars fail,4/5componentsmissed. Do not accept the candidate or proceed
through its conditional MPS stage. Current real v3 recipe remains fixed; no new MPS/real request.

Independent review reproduces counts/bars/full-state equality. Denominator arithmetic explains a
potential allocation issue: in sparse synthetic targetv3pancreas17.25%/lesion12.91%,v4pancreas93.03%/
lesion1.09%; these are shares,not measured gradients or causalproof. Next recommended factor is
per-case present-class mean CE, with unchanged foreground Dice and original bars, separately specified
and not implemented/accepted/launched. Never remove tiny/boundary targets or soften the gate.

CPUpackaged298c9d3 (59files/188,880,118B); tests5f304229;independentreviewd94295ab. FreshD330
256MiB failed-qualification snapshot preserves67files/188,947,673B and four8-member checkpoints,
all decoded under primary Python read denial,0extra model/optimizer/original reads. Manifest a69e1f78,
capability0a3a0eaf;whole-root14,100,935,189B below unchanged14,892,449,687B earlierceiling.
118producing/source pins(114prior+4new)/registry/cohorts/allholds exact; no unexpected runtime/review
faults,oldsource edits,quotareset,deletion,eligibility changes,promotion or formalregistration.
[Results](operations/SEGMENTER-BALANCED-QUALIFICATION-RESULTS-2026-10-03.md);
[next proposal](operations/SEGMENTER-CLASS-NORMALIZED-CE-PROPOSAL-2026-10-03.md).

### October 3 — dispatch of class-normalized CE qualification

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-331|Implement/qualify isolated v5 per-case present-class mean CE with preserved foreground Dice and original synthetic learning bars; native MPS/recovery follows only if CPU learning passes.|Quinton: “Great, move onto the next” after D-330 failure and the class-normalized proposal.|No real inputs/optimizer calls/imports, accepted producer edits, old request reuse or eligibility changes. Two480-update invented CPU paths, exact actual interruption/restart; no automatic duration extension or real launch.|

[Prospective plan](operations/SEGMENTER-NORMALIZED-QUALIFICATION-PLAN-2026-10-03.md) and
[exact numerical proposal](operations/SEGMENTER-CLASS-NORMALIZED-CE-PROPOSAL-2026-10-03.md)
are the scope. Equal class means change the CE allocation/reduction factor; architecture/targets/
seed/optimizer/sampler and original pancreas/tiny-lesion/component/negative gates remain fixed.
A numerical or mechanics pass does not waive a failed learning gate or establish real CT performance.

D-331 complete with a **failed learning gate**:40new/2,678native tests(100.76s), isolated v5
per-case present-class mean CE numerical/codec checks pass. CPUrequestbfd4b3a2 consumed once;
freshseed42/24³/AdamW0.003, two480-update paths,960invented calls, actualSIGTERM30/fresh450restart
exactmodel/optimizer/RNG/progress/predictions.58.084s total, maxworker0.750GiB. Lossratio0.353020/
allpancreasDice0.831–0.848 pass, but allpositive lesionDice0.021–0.047 fail; sparse/boundary/outside
recall1.0, multiple0.25/onecomponentmissed. NegativeFP368/13,824=0.026620 fails0.02. StopbeforeMPS.

Independent numeric/fullstate review reproduces failure. Separately frozen inspectionrequest9e964704
consumed:teninventedCPUforwards/zerooptimizer/original/real/validationreads,1.155s/0.582GiB;
all savedlosses/metrics reproduce, complete transaction state unchanged. Falsepositives occurontrue
backgroundandpancreas (negative151/217). Last20v5epochmeans0.757289–1.340302,terminal0.850028,
earlierminimum0.516616; fluctuation is notcausalproof orcheckpointselection permission. Nextproposed
singlefactor: freshv5constantCPU LR0.001 versus retained0.003, same480/originalbars. Proposal only,
notimplemented/frozen/launched; no automatic sweep, duration extension or realrequest.

CPUpackage52211138(59files/188,884,855B),testsc5185bd6,review59dcf67b,inspection2057c97d;
newD331256MiB completefailedsnapshot73files/189,009,159B,manifest681726f9/capability9b8906ec.
Everyhash/four8-memberCPdecodes independently verified under primaryPythonread denial;zeroextra
preservationforwards/updates/originalreads. Whole-root14,289,944,348B belownew14,369,370,645B
and earlier14,892,449,687B ceiling; registry/capsfixed,no deletion/quotareset.122sourcepins/accepted
producers/cohorts/holds unchanged,no unexpectedfaults,noMPS/realtraining/imports/promotion/registration.
[Results](operations/SEGMENTER-NORMALIZED-QUALIFICATION-RESULTS-2026-10-03.md);
[next optimization packet](operations/SEGMENTER-NORMALIZED-OPTIMIZATION-PACKET-2026-10-03.md).

### October 3 — dispatch of controlled v5 low-rate qualification

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-332|Implement and qualify fresh v5 CPU LR0.001 versus retained0.003, with original480-update learning bars; conditional native MPS and independent recovery only after a pass.|Quinton: “Great, continue on with that” following D-331 results and optimization packet.|Single-factor LR comparison; same fixtures/seed/sampler/objective/decay/terminal480. No real inputs/updates, old source edits, imports, sweep/extension, eligibility changes or real launch.|

[Prospective plan](operations/SEGMENTER-LOWRATE-QUALIFICATION-PLAN-2026-10-03.md) defines the
fresh task/identity, two-path actual interruption/restart, original gates and independent preservation.
A synthetic pass does not establish real CT performance or approve a new real optimizer setting.

D-332 complete: **all original low-rate synthetic learning gates pass**. Only CPU LR0.003→0.001;
same v5/seed42/24³/five fixtures/480. Pancreas/positive lesion Dice/recall1.0, all5 components hit,
negativeFP0, lossratio0.006461.960 invented qualification calls, actualSIGTERM30/fresh450 exact
fullmodel/optimizer/RNG/progress/predictions.62.786s/maxworker0.748GiB; no real or original arrays.
Independent review recomputes integer metrics, unchanged bars, exposures and complete state.

First requestab730d92 consumed then sandbox `/bin/ps` denied; child exited before required
worker-start/model construction,0updates. Fault package98ff446e/12files100,781B retained. No
auto-review rejection. Corrected native execution/preflight in isolated attempt02 wrapper, binding
all125 first-source pins; new regression covers source ancestry (including a self-import corrected
before the first request) and zero-update failure. Separate request7b5e649d/package64b7ae4d,
64files188,904,572B; no consumed rerun or prior source edits. All failed evidence stays preserved.

Conditional fresh144³/v5/MPS0.0003 request089f975e/package3e13f53a consumed once. Producer4clean
updates+1deliberately dirty step4 repeat fromsaved3, coldnext3 once:6invented optimizer calls/8forwards.
Clean0/2/4 eight-member checkpoints independently restored with primaryPythonreadsdenied. Probability
delta0, native export/inverse/derived-invented-target scores exact; nextlossdelta0/nextweight1.033e-8.
47.285s combined/maxRSS2.818GiB/driver4.839GiB. Step2 native lesion mask is empty (0/4,140TP),
retained; no native480-learning, original-reference or real-performance claim. Dirty operations refused3.
Zero real updates/original reads/imports. Final65new/2,743native tests(94.05s), two existing warnings;
all129 source pins/registry/cohorts/holds exact. Current real v3 and CAP-EXP-013 terminal48 unchanged.

Independent CPU/fault snapshot87files189,101,113B/four8-memberCPs; native32files227,218,858B/
three8-memberCPs; numeric30files175,563B, everyhashverified. Manifests03973c58/3fd1ed40/4158dbeb.
Whole backup root14,706,439,882B below fresh14,714,652,927B numeric/native14,814,589,781B and
retained D-32814,892,449,687B; no deletion/quotareset/registry increase. Completed scopes' narrower
transaction caps stay historical, unchanged and consumed. Original ps fault is the only unexpected
execution fault; no unexpected native/recovery/review fault. All three requests consumed, no pending
real consumer/request/launch, autoextension/eligibility/source activation/promotion/registration.

Only186,009,805B remain below retained D-328 ceiling. Next packet proposes separately versioned
real v5 consumer and invented executor/recovery qualification, fresh14-target scope, same6/1/48/LR0.0003,
training-only numeric comparison screens and explicit reviewed new stage backup allowance. No silent
ceiling expansion; review concrete capacity/request before related external writes/launch. This next
packet is not implementation dispatch, accepted real recipe or launch approval.
[Results](operations/SEGMENTER-LOWRATE-QUALIFICATION-RESULTS-2026-10-03.md);
[next packet](operations/SEGMENTER-V5-REAL-COMPARISON-PACKET-2026-10-03.md).

## D-333 — isolate v5 real consumer; capacity-gated full rehearsal prepared (2026-10-03)

Quinton's “Great, continue” authorizes the D-332 packet's bounded implementation. It does not
approve an increased backup ceiling or a real launch. Separate v5 session/config/state/progress,
executor/target/export/probe/summary/backup/dispatcher implemented; accepted numerical objective
and all129 producing pins preserved.142 source pins include13 new implementation/test files.
2,933 native tests/190 new pass(118.03s), two existing warnings. Complete six-update CPU unit
cadence/save/reload/terminal policy passes; full144³48-update transaction and independent recovery
remain unexecuted. Invented unit replicas are not independent-media evidence. No real updates,
original/processed-real-array reads, dependencies, cohort/hold/source/rights/promotion changes.

Real comparison proposed/fixed in code: same6/1/48/seed42/144³/zerojitter/0.0003/decay1e-5,
v5 CE allocation only,0/6/24/48, terminal48 primary. Exact training pancreas Dice>.08413627515978402
and TP eachcase>0; lesionDice≥.03088619116270695, macrorecall≥.8/allcomponentshit; report excess
foreground/FPvolume/precision.2514 selects nothing. No numeric volume bar, specificity/usability
or promotion claim. Fresh14-target stage is proposed only: hash/decode1,265,220B, expanded272,494,704B,
0CT; prior grants consumed. Descriptor-only preparation reads no arrays; fresh real stat/readiness
and actual capacity still required before a real request.

Read-only source/package/manifest/domain review verifies3 sealed consumed jobs,32 primary and149
independent members. Whole backup14,706,439,882B remains below unchanged D-32814,892,449,687B;
only186,009,805B left. Exact invented48 rehearsal request8e2dcc5d and capabilitya318b3b6 prepared
locally, unconsumed. Proposed2GiB new primary/backup-root allowance/fixed whole ceiling16,853,923,530B,
within unchanged registered20GiB; conservative keeper+restore+controls1,974,853,376B/headroom172,630,272B.
No external writes/directory creation/capreset/deletion or fabricated approval. Exact storage authority
must match capability bytes and explicitly grants no real launch. Prospective real2GiB outline requires
actual post-rehearsal rebasing and separate review. Request Quinton's concrete invented-rehearsal/capacity
approval first, then full native transaction/14 cold restores and measured resources, then freeze the
fresh exact real request for separate launch review. No pending launch-ready real request or extension.

Pre-freeze full suite caught a new size guard placed in control validation:10fail/122setup errors;
fixed at checkpoint boundary,190focused and2,933finalnative pass. Local system-Python helper initially
failed before capability creation; dependent preparation remained unconsumed. Venv preparation succeeds.
Read-only helper count corrected143→142 before review output. All logs/fault evidence retained locally;
no unexpected launched-job fault or automatic approval rejection. No commit/push/Claude-lane edits.
[Results](operations/SEGMENTER-V5-EXECUTOR-RESULTS-2026-10-03.md);
[concrete rehearsal/capacity review](operations/SEGMENTER-V5-REHEARSAL-REVIEW-2026-10-03.md).

## D-334 — exact invented v5 rehearsal and2GiB capacity approved (2026-10-03)

Quinton's “Great, continue on with that.” approves the concrete D-333 invented48-update rehearsal,
independent recovery and2GiB storage allowance. Exact request
`8e2dcc5d3401094e1e3c5e8b83c05e89ecc2bc615086eddda20efae2ddf0a05c`, capability
`a318b3b6681c3fde0883b7ecaf730e4266a6883e6463fb2698912e858a044ab3`.
Maximum new primary/backup-root bytes2,147,483,648; fixed whole-backup ceiling16,853,923,530B,
registered20GiB unchanged. No deletion, quota reset, source activation or real-launch authority.
Fresh seed42/144³/v5/0.0003/48/6inventedtrain+1inventedeval;0/6/24/48/terminal48. One producer48
invented calls and one separate cold-recovery invented next update; restore14artifacts with primary
Python path/descriptor reads blocked. Zero original/source/processed-real arrays or real updates.
No automatic rerun, extension, filter or imports. Frozen142 producing pins and2,933-test baseline
must remain unchanged. Native preflight and exact storage-approval transport precede consumption.
After successful measured/audited qualification, accept readiness and prepare fresh14-target metadata,
actual real-stage capacity and exact CAP-EXP-014 request for separate review/launch approval.
[Approved scope](operations/SEGMENTER-V5-REHEARSAL-REVIEW-2026-10-03.md).

### D-334 completion — rehearsal accepted; no real launch

Exact once-only producer48 and cold1 invented calls pass. All14 artifacts/387 physical files independently verified, seven exports/sheets reviewed; probe0/nextweights7.45e-9. Combined363.490s; frozen142 pins/2,933-test baseline unchanged. Accepted readiness and fresh14-target stat-only metadata; zero real/source/processed-real reads/updates. Preserve controls within approved2GiB/fixed16,853,923,530B ceiling. Next exact real request/capacity review; no real-launch authority or extension. [Results](operations/SEGMENTER-V5-REHEARSAL-RESULTS-2026-10-03.md).

### D-334 real proposal prepared; separate approval pending

CAP-EXP-014 exact request `e63f5613085bf202bbb1157616afc7492f84e0855e81d243dd3981ed41ec4a10`; conditional storage capability `85b9a90c4a1bb1042ad208d4c14d1b7d87c71caf8db16abd8c194e39822e5024`. Measured post-main-preservation base16171162225B, proposed fixed ceiling18318645873B within20GiB; no quota reset/deletion. Fresh14-target stat scope, accepted processed-cache resolution for preparation only; zero original arrays, model forwards or real calls. No real storage/launch authority or areas/consumption. Same6/1/48, terminal48, training-only screens,2514 report-only. [Concrete review](operations/CAP-EXP-014-LAUNCH-REVIEW-2026-10-03.md).

D-334 final review correction: earlier `85b9a90c` is the canonical semantic real capability hash, not on-disk transport. Actual transport `5dfc16d148d159d4edb2b5fcd2109957deb519821871f118c958e8a9b9e53b51` is authoritative for human storage approval; preparation-review-V2 supersedes the retained mislabeled helper output. Exact requeste63f5613/source/ceilings unchanged; final preservation stopped before destination creation. No real approval or launch.

## D-335 — exact CAP-EXP-014 launch, target reads and capacity approved (2026-10-03)

Quinton's “Yes, full approve. Continue on.” explicitly approves the complete concrete
CAP-EXP-014 review: request `e63f5613085bf202bbb1157616afc7492f84e0855e81d243dd3981ed41ec4a10`,
actual capability transport `5dfc16d148d159d4edb2b5fcd2109957deb519821871f118c958e8a9b9e53b51`.
Fresh seed42, v5 loss, same six training cases and evaluation-only2514, 144³/48 updates,
AdamW0.0003/decay1e-5/constant, zero jitter, checkpoints/evaluation0/6/24/48 and terminal48.
Fresh stage-specific14-original-target hash/decode grant; zero original CT reads. Fixed proposed
ceiling18,318,645,873B is now approved; maximum2GiB new primary and backup-root allowance,
registered20GiB unchanged. No deletion/reset/import/continuation/filter/promotion or extension.
Independent14-artifact recovery and seven-sheet/numeric review follow the one exact run.
Clarification from final code reading: the frozen real cold worker makes zero optimizer calls;
the separately accepted invented rehearsal proves next-update recovery. The launch review's
phrase about an invented cold next update does not add an update to this frozen real worker.
No producing source or request change. Native preflight precedes consumption; preserve failures
and do not rerun consumed requests. [Approved exact review](operations/CAP-EXP-014-LAUNCH-REVIEW-2026-10-03.md).

### D-335 completion — limited training screen passes; no promotion

Exact48 real updates and14 original target reads completed;0CT. Cold14restores/7native predictions/fourprobability probes exact,0cold updates/source reads. Combined525.229s, producerRSS4.790GiB/driver4.776GiB. All5 predeclared training screens pass: pancreasDice0.159877, lesionDice0.055142/recall0.833063,6components hit; oversized12.78–383.26× masks remain.2514 lesionrecall0.123936/Dice0.006397, selects nothing. All7sheets reviewed; integer/component/volume arithmetic and three copies audited.142pins/2,933tests unchanged. Both jobs consumed; no extension/import/promotion/generalization claim/new run. Fixedceiling18,318,645,873B unchanged. Next discussion only: saved training evidence, duration/coverage proposal and varied multiclass cohort readiness. [Results](operations/CAP-EXP-014-RESULTS-2026-10-03.md).

D-335 retained training-history inspection: zero forwards/updates/source/cache reads; terminal independent keeper confirms eight complete epochs, constant0.0003 and mean loss2.037188→1.692695 (ratio0.830898), training tensor overlap still improving at48. Supports a proposed fresh duration comparison; no extra training or new policy authorized. Terminal48 remains primary;2514 not used for selection.


## D-336 — record approved P2 language amendments and seven interpretations (approval 2026-09-28; recorded 2026-10-03)

Quinton's present L1 instruction confirms the decisions Claude recorded in
[RUNNING-LOG](retrieval/planning/RUNNING-LOG.md), entry “2026-09-28: Quinton adopts the Codex
decision-sheet review as the P2 outline (Claude records)”, followed by “Decisions applied; C-25
check; Goddard chaining; run record P drafted”. Approve A1 uppercase whole-token `AI` in block A,
A2 listed `intra-observer` in M, and A3 `reader studies` in W, one concept with `reader study`.
The AI-assisted side effect is disclosed; these are pre-run semantic amendments, not seed tuning.

All seven written interpretations are approved: snapshot is the upper date bound, later issue years
retained/flagged; OtherAbstract/VernacularTitle not matched; only the six listed publication types
exclude; deleted PMIDs remain in reconciliation; seed recall uses stage1; qualifier testing uses the
CORE development sample split after labeling; stage2 licence eligibility is fixed in signed run B.
Historical adoption review SHA-256 `4830b3e48ceb60adacc9c5c5bfbc2603546da1ed973c00de94a15c21d152061e`;
then-applied SEARCH revision8 logged hash `44e0bcb9617568b9e2805c73b4947142fb689b74fcf76f6a30862552e78f96e1`.
The current rev9 policy hash is in D-339. This records the September approval retrospectively;
whole-policy approval did not occur until October3. No selection run or execution permission.

## D-337 — record approved S-01 correction, designated chaining route and provisional subset (approval 2026-09-28; recorded 2026-10-03)

Authority: Quinton's L1 reconciliation instruction and the same September28 adoption/application
entries in [RUNNING-LOG](retrieval/planning/RUNNING-LOG.md). Approve SEED-SET rule12's corrected
S-01 candidate (Suman2021, “Quality gaps in public pancreas imaging datasets: Implications &
challenges for AI applications”, PMID33840636/DOI10.1016/j.pan.2021.03.016); retain the original
appendix citation/conflict, reassess needs and still verify against the P5 final snapshot.
Approve rule1's written designated-source route and designate Goddard2012,
DOI10.1136/amiajnl-2011-000089, for disclosed reference chaining. Designation does not make Goddard
itself a seed. Approve the16 sectionA R candidates provisionally, not as verified/frozen seeds;
C-25 only if scope is supported. P-02/P-03 remain probes and the three negative controls remain.
PANORAMA protocol download remains in principle only, requiring its own signed run record.

Historical SEED-SET rev7 application hash `fd7006a1fd160ae64de5f66d973c52b85dd1c596e6ea6a0567f75be3abe4cc8b`;
latest SEED-SET hash `d68b0b18e1085f87cc413f91ca1ad8b720a86d9d7517cf4eea5dc6006fff604c`
is logged in the October3 corrected/approval entries and verified unchanged. No new abstract reading,
identifier verification, freeze, signature or download follows from this record.

## D-338 — record October3 P2 working priorities, reserves and family2 delegation (2026-10-03)

Authority: Quinton's L1 instruction and [RUNNING-LOG](retrieval/planning/RUNNING-LOG.md), entry
“2026-10-03: Quinton's round-2 decisions; family 2 resolved by chaining; PANORAMA status (Claude)”.
Accept sectionA2 C-31/C-32/C-33 provisionally; verify C-36; keep C-34/C-35/C-37/C-38 as reserves;
C-39 stays outside the initial subset. Keep all11 sectionA O candidates as reserves. Leave the
family2 second-candidate route to Claude's judgment within existing disclosed planning routes.
Claude's subsequent C-10 chaining and moving C-25's scope check to the local P5 snapshot are
Claude's actions, not invented separate Quinton approvals. N5.1 remains directly uncovered;
analogy/background does not satisfy the frozen need. Questions about already-acquired PANORAMA
imaging did not sign or download its separate protocol PDF.

The round2 corrected candidate hash was `7fcd2b783c9b99c55085f70a48e32220b4a2ca9abea072874b5b7b60bfcc044f`;
final draft8 approval hash is `eceaa8bf57c7863f9cb2c1842f893b5e1d386002f05786364ca12099eda195f2`.
Current decision sheet hash `8f3abc520162a8edca3fc70bbe18c5ba48fc68b8e693724ad6c1f7b266074311`
and candidate hash both match the latest log. These are working choices, not P5/P6 completion.

## D-339 — selection v0 approved as a whole and21-seed working list adopted (2026-10-03)

Authority: Quinton's L1 instruction and [RUNNING-LOG](retrieval/planning/RUNNING-LOG.md), entry
“2026-10-03: Quinton approves selection v0 as a whole; handoff to Codex written (Claude)”, recording
“Yes, I agree on the search policy, continue with that.” Selection policy v0 is approved as a whole:
SEARCH-AND-SELECTION document revision9 SHA-256
`1cb96a960f04b58cb07a796a5ef0b2ea53e0337503279c8d373aa849f4b5c46a`, verified against the log
and Quinton's packet. This includes section5.2. Policy text changes create a new version and log the
reason (v0.1 before first run); a future P6 code hash is distinct from this policy-text identity.

Approve the21-seed working list:16 sectionA R plus C-31/C-32/C-33 and sectionA3 C-40/C-42;
22 only if C-36 verifies. A3's other five remain reserves. Latest draft8 hash
`eceaa8bf57c7863f9cb2c1842f893b5e1d386002f05786364ca12099eda195f2` and SEED-SET hash
`d68b0b18e1085f87cc413f91ca1ad8b720a86d9d7517cf4eea5dc6006fff604c` match the log.
Identifiers/scope/MeSH are still checked in P5, then P6 freezes before selection. No seeds are
verified/frozen now; >=90% recall and family/MeSH safeguards remain. Approval completes the P2
policy/candidate decisions, not S1/S2/S3/S4, a run signature or acquisition.

## D-340 — Claude's independent Plan07 planning arrangement; ownership unchanged (2026-10-03)

Authority: Quinton's L1 instruction, October3 round2/approval entries in
[RUNNING-LOG](retrieval/planning/RUNNING-LOG.md), and the
[Claude handoff](retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md), SHA-256
`9978b8088d25fa9dc24bcc1999470a2feec51e4d822ab7352f1afb5d4e1142df` verified against the log.
Claude continues Plan07 planning on its own judgment without waiting for Codex review; reviews are
welcome but are no longer a planning gate. Claude retains planning/retrieval implementation;
Codex retains shared decisions, registry, operations, contracts, storage aliases and Git checkpoints.
One writer per shared file and imaging priority remain. Claude's independent checks, exposure
logging and separate permission requirements for code dispatches/downloads/installs/signatures stay
in force. This does not grant GroupC/S2/P4/P5 execution, activate a source or enlarge storage.

Reconciliation evidence: RUNNING-LOG exact byte SHA-256
`f7657b99d87fd418857b1067adeca65460819b8dc43321b4c70fe09ff543bc9e` at this read;
[Codex L1–L6 handback](retrieval/CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md).

## D-341 — bounded S1 setup and Claude S2 dispatch (approved 2026-10-03; recorded 2026-10-04)

Authority: Quinton's present M1–M6 dispatch and [RUNNING-LOG](retrieval/planning/RUNNING-LOG.md),
entry “Codex L1-L6 handback reviewed; Quinton's S1/S2, cleanup and integration decisions”.
“Approve both” authorizes Codex's [S1 allowlist/order](operations/PLAN07-LITERATURE-S1-PROPOSAL-2026-10-03.md)
and Claude's separately owned S2 code/invented offline tests. S1 may create only
`scratch/literature`, `artifacts/literature`, `artifacts/literature/receipts` under the verified
registered external roots and internal fallback `/Users/quintonevans/PROWL-Literature-Receipts/`.
Tests precede setup/writer activation. One capability-scoped writer; at most 1 MiB invented setup
payload, 64 MiB primary receipt reserve and 64 MiB fallback reserve. Future 40 GiB sizing allowance
is not setup allocation. Registry/source/backup permissions and the fixed imaging backup ceiling
remain unchanged. Native probes only while imaging is idle. The S1-to-S2 binding is a named
follow-up, not live Run S execution.

“Watchdog is fine” approves the parser-child RSS monitor every approximately 0.5 seconds, stopping
above 4 GiB; growth within a poll interval can overshoot. This is not an OS memory limit. The signed
Run S copy must name this method. S2 dispatch is code/testing only. No S3/S4, signature, download,
installation, database operation, P4/P5 execution, commit or push follows from this record.

## D-342 — two exact housekeeping deletions (approved 2026-10-03; recorded 2026-10-04)

Same authority/entry as D-341: “Delete both”. Recheck regular-file type, exact size and full hash
from the [L1–L6 handback](retrieval/CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md) before deleting only
`_to_delete/claude-RUNNING-LOG.md.tmp` (114 bytes,
`0c1f14cffafe4293718b85a8ef52dfa9bd004be9ebeddea03150082e1b004fe9`) and
`.git/index.lock.stale-claude-20260928` (0 bytes,
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
No other cleanup or active-lock removal is authorized.

## D-343 — separate retrieval offline contract section (approved 2026-10-03; recorded 2026-10-04)

Same authority/entry as D-341: “Accept all three”. Accept inclusion of all 12 accepted retrieval
1.0.0 schemas as a separate shared offline contract-check section. Keep existing Plan01/02 checks
and retrieval runtime relationship tests. A concrete implementation packet and reconciliation of
the contract README's stale “pending re-review” status are owed; this M5 task drafts the packet,
not its code. Schema checking does not accept a corpus or database.

## D-344 — D-085 additional span and delivered metrics (approved 2026-10-03; recorded 2026-10-04)

Same authority/entry as D-341: “Accept all three”. This accepts the previously proposed D-085
amendment as additional, separately reported measures: ranked span-hit recall@1/3/5/10,
delivered-span recall, required-concept coverage and delivered token count. Official source/passage
recall@1/3/5/10 and MRR remain unchanged; no release bar is retroactively changed.

Per answerable question, ranked span-hit and delivered-span denominators are the distinct direct
evidence spans keyed by immutable representation identity and half-open Unicode code-point
`[start,end)` offsets. Credit requires complete containment in a top-k passage or, respectively,
an actually packed/displayable passage; repeated containment counts once. Required-concept coverage
uses distinct required concepts as denominator and counts a concept once when a delivered direct
span supports it. Delivered token count is the sum for actually packed passages, with no recall
denominator. Empty eligible denominators are undefined and reported with counts/reasons, never
perfect scores. Macro averages over answerable questions disclose excluded refusal questions and
undefined questions; passage measures disclose configurations without gold passages.

Measured use requires verified question/query/ranking/corpus binding, immutable representation
hashes and exact slices, identity-verified rights permitting snippet display (index permission alone
is insufficient), a named/versioned/hash-pinned reference or generator tokenizer, pinned packing
rule and context budget. The starting budget is the D-265 provisional 2,000 tokens. Fixture/word
counters demonstrate mechanics only and cannot evidence actual model token delivery. The current
P3 producers retain their provisional labels until a separately scoped implementation reconciles
them; do not relabel old results. Additional metrics may inform development configuration selection
after these preconditions and the comparison rule are frozen. Held-out labels remain sealed from
implementers/selection, used only for verification. No unseen labels were opened by this amendment.

## D-345 — P4a packet after imaging; separate trial approval (approved 2026-10-03; recorded 2026-10-04)

Same authority/entry as D-341: “Accept all three”. Prepare a named runtime, pinned PostgreSQL/
pgvector, storage/resource/stop-limit install-authorization packet after the immediate imaging and
checkpoint queue. Any approved trial runs in an idle window. Current M5 authorizes a draft only:
no install, image pull, runtime start, global Docker change, database or accelerator trial. P4b and
its psycopg3 dependency remain separate. D-341–345 grant no Run S signature or follow-on dispatch.

## D-346 — Claude's filesystem hook first, then Codex binding (2026-10-04)

Authority: Quinton's present agreement to continue and the October4 entry in
[RUNNING-LOG](retrieval/planning/RUNNING-LOG.md), “Codex M1-M6 handback reviewed; Quinton approves
the S2 filesystem hook, a local commit and the shared-contract packet”. Quinton chose “Claude adds
the hook first”: Claude owns `sizing_v1.1` and its `SizingFs`/`PlainFs` implementation; Codex then
implements S1-S2-BINDING-V1 and repeats native qualification against the new exact handback.
Reviewed proposal SHA `270436ae6e19fd73730bfbbd05d5c5e94725dc52aeb64d9f5b6b353deedea87b`.
Current source remains the qualified `sizing_v1` identity814b89c5; the hook has not arrived in this
checkout. Do not implement against an assumed changed interface or patch Claude's files.

Codex prepares the concrete binding/qualification packet and hook review while that handback is
pending. Single literature lease, descriptor-based I/O including parser handoff, explicit cumulative
receipt/fallback ceilings and failure preservation precede live use. The old bounded-setup capability
does not become a sizing-job permission. No S3, S4/signature, download or Run S execution follows.
Log hash at reconciliation `faa7b33b03ff6593ba91e3d5c3488bbf9348b25d186e850dc82a0983c8e5cbbd`.

## D-347 — local preservation only; current exact scope recheck (2026-10-04)

Same authority/entry as D-346, recording Quinton's “Commit locally, no push”. Codex rechecks and
preserves the pending Plan07 checkpoint locally, including completed approved offline contract
checks and the reviewed follow-up records, after freezing a refreshed exact file list. Retain the
older40-file proposal as historical evidence; its RUNNING-LOG hash is now stale because Claude
recorded newer approvals. Never silently stage a partial hook implementation or change expected
S2 pins. No public push, merge, cleanup, source/job permission or experiment extension is granted.

## D-348 — dispatch the separate shared offline retrieval contract section (2026-10-04)

Same authority/entry as D-346, recording Quinton's “Yes, build it” for
[the exact shared-contract packet](operations/PLAN07-SHARED-CONTRACT-PACKET-2026-10-04.md).
Allow the new shared test module and invented fixture/pin directory, and scoped reconciliation of
the shared contract README's stale review status. No schema or Claude producer/test change.
Existing Plan01/02 names/checks and retrieval runtime relationship checks remain intact. D-344
metric policy does not dispatch producer/tokenizer migration. No install, DB, P4a or scientific run.

## D-349 — delivered S2 v1.1 verified; bounded binding prerequisite remains (2026-10-04)

Reconciles D-346's earlier “not arrived” state with
[Claude's v1.1 handback](retrieval/CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md), SHA
`3d00e92aac6f12ae4a052c70988a630522bd5af3ad210e40cc846d8a1f13b2c6`, and the
[other Codex chat's native N2 review](operations/CODEX-S2-V1.1-NATIVE-REVIEW-2026-10-04.md), SHA
`c151b1a306fa4f1251c7827cf127edd7c9abbf78edb760d235f902ce16470b4c`.
That chat records Quinton's ownership instruction: “Keep N4/N5 in the other chat; this chat verifies
N2 and hands back”. N2 passed144sizing/326retrieval tests, no skips. This chat independently
reverified all22pins and identitydf585e2b, preserving Claude's bytes, and reran the shared contract
gate:198passed/3054deselected, two existing warnings. The49-check S1 source/fixture inventory and
registry hash remain fixed. No new full-project acceptance is claimed.

N4 is incomplete: the delivered watchdog's unbounded internal stderr temporary file and undrained
stdout pipe are outside SizingFs. The [concrete interface request](operations/PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md)
requires bounded concurrent diagnostics with failure/closure tests and a fresh Claude-owned handback;
Codex does not patch that lane. Native compatibility qualification does not close binding acceptance.
No binding backend, native external rehearsal, sizing signature or run is enabled. D-347 permits
the local checkpoint to preserve verified work while listing N4 as incomplete; no push. The current
Claude log hash is `fc5df4c5fc0b747387c7773b9f40422492f29778fe99f6178215d3eb886d91c5`.
