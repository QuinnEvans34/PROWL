# Plan 07 lane scope: the PROWL evidence system

**Status:** Planning set v4, **approved by Quinton on 2026-09-28** (groups A and B of section 12).
Execution permissions (group C) are not granted. Not an implementation,
download, install or model authorization.
**Owner / decider:** Quinton Evans. **Lane implementer:** Claude. **Reviewer and shared-document
owner:** Codex.
**Companion:** [`PHASES.md`](PHASES.md). **Revision history:** [`RUNNING-LOG.md`](RUNNING-LOG.md).
**Governing records:**
- [`../../implementation/07-literature-retrieval.md`](../../implementation/07-literature-retrieval.md)
  and the six design files in [`../`](../);
- **D-260**: [`../../operations/POSTGRES-PGVECTOR-DECISION-2026-09-28.md`](../../operations/POSTGRES-PGVECTOR-DECISION-2026-09-28.md).

This document narrows that design to exactly what *we* will do. It never edits a shared record;
where a change is needed, it proposes one to Codex (section 10).

## How to read status labels

| Label | Meaning |
|---|---|
| **APPROVED (D-xxx)** | Recorded in `docs/capstone/DECISIONS.md` |
| **APPROVED (Quinton, Claude discussion 2026-09-28)** | Quinton decided in the planning conversation with Claude. Not yet in `DECISIONS.md`; the integration owner (Codex) needs Quinton's confirmation to record it |
| **PROPOSED** | Claude's recommendation. Not binding until approved |
| **OPEN** | Not decided. A named phase or piece of evidence settles it |
| **RECONCILIATION NEEDED** | A shared document's text conflicts. Codex updates it after approval |

## 1. What we are building

A local, reproducible evidence system for the reviewer workflow. A reviewer looking at a proposed
pancreas or lesion contour asks a bounded, non-diagnostic question. The system:

1. validates a query built from an allowlisted, non-identifying structured finding plus the
   question (D-075);
2. retrieves passages from a frozen, rights-reviewed corpus through keyword, vector and hybrid
   retrieval in PostgreSQL + pgvector (D-260);
3. checks evidence sufficiency before any language model runs; and
4. returns claims tied to exact retrieved passages, or an explicit refusal. The extractive
   ranked-passage view is the safe fallback (D-013, D-086).

Measured by:
- recall@1/3/5/10 and MRR (D-085);
- groundedness, citation support and refusal accuracy (D-087);
- latency and resource use.

It serves the proposal's **relational and vector data storage** and **evidence-grounded applied
AI** commitments. It never blocks imaging (D-073) and never touches patient data (D-075).

## 2. Lane decision register

