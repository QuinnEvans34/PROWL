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

## Candidate result and manual review

Candidate producers frozen at `79a9458`; unchanged matrix. Retained at
`outputs/prowl/week3-quality-candidate-20261020`: **20/20 supported,10/10 boundaries**,20 chat
calls,135.08seconds total. No retry, timeout or fallback. All20 intended record sets matched.

| Dimension | Candidate result | Meaning |
|---|---|---|
| Factual support | 20/20 engineering review | Each emitted assertion checked against the retained source passages; not independent adjudication |
| Completeness | 20/20 | All91 required unit instances and their qualifications retained |
| Readability | 20/20 engineering review | Complete sentences, terminology introduced, factual paragraphs followed by separate limitations |
| Citations | 110/110 paragraph-source links | Exact canonical text/locator binding;13 distinct source passages |
| Direct model composition | 20/20 | No source fallback counted as success |
| Boundary behavior | 10/10 | Zero model calls, no composed answer |
| Supported latency | 3.54–13.47s; median6.80s | End-to-end HTTP including retrieval; all below40s |
| Boundary latency | maximum0.66s | No generation |

Manual review covers50 paragraph instances/16 distinct emitted paragraphs. Disease sources preserve
the focal-head context, MRCP, calcification morphology, combined-feature limitation and focal-AIP
portal-venous phase/duct/atrophy qualifications. Volume sources preserve the study population, MRI,
sample sizes, means, SEM identity, matching and non-universal/non-CT applicability. Citation review
used canonical PMID32703312 passages4/7/9/22/24/37/39/43/44 and PMID25950180 passages2/18/27/29;
the complete retained text and character locators are in the separate source packet.

`engineering-review.json` binds these observations to receipt SHA-256
`21d7689edc52ed5f3bd4faa5b7bb553fab5411812a5626646f23e2fc9755763f`.
The original producer receipt's manual-pending field is retained; the separate review records the
subsequent check. This is one engineering reviewer and exposed data, not independent or clinical review.

Readable files: `all-questions.md`, individual D01–D12/V01–V08/B01–B10 files, and `sources.md` in
the candidate directory. The renderer is `scripts/retrieval/render_week3_review.py`. Complete claims
remain visible separately from long source excerpts, with exact per-paragraph source links.

## UI and deployment

All60 baseline/candidate responses pass the actual UI validator; forged claims and unknown policies
remain rejected. A retained-response React test renders every candidate question, checks all answer
paragraphs, opens the exact cited excerpt and switches back to Answer; all30 cases pass. Combined
with the existing UI checks,66 distinct tests qualified. Production build passes with the existing
large-chunk advisory. No additional browser automation was attempted: the app's earlier localhost
URL-policy rejection remains binding. These are React/HTTP checks, not a fresh visual-browser review.

After the gate/manual review, every candidate producer hash was reverified. Only the verified old
literature PID9015 was stopped. Replacement8016 runs in owned session37988 using the existing
`.venv-retrieval` and `--volume-answers`; DB/Ollama/inference/Vite preserved. Two additional, separately
counted rollout probes through Vite5180 completed: volume1.2 in6.93s and disease1.1 in7.24s.
These are not added to the30-case denominator. Evidence: `week3-quality-promotion-20261020`.

W03-04 is complete for this declared slice. W03-05 engineering checks and deployment are complete;
Quinton's packet/UI walkthrough decision is requested and remains pending, so the card stays In
Progress with that single review item open. Formal independent evaluation, arbitrary wording,
unreviewed diseases/modalities/populations and measurement accuracy remain open. No corpus expansion,
new medical wording, training or protected evaluation occurred.
