> # ⛔ READ FIRST — `docs/SUBMISSION-READINESS.md`
>
> **BLOCKER 1: largest-connected-component post-processing is incompatible with tumour-wise
> sensitivity, the metric Johns Hopkins ranks on.** It structurally caps us at one detected tumour
> per patient. This is a design contradiction, not a tuning issue, and it is the **first code change
> of the capstone** — before any training run.
>
> Five blockers total. Nothing is emailed to JHU until they are closed.

# Capstone planning — working document

**Status:** gathering context. Not a proposal yet. This accumulates constraints and evidence so the
actual proposal can be drafted once the requirements files are in hand.

**Course project outcome:** finished with an A. Final registered model, honest held-out numbers, a
working end-to-end system. That work is the foundation this builds on, not something to redo.

---

## Constraints and context (confirmed)

**Timeline — 10 weeks, plus a running start.**
Twice the course project's five weeks. Work begins the moment the proposal is approved and continues
through the break, so the quarter starts with a real basis rather than a blank page. This is normal
and permitted — most students do it. **Important framing note:** the *proposal itself* must still
describe a 10-week project. Break work is a head start on execution, not extra scope on paper.

**What the degree chair cares about — this drives the design.**
Two things, in order:
1. **Meeting every capstone requirement.** Not partially, not "close enough."
2. **Covering as much of the program curriculum as possible.** The capstone is meant to demonstrate
   the breadth of what was learned across the degree, not just the deepest single skill.

The second point is what most changes the shape of the project. The course project was deliberately
narrow — a 3D segmentation model and the MLOps around it. A capstone judged on curriculum breadth
needs to deliberately pull in areas the course project skipped or only touched. **Data engineering
is the clearest gap**, and adding a real database plus a proper data layer is both genuinely useful
here and directly demonstrable.

**Hardware — unchanged, with one option.**
Primary remains the MacBook Pro (M5 Pro, 20-core GPU, 64 GB unified memory, PyTorch **MPS** backend).
Training runs have been 7-14 hours each, capping throughput at roughly one experiment per night.
A Windows laptop with **CUDA** is available and worth benchmarking — if meaningfully faster it
changes what is realistic, particularly for "train on all 9,000 cases." Treat as an early, cheap
experiment rather than an assumption.

---

## Technical spine carried forward (evidence-based, not speculative)

Everything below was measured during the course project and is logged in `experiments.md`.

**1 - Remove the oracle: the autonomous cascade.**
The current headline (lesion Dice 0.474) is **provided-ROI** — the model is handed the pancreas
region. A localize-then-segment cascade is already built and runs (`scripts/cascade_eval.py`), but
its accuracy has never been re-validated since the validation-leakage fix, so there is no clean
autonomous number. Finishing and validating this is capstone item one; it is what makes results
comparable to published benchmarks.

**2 - Add a tumor-presence gate: the specificity fix.**
Specificity is 17%, the weakest number. Key finding: **patient-level AUC is 0.804**, so the model
*can* discriminate tumor from healthy — the decision threshold is misplaced, not the capability.
Two things were proven:
- A **volume gate** on the existing model lifts specificity 17% to ~43% at 90% detection with **no
  retraining** (AUC on predicted volume alone = 0.843).
- **Retraining the segmenter to be cautious is the wrong fix.** EXP-25 (1:9 healthy) and the 1:3 run
  were both beaten at every matched operating point by gating the better segmenter instead.

The real work is a **dedicated tumor-presence classifier** as a gate in front of the segmenter. This
is the highest-value modeling contribution available.

**3 - Scale the data.**
Data scale was the only lever that consistently moved lesion accuracy; four recipe knobs (sampling,
loss, field of view, resolution) all came back null. Training used ~1,400 of 9,000 available cases
and the ceiling was never found. Requires the disk-cache work already started.

**Known failure mode to carry forward:** the model detects small tumors (<1 cm3) but over-draws them
25-50x, which simultaneously caps their Dice (0.067) and drives the low specificity. One behaviour,
two symptoms.

---

## Open questions — resolve once the requirement files arrive

- [ ] **Capstone requirements file** — awaiting. Defines hard deliverables and rubric.
- [ ] **Program curriculum file** — awaiting. Defines what breadth needs demonstrating.
- [ ] Which program topics does the current system *already* demonstrate, and which need deliberately
      building in? (Early read: data engineering, database design, and possibly distributed/scalable
      processing are gaps; ML modeling, MLOps, experiment tracking, deployment, and front-end are
      already covered.)
- [ ] Where does a **database** genuinely improve this system rather than being bolted on?
      (Candidates: a case/metadata store replacing `manifest.csv`; a predictions and review-decision
      store behind the UI; an experiment/results warehouse. The first two are real product needs.)
- [ ] Does CUDA on the Windows laptop meaningfully beat MPS? Benchmark early — it gates the
      data-scale ambition.
- [ ] Scope ceiling: what is genuinely achievable in 10 weeks plus break, at roughly one experiment
      per night on current hardware?

---

## Design principles to carry over

These worked and should not be relitigated:

- **Pre-register every experiment** — hypothesis and accept/reject bar written before the run. This
  caught a false positive (EXP-26) and prevented goalpost-moving (EXP-25).
- **Single variable at a time**, everything else held fixed.
- **Guardrails stay:** never commit raw data; split by patient, not slice; full-volume sliding-window
  evaluation; report pancreas and lesion Dice separately; no clinical or diagnostic claims;
  config-driven with the dataset path never hardcoded.
- **Adversarial review loop** — spec, second AI reviews the plan, code, review the code, a regression
  test per issue found. This caught the leakage bug and three rounds of deployment bugs.
- **Honest reporting.** Every number carries the caveat that lives in the experiment log.

---

## Requirements absorbed (from `BSAAI_Curriculum_Coverage_Reference.md`)

**The standard (§3).** PRO390 must demonstrate attainment of the *program's* outcomes, not one
feature. A credible proposal identifies **3-5 primary competency domains demonstrated deeply**, plus
several supporting domains, each tied to a concrete artifact and an evaluation method.

**Explicitly allowed:** the proposal does NOT need to force every course in. "Artificially adding
unrelated features weakens the architecture and creates unrealistic scope." So breadth is achieved
by choosing domains that genuinely belong, not by bolting on.

**Deep coverage — need >=3 of:** data engineering · machine learning · NLP/generative AI · analytics
and visualization · database and persistence design · cloud-based AI · software/web application
development · computer vision.

**Supporting coverage — need all or nearly all:** systems analysis & requirements · project
management · quality assurance · governance and ethics · professional documentation · business/user
value · deployment or reproducibility planning.

**Weak-capstone warning signs to avoid** (§9.3) — several are live risks for a project built on an
existing repo:
- a model trained once with no baseline comparison or error analysis
- a notebook without a usable system or reproducible process
- a static dashboard with no meaningful data pipeline
- **a collection of disconnected features added only to mention more courses**
- a project whose data source, legality, or reliability is undefined
- no testing, governance, or failure analysis

**Critical framing requirement (§11, §12).** The proposal must clearly **distinguish what already
exists in the repository from what is new capstone work**, and show the new work is substantial
enough for the term. This is the single biggest structural demand on us: the course project already
delivered a lot, so the proposal has to be explicit about the line between "done" and "to build."

**Expected artifacts (§13)** — several of: architecture diagram · **data-flow diagram** · **domain
model** · **entity-relationship diagram** · **data dictionary** · pipeline documentation ·
model-training report · model evaluation report · dashboard · **test plan** · automated tests ·
**risk register** · **ethical-impact analysis** · user guide · developer setup guide · final
presentation · demonstration recording · retrospective.
*(Bold = not yet produced by the course project.)*

---

## First-pass domain read (to confirm against the plan)

**Already demonstrated by the existing repo:** machine learning (deeply — 26 pre-registered
experiments, baseline comparison, error analysis), computer vision (3D segmentation), software
application development (React + FastAPI), quality assurance (regression tests, adversarial review),
project management (standups, plan, retrospectives), professional documentation, governance-adjacent
work (non-diagnostic framing, honest limitations).

**Genuine gaps that would make this a stronger capstone — and are real product needs, not bolt-ons:**
- **Data engineering** — the pipeline is script-and-CSV based; a real ingestion/transformation layer
  is both a curriculum gap and an actual weakness.
- **Databases and persistence** — `manifest.csv` is doing a database's job. Review decisions in the
  UI currently live in browser localStorage, which is not persistence in any real sense.
- **Information modeling** — no domain model, ERD, or data dictionary exists yet.
- **Analytics and visualization** — no dashboard over results/cohorts.
- **Cloud-based AI** — everything is local; deployment/scaling is documented but not built.
- **Governance and ethics** — handled honestly in prose, but no formal ethical-impact analysis or
  risk register.
