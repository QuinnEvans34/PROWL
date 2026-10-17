# Live research workflow verification — October 17, 2026

The approved single-question check passed through the real browser, Vite proxy, workflow API,
existing pgvector collection and pinned Qwen3:8B v2 selector. All four stages completed; repeated
same-ID delivery returned the identical saved answer without another model call. This qualifies
this integration path, not semantic answer quality, full Plan04/G3, or the final expert system.

## Cleanup and service recovery

Quinton explicitly approved deletion after the cache review. Fresh inspection matched exactly
37 private, immutable, reclaimable build-cache records. An anchored ID allowlist deleted those
records only; Docker reported9.162GB freed, with34 shared records remaining. Container, image
and volume inventories were unchanged. Npm cache and database stores were untouched.

Host free space recovered asynchronously from approximately96.08GiB to105.46GiB. The normal
104GiB internal/408GiB external admission remained enforced and passed. Docker then reported
the recurring external-drive bind error, despite the directory and correct drive UUID existing.
An authorized Docker Desktop restart repaired sharing; the exact previously running XML-Adventure
container was restored, and PROWL's checked database startup succeeded. No reinitialization,
re-embedding or corpus replay occurred. Historical storage-review evidence remains intact.

Current services: database55433, workflow8015, Ollama11434 and UI5180 running. Old retrieval8013
and answer8014 APIs remain offline; the new workflow does not depend on them. Their older panels
remain visible in the standalone page but require those services if used. Stop PROWL APIs/database
before disconnecting the external drive. Service state is a point-in-time observation.

## Browser integration and verification

The standalone `/research` route was missing the workflow panel already available in the case
workspace. Added the existing panel there; no model, prompt, corpus or workflow-engine change.
The visible browser ran the radiomics guided question exactly once, without a scan or patient data.

- Run ID: `2c31c846-0843-42e3-b31f-35d2d6b23343`.
- Retrieve/select/validate/save all complete;8 hash-chained events;5 retrieved passages,3 exact quotes.
- Stage-journal elapsed10.890196seconds; one model call. Ollama HTTP duration10.02102175seconds.
  These are single smoke observations, not latency benchmarks.
- Model remains `qwen3:8b`, digest500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41,
  policy `verified-extracts-v2`. Ollama log confirms completion and all slots idle.
- Same-ID POST through the real5180 proxy and repeated GET returned identical run/response objects.
  All immutable artifact bytes and event count stayed fixed; the chat-call count increased by
  exactly one from the pre-call baseline and did not increase during reuse verification.
- Response SHA256: `6d04588993c8f5e3db20f5917142f1bf3ad7bcd3efa67673e17b34eb1ad0c523`.
- Read-only before/after comparison:274passages/9batches, identical record/text/vector/encoder hashes.
  All row/rights/text checks and actual stored-vector hashes validate. No collection mutation.
- Browser visibly displayed the final stages, cited quotations and download links. Screenshot
  retained locally. Production build passed using existing Node24.21.0; existing chunk-size advisory.

Manual relevance review: definition and workflow excerpts address the question; the intervening
pancreatic-cancer appearance/application excerpt is loosely related and unnecessary. Exact-quote
validation does not solve selection relevance. No quality promotion or fresh suite score is claimed.

## Evidence and limitations

Local evidence is under `outputs/prowl/workflow-live-20261017/`: approved cache allowlist and prune
receipt, unchanged inventories, Docker recovery logs, before/after DB fingerprints, call baseline,
`live-verification.json`, and `browser-completed.png`. Immutable actual run artifacts remain under
`outputs/prowl/research-workflow/` with that run ID. Article/model text and runtime artifacts stay local.

Retained diagnostic failures: startup's wrapper initially hid Docker stderr; a bytes/text log-writing
mismatch interrupted the first capture. Corrected capture exposed the mount failure. Read-only DB
verification initially rejected SQL tuples, then normalized JSON. Final comparison initially wrapped
the encoder row in an extra list; matching the original single-row shape restored the identical
fingerprint. These were probe defects, not database drift; no additional inference followed them.

Next: exercise explicit interruption/recovery against the real service using retained or synthetic
outputs and controlled faults before extending workflow scope. Keep model-quality work separate:
relevance/study mixing remains unresolved. No automatic retries, model sweep, full selector,
training, human-hours credit or final expert-system acceptance follows from this check.
