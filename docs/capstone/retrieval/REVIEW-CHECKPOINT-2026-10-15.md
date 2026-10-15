# DAG/RAG review and Git checkpoint — October 15, 2026

Quinton requested review and preservation of the accumulated October 14 implementation.
This checkpoint owns literature ingestion, guided retrieval, extractive answers and their UI.
Training/PANORAMA execution remains in the other chat. The full selector stays parked.

## Reviewed scope

Two coherent units preserve the existing work:

1. Direct CC BY 4.0 JATS ingestion, pinned MiniLM descriptor, immutable vector batches,
   transactional pgvector publication, dedicated Compose configuration, CLI, tests and delivery notes.
2. Guided query facets/fusion, exact-quotation answers, immutable response storage, loopback API,
   separate research/answer UI panels, tests and handoff/review notes.

Only explicit source/config/test/documentation paths are staged. Private configuration, credentials,
article text, vectors, model weights, runtime outputs and build products remain excluded.
Historical October 14 reports describe their producing runs; their service statements are not current
health guarantees. The approved proposal v3.8 and appendix v3.1 hashes were verified during takeover.

## Findings corrected before checkpoint

- A model API returning a JSON list, null or string caused an uncaught AttributeError instead of
  rejected-generation abstention. Validate the envelope before accessing fields; retain its output
  hash and report no duration when the envelope is not an object.
- ResearchStore previously wrote a generated answer before its readback validated quotations.
  Invalid output could leave an immutable file that made every retry fail. Validate the answer before
  publication; a failed validation leaves the request ID available for a corrected retry.

Four new regression cases reproduced these failures against the original implementation, then
passed after repair. Existing saved responses are untouched; retrieval/model/prompt policy is unchanged.
These fixes strengthen failure handling, not semantic relevance or clinical correctness.

## Verification performed here

- Initial focused Python suite: **44 passed, 4 skipped**.
- After the four regression cases and repairs: **48 passed, 4 skipped** (0.18 seconds).
  Includes direct ingestion, guided retrieval, answer validation, response storage and fixture regression.
  All four skips require an explicit live database configuration; no database tests were represented
  as passing or dispatched against the stopped service.
- Existing UI unit suite: **37 passed across 4 files** using Node 24.21.0.
- Additional research-panel suite: **3 passed** covering both modes' identical-request retry and an
  invented quotation rejected by the response adapter. Combined distinct UI checks: **40**.
- Production build passed with the existing large-chunk advisory.
- Whitespace checks passed. No installs, downloads, embeddings, generation, patient reads, selector
  or training execution occurred. No live browser checks were rerun in this checkpoint.

Commands from the repository root (UI commands run in `ui/` with Node 24.21.0 on PATH):

```sh
env -u PROWL_TEST_INGESTION_CONFIG PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv-retrieval/bin/python -m pytest -q -p no:cacheprovider \
  tests/retrieval/test_direct_ingestion.py tests/retrieval/test_guided_retrieval.py \
  tests/retrieval/test_grounded_answer.py tests/retrieval/test_guided_research.py \
  tests/test_guided_evidence_fixture.py
npm run test:run
npm run test:run -- tests/ResearchEvidencePanel.test.jsx
npm run build
```

## Explicit remaining work

Takeover checks found the correct external UUID mounted; APIs 8013/8014 and UI 5180 responded.
The literature database was stopped, Ollama 11434 refused connection, and a request with UI Origin
5180 returned 403. This checkpoint leaves service state and Origin policy unchanged. Running API
processes still hold the previously loaded Python code until deliberately refreshed.

Next: restore and verify the local demo, then freeze a small development question/evidence set before
tuning. Measure relevance, citation support, refusal and latency; preserve failures and keep final
held-out evaluation separate. Three fixed questions over two papers and exact quotation checks do
not yet fulfill the proposal's finding-aware summary workflow or broader restartable DAG.

Other review limits: source size is checked after reading a file; the current ingestion deadline is
cooperative, and storage checks are admission checks rather than hard quotas. Saved-response reads
depend on the current question catalog wording. These limitations need attention before broader
ingestion or catalog evolution; this checkpoint does not claim production hardening.

Git commit identities and publication outcome are recorded on the existing
[W02-08 Trello card](https://trello.com/c/nqTumUtb). A Git checkpoint preserves code and reports;
it does not back up the ignored corpus/model/runtime artifacts or close feature acceptance.
