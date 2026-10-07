# Technical Appendix

**Autonomous Pancreatic Lesion Detection and Radiologist Review System**
Supplement to the BSAAI Capstone Proposal — Quinn Evans

This appendix documents the system design behind the proposal. It is included so a reviewer can
assess whether the architecture has been thought through, not only whether the technologies have been
named. Every quantity given here was measured against the real dataset or taken from published
documentation; estimates are labeled as such.

---

## A1. System architecture

The project consists of two systems that meet at a shared data layer. The imaging pipeline produces
structured findings; those findings become the retrieval context for the knowledge assistant. Neither
system calls the other directly.

<svg width="100%" viewBox="0 0 700 340" xmlns="http://www.w3.org/2000/svg" font-family="Carlito, sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="#5f5e5a" stroke-width="1.5" stroke-linecap="round"/></marker></defs>
<rect x="40" y="30" width="280" height="54" rx="8" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
<text x="180" y="52" text-anchor="middle" font-size="13" font-weight="600" fill="#04342c">Imaging pipeline</text>
<text x="180" y="70" text-anchor="middle" font-size="11" fill="#0f6e56">localize, segment, measure, score</text>
<rect x="380" y="30" width="280" height="54" rx="8" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
<text x="520" y="52" text-anchor="middle" font-size="13" font-weight="600" fill="#042c53">Knowledge assistant</text>
<text x="520" y="70" text-anchor="middle" font-size="11" fill="#185fa5">retrieve, ground, cite or refuse</text>
<line x1="180" y1="92" x2="180" y2="142" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar)"/>
<line x1="520" y1="142" x2="520" y2="92" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar)"/>
<rect x="40" y="150" width="620" height="130" rx="12" fill="none" stroke="#b9c0c7" stroke-width="0.8" stroke-dasharray="4 4"/>
<text x="60" y="174" font-size="12" font-weight="600" fill="#14171a">Shared data layer — PostgreSQL with pgvector</text>
<rect x="60" y="190" width="185" height="52" rx="6" fill="#f4f6f8" stroke="#b9c0c7" stroke-width="0.8"/>
<text x="152" y="210" text-anchor="middle" font-size="12" font-weight="600" fill="#14171a">Relational</text>
<text x="152" y="228" text-anchor="middle" font-size="10.5" fill="#5f5e5a">cohorts, findings, reviews</text>
<rect x="257" y="190" width="185" height="52" rx="6" fill="#f4f6f8" stroke="#b9c0c7" stroke-width="0.8"/>
<text x="349" y="210" text-anchor="middle" font-size="12" font-weight="600" fill="#14171a">Vector</text>
<text x="349" y="228" text-anchor="middle" font-size="10.5" fill="#5f5e5a">embedded literature</text>
<rect x="454" y="190" width="186" height="52" rx="6" fill="#f4f6f8" stroke="#b9c0c7" stroke-width="0.8"/>
<text x="547" y="210" text-anchor="middle" font-size="12" font-weight="600" fill="#14171a">Object storage</text>
<text x="547" y="228" text-anchor="middle" font-size="10.5" fill="#5f5e5a">volumes and masks on disk</text>
<text x="350" y="264" text-anchor="middle" font-size="10.5" fill="#5f5e5a">Findings written by the pipeline become the query the assistant retrieves against</text>
</svg>

---

## A2. End-to-end data flow

The following is the complete path a scan takes. Steps 2 through 5 are the autonomous cascade that
this capstone builds; today step 2 is replaced by a human-provided region of interest.

