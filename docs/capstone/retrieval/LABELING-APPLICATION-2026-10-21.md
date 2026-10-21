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
