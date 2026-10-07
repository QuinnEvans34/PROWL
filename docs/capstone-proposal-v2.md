---
title: "BSAAI Capstone Proposal"
subtitle: "Autonomous Pancreatic Lesion Detection and Radiologist Review System"
author: "Quinn Evans"
---

# BSAAI Capstone Proposal

**Autonomous Pancreatic Lesion Detection and Radiologist Review System**

**Student:** Quinn Evans · **Degree:** B.S. Applied Artificial Intelligence and Data Engineering

## 1. What? — Project Summary

**The problem.** Pancreatic cancer is the third leading cause of cancer-related deaths in the United States, and 80 to 85% of cases are diagnosed too late for effective treatment. Its silent progression and anatomical complexity make it difficult to detect early — which is why Johns Hopkins researchers, working with NVIDIA and 145 medical centers, released PanTS: 36,390 CT scans with expert-validated annotations of more than 993,000 anatomical structures, built using MONAI Label, the framework this project trains in.

**The user.** The direct user is a radiologist or radiology clinician reviewing abdominal CT. The indirect beneficiary is the patient, for whom earlier identification of a suspicious region changes the available treatment options. **This system does not diagnose and makes no clinical claim.** It proposes regions of interest that a qualified human accepts, edits, or rejects, and records that decision.

**What it is.** A CT volume arrives and the system runs without further input: it locates the pancreas on the full scan, segments the organ and any lesion, scores the patient for tumor presence, and computes measurements — lesion volume, maximum diameter, anatomical subregion. Those findings populate a review interface where a clinician sees the scan with overlays, a drafted set of structured findings, and a locally hosted knowledge assistant that answers questions using retrieval over indexed pancreatic imaging literature. Every statement the assistant makes is tied to a source shown beside it; when retrieval finds nothing relevant, it declines rather than generating. The reviewer's accept, edit, or reject decision is stored, so the system produces a corrections record as a byproduct of being used. Full architecture, data flow, and schema appear in the technical appendix.

### Data integration — verified, not assumed

Combining PanTS with PANORAMA requires knowing which cases appear in both. That is verified rather than argued. PANORAMA's `clinical_information.xlsx` carries a `level` column that names the origin of imported cases: **194 rows labeled `MSD_dataset` and 80 labeled `NIH_dataset`**. Both sources are already inside PanTS, which holds 966 single-institution Memorial Sloan Kettering cases and 97 NIH cases. Excluding them is a filter on a column the dataset ships, not an inference from metadata.

| cohort | cases | tumor-positive |
|---|---:|---:|
| PANORAMA public set | 2,238 | 676 |
| less `MSD_dataset` | −194 | −98 |
| less `NIH_dataset` | −80 | 0 |
| **usable, non-overlapping** | **1,964** | **578** |

Inspecting the label archive confirms the rest. The two mask directories hold 482 and 1,756 files, totalling exactly the 2,238 rows in the spreadsheet; filenames are the study identifier verbatim, so the exclusion applies directly to files; and reading a mask confirms the label legend the remap depends on.

It also corrected an assumption. **Of the 578 usable tumor cases, 382 carry expert delineations and 196 are machine-generated** — because PANORAMA re-delineated the Decathlon cases rather than inheriting their labels, so 97 of the tumors removed by the exclusion were expert-annotated. The training design follows from that: the expert subset first, with machine-annotated cases as a labeled ablation rather than a silent addition.

Two controls run at ingest. The exclusion is **asserted at load** — a merged cohort that does not contain exactly 1,964 PANORAMA cases and 578 tumors aborts the run, the same guard that protects the existing training splits. And because a declared import list cannot catch *undeclared* duplicates, a **pixel-level detector** downsamples every volume, hashes it, and flags collisions across datasets; its recall is measured by planting twenty known duplicates and reporting how many it recovers.

One further constraint surfaced from the spreadsheet: PANORAMA's 2,238 studies come from **2,224 patients**, so splits must group by patient rather than study. PanTS does not have this property, so the rule exists only once the second dataset is present.

