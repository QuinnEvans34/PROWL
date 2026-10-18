# Live development literature search

> Later October17 update: [natural-answer development preview](NATURAL-ANSWERS-2026-10-17.md)
> now supplies a separate /answer endpoint and answer-first UI under explicit user authorization.
> The original /query behavior and the source-search observations below are preserved history.

October 17, 2026 — delivered and verified in the local browser. [AI-09](https://trello.com/c/AcXlKWQg).

Quinton explicitly authorizes: “Continue autonomously until I can type a literature question and
inspect real search results in the local UI.” This is a sequencing amendment: an opt-in local
source-search demo comes before final evaluation, without closing core acceptance or permitting
held-out tuning. Existing frozen evaluation criteria and measurement-after-core sequence remain.

Bounded implementation: a general literature question box on /research, a loopback-only service
on port8016, fixed research-disease-v1 corpus and existing exact dense retrieval/top5. No query
expansion/configuration comparison, generated answers, training, full selector or patient inputs.
The indexed14sources/1179passages stay unchanged. Per-request results are ephemeral, not logged or
saved automatically. Existing guided demos remain available.

## Implementation

`development-search-v1.json` pins collection, manifest, corpus, encoder and fixed top5 policy.
The new service verifies source bundles and corpus membership at startup and the database inventory
inside a read-only repeatable-read transaction for each query. Existing MiniLM query embedding and
exact cosine search execute on the entered wording; no expected answers or evaluation labels are
loaded. Every returned record resolves to canonical text, citation, rights and offsets. The existing
reviewed-question adapter still requires its original scope review; the general-library interface
has a separate development policy and internally constructs its own bound retrieval ticket.

HTTP accepts only a small closed JSON request (schema version, UUID, question), with loopback host
and browser-origin checks. One retrieval runs at a time; busy/provider/inventory failures yield a
generic unavailable result. The UI supports loading, cancel, retry, empty results and missing scan
context. Editing a question clears old results and discards an in-flight stale response. Its45-second
client timeout does not kill server work; a new request may remain busy until that work finishes.
Database statements have a30-second timeout; this is not a whole-process watchdog.

## Verification

- Python:127 passed (24new development search,34existing adapter,69routing).
- UI:22 passed (11new search,3existing evidence,8workflow).
- Production build passed; existing imaging/compression chunks exceed the500kB warning threshold.
- Real API through Vite: two literature requests returned five actual passages each; a scan-size
  request returned not_searched/case_context_unavailable. Recorded local elapsed times were0.371s,
  0.354s and0.002s respectively; these are smoke observations, not a latency benchmark.
- Real browser: entered both literature questions, inspected five results, expanded an exact excerpt
  with authors/PMID/source link/license/offsets, verified clearing on edit and missing scan guidance.
  No console errors observed. Screenshot: `outputs/prowl/live-search-20261017/live-search.jpg`.
- Unit checks cover provider failure/retry, cancellation, stale results, no-results, closed inputs,
  foreign/altered evidence, request/corpus/citation mismatch and host/origin refusal. Unavailability
  and retry were fixture-tested; the live database was not deliberately stopped.

The example head-size question returns a general anatomy excerpt first; relevant disease references
also occur in the five results. This is demonstrably real retrieval, not an optimized relevance or
complete-answer claim. No configuration was tuned to these examples. All questions used here and in
tests are exposed development data; the new live-search exposure supplement must join the previous
supplements before protected authoring. No private evaluation content was accessed.

## Local operation

Open http://127.0.0.1:5180/research, type a general pancreatic literature question and select
**Search literature**. Expand any result to inspect the excerpt and source. The existing database,
approved data drive and pinned local embedding model must remain available. Ollama generation is
not used by this feature. No internet search or new source acquisition happens at query time.

From the repository root, if port8016 has no existing owned service:

```sh
.venv-retrieval/bin/python scripts/serve_literature_search.py
```

In a second terminal, if the UI is not already running:

```sh
cd ui
npm run dev -- --open false
```

The local host needs Node on PATH (the Codex bundled Node runtime was used for verification).
Both commands run in the foreground; Ctrl-C stops only the service in that terminal. Do not launch
duplicates or stop other project services. Runtime configuration remains ignored in
`infra/retrieval/.env.ingestion.json`; do not copy credentials into source control. The health route
`/literature-search/health` confirms HTTP service presence, not fresh database readiness; a real query
performs the inventory/storage checks. A restart must pass startup checks again. No startup daemon
or boot persistence was installed. Static production output still needs a server proxy; this delivery
is the local Vite demo, not a hosted deployment.

## Remaining work

Keyword scope checks are a convenience, not a certified semantic privacy/clinical filter. Only
general public-literature questions belong here; there is no attached scan or measured case context.
The original article text can contain technical or clinical statements; displaying it does not
endorse it as current guidance or an answer to the question. Relevance, completeness, source
currentness and disease-answer quality remain unassessed for this search configuration.

Next reconcile disease-label candidates, independent verification and exposure tracking under AI-03,
then freeze evaluation and compare retrieval configurations. Readable cited summaries and viewer
context follow their acceptance gates. The required measurement-aware extension remains after core
acceptance. This delivery closes the requested live-source-search milestone only.


## October 17 reading-view refinement

At Quinton's request, results now open as readable original paragraphs with a separate Sources
button. Numbered source buttons switch views, focus the corresponding citation heading and expand
its exact excerpt. Paper titles, authors, licenses, links and offsets remain inspectable. Each entry
represents a retrieved passage, so multiple entries can belong to the same paper. Changing the
question clears the entire view. This does not generate or simplify the article wording; the
requested concise plain-language answer remains AI-04 work, recorded in spec1.20.

22 focused UI checks and production build pass (existing large-chunk warning). Real browser checked
reading→source1→reading against the user's already displayed general question; no question was
replaced and no extra model/search call was needed. Screenshot: local
`outputs/prowl/live-search-20261017/reading-view.jpg`. Original checkpoint hashes remain historical.
