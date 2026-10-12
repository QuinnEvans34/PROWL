# AI expert: database and retrieval implementation plan

Date: October 12, 2026. Status: implementation proposal; inventory complete, no database launched.
Owner: Quinton + Mac development chat. Tracking: [W02-08](https://trello.com/c/nqTumUtb).

## Phase dashboard and review agreement

This is the current execution guide for returning to the AI expert. The phase names below are
review milestones mapped to the existing [P0–P12 design](planning/PHASES.md), not a replacement
architecture or a promise to finish the entire expert in Week 2. Reuse accepted work; inspect its
evidence before deciding that a requirement needs implementation again.

**Current:** Phase 1 accepted by Quinton's instruction to continue; Phase 2 partially executed.
User cleanup cleared the storage blocker (127.0 GiB internal free at admission). Synthetic SQL,
clean restart, process-crash recovery and fresh-database dump/restore passed; container stopped.
28 model-free checks and Compose validation pass. See [handback](../../../infra/retrieval/README.md).
**October 12 larger trial:** 100k benchmark and separate-instance restore completed; filtered HNSW
recall failed the 95% bar. [Results and exact-first recommendation](PGVECTOR-PHASE2-RESULTS-2026-10-12.md).
**Current closeout:** Quinton selected exact-first retrieval. Client latency (205 ms broad p95;
211 ms concurrent) and synthetic GPU coexistence (1.73% throughput reduction) passed; all owned
containers stopped. Phase 2 engineering complete, ready for review; HNSW remains deferred.
**Next:** Phase 3 / W02-06 full journal selection. Real-corpus ingestion remains Phase 5.
All later implementation phases remain pending; platform acceptance is not complete.

| Phase | What Quinton can review | Completion checks | Next / existing tracking |
|---|---|---|---|
| 1. Database setup package | Compose configuration, storage diagram/paths, exact image and resource packet, simple start/check/stop instructions | Configuration validates; missing/wrong drive, occupied port and insufficient space refuse startup; secrets stay local; footprint fits the floor | Phase 2; W02-08 / P4a |
| 2. Working synthetic database | A repeatable demo of keyword/vector/combined searches plus restart and recovery report | Initial 1k smoke passes, then formal 100k P4a filter/recall/performance/resource/restore criteria below pass; limitations recorded | Phase 3; W02-08 / P4a |
| 3. Selected literature | Candidate-selection summary with inclusion/exclusion reasons and corpus identity | Full selector completion and counts/hashes reconcile; seed/reserve controls met; candidates explicitly remain distinct from permitted text | Phase 4; [W02-06](https://trello.com/c/LxvwMa3s) / P6 |
| 4. Traceable passages | Example permitted passages with source, offsets, notices and stable IDs; contract mapping | Storage/embedding/display permissions checked separately; passage validation passes; missing permissions excluded; P3 review reconciled | Phase 5; [W02-07](https://trello.com/c/fGxysGgy) / P3, P6 |
| 5. Real searchable corpus | Versioned schema/loader, encoder decision, bounded ingestion report, example searches | P4b contracts pass; P7 evaluation set and protected roles frozen before P8; selected encoder/config and rights valid; atomic publication and rebuild checks pass | Phase 6; W02-08 / P4b, P7, P8 |
| 6. Evidence search in the app | Guided question returns real cited passages; clear loading, empty, failure and case-switch behavior | Development-only lexical/vector/hybrid comparison recorded; exact provenance preserved; retrieval outage does not break imaging | Phase 7; P9, early P12 |
| 7. Grounded expert responses | Reviewed DAG, supported answers and insufficient/conflicting/refusal examples, saved response history | Claim/citation support and response-state tests pass on development examples; one saved response per request; approved wording and clinical boundary preserved | Phase 8; P10, P12 |
| 8. Final evaluation and delivery | Frozen configuration, held-out results, end-to-end demo and operating instructions | P11 held-out evaluation performed once after freeze; G6/integration criteria checked; limitations and remaining defects reported | Stabilization; P11, P12 |

Phases 6–8 need linked Trello implementation cards when promoted into the active queue; first check
for existing Plan 07 cards and reuse them. W02-08 stays open after Phase 2 because it also owns Phase 5.
Use phase completion notes on existing cards to avoid creating a second competing task queue.

### How we work through a phase

1. At the start, state the current phase, concrete deliverable and acceptance checks. Keep one
   implementation phase active; a long background job does not silently expand scope.
2. Complete the phase's implementation and appropriate checks, then show Quinton a short handback:
   **what changed; what to inspect/demo; checks passed or failed; remaining limits; next phase**.
3. End at that review boundary so Quinton can request changes before we begin the next phase.
   Routine fixes inside the selected phase do not need repeated permission questions. If Quinton
   explicitly asks to continue through multiple phases, honor that scope and still report milestones.
4. Record status as pending, active, ready for review, changes requested, accepted, or blocked. Mark
   acceptance only after the required evidence and review; a partially passing phase stays partial.
5. Update this dashboard and the existing Trello card with evidence and the next action. Finish each
   accepted code phase with focused commits; keep data, credentials and runtime outputs out of Git.

When blocked, name the missing evidence or decision and identify any independent useful work.
Do not automatically repeat successful tests or expand corpus/model scope. Hours are recorded only
from Quinton's confirmed human work, separately from unattended runtime.

### Phase 1 boundary

Build the proposed configuration, preflight and synthetic smoke harness; make the launch packet
concrete with an image digest, verified path/port, stop behavior and enforced budgets. Show those
artifacts for review before the first runtime/image launch. Phase 2 executes and measures that packet.
No journal scan, model download or real embedding job is part of Phase 1.

## Starting point

- PostgreSQL + pgvector is already selected by D-260; retain the [P4a/P4b requirements](TOOL-SELECTION.md).
- PubMed replay is complete: 1,656 files, 41,226,017 records, 10,817 deleted PMIDs,
  510,130,282,496 database bytes. Selection and rights qualification remain false.
- MeSH 2026, journal selection code, passage/provenance contracts and guided response fixtures exist.
- No PROWL PostgreSQL instance, pgvector adapter or real embeddings were found in this inventory.
- External APFS volume PROWL-Data has UUID `22750B93-2F3F-499D-87F5-902981BFAB59`
  and approximately 2.1 TiB free. Internal storage has approximately 103 GiB free,
  close to the existing 100 GiB floor; remeasure before any pull or launch.
- Docker Desktop is running with 18 CPUs and approximately 7.75 GiB VM memory.
  The running `nw-postgres` PostgreSQL 17 container belongs to another project.
  Native PostgreSQL/Homebrew package availability was not established.

## Proposed order and deliverables

| Step | Work | Done when |
|---|---|---|
| 1 — W02-08 platform | Build a PROWL-only synthetic PostgreSQL/pgvector trial | Persistence, search, filters, crash recovery and restore have measured evidence |
| 2 — W02-06 | Execute the full journal candidate selector | Candidate IDs, counts, exclusions, input identities and completion receipt reconcile |
| 3 — W02-07 | Qualify permitted representations and construct passages | Stable IDs, exact source offsets/hashes and separate storage/embedding/display permissions validate |
| 4 — W02-08 integration | Choose a pinned encoder and ingest a bounded real passage slice | Rebuildable published corpus, exact citations and lexical/vector/hybrid queries validate |
| 5 — expert integration | Connect retrieval to guided reviewer questions, then grounded responses | Saved response/request, citation support and failure/refusal behavior pass end-to-end checks |

Step 1 can proceed independently of journal selection. Steps 2–4 retain their data dependencies.
The SQLite catalog stays authoritative upstream: do not copy or embed all 41 million records.
Seed/reserve controls precede selection evaluation or protected-question use. Training and PANORAMA
remain with the other laptop/chat. Deferred Week 2 checks and Sunday review remain open.

## First implementation packet: isolated platform

Proposed files: `infra/retrieval/compose.yaml`, a documented ignored local environment file,
`scripts/retrieval/check_pgvector_platform.py`, and focused synthetic integration tests.
These paths describe future implementation, not existing artifacts.

1. Pin a compatible ARM64 PostgreSQL/pgvector image by digest and record server/extension versions.
   Inspect image size and internal Docker overhead before pulling; preserve the internal free-space floor.
2. Compare an external PROWL bind mount with a dedicated runtime/VM. Prefer the existing Docker
   runtime with a dedicated external PROWL data directory if permissions, persistence and performance
   pass. A dedicated runtime adds installation/storage overhead and is a fallback to discuss if needed.
   Do not relocate the global Docker disk or modify unrelated containers.
3. Use a unique Compose project, localhost-only unused port, ignored local credentials, health check,
   explicit data root, stop signal/grace and recorded resource limits. Verify volume identity before
   startup so a missing drive cannot silently create an internal data directory.
4. Proposed initial smoke: 1,000 deterministic synthetic passages/vectors, 2 CPUs, 2 GiB container
   memory, 8 GiB external output ceiling and 30-minute execution ceiling. These are proposed caps;
   the launch packet must define enforcement, internal overhead allowance and free-space margins.
5. Verify exact cosine search, PostgreSQL full-text search (`ts_rank_cd`), deterministic fusion,
   restrictive rights/build filters, empty results, duplicates, invalid dimensions and restart.
6. Expand to the formal 100k synthetic P4a trial with a separately recorded budget. Compare default
   HNSW to exact eligible results, including restrictive filters and exact fallback. Preserve P4a bars:
   recall >=0.95 at k=10, hybrid p95 <=500 ms, VM memory <=15% physical RAM, and <=10% synthetic
   MPS throughput reduction. The small smoke alone does not satisfy these platform exit criteria.
7. Test clean stop/start, process-crash recovery and dump/restore into a fresh synthetic instance.
   Compare IDs/counts/content hashes/vector checksums. Preserve failed logs; do not unplug the drive
   or claim that a process kill proves power-loss durability.

No model download or real literature is needed for the initial smoke. Record and review the measured
layout before treating the platform as accepted. Runtime/image and dependency decisions required by
the existing plan belong in the concrete launch packet.

## Contract-bound database adapter

After P4a and P3 contract review, resolve the psycopg dependency and implement versioned SQL migrations,
an ingestion CLI and a small retrieval adapter under `src/retrieval/`. Map existing records rather than
introducing a second passage identity scheme:

- Corpus builds, source works/revisions, representations and passages with foreign keys and uniqueness.
- Separate rights for local text storage, embedding and display; retain notices and provenance.
- Embedding configurations pin encoder revision, tokenizer, dimensions, normalization and metric;
  incompatible configurations cannot share a vector table/query.
- Stage and validate a complete build before atomic publication. Failed/partial loads stay invisible.
- Lexical, vector and hybrid branches use the same eligible published build. Compare approximate
  under-return with exact eligible search; report when fewer than k eligible passages exist.
- Canonical passage exports and frozen embedding files remain authoritative outside PostgreSQL.
  Rebuild into a new database/build and verify before switching; no database-only corpus corrections.

Only then select a bounded real ingestion count and encoder budget from measured candidate sizes and
permissions. Do not invent a model choice or dimensionality during the infrastructure trial.

## Expert flow after retrieval

Guided question + allowed coarse imaging context → scope/privacy check → versioned query → eligible
lexical/vector retrieval → fusion and evidence sufficiency check → cited response or explicit
insufficient/conflicting/unavailable/refusal state → one saved response per request.

Retain the approved professional wording and clinical-scope boundary. A retrieved passage alone does
not establish that a generated claim is true: validate support/citations and evaluate response quality
before replacing the clearly labeled fixture experience. Database outages must not block imaging.

## Sources and next decision

- [Existing platform and integration requirements](TOOL-SELECTION.md)
- [Query and retrieval contract](QUERY-AND-RETRIEVAL.md)
- [Corpus runbook](STREAMING-CORPUS.md)
- [Official pgvector documentation](https://github.com/pgvector/pgvector): exact search is the default;
  approximate indexes trade recall for speed, so exact search supplies the comparison baseline.

Recommended next implementation: prepare the isolated Compose configuration, preflight and synthetic
smoke harness, then review its concrete image/layout/resource packet before the first launch.
