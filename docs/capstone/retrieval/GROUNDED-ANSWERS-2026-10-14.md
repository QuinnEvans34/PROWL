# Local grounded extractive answers — October 14

Delivered: Grounded research answers panel, separate from raw search and synthetic fixture.
The installed Qwen3:8b Q4_K_M model selects up to three quotations from the five real pgvector
results. Server validates every passage ID and exact quote substring before publication. No
model-authored paraphrase is accepted. This is an extractive answer prototype, not a free-form
synthesis engine or a guarantee of truth, completeness, relevance or clinical validity.

Model digest:500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41.
Local Ollama only, localhost11434; model tag/digest checked before each generation. No downloads,
training, cloud calls, arbitrary questions or patient context. Structured schema, nonthinking
mode, temperature0,seed42,8192context,900output-token cap,90second HTTP timeout,5minute keep-alive.
Prompt hash/model identity/output hash are retained in every saved response. Structured-output
API reference: https://docs.ollama.com/capabilities/structured-outputs .

Generation is optional in ResearchStore and uses a separate schema and storage directory, so
old retrieval snapshots remain readable. New requests save one immutable result; retries return
it without another model call. Malformed/truncated output, invented citations and mismatched
quotes produce an explicit rejected-generation abstention. Empty retrieval skips the model.
Model unavailability or identity mismatch returns503 without claiming a save. Model-chosen
insufficient evidence is distinct from output-validation rejection. Existing fixed question
allowlist excludes diagnosis/treatment requests; general out-of-scope free-text routing is not
implemented because free text is not accepted.

Observations retained:
- Original EUS and broad radiomics questions abstained in live tests (about3.5s and1.2s).
  Returned passages did not directly establish the requested specifics. This exposes a remaining
  retrieval-quality gap; no forced answer or relaxed quote validator was introduced.
- Added focused question: How have CT radiomic models been studied for pancreatic cancer detection?
  First live answer returned valid quotations but included an irrelevant MRI example. Retained
  saved response documents this failure. Prompt now explicitly requires matching modality/task.
- Revised live browser check passed with cited quotations and no MRI/treatment-response excerpts.
  This is one development check, not a general relevance guarantee. Model outputs may vary.

Verification:27Python tests including malformed output, citation/quote rejection, model identity
refusal, empty-evidence abstention and saved retry;7existing UI unit tests;3browser scenarios
(answer + retrieval + fixture). After prompt/citation-link edits, answer browser check reran and
passed (11.9s including browser operations), and production build/whitespace check passed.
Earlier schema syntax error was corrected before any inference. Large UI bundle advisory remains.
Browser answer tests use actual Ollama and pgvector with the synthetic viewer/no patient arrays.

Evidence: outputs/prowl/grounded-answer-20261014/live-{eus,radiomics}.json;
outputs/prowl/research-answers/responses/*.json (includes initial MRI relevance failure and revised
answer); outputs/prowl/testing/ui-browser/grounded-answer-*/answer-live.png.

## Run

```sh
.venv-retrieval/bin/python scripts/serve_research_evidence.py --answers
```

Answer API127.0.0.1:8014, owned session70646; retrieval API8013 session1762. Vite proxies both.
Database still uses external drive. Stop both APIs and the dedicated DB before ejecting.
Do not stop unrelated Ollama workloads. The service is local development only; static deployment
has no answer backend. Current UI has three fixed questions; all use research-v1 (274passages).

Next: review these real outputs together, improve retrieval for the two abstaining questions,
and add a small independent relevance/abstention set before expanding to free-form synthesis.
Full-corpus selector stays paused. No machine runtime counted as human hours.
