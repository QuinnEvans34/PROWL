# Local answer failure and latency repair

October 17, 2026 — reported-question repair verified; general answer quality remains open.

Quinton reported waiting over two minutes and receiving the generic checked-answer failure. The
visible question was “What does the pancreas do?” The database returned relevant evidence. A fresh
v5 reproduction failed after 6.888 seconds because the numeric guard treated the2 in `[P2]` as a factual
number. The original request's precise cause cannot be recovered: runtime does not save queries,
drafts or raw errors. This reproduction establishes a concrete bug, not the original request's trace.

## Changes

- The model selects one or two retrieved source IDs for each paragraph. A source-bound schema and
  independent runtime validation reject foreign IDs and model-supplied quotation fields. Code binds
  each selected ID to its exact full retrieved passage (20–2000 characters). These are source excerpts,
  not prepared answers. The model still writes the answer from the question and retrieved evidence.
- Exact quote membership, numeric checks and range-versus-average checks remain. Only bracketed or
  parenthesized inline source markers bound to that claim's verified citations are removed before
  numeric validation and display. Arbitrary numbers and unbound references are not exempted.
- Source text is presented as literal Unicode. The draft retains reasoning mode; the separate review
  uses concise structured output without extended reasoning, capped at 1536 output tokens. It must
  approve every claim, safety and relevance. Shorter drafting instructions discourage extra facts;
  review instructions explicitly disallow importing familiar facts from uncited sources.
- One 60-second generation budget covers model lookup, drafting and review. Transport timeouts use
  the remaining budget, including incremental body reads; exhausted requests cannot start another
  stage. There are no retries. This is not an independent process watchdog or a guarantee about
  when Ollama stops computation after a connection closes. Retrieval precedes this budget.
- UI shows elapsed time, uses a 90-second client wait limit, and distinguishes timeout, incomplete
  output, support rejection, model unavailability and citation/format failure. Evidence remains
  accessible on generation failure. Raw errors, reasoning and review text are not exposed.
- Health reports the imported policy constant, avoiding stale hardcoded version labels.

## Retained diagnosis

All eight attempts are retained under `outputs/prowl/answer-failure-20261017/`. No automatic
per-request retries were added. Intermediate attempts have raw outcomes; only the final producing
code is separately snapshotted. The original v5 checkpoint and preceding 25 trial records are fixed.

| Attempt | Seconds | Outcome |
|---|---:|---|
| v5 reproduction | 6.888 | Inline citation mistaken for a factual number |
| v6 marker repair | 9.176 | Escaped Unicode in copied quote rejected |
| Unicode source presentation | 60.002 | Draft completed; extended review timed out |
| Concise review | 12.598 | Reviewer rejected an unsupported part of a paragraph |
| Focused draft instructions | 8.703 | Model removed embedded reference text from a quote |
| Quote-choice schema | 8.742 | Duplicate source references rejected |
| Source-ID selection | 9.091 | Mechanical/model pass; agent rejected extra insulin detail absent from selected citations |
| Final concise draft and stricter review | 7.336 | Short supported response; jargon remains |

Twelve diagnostic model calls were attempted, including the timed-out review. The real browser
verification added two model calls. The intermediate false acceptance demonstrates why same-model
review is not independent factual validation. It was not promoted as a quality success.

Citation granularity is now the whole retrieved passage rather than a model-selected substring.
This prevents copying failures, but exact text binding alone does not prove that every part of a
claim is supported. Formal evaluation must still assess claim-level support and relevance.

## Verification and remaining work

94 focused Python tests pass, covering citation binding, marker normalization, unsupported numbers,
Unicode presentation, rejection/privacy, shared deadlines and an actual stalled loopback HTTP
response.41UI tests pass across literature, guided evidence and research workflow panels, including
elapsed feedback, client timeout and distinct failure explanations. Production build passes with
the existing large imaging/compression chunk warning. An initial npm invocation used the wrong
script name; the correct `test:run` command passed.

The live Vite→8016→database→Ollama path returned the same visible question's answer within 6.524 seconds
of submission observation. Source 2 opened the matching paper and exact excerpt; returning to Answer
restored the prose. The answer was short and supported, but retained “exocrine,” “endocrine” and
“duodenum.” Plain-language quality is not accepted. These timings are individual observations, not
a latency guarantee or a frozen evaluation result.

Vite retained a missing-import error while the new configuration was being created. Restarting the
verified PROWL dev server cleared it; earlier console errors remain historical, not erased. Current
owned sessions: backend 99570 on 8016; UI 67009 on 5180. Database, corpus and Ollama were preserved.
Screenshot: `outputs/prowl/answer-failure-20261017/live-fixed-answer.jpg`.

Published records: `configs/evidence/natural-answer-v6.json`,
`configs/evidence/natural-answer-checkpoint-v2.json`, and
`configs/evidence/evaluation/public-exposure-natural-answers-v2.json`. Merge exposure supplements
before protected authoring; no protected content was accessed. No corpus/ranking changes, training,
selector restart, model download, automatic query storage or human-hours credit. AI-04 remains in
progress: broaden source-support/plain-language checks and reconcile the formal evaluation plan.