- **NLP** — the PanTS dataset is described as *vision-language* with radiology-report metadata, so
  there is a legitimate hook here rather than a forced one. Worth exploring, not assuming.

**Status:** Template received in readable form — `BSAAI_Capstone_Proposal_Template.md`.

---

## 🔍 FLAGGED FOR REVISIT — PanTS is a vision-language dataset (NLP is legitimate here)

**Why this matters.** The PanTS authors describe it on their own repository as *"a vision-language
dataset, which enables development and external evaluation of AI for pancreatic tumor detection,
localization, and **reporting**, with multi-structure context and **metadata** to support robust,
anatomy-aware modeling."* Each scan also ships with metadata: patient age, sex, diagnosis, imaging
protocol, and biomarkers.

**The competitive evidence.** On the official PanTS leaderboard, **R-Super scores 53.4% DSC — the
top entry — and it gets there by using ~1.8K pancreatic lesion *reports* as additional supervision.**
That is a language signal improving a vision model. Our 0.474 was achieved with no report
supervision at all.

**Why this is a real hook and not a forced one.** Three separate capstone requirements are satisfied
by the same piece of work:
1. **NLP / generative AI** becomes a genuine primary domain rather than a bolt-on.
2. **Data engineering + information modeling** — reports and metadata are structured/semi-structured
   data that need parsing, validation, storage, and joining to imaging cases. That is exactly the
   ingestion-and-modeling work the curriculum wants to see.
3. It attacks a **known weakness** — 17% specificity. A report says whether a tumor was actually
   found; that is a per-patient label, which is precisely what the tumor-presence gate needs.

**Directions worth exploring (NOT decided yet):**
- Report-derived supervision for the segmenter (the R-Super direction).
- Structured extraction from reports/metadata into a real database — the join between imaging and
  text is the data-engineering deliverable.
- Automatic **report generation** from a prediction — "possible 2.1 cm lesion in the pancreatic
  head" — which closes the CADe loop into something a radiologist actually consumes, and is a
  natural generative-AI component with an obvious evaluation method.
- Metadata as tabular features for the presence classifier (age, sex, protocol, biomarkers) — this
  also pulls in **statistics** and **analytics**.

**✅ VERIFIED ON DISK (2026-08-01) — the data is already here.** `outputs/manifest.csv` has 29 columns
including a **`structured report`** field populated for **9,900 of 9,901 cases (100%)**, ~500
characters each, 9,643 unique. Format is free-text radiology findings, per organ:

```
FINDINGS:
Spleen:   Normal size (volume: 78.9 cc). Mean HU value: 44.9 +/- 26.5.
Liver:    Normal size (volume: 758.9 cc). Mean HU value: 37.7 +/- 21.3.
Pancreas: Normal size (volume: 56.6 cc). Mean HU value: 37.4 +/- 27.8.
...
```

Also present: `tumor?` (100%), `ct phase` (100%), `site` (94%), `sex` (53%), `age` (51%),
`manufacturer` (45%), `study year` (44%), `patient_id` (100%).

**Implication: no data acquisition needed.** The NLP/data-engineering component can be built from
what is already downloaded. That removes the single biggest risk from adding a new primary domain —
we are not betting on getting access to something.

**Note the reports carry quantitative statements** ("volume: 56.6 cc", "Pancreas is enlarged",
"Mean HU value") — so extraction yields *structured numeric fields*, not just sentiment. That is a
genuine information-modeling and database exercise, and those extracted values can be cross-checked
against the model's own measured volumes. A report saying the pancreas is enlarged, versus what the
segmentation measures, is a real validation signal.

---

## Proposal template — required structure (`BSAAI_Capstone_Proposal_Template.md`)

| Section | Requirement |
|---|---|
| **1. What?** | Problem · target user · what it is and its utility · technologies needed · **how it exceeds prior coursework** · path to professional quality · 10-week feasibility |
| **2. Why?** | **Minimum 250 words.** Motivation, unmet need, personal/professional drive. Must be more substantive than grades. |
| **3. How?** | **Annotated** list. Each item: technology/skill · demonstrable capability · **current experience level** · learning plan if new |
| **4. Schedule** | 10-week table: primary goal · milestones · **measurable deliverable** · ahead/behind indicator per week |
| **5. Pillars** | **Choose 3+** from: Data Analytics & Decision-Making · Data Engineering · Machine Learning · Process Automation · Data Science · Strategic Technology Leadership · Cloud Technology |
| **6. Reflection** | **Minimum 200 words** on challenge, problem-solving, new skills, resilience |

**Standard set by the template:** capstones must be **"enterprise-quality solutions you would be
proud to feature on your résumé and LinkedIn"** — built by doing, engaging **real users, stakeholders,
or live datasets**, with professional implementation and documentation, and **deep proficiency in at
least one core discipline**.

**Note the pillar list differs from the curriculum-reference domain list.** The proposal must use
*these* seven pillar names. Computer vision and NLP are not pillars — they are evidence *within*
Machine Learning / Data Science. Plan accordingly.

### Signal check on the reports (run 2026-08-01, real data)

Keyword presence vs. the tumor label, across all 9,901 cases (base rate 10.4% tumor-positive):

| Keyword in report | Reports containing it | % that are tumor-positive | Enrichment |
|---|---:|---:|---:|
| `lesion` | 1,013 (10%) | **31%** | **3.0x** |
| `mass` | 1,512 (15%) | **24%** | **2.4x** |
| `enlarged` | 4,245 (43%) | 11% | 1.1x (no signal) |
| `tumor` | 5,164 (52%) | — | (appears in template text, needs parsing not matching) |

**Read:** naive keyword matching alone already triples tumor enrichment. That is genuine predictive
signal in the text, before any modeling. It is also honest evidence that a text-derived feature could
help the tumor-presence gate — which is the exact component the capstone needs to fix the 17%
specificity.

**Caution to carry forward:** `tumor` appears in 52% of reports, which suggests it is part of a
templated section header rather than a finding. Reports must be **parsed structurally**, not
keyword-matched. That parsing *is* the data-engineering deliverable.

---

# PROJECT SHAPE — agreed 2026-08-01

## The frame
The course project produced a **research artifact** — a model that scores scans handed to it. The
capstone turns it into an **operational imaging pipeline**: a system that ingests data it has never
seen, stores what it learns, and improves from human corrections.

Every component has a job in that story:
new study arrives (ingestion) → validated + catalogued + joined to metadata/report (database) →
routed through localizer → segmenter → gate (ML) → prediction persisted with provenance (database) →
report parsed and cross-referenced (NLP) → radiologist accepts/edits/rejects and **that decision is
stored** (feedback loop) → performance monitored over time and across sources (analytics).

**Framing guardrail (unchanged):** human-in-the-loop system that flags regions for a person to look
into. NOT diagnostic. The LLM *describes and cross-references*, it never diagnoses. The question
"at what accuracy would this cross from assist to diagnostic, and who decides?" belongs in the
**governance section** — it is a strength to have reasoned about the line and deliberately stayed
behind it.

## Five primary domains — min/strong split
Committed = the minimum across all five (earns coverage). Stretch = depth *within* a domain, never
the domain itself. A bad week costs sophistication, not a pillar. (The rubric explicitly asks whether
stretch goals are separated from required deliverables.)

| Domain | Minimum (committed) | Strong (stretch) |
|---|---|---|
| ML | Autonomous cascade validated → first honest end-to-end number | Presence-gate classifier beating the volume-gate baseline |
| Data engineering | Ingestion pipeline: validate → catalogue → store, second dataset flowing | External validation across institutions, by scanner/phase |
| Database | Postgres live, manifest migrated, predictions + reviews persisted | Full provenance lineage; monitoring queries |
| NLP | 9,900 reports extracted to typed fields, accuracy-scored | Cross-referencing model measurements vs report language |
| Computer vision | Delivered (the segmenter) | Report generation from measurements, scored vs real report |

## Decisions locked
- **Second dataset:** MSD Task07 (420 pancreas CTs, classic benchmark, PanGuide3D used it for the
  same cross-cohort test). Swappable if it disappoints.
- **Cloud:** **Neon** free tier — permanent, 3 GiB, **never pauses** (Supabase sleeps after 7 days
  idle; Railway is a one-time credit). Makes **Cloud Technology** a legitimate pillar.
- **Storage split:** CT volumes stay on disk/object storage; Postgres holds paths, metadata, reports,
  predictions, reviews. Payload is ~50 MB of 3 GiB. This is correct medical-imaging practice, not a
  free-tier compromise.
- **UI:** already solid. New work = features stacking on it — upload/import page, generated-report
  view, prior-analysis (NLP) page, and **review decisions persisting to Postgres**.