| ID | Decision | Status | Rationale / notes |
|---|---|---|---|
| L-01 | Tier 1 is the committed, focused, frozen, rights-reviewed, **graded** corpus feeding the reviewer UI (D-074 scope) | APPROVED (D-260 restates Tier 1; D-074) | Codex D2 |
| L-02 | Tier 2 (broad research library) is a separately approved extension: own budget, IDs and evaluation; never a product answer; never Weeks 9-10; starts from a bounded broader sample | APPROVED (D-260: Tier 2 needs separate scope approval) | Codex D2/D3; section 8 |
| L-03 | PubMed acquisition by the **NLM 2026 annual baseline plus ordered update files** to a pinned cutoff, then a local versioned selection policy | APPROVED (Quinton, 2026-09-28; confirmed for recording; SCOPE 12A) | Not part of D-260. D-077's text permits "approved services" generally. The E-utilities specificity lives in P07-05's plan text and `CORPUS-AND-RIGHTS.md`, so those need reconciling (section 10). Codex recommended E-utilities for Tier 1; its cautions are carried as requirements (section 6) |
| L-04 | PMC full text only from the PMC Cloud Service (`pmc-oa-opendata`) for selected works whose per-article licence permits the use. XML text only | APPROVED as the planned route (Quinton, 2026-09-28, approved scope). Execution only via a signed run B | OA Web Service retired August 2026 |
| L-05 | PostgreSQL + pgvector is the literature/evidence data layer | **APPROVED (D-260)** | Supersedes the D-082/D-202 engine direction for Plan 07 |
| L-06 | Literature only; imaging stays file-first; no imaging mirror | **APPROVED (D-260)** | D-401 unaffected |
| L-07 | Canonical versioned literature artifacts are authoritative; the database is rebuildable operational state | **APPROVED (D-260)** | |
| L-08 | Frozen embeddings are canonical hashed artifacts; rebuilds reload rather than regenerate | APPROVED (Quinton, 2026-09-28; confirmed for recording; SCOPE 12A) | Not part of D-260. D-260 requires "embedding preservation/regeneration" to be specified; L-08 chooses preservation |
| L-09 | The live literature database is stored on the PROWL-Data external drive under a tested operating and recovery procedure (section 5) | APPROVED as a direction (Quinton, 2026-09-28; confirmed for recording; SCOPE 12A), subject to the P4a trial and 5.7 limits | D-260 requires "an explicit storage/risk decision" for removable media; section 5.7 is the risk statement for that decision |
| L-10 | Docker is the preferred runtime. The runtime, image digest, versions and storage layout are pinned only after P4a measurement, and **no change to shared Docker settings without inventory and approval** (section 5.5) | APPROVED as the prototype candidate (Quinton, 2026-09-28; SCOPE 12A). Pinned after P4a | Docker settings affect every project on the Mac |
| L-11 | The lexical control is PostgreSQL full-text search ranked by `ts_rank_cd` with a named, versioned text-search configuration. **Not BM25.** A BM25 extension only if development evidence shows the ranking is the bottleneck | APPROVED as the prototype candidate (Quinton, 2026-09-28; SCOPE 12A) | D-260 requires naming the actual method |
| L-12 | Planning documents: `SCOPE.md` + `PHASES.md` (not `SCOPE-AND-PHASES.md`) | APPROVED (Quinton, Claude discussion 2026-09-28) | Codex informed |
| L-13 | Embedding models: at least one general and one biomedical configuration, with matched query/article encoders where the model defines them | **PROPOSED implementation choice**, not a consequence of D-260 | Decided by P8 evidence with each model download authorized |
| L-14 | Generation: a local LLM candidate, selected by groundedness/refusal/latency | **PROPOSED implementation choice**; OPEN pending the Plan 10 boundary review | The extractive fallback is a complete output meanwhile |
| L-15 | Codex's synthetic foundation packet stays **on hold**. Its pure-Python parts remain valid; its SQLite FTS5 `lexical.py` is superseded by D-260/L-11 | APPROVED plan (Quinton, 2026-09-28). The implementation hold lifts only when Codex issues the revised packet and Quinton dispatches it | Needs a revised packet |
| L-16 | Selection specifics: language, date range, caps, bars | APPROVED as provisional settings (Quinton, 2026-09-28; SCOPE 12B). Changeable by a recorded decision | `SEARCH-AND-SELECTION.md`; frozen in P6 |

Everything else in the approved Plan 07 design (D-073 to D-087, D-209) stands.

## 3. In scope (deliverables)

1. **Planning set:** this document, `PHASES.md`, `INFORMATION-NEEDS.md`, `SEARCH-AND-SELECTION.md`,
   `SEED-SET.md`, `ACQUISITION-PLAN.md`, and `RUNNING-LOG.md` (append-only).
2. **Contracts:** versioned JSON Schemas and a logical ER model for:
   - source revisions and events, notices, rights decisions;
   - document representations, passages, corpus versions and membership;
   - embedding configurations and embeddings, builds;
   - queries, retrieval results, claims, responses;
   - evaluation spans and labels.
3. **Synthetic foundation:** deterministic records and identities, passages with exact offsets,
   the query gate, and pure metrics. No database, no network.
4. **Database platform:** pinned PostgreSQL + pgvector, migrations, constraints,
   staging-to-publication, rebuild from artifacts, backup/restore, operating procedure.
   Synthetic data first.
5. **Acquisition:** the 2026 PubMed baseline plus update files, MeSH 2026, and permitted PMC objects
   for selected works. Each needs a signed run record.
