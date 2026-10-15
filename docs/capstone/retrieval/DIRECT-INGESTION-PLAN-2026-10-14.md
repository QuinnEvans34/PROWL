# Direct vector ingestion: revised delivery path

Quinton selected proceeding without the global topic-selection gate on October14. This supersedes
full selector completion as a prerequisite in PGVECTOR-IMPLEMENTATION-PLAN-2026-10-12.md.
It does not mean that all41million records are embedded or that the partial selection is complete.

## Parked work

Full selector session46696 intentionally stopped with SIGINT, exit130; Python2142/caffeinate2143
confirmed absent. Checkpoint39,351,230 documents, cursor41,364,357, sequence39,982 preserved.
Receipt: outputs/prowl/selection-launch-r02/parked-direct-ingestion.json. No deletion or restart.
Raw download, reconciled source catalog, processed metadata and original evidence remain available.
The drive remains mounted. No unattended runtime credited as human project hours.

## Delivery path

1. Passage-to-search: reuse the qualified PostgreSQL/pgvector platform and existing passage
   contracts. Select/pin one local embedding encoder, implement batch loading with stable passage
   IDs/citation metadata and a query adapter. Demonstrate actual semantic retrieval, distinguishing
   synthetic contract fixtures from research evidence. No whole-catalog scan as an admission gate.
2. Real text ingestion: stream an explicitly identified collection in bounded resumable batches;
   retain text provenance, usable-text permissions, duplicate/version handling and notices. Publish
   only completed batches. Log records/passages/vectors, throughput and failures. Batch size controls
   execution; it is NOT a permanent corpus-size ceiling. PubMed abstracts are not full articles.
3. Guided question to answer: connect retrieval to one local generation model through the existing
   guided interface. Supply retrieved passages and citations; keep approved evidence-insufficient,
   conflict, scope-refusal and service-failure behavior. Save one response per request. No training.
4. Expansion: continue ingesting as coverage/resource measurements justify. Measure retrieval
   relevance and latency; the prior exact-first configuration is an initial choice, not a claim that
   exact scans meet large-corpus latency. Revisit approximate indexing on actual vectors when needed.

The first deliverable is a repeatable question returning actual database-retrieved passages with
source identifiers. Then add grounded generation and UI integration. Existing fixed answers must
remain clearly identified until replaced by live retrieval/generation.

## Reuse and remaining decisions

Available: PostgreSQL17.10/pgvector0.8.2 synthetic qualification, passage/query/provenance contracts,
guided fixture UI, approved wording, response persistence, downloaded/reconciled PubMed data.
Not yet delivered: production passage loader, selected encoder/real embeddings, live DB adapter,
selected small generation model, grounded generation adapter and real-content relevance evidence.
Next implementation work is encoder/schema/loader/query integration, not more selector tuning.

Read source records directly from the reconciled catalog or reuse saved parsed metadata with its
explicit incomplete-coverage label. Do not blindly embed raw baseline/update files: version and
deletion reconciliation still matters. Compare a bounded real ingestion path before any large job;
removing the selection gate does not remove disk I/O or embedding costs. Do not recreate a full
metadata-selection/export audit before the first searchable batch.

Keep citation provenance and local text-use checks. Defer research sampling/held-out coverage claims
until their original evidence requirements are met; no claim of validated clinical correctness follows.
The broader corpus selection study is parked, not marked completed. No source/policy history rewritten.
