# Literature workflow and rebuild qualification — October 17, 2026

**Disposition:** Completion-spec Step 3 is complete for the bounded literature adapter. The
two-review corpus rebuilt exactly, changed dependencies fail closed, publication interruptions
preserve history, and literature failure leaves the fixture imaging controls usable. Answer quality
remains unqualified. Broader Plan 04/G3, full imaging orchestration and D-201 remain open.

Quinton's continuation after AI-02 authorizes this implementation and qualification. This preserves
the live `verified-extracts-v2` policy; it adds no generation experiment, training or full selection.

## Runner decision and stage contract

Retain the existing sequential repository `ResearchWorkflow` runner for this literature slice.
It already supplies explicit stage visibility, immutable records, file locks and linked recovery,
with no new framework dependency. This is a scoped engineering decision, not a claim that Prefect
failed its trial: that trial has not run. General D-201 selection, cancellation, cross-workflow
accelerator coordination and full registry/CLI obligations remain separately assessed.

| Stage | Inputs | Published output | Reuse / invalidation |
|---|---|---|---|
| Retrieve | Guided question, catalog hash, collection inventory, pinned encoder, retrieval producer hashes | Validated passage snapshot, bound to request manifest | Only verified successful parent snapshot; no fresh search during reuse |
| Select | Exact passage snapshot, question, model digest, prompt/policy/code identity | Original generation, including rejected output | Rejected or uncommitted selection executes again only in an explicit linked recovery |
| Validate | Selection hash, original passages, validation code | Status and exact selection hash | Revalidated on reads/recovery and rebound to child selection artifact |
| Save | Verified ancestors, new run ID | Immutable response plus save artifact and completion event | Each recovery publishes its own response ID; no global exactly-once claim |

The `prowl-research-workflow-v1` artifact format is preserved. New service manifests add a
`prowl-corpus-inventory-v1` content identity and guided-catalog hash inside `retrieval_identity`.
Inventory covers encoder descriptor identity, batch IDs/counts, source revisions/hashes, every
record hash and verified float32 vector hash. Collection name is excluded from content identity
so a separate rebuild can demonstrate parity. Counts alone cannot establish equivalence.

| Changed dependency | Required behavior |
|---|---|
| Corpus membership, text, rights, citation, revision, vector or batch inventory | Running service refuses fresh retrieval; restart pins the new inventory; old recovery binding no longer matches |
| Encoder descriptor/bytes, guided catalog/facets or retrieval code | Restart and new request; incompatible collection encoder refused |
| Question, generation model/digest, prompt, response policy or producing code | New request; recovery under a different binding refused |
| Existing request ID | Read its verified original snapshot; never silently refresh or regenerate |
| Missing/corrupt completed artifact | Refuse read/recovery; preserve evidence, do not substitute current DB contents |

Invalidation is deliberately conservative across the whole binding. Selective reuse across code
or configuration migrations is not implemented. Historical completed responses remain readable;
failed attempts produced before this code change cannot be resumed under the new producer identity.
They require a new request, with the old attempt retained.

Inventory and all guided-search facets execute in one PostgreSQL repeatable-read, read-only
transaction. Concurrent ingestion therefore cannot mix two corpus states within a new response.
After retrieval, later stages operate on that saved snapshot, not a changing database.

## Admission and failure behavior

The production service checks the existing registered external volume/configuration and storage
limits at startup, before a new attempt and before each executing stage. The unchanged limits are
104 GiB internal free and 408 GiB external free, including existing reservations. Storage refusal
before selection prevents generation. Existing-ID reads bypass admission and remain available
when DB/Ollama is down, provided the saved local artifacts remain accessible and valid.

Startup now needs the configured DB to establish corpus identity; a running service can still read
saved responses after DB loss. A failed retrieval or model call is unavailable, not a successful
insufficient-evidence answer. No automatic retry is introduced. File locks still serialize only this
workflow directory; they are not a machine-wide GPU scheduler.

Inventory is explicitly limited to 4,096 passages / 256 batches. This qualifies the present small
corpus; expansion beyond it requires a measured bounded implementation change. Rebuild files are
limited to 8 MiB per batch / 32 MiB per source bundle and 64 MiB per input group. Rebuild admission
retains the 8 GiB database cap, 300-second cooperative budget and existing storage floors.

## Rebuild and recovery procedure