6. **Tier 1 corpus v1:** selection, precision sampling (development plus fresh confirmation), seed
   recall, rights records, normalization, passages, frozen manifest.
7. **Evaluation set:** 60 questions (D-209), with span-based relevance labels and a required
   consistency pass, frozen before tuning.
8. **Embeddings and index:** L-13 configurations frozen as artifacts, loaded and published.
9. **Retrieval and response development** on development questions only, then **one frozen held-out
   evaluation** of the complete configuration.
10. **Integration:** the Plan 04 literature workflow, Plan 08 UI states, G6 evidence.

## 4. Out of scope

- Patient images, masks, reports, identifiers, dates, institutions or ground truth anywhere in the
  literature system (D-075).
- Diagnosis, malignancy, stage, subtype, prognosis or treatment answers. These are refusal tests.
- An imaging database or imaging mirror (L-06).
- Indexing all of PubMed as the graded corpus; combining tiers; turning the parsed PubMed store into
  a vector index without X1 approval.
- Hosted vector services, external embedding APIs or paid calls without a separate Plan 10 decision.
- Scraping article pages. Bulk PDFs, media or supplements.
- Editing the proposal, appendix, `DECISIONS.md`, shared plans or Codex-owned files.

## 5. Architecture, operations and recovery

### 5.1 Authority and data flow

```text
NLM baseline + update XML ─┐   canonical, read-only, hashed (literature_source)
MeSH 2026 ─────────────────┤
                           v
          ordered event parser (derived parsed store, prowl_artifacts)
                           v
          selection policy vN ─> Tier 1 selection output (canonical)
                           │            │
PMC Cloud objects (bytes frozen at retrieval; canonical) <─┘
                           v
          rights records ─> normalized representations ─> passages (canonical)
                           v
          embedding config ─> frozen embedding artifacts (canonical)
                           v
      PostgreSQL + pgvector (derived operational state): staging -> validated -> published
                           v
      query gate -> lexical | dense | hybrid -> sufficiency -> claims+citations | refusal
```

**Canonical (authoritative) artifacts:**
- raw baseline/update/MeSH files and retrieved PMC object bytes;
- selection outputs;
- rights decisions;
- normalized representations and passages;
- corpus manifests;
- embedding configurations and frozen embeddings;
- question sets and labels;
- evaluation outputs.

**Derived:**
- the parsed PubMed store (regenerable from raw files plus parser version);
- every database table, index, WAL and publication flag.

### 5.2 Rebuild inputs

A published build is reconstructible from:
- the corpus manifest;
- source revisions and events;
- notices;
- rights decisions;
- representations and passages (content and hashes);
- corpus membership;
- embedding configuration plus frozen embedding artifacts;
- the lexical configuration;
- the migration version;
- index parameters.

Verification after a rebuild:
- **Exact:** identities, relationships and eligibility; **per-record content hashes** (passage text
  hash, representation hash); **per-row embedding checksums** compared with the frozen artifact;
  counts.
- **Declared tolerance:** approximate-index retrieval compared with exact search. We do not promise
  bit-identical approximate results.

### 5.3 Logical data model (proposed; finalized in P3/P4b)

| Table | Holds | Key constraints |
|---|---|---|
| `source_work` | Canonical bibliographic work | PK; unique PMID where present |
| `source_revision` | One content revision of a record | `revision_id` = SHA-256 of canonicalized record XML; FK work; NOT NULL provenance |
| `source_event` | Add/replace/delete events with file and ordinal | FK revision (nullable for delete); unique (source_file, ordinal) |
| `notice` | Retraction, correction and concern links | FK revision; enum |
| `rights_decision` | Per-representation permissions and policy version | booleans NOT NULL; enum decision |
| `document_representation` | Abstract or permitted full text | unique (revision, kind, content_sha256) |
| `passage` | Span with section path, offsets and hash | unique (representation, chunking_version, start, end); CHECK start < end |
| `corpus_version`, `corpus_membership` | Frozen corpus and its passages | unique manifest hash; unique pairs |
| `embedding_config` | Model, encoder role, dimension, normalization, precision, weight/tokenizer hashes | unique config hash |
| `embedding_<config>` | Vectors for one configuration | FK passage and config; unique (passage, config); typed `vector(n)` |
| `build` | Corpus + embedding config + lexical config + index parameters | status: `staging`, `validated`, `published`, `retired`, `failed` |