Merging also introduces differences that remapping alone cannot resolve — machine-generated organ masks, PDAC-only tumor coverage, a single contrast phase, and two different definitions of a negative case. Each is named with its mitigation in appendix section A4.7.

### How this exceeds prior coursework

The five-week machine learning project preceding this produced a working segmentation model, a serving endpoint, and a review interface. It has one disqualifying limitation: the model is handed the pancreas location before it segments. Every number it produces — lesion Dice 0.474, detection sensitivity 96%, specificity 17% on the official 901-scan held-out test set — assumes something already found the organ. Published models on the same benchmark find it themselves, so the results are not comparable and cannot be submitted anywhere. The capstone removes that assumption, and adds a second dataset requiring genuine cross-source integration, a relational and vector data layer, a separate retrieval-augmented AI system, and an external validation path.

The PanTS authors deliberately included a large number of tumor-free scans, noting that oversensitive models produce false positives that cause patient anxiety, overdiagnosis, and costly follow-up. My current model has exactly that failure mode: 96% detection sensitivity against 17% specificity. Correcting it is the center of this capstone.

**Professional quality and feasibility.** The existing repository carries a registered model with a version and checksum, twenty-seven pre-registered experiments with recorded decisions, two independent code audits, and complete documentation. The capstone adds a model card, data lineage, a validation suite that runs on ingest, and a review session with a practicing clinical stakeholder. Each pillar is scoped with a committed minimum and an optional stronger version, so a difficult week costs sophistication rather than a component. System capabilities are committed and must work; experimental outcomes are pre-registered and reported honestly either way.

## 2. Why? — Project Motivation and Capstone Value

I chose the pancreas because it is hard. It is soft tissue, it hides in a crowded abdomen, and pancreatic cancer is difficult to see even when someone is looking directly at it. My aunt is a diagnostic care coordinator — she schedules biopsies, works with the CT scans, and sits with patients to explain what the imaging showed, including telling them they have cancer. When I described this project to her, she told me the pancreas is an organ radiologists do not enjoy imaging. That conversation shaped the problem statement more than any paper I read. Software that finds the organ, outlines it, and flags a region worth a second look does not replace her judgment or anyone else's. It gets a human to the right part of the image faster.

There is a lot of healthcare behind me. My step-grandfather was a radiologist his entire career and my mother started radiology school. My grandfather was a vice president at Intermountain Healthcare, overseeing the Urban South region, and his job was to know what physicians considered the best available practice. They pointed at Johns Hopkins, so he read their research constantly — my mother describes his hospitals as having been propped up by it. He went to conventions meant for doctors so he could hear what they were arguing about, and brought what he found back into the hospitals he was building, including a women and children's center and daycare facilities inside them.

In 1998 he had a stroke. The angiogram found nothing and it was recorded as a transient ischemic attack, so no treatment followed. Months passed before the blood clot was found, and by then the damage was permanent. He lived with dementia for the rest of his life and died last year.

That is why I care about medical imaging specifically rather than AI in the abstract. The gap between what a scan can show and what a clinician needs to know is not an academic problem to me. It is also not lost on me that the dataset I train on and the pretrained model I fine-tune both come from the institution whose research he spent his career putting into practice, and that Johns Hopkins is where I hope to attend graduate school.

The unmet need in my own work is specific. My current system finds tumors well — 96% patient-level detection, higher than either published model on the benchmark — but flags most healthy patients as suspicious. A tool with that false-positive rate is not usable. Fixing it is a real engineering problem, and it is the one the dataset's own authors named when they deliberately included thousands of tumor-free scans to counter oversensitive models. I want to finish this because I want it to actually work.

## 3. How? — Technologies and Applied AI Skills

The preceding project supplies working machinery — model architecture, training loop, tracking, serving, and the review interface. What changes is everything touching data and everything touching the region of interest: a relational and vector data layer, cross-source integration, autonomous localization replacing the provided region, a tumor-presence gate, and the retrieval assistant. A full reused / adapted / new breakdown is in appendix section A8.1.

### Technologies and skills

