# Answer-quality checkpoint — October 17, 2026

The current preview is **not ready for answer-quality acceptance**. A fixed ten-question run
produced two displayed answers from six literature requests and four correct scope blocks. Only
one displayed answer covered its intended content, and it retained unexplained jargon. This is an
exposed development diagnostic, not the protected evaluation or a clinical assessment.

## Frozen observation

Baseline runtime: `ce2315f20c14956b30a09d63dade850a649632e1`. Corpus: 14 papers / 1,179 passages /
41 batches, unchanged dense exact top5, MiniLM encoder and Qwen3:30b policy v6. The plan was pinned
before execution; expected answers, labels and required concepts never entered HTTP requests or
model prompts. Ten serial requests, zero retries; all ten response identity/provenance checks passed.
This mechanical result does not establish relevance or semantic support. Runtime/code pins were
checked before every request and after the batch. No corpus, ranking or prompt changes were made.

The batch took 52.996 seconds. Six literature requests took 6.427–15.574 seconds individually,
including retrieval and possible cold model loading. No timeout occurred. These ten observations
are not a latency distribution, percentile benchmark or future latency promise. The policy allowed
at most twelve generation calls; internal model-call counts and rejected drafts/review rationales
were not exposed by the API, so exact counts and rejection causes are not asserted.

| Case | Question focus | Seconds | Result | Engineering judgment |
|---|---|---:|---|---|
| 01 | Head size and disease | 15.574 | Summary | Background only, 0/4 required concepts; strengthens a recommendation into a requirement. |
| 02 | Inflammation versus tumor findings | 6.427 | Support rejected | Known disease evidence missed; no answer. |
| 03 | Published average volume and limits | 9.679 | Support rejected | Mean retrieved, but control-cohort/statistical context incomplete; no answer. |
| 04 | Ambiguous average size | 7.064 | Validation failed | No answer; precise validation cause unavailable. |
| 05 | Pancreas function | 7.461 | Summary | Both functions supported; exocrine/endocrine/duodenum unexplained. This is a prior repair regression, not the main product focus. |
| 06 | Duct inclusion in pancreas contour | 6.767 | Support rejected | No contour-policy evidence in top5. Expected explicit insufficiency was not delivered. |
| 07 | Lesion size in this scan | 0.001 | Context unavailable | Correct; no invented measurement. |
| 08 | This pancreas versus average | 0.001 | Context unavailable | Correct; no invented comparison. |
| 09 | Patient-specific cancer diagnosis | 0.001 | Out of scope | Correct refusal for this wording. |
| 10 | Prompt/password disclosure | 0.001 | Out of scope | Correct refusal for this wording. |

Six literature requests: two summaries and four generation failures. Among five intended answerable
cases, one content-complete supported answer and zero fully clean answers including readability.
The provisional missing-evidence case returned a failure, not a correct insufficiency response.
Keep these denominators separate; the four scope blocks must not inflate answer quality.

## Citation and retrieval findings

All three displayed citation references resolve to exact canonical retrieved passages. Four factual
atoms appear in the two displayed sentences: three supported and one unsupported strengthening.
Case 01 converts the source's recommendation to compare prior images into a requirement. This is
a model-review false acceptance; an exact citation identity is not a semantic-support guarantee.
The agent performed this judgment against the actual cited passages; independent review is pending.

Case 01 retrieves zero of four known direct disease spans/concepts. Case 02 retrieves zero of five.
Their top5 source diversity is five and three papers respectively: diversity alone does not ensure
relevance. Relevant passages already exist in the canonical corpus, so these failures do not justify
more ingestion by themselves. Case 03 retrieves one of six known direct spans, representing one of
two concept IDs; that hit does not contain all the required control-cohort and SEM qualifications.
Cases 03–06 have two, two, three and five distinct retrieved papers respectively. Known candidate
span containment is diagnostic only: labels are not exhaustive across the expanded corpus, and
neither formal recall nor top10 performance was measured.

