# Assessed exact-span selection — October 17, 2026

## Frozen pre-run design

User authorized answer-quality development. One candidate tests explicit assessment of every
retrieved passage before selection, within a single model call. It reuses the same question,
five frozen passages, sentence segmentation and exact selectable spans as direct30B selection.
The prompt/schema change: classify question intent; give each source a short reason and direct,
context or none verdict; select at most three exact spans from directly supporting sources.
The server refuses missing/foreign assessments, excluded-source selection and abstention that
contradicts direct support. Structural consistency is not proof that a model's judgments are true.
Audit reasons are retained privately and never presented as supported answer text.

Motivation: direct30B falsely abstained on radiomics/PET and omitted CT method context; previous
study-record extraction lost useful selections. This tests a single-call representation of the
selection decision, without a separate extractor/reviewer or gold-derived hardcoded study rules.
No claim about the cause of previous errors. All ten frozen corpus-informed cases are development
cases; earlier failures have informed this candidate, so this is not held-out validation.

Pinned Qwen3:30B, nonreasoning, temperature0, seed42, context8192. Output cap1200 (was900 for direct
spans) accommodates five short assessments. Thus this is a policy comparison, not a single-variable
prompt ablation. One ten-case run, maximum600seconds total/60seconds per call, zero retries or sweep.
Only questions/source sentences enter the model; reference IDs, expected status, aspects and rubric
remain evaluator-only. Save producing sources, original requests and immediate raw responses.

Compare unchanged scoring: direct30B5/7supported,4/7clean,9/14aspects; direct8B7/7supported,
4/7clean,12/14aspects; best experimental8B+30Bscope7/7supported,5/7clean,14/14aspects.
Candidate improvement requires >5/7clean,7/7supported,14/14aspects,3/3correct fresh abstentions,
zero invalid generations. Full development acceptance remains7/7clean with no irrelevant excerpts.
Review every output against source and the fixed rubric. No automatic live promotion follows this
small known suite. No database query/write, new papers, embeddings, model download, full corpus
selector or training. Production v2 and live workflow remain unchanged.

## Results and decision

**Rejected; production unchanged.** Ten fresh calls completed in37.043seconds, with no retries,
timeouts or output-length terminations. Client exited0. Five answers were rejected because the
model explicitly marked a source directly supporting, then emitted insufficient evidence with
no spans. The remaining outputs were two answers and three correct missing-evidence abstentions.

| Fixed development measure | Direct30B | Assessed30B |
| --- | ---: | ---: |
| Supported answers | 5/7 | 2/7 |
| Clean complete answers | 4/7 | 1/7 |
| Required aspects covered | 9/14 | 3/14 |
| Relevant / emitted excerpts | 6/6 | 2/2 |
| Fresh correct missing-evidence abstentions | 3/3 | 3/3 |
| Invalid generations | 0 | 5 |

The five contradictions are radiomics, EUS, CT detection, nCLE and MRI. Exact offline resolution
reproduces `Abstention contradicts direct support` for each. This is an explicit inconsistency in
the returned fields, not a timeout or missing-source failure. It does not establish why the model
made that decision, nor prove the correctness of its preceding assessment. In particular, nCLE
also labels a different EUS morphology study as directly relevant despite the requested nCLE method.
The guard blocks publication; the model's assessment is not a reliable independent verifier.

PET now selects the correct named study/tracer/grades without adjacent MRI text. CT external
validation still chooses only the numerical result, omitting contrast-enhanced CT method context.
Both surviving excerpts are exact and relevant, but their precision does not compensate for lost
answers and coverage. No candidate output is mixed with prior runs to claim a better score.

## Verification and evidence

43 focused tests passed before inference: candidate structure/identity/empty-input/truncation
refusal, runner integration without old selections or gold inputs, prior span mechanics, deadline
handling, frozen-input binding and scoring. Ten offline replays reproduce complete generation
objects and exact recorded requests. All ten user messages and frozen passages equal direct30B's;
only the intended prompt/schema/output-budget policy changes. Producing-source hashes and request
hashes verify; the unchanged scoring function reproduces the public review exactly.

Public engineering judgments: `configs/evidence/evaluation/assessed-spans-v1-review.json`.
Local requests, raw responses, pre-run source snapshots, manifest, receipts, score and replay checks:
`outputs/prowl/development-evaluation-20261015/assessed-spans-v1/`. Raw article/model text stays local.
The report frozen with the run contains only its pre-run design; this final report appends outcomes.
Known development cases and agent judgments are not independent clinical or held-out validation.
The score's existing `errors` field counts receipt-level failures; the five invalid generations
are separately reported here and in per-case validation states, not misrepresented as valid abstentions.

## Next recommendation

Stop adding model assessment fields or another verifier layer to this candidate. It asks the model
to independently express support, final status and span selection, and those decisions contradicted
each other in five cases. A future bounded comparison should test one authoritative evidence choice
per source, with final answer status derived by code from the verified choices. That would remove
this representational contradiction, but would still require the same relevance, study-identity,
coverage and unsupported-question tests; it is not a proven quality repair. First freeze that new
contract and synthetic rejection cases, then evaluate once. No follow-up model run was performed.
