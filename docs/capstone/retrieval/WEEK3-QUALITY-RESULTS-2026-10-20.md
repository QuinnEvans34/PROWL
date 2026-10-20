# Week 3 answer quality results

## Frozen baseline

Plan/matrix/harness committed as `81cb1ee`; matrix SHA-256
`7f64e8e51fdf00770e65a50380987644eeede50fd2a76dbd8f43587473956ff6`.
The first attempt used `.venv-prowl` and stopped at the missing `transformers` import before any
model call or question. It is retained at `outputs/prowl/week3-quality-baseline-20261020`.
The correct existing `.venv-retrieval` environment completed the unchanged batch at
`outputs/prowl/week3-quality-baseline-a02-20261020`: 123.28 seconds, 17 chat calls, no retry.

Supported questions: **13/20** direct complete model answers; boundaries: **10/10** safe.
Exact intended selection: **17/20**. All returned evidence matched the canonical corpus.

| Failure | Category | Observed cause |
|---|---|---|
| D04: autoimmune pancreatitis can “resemble” cancer | Routing | Comparison grammar omitted resemble |
| D10: radiologist “tell autoimmune pancreatitis and pancreatic cancer apart” | Routing | Phrase exceeded 45-character tell/apart span |
| D11: diseases associated with a large pancreatic head | Refusal, then selector gap | Legacy “what disease” diagnosis prefix; “large” absent from head grammar |
| D05: MFCP/PDAC imaging | Composition | All choices present; qualifier shared a factual paragraph |
| V01: average pancreas volume | Composition | All choices present; matching clause preceded SEM clause |
| V03: normal-glucose-tolerance volume | Composition | Same ordering failure |
| V04: type-two volume | Composition | All choices present; qualifier shared a factual paragraph |

The pre-demo V01 failure remains retained under `demo-readiness-20261020/literature-answer.json`.
Its raw plan was not captured, so its exact layout error remains unknown. The new V01 reproduces
an invalid-composition fallback with a retained, demonstrably complete but reordered plan.
No positive case demonstrated missing source facts; unsupported CT ranges, children, acute
pancreatitis and treatment remain explicit coverage limits, not newly answered topics.

## Selected repair and candidate freeze

Largest observed problem: **four avoidable layout fallbacks**. Keep the model, prompt, wording,
facts, corpus and one-call deadline fixed. Before rendering, validate every model unit/wording
choice for exact membership, type, no duplicates and no additions. Only after full coverage passes,
arrange those same choices in source order and separate qualification paragraphs. The strict
assembler and UI independently check the resulting text/citations. Never fill omitted choices
or turn arbitrary model prose into an answer. Record policy becomes1.1; volume policy becomes1.2.

Source selector1.1 adds general resemblance/mimicry, a bounded120-character tell/apart span and
“large” head wording. A separate disease-search scope wrapper permits only a general plural
“what diseases can/could/may be associated with” request that matches a reviewed record and whose
only legacy refusal is RF1. Original planner and other privacy/diagnosis gates remain unchanged.
The UI accepts the immediately preceding policy versions only because their wording, prompt and
citation contracts are identical; content checks still apply during deployment.

Offline replay of all17 retained model plans confirms full exact unit membership; normalization
fixes all four layout failures while retaining every selected wording. Zero new model calls.
Replay evidence: `outputs/prowl/week3-quality-layout-replay-20261020.json`.

Relevant backend checks:224 initially passed; one obsolete reversal-expects-refusal test failed.
It was replaced by an explicit choice-preservation assertion; its first literal phrase assertion
had a test typo, corrected against the actual reviewed wording. All26 volume tests then pass;
225 distinct affected backend checks are qualified across those runs. UI:65 tests pass, including
all30 original HTTP responses through current validation, forged-text and unknown-policy rejection.

Candidate batch, manual source/answer review, deployment and walkthrough: pending. No acceptance
or model accuracy is inferred from the baseline or offline repair. Formal independent gates stay open.
