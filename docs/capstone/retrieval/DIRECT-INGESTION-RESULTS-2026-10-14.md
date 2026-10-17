# Real passage embeddings and batch publication

## Delivered

The first direct corpus is live in the isolated `prowl-literature` PostgreSQL project on
127.0.0.1:55433, database/user `prowl_literature`, collection `research-v1`.
274 real passages from two CC BY4.0 research papers are stored with384-dimensional normalized
embeddings, citation metadata, exact normalized-text offsets, original-paragraph maps, source
hashes, revision IDs, rights decisions and attribution. Nine independently atomic batches were
published. No full-PubMed selection or global sort was needed. No generation or UI wiring yet.

Sources: PMID35406426/PMC8997008 (quantitative imaging/radiomics review) and
PMID37173876/PMC10177524 (AI in pancreatic cystic lesions/adenocarcinoma review). Exact retained
JATS hashes, URLs and licence links: configs/evidence/direct-source-batch-v1.json. Licence was
read from each local JATS permissions block. Only abstract/body prose is included, excluding
figures, tables, supplementary material and references. No live retraction-status certification;
notice scope is the retained source snapshot. These are development sources already reviewed,
not a held-out evaluation set or representative complete research corpus.

## Encoder and environment

Selected local baseline: sentence-transformers/all-MiniLM-L6-v2, revision
1110a243fdf4706b3f48f1d95db1a4f5529b4d41, Apache2.0. Mean pooling with attention mask,
unit normalization, CPU float32,4threads,256token maximum. Pinned file hashes and configuration
are in configs/evidence/encoder-minilm-v1.json. Model bytes are~87MiB and remain ignored.
Official model card: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2.
This is an initial general-purpose encoder, not a qualified medical-retrieval model.

The separate .venv-retrieval installs transformers4.57.1 and psycopg3.2.10; a local
prowl-foundation.pth points to .venv-prowl/lib/python3.12/site-packages to reuse torch2.13.0
and existing contracts. The foundation environment is unchanged. Installed overlay versions:
requirements/locks/retrieval-overlay-macos-arm64-py312.txt (version snapshot, not a hashed lock).
Recreate with Python3.12 venv, install that overlay file, then add the absolute foundation
site-packages path to a .pth in the new environment. Existing model files load offline with
safetensors and trust_remote_code=False. Changing encoder configuration requires a new collection.

## Behavior and limits

- Existing deterministic paragraph normalization and passage contracts are reused. Sentences pack
  to600characters with one-sentence overlap. One474token sentence exceeded the model limit;
  explicit200character subwindows preserve exact offsets/text under prowl-char-fallback-v1.
  Any remaining over-limit window is rejected, never silently truncated. Source1 yields184passages,
  source2 yields90. Chunking boundaries may cut words in the rare fallback; relevance is unqualified.
- Canonical source bundles and frozen vector batches are written before publication. Artifact
  files are create-if-absent, fsynced and content checked. Interrupted partial files are retained;
  they do not block a fresh attempt. The initial artifact set is~3MiB in ignored outputs.
- One database transaction publishes each batch. Advisory collection locks serialize cooperating
  writers; statement timeout30s/lock timeout5s bound SQL. Queries see only committed batches.
- Exact retry checks row count, all record/text content and float32 vector hashes. It neither
  duplicates nor silently overwrites. Same work with another revision or changed encoder is refused;
  use a new collection. Overlapping batches with different grouping fail on duplicate passage IDs,
  so retain batch size32 for this build. Incremental *new* works can be added to the same collection.
- Each source document is bounded at32MiB; each ingestion invocation defaults300seconds, max1800.
  Max128passages/batch. One source is parsed in memory at a time. SQL/final batch completion can
  exceed a cooperative invocation deadline; no hard process watchdog is claimed.
- Dedicated container:2CPU/2GiB/128PIDs, loopback port only, no automatic restart. Existing
  containers and synthetic qualification data untouched. External volume UUID is checked for
  commands; initial8GiB database ceiling and104GiB internal/408GiB external admission floors remain.
  Size checks are admission checks, not filesystem quotas. No automatic whole-corpus ingestion.
- Search uses the identical pinned encoder, explicit collection and exact cosine ranking. These
  timings on274rows do not establish performance at millions of passages. No small permanent
  corpus-size limit is imposed by the format; expansion requires resource/latency measurements.

## Verification and measurements

17 focused tests passed, including live PostgreSQL retry/atomic rollback, incompatible encoder
rejection, corrupted-vector retry detection, exact locators, missing permissions, entity XML,
source mutation, nonfinite/dimension/norm checks and partial-file retry. No synthetic vectors are
in research-v1; tests use separately named test collections.

First CLI attempt failed before publishing because the caller omitted the descriptor argument.
The call was corrected; its failure log is preserved. Successful first batch published32vectors,
then the continuation reused that batch and published the other8. Ingestion timer after encoder
loading: first batch0.554s; continuation1.804s. These tiny cached-source timings are not throughput
predictions for the full archive.

All9frozen batches replayed idempotently. Rebuilt274records in research-rebuild-check-v1 without
re-embedding and compared full records/text/vector values/hashes exactly. Clean Docker restart
preserved the same inventory. Database~11.1MB including test/rebuild collections. No crash/power-loss
claim beyond the earlier platform trial. Inventory SHA256:
2880ca46149d8841062e193b36018586f020f385a2b5cffbb077c6be02513036.

Two development searches (encoder already loaded): radiomics/CT feature extraction62ms,
top3PMIDs35406426; AI/endoscopic-ultrasound cyst studies8ms, top3PMIDs37173876. Returned passages
have source identifiers and citations. These are smoke checks, not a relevance benchmark or
proof that all retrieved text supports a generated answer.

Evidence: outputs/prowl/direct-ingestion-20261014/{tests-final.txt,first-batch.log,
first-batch-02.log,resume-batches.log,search-results.json,verification.json,environment.txt,batches/}.
The full selector remains parked; no training, generation, independent sampling or hours credit.

## Operations

Local private configuration: infra/retrieval/.env.ingestion.json. It contains paths, not the password;
credential file mode600. Dedicated data: /Volumes/PROWL-Data/PROWL/scratch/literature/pgvector-direct-01.
Keep the drive attached while the service runs. Stop this project before ejecting; unrelated
PostgreSQL containers must not be stopped.

```sh
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json start
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json stop
```

Search from the repository root:

```sh
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json search --collection research-v1 --question 'What is radiomics and how are quantitative features extracted from pancreatic CT images?' --k 3
```

Add reviewed CC BY4.0 JATS snapshots using `ingest --sources PATH1 PATH2 --artifacts ARTIFACT_DIR
--collection research-v1 --batch-size 32`. Use the same artifact directory to reuse frozen batches.
`--max-batches 1` demonstrates a bounded stop. `load --batches FILE1 FILE2 --collection NEW_NAME`
rebuilds directly from frozen artifacts without loading the embedding model. Each published batch
is immediately searchable. Missing or unsupported permissions fail explicitly. The initial adapter
is JATS-only; arbitrary PubMed abstract ingestion requires a separate explicit text-use decision.

Next deliverable: expose these actual search results through the guided evidence interface, then
add grounded generation. Existing fixture responses remain explicitly labelled until that integration.
