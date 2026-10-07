---
title: "BSAAI Capstone Proposal"
degree: "Bachelor of Science in Applied Artificial Intelligence and Data Engineering"
student_name: "Quinn Evans"
capstone_title: "Autonomous Pancreatic Lesion Detection and Radiologist Review System"
status: "Draft"
---

# BSAAI Capstone Proposal

**Degree:** Bachelor of Science in Applied Artificial Intelligence and Data Engineering

| Proposal Information | Details |
|---|---|
| **Student Name** | Quinn Evans |
| **Capstone Title** | Autonomous Pancreatic Lesion Detection and Radiologist Review System |

---

## 1. What? — Project Summary

### Project Summary

**The problem.** Pancreatic cancer has a five-year survival rate below ten percent, and the largest
single reason is late detection. The pancreas is difficult to work with on CT: it is soft tissue with
poor contrast against everything around it, it varies widely in shape and position, and early tumors
are small and easy to miss on a scan acquired for an unrelated reason. Published studies show that
radiographic signs often appear months before diagnosis and go unnoticed. This is not a failure of
attention — it is a hard perception problem inside a high-volume workflow.

**The user.** The direct user is a radiologist or radiology clinician reviewing abdominal CT. The
indirect beneficiary is the patient, for whom earlier identification of a suspicious region changes
the available treatment options. **This system does not diagnose and makes no clinical claim.** It
proposes regions of interest that a qualified human accepts, edits, or rejects, and it records that
decision.

**What it is.** A CT volume arrives and the system runs without further input: it locates the
pancreas on the full scan, segments the organ and any lesion, scores the patient for tumor presence,
and computes measurements — lesion volume, maximum diameter, anatomical subregion. Those findings
populate a review interface where a clinician sees the scan with overlays, a drafted set of structured
findings, and a locally hosted knowledge assistant that answers questions using retrieval over indexed
pancreatic imaging literature. Every statement the assistant makes is tied to a source shown beside
it; when retrieval finds nothing relevant, it declines rather than generating. The reviewer's accept,
edit, or reject decision is stored, which means the system produces a corrections record as a
byproduct of being used. Full architecture, data flow, and schema are in the technical appendix.

**How this exceeds prior coursework.** The five-week machine learning project preceding this produced
a working segmentation model, a serving endpoint, and a review interface. It has one disqualifying
limitation: the model is handed the pancreas location before it segments. Every number it produces —
lesion Dice 0.474, detection sensitivity 96 percent, specificity 17 percent on the official 901-scan
held-out test set — assumes something already found the organ. Published models on the same benchmark
find it themselves, so the results are not comparable and cannot be submitted anywhere. The capstone
removes that assumption. It also adds a second dataset requiring genuine cross-source integration, a
relational and vector data layer, a separate retrieval-augmented AI system, and an external validation
path.

**Professional quality and feasibility.** The existing repository carries a registered model with a
version and checksum, twenty-seven pre-registered experiments with recorded decisions, two independent
code audits, and complete documentation. The capstone adds a model card, data lineage, a validation
suite that runs on ingest, and a review session with a practicing clinical stakeholder. Because the
model, serving layer, and interface already work, each pillar is scoped with a committed minimum and an
optional stronger version, so a difficult week costs sophistication rather than a component. System
capabilities are committed and must work; experimental outcomes are pre-registered and reported
honestly either way.

---

## 2. Why? — Project Motivation and Capstone Value

### Project Motivation and Justification

I chose the pancreas because it is hard. It is soft tissue, it hides in a crowded abdomen, and
pancreatic cancer is difficult to see even when someone is looking directly at it. My aunt is a
clinician's assistant who reviews scans and then sits with patients to explain what the doctors found
— including telling them they have cancer. When I described this project to her, she told me the
pancreas is an organ radiologists do not enjoy imaging. That conversation shaped the problem statement
more than any paper I read. Software that quickly finds the organ, outlines it, and flags a region
worth a second look does not replace her judgment or anyone else's. It gets a human to the right part
of the image faster.

There is a lot of healthcare behind me. My step-grandfather was a radiologist his entire career, and
my mother started radiology school. My grandfather was a vice president at Intermountain Healthcare
and oversaw the Urban South region. He read research constantly and tried to bring cutting-edge work
into the hospitals he was responsible for, and a great deal of what he read came out of Johns Hopkins.
That is close to exactly what I am doing now. The dataset I train on is Johns Hopkins' PanTS. The
pretrained model I fine-tune is their SuPreM checkpoint. I am taking research from the institution he
followed and trying to turn it into something operational. Johns Hopkins is also where I hope to
attend graduate school, so choosing a dataset released by the lab whose work I want to build on was
deliberate rather than incidental.

