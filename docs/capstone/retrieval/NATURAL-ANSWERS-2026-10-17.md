# Natural local literature answers

October 17, 2026 — local development synthesis implemented; formal quality acceptance remains open.

Quinton explicitly requests that the local AI take retrieved evidence and formulate a human-readable
answer. This authorizes a new development synthesis path before final evaluation, superseding the
prior no-generation sequencing for this local demo only. Frozen acceptance thresholds, prior failed
experiments, protected evaluation and required measurement extension remain intact. No training,
full selector, new model download, new corpus or retrieval tuning.

Planned bounded policy: installed pinned Qwen3:30b, unchanged dense top5; one structured draft and
one separate source-support review, up to60 seconds each, no automatic retries. Each paragraph must
cite a retrieved passage with an exact supporting quote. Reject malformed/foreign/missing citations,
unsupported review outcomes and truncated outputs. The same-model review is not independent clinical
validation. Failures retain source access and are distinct from insufficient evidence. No runtime
query/answer persistence. Development smoke questions and retained outputs are exposed material.

## Delivered development contract

`POST /literature-search/answer` preserves the closed request and canonical retrieval bindings,
then uses `natural-literature-answer-v5` with installed Qwen3:30b (pinned digest), reasoning enabled,
8,192 context,4,096 output-token cap, temperature0/seed42. Each request permits at most one draft
and one review; no automatic regeneration. Existing `/query` stays excerpts-only. The new response
version distinguishes completed, unavailable and not-called generation. `summarized` means a
validated development summary, not proof of a complete answer. Empty claims earn an insufficient
state only after review; provider/format/support-check failures instead retain evidence with no answer.

Every paragraph cites one or two actual retrieved ranks and a verbatim quote. Deterministic checks
reject foreign/altered quotes, unsupported numeric tokens, average/mean terminology absent from cited
quotes, malformed output and truncated generation. A separate model review checks only displayed
claims, with exact cardinality and strict booleans. The model receives general question/public source
text only, no local request ID, case data, gold answers or evaluation labels. It has no tools. Raw
reasoning/grounding/review content is never returned to the UI. Runtime does not persist prompts,
answers or refused input. Deliberately retained development trials are a separate verification activity.

UI defaults to Answer, with paragraph citation buttons opening the existing source view. Original
passages remain under Read passages. The client validates request/corpus/model/policy/prompt identity,
citation rank and quote containment before rendering plain escaped React text. Editing/cancel clears
old state. Client timeout is165seconds; each model HTTP call has60-second socket timeout and the DB
has30-second statement timeout. These are not an end-to-end process watchdog; browser cancellation
stops display/waiting and may leave the server finishing its bounded request. One answer request is
admitted at a time; the model uses a2-minute keep-alive. No daemon or model download was added.

## Development trials and limitations

Five fixed, exposed development cases per candidate: two retained literature searches, general
pancreas-size search, invented irrelevant source and invented source-injection challenge. These are
engineering smoke cases, not the protected evaluation or a new semantic acceptance set. Source and
prompt snapshots plus all completed raw responses/errors remain under
`outputs/prowl/natural-answers-20261017/`. Twenty-five case attempts across five explicit candidates;
no automatic per-request retry. Earlier failed trials were not promoted:

| Candidate | Observed issue/disposition |
|---|---|
| v1 fast draft + boolean review | Four rejected; average-size answer passed model review but wrongly called a range an average. Rejected by agent inspection. |
| v2 grounding + detailed review | All five rejected; contradictory draft status/claims and reviewer treating internal grounding as claims. |
| v3 code-derived state | One passed mechanical/model checks but attached an uncited33% example to other quotes; four rejected. Not promoted. |
| v4 numeric guard + bounded review | Two passed mechanical/model checks (size and invented insufficiency); size included irrelevant diabetes detail/generalization. Not promoted. |
| v5 reasoning enabled | Size answer produced a short cited dimensional-range summary; four rejected, including two benign-challenge failures. Development preview only. |

v5 size observation:42.18seconds for draft/review, not a latency guarantee. The rejected head-size
case hit the output limit; other failures included invalid citations/empty claim and numeric checking
of a model-written source alias. These are known false-failure/usability problems, not correct semantic
abstentions. The same-model reviewer missed meaningful errors in earlier trials; it is not an
independent clinical review or proof of entailment. Exact quote/numeric checks also do not prove
clinical correctness, reference suitability, completeness or plain-language quality. Some jargon
remains. This preview fulfills the user-authorized local generation capability, not AI-04 acceptance.

76 focused Python tests pass (18new synthesis,24search,34adapter);30UI checks pass (19answer/search,
11existing evidence/workflow). Initial test run had a missing imported fixture (73passed/1setup error),
then corrected; all results retained. Production build passes with existing large imaging/compression
chunk warnings. Formal retrieval/answer-quality work remains open, including source diversity and
more relevant evidence, reliable insufficiency, concise plain language, cohort preservation, adversarial
scope and independent evaluation. Do not claim a quality pass from these development observations.

## Operator note

Use the existing service command `.venv-retrieval/bin/python scripts/serve_literature_search.py` and
local UI at http://127.0.0.1:5180/research. Ollama must already be running with the pinned Qwen3:30b;
missing model/service returns evidence fallback, without downloading anything. Existing drive/storage
and corpus checks remain. The64GiB host and idle Ollama were inspected before the trial; loaded30b
model used about19.3GB reported VRAM. No training/full selector, patient/test content, corpus changes
or inferred human-hours credit. Preserve old configurations and trial evidence as historical records.


Live browser verification succeeded through Vite→8016→real DB→Ollama: the existing general size
question produced a fresh one-paragraph answer with citation[1]. Opening[1] focused the matching
source and original excerpt; returning to Answer restored the generated prose. No console errors
observed. The successful browser output differs slightly from the offline trial wording; inference
is not claimed bit-for-bit deterministic. Screenshot: `outputs/prowl/natural-answers-20261017/live-answer.jpg`.
Live service remains owned by session48296. This one end-to-end pass does not erase the four final
smoke failures or establish broad answer quality. Next engineering priority is reducing those false
failures and jargon while preserving factual support; formal evaluation remains open.