- **Scale-to-9,000-cases:** demoted to STRETCH. It is 15h+ per iteration and competes with the
  presence classifier for the same GPU nights. The gate is worth more — it fixes the documented
  weakness and the AUC evidence points at it. Scale-up is a known quantity.

## Proposal-vs-execution structure (important)
The **10-week plan is the source of truth** and must stand alone as if zero break work happened.
Break work (Sept 3 → early Oct, ~4.5 weeks) then shows up as **ahead of schedule**, which the
template already has a column for. Nothing hidden — Quinn discloses the break plan verbally in the
chair meeting; the written proposal is judged on the 10 weeks because it passes to additional
reviewers after the chair.

## Ten-week schedule (self-contained)

| Wk | CPU track | GPU track (overnight) | Measurable deliverable |
|---:|---|---|---|
| 1 | Postgres schema, Neon live, ERD + data dictionary | Localizer retrain on clean splits | Schema deployed; ERD + dictionary committed |
| 2 | Migrate manifest → Postgres; patient-split enforced as constraint | Cascade evaluation | **First clean autonomous lesion Dice** |
| 3 | Report parser → `report_finding`; 9,900 reports structured | buffer | Extraction pipeline end to end |
| 4 | Hand-label sample; score extraction; derive per-patient labels | Presence classifier v1 | Extraction accuracy vs labeled sample |
| 5 | Gate integration; volume-gate baseline formalized | Presence classifier training | Baseline operating curve |
| 6 | Evaluate gate vs pre-registered bar | Presence classifier iteration | **Accept/reject decision** with numbers |
| 7 | Ingestion pipeline; acquire MSD Task07 | — | Second dataset flowing into Postgres |
| 8 | UI: upload page, generated-report view | External validation eval | Cross-institution performance by scanner/phase |
| 9 | Review persistence; monitoring dashboard; risk register; ethical analysis | — | Dashboard over `prediction ⋈ review` |
| 10 | Test plan, automated tests, docs, final report, demo recording | — | Complete package |

**Ahead indicators:** DB live + reports extracted before W3 · autonomous number by W2.
**Behind indicators:** no autonomous number by end of W3 · extraction unscored by W5 · gate
undecided by W7.

**Critical path:** DB → report extraction → per-patient labels → gate. Most novel work, and none of
it needs the GPU — which is exactly why it is the right thing to front-load.

---

# NLP DESIGN — what the text actually does (verified 2026-08-01)

## The trap to avoid: circularity
A report says "mass in the pancreatic head." Feed that in as a model input and you have not built a
detector — you have built a text classifier that repeats a radiologist's conclusion. Worse, the
deployment order makes it impossible: **scan arrives → AI runs → radiologist writes the report.**
The report does not exist yet at inference time.

**Rule: reports may be used during TRAINING. They must never be an inference input for detection.**

## R-Super — the published precedent (verified)
- **MICCAI 2025 Best Paper Award.** Same JHU lab as PanTS and SuPreM (`MrGiovanni/R-Super`).
- Converts radiology reports into **voxel-wise supervision** via two new losses: **Volume Loss** and
  **Ball Loss**, which force segmentation output to agree with tumor attributes stated in the report
  (count, size, location).
- Reports are parsed with **Llama 3.1 using radiologist-designed prompts** into structured attributes.
- Training with masks **and** reports improved F1 by **up to 16%** over masks alone.
- Reports used at training only; at inference the model takes a CT and nothing else.

**This validates the local-LLM idea.** Structured extraction with a local model is not a nice-to-have
— it is the technique behind the current best entry on this benchmark, from the dataset authors.
Cite as precedent rather than justifying from scratch.

**Honest nuance:** R-Super's core value is solving "abundant reports, scarce masks" (they paired
~2,000 masks with 100,000+ reports). PanTS gives us both for every case, so copying R-Super wholesale
is NOT automatically a win. Do not propose it as reproduction.

## ~~★ The strongest idea on the table: Volume Loss vs our over-segmentation~~ — **DEAD (2026-08-02)**
> **Superseded.** Reports are template-generated *from* the masks (see "REPORTS ARE TEMPLATE-GENERATED"
> at the end of this doc). Volume Loss would supervise the model with a restatement of its own labels.
> Kept below only to show the reasoning that was tested and rejected. **Do not put this in the proposal.**

Our single worst behaviour — the one that caps small-tumor Dice at 0.067 **and** drives the 17%
specificity — is **over-drawing small tumors by 25-50x**. One behaviour, two symptoms.

Volume Loss penalises exactly that: it forces predicted tumor volume to match the size stated in the
report. Our reports contain quantitative volume statements. **This is a targeted, published treatment
for the specific disease we diagnosed.**

Reframes the NLP component from "added for coverage" to: *"I identified over-segmentation as my core
failure mode, found that the state-of-the-art method on this benchmark addresses it through
report-derived volume supervision, and implemented it."*

Gives a real pre-registered experiment: **does report-supervised volume loss reduce over-segmentation
on small tumors?** Bar to be set before running, per standing practice.

## NLP now has three evidence-backed jobs
1. **Extraction layer** — local LLM parses 9,900 reports into typed fields (the data-engineering
   deliverable; accuracy scored against a hand-labeled sample).
2. **Per-patient labels** — supplies the presence/absence signal the gate needs.
3. **Volume supervision** — attacks over-segmentation directly (the R-Super insight, applied to our
   documented weakness).

Plus two output-side / QA uses that carry no leakage risk:
4. **Cross-referencing** — model-measured organ volume vs report-stated volume; disagreement flags a
   probable segmentation failure automatically across 9,900 cases.
5. **Report generation** — structured finding produced from the model's measurements, scored against
   the real report.

## Feature design for the gate (per-patient binary classifier)
**CORRECTED RULE (supersedes an earlier looser note): reports are TRAINING-TIME ONLY and are never
an inference input for any component.** The reason is not only circularity but **availability** — the
report does not exist when the model runs (scan arrives → AI runs → radiologist reports). Simple test:
**if it is not in the scan or its DICOM header, it cannot be an input.**

| Source | Examples | Usable as an inference feature? |
|---|---|---|
| Segmenter outputs | predicted lesion volume, peak/retained confidence, pancreas volume, lesion/pancreas ratio | ✅ yes |
| Metadata (ships with the scan) | age, sex, contrast phase, scanner manufacturer | ✅ yes — not NLP-derived |
| Report content — any organ | volumes, HU, findings | ❌ no — does not exist at inference |
| Report content — pancreas findings | "mass", "lesion" | ❌ no — also circular; use as TRAINING LABELS only |

**Nothing NLP-derived ever enters the model at inference.** That is what makes the system deployable
on a scan nobody has reported on yet — which is the entire product premise.

## Set aside (not chosen)
- Direct text-into-CV fusion (FiLM, cross-attention, broadcast embeddings) — works in principle, but
  awkward for voxel-wise output and carries the full circularity problem. Stretch experiment at most.
- Retrospective audit tool (reports *are* a legitimate input when reviewing already-reported cases to
  catch misses) — a different product with different value. Parked, not pursued.

---

# ★★ DATA INVESTIGATION — 2026-08-01 (run on real manifest, no drive needed)

## Report structure — richer than expected
Tumor-positive reports contain a fully structured lesion block:

```
Pancreas lesions:
Pancreas lesion 1:
  Location: pancreas head.
  Size: 2.4 x 1.4 cm (image 14). Volume: 5.3 cc.
  Enhancement relative to pancreas: Isoattenuating (HU 90.6 +/- 21.1).
IMPRESSION:
  A isoattenuating pancreas (head) mass (2.4 x 1.4 cm).
```

Extractable typed fields: **location** (head/body/tail), **2-D size**, **volume in cc**,
**enhancement class**, **HU mean/SD**, **lesion count**, plus an IMPRESSION summary. Multi-lesion
cases exist (up to 5 reported). Extraction is a genuine, reliable data-engineering deliverable.

## FINDING 1 — Volume Loss on masked cases is REDUNDANT (naive plan killed)
For the 312 cases with **both** a mask and a reported lesion, report volume ~= mask volume:

| metric | value |
|---|---|
| correlation r | 0.68 |
| median ratio report/GT | **1.001** |
| within 10% of GT | 69% |
| within 2% of GT | 43% |

The reported volume is derived from the mask. **Volume Loss there teaches nothing new** — it would be
a constraint computed from the data already being trained on. Do NOT propose Volume Loss as the
headline fix for over-segmentation. (Caught before it became load-bearing.)

## FINDING 2 ★ — 701 cases: report describes a lesion, MASK IS EMPTY
This is R-Super's actual premise, present in our own data.