Retrieval reads only a published-build view or function that takes an explicit corpus version and
embedding configuration.

### 5.4 Invariants and enforcement

| Invariant | Enforcement |
|---|---|
| Every passage references a valid source revision | FK + pre-load artifact validation |
| Required provenance/version fields are present | NOT NULL + JSON Schema |
| Duplicate logical records are rejected | UNIQUE on logical keys; conflicting content for an existing key is an error, never last-write-wins |
| Embeddings reference a valid passage and pinned configuration | FKs; configuration hash matches the frozen-artifact manifest |
| Vector dimensions are valid | Typed per-configuration column; load-time check |
| Equal dimensions do not imply compatibility | Every query names its configuration; the query encoder comes from that configuration's matched pair; crossing configurations is an error (application test) |
| Retrieval uses only published builds | Least-privilege retrieval role reads the published view only; test proves staging/failed builds are invisible |
| Incomplete or failed builds never become visible | Staging, validation against canonical manifest content hashes, then one short publication transaction |
| Rights/notice filters apply to every branch | Filters live in the shared view; the same filter fixtures run through lexical, dense and hybrid |
| Filtered vector search returns up to `min(k, eligible_count)` eligible results | Compared with exact search. If fewer than k eligible records exist, return all of them with an explicit `result_count` and a reason flag. If approximate plus filter under-returns, fall back to iterative index scans or exact search |
| Citations resolve to the exact revision and passage | Response validator; test resolves every cited ID to canonical artifacts |
| Interrupted ingestion resumes without duplicates | Idempotent keyed staging loads; conflict is an error; resume test |

### 5.5 Storage placement and runtime

- **Placement (L-09):**
  - `literature_source` holds read-only raw files and PMC bytes;
  - `prowl_artifacts/literature/` holds derived and canonical lane artifacts;
  - `prowl_literature_db` holds live database state, never authority.

  All three are on `PROWL-Data`. The aliases need Codex's Plan 10 registry amendment.
- **Docker scope:** Docker Desktop's disk-image location is a **global runtime setting**. Moving it
  changes storage for every container and volume on the Mac, not just PROWL. Before proposing any
  such change:
  - inventory existing containers, images and volumes, and their sizes;
  - show the impact;
  - get Quinton's explicit approval.

  The P4a candidate layouts are:
  - (B) bind-mount a PROWL directory on the drive;
  - (C) a PROWL-dedicated runtime or VM whose disk lives on the drive, leaving other projects
    untouched;
  - (A) relocate the global disk image, only if approved after inventory.
- **Footprint and memory are measured, not assumed.** P4a records the database size, WAL, index
  size, the internal-SSD footprint of each layout, and memory use. No claim about memory residency is
  made until measured.
- **Coexistence limits are defined before testing** (proposed; confirmed once the Mac's installed RAM
  is recorded). Coexistence uses a **synthetic, bounded workload**, never a real imaging run.
  Recorded hardware: **64 GiB physical RAM** (verified by Codex, 2026-09-28). Proposed limits:
  - Docker VM memory cap no more than 15% of physical RAM (about 9.6 GiB);
  - top-10 hybrid query p95 latency no more than 500 ms at a synthetic 100k-passage scale;
  - the synthetic MPS workload loses no more than 10% throughput with the database running.
- **Credentials:** listen on 127.0.0.1 only. Secrets live in the macOS Keychain or an ignored env
  file, never in Git, docs or logs.

### 5.6 Operating procedure (PROPOSED; rehearsed in P4a on disposable synthetic instances)

**Start:**
1. The volume is mounted, its UUID matches the registry, and free space is above the floor.
2. Start the runtime.
3. Start the pinned image by digest.
4. Health gate:
   - `pg_isready`;
   - migration version;
   - the published build's per-record content hashes and embedding checksums match its canonical
     manifest.

   Only then enable retrieval.

