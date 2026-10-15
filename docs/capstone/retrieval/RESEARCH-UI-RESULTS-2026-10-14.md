# Guided research retrieval interface — October 14

Delivered: a separate Research passage search panel in the review workspace connects to the
real research-v1 pgvector collection. Two fixed research question IDs are accepted; no patient
context, arbitrary prompt, or diagnosis request is transmitted. Five exact-cosine results show
source excerpts, paper title/authors/year, PMID/DOI, PMC link, attribution, retained-snapshot
notice scope and normalized character locations. Similarity is explicitly not an answer or
support verdict. The earlier synthetic fixture remains separately labelled and unchanged.

The loopback API uses port 8013. Vite forwards /research-evidence to it. One durable JSON
snapshot is saved per UUID; retry returns the original snapshot, conflicting reuse returns409,
private/additional fields return400, foreign Origin returns403, and retrieval/storage failures
return503. Concurrent searches are refused as busy rather than queued on the encoder. Browser
requests time out after45seconds and preserve the request ID for retry. No generated claims or
LLM are connected. Backend SQL has its existing30second timeout. Saved responses remain readable
without repeating a search; a service restart still requires the drive and pinned encoder.

Run from the repository root with the drive mounted and literature database running:

```sh
.venv-retrieval/bin/python scripts/serve_research_evidence.py
```

Then use the local Vite UI with Node24.21.0. Open Research passage search and select Search and
save passages. This is local development integration; a static deployed site has no such backend.
The API is currently running in owned session12366. Stop it and the dedicated database before
ejecting the drive. Responses are under outputs/prowl/research-evidence/responses/ (ignored).

Verification:18Python tests (new store plus fixture regressions),7existing panel unit tests,
2Chromium scenarios (existing fixture and actual live research service/database), production
build and git diff whitespace check passed. Live browser coverage includes both guided questions,
citation rendering, saved GET/exact retry, conflict/private-input/foreign-Origin refusal, and
service failure with stale results removed. Screenshot retained at
outputs/prowl/testing/ui-browser/research-evidence-live-res-e2a9c-ions-offline-stays-explicit/research-live.png.
The browser harness uses a synthetic viewer without patient arrays and the actual research API.
First unit invocation used shell Node20 and failed in jsdom before tests; rerun using the
repository's pinned Node24 passed. Build retains existing large-bundle advisories.

Next review: grounded generation using retrieved passages, explicit citations and abstention.
Retrieval alone does not establish clinical validity, relevant-answer coverage or large-corpus
performance. Full-catalog selection stays paused; no training or human-hour credit.
