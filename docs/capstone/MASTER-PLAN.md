# PROWL capstone master plan

**Status:** Active planning baseline  
**Baseline date:** 2026-09-07  
**Official course start:** 2026-10-05; confirmed by Quinton on 2026-09-18  
**Owner:** Quinton Evans  
**Governing sources:** Proposal v3.8 and Technical Appendix v3.1

## 1. Outcome

PROWL will be a reproducible, autonomous pancreatic-lesion annotation-assist workflow. It will ingest
controlled imaging data, localize the pancreas, propose pancreas and lesion contours, calculate
review measurements and a review-ordering score, show the output in an existing React/NiiVue review
interface, retrieve cited supporting literature for structured questions, and append the reviewer's
accept/edit-required/reject event. It remains a research and annotation-assist system, not a diagnostic
product.

The capstone succeeds by demonstrating a coherent system with honest evaluation and auditable
artifacts. It does not succeed merely by training a higher-scoring model or adding unrelated
technologies.

### October 17 required final-deliverable addition

Quinton explicitly requires [measurement-aware AI expert functionality](retrieval/MEASUREMENT-AWARE-EXPERT-PLAN.md)
after the core RAG system has passed its frozen acceptance gates. Required scope: verified pancreas/
lesion measurements, eligible cited reference comparisons, readable non-diagnostic explanations,
and a working human-reviewed training-feedback pipeline. These are REQ-X01–X04 and completion-spec
Steps 10–12, tracked in AI-05–AI-07. They are not stretch goals. Core RAG acceptance alone does not
complete the expanded final deliverable. No training launch or clinical diagnosis is authorized.
This records the user's added implementation commitment, not a claim that the original proposal
files were amended or institutionally reapproved. Reconcile schedule impact in the next planning pass.

## 2. Prior foundation versus new capstone work

### Reusable foundation

- Experience and code for 3D CT loading, preprocessing, training, evaluation, and experiment logging.
- Existing React/NiiVue interface scaffolding and imaging service experience.
- Prior provided-region results, failure analysis, and the experiment log as design evidence.
- Existing utility modules, configuration patterns, and presentation artifacts where still valid.

### Required new work

- New protected cohorts and tests appropriate to the capstone data design.
- PANORAMA integration with explicit label mapping, exclusions, provenance, duplicate controls, and
  patient grouping.
- A restartable, tested workflow DAG and versioned artifact contracts.
- A newly trained and evaluated autonomous localize-then-segment workflow. No checkpoint trained
  during the previous project is the capstone model.
- At least one controlled model comparison selected from baseline evidence.
- Patient-level detection/specificity evaluation and separate pancreas/lesion segmentation results,
  including autonomous versus provided-region distinction.
- A versioned PubMed/PMC retrieval corpus, measured retrieval quality, cited generation, and
  insufficient-evidence refusal behavior.
- Extension of the existing review interface to connect model output, evidence, and stored reviewer
  action.
- Unit, integration, regression, data-quality, and end-to-end testing proportional to the system.
- Stakeholder review, professional documentation, stabilization, and delivery.

## 3. Boundaries

### Committed

- PanTS, eligible PANORAMA data, and a licensed/allowed PubMed/PMC evidence corpus.
- Autonomous imaging, multi-source data controls, controlled experimentation, retrieval evaluation,
  a recorded review workflow, and reproducibility evidence.
- File-based, versioned artifacts as the minimum implementation boundary.

### Explicitly flexible

- Model architecture, localization technique, false-alarm method, ensemble or distillation approach.
- Workflow tool, vector index, relational persistence, rented compute, and cloud persistence.
- These choices are made only after their requirements and selection tests are documented.

### Not committed

- Diagnostic conclusions, tumor-type classification, treatment recommendations, or clinical claims.
- Reusing the previous project's trained model as the capstone model.
- A mandatory relational database, managed vector service, or cloud platform.
- Level 5 multi-structure segmentation.
- Browser-based contour editing unless the core is complete and a stakeholder identifies it as the
  highest-value remaining change.