| | no lesion block | HAS lesion block |
|---|---:|---:|
| **mask NEGATIVE** | 8,167 | **701** |
| **mask POSITIVE** | 721 | 312 |

Example — `PanTS_00002303`, mask 0 mm3:
*"Pancreas lesion 1: Location: pancreas head. Size: 3.1 x 2.2 cm. Volume: 9.3 cc. Hypoattenuating."*

**Implications:**
1. On these 701, the report is the ONLY signal — report supervision is genuinely additive, not
   redundant. This is where R-Super's approach legitimately applies to us.
2. These cases currently sit in the **training set as negatives** — we have been teaching the model
   that scans with radiologist-described tumors are healthy. That is a real label-quality defect.
3. Reframes the NLP contribution: not *"Volume Loss fixes over-segmentation"* but **"report
   supervision recovers ~701 tumor cases currently mislabeled as healthy, and corrects a
   training-set labeling error."** Stronger, and it is our own finding from our own data.

## FINDING 3 — the specificity effect is REAL but SMALL (do not over-claim)
Tested on the frozen 750-case tumor-free test cohort; 122 (16%) have a report-described lesion.

| cohort | flagged by model |
|---|---:|
| mask-empty, report **describes a lesion** (n=122) | **93%** |
| mask-empty, report **silent** (n=628) | **81%** |

The 12pp gap is genuine evidence the model preferentially flags cases where a radiologist saw
something — i.e. it is detecting real findings, not hallucinating.

**BUT:** specificity only moves **17% -> 19%** when those cases are excluded. The model still flags
81% of genuinely silent healthy scans. **Over-prediction is a real model problem, not a labeling
artifact.** Report this honestly; do not build a narrative on "my specificity was understated."

## RESOLVED — see 'REPORTS ARE TEMPLATE-GENERATED' below. The 701 are NOT a goldmine.

### (original open question, kept for provenance)
We previously documented that some PanTS masks are **genuine source defects** (101 both-empty cases
from one site/scanner cohort; 7 corrupt-huge combined masks). So the 701 could be:
- (a) annotation never performed — the R-Super premise, best case
- (b) annotation broken/corrupt — a data-quality bug
- (c) auto-generated or unreliable report text — worst case

**Action: visually inspect a sample of the 701 in the NiiVue viewer** — does a lesion visibly exist
at the reported location (e.g. "pancreas head, 3.1 x 2.2 cm")? That single check decides whether this
is a headline capstone contribution or a footnote.

---

# ★★★ RESOLVED — REPORTS ARE TEMPLATE-GENERATED (2026-08-02)

**This supersedes the optimistic reading of the 701 report-only cases. Investigated and closed.**

## Two independent tests, both negative

**Test 1 — correlation.** On the 122 report-only cases inside the frozen test-negative cohort, does
the model's predicted lesion volume track the report's stated volume?

| cohort | r |
|---|---:|
| all 122 | **-0.090** |
| restricted to plausible sizes (0.5-20 cc, n=84) | **-0.045** |

Zero, with a hint of negative. Our model detects tumors 96% of the time. If lesions of the stated
sizes were present, predicted volume would track reported volume. It does not.

**Test 2 — visual.** Rendered a representative random sample (0.5-8 cc, plausible focal-mass range).
No focal masses visible. In several cases (`00006446`, `00002914`, `00004787`, `00009300`) the named
subregion outline lands on **bowel or duodenum**, with no pancreas mask nearby — so the head/body/tail
subregion masks are unreliable for these cases too.

## The actual explanation
The report format gives it away:

```
Spleen: Normal size (volume: 78.9 cc). Mean HU value: 44.9 +/- 26.5.
```

**No radiologist dictates "Mean HU value: 44.9 +/- 26.5."** These are **template-generated from
segmentation measurements**, not clinical dictation. That single fact explains every observation:

- report volume matched mask volume at ratio **1.0015** for the 312 → the text was *generated from*
  the mask
- the 701 have anatomically impossible sizes (148 cc "lesions" in a ~90 cc organ) → a generator
  emitting lesion entries from an unreliable source
- one case reported location as "pancreas head/body/tail" → a template filling every subregion

Consistent with PanTS being published as a **vision-language** dataset "for reporting" — the text
exists to train report generation and is **derived from** the annotations.

## Consequences for the plan

**DEAD — report supervision as an independent training signal.**
R-Super's premise is that text carries information the masks lack. Here the text *is* the masks in
prose form. Volume Loss / report supervision would teach the model nothing new. **Do not propose
this.** (Caught in planning, not week 6.)

**PROMOTED — report generation becomes the strongest NLP component.**
Precisely *because* the reports are templated, generation is a clean task with **exact ground truth**:
generate a structured report from the model's own measurements, then score it **field by field**
(organ, volume, HU, normal/enlarged, lesion location/size) against the template. No fuzzy text
metrics, no human rating. A far more evaluable generative-AI component than "an LLM writes prose."

**STILL VALID — structured extraction as the data-engineering deliverable.**
Parsing 9,900 templated reports into typed fields remains real ETL work with measurable accuracy,
and it populates `report_finding`. Less scientifically novel than hoped, but honest and it feeds the
database layer.

**STILL VALID and now more interesting — the cohort-contamination finding.**
16.3% of the frozen tumor-free test cohort (122/750) carries a report-described lesion, versus **0%**
of the positive cohort (0/151), because cohorts were built from **mask presence alone**. Split by
carved fold: train 452/7200 (6.3%), val 127/1800 (7.1%), test_neg 122/750 (16.3%),
`scaledmax_clean` (what the final model trained on) 38/1412 (2.7%).
This is a genuine methodological result about how the benchmark cohorts were constructed, and the
database layer prevents it structurally — cohorts defined by a **join across mask AND report
evidence** rather than one column.

**NOT the specificity explanation.** Removing those 122 moves specificity only **17% -> 19%**. The
model flags 81% of genuinely report-silent healthy scans. Over-prediction is a real model problem.
Report this honestly; do not build a narrative on "my specificity was understated."

## Download corruption ruled out
Quinn asked whether his download corrupted the masks. Evidence says no:
1. For the 312 masked+reported cases, report volume matches mask volume to **1.0015** — impossible if
   voxel data were corrupted.
2. The 701 are **evenly spread across sites** (4.6%-8.7% for every site with 150+ cases). Download
   corruption is random and would cluster by download session, not by an institutional variable.
3. Pancreas, head, body, and tail masks are present and correct for those same cases — corruption
   would not selectively drop one organ.
No public GitHub issue found documenting this; **worth filing one** — it would be a real contribution
and a legitimate capstone line.

---

# DECISIONS — 2026-08-02 (post-investigation)

## 1. Contamination finding: SUPPLEMENTAL, not proposal body — **Quinn's call, agreed**
The 122/750 vs 0/151 cohort result affects **our development**, not the **approval decision**. The
chair is approving scope, rigor, and curriculum coverage — not adjudicating a dataset defect.

- **In the proposal:** one sentence, factual, no dig-in. Something like *"Preliminary data validation
  surfaced an inconsistency between mask-derived and report-derived tumor labels in the evaluation
  cohorts; the database layer is designed to make cohort definitions verifiable rather than implicit."*
  That earns the data-engineering pillar without spending a page on it.
- **In a supplemental packet** (Quinn fills out, hands to the professor if asked): the full evidence —
  counts by fold, the two negative tests, the correlation table, the contact sheets.
- **Verbally:** Quinn can go as deep as the room wants.

**Rationale:** a proposal that spends real estate on a dataset defect reads as *"student found a
problem"* rather than *"student is proposing a system."* One sentence signals diligence; three pages
shifts the subject.

## 2. GitHub issue: DEFERRED to Week 1-2 or the break — **Quinn's call, agreed**
Not now. *"Hey something weird is here"* is a bad issue and a worse first impression with a lab whose
checkpoint we depend on. File it only when we can state, in order:

- [ ] exact count and case-ID list of affected scans, with the manifest query that produced them
- [ ] the two negative tests (correlation r, visual sample) with methodology stated
- [ ] the plausibility argument (lesion volumes exceeding organ volume; "head/body/tail" locations)
- [ ] what we ruled out (download corruption — the 1.0015 volume-match argument; site clustering)
- [ ] a specific, answerable question, not a complaint — e.g. *"Are the `structured report` fields
      derived from the released annotations, or from a separate source? Cases X, Y, Z describe
      pancreas lesions with empty lesion masks."*
- [ ] a reproducible snippet a maintainer can run

A well-formed issue is a citable contribution. A vague one is noise. **Timing: after the first data
pass in Week 1-2, or over the break.**

## 3. Reports are synthetic: HEDGE — **Quinn's call, agreed and important**
> *"I don't want to claim something just because we think it to be true."*