<svg width="100%" viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" font-family="Carlito, sans-serif">
<defs><marker id="ar2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="#5f5e5a" stroke-width="1.5" stroke-linecap="round"/></marker></defs>
<rect x="20" y="30" width="150" height="56" rx="6" fill="#f4f6f8" stroke="#b9c0c7" stroke-width="0.8"/>
<text x="95" y="50" text-anchor="middle" font-size="11.5" font-weight="600" fill="#14171a">1. Scan arrives</text>
<text x="95" y="66" text-anchor="middle" font-size="10" fill="#5f5e5a">watch folder or POST</text>
<text x="95" y="79" text-anchor="middle" font-size="10" fill="#5f5e5a">triggers the pipeline</text>
<rect x="196" y="30" width="150" height="56" rx="6" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
<text x="271" y="50" text-anchor="middle" font-size="11.5" font-weight="600" fill="#04342c">2. Localize</text>
<text x="271" y="66" text-anchor="middle" font-size="10" fill="#0f6e56">full volume at 1.5 mm,</text>
<text x="271" y="79" text-anchor="middle" font-size="10" fill="#0f6e56">predicted pancreas box</text>
<rect x="372" y="30" width="150" height="56" rx="6" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
<text x="447" y="50" text-anchor="middle" font-size="11.5" font-weight="600" fill="#04342c">3. Crop</text>
<text x="447" y="66" text-anchor="middle" font-size="10" fill="#0f6e56">box plus 16 voxels,</text>
<text x="447" y="79" text-anchor="middle" font-size="10" fill="#0f6e56">resize to 128 cubed</text>
<rect x="548" y="30" width="132" height="56" rx="6" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
<text x="614" y="50" text-anchor="middle" font-size="11.5" font-weight="600" fill="#04342c">4. Segment</text>
<text x="614" y="66" text-anchor="middle" font-size="10" fill="#0f6e56">SegResNet, three</text>
<text x="614" y="79" text-anchor="middle" font-size="10" fill="#0f6e56">class output</text>
<line x1="176" y1="58" x2="190" y2="58" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<line x1="352" y1="58" x2="366" y2="58" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<line x1="528" y1="58" x2="542" y2="58" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<path d="M614 92 L614 110 L95 110 L95 128" fill="none" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<rect x="20" y="136" width="150" height="56" rx="6" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
<text x="95" y="156" text-anchor="middle" font-size="11.5" font-weight="600" fill="#04342c">5. Gate and measure</text>
<text x="95" y="172" text-anchor="middle" font-size="10" fill="#0f6e56">volume, diameter,</text>
<text x="95" y="185" text-anchor="middle" font-size="10" fill="#0f6e56">subregion, suspicion</text>
<rect x="196" y="136" width="150" height="56" rx="6" fill="#f4f6f8" stroke="#b9c0c7" stroke-width="0.8"/>
<text x="271" y="156" text-anchor="middle" font-size="11.5" font-weight="600" fill="#14171a">6. Persist</text>
<text x="271" y="172" text-anchor="middle" font-size="10" fill="#5f5e5a">finding row in Postgres,</text>
<text x="271" y="185" text-anchor="middle" font-size="10" fill="#5f5e5a">mask file on disk</text>
<rect x="372" y="136" width="150" height="56" rx="6" fill="#f4f6f8" stroke="#b9c0c7" stroke-width="0.8"/>
<text x="447" y="156" text-anchor="middle" font-size="11.5" font-weight="600" fill="#14171a">7. Worklist</text>
<text x="447" y="172" text-anchor="middle" font-size="10" fill="#5f5e5a">queue ordered by</text>
<text x="447" y="185" text-anchor="middle" font-size="10" fill="#5f5e5a">suspicion score</text>
<rect x="548" y="136" width="132" height="56" rx="6" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
<text x="614" y="156" text-anchor="middle" font-size="11.5" font-weight="600" fill="#042c53">8. Review</text>
<text x="614" y="172" text-anchor="middle" font-size="10" fill="#185fa5">overlay, assistant,</text>
<text x="614" y="185" text-anchor="middle" font-size="10" fill="#185fa5">accept edit reject</text>
<line x1="176" y1="164" x2="190" y2="164" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<line x1="352" y1="164" x2="366" y2="164" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<line x1="528" y1="164" x2="542" y2="164" stroke="#5f5e5a" stroke-width="1.2" marker-end="url(#ar2)"/>
<path d="M614 198 L614 218 L271 218 L271 200" fill="none" stroke="#5f5e5a" stroke-width="1.2" stroke-dasharray="3 3" marker-end="url(#ar2)"/>
<text x="440" y="234" text-anchor="middle" font-size="10" fill="#5f5e5a">reviewer decisions return to the database as a corrections record</text>
</svg>

**Measured inference cost.** A full CT resampled to 1.5 mm isotropic is a median of 253 × 190 × 142
voxels — 6.9 million voxels, 26.5 MiB as float32, computed across all 9,901 scans in the dataset.
Sliding-window localization at 128³ with 50 percent overlap requires a median of 12 windows per scan.
Against the current serving time of roughly 0.6 seconds for the provided-region path, autonomous
whole-scan inference is expected to land in the range of several seconds per study.