- External Johns Hopkins submission. Compatibility is valuable; submission itself is optional.

## 4. System workstreams

```text
Governance, contracts, tests, and operations
  +--> PanTS --> protected cohorts --> tested imaging DAG --> new autonomous baseline
  |                                                               |
  +--> PANORAMA --> separate G2 validation --> eligible source experiment --> evaluation
  |
  +--> Literature corpus --> retrieval index --> retrieve/cite/refuse
  |
  +--> Existing interface --> validated case/evidence adapters --> durable review
                                                                  |
                                          integration + evaluation + release
```

The imaging path is the scientific critical path. Retrieval is a supporting parallel path. They
remain separate until the interface so a retrieval problem cannot invalidate imaging results and an
imaging problem cannot contaminate the evidence corpus.

PANORAMA remains committed capstone work, but G2 is not a prerequisite to the PanTS-only baseline.
The baseline requires its own trusted cohorts, imaging/DAG checks, and resource preflights; a
PANORAMA or mixed-source arm additionally requires G2. Diagrams describe dependencies, not a demand
to execute all component plans in numerical order.

## 5. Governing 10-week schedule

September 7 records the beginning of planning, not the course clock. Pre-course work may satisfy
deliverables early once their prerequisites pass. Calendar Week 1 is October 5–11; Week 9 is
November 30–December 6; Week 10 is December 7–13. Exact assignment deadlines remain governed by the
course calendar. The break before September 18 did not consume official capstone weeks.

This table preserves the approved proposal wording and clarifies the internal gates.

| Week | Primary focus | Meaningful outcome | Exit gate |
|---:|---|---|---|
| 1 | Architecture and test planning | Confirm data design, retrieval requirements, workflow DAG, UI-extension requirements, and test strategy. | Architecture, contracts, risks, implementation plans, and test plan are reviewable and internally consistent. |
| 2 | Protected data splits | Reproduce cohorts and add unit tests for patient separation, manifests, and repeatability. | Frozen cohort artifacts reproduce exactly; overlap/leakage assertions pass. |
| 3 | Second-source integration | Integrate PANORAMA with tested label mapping, provenance, exclusions, and duplicate controls. | A mixed-source smoke cohort loads correctly; reconciliation report and tests pass. |
| 4 | Unified pipeline and orchestration | Produce reproducible training inputs and implement the tested preprocessing/workflow DAG. | Restartable DAG builds versioned artifacts and safely resumes after an injected failure. |
| 5 | Autonomous baseline and retrieval foundation | Establish the imaging baseline; use model-training time to ingest literature and create the retrieval-index prototype. | New end-to-end autonomous baseline is scored; versioned retrieval prototype is queryable. |
| 6 | Model experiment and retrieval evaluation | Complete one controlled model comparison, evaluate the false-alarm tradeoff, and measure retrieval quality. | Model decision and operating curve are documented; retrieval metrics and grounded response tests are reported. |
| 7 | UI refinement and stakeholder review | Extend the existing interface, integrate representative model/evidence outputs, and conduct stakeholder review. | Core review task completes in the UI; stakeholder findings are prioritized and recorded. |
| 8 | Integration, testing, and evaluation | Complete end-to-end integration, full unit/integration/regression testing, held-out evaluation, and documentation drafts. | Release candidate passes the test matrix and produces reproducible evaluation evidence. |
| 9 | Protected buffer and stabilization | Absorb overruns, correct defects, rerun affected tests or evaluation, and lock the release. No new scope. | Priority defects resolved or explicitly accepted; release is locked. |
| 10 | Delivery and presentation | Package the stable system, complete documentation, rehearse the demonstration, and present. | Submission package, demonstration, user/developer guidance, and presentation are complete. |

### Continuous model-learning lane

Weeks 5 and 6 are the formal autonomous-baseline and controlled-comparison milestones; they are not
the only weeks in which models may be trained. After G0, model work continues in parallel whenever
the particular run's data, contract, test, lineage, and resource dependencies are satisfied:

- early smoke, diagnostic, and exploratory runs use registered train-role descendants and never the
  publisher-test cohort;