The technical reason for this dataset is just as concrete. PanTS has an active external evaluation
path: the authors accept submitted models and score them on 26,489 held-out scans from UCSF, a Polish
cohort, Peking University, and an RSNA dataset re-annotated by their team. Almost no public dataset
offers that. It means the work can be measured against something I cannot see, cannot overfit, and did
not grade myself.

The unmet need is specific. My current system finds tumors well — 96 percent patient-level detection,
higher than either published model on the benchmark — but flags most healthy patients as suspicious. A
tool with that false-positive rate is not usable, and fixing it is a real engineering problem rather
than a cosmetic one. I want to finish this because I want it to actually work, and because I believe
the best use of AI is in healthcare, where a small improvement in how fast someone looks at the right
image is worth more than almost anything else I could build.

---

## 3. How? — Technologies and Applied AI Skills

### Technologies and Skills

- **Python, PyTorch, and MONAI — 3D medical image segmentation**
  **Demonstrated capability:** Training a 3D SegResNet by transfer learning from a pretrained abdominal
  CT checkpoint; volumetric preprocessing (isotropic resampling, Hounsfield windowing, ROI extraction);
  sliding-window inference over full volumes.
  **Current experience level:** Solid, used extensively in the preceding project.
  **Learning plan:** No new tooling. The growth is in the problem — replacing a provided region of
  interest with a predicted one changes the failure modes entirely.

- **PostgreSQL with pgvector — unified relational and vector storage**
  **Demonstrated capability:** A schema in which cohort membership is a constrained relation rather
  than a text file, making the leakage that previously invalidated my results impossible to express;
  hybrid queries combining semantic similarity with structured predicates.
  **Current experience level:** Solid with PostgreSQL and SQL; new to pgvector specifically.
  **Learning plan:** pgvector is an extension over familiar ground. I will build the index and tune
  HNSW parameters against a held-out retrieval question set in Week 6.

- **Retrieval-augmented generation with a locally hosted LLM (Ollama, Qwen)**
  **Demonstrated capability:** A grounded assistant that answers only from retrieved passages, cites
  each visibly, and declines when retrieval finds nothing relevant. Running locally means no
  imaging-derived data leaves the machine.
  **Current experience level:** Solid — I have built embedding pipelines, vector search, and RAG
  systems several times and already run local models.
  **Learning plan:** The new work is evaluation rather than construction: recall@k and mean reciprocal
  rank for retrieval, and measuring what fraction of generated claims trace to a source.

- **Cross-source data integration and entity resolution**
  **Demonstrated capability:** Merging PanTS with PANORAMA despite different label conventions,
  annotation provenance, reference standards, and tumor-type coverage, and identifying the cases that
  appear in both using institution matching and tumor-volume distribution fingerprinting.
  **Current experience level:** New. I have never merged two clinical imaging datasets.
  **Learning plan:** Build the exclusion list and label remapping behind unit tests and a load-time
  assertion, using the same guard pattern that now protects my training splits.

- **MLflow — experiment tracking and model registry**
  **Demonstrated capability:** Versioned model registration with checksums; every run tied to its
  cohort, preprocessing configuration, and git revision.
  **Current experience level:** Solid.
  **Learning plan:** Extend to a PostgreSQL tracking backend so local and cloud runs share one store.

- **FastAPI, React, and NiiVue — serving and volumetric review interface**
  **Demonstrated capability:** An inference endpoint triggered on scan arrival; a browser-based
  tri-planar and 3D viewer with overlays, measurements, and a persisted review decision.
  **Current experience level:** Solid with FastAPI and React; NiiVue used once, in the preceding
  project.
  **Learning plan:** Deepen NiiVue for measurement display and comparison views from its documentation.

- **Docker and rented cloud GPU compute**
  **Demonstrated capability:** A pinned environment that runs identically on an Apple Silicon laptop
  and a rented NVIDIA instance, raising throughput from one overnight run to several per day.
  **Current experience level:** Solid with Docker; limited with rented GPU infrastructure, as my cloud
  ML experience is with Azure.
  **Learning plan:** Start on-demand rather than preemptible, re-establish a matched baseline on the
  new hardware before drawing any comparison, and hold numerical precision constant so results stay
  comparable to prior runs.

