# Local research demo — October 15, 2026

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

## Database recovery blocker

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
XML-Adventure container. Its identity and restart policy (`no`) were inspected; if the restart is
approved, restore that same container afterward. No Docker-wide restart, data deletion, database
reinitialization, full selector or training was performed while that decision was pending.
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

End-to-end retrieval, generated quotation checks, saved-response retry and live database tests
remain pending successful database startup. Do not describe the demo as fully restored yet.
Local operation logs: `outputs/prowl/demo-restore-20261015/` (ignored).

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