---

## A3. Relational schema

Abbreviated to the tables that carry the design decisions. The full schema adds audit columns and
indexes.

```sql
-- Storage roots are configuration, never absolute paths in data.
CREATE TABLE storage_root (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,      -- 'cold_archive', 'warm_cache'
    tier         TEXT NOT NULL CHECK (tier IN ('cold','warm','cloud'))
);

CREATE TABLE scan (
    id              BIGSERIAL PRIMARY KEY,
    case_id         TEXT NOT NULL,
    source_dataset  TEXT NOT NULL,          -- 'pants' | 'panorama'
    shape           INT[3] NOT NULL,
    spacing         REAL[3] NOT NULL,
    contrast_phase  TEXT,
    manufacturer    TEXT,
    site            TEXT,
    UNIQUE (source_dataset, case_id)
);

-- Provenance is data, not an assumption. PANORAMA organ masks are machine
-- generated; PanTS masks are expert validated. The model must know which.
CREATE TABLE annotation (
    id              BIGSERIAL PRIMARY KEY,
    scan_id         BIGINT NOT NULL REFERENCES scan(id),
    structure       TEXT NOT NULL,          -- 'pancreas' | 'lesion' | ...
    provenance      TEXT NOT NULL CHECK (provenance IN ('expert','automated')),
    volume_mm3      DOUBLE PRECISION
);

CREATE TABLE scan_file (
    id              BIGSERIAL PRIMARY KEY,
    scan_id         BIGINT NOT NULL REFERENCES scan(id),
    storage_root_id INT NOT NULL REFERENCES storage_root(id),
    relative_path   TEXT NOT NULL,
    bytes           BIGINT,
    sha256          CHAR(64),
    verified_at     TIMESTAMPTZ
);

-- A cohort is a materialized query, not a text file. This is the control that
-- makes the validation leak found in the preceding project inexpressible.
CREATE TABLE cohort (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    definition    TEXT NOT NULL,            -- the SQL that produced it
    parent_fold   TEXT,                     -- 'train' | 'val' | 'test'
    frozen_at     TIMESTAMPTZ
);

CREATE TABLE cohort_member (
    cohort_id  INT    NOT NULL REFERENCES cohort(id),
    scan_id    BIGINT NOT NULL REFERENCES scan(id),
    PRIMARY KEY (cohort_id, scan_id)
);

-- Enforced at write time: a scan may never appear in a training cohort and an
-- evaluation cohort simultaneously.
CREATE OR REPLACE FUNCTION assert_cohort_disjoint() RETURNS TRIGGER AS $$
BEGIN
  IF EXISTS (
      SELECT 1 FROM cohort_member cm
      JOIN cohort c   ON c.id  = cm.cohort_id
      JOIN cohort nc  ON nc.id = NEW.cohort_id
      WHERE cm.scan_id = NEW.scan_id
        AND c.parent_fold IS DISTINCT FROM nc.parent_fold
  ) THEN
      RAISE EXCEPTION 'scan % would cross folds', NEW.scan_id;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TABLE prediction (
    id              BIGSERIAL PRIMARY KEY,
    scan_id         BIGINT NOT NULL REFERENCES scan(id),
    model_version   TEXT NOT NULL,
    lesion_volume_mm3 DOUBLE PRECISION,
    max_diameter_mm   DOUBLE PRECISION,
    subregion         TEXT,
    suspicion_score   DOUBLE PRECISION,     -- drives worklist ordering
    mask_file_id      BIGINT REFERENCES scan_file(id),
    UNIQUE (scan_id, model_version)
);

CREATE TABLE review (
    id             BIGSERIAL PRIMARY KEY,
    prediction_id  BIGINT NOT NULL REFERENCES prediction(id),
    decision       TEXT NOT NULL CHECK (decision IN ('accept','edit','reject')),
    reviewer       TEXT NOT NULL,
    decided_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    note           TEXT
);

-- Literature chunks share the database with the imaging metadata, so a single
-- query can combine semantic similarity with structured filters.
CREATE TABLE doc_chunk (
    id         BIGSERIAL PRIMARY KEY,
    pmid       TEXT NOT NULL,
    title      TEXT,
    journal    TEXT,
    year       INT,
    chunk_text TEXT NOT NULL,
    embedding  VECTOR(768)
);
CREATE INDEX ON doc_chunk USING hnsw (embedding vector_cosine_ops);
```

