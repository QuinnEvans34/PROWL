# PostgreSQL + pgvector configuration trial

## October 12 configuration decision

Quinton accepted exact vector search plus PostgreSQL full-text search for the initial bounded
corpus and deferred optimization after reviewing the filtered HNSW recall failure. The synthetic
trial is authorized by the Phase 2 continuation requests. The older no-execution status below
records the original design stage, not the current trial authorization.

Exact-first configuration must still meet the latency/resource/coexistence and recovery criteria.
The >=0.95 approximate-recall bar remains mandatory before any future approximate-index promotion;
the failed HNSW trial is retained, not relabeled as passing. See
[Phase 2 evidence](PGVECTOR-PHASE2-RESULTS-2026-10-12.md). Real embeddings, relevance and contract-bound
ingestion remain later work.

Status: approved engine and trial design; no installation/execution permission.
D-260 selects the literature-only engine. D-263/D-264 and approved PHASES P4a/P4b
supersede the historical engine bake-off retained below. D-202 remains open for measured
index/embedding configuration, not a second engine. Files and frozen embeddings are authoritative.

## P4a: platform trial

Separate runtime/image/extension authorization is required. Inventory shared Docker state
before proposing any global change. Compare a PROWL bind mount and dedicated runtime/VM
first; global disk-image relocation requires explicit approval. Record internal footprint,
external filesystem/UUID, versions, image digest, stop signal, grace period and resource budget.
Use disposable synthetic instances only; never unplug the shared drive as a test.

Test exact vector search and representative HNSW at defaults, including restrictive filters
and iterative/exact fallback. Expand to IVFFlat, half precision or tuned HNSW only if latency,
approximate recall (<0.95 at k=10 against exact), or memory triggers justify it. Vector recall
is separate from relevance recall/MRR. The lexical control is PostgreSQL FTS ts_rank_cd,
with pinned dictionaries/configuration; it is not BM25.

Proposed P4a bars from the approved planning set: VM memory <=15% of physical RAM
(~9.6 GiB on the recorded 64 GiB Mac), hybrid p95 <=500 ms at 100k synthetic passages,
and <=10% synthetic MPS throughput reduction. These require measurement; no real imaging
job is authorized. Define the trial duration and disk/time caps in its execution packet.

Rehearse clean start/stop, process-crash recovery and synthetic dump/restore. A container
kill proves neither USB-loss nor power-loss durability. Preserve failed instances and logs;
rebuild into a new instance, verify, then switch. Deletion is separately reviewed.
Quinton approves the measured layout. If limits fail, stop and present options.

## P4b: contract-bound integration

Requires P4a exit, Codex review of P3 contracts, and explicit psycopg dependency approval.
Map constraints to SQL, transaction, query or tests: parent references, logical uniqueness,
rights/notices, dimensions, encoder compatibility, staging visibility and atomic publication.
All retrieval branches use the same eligible published-build scope. Under-return checks
compare with exact eligible search; fewer than k eligible records gets a count/reason.

Reload canonical records and frozen vectors. Compare IDs, relationships, counts, per-record
content hashes and per-row embedding checksums exactly. Approximate search equivalence uses
declared tolerances. No database-only corpus edits. Missing/corrupt/unverified stores yield
an honest unavailable state and never block imaging.

## D-202 evidence and later selection

Record platform/root versions, fixture identities, resource measurements, filter/restore
results, limitations, adapter size and selected configuration. P8 names and authorizes each
embedding candidate before any pull; P9 measures relevance on development questions.
Freeze retrieval and response together before P11 held-out evaluation. Model identities are
still proposed/open. Another vector engine requires a new decision, not automatic fallback.

## Historical September 9 tool-selection plan (superseded)

The following text preserves the earlier rationale only. Its install, engine-selection,
fixture-size, four-hour and fallback instructions are not the current execution packet.

<details>
<summary>Superseded local-engine comparison</summary>

# Local retrieval tool selection

**Status:** Approved bounded design for D-202; no tool selected yet  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P07-10 through P07-12  
**Governing plan:** [`../implementation/07-literature-retrieval.md`](../implementation/07-literature-retrieval.md)

## Decision to make

Choose the smallest local stack that provides reproducible vector retrieval, stable passage/metadata
mapping, required filters, rebuildability, and acceptable latency without becoming a separate service
project.

The scientific contracts do not depend on the selected library. Corpus/passages and retrieval-result
records remain PROWL-owned versioned artifacts.