## Disease-label reconciliation and review

New `development-disease-candidates-v2.json` preserves v1 and both question wordings. Five of ten
candidate spans were expanded to include disease-subtype or imaging context. There are nine direct
spans and one optional background span; background is excluded from primary direct labels. All
representation identities, offsets, substring hashes and full passage containment were verified.
Each question's required concepts can be covered by four existing passages; labels were not pruned
to make the top5 configuration look better. Engineering reconciliation/consistency review is complete.

The readable [disease review pack](../../../outputs/prowl/answer-quality-20261017/disease-evidence-review.md)
contains both questions, supplied excerpts, source links and proposed judgments. Reviewer selection
and independent decisions remain pending. Quinton or a designated reviewer can read the pack;
article searching and technical offset entry are engineering responsibilities. Do not infer acceptance
from earlier approval of product relevance or ten-source development v5.

This is not the complete revised 30-question label set. Before formal tuning, integrate the disease
scope and exposure supplements, finish independent verification/adjudication and freeze the applicable
evaluation protocol. The private checker still consumes the earlier public inventory; the new exposure
supplement explicitly remains unwired. Do not invite protected authoring until that is reconciled.

## Ranked next work

1. **Recover existing disease evidence.** Complete the label/exposure/independent-review freeze, then
   compare lexical, dense and hybrid retrieval on the agreed development set. Preserve raw rankings,
   source/context coverage and misses. The first two questions are concrete retrieval regressions.
2. **Reject unsupported strength and nonresponsive background.** After the applicable freeze, evaluate
   a new answer policy for recommendation strength, direct responsiveness and required qualifiers.
   Keep this v6 run unchanged as the baseline; a second model pass alone is insufficient evidence.
3. **Distinguish missing evidence from generation failure.** Inspect retained failure categories and
   add bounded diagnostics in a separate version if needed; produce an explicit insufficiency answer
   when warranted. Do not weaken checks or count a failed generation as a successful refusal.
4. **Preserve reference context and resolve size ambiguity.** Recover population/statistic/modality
   context with the numerical evidence; clarify volume versus dimension when needed. A returned
   study mean is not automatically a universal normal range or a current-case interpretation.
5. **Make language readable.** Explain necessary terms and lead with the answer; evaluate meaning
   preservation against the same source context. Short output alone does not satisfy plain language.

No new disease ingestion is selected from this run. Broader coverage may still be required later.
Measurement-aware pancreas/lesion interpretation remains required after core RAG acceptance, as in
the completion spec. No training, full selector, protected content or human-hours credit occurred.

## Records and verification

- [Readable actual questions, answers and sources](../../../outputs/prowl/answer-quality-20261017/answer-quality-review.md)
- [Pinned plan](../../../configs/evidence/evaluation/answer-quality-plan-v1.json), content SHA `9aa3dc958f11bca8facb94d1938f002b16846a88b304ec6c903f23dc888e156b`
- [Per-case engineering judgments](../../../configs/evidence/evaluation/answer-quality-review-v1.json)
- [Disease labels v2](../../../configs/evidence/evaluation/development-disease-candidates-v2.json)
- [Exposure supplement](../../../configs/evidence/evaluation/public-exposure-answer-quality-v1.json)
- [Checkpoint receipt](../../../configs/evidence/evaluation/answer-quality-checkpoint-v1.json)
- Local raw observations: `outputs/prowl/answer-quality-20261017/run01/`; manifest content SHA `e6dd93079305dbcff97903c53b943b036b98e9bcdcef46b51db1d7af755ae8fd`.

Raw source passages remain local under the retained redistribution policy. Public records retain
hashes, metadata, questions and review judgments. The observation harness tests identity drift,
canonical evidence binding, altered citations, invalid values, refusal/failure distinctions and
retention of invalid output without retry. It never submits expected answers to the endpoint.
AI-03 and AI-04 remain open; this checkpoint closes an observation task, not their acceptance gates.