**Why this matters.** In the preceding project, cohort membership lived in text files, and a script
sampled from the wrong column. The result was 266 evaluation cases inside the training set and a
headline lesion Dice inflated from 0.415 to 0.528. That number had to be withdrawn. Expressing
membership as a constrained relation makes the same mistake impossible to commit rather than merely
possible to detect.

---

## A4. Cross-source integration

PanTS and PANORAMA describe the same anatomy under incompatible conventions.

| | PanTS | PANORAMA |
|---|---|---|
| label values | 1 = pancreas, 2 = lesion | 1 = PDAC, 2 = veins, 3 = arteries, 4 = parenchyma, 5 = duct, 6 = bile duct |
| lesion annotation | expert validated | 482 expert, 194 automated |
| organ annotation | expert validated | automated throughout |
| negative standard | no lesion mask present | histopathology or 36 month follow-up |
| tumor types | PDAC, IPMN, PNET | PDAC only |
| contrast phase | four phases | portal venous only |

**Deduplication.** PANORAMA states that its public set includes 194 Medical Segmentation Decathlon
cases and 80 NIH cases. Those sources are already inside PanTS, which contains 966 single-institution
Memorial Sloan Kettering cases and 97 NIH cases. The overlap was confirmed by two independent signals:
institution matching against the site metadata, and a tumor-volume distribution fingerprint — PanTS
and the Decathlon share a single 732 cm³ tumor, an outlier neither dataset has twice.

| | cases | tumor positive |
|---|---:|---:|
| PANORAMA public set | 2,238 | 676 |
| less Decathlon contribution | −194 | −98 |
| less NIH contribution | −80 | 0 |
| **usable, non-overlapping** | **1,964** | **578** |

**Why this is load-bearing.** The training fold contains 706 tumor-positive scans and the preceding
project already used all 706. Scaling within PanTS therefore adds only healthy scans, which was tested
and rejected — specificity rose from 17 to 46 percent but detection fell from 96 to 88 percent, below
the pre-registered floor. PANORAMA is the only available source of additional tumors, and the merge
cannot proceed safely until deduplication and remapping are correct.

**Residual risk, disclosed.** 533 PanTS records name Radboud inside a pooled multi-institution
provenance string. No single-institution Dutch case exists in PanTS, but without case-level
identifiers a small overlap cannot be fully excluded. This will be stated in the results rather than
claimed away.

---

## A5. Storage tiers and compute

Measured across all 9,901 PanTS scans: 297.5 billion voxels total.

| tier | contents | size | location |
|---|---|---:|---|
| cold | original compressed volumes, both datasets | **582 GB** | external drive, checksummed, never read during training |
| warm | preprocessed 128³ arrays, 10.0 MiB per case | **25 GiB** for the merged training cohort | internal SSD or cloud volume |
| index | metadata, cohorts, findings, embeddings | ~1–2 GB | PostgreSQL |

Uncompressed, the imaging archive would occupy 831 GB, and storing all 28 annotated structures as
separate full volumes would require 8.1 TB. Neither is necessary: training reads only the warm tier.

**Consequence for compute.** Moving training to a rented GPU requires uploading 25 GiB once, not
582 GB. Three controls preserve comparability with existing results: numerical precision stays at
fp32, the baseline is re-established on the new hardware before any comparison is drawn, and
on-demand rather than preemptible instances are used until checkpoint resume is verified end to end.

---

## A6. Knowledge assistant

**Corpus.** PubMed abstracts and the PMC Open Access subset, filtered by MeSH terms covering
pancreatic neoplasms and computed tomography. Estimated 30,000–80,000 articles yielding roughly
300,000–500,000 chunks; both figures to be confirmed at build time. The snapshot is pinned by date
and query, because a corpus that changes underneath the system makes retrieval metrics from week 6
incomparable to week 10.

**Pipeline.**