**Stop:**
1. Stop ingestion jobs and the evidence API.
2. Stop the database. The pinned image's actual stop signal and grace period are recorded at pin
   time. The official PostgreSQL image is expected to declare `SIGINT` (a fast shutdown); verify this
   for the pinned digest. Docker's default 10-second timeout is too short, so set an explicit grace
   period (proposed 120 s) and require a clean-shutdown log line.
3. Stop the runtime if its storage is on the drive.
4. Confirm no open files.
5. Eject.

**Scoped recovery after a crash or unexpected disconnect:**
1. Mark the affected build unavailable. Retrieval returns `evidence_unavailable` (it never guesses).
2. **Preserve diagnostic evidence:** logs, and the failed instance moved aside, not dropped.
3. Run PostgreSQL's recovery, then the supported structural checks:
   - `amcheck` covers B-tree indexes and heap relations. It does **not** validate pgvector HNSW or
     IVFFlat indexes.
   - Verify vector behaviour separately against exact search, and `REINDEX` derived vector indexes
     when in doubt.
4. Compare record contents and embeddings with canonical artifacts.
5. If verification fails, rebuild **only the identified derived database** into a new instance,
   verify it, then switch.
6. The failed instance is deleted only after review.

**What the drills prove, and what they do not:**
- A container kill proves process-crash recovery only. It does **not** prove durability against USB
  disconnection or power loss, and Docker virtualization plus macOS external-drive caching mean we
  make no durability claim for those cases.
- **The shared data drive is never physically unplugged as a test.**

### 5.7 Recovery honesty and backups (the L-09 risk statement)

Database-only corruption is recoverable **if the canonical artifacts remain intact**. A drive or
filesystem failure can destroy the database **and** the canonical artifacts together, because they
share `PROWL-Data`. Recovery then depends on verified independent backups or reacquisition, and exact
historical bytes may not be available upstream:

- PMC object bytes can change without a version change.
- Annual PubMed baseline files are not guaranteed to stay downloadable after the next baseline
  release.

The rebuild set, measured and classified in P4a/P5/P6 (sizes are unknown until measured):

