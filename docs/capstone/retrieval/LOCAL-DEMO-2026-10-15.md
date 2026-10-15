# Local research demo — October 15, 2026

**Current status: restored and live-tested.** Quinton approved Docker recovery; Docker Desktop
restart repaired external-drive sharing. The existing PostgreSQL database recovered, XML-Adventure
was restored, and browser search plus all three guided answer questions succeeded. Relevance
evaluation remains open; see the CT scope issue below.

Entry point: http://127.0.0.1:5180/research (also the **Research evidence** navigation button).
This page reuses the real research/answer panels without selecting or loading an imaging case.
It offers three fixed questions over the existing two-paper collection, not free-form chat.

## Startup repairs

- Align Vite's default with the active demo: loopback 127.0.0.1, port 5180, strict port selection.
  Add exactly that Origin to the existing API allowlist. Foreign origins and other ports remain denied.
- Refresh both PROWL research APIs to load the committed validation repairs and new Origin.
- Start the installed Ollama on loopback with cloud features disabled. The existing qwen3:8b digest
  matches `grounded_answer.py`; no download, model change or training occurred.
- Restart the stale PROWL Vite process with Node 24.21.0. The browser previously failed before
  rendering with `__SERVER_FORWARD_CONSOLE__ is not defined`; refreshed Vite renders correctly.

The initial empty case table was transient during loading: three historical prepared cases later
appeared. Their imaging scores are not new capstone results. The dedicated research entry point
keeps this test independent of those cases and their scan files.

## Initial database recovery blocker (resolved)

The expected external UUID `22750B93-2F3F-499D-87F5-902981BFAB59` is mounted; the existing
database directory and its `pgdata` child are directories on macOS. The checked start passed
resource admission (about 108 GiB internal / 1.9 TiB external free) but Docker refused its bind mount:

```text
invalid mount config for type "bind": stat /host_mnt/Volumes/PROWL-Data/PROWL/scratch/literature/pgvector-direct-01: not a directory
```

A fresh temporary read-only container using the installed pinned image also refused the child mount.
This supports stale Docker external-drive sharing; it does not establish database-file corruption.
Earlier PostgreSQL logs record lost directory access and immediate shutdown after an invalid data
directory lock file. Exit 0 alone must not be interpreted as a clean shutdown.

Requested permission to restart Docker Desktop because it also interrupts the unrelated running
XML-Adventure container. Quinton explicitly approved: "Yes, do whatever you need for docker."
Docker Desktop restart succeeded, and the exact previously running XML-Adventure container
`ac77e4b628e81e1f694a862028616f0d353dfe692b9e266584ca48a34cdbbf9d` was started and verified running.
The normal checked PROWL start then succeeded on the existing data directory, with the dedicated
container healthy. PostgreSQL reported automatic WAL recovery after an interrupted shutdown and
readiness for connections; initialization was skipped because the existing database was present.
No database deletion/rebuild, corpus replay, model download, full selector or training occurred.
Canonical frozen batches and original database files remain preserved.

## Checks completed before database recovery

- 22 Python HTTP/fixture checks passed: real temporary loopback HTTP requests include exact demo
  Origin acceptance, identical retry, foreign/other-port/null Origin denial and no refused writes.
- 40 UI checks passed; production build passed (existing large-chunk advisory remains).
- Refreshed APIs 8013/8014 return health 200. Empty requests from Origin 5180 return validation 400,
  proving they pass Origin handling rather than the prior 403. Health does not imply backend readiness.
- Ollama's installed Qwen3:8b digest verified. No model inference performed at this stage.
- Browser navigation from the main page reaches `/research`; search while DB is stopped shows
  an explicit unavailable/save-unconfirmed alert and a same-request retry button.

## Recovery and live verification

- Read-only comparison verifies all **274 research-v1 passages across nine batches** against the
  canonical frozen batch files: encoder identity, batch inventory, records, text and float32 vector
  hashes match exactly. No re-embedding or reload was needed. This verifies this retained collection,
  not every PostgreSQL object or a general power-loss guarantee.
- The **four previously skipped live PostgreSQL checks pass** (13 offline cases deselected):
  atomic retry, whole-batch rollback, query encoder isolation and tampered-vector rejection.
  They use unique test collections; research-v1 is unchanged.
- In the actual browser on port 5180, the search that failed while DB was stopped succeeded on
  its same-request retry and returned five real passages. Saved hash and exact retry pass; conflicting
  question reuse returns 409, unexpected fields 400 and foreign Origin 403 through the actual proxy.
- All three guided answers were generated through the actual `/research` page. The server-validated
  quotations, response content hashes and exact saved retries pass. A source link was expanded to
  inspect the cited text, authors, PMID, DOI and source location. Changing questions clears old results.

| Guided question | Saved response ID | Excerpts | Ollama reported duration |
|---|---|---:|---:|
| Radiomics | `1892ad24-9b37-47a2-becc-dfbb37b61fb1` | 3 | 10.77 s |
| EUS cystic lesions | `38b7cf40-406e-475b-b610-668079b5ed65` | 2 | 14.22 s |
| CT detection | `3eaeae11-fbdd-4397-8c97-4f6279996a67` | 3 | 11.17 s |

These are observed model durations, not full end-to-end latency benchmarks. Search response ID:
`25107689-241d-46cd-a5fa-ec34f12b78d0`. Exact answer retries took approximately 1.5–2.5 ms through
the local proxy and returned the original payload without generation. One earlier retry probe
overlapped EUS generation and received the existing busy 503; retry after the worker was idle passed.
The current store serializes even saved POST retries; GET remains readable. Short browser-tool waits
also expired before generation finished; later inspection confirmed completed saved answers, rather
than treating the wait timeout as an application failure or resubmitting the request.

**Quality limit retained:** the CT answer's third excerpt concerns PET/CT neuroendocrine tumors.
Exact quotation matching passes, but modality/subtype relevance still needs evaluation. No prompt,
ranking, model or question policy was changed to make this smoke check pass. These three familiar
questions are development checks, not a held-out quality score or a complete refusal evaluation.

Local evidence under `outputs/prowl/demo-restore-20261015/` (ignored): `database-verification.json`,
`live-search-check.json`, `live-answer-checks.json`, service logs, the initial database-start error,
`research-db-unavailable.jpg` and `research-restored.jpg`. Original response artifacts remain in their
existing immutable response stores. The research page is left open with a completed answer.

Services at handback: healthy PROWL DB on 55433, retrieval API 8013, answer API 8014, installed Ollama
on 11434 and Vite on 5180, all bound to loopback on the host. XML-Adventure is running again with
its prior configuration. No human-hours credit is inferred from service/test runtime.

## Normal operation

From the repository root, with the correct drive mounted and Docker Desktop running:

```sh
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json start
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 ollama serve
.venv-retrieval/bin/python scripts/serve_research_evidence.py
.venv-retrieval/bin/python scripts/serve_research_evidence.py --answers
```

Each long-running service needs its own terminal; check ports/process identities first to avoid
duplicates. In `ui/`, use Node 24.21.0 and `npm run dev -- --open false`, then open the research URL.
The currently running services need no second launch. Stop the PROWL APIs and dedicated database
before ejecting the external drive; leave unrelated containers and services alone.

This is a local development demo. Static hosting has no research backend. Next quality work remains
a frozen development question/evidence baseline, separate from final held-out evaluation.