`scripts/retrieval/rebuild_corpus.py` accepts explicit retained canonical source bundles and frozen
embedding batches. It validates every batch and binds rows to source representations, exact locators,
rights and citations before loading. Source bundles and frozen embeddings are authoritative inputs;
this rebuild does not redownload articles or re-embed passages.

From the repository root, with the configured drive/database available:

```sh
.venv-retrieval/bin/python scripts/retrieval/rebuild_corpus.py \
  --batches outputs/prowl/direct-ingestion-20261014/batches/*.batch.json \
  --bundles outputs/prowl/direct-ingestion-20261014/batches/rev-*.json \
  --reference research-v1 --destination research-rebuild-NEW-ID \
  --output outputs/prowl/rebuild-NEW-ATTEMPT --verify-guided-queries
```

Choose a new destination for a fresh rebuild. The command records exact input file hashes in
`plan.json`, compares the reference against the complete canonical inventory, then uses the existing
atomic batch loader. Completion is written last after count/content parity and optional query parity.
For an interrupted rebuild, keep the same inputs/destination and choose a **new receipt directory**.
Existing batches are verified and reused; incomplete transactions cannot appear published. Missing
canonical members, changed embeddings and unexpected destination contents refuse completion. Neither
the original collection nor earlier attempt records are overwritten or deleted.

## Results and limits

- **63 Python checks passed:** 57 corpus/workflow/HTTP/restart checks, four production-service wiring
  checks and two rebuild checks (one real PostgreSQL interruption/recovery scenario). The initial
  57-check invocation had 52 passes and five failures from tuple serialization in the new inventory;
  replacing tuple pairs with JSON objects resolved it. That failure is retained, not counted as a pass.
- Four new interruption cases stop after each stage artifact but before its completion event. Only
  completed ancestors are reused. Orphan artifacts remain intact. An uncommitted selection may need
  another generation in a later explicit recovery; the tests use synthetic callbacks only.
- Missing artifacts, all seven changed-dependency classes, unavailable DB, admission refusal before
  work, and a storage drop after retrieval passed. Existing controlled HTTP SIGKILL recovery passed
  again because the workflow implementation changed; source-model calls remained zero.
- The real synthetic rebuild interrupted immediately after the first batch committed. The second
  attempt verified/reused that batch and loaded the second. The first plan stayed byte-identical.
  Missing-member and corrupt-file checks refused completion. Four synthetic rows across two isolated
  fixture collections are retained; neither contains patient data.
- **Three imaging component checks passed**, including a new literature-service failure case. The
  fixture viewer, 2D/3D control and scan-library control remain usable. This checks UI isolation, not
  real CT rendering or the broader imaging pipeline.
- Real rebuild `research-workflow-rebuild-20261017`: **274 passages, nine batches, two sources**, in
  **3.901734 seconds** including pinned CPU query-encoder setup. All three guided questions match
  complete returned records, ranking, scores and retrieval metadata exactly. There were zero passage
  embedding calls and zero generative model calls; query facets were embedded once and reused for
  both collections. [Public result](../../../configs/evidence/corpus-rebuild-v1-review.json).
- Canonical/reference/rebuild inventory SHA256:
  `415ca84294b21864c1a12c1a24effec3fd99b3f64be04576cf35c41cd400acc9`.
  This versioned digest differs in format from the older October 14 inventory checksum; it is not
  evidence of a corpus change. Original `research-v1` remained identical before/after.
- The verified idle workflow process was restarted with the new code. Workflow8015, UI5180 and
  Ollama11434 returned200 afterward; an existing saved response remained exactly equal through HTTP.
  DB grew from11,245,235 to12,793,523 bytes including the retained rebuild/fixture collections.
  Internal free space was113,180,966,912 bytes at postflight. No other service was stopped.

Private evidence: `outputs/prowl/workflow-closure-20261017/` contains the qualification plan,
pre/postflight, producing source copies/hashes, rebuild plan/receipts/completion, retained synthetic
interruption attempts, test reports and service log. The rebuilt collection is retained, not promoted.
The source corpus, live answer policy and frozen acceptance rubric are unchanged. No human hours
are inferred. Power-loss durability, all crash timings and global exactly-once publication remain
unproven; final Step 9 rechecks the affected integration paths.

**Next: Step 4 — coverage review and a bounded corpus freeze.** Identify missing information needs
before choosing additional permitted sources. The full selector stays parked and the answer-quality
gate remains open for Step 7.