- candidate models and negative results are preserved rather than overwritten;
- formal baseline and controlled-comparison claims wait for G1–G4 as applicable;
- training may overlap data, orchestration, retrieval, and UI work when compute/storage ownership is
  safe; and
- Week 9 allows only defect-driven stabilization reruns, while Week 10 cannot introduce a
  result-changing experiment or model selection.

Plan 06 governs the run classes, promotion rules, evaluation roles, experiment registry, and final
selection freeze. This lets the project gather evidence continuously without turning every
exploratory run into a formal claim or weakening the held-out evaluation.

[`../experiments.md`](../experiments.md) remains the living notebook by Quinton's September 18
direction. Write a game plan before every experiment, record every attempt/outcome, and state which
prior evidence and retained settings motivate the next test. New capstone entries link immutable
Plan 06 records; historical ideas are reviewed rather than automatically queued. Plan 10's approved
staged readiness separates foundation setup, safe individual experiments, and full pre-G8 delivery
checks, so incomplete retrieval/UI work does not block otherwise eligible imaging preparation.

Plan 11's lightweight living protocol is approved. Quinton owns expert/radiologist outreach; confirm
the participant/session or activate a suitable fallback by Week 5, then conduct the main walkthrough
in Week 7. Scheduling is not a prerequisite for early data, model, retrieval, or UI work. Actual
stakeholder feedback, role limitations, and bounded approved revisions remain part of G7 evidence.

## 6. Milestone gates

| Gate | Must be true | Blocks |
|---|---|---|
| G0-design — bounded start | Approved component designs, authority, risks, planned tests, and a scoped implementation order are documented. | Unplanned implementation; permits the environment/fixture/test foundation needed for G0-verification |
| G0-verification — runnable foundation | Clean supported environments, unchanged historical baseline/classification, core contract fixtures, and fast Python/UI checks have evidence. Full G0 means both checkpoints. | Production component acceptance and real model experiments, in addition to their own gates |
| G1 — cohorts trusted | Patient grouping, split disjointness, manifest schema, source identity, and repeatability tests pass. | PANORAMA mixing and training |
| G2 — PANORAMA trusted | Label remap, exclusions, provenance, duplicate controls, and mixed-source smoke test pass. | Unified training inputs |
| G3 — DAG trusted | Steps are idempotent, restartable, versioned, and fail closed on invalid inputs. | Expensive baseline training |
| G4 — baseline valid | Newly trained model runs autonomously on full volumes with comparable metrics and no oracle input. | Selecting the model experiment |
| G5 — comparison valid | One controlled comparison has a preregistered bar and matched evaluation. | Model selection |
| G6 — retrieval valid | Corpus snapshot, question set, recall@k/MRR, citation checks, groundedness, and refusal tests exist. | Evidence assistant in the UI |
| G7 — workflow usable | Representative user completes inspect → evidence → accept/edit/reject flow and the decision persists. | Release candidate |
| G8 — release candidate | End-to-end and regression tests pass; held-out results and limitations are documented. | Stabilization lock |
| G9 — release locked | No new scope; artifacts are reproducible and demonstration is rehearsed. | Delivery |

## 7. Work breakdown and ownership

| ID | Work package | Main artifact | Gate |
|---|---|---|---|
| WP-01 | Governance and architecture | Architecture diagrams, contracts, decision register | G0 |
| WP-02 | Source inventory and cohorts | Unified manifest schema, frozen cohorts, reconciliation report | G1 |
| WP-03 | PANORAMA ingestion | Source adapter, label mapping, provenance and exclusion tests | G2 |
| WP-04 | Orchestration | Restartable DAG, run manifest, failure/retry evidence | G3 |
| WP-05 | Autonomous imaging | Localizer/segmenter workflow and full-volume baseline | G4 |
| WP-06 | Experimentation and evaluation | Preregistered comparison, operating curves, error analysis | G5 |
| WP-07 | Literature retrieval | Corpus/index manifest, question set, retrieval/generation report | G6 |
| WP-08 | Review interface | Extended UI, shared case-package contract, append-only review event | G7 |
| WP-09 | Quality and release | Test suite, traceability, release checklist | G8–G9 |
| WP-10 | Stakeholder and communication | Session protocol, findings, user/developer docs, presentation | G7–G9 |