## Required capabilities

- local/offline operation after dependencies/models are acquired;
- persistent index under a configured root;
- explicit passage IDs, vectors, and metadata;
- cosine/inner-product or selected metric with documented normalization;
- metadata filtering or a deterministic tested adapter;
- exact or quality-measured approximate top-k;
- full export/inventory/count/hash validation;
- deterministic/tolerance-tested rebuild;
- simple backup/delete/rebuild from authoritative corpus;
- Apple Silicon/Python environment compatibility;
- license acceptable for capstone use/release;
- query/build latency measurement;
- no managed account/control plane requirement; and
- adapter surface small enough to replace without changing Plan 07 contracts.

## Candidates

### Control: SQLite FTS5

Purpose: lexical baseline, durable metadata/query support, and fallback.

Strengths:

- built into a single local database file in common Python distributions;
- transparent rows/joins/filtering;
- good exact terminology baseline; and
- easy deterministic rebuild/export.

Limit: not by itself the required dense vector implementation.

### First vector candidate: LanceDB OSS local

Why first:

- embedded/local filesystem connection;
- passage vectors plus metadata in one table;
- documented vector search, filtering, full-text, and hybrid capabilities; and
- supports the file-first single-workstation shape without a server.

Questions for the spike:

- Python/Apple Silicon installation and dependency footprint;
- exact local persistence/reopen/backup behavior;
- whether local full-text/hybrid behavior meets our deterministic needs;
- filter semantics for missing values and rights/source policies;
- stable export/count/passage mapping and rebuild;
- upgrade/schema migration behavior; and
- whether the storage layout can be treated as disposable derived output.

### Fallback: Chroma persistent local

Evaluate if LanceDB fails. It offers a local persistent client and metadata/document filtering, but
the spike must verify current local—not cloud-only—features, export/rebuild behavior, and dependency/
storage stability.

### Minimal fallback: FAISS exact index plus PROWL sidecar

Use normalized vectors with exact inner-product search for cosine-equivalent ranking and keep passage/
metadata/filter authority in a validated SQLite/Parquet/JSONL sidecar. This adds adapter responsibility
but minimizes database assumptions and is highly rebuildable for a small corpus.

## Four-hour spike ceiling

Timebox the first-candidate spike to four focused hours after dependencies and a small rights-cleared
fixture are ready. Stop early on a non-negotiable failure.

### Fixture

- 100–500 synthetic or rights-cleared passages;
- repeated sources, missing metadata, multiple rights states, and duplicate text;
- fixed local embedding vectors plus optional pinned real embedding sample;
- exact-term, semantic-paraphrase, filter, tie, empty, and restart queries; and
- known expected top-k/filter behavior.

### Required demonstrations

1. Install/import in the Plan 10 environment.
2. Create persistent store at an explicit temporary/root location.
3. Insert/update is not relied upon for scientific correction; rebuild new index version instead.
4. Close/reopen and retrieve the same passage IDs/ranks within tolerance.
5. Enforce source/rights/topic filters, including missing metadata behavior.
6. Export/inventory every row and validate count/vector dimension/content mapping.
7. Rebuild from the same corpus/config and compare.
8. Corrupt/remove index and prove recovery by rebuild.
9. Measure build/query latency, memory, and bytes.
10. Delete only the disposable test index and prove the authoritative corpus remains.

## Binary selection rule

Select LanceDB if all required demonstrations pass within the ceiling and its adapter remains small.
Otherwise record the failed criterion and evaluate Chroma under the remaining/next bounded spike. If
both embedded databases create disproportionate burden, choose SQLite FTS5 plus exact FAISS/sidecar.

Retrieval quality still decides lexical versus dense versus hybrid use. Passing the storage spike does
not prove vector search improves recall/MRR.

## D-202 evidence record

- candidate versions/licenses and dependency lock;
- environment/hardware/root;
- fixture/corpus and query identities;
- pass/fail for each required demonstration;
- latency/memory/bytes and exact/approximate recall if relevant;
- adapter/code surface and backup/rebuild procedure;
- known limitations/fallback;
- selected tool and reason; and
- effect on Plans 04, 08, 09, and 10.

## Reopen conditions

Reconsider D-202 only if measured corpus scale, metadata filters, query latency, persistence failure,
library support, or portability breaks a requirement. A new popular vector product is not by itself a
reason to migrate.

</details>