Correct. We have **strong circumstantial evidence**, not confirmation. State it as inference.

**What we can assert as fact (verifiable):**
- The reports are **rigidly templated** — identical sentence frames across 9,900 cases, with
  machine-precision fields (`Mean HU value: 44.9 +/- 26.5`) that no human dictates.
- For the 312 masked+reported cases, **report volume matches mask volume at ratio 1.0015** — a
  numerical identity, not a clinical estimate.
- **The PanTS paper does not document a report field at all.** Verified 2026-08-02 against
  arXiv:2507.01291 (Li et al., 2025): the metadata list is *"patient age, sex, contrast phase,
  diagnosis, in-plane spacing, and slice thickness."* No reports, no text, no vision-language claim.
  The `structured report` column in `metadata.xlsx` is **undocumented in the publication.**

**What we infer (label as inference):**
- These reports appear to be **generated from measurements rather than clinically dictated.**

**Proposal wording (approved register):**
> *"The dataset includes a `structured report` field that is not described in the accompanying
> publication. Its rigid templating and exact numerical agreement with the segmentation masks
> (volume ratio 1.0015 across masked cases) indicate the text is most likely derived from
> measurements rather than clinically dictated. We treat it as machine-generated for the purposes of
> this project and design the NLP component accordingly; confirming its provenance is an open
> question we intend to raise with the dataset authors."*

That is honest, states the evidence, labels the inference, and turns the uncertainty into a planned
action instead of a hole.

## 4. More investigation BEFORE locking scope — **Quinn's call, agreed and correct**
> *"Every time we look into something it makes a stronger case for us... if we did not look into the
> reports, the NLP would have been a huge issue."*

This is the single best process decision of the planning phase. The report investigation cost two
days and prevented a dead pillar in Week 6. **Apply the same treatment to every pillar before it is
written into the proposal.** Pre-mortem list in the next section.

---

# STORAGE & COMPRESSION — measured 2026-08-02

Computed from `outputs/manifest.csv` (`shape` column, all 9,901 scans parsed). Total voxels across
the cohort: **297,548,600,819**. Median scan 29.3 M voxels; largest 240 M.

## Uncompressed footprint

| what | size |
|---|---:|
| **on the external drive today (gzip, images + all labels)** | **382 GiB** |
| CT images alone, uncompressed `int16` | **554 GiB** |
| + one `combined_labels` `uint8` per case | + 277 GiB |
| **images + combined labels, uncompressed** | **831 GiB** |
| if all **28** structures kept as separate full-volume `uint8` masks | **8,313 GiB (8.1 TiB)** |

Two things fall out immediately:

1. **Decompressing in place is not an option.** 831 GiB does not fit on a 1 TB internal drive that is
   already hosting an OS, and the external drive has 83 GiB free. The 8.1 TiB figure shows why the
   dataset ships one packed `combined_labels` volume instead of 28 separate masks — sparse binary
   masks compress ~30:1, so the packed+gzipped form is the only sane distribution.
2. **We don't need to.** See below.

## The actual working set is tiny

Training never reads a full-resolution scan. The whole-box recipe crops to the pancreas, resamples to
1.5 mm, and resizes to 128³ — that is the *only* array the model sees.

| cache | per case | total |
|---|---:|---:|
| 128³ `float32` image + `uint8` label | **10.0 MiB** | — |
| × 1,412 (`scaledmax_clean`, current training cohort) | | **13.8 GiB** |
| × 9,901 (entire PanTS Mini) | | **96.7 GiB** |

**So the whole dataset, in the form the model actually consumes, is 97 GiB — and the cohort we train
on is 14 GiB.** That fits on the internal SSD with room to spare, and it is *already decompressed*
(the deferred "persistent disk cache" from Week 3 is exactly this).

**Conclusion: decompression is a caching decision, not a storage decision, and it is already solved
in principle.** Keep the archive gzipped on the external drive as cold storage; materialize the 1.5 mm
whole-box cache once to fast local disk. This is a legitimate **data-engineering deliverable** —
cold-store / warm-cache separation, with a measured justification — and it directly fixes the MPS
throughput problem, because gzip decompression on every epoch is CPU cost we currently pay repeatedly.

## Postgres holds **no voxels** — settled

One uncompressed CT averages **57 MiB**. Neon's free tier is **3 GiB** — about **53 scans**. Storing
imaging in a relational database is wrong at any tier, not just the free one; it defeats the storage
engine, blows up backups, and makes every query slow.

**The database stores the *index*, not the *images*:** case IDs, file paths, spacing/shape,
acquisition metadata, parsed report fields, model predictions, cohort membership, and reviewer
decisions. Estimated **~50 MB of the 3 GiB budget** — 1.6%, with room for many experiment runs.

This is the standard medical-imaging pattern (PACS stores pixels on a filesystem/object store; the
database stores the study index), and being able to say *"we measured it: 831 GiB uncompressed, 57 MiB
per scan, 3 GiB tier — here is why the pixels live on disk"* is a stronger design-justification answer
than citing the convention.

**Open item for the proposal:** if we want the demo reachable from outside the laptop, the *images*
need a home too. Options to price out: object storage (S3/R2/B2) for a small demo subset (~50 cases ≈
1-3 GiB compressed), versus keeping the demo local and hosting only the API + database. Not blocking.

---

# ★★★ MSD TASK07 INVESTIGATION — 2026-08-02. **THE EXTERNAL-VALIDATION PILLAR AS DESIGNED IS DEAD.**

Investigated before writing it into the proposal, exactly as the reports were. Same outcome: the plan
would have failed, and it would have failed *publicly*, at defense.

## Verified facts about MSD Task07 (medicaldecathlon.com + MSD dataset paper)

| property | value |
|---|---|
| total cases | 420 (**281 train + 139 test**) |
| **test labels** | **NOT public.** Organisers: *"We will release the validation scripts for public scrutiny, but not the validation labels."* Usable labeled data = **281 cases**, not 420. |
| labels | `1 = pancreas`, `2 = tumour` — **same convention as our Level 4.5** |
| **tumor coverage** | **281/281 = 100%. There are ZERO healthy cases.** |
| modality | **portal-venous phase only** — single phase |
| **source** | **Memorial Sloan Kettering Cancer Center — single institution** |
| spacing | in-plane 0.61-0.98 mm; **slice thickness median 2.5 mm, max 7.5 mm** |
| tumor volume | min 0.4 cc, median 6 cc, **max 732 cc** |
| pancreas volume | min 20 cc, median 77 cc, max 201 cc |
| license | **CC-BY-SA 4.0** (permissive) |
| availability | live — AWS direct + Google Drive |

## ☠ THE KILLER: Task07 is already inside PanTS

`site detail == "Memorial Sloan Kettering Cancer Center"` in our own manifest:

- **966 PanTS Mini cases from MSKCC** (331 tumor-positive, 34.3% prevalence — versus 10.4% overall)
- distributed straight through our carved folds: **742 in `train.txt` (207 positive)**, 198 in
  `val.txt` (49 positive), 195 in the official test split (78 positive)

And the arithmetic closes it:

| | PanTS MSKCC subset | MSD Task07 published |
|---|---:|---:|
| median tumor volume | 4.9 cc | 6.0 cc |
| **max tumor volume** | **732.4 cc** (`PanTS_00002720`) | **732 cc** |

**A 732 cc pancreatic tumor is a once-in-a-dataset outlier. Both datasets have exactly one, from the
same institution. That is the same scan.** Combined with the same donor (Amber Simpson, MSKCC, who
donated Pancreas / Colon / Hepatic Vessels / Spleen to MSD) and PanTS's stated aggregation of public
sources, this is as close to proof as we can get without file hashes.

**Consequence: "external validation on MSD Task07" would have validated the model on scans it was
trained on.** Same leakage class as `make_scaled_split.py` — and this time it would have been the
headline claim of the capstone rather than a bug found in an audit.

**Do not propose MSD Task07 as an external test set.** If we use it at all, it is as a
*label-convention sanity check*, disclosed, not as evidence of generalization.

## Secondary reasons it was a poor fit anyway
Even without the overlap, Task07 could not carry the pillar:
1. **Zero healthy cases** → **specificity is undefined on it.** Specificity is our headline weakness
   (17%) and the whole point of the volume gate. A validation set that cannot measure the metric we
   are trying to improve is the wrong validation set.
2. **Single institution, single contrast phase** → no domain shift. External validation is supposed
   to test transfer across scanners, protocols, and populations. MSKCC portal-venous only tests none
   of that. (And EXP-14 proved contrast phase is the single strongest driver of our behaviour.)
3. **281 usable cases**, not 420 — the headline number is nearly halved by the withheld test labels.
4. Median slice thickness 2.5 mm (max 7.5 mm) vs the finer PanTS distribution → a resolution
   confound layered on top.

