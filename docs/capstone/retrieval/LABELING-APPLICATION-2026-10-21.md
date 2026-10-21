# Assisted labeling application — invented-data qualification

User-authorized scope: a usable question → proposed meaning/evidence → accept/correct workflow,
tested with invented questions before any protected use. This is AI-03 implementation; no corpus,
live literature policy, training or measurement change.

## Implementation contract

- Standalone loopback application, separate from the research viewer. No database or new dependency.
- Fixed fictional source library; no protected-path argument, private import or evaluation release.
- Existing local Qwen3:8b proposes meaning, concepts and exact excerpts from all supplied sources.
  No candidate-system answers or development gold answers are supplied. One bounded model request
  per revision; no hidden retries. Timeout/failure becomes a visible retryable error, never acceptance.
- Full source text, exact excerpts and limitations supplied together. User enters a natural-language
  correction to request a new proposal; previous proposals and decisions remain in session history.
- Acceptance requires explicit meaning/source review and no mechanically unresolved evidence.
  Reject and a separate consistency decision are distinct events. Neither means evaluation-ready.
- Session state in memory only; explicit JSON export carries versioned provenance/review history.
  Reload can reconnect during the server session; restarting clears state. No content in request logs,
  analytics, browser local storage or automatic files. Same-user OS access is not prevented.
- Loopback Host/Origin and mutation-token checks; bounded payloads; no remote model endpoint or redirects.

## Qualification target

Exercise actual HTTP create/revise/accept/reject/consistency/export, stale decisions, missing and
invented quotes, unresolved support, model outages, source-instruction text, role/history bindings,
and safe UI rendering using invented fixtures. Run a bounded real local-model rehearsal on fictional
questions, inspect resulting excerpts manually, and report latency separately from fixture tests.
UI interaction tests must exercise correction and acceptance, not merely snapshot markup.

## Remaining private-use gates

Real canonical corpus/passage alignment, model/context budgets across the larger corpus, semantic
overlap adjudication, protected storage/backup, operator isolation and frozen evaluation admission
remain separate. This application must not open the existing protected evaluator. Reviewer names
record actual roles; the same person may fill several roles without being called independent raters.
Only invented content is authorized for the developer's end-to-end rehearsal.

## Delivered application and operator instructions

Open **http://127.0.0.1:5182**. The application is a separate Python standard-library server, with
plain HTML/CSS/JavaScript and the existing local Qwen3:8b model. It does not use the research viewer,
literature database, patient inputs, candidate answer service or protected question files.

From the repository, start it with:

```sh
.venv-retrieval/bin/python -m src.retrieval.labeling_app --port 5182
```

1. Enter your name and select an example or type a **fictional Luma sensor** question.
2. Choose **Prepare evidence**. Read the proposed meaning, excerpts and expandable full sources.
3. If wording or source relevance is wrong, enter an ordinary-language correction and request a
   revised proposal. All evidence must be reviewed again for the new revision. Reject records a
   reason without discarding the question; later correction remains available.
4. Check the meaning and each source, then accept only a revision you agree with. Uncertain/conflicting
   evidence and missing support for a claimed answer prevent acceptance. A deliberate evidence gap
   can be accepted as a gap; it never becomes a supported numeric answer.
5. Record the separate consistency review with a note after comparing reviewed questions. Expand
   **Earlier proposals and review history** to inspect prior meanings, corrections and decisions.
6. Export the session before stopping the process. The JSON is for recordkeeping; normal use needs
   no JSON editing, paper search, evidence-offset entry or technical label entry.

Model source sentences are selected by closed, source-specific IDs. Canonical quotes/offsets are
supplied by the application, not typed by the user or invented by the model. This prevents the
observed source misattribution mechanically; it cannot prove semantic support or source relevance.
Requests include the previous meaning and human correction. One request per revision, no automatic
repair loop. Model identity is pinned; context16384/output2600 tokens, small fixed-input byte budget,
5-second metadata/85-second model socket timeouts. Those socket timeouts are not a certified absolute
wall-clock deadline under arbitrary slow-stream conditions. Each case is limited to10 revisions,
each in-memory session to30 questions. Backend and asset hashes are included in new exports.

## Verification and findings

- **44 Python checks pass**:20 initial application checks plus2 added model/busy checks,17 existing
  excerpt-boundary checks and5 public-admission checks. Tests exercise HTTP create/revise/review/export,
  stale hashes/revisions, preserved history, missing support, unknown/source-mismatched sentences,
  exact source identities, model change/truncation/outage, safe errors and origin/token rejection.
- **2 UI interaction checks pass** under the bundled Node runtime: type/select question, inspect
  evidence, correct, re-review, accept, consistency, history and export; service error and escaped
  source markup. No real-browser visual walkthrough is claimed. An initial Node20/jsdom mismatch
  and test-fixture path assumptions were corrected; runtime/dependency versions were not changed.
- **Seven bounded real model calls**, all fictional:two initial free-quote attempts rejected for
  source mismatch (second captured for diagnosis);one repaired sentence-selection trial;four actual
  HTTP requests covering interval proposal/revision and humidity-gap proposal/revision. No corpus
  questions, medical evidence, protected data, training or live-answer-policy changes.
- HTTP generation durations10.159s,11.641s,5.320s,6.956s. These are local-model request times, not
  broad performance guarantees or browser-render timings.
- Manual engineering inspection found an overclaim: “not established outdoors” became “does not
  apply outdoors.” The natural-language correction repaired meaning, concepts and source rationale.
  All four corrected interval excerpts match their sources and preserve the stated qualifications.
- The humidity answer correctly reported a missing threshold. Its first draft overlooked the
  explicit maintenance-note gap statement; correction recovered that exact sentence but introduced
  unnecessary indoor-schedule context. That revised case remains **rejected**, not accepted gold.
  This is a known assistant-relevance limitation. No further prompt sweep was run to conceal it.
- HTTP rehearsal completed9 append-only events:2 questions,2 proposals each,3 rejections,1 simulated
  acceptance and1 separate consistency review. Stale acceptance was refused. These decisions are
  explicitly attributed to an **engineering simulated reviewer**, never inferred as Quinton's approval.

Artifacts under `outputs/prowl/labeling-app-20261021/` retain original attempts and HTTP proposals.
The exported rehearsal session SHA256 is
`24982b95165edbf6c761d9d43c2de278216644b5e4eef0c650ef9b26037009c0`.
It contains the actual rehearsal before the final history-display/tool-hash additions; those additions
were covered by the focused checks. The export is preserved before resetting the live server to a
fresh session for Quinton. Source/proposal/model identities and the old failure evidence remain intact.

## Scope and tracking

This delivers the requested usable **invented-data rehearsal**, not qualified protected authoring
or automatic gold labels. Source relevance and semantic judgments still require review; the model
has demonstrated errors. Broad corpus passage alignment, independence/overlap adjudication,
operator isolation, encrypted storage/backup and frozen admission remain open. No real held-out
questions should be entered. The public evaluator still refuses private admission.

Trello: an AI-03 progress comment was attempted through the connector, but no result returned and
its write outcome is unconfirmed. Do not duplicate it blindly. Pending final update for AI-03 and
the weekly dashboard: “Invented-data labeling app delivered on5182;44Python+2UI checks pass; real
local model question/revision/accept/reject/consistency/export exercised. Source IDs fix attribution;
semantic/source-relevance review remains necessary, gap rehearsal rejected. Protected use still
closed. See LABELING-APPLICATION-2026-10-21.md.” Read the card before retrying this pending update.
