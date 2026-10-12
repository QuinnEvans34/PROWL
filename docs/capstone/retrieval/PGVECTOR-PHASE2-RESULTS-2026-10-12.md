# Phase 2 platform trial: results and configuration decision

Status: exact-first platform engineering checks complete; ready for Quinton's phase review.
Quinton selected exact search and deferred optimization. HNSW remains rejected for promotion under
the unchanged restrictive-filter recall requirement. No real-corpus ingestion is claimed.

## Exact-first closeout

The client benchmark uses a materialized relation of IDs, exact distances and lexical scores, so
approximate HNSW cannot determine its nearest neighbors. All 80 dense result sets match the saved
exact reference. Lexical and dense branches share the same eligible set.

| Client measurement | p95 |
|---|---:|
| Broad exact hybrid | 205.33 ms |
| Restrictive exact hybrid | 93.26 ms |
| Five eligible passages | 72.63 ms |
| Empty eligible set | 94.06 ms |
| Broad exact hybrid during synthetic GPU work | 210.63 ms |

These round trips include Docker exec, a fresh psql connection, SQL execution and JSON delivery.
They do not include a future application/API or query embedding model. Each nonconcurrent scope
has 20 samples; p95 uses the nearest-rank method. All measurements are below 500 ms.

Synthetic GPU check: three baseline/concurrent/baseline pairs, each window at least three seconds,
1024x1024 float32 matrix multiplications, MPS synchronized every ten operations, Torch 2.13.0.
The median concurrent rate was 1.73% lower than the median paired baseline, within the 10% bar.
This is a short synthetic coexistence check, not evidence about training throughput, sustained thermal
behavior or clinical model performance. No model weights, patient arrays or optimizer were used.

The successful bounded run finished in 39.47 seconds and confirmed container shutdown. Evidence:
`outputs/prowl/pgvector-phase2-20261012/exact-coexistence-02/`, including source snapshots.

The preceding `exact-coexistence-01` attempt is retained: it measured broad p95 1115.87 ms and then
failed before the concurrent GPU window because a local variable shadowed the `concurrent` module.
Its database shutdown succeeded. The corrected query projects only IDs/scores into its temporary
relation instead of carrying full vectors/text; the variable collision was repaired. Thresholds,
dataset, scopes and exact-search reference stayed fixed. 29 model-free platform tests now pass.

**Next phase:** W02-06 journal selection. W02-08 stays open for the later contract-bound real-corpus
database/embedding work. Recheck latency and memory with the actual encoder dimension and corpus
before scaling; retain failed approximate-index evidence for later optimization.

## What ran

100,000 synthetic passages, deterministic 128-dimensional vectors, 20 independent synthetic queries
in each of four eligibility scopes (80 measurements). These are generated mathematical vectors,
not article embeddings or a relevance evaluation. PostgreSQL 17.10 / pgvector 0.8.2 on ARM64,
default HNSW build/search settings, followed by strict-order iterative scanning; exact eligible
search supplies the recall reference. Lexical control uses English PostgreSQL FTS `ts_rank_cd`.

The combined search measurement uses exact dense search and lexical reciprocal-rank fusion with
constant 60. SQL assertions verified hybrid result counts and absence of forbidden rows.

| Scope | Eligible rows | Default HNSW mean recall@10 | Iterative mean recall@10 | Exact hybrid p95 |
|---|---:|---:|---:|---:|
| Broad | 90,000 | 100% | 100% | 49.18 ms |
| Restrictive bucket | 1,000 | 4% | 74.5% | 27.53 ms |
| Fewer than k | 5 | 100% of 5 | 100% of 5 | 16.45 ms |
| Empty | 0 | Correct empty | Correct empty | 21.60 ms |

The empty case uses recall=1 as a bookkeeping convention, not retrieval evidence. Timings are
server-side SQL execution on this workload, excluding client/UI/network time. They do not qualify
end-to-end latency or future encoder dimensions/corpus sizes.

All 20 restrictive queries under-returned with default HNSW. Iterative search returned ten for
every query but still missed exact neighbors (worst recall 50%). Therefore, checking only the
number of returned passages is insufficient to establish approximate-search quality.

## Persistence and resources

- Prior small smoke passed search, constraints, clean restart and process-crash recovery.
- This run dumped the 100k dataset and restored it into a **separate container with a separate
  external data directory**. Source was stopped before starting the restore instance.
- Sorted inventories compare every ID, bucket, permission, text hash and serialized-vector checksum.
  Both inventories have SHA256 `020bb3445f5da899c77e19f782c00db2071f0718010d52a753fd6596e8cb5c0c`.
- The bounded qualification finished in 85.74 seconds. Sampled combined external trial storage was
  about 0.75 GiB including source, restore and dump, below 8 GiB. Memory was capped at 2 GiB/container;
  Docker VM allocation remained 8,317,267,968 bytes, below the 15% host-memory bar.
- Internal free space remained about 126.4 GiB. The shared Docker runtime and unrelated containers
  were not reconfigured. Both owned qualification containers were confirmed stopped; retained
  containers/data are intentional, not running services.
- HNSW construction exceeded default maintenance memory at 52,687 rows; PostgreSQL completed the
  build using its normal spill behavior. No tuning or memory increase was applied.

The first helper preflight reports the preserved earlier smoke container as an existing-instance
refusal. The qualification harness admits only that expected condition after verifying it is stopped,
then verifies both new project names are unused. It never overwrites or restarts the old smoke instance.

## Configuration decision and scope limits

Use **exact vector search plus keyword search for the first bounded corpus**. It meets the synthetic
latency target here and avoids the observed filtered approximate-search losses. Keep HNSW as a later
measured optimization when the actual corpus/encoder requires it. Quinton accepted this configuration;
the failed HNSW requirement has not been relabeled as passing.

The client-latency and synthetic MPS checks are now recorded above. Higher-dimensional embeddings,
real relevance and production schema validation remain later phases. A process crash/restore does
not establish USB/power-loss durability.

## Evidence and reproduction

- Runner: `scripts/retrieval/qualify_pgvector_platform.py`
- Synthetic SQL: `infra/retrieval/benchmark.sql`
- Immutable local run evidence: `outputs/prowl/pgvector-phase2-20261012/qualification-01/`
  contains SQL output, all 80 measurements, metrics, original/restored inventories, stop results,
  Compose configurations and snapshots of producing source files.
- External data: `/Volumes/PROWL-Data/PROWL/scratch/literature/pgvector-qualification-01/`.
- Current 28 model-free platform tests pass; actual benchmark/restore evidence is separate.

The runner refuses existing qualification projects and existing output/data roots. Preserve these
results; a future trial needs a reviewed fresh identity, not deletion to make a repeat pass.