| stage | specification |
|---|---|
| chunking | approximately 512 tokens, 64 token overlap, section boundaries respected |
| embedding | sentence-transformer; pre-registered comparison of a general model (384 dimensions) against a biomedical model (768 dimensions) |
| index | pgvector HNSW, cosine distance, parameters tuned against a held-out question set |
| retrieval | top-k passages, filtered by structured predicates in the same SQL query |
| generation | Qwen instruct via Ollama, temperature 0, executed locally |

**Query construction.** The assistant is not a free-text chatbot. A query is templated from the
finding row the pipeline just wrote:

```
finding: lesion 2.4 cm maximum diameter, 5.3 cm³, pancreatic head,
         portal venous phase, organ volume 77 cm³
question: <clinician question>
retrieve: top-k chunks WHERE embedding <=> query_embedding
          AND year >= 2010
```

**Cite or refuse.** The system prompt permits only statements supported by the retrieved passages,
each rendered in the interface beside the text it supports. If the best retrieval score falls below a
calibrated threshold, the assistant returns a refusal rather than generating. This is a testable
property, and it is what keeps a literature-lookup tool from becoming unlicensed clinical advice.

**Evaluation.** Retrieval is scored with recall@k and mean reciprocal rank against a hand-authored
question set with known-relevant documents. Generation is scored by groundedness rate — the fraction
of generated claims traceable to a retrieved passage — and by refusal accuracy on questions
deliberately outside the corpus.

---

## A7. Risks and fallbacks

| risk | likelihood | response |
|---|---|---|
| The Week 4 experiment returns null — added tumors do not improve lesion Dice | Moderate | Reported as a null result and the baseline cohort is retained. The integration work stands on its own as the data engineering deliverable; the pipeline and gate are unaffected. |
| The autonomous cascade loses significant accuracy against the provided-region baseline | Moderate | Both numbers are reported side by side, which is the honest comparison in any case. Prior work measured 98 percent tumor coverage from the predicted region, so a total failure is unlikely. |
| Johns Hopkins does not respond to the external submission | Likely enough to plan for | The submission is a stretch goal outside the critical path. Two alternative external validations remain: leave-one-institution-out across six sites within PanTS, and the PANORAMA challenge's own hidden test cohort. |
| Specificity cannot be raised without breaching the 96 percent detection floor | Moderate | Report the full operating-point curve rather than a single threshold, and state plainly which trade-offs are available. A prior experiment already established that this axis is movable and located the cost in small tumors. |
| PANORAMA download or licensing proves impractical | Low | CC BY-NC 4.0 is confirmed and the data is on Zenodo. If it fails, the project continues on PanTS alone with a reduced Week 4 scope. |
| Assistant produces an ungrounded clinical statement | Low, and gated | Cite-or-refuse is enforced at generation, not by disclaimer, and refusal accuracy is measured. Any ungrounded output reaching the interface is treated as a defect, not a tuning issue. |
| Training throughput on local hardware is insufficient | Moderate | The warm cache makes cloud GPU a 25 GiB upload. A profiling pass in Week 1 determines whether the bottleneck is compute or input/output before any money is spent. |
| Scope overruns across two systems | Moderate | Each pillar carries a committed minimum and an optional stronger version, so a difficult week costs sophistication rather than a component. |

---

## A8. What already exists

The following is complete and working before Week 1, and is the foundation the capstone builds on.

- A registered model in MLflow with version, step, and checksum, trained by transfer learning from the
  SuPreM pretrained checkpoint.
- Evaluation on the official 901-scan held-out test set: lesion Dice 0.474 with a 95 percent
  confidence interval of 0.42 to 0.52, pancreas Dice 0.827, detection sensitivity 96 percent,
  specificity 17 percent, patient-level AUC 0.804. These are provided-region results, and are reported
  as such.
- A FastAPI inference service and a React and NiiVue review interface with prediction overlays and 3D
  reconstruction.
- Twenty-seven pre-registered experiments with recorded accept or reject decisions, including two
  rejections and one withdrawn result.
- A localize-then-segment cascade that runs end to end and has been measured once at 98 percent tumor
  coverage from the predicted region.
- Two independent adversarial code audits, one of which found the validation leak described in A3.

The capstone is not a rebuild. It removes the system's central assumption, adds a second data source
and a second AI system, and replaces convention with enforcement in the data layer.