| technology or skill | demonstrated capability | experience | learning plan |
|---|---|---|---|
| **Python, PyTorch, MONAI** — 3D medical image segmentation | 3D SegResNet trained by transfer learning from a pretrained abdominal CT checkpoint; isotropic resampling, Hounsfield windowing, ROI extraction; sliding-window inference over full volumes | Solid | No new tooling. Growth is in the problem — replacing a provided region with a predicted one changes the failure modes entirely. |
| **PostgreSQL with pgvector** — unified relational and vector storage | Cohort membership as a constrained relation rather than a text file, making the leakage that previously invalidated my results impossible to express; hybrid queries combining semantic similarity with structured predicates | Solid with PostgreSQL; new to pgvector | An extension over familiar ground. Build the index and tune HNSW parameters against a held-out question set in week 8. |
| **Retrieval-augmented generation, local LLM** (Ollama, Qwen) | Assistant answering only from retrieved passages, citing each visibly, declining when retrieval finds nothing relevant. Local execution means no imaging-derived data leaves the machine. | Solid — built embedding pipelines, vector search, and RAG several times | New work is evaluation, not construction: recall@k (whether the relevant passage appears in the top k results) and mean reciprocal rank (how near the top the first correct passage lands) for retrieval, and groundedness rate for generation. |
| **Cross-source integration and entity resolution** | Merging PanTS with PANORAMA across incompatible label conventions, annotation provenance, and reference standards; identifying cases present in both | **New** — never merged two clinical imaging datasets | Exclusion list and label remap behind unit tests and a load-time assertion, using the guard pattern that now protects my training splits. |
| **MLflow** — tracking and model registry | Versioned registration with checksums; every run tied to its cohort, preprocessing configuration, and git revision | Solid | Extend to a PostgreSQL tracking backend so local and cloud runs share one store. |
| **FastAPI, React, NiiVue** — serving and review interface | Inference endpoint triggered on scan arrival; tri-planar and 3D viewer with overlays, measurements, persisted review decisions | Solid with FastAPI and React; NiiVue used once | Deepen NiiVue for measurement display and comparison views from its documentation. |
| **Docker and rented cloud GPU** | Pinned environment running identically on an Apple Silicon laptop and a rented NVIDIA instance, raising throughput from one overnight run to several per day | Solid with Docker; limited with rented GPU — my cloud ML experience is Azure | Start on-demand rather than preemptible; re-establish a matched baseline on new hardware before any comparison; hold numerical precision constant. |
| **Experimental methodology** — pre-registration and honest reporting | Every hypothesis recorded with one changed variable and an accept threshold written before the run; paired per-case comparison with bootstrap intervals; results reported at the pre-registered horizon regardless of outcome | Solid | Extend to retrieval quality — the part of this project most at risk of being judged by impression rather than measurement. |

## 4. Ten-Week Project Schedule

Week 1 begins Monday, October 6. **Two of the ten weeks carry no new engineering.** Week 6 runs a pre-registered training experiment using existing code and absorbs any overflow from weeks 1 through 5; week 10 runs the final evaluation with the existing harness and produces documentation. The four engineering efforts identified in review — schema design, entity resolution across datasets, second dataset integration, and the localizer retrain — span weeks 1 through 5 rather than weeks 1 through 3.