## ✅ THE REPLACEMENT — better than the original plan, and free

**Leave-one-institution-out validation inside PanTS.** Our manifest already carries `site detail` and
`site nationality`. Single-institution cohorts with n>=100:

| institution | country | cases | tumor-positive | prevalence |
|---|---|---:|---:|---:|
| Memorial Sloan Kettering Cancer Center | US | 966 | 331 | 34.3% |
| University Hospital Tubingen | DE | 894 | 73 | 8.2% |
| University of Minnesota Health | US | 665 | 36 | 5.4% |
| Medical University of Warsaw | PL | 293 | **0** | 0.0% |
| IRCAD Hopitaux Universitaires | FR | 173 | 13 | 7.5% |
| Guangdong Provincial People's Hospital | CN | 113 | 22 | 19.5% |

**Why this is strictly better than the MSD plan:**

- **It is genuinely held out** — we control the split and can assert disjointness with an assert, the
  same guard that now protects `train.txt`.
- **It measures real domain shift** — US / Germany / Poland / France / China, different scanners,
  different protocols, tumor prevalence from 0% to 34%.
- **Specificity is measurable**, because these cohorts contain healthy scans. Warsaw is **293 cases,
  0 tumors** — a pure specificity probe, which is exactly the axis we are weakest on.
- **No new download, no new license, no new preprocessing path.** Zero infrastructure risk.
- **It is a stronger scientific claim:** *"Dice degrades by X when the model meets an institution it
  has never seen"* is a more useful, more honest result than a single number on a second dataset.
- **It converts a known weakness into a designed experiment.** Site was already a suspected confound
  (EXP-13/14 contrast-phase results, the 101 both-empty healthy cohort at site CH/SIEMENS).

**Pre-register now:** hold out **Warsaw (specificity probe)** + **Guangdong (domain shift + high
prevalence, non-US)** + optionally **Tubingen**. Train on the remainder. Report per-site Dice,
detection, and specificity. Cost: one retrain, no new data.

## Still worth checking (not blocking)
- **PanTS official leaderboard**: the paper reserves **26,489 test scans for third-party evaluation**.
  A leaderboard submission would be true external validation with zero leakage risk. Verify the
  submission portal is live and what it accepts. **This is the strongest possible version of the
  pillar if it is open.**
- **PANORAMA** (cited by PanTS as the largest prior public pancreas dataset) as a genuine second
  dataset — but **run the same overlap check first**. Assume overlap until disproven.
- Every other candidate dataset gets the overlap check before it enters the proposal. Note the
  manifest already shows `National Institutes of Health` (97 cases) and `IRCAD` (173) inside PanTS —
  so NIH Pancreas-CT and LiTS-adjacent sources are likely absorbed too.

## Process note
Two pillars investigated, two pillars materially changed before writing. The report dig killed
NLP-as-supervision; this dig killed MSD-as-external-validation. **In both cases the replacement is
stronger than the original.** Continue this before locking any remaining pillar.

---

# ★★★ JHU EXTERNAL EVALUATION — **IT IS LIVE, AND IT RESHAPES THE CAPSTONE** (2026-08-02)

Verified from the official repo README (github.com/MrGiovanni/PanTS).

## It is not a self-serve leaderboard — it is an evaluation service by email

> *"To submit your model for evaluation, please email Dr. Zongwei Zhou (zzhou82@jh.edu) with: your
> model checkpoint · testing script · in-distribution test results · a brief README with usage
> instructions. The JHU Team will assess performance on three large out-of-distribution test sets and
> a RSNA Dataset, for which all pancreatic tumors have been re-annotated by our team."*

**The four held-out sets (26,489 scans total):**

| set | n | access |
|---|---:|---|
| UCSF Pancreatic Dataset | 13,458 | proprietary |
| Polish Pancreatic Dataset | 5,259 | proprietary |
| Peking University Dataset | 3,066 | proprietary |
| RSNA Abdominal Trauma Detection (re-annotated by JHU) | 4,706 | public images, JHU labels |

This is **better than a leaderboard**. Three genuinely proprietary cohorts on three continents,
re-annotated by the dataset authors, that we can never see, never overfit, and never leak. It is the
answer to *"does this work anywhere else"* in the strongest form available anywhere.

## ✅ We are NOT disqualified for using SuPreM or external data — CONFIRMED

Quinn's specific worry, answered by the README itself:

1. **SuPreM is a listed benchmark method** on their own table. Our exact transfer approach is in scope.
2. **R-Super, their own MICCAI Best Paper, carries the footnote:** *"Trained with additional external
   data (1.8K pancreatic lesion reports)."* External data is **disclosed with a dagger, not banned.**
3. **They are actively recruiting:** *"We are calling for more baseline methods."* Most rows in their
   benchmark table are **empty**.

(Contrast with the *MSD* challenge, which does forbid task-specific external pretraining. Different
challenge, different rules — do not confuse them.)

## Where we would actually land

Their in-distribution benchmark (901 official test scans) vs our registered model:

| model | P-Sen | T-Sen | Spe | AUC | DSC |
|---|---:|---:|---:|---:|---:|
| MedFormer | 80.8% | 75.2% | 90.0% | 0.924 | 52.9% |
| R-Super | 80.1% | 80.1% | 93.2% | 0.903 | 53.4% |
| **ours (provided-ROI)** | **96%** | **not computed** | **17%** | **0.804** | **47.4%** |

Read honestly:
- **DSC 47.4% vs 52.9/53.4% is respectable** — but ours is **provided-ROI (oracle box)** and theirs
  is autonomous. **NOT COMPARABLE. Never present this table without that caveat.**
- **P-Sen 96% genuinely exceeds both** — we are the most sensitive model on the board, by a lot.
- **Spe 17% vs 90/93% is the whole story.** We are not a worse segmenter; we are an untuned detector.
  This is precisely what the volume gate / presence classifier exists to fix, and the AUC 0.804 says
  the discriminative signal is already there.
- **T-Sen (tumor-wise sensitivity) we have never computed.** Required to fill their row. Concrete,
  bounded deliverable: per-lesion connected-component matching. **Add to the plan.**

## ☠ THE CONSTRAINT THAT REORGANIZES EVERYTHING

**We must send them a checkpoint and a testing script that runs on THEIR scans. There is no oracle
pancreas box on their data. A provided-ROI model is UNSUBMITTABLE.**

So the autonomous localize-then-segment cascade is not a nice-to-have or a "capstone stretch" —
**it is the precondition for the single most valuable result available to this project.**

That is the cleanest possible scoping argument for the chair:
> *"The strongest external validation in this field is open to us. To use it, the model has to run
> without a human drawing the region first. That is what the capstone builds."*

## Whole-scan inference is CHEAPER than feared — measured, not guessed

Computed over all 9,901 manifest entries, resampling each scan to 1.5 mm isotropic:

| | median | p90 | max |
|---|---:|---:|---:|
| full-scan dims @1.5 mm | 253x190x142 | 313x238x293 | 944x333x573 |
| voxels | 6.9 M | 17.0 M | — |
| float32 size | **26.5 MiB** | 64.9 MiB | — |

**A whole CT at 1.5 mm is only 3.3x the whole-box 128³ cube (8.0 MiB).** Sliding-window 128³ at 50%
overlap needs a **median of 12 windows per scan** (p90 45). At the current ~0.6 s/scan serving time,
autonomous whole-scan inference lands around **7 s/scan median** — completely acceptable, and it does
**not** require a different model, only a different inference path.

**Conclusion: "train/infer on the whole scan" is an engineering path, not a research risk.** We
already have `scripts/cascade_eval.py`. The open questions are accuracy and containment, not
feasibility.

## ★ THE TUMOR-SUPPLY FINDING — Quinn was right, and it is now measured

> *"If we could find more tumors I think that would be great. The training data seems to not have
> enough for us."*

**Confirmed, exactly.** Accounting over the carved folds:

| | count |
|---|---:|
| tumor-positive cases in all of PanTS Mini | 1,033 / 9,901 (10.4%) |
| tumor-positive available in `train.txt` | **706** |
| tumor-positive actually used by `scaledmax_clean` | **706** |
| **unused tumor-positive training cases remaining** | **0** |
| unused tumor-**free** training cases remaining | **5,788** |

**We have already consumed every single tumor-positive scan available for training.** "Scale to 9,000
cases" therefore does **not** mean more tumors — it means **only more healthy scans**, which is
exactly EXP-25 (`fullhealthy`), already run and **rejected** (specificity 17%→46%, but detection
96%→88%, below the pre-registered floor).

**This is a major scoping correction.** It reframes three things at once:
1. **"More data" is no longer a lever for lesion accuracy.** The data-scale finding (EXP-17) is real
   but we have already spent it. Saying "we'll scale up" in the proposal would be wrong.