| Artifact | Replaceable? | Independent copy plan (PROPOSED) |
|---|---|---|
| **Held-out** questions, labels, adjudication notes | **No** (human work) | Protected store only (section 5.8): an encrypted archive on `PROWL-Data` plus an independent encrypted copy on the internal `prowl_backup`. **Never committed to the working checkout** |
| Development questions and labels | **No** (human work) | Git **and** `prowl_backup`. A commit in the same local checkout is **not** an independent copy until it is pushed to the remote (pushing needs Quinton's authorization) |
| Selection outputs, rights decisions, corpus/passage manifests, configs, held-out manifest **hash** | Regenerable only with the same raw inputs | Git (manifests, hashes, IDs; no restricted text) once pushed, plus `prowl_backup` |
| Tier 1 raw record subset and PMC object bytes | Not exactly reacquirable | `prowl_backup`, if the measured size fits the allocation |
| Normalized representations and passages | Regenerable from the above | `prowl_backup` if it fits; otherwise regenerated |
| Frozen embeddings | Regenerable but not bit-identical | `prowl_backup` if it fits. If lost, regenerated embeddings get a **new artifact and build identity**; they never replace the lost artifact under the old identity, and affected results are re-verified |
| Full raw baseline and update files | Reacquirable only while NLM hosts them | No independent copy planned (too large for the internal cap). Residual risk recorded. A second drive is an OPEN option |
| Parsed store, database, indexes | Derived | None needed |

`prowl_backup` has a 20 GiB cap and a 100 GiB internal free-space floor (D-258), **shared with
existing imaging controls**. Literature does not get that capacity automatically. Once P6 has
measured the Tier 1 rebuild set, Claude proposes a literature allocation, and Quinton (with Codex)
approves it or chooses another independent target.

### 5.8 Held-out isolation (PROPOSED safeguard)

This is a **separate encrypted container for evaluation material only**. It is not drive-wide
encryption, and it does not change the drive.

**Lifecycle:**

| Stage | Container | Access |
|---|---|---|
| **Authoring** (P7, pre-freeze) | Read-write encrypted image (built-in `hdiutil`; no new dependency), stored at `prowl_artifacts/literature/evaluation/heldout/authoring/` | Quinton mounts it for logged sessions: authoring, labelling, the required consistency pass. Validators run by Quinton report only pass/fail, counts and hashes to agent sessions |
| **Freeze** (end of P7) | A new **frozen evaluation image** is created from the authoring content. Its image hash and content-manifest hash are recorded | Logged session |
| **Backup verification** | The frozen image is copied to the internal `prowl_backup` | Verified by comparing image-file hashes without mounting. Any mount for verification is logged and read-only |
| **Evaluation** (P11 and any genuine-defect rerun) | Frozen image mounted **read-only** (`hdiutil attach -readonly`) | A logged session for a dedicated evaluator process, then unmounted |

**Access boundary (stated honestly):**
- While an image is mounted, any process running as Quinton's macOS user could technically read
  its plaintext, including agent tools that have filesystem access.
- The real boundary is therefore **procedural**:
  - mount only during logged sessions;
  - mount at a location **outside every folder connected to Claude or Codex sessions**;
  - no agent session is given the mount path or the passphrase (held by Quinton in the Keychain);
  - unmount immediately afterwards.
- The static check that tuning code never references the held-out location proves only that the
  code doesn't point there. It is **not** an access-control guarantee.

**Audit:** every mount is logged in `RUNNING-LOG.md`: who, when, stage and purpose, image hash
before and after, and result hash. Mounts outside these stages are protocol deviations.

**Git** holds schemas, synthetic examples, and the frozen image's manifest hash and counts. Never
held-out questions or labels.

## 6. Requirements carried from Codex's review (L-03)

- Apply baseline, then update files, strictly in order: additions, replacements, deletions, repeated
  events. A source revision is defined by **content hash plus event provenance** (file and ordinal),
  not by a bibliographic version field.
- The local selection policy is PROWL's own policy, not PubMed's automatic term mapping.
- Missing MeSH never silently excludes a record. Indexing status comes from the record's
  `MedlineCitation` status, not from publication year.
- Citation records are not full text.
- PMC bytes are frozen at retrieval.
- Every download is a live network job with its own signed run record.

## 7. Definition of done

Plan 07 G6 met under D-260:
- versioned selection, cutoff and manifest;
- every indexed passage maps to a rights-approved revision and locator;
- exact rebuild checks pass;
- lexical and dense (plus hybrid if adopted) measured, with the selection recorded;
- the question set frozen, with the held-out evaluation run once on the frozen complete configuration;
- the query gate rejects forbidden inputs;
- claims resolve;
- refusal and unavailable states tested;
- transports agree;
- the workflow rebuilds and resumes without blocking imaging;
- artifacts handed to Plan 08.

Proposal checkpoints:
- **Week 5:** queryable prototype;
- **Week 6:** development retrieval metrics;
- **Week 8:** held-out metrics.

## 8. Tier 2 boundaries (gated, L-02)

Tier 2 needs a separate extension plan and approval covering budget, storage, users, stop rules and
evaluation. Its rules:

- separate identities;
- a resolver that never combines tiers or falls back from one to the other;
- no patient data or protected labels;
- agents cannot reach held-out answers through it;
- promoting material into Tier 1 creates a new reviewed Tier 1 corpus version;
- it starts with a bounded broader sample and measures whether breadth helps without hurting
  precision;
- Weeks 9-10 are protected.

## 9. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-01 | Drive/filesystem failure takes out the database **and** the canonical artifacts | Section 5.7 inventory; independent copies of irreplaceable artifacts; residual risk recorded |
| R-02 | Runtime memory competes with MPS training | Numeric limits (5.5); synthetic coexistence test; database off during heavy training until measured |
| R-03 | Drive latency (type unknown) | Measured in P4a |
| R-04 | Missing MeSH drops records | Text rules; indexing status from `MedlineCitation` |
| R-05 | Local selection mistaken for a PubMed search | Documented; seed recall; fresh confirmation sample |
| R-06 | Filtered approximate search under-returns | Exact-search reference and test |
| R-07 | Wrong embedding space | Explicit configuration per query; matched encoders |
| R-08 | Question-set circularity or leakage | Needs frozen before inspecting this run's results; prior exposure disclosed; Quinton authors and labels; held-out isolation test |
| R-09 | Rights misclassification | Fail-closed records |
| R-10 | Tier 2 scope creep | Separate approval |
| R-11 | Week 5 slip | Pre-course P0-P4; background download |
| R-12 | Shared Docker settings changed for other projects | Inventory and approval before any global change (5.5) |
| R-13 | Pillar wording also names scans, findings and reviews | D-260 literature-only boundary; interpretation recorded |
| R-14 | Update ordering or replay errors | Event-log parser with replay tests |
| R-15 | PMC bytes change | Frozen bytes plus independent copy (5.7) |
| R-16 | Appendix v3.1 says relational DB only after a measured need | Reported openly with D-260's rationale; appendix not edited |
| R-17 | Drills over-claimed | 5.6 states what each drill proves |
| R-18 | Rechunking changes recall denominators | Span-hit metrics and label versions (PHASES P7-P9) |

## 10. Reconciliation list (for Codex; not edited by Claude)

**Status note (2026-09-28, recorded by Claude from the Codex P2 review; row text unchanged):**
- **Done (wording only):**
  - the P07-05 and `CORPUS-AND-RIGHTS.md` channel-text rows are reconciled: baseline plus ordered
    updates, with E-utilities for bounded checks;
  - L-03, L-08 and L-09 are recorded as D-261 to D-263.
- **Not done:** runs S, A and B are unsigned. The storage-alias rows are not complete (see
  `ACQUISITION-PLAN.md`, S1). Codex owns the other rows.

| Record | Issue | Proposed change |
|---|---|---|
| `DECISIONS.md` D-077 | Text already permits "approved services"; no conflict | Optional clarifying note that the NLM annual baseline/update distribution is an approved service route under L-03, once Quinton confirms L-03 |
| P07-05 text (`07-literature-retrieval.md`) and `retrieval/CORPUS-AND-RIGHTS.md` "Approved source channels" | E-utilities-specific | Add the bulk baseline/update channel with event-order semantics; keep E-utilities for small checks |
| D-082, D-202 | Superseded for Plan 07 by D-260 | Reframe D-202 as the pgvector configuration and embedding selection by P4a/P8 evidence |
| D-211 | Relational persistence only on a measured need | Note that it is answered for literature by D-260 |
| New decision records | L-03, L-08, L-09 approved in Claude's discussion, not in D-260 | Record them after Quinton confirms (section 2 wording) |
| D-085 (retrieval metrics) | recall@k/MRR only | **Proposed amendment:** add span-hit recall@k (a ranked metric), plus separately reported delivered-evidence metrics under a context budget (PHASES P7, part B). The D-085 ranked metrics stay official |
| `retrieval/QUESTION-SET-AND-EVALUATION.md` | No protected held-out storage procedure; passage labels by ID | Add the SCOPE 5.8 protected store and access audit, and span-based labels with complete-containment scoring |
| `07-literature-retrieval.md` | SQLite/LanceDB wording, implementation steps 11-12 | Align with D-260 and PHASES |
| `retrieval/TOOL-SELECTION.md`, `QUERY-AND-RETRIEVAL.md`, `README.md` rule 11 | LanceDB/SQLite assumptions | pgvector configuration spike; PostgreSQL FTS `ts_rank_cd` control |
| `CLAUDE-PLAN07-FOUNDATION-PACKET-2026-09-28.md` | SQLite FTS5 `lexical.py` | Revised packet (L-15) |
| `PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md` D8 | `SCOPE-AND-PHASES.md` | `SCOPE.md` + `PHASES.md` |
| `operations/STORAGE-ROOTS-AND-ARTIFACTS.md` | No literature aliases | Add `literature_source` and `prowl_literature_db` with failure-domain IDs |
| `operations/BACKUP-RETENTION-AND-RECOVERY.md` / D-258 | Shared 20 GiB cap | A literature allocation or another target after P6 measurement |
| Appendix v3.1 | Relational-DB boundary | Explain in reporting; do not edit |

## 11. Ownership and authorizations

| Area | Owner | Needs before execution |
|---|---|---|
| This planning set | Claude drafts; Quinton approves; Codex reviews | Quinton's review |
| Shared records (section 10) | Codex | Quinton's confirmation |
| Synthetic foundation code | Claude | Revised packet dispatched |
| Runtime/PostgreSQL/pgvector/driver install | Claude, with Codex review | Explicit install authorization; Docker inventory if shared settings are involved |
| Downloads | Claude or Codex | A signed run record per job |
| Embedding models and LLM pulls | Claude | Authorization per model; licence checked |
| Question authoring and labels | Quinton | Needs approved first |
| Notion lane entries | Claude | Accurate and linked to evidence; hub snapshot stays with Codex |

## 12. Approval checklist (v4)

Approving an item in one group does **not** approve anything in another. General plan approval is
**not** a signature on run S, A or B, and not permission to download any model.

### A. Architecture and design (Codex recommends approval)

| Item | Status |
|---|---|
| Plan 07 scope, the 13-phase structure, and development/held-out separation | **APPROVED** (Quinton, 2026-09-28) |
| L-03 bulk PubMed acquisition as the **intended route**, for recording (separate from D-260) | **APPROVED** (Quinton, 2026-09-28) |
| L-08 frozen embedding artifacts, for recording | **APPROVED** (Quinton, 2026-09-28) |
| L-09 external-drive database as a **direction**, subject to the P4a storage trial and the SCOPE 5.7 backup limits, for recording | **APPROVED** (Quinton, 2026-09-28) |
| L-10 Docker and L-11 PostgreSQL `ts_rank_cd` keyword baseline as **prototype candidates** | **APPROVED** (Quinton, 2026-09-28) |
| Separate encrypted held-out container (SCOPE 5.8), if Quinton wants this safeguard | **APPROVED** (Quinton, 2026-09-28) |
| Two-stage selection, confirmation reserve and inspected-PMID ledger | **APPROVED** (Quinton, 2026-09-28) |

### B. Provisional experimental settings (changeable by a recorded decision; not permanent limits)

**Status:** all B settings **APPROVED as provisional** by Quinton on 2026-09-28.

| Setting | Proposed value |
|---|---|
| Language | English only, with missing language included and flagged |
| Date range | 2000 to cutoff; missing dates included and flagged |
| WORKFLOW cap | 500, applied after hard exclusions |
| Seed-recall bar | At least 90%, every miss explained |
| Precision bars (confirmation or census) | At least 60% relevant + partial; at least 40% relevant |
| Revision limits | 3 policy revisions; 2 confirmation rounds |
| Context budget | 2,000 tokens (starting setting, not a product limit) |
| Capacity ceilings | 100 GiB each for Tier 1 artifacts and for the database + recovery instance. These are **ceilings, not expected sizes** |
| Coexistence limits (64 GiB RAM) | Runtime memory at most about 9.6 GiB; hybrid p95 at most 500 ms at synthetic scale; at most 10% synthetic MPS slowdown. Remain PROPOSED until P4a measures |

### C. Execution permissions (each needs its own explicit authorization; none granted)

**Status:** none granted. Quinton's 2026-09-28 approval of groups A and B does **not** grant any
item below.

| Permission | When requested | Needs |
|---|---|---|
| Revised synthetic foundation packet (P3) | Next | Codex issues it; Quinton dispatches it |
| Install a container runtime, pinned PostgreSQL image and pgvector (P4a) | After P3 starts | A named runtime and versions; a Docker inventory if any shared setting is involved |
| psycopg 3 dependency (P4b) | After P3 contract review | Dependency approval |
| Sizing-only tool packet, then **sign run S** | P2 to P5 | Tests passing; signed S |
| Full downloader/parser packet, then **sign run A** | P5 | Tests passing; S receipt reviewed; capacity check |
| **Sign run B** | P6 | Frozen stage-1 candidate set |
| Each embedding model download (L-13) | P8 | **Specific** model names, licences, sizes and hashes identified first |
| Generator runtime and model (L-14) | P10 | Plan 10 boundary review; specific model, licence, size |
| Plan 04 workflow coding (P12) | P12 | Plan 04 authorization |