## 8. Week 1 planning sprint

Up to roughly 50 hours of planning is reasonable because the approved Week 1 is explicitly
architecture and test planning. The week is successful if it reduces downstream rework, not if it
maximizes page count.

| Block | Focus | Output |
|---|---|---|
| 1 | Governance and repo audit | Source hierarchy, active-doc hub, stale/valid map, cleanup proposal |
| 2 | Data contracts | Case identity, manifest/cohort schemas, PANORAMA controls, artifact layout |
| 3 | Scientific contracts | Autonomous boundary, metric definitions, experiment selection process |
| 4 | Workflow and operations | DAG stages, idempotency, resumption, storage/compute decision gates |
| 5 | Retrieval and UI | Corpus/query/response contracts, UI data contract, stakeholder tasks |
| 6 | Quality review | Test matrix, risk review, traceability audit, plan-readiness review |

Small discovery spikes are allowed only when a document cannot be made accurate without them. No
long training run, framework migration, or broad UI rewrite belongs in this sprint. The continuous
model-learning lane begins after the planning package and its run-safety boundaries are approved,
not merely because unused compute is available.

## 9. Change-control rules

1. The approved outcome and Weeks 9–10 protections cannot be changed by a technical convenience.
2. A new dependency requires a named requirement, selection rationale, maintenance impact, and
   fallback.
3. A change that affects scientific comparison requires a new experiment entry; old results remain
   unchanged.
4. A change to input identity, preprocessing, labels, cohorts, or metrics invalidates downstream
   artifacts unless compatibility is proven.
5. Stretch work begins only after the committed capability and its tests pass.
6. Every expensive run must have a preregistered hypothesis, stop condition, and preserved outputs.
7. No source dataset, historical proposal, prior model artifact, or previous result is overwritten.

## 10. Project-level definition of done

The capstone is complete when:

- the autonomous workflow runs from a documented input to a versioned prediction and review event;
- data identity, provenance, exclusions, and cohort disjointness are test-enforced;
- a newly trained model has full-volume held-out results with pancreas and lesion metrics reported
  separately and patient-level sensitivity/specificity shown as a tradeoff;
- one controlled model comparison has an honest accept/reject decision;
- the evidence assistant retrieves a versioned allowed corpus, cites supporting passages, and
  refuses when evidence is insufficient, with retrieval and response metrics reported;
- the existing interface demonstrates the full review task and captures stakeholder feedback;
- unit, integration, regression, and end-to-end tests pass in the documented environment;
- artifacts trace to source versions, cohort hashes, configuration, code revision, and model version;
- limitations, ethics, licensing, and non-diagnostic framing are visible;
- Week 9 contains no new scope and Week 10 is delivery only.

## 11. First implementation after planning

All twelve designs are approved. The September 18 focused prerequisite review and concrete starting
sequence are in [`IMPLEMENTATION-START.md`](IMPLEMENTATION-START.md):

1. protect reviewed documentation/source and establish clean test environments without replacing
   historical environments or modifying old test assertions;
2. preserve the unchanged baseline, then build generated contract/identity/cohort fixtures and fast
   checks to satisfy G0-verification;
3. resolve storage choices and verify scoped roots, then acquire/reconcile pinned sources;
4. implement protected cohort, spatial/target, initialization, metric, and run/checkpoint controls;
5. explain Plan 04 and obtain its explicit implementation authorization before orchestration code;
6. preregister the first tiny PanTS training experiment once its exact prerequisites pass; proceed
   to PANORAMA integration as a separately gated branch.

G0-design is sufficient for the bounded foundation work that produces G0-verification evidence.
An unqualified "after G0" still requires both checkpoints. Completing every downstream product
component is not a prerequisite for setup; no synthetic result replaces a real-data gate.