2. **The capstone must extract more from 706 tumors, not find more tumors** — which is precisely the
   gate/classifier/cascade direction we already chose, now with a hard justification instead of a
   preference.
3. **More tumors can only come from outside PanTS.** That, and only that, is a legitimate reason to
   want a second dataset — *not* validation, which leave-one-site-out and the JHU service cover
   better. **This is the surviving argument for external data. Keep it.**

### If we chase more tumors, the protocol is fixed
Every candidate gets the overlap check **before** it enters the proposal:
1. institution names in the source's documentation vs our `site detail` column
2. tumor-volume distribution fingerprint (min / median / **max** — the 732 cc outlier is what
   convicted MSD Task07)
3. case counts and prevalence
Assume overlap until disproven. **PANORAMA** (Radboud, cited by PanTS as the largest prior public
pancreas dataset) is the first candidate; note our manifest already contains `National Institutes of
Health` (97) and `IRCAD` (173), so those sources are likely absorbed too.

## ACTION ITEMS
- [ ] Compute **T-Sen** (tumor-wise sensitivity, per-lesion CC matching) — fills their benchmark row
- [ ] Build the autonomous cascade to submission quality (**precondition for everything above**)
- [ ] Package: checkpoint + testing script + in-distribution results + README (we already have the
      in-distribution results: DSC 0.474, P-Sen 96%, Spe 17%, AUC 0.804 on the official 901)
- [ ] Email Dr. Zhou — **but only once the autonomous number is real.** One shot at a first impression.
- [ ] Run the overlap protocol on PANORAMA before proposing it

---

# ★★★ PANORAMA — OVERLAP PROTOCOL **PASSED**. This is the tumor source. (2026-08-02)

First candidate run through the protocol established by the MSD Task07 failure. **It passes** — with
one known, quantified, removable contamination and one residual ambiguity we must disclose.

