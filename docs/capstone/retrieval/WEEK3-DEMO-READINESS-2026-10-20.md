# Week 3 demo readiness — October 20, 2026

**Outcome:** local demo restored; one real answer and citation navigation verified.\
**Card:** [W03-02](https://trello.com/c/KCcUA5kn). Startup/integration repair, not a new answer policy.

## Recovery and findings

At17:42UTC, UI5180/API8016/Ollama11434/DB55433 refused connections; PROWL-Data was unmounted.
Quinton reconnected it. UUID `22750B93-2F3F-499D-87F5-902981BFAB59` matched the configuration;
existing data/pgdata directories and unchanged 104GiB internal/408GiB external floors passed.

Two checked starts failed before PostgreSQL started. The first CLI swallowed Compose stderr;
the second exposed `stat /host_mnt/Volumes/PROWL-Data/PROWL/scratch/literature/pgvector-direct-01:
not a directory`. Docker Desktop restart repaired access. XML-Adventure, the only previously
running container, was restored with its existing configuration. Checked PROWL startup succeeded.
PostgreSQL skipped initialization, recovered the existing database automatically and became healthy.

October19 logs show lost directory access (`pg_filenode.map`, bad descriptors, invalid
`postmaster.pid`) before shutdown. This supports a storage-access failure for that shutdown,
not a proven explanation of the earlier October18 backend exit-code-2 events.
No database deletion/reinitialization, ingestion or image/model download occurred.
Ollama's own startup log reported removal of two unused blobs; no manual model cleanup was run.
Both installed Qwen models remain listed; selected qwen3:8b digest matches the pinned configuration.

## UI repair and checks

Vite initially rejected public evidence JSON imports outside its `ui/` root. The production build
alone had not established dev-server access. `ui/vite.config.js` now permits exactly the ten public
JSON contracts imported by UI components, plus the UI root, without allowing the whole repository.

- Ten contract URLs return200; repository `README.md` outside the allowlist returns403.
- API8016 and UI5180 proxy report `source-record-answer-v1`, `source-linked-record-search-v1`,
  collection `research-disease-v1`. Startup validates the canonical inventory.
- 50 existing AskPanel/LiteratureSearchPanel tests pass; production build passes with its existing
  large-chunk advisory.
- Actual browser renders the redesigned Research page and answer/source controls.

Asked once in the browser: “What additional findings help distinguish inflammation from a pancreatic
tumor?” The UI displayed local AI composition, four paragraphs and seven passage citations.
Scope, MRCP identity, calcification/duct context, no-single-feature qualification, focal-AIP
portal-venous CT/duct/atrophy details and individual-diagnosis limits remained visible.
Citation6 opened the matching Schima2020 passage, body-20, characters16475–16928. Its phase,
duct and atrophy statements match the associated paragraph. Returned to Answer afterward.

One Ollama `/api/chat` call returned200 in **9.870seconds**, including model load. This is the
model endpoint's observation, not end-to-end timing or a latency benchmark. No retries or sweep.
This is one known integration question and one manually opened source, not full quality or
independent acceptance. Existing exact UI answer validation passed.

Local evidence: `outputs/prowl/week3-readiness-20261020/readiness.json`, `restored-answer.png`,
`database-log.txt`. The receipt binds the changed Vite config hash. Answer remains visible.

## Current operation

After checking ports and drive identity, use separate terminals from the repository:

```sh
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json start
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 ollama serve
.venv-retrieval/bin/python scripts/serve_literature_search.py --record-answers
```

From `ui/`, select `.nvmrc`'s Node version and run `npm run dev -- --open false`. Check
`/literature-search/health` on8016 and through5180. Old guided services8013/8014/8015 are unnecessary
for the current literature page. Do not start duplicates. Current owned sessions: Ollama3015,
API2188, Vite29391. Existing `prowl-literature-db-1` is healthy on loopback55433.

Before disconnecting the drive, stop the literature API and run the checked
`direct_corpus.py --config infra/retrieval/.env.ingestion.json stop` command. Leave unrelated
containers alone. A remount bind error requires checking the host directory/UUID, never creating
a replacement database directory. Docker restart affects other containers: inventory and restore
their prior state, as done here under Quinton's existing Docker authorization.

W03-02 remains open for the earlier unexplained backend exits and final recovery closeout.
Offline W03-03 volume-adapter preparation can proceed; W03-04/05 then qualify wording and quality
before replacement promotion. No patient arrays, training, full selector or protected evaluation
was accessed; no human-time credit is inferred.