- **Experimental methodology — pre-registration and honest reporting**
  **Demonstrated capability:** Every hypothesis recorded with a single changed variable and an
  accept-or-reject threshold written before the run; paired per-case comparison with bootstrap
  confidence intervals; results reported at the pre-registered horizon regardless of outcome.
  **Current experience level:** Solid, developed during the preceding project.
  **Learning plan:** Extend the same discipline to retrieval quality, the part of this project most at
  risk of being judged by impression rather than measurement.

---

## 4. Ten-Week Project Schedule

Week 1 begins Monday, October 6.

| Week | Primary Goal | Planned Work and Milestones | Measurable Deliverable | Ahead/Behind Indicator |
|---:|---|---|---|---|
| **1** | Relational foundation | Deploy PostgreSQL schema; ingest the PanTS manifest; convert cohorts from text files to constrained tables; write the ingest validation suite | 9,901 scans indexed; cohort disjointness enforced by database constraint; validation suite passing | **Ahead:** PANORAMA download started. **Behind:** cohorts still defined by text files |
| **2** | Second dataset integrated | Download PANORAMA; unit-test the label remap; automate exclusion of the 274 overlapping Decathlon and NIH cases; build the merged cohort | 1,964 usable cases ingested with provenance columns; entity-resolution report; merged cohort verified disjoint from evaluation sets | **Ahead:** EXP-27 smoke test run. **Behind:** remap or exclusion incomplete |
| **3** | Autonomy | Retrain the pancreas localizer on leak-free splits; measure effective containment after the final crop, not before it; run the cascade end to end | First autonomous lesion Dice on held-out PanTS, with no provided region of interest | **Ahead:** specificity gate prototyped. **Behind:** containment still unmeasured |
| **4** | Pre-registered training experiment | Run EXP-27: does adding 578 non-overlapping tumor cases improve lesion Dice? Evaluate against the bar fixed before the run | Accept or reject decision with paired bootstrap confidence interval; result recorded either way | **Ahead:** a second configuration trained. **Behind:** run not finished at the pre-registered horizon |
| **5** | Usable operating point | Build the volume gate and tumor-presence classifier; select the threshold on validation and report on test | Specificity materially above 17% with detection sensitivity at or above 96%, or a documented account of why that trade is unavailable | **Ahead:** submission package drafted. **Behind:** no operating point beats baseline on both axes |
| **6** | Knowledge corpus | Build and pin a filtered PubMed and PMC Open Access snapshot; chunk and embed; build the pgvector HNSW index; author a retrieval evaluation set | Queryable index with recall@k and mean reciprocal rank reported on held-out questions | **Ahead:** embedding ablation started. **Behind:** index not queryable |
| **7** | Grounded assistant | Wire Ollama and Qwen to the retriever; implement cite-or-refuse; construct queries from the pipeline's own findings | Assistant answering with visible citations; measured groundedness rate; refusal verified when retrieval fails | **Ahead:** biomedical versus general embedding ablation complete. **Behind:** any ungrounded generation reaching the interface |
| **8** | Integration and automation | Trigger inference on scan arrival; build the suspicion-ranked worklist; surface overlays, measurements, and the assistant in the interface; persist review decisions | End-to-end demonstration from scan arrival to a recorded reviewer decision | **Ahead:** stakeholder session scheduled. **Behind:** components not wired end to end |
| **9** | Evaluation and stakeholder feedback | Final held-out evaluation; leave-one-institution-out analysis across sites; structured review session with a clinical stakeholder; incorporate feedback | Final metrics table with confidence intervals; per-site results; documented stakeholder feedback and the changes it produced | **Ahead:** Johns Hopkins submission package complete. **Behind:** final evaluation incomplete |
| **10** | Package and present | Model card, data lineage documentation, README; assemble the external submission package; build and rehearse the presentation | Complete documentation set, presentation delivered, submission package ready to send | **Ahead:** model submitted to Johns Hopkins. **Behind:** documentation incomplete |

**Stretch items, deliberately outside the critical path:** external evaluation by the Johns Hopkins
team; the biomedical embedding ablation; a style fine-tune for report formatting.

---

## 5. BSAAI Capstone Pillars

### Available Pillars

- [ ] Data Analytics and Decision-Making
- [x] Data Engineering
- [x] Machine Learning
- [ ] Process Automation
- [ ] Data Science
- [ ] Strategic Technology Leadership
- [ ] Cloud Technology
- [x] Applied Artificial Intelligence *(listed under Core Disciplines in the reference guide rather than in the checkbox list above — see note)*

> **Note for the reviewer:** I selected Machine Learning, Data Engineering, and Applied Artificial
> Intelligence based on guidance from my degree chair. Applied Artificial Intelligence appears in this
> document as a core discipline but not in the pillar checkbox list. If the three selections must come
> from the checkbox list, the closest mapping is Machine Learning, Data Engineering, and Data Science,
> with Process Automation and Strategic Technology Leadership both available as a fourth. I am happy
> to relabel.