| Wk | Primary goal | Planned work | Measurable deliverable | Ahead / behind |
|---|---|---|---|---|
| 1 | Relational foundation | Deploy schema; ingest the PanTS manifest; storage roots, scans, files, annotations; checksums; validation suite | 9,901 scans indexed with provenance and checksums; validation suite green | **A:** PANORAMA download started. **B:** cohorts still text files |
| 2 | Cohorts as constraints | Migrate splits to constrained tables; disjointness trigger; regression test | Every existing cohort reproduced from a query with identical membership; cross-fold writes rejected by the database | **A:** remap unit tests written. **B:** membership does not reproduce |
| 3 | PANORAMA ingested | Index labels and metadata; label remap behind unit tests; exclusion of the 274 imported cases; build the duplicate detector | PANORAMA indexed with provenance; exclusion asserted at load; duplicate detector with recall measured on twenty planted duplicates | **A:** merged cohort built. **B:** exclusion not asserted |
| 4 | Unified cohort | Merge; provenance columns for expert versus automated; extend validation; build the warm cache | Merged cohort verified disjoint from every evaluation set; cache built with a bit-identical regression test | **A:** EXP-27 smoke test run. **B:** cache unverified |
| 5 | Autonomy | Retrain the localizer on leak-free splits; measure containment after the final crop; run the cascade end to end | First autonomous lesion Dice on held-out PanTS, no provided region | **A:** gate prototyped. **B:** containment unmeasured |
| **6** | **Contingency — no new engineering** | Run the pre-registered training experiment on existing code; absorb overflow from weeks 1 through 5 | Accept or reject against the pre-registered bar with a paired bootstrap interval | **A:** weeks 1–5 complete on entry. **B:** week 5 work still open |
| 7 | Usable operating point | Volume gate and tumor-presence classifier; threshold on validation, report on test; **clinical stakeholder session on the current interface** | Specificity above 17% at detection at or above 96%, or a documented account of why that trade is unavailable; documented stakeholder feedback | **A:** corpus build started. **B:** no operating point beats baseline on both axes |
| 8 | Corpus and retrieval | Build and pin the filtered PubMed and PMC snapshot; chunk, embed, index; author the retrieval evaluation set | Queryable index with retrieval quality measured on held-out questions | **A:** embedding comparison started. **B:** index not queryable |
| 9 | Assistant and integration | Ollama and Qwen with cite-or-refuse; arrival-triggered inference; worklist; interface wiring; act on stakeholder feedback | End-to-end run from scan arrival to recorded reviewer decision; measured groundedness | **A:** final evaluation started. **B:** components not wired end to end |
| **10** | **Contingency and delivery — no new engineering** | Final held-out evaluation using the existing harness; leave-one-institution-out; model card and documentation; presentation | Final metrics with confidence intervals; complete documentation; presentation delivered | **A:** submission package sent to Johns Hopkins. **B:** documentation incomplete |

**Stretch items, deliberately outside the critical path:** external evaluation by the Johns Hopkins team; the embedding-model comparison; a knowledge-distillation arm; report generation quality.

**Stakeholder plan.** A diagnostic care coordinator has confirmed availability for the week 7 session, held against the current interface so her feedback can shape weeks 8 through 10. A practicing radiologist is being arranged as the primary reviewer; if that does not come together, the confirmed coordinator is the fallback rather than a hedge.

## 5. Reflection

The hardest part of the project that preceded this was not building the model. It was making it more accurate. You can run a hundred training runs and they do not simply get better. That realization changed how I work: I started writing down a hypothesis and a single changed variable before every run, along with the threshold that would count as success, and only then training. It is the biggest improvement I made, and if I could start over I would have done it from day one instead of week three. I am carrying it into the capstone from the beginning.

That discipline gets tested here in a way it has not been before. This project already has two rejected experiments, and one accepted result that turned out to be a false positive because I read the metrics before the run had finished. I have withdrawn a headline number of my own after finding a validation leak in my splits that inflated it by 0.11 Dice. Reporting that honestly cost me the best result I had. The capstone will produce more moments like that, and the plan explicitly separates committed system capabilities — which must work — from pre-registered experiments, which are allowed to fail and still count as results.

Technically I am moving into territory I have not been in. I have never merged two clinical imaging datasets with different annotation provenance and overlapping membership, and that is exactly where data leakage hides. I have never removed a human-provided region of interest from a pipeline built assuming one. I had not worked with 3D images at all before June, and I am taking a computer vision course concurrently, which is priming me directly for the localization work.

The largest source of uncertainty is one I do not control. The stretch goal is having my model evaluated by the research group that published the dataset. They may be slow, or the result may not be good. The project is deliberately built so that outcome changes nothing structural — I will have built an autonomous, externally validatable system either way, and I will report what comes back exactly as it comes back.