## What PANORAMA is
[PANORAMA Challenge](https://panorama.grand-challenge.org/) — Radboud UMC + UMC Groningen, PDAC
detection, EU Horizon 2020 PANCAIM funded, published in *Lancet Oncology* (2025).

| property | value |
|---|---|
| public training + development set | **2,238 CECT scans** |
| **PDAC-positive cases** | **676** |
| of those, **expert-manual** lesion delineations | **482** (remainder AI-generated) |
| centers (study) | Radboud UMC, UMC Groningen, Ziekenhuis Groep Twente (NL), Karolinska (SE), Haukeland (NO) |
| modality | **portal-venous CECT only** |
| license | **CC BY-NC 4.0** (non-commercial — compatible with PanTS's non-commercial terms) |
| download | 4 Zenodo batches, batch 1 = 49.3 GB → **~200 GB total** |
| labels | live repo `github.com/DIAGNijmegen/panorama_labels` |
| reference standard | histopathology, or CT + **≥36-month** follow-up |
| extra structures | pancreas parenchyma, pancreatic duct, veins, arteries, common bile duct |

## Overlap protocol — results

**Step 1 — institution names vs our `site detail` column:**

| term | rows mentioning it | as a **single-institution** site |
|---|---:|---:|
| Radboud | 533 | **0** |
| Groningen | 0 | **0** |
| Nijmegen | 64 | **0** |
| Netherlands | 0 | **0** |
| `site nationality` exactly `NL` | — | **0** |

**PanTS Mini contains no single-institution Dutch cases.** Every mention of Radboud sits inside a
multi-center aggregate provenance string (the 411 / 64 / 58 groups), i.e. cases inherited from a
pooled public collection where per-case origin is not recorded.

**Step 2 — self-declared contamination (the honest part, stated by PANORAMA itself):**
> *"Includes **194 cases from the Medical Segmentation Decathlon** dataset and **80 cases from
> National Institutes of Health**"* — and of the MSD 194, **98 are PDAC**.

Cross-checked against our manifest: PanTS contains **966** single-institution MSKCC cases (the MSD
Task07 donor) and **97** NIH cases. **So those 274 PANORAMA cases are the ones already inside PanTS.**

**Step 3 — the clean remainder:**

| | cases | PDAC |
|---|---:|---:|
| PANORAMA public total | 2,238 | 676 |
| − MSD contribution (already in PanTS) | −194 | −98 |
| − NIH contribution (already in PanTS) | −80 | −0 (all non-PDAC) |
| **= usable, non-overlapping** | **1,964** | **578** |

## ★ THE HEADLINE: +578 tumors, an **82% increase**

We have **706** tumor-positive training cases and **zero** unused. PANORAMA's clean remainder adds
**578 new tumor-positive scans** — plus ~1,386 clean negatives with a **36-month follow-up** negative
standard that is *stronger than PanTS's mask-absence definition*.

**706 → 1,284 tumor-positive cases.** Given that data scale is the one lever that ever moved lesion
Dice (EXP-17: +0.05 from tripling tumors), this is the single highest-expected-value action available
to the capstone.

## ⚠ Caveats that MUST be disclosed
1. **PDAC only.** PanTS covers PDAC + IPMN + PNET. Adding PANORAMA shifts the tumor-type distribution
   toward PDAC. Report per-type performance if PanTS metadata supports it; expect PDAC to improve
   more than the rest, and say so.
2. **Pancreas masks are AI-generated** (Alves et al. algorithm), not expert. Our whole-box recipe
   crops to the pancreas — so on PANORAMA we would be cropping to a *silver-standard* organ mask.
   Pancreas-Dice claims on PANORAMA are therefore weaker than on PanTS. Lesion labels for 482/676
   PDAC are genuinely expert; **prefer those 482 for training.**
3. **Different label convention** — PANORAMA: `1=PDAC, 2=veins, 3=arteries, 4=pancreas parenchyma,
   5=duct, 6=CBD`. Ours: `1=pancreas, 2=lesion`. Remap is trivial but **must be config-driven**, and
   getting it backwards would silently poison training. Write a unit test.
4. **Portal-venous only.** EXP-14 showed contrast phase is the strongest driver of our specificity
   behaviour (non-contrast 90% vs PV 10%). Adding 1,964 PV scans will **push the model toward the
   over-firing regime.** This is predictable and must be pre-registered, not discovered.
5. **Residual overlap risk, unresolvable:** 533 PanTS cases carry "Radboud" somewhere in a pooled
   provenance string. We cannot rule out that a handful are physically PANORAMA-cohort scans without
   case-level identifiers. **State this in the writeup rather than claiming zero overlap.**
6. **~200 GB download.** The external drive currently has 83 GB free. Storage plan required first
   (see the storage section — the warm-cache design makes this tractable, the raw archive does not).
7. **Live labels repo** — annotations can change. **Pin a commit hash** and record it, or results
   become irreproducible.

## ✅ BONUS: a second independent external evaluation
PANORAMA runs its own Grand Challenge leaderboard with a **hidden validation cohort (86)** and a
**hidden testing cohort (>400)** — the latter including *"external testing data (unseen cases from an
unseen center)"*, scored against histopathology.

**So there are now two independent external evaluation routes:**

| route | held-out scale | what it proves |
|---|---:|---|
| **JHU PanTS email submission** | 26,489 (UCSF / Poland / Peking / RSNA) | generalization across 3 continents, JHU-re-annotated |
| **PANORAMA Grand Challenge** | ~486 hidden, incl. unseen center | performance vs **radiologists**, histopathology-confirmed |

Both are open. Either alone justifies the autonomous cascade; together they make it unarguable.

## Verdict
**ADOPT PANORAMA — as a source of tumors, not as a validation set.** Leave-one-site-out inside PanTS
and the two external services cover validation better. PANORAMA's unique contribution is **578 new
tumor-positive scans with a histopathology/36-month-follow-up reference standard.**

**Before it enters the proposal as committed scope:**
- [ ] resolve storage (~200 GB) against the warm-cache plan
- [ ] pin the labels repo commit
- [ ] write + unit-test the label remap (`1=PDAC → our 2=lesion`; `4=parenchyma → our 1=pancreas`)
- [ ] build the exclusion list for the 274 MSD/NIH cases **and assert it at load time**, same guard
      pattern as the leakage abort in `train.py`
- [ ] pre-register the expected specificity regression from PV-only data

---

# ✅ PANORAMA DEDUPLICATION — **VERIFIED AGAINST THE REAL FILE** (2026-08-15)

Answers the two review comments: *"This is a hypothesis. Can you provide evidence that this will
work?"* and *"Or methods to validate?"*

**It is not a hypothesis. PANORAMA ships a column that names the imported cases.**

Source: `clinical_information.xlsx` from `github.com/DIAGNijmegen/panorama_labels` (note: the repo
README calls it `.csv`; the actual file is `.xlsx`). 2,238 rows x 8 columns:
`PANORAMA_patient_id, PANORAMA_study_id, anonymized_study_date, patient_age, patient_sex, scanner,
label, level`.

The **`level`** column records the reference standard — and for imported cases it records the source
dataset by name:

| level | n |
|---|---:|
| radiology | 1,212 |
| histopathology | 353 |
| pathology | 210 |
| **MSD_dataset** | **194** |
| cytology | 183 |
| **NIH_dataset** | **80** |
| radiology / 3yFU | 6 |

## The exclusion, verified

| | cases | PDAC |
|---|---:|---:|
| PANORAMA public set | 2,238 | 676 |
| less `level == MSD_dataset` | −194 | −98 |
| less `level == NIH_dataset` | −80 | −0 |
| **usable, non-overlapping** | **1,964** | **578** |

**Our documentation-derived estimate was 1,964 / 578. The file confirms it exactly.**
Cross-check: the README states *"80 patients without PDAC from NIH and 194 patients (98 PDAC) from
MSD"* — the file gives MSD_dataset = 98 PDAC / 96 non-PDAC and NIH_dataset = 0 PDAC / 80 non-PDAC.
Consistent on every figure.

**Implementation is one line**, with a load-time assertion:
```python
IMPORTS = {"MSD_dataset", "NIH_dataset"}
clean = df[~df.level.isin(IMPORTS)]
assert len(clean) == 1964 and (clean.label == "PDAC").sum() == 578
```

## ★ SECOND FINDING — split by patient, not study
`2,238` studies but only **`2,224` unique patients**. **11 patients contribute 14 studies.**
Splitting on `PANORAMA_study_id` would place the same patient on both sides of a fold — the exact
leakage class that cost us 0.11 lesion Dice in the preceding project. **Group by
`PANORAMA_patient_id`.** (Note this differs from PanTS, where each scan is its own patient.)
Repeat patients: 13 histopathology-confirmed (6 PDAC), 12 radiology-confirmed.

## Clean cohort profile (n=1,964)
- reference standard: radiology 1,212 · histopathology 353 · pathology 210 · cytology 183 ·
  radiology+3-year-follow-up 6 → **746 of 1,964 (38%) have tissue confirmation**
- age median 67, range 18–99, **zero missing**
- sex 1,064 M / 900 F
- scanners: Siemens 938, Toshiba 651, Philips 319, GE 46, Canon 7 — **the same four manufacturers
  present in PanTS**, which supports the transfer argument

## Residual risk, still disclosed
The `level` column resolves the *declared* imports. It cannot rule out undeclared duplicates —
notably the 533 PanTS records carrying "Radboud" inside a pooled multi-institution provenance string.
The pixel-level duplicate detector (32³ downsample + hash, recall measured on planted duplicates)
remains the answer for that, and stays a Week 3 deliverable.

## Still to verify (needs the label masks, not just the spreadsheet)
- [ ] `ls manual_labels | wc -l` = 482 and `ls automatic_labels | wc -l` = 194
- [ ] label values read from an actual mask match the documented legend (1=PDAC … 4=parenchyma)
- [ ] filename convention maps to `PANORAMA_study_id`

---

# DATA USE, LICENSING, AND ATTRIBUTION (recorded 2026-08-15)

Both datasets are **non-commercial** license. Compatible with each other and with an academic
capstone; incompatible with any commercial deployment. State this plainly in the proposal.

| dataset | license | source |
|---|---|---|
| PanTS (9,901 public training scans) | non-commercial | Johns Hopkins, `github.com/MrGiovanni/PanTS` |
| PANORAMA public training and development set | **CC BY-NC 4.0** | Zenodo, 4 imaging batches + labels repo |

## Required citations

**PANORAMA — required by the labels repository:**
> Alves, N., Schuurmans, M., Rutkowski, D., Yakar, D., Haldorsen, I., Liedenbaum, M., Molven, A.,
> Vendittelli, P., Litjens, G., Hermans, J., & Huisman, H. (2024). *The PANORAMA Study Protocol:
> Pancreatic Cancer Diagnosis — Radiologists Meet AI.* Zenodo. https://doi.org/10.5281/zenodo.10599559

**PanTS:**
> Li, W., Zhou, X., Chen, Q., Lin, T., Bassi, P.R.A.S., et al., Yuille, A.L., & Zhou, Z. (2025).
> *PanTS: The Pancreatic Tumor Segmentation Dataset.* NeurIPS 2025 Datasets and Benchmarks Track.
> arXiv:2507.01291

**SuPreM** (the pretrained checkpoint being fine-tuned): arXiv:2501.11253

**Alves et al. (2021/2022)** — the algorithm that generated PANORAMA's automatic organ and lesion
masks. Must be cited whenever we describe that provenance. PMID 35053538.

**Medical Segmentation Decathlon** — cite if Task07 is discussed:
> Antonelli, M., Reinke, A., Bakas, S., et al. (2022). *The Medical Segmentation Decathlon.*
> Nature Communications. doi:10.1038/s41467-022-30695-9 · also Simpson et al., arXiv:1902.09063

**Suman et al. (2021)** — source of the PDAC vs non-PDAC split within the MSD import. PMID 33840636.
Cite only if we rely on that distinction.

## Compliance notes
- Non-commercial licensing means the system **cannot be commercialized** as built. Consistent with the
  no-clinical-claims guardrail; worth one sentence in the proposal so a reviewer does not have to ask.
- The PANORAMA labels repository is **live and mutable**. Pin the commit hash and record it, or
  results are not reproducible.
- The repo README refers to `clinical_information.csv`; the actual file is `clinical_information.xlsx`.
  Minor upstream documentation error — worth reporting alongside any issue we file.

---

# ✅ PANORAMA — FULLY VERIFIED AGAINST REAL FILES (2026-08-15)

Every claim below checked against `panorama_labels-main.zip` and `clinical_information.xlsx`.
Nothing here rests on documentation.

## File reconciliation — exact
| | observed | documented |
|---|---:|---:|
| `manual_labels/` | **482** | 482 |
| `automatic_labels/` | **1,756** | — |
| total | **2,238** | 2,238 spreadsheet rows ✓ |

Decomposes exactly: 676 PDAC = 482 manual + 194 automatic; 1,562 non-PDAC all automatic;
194 + 1,562 = 1,756. One label file per case, none missing or duplicated.

## Join key
Filenames are `PANORAMA_study_id` verbatim (`100002_00001.nii.gz`). The exclusion list applies
directly to files — **no ID mapping layer needed.**

## Label legend — read from a real mask
`manual_labels/100002_00001.nii.gz`, shape 512x512x561, spacing 0.709 x 0.709 x 1.0 mm.
All seven documented values present: 0 background, 1 PDAC, 2 veins, 3 arteries, 4 parenchyma,
5 duct, 6 common bile duct. **Remap verified against data.**

Note the geometry: finer in-plane than the PanTS median, long z-extent. Resampling to 1.5 mm changes
PANORAMA volumes more than it changes PanTS volumes.

## ★ CORRECTED — annotation quality after exclusion
**Earlier estimate of 482 expert-annotated PDAC was WRONG. The real figure is 382.**

| | cases |
|---|---:|
| usable PDAC after exclusion | 578 |
| **...expert manual delineation** | **382** |
| ...machine-generated | 196 |

**Cause:** 97 of the 98 Decathlon PDAC cases carry **manual** masks — PANORAMA re-delineated them
rather than inheriting the original labels. So the excluded cases are disproportionately the
best-annotated ones. **The exclusion costs 97 gold-standard tumors.**

Manual masks by source (all 482): MSD 97 · histopathology 171 · pathology 109 · cytology 85 ·
radiology 20 · NIH 0.

**Revised lever size:** 706 current tumors -> **1,088** with the expert subset = **+54%**
(not the +82% implied by the raw 578 figure). Still the largest single lever and still the only
route to more tumors.

**Design consequence (now evidence-backed, not principle):** train on the 382 expert cases first;
treat the 196 machine-annotated as a **labeled ablation arm**, never folded in silently.

**Shortcut to refuse:** keeping the Decathlon cases would recover 97 expert tumors, but those scans
sit in PanTS `val.txt` (198 MSKCC) and the official test split (195 MSKCC). Training on them
contaminates our own evaluation — the same trade that produced the withdrawn 0.528.

## Minor anomalies (documented, not blocking)
- **3 non-PDAC cases carry manual masks** (2 histopathology, 1 radiology) though the README says
  manual delineation was PDAC-only. Likely non-PDAC lesions outlined anyway.
- **1 of 98 Decathlon PDAC cases has no manual mask.** Their split is not perfectly clean either.