### Pillar 1: Machine Learning

**How the project demonstrates this pillar:**

The core of the project is a 3D segmentation and detection model trained by transfer learning from a
pretrained abdominal CT checkpoint. The capstone covers the full lifecycle: replacing a provided region
of interest with a learned localization stage, retraining on an expanded cohort under a pre-registered
hypothesis, building a downstream classifier to fix a specific failure mode, selecting an operating
point on validation and reporting it on held-out test data, versioned registration, and containerized
deployment behind an inference endpoint.

The objective is measurable. The current model reaches 96 percent patient-level detection sensitivity
but only 17 percent specificity, and its lesion Dice of 0.474 depends on being given the organ
location. The capstone removes that dependency and attacks the specificity gap, with every experiment
declared before it runs and reported whether it succeeds or fails.

### Pillar 2: Data Engineering

**How the project demonstrates this pillar:**

This project merges two clinical imaging datasets that are not compatible: different label conventions,
different annotation provenance, different negative reference standards, different tumor-type coverage,
and different contrast phases. Producing a single trainable cohort requires a canonical schema, a
tested per-source mapping layer, and provenance carried as data rather than assumed. It also requires
entity resolution across sources — I have already shown that the Medical Segmentation Decathlon
pancreas dataset sits inside PanTS, and that PANORAMA absorbs 194 Decathlon and 80 NIH cases. Merging
naively would place training data inside the evaluation set. Details are in appendix section A4.

Alongside that sits feature engineering — the volumetric preprocessing pipeline, derived measurements
stored with lineage, and the feature set consumed by the tumor-presence classifier — and data quality
enforcement informed by defects already found in this data, including a validation split leak that
inflated a headline result by 0.11 Dice before I caught it.

The data engineering is not parallel to the machine learning here; it is upstream of it. The Week 4
experiment cannot run at all until the integration and deduplication work is correct.

### Pillar 3: Applied Artificial Intelligence

**How the project demonstrates this pillar:**

The second system is a retrieval-augmented assistant built on a locally hosted large language model,
grounded in an indexed corpus of peer-reviewed pancreatic imaging literature. It is not a chatbot
bolted onto a viewer: the imaging pipeline's structured output — lesion volume, maximum diameter,
anatomical subregion, contrast phase — becomes the retrieval context, so the two systems are joined
through the data layer rather than running side by side.

The design constraint is a safety property, not a disclaimer. The assistant may only make statements
traceable to a retrieved passage displayed next to it, and must refuse when retrieval returns nothing
relevant. That is testable, and it is what keeps a research tool from drifting into unlicensed clinical
advice. Retrieval is measured with recall@k and mean reciprocal rank against a held-out question set,
and generation by groundedness rate, so the AI component is held to the same evidentiary standard as
the imaging model. The full pipeline specification is in appendix section A6.

---

## 6. Reflection

### Personal Growth and Technical Resilience

The hardest part of the project that preceded this was not building the model. It was making it more
accurate. You can run a hundred training runs and they do not simply get better. That realization
changed how I work: I started writing down a hypothesis and a single changed variable before every run,
along with the threshold that would count as success, and only then training. It is the biggest
improvement I made, and if I could start over I would have done it from day one instead of week three.
I am carrying it into the capstone from the beginning.

That discipline gets tested here in a way it has not been before. This project already has two rejected
experiments, and one accepted result that turned out to be a false positive because I read the metrics
before the run had finished. I have withdrawn a headline number of my own after finding a validation
leak in my splits that inflated it by 0.11 Dice. Reporting that honestly cost me the best result I had.
The capstone will produce more moments like that, and the plan explicitly separates committed system
capabilities — which must work — from pre-registered experiments, which are allowed to fail and still
count as results.

Technically I am moving into territory I have not been in. I have never merged two clinical imaging
datasets with different annotation provenance and overlapping membership, and that is exactly where
data leakage hides. I have never removed a human-provided region of interest from a pipeline built
assuming one. I had not worked with 3D images at all before June, and I am taking a computer vision
course concurrently, which is priming me directly for the localization work.

The largest source of uncertainty is one I do not control. The stretch goal is having my model
evaluated by the research group that published the dataset. They may be slow, or the result may not be
good. The project is deliberately built so that outcome changes nothing structural — I will have built
an autonomous, externally validatable system either way, and I will report what comes back exactly as
it comes back.
