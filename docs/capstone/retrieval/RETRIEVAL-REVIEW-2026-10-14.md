# Guided retrieval review — October 14

The two abstaining questions had relevant material in the existing274passage collection.
Whole-question cosine ranking favored generic introductions/search methods over definitions and
specific EUS studies. No download, re-embedding, database write, or full-catalog restart was needed.

Implemented guided-facets-v1 in src/retrieval/guided_retrieval.py. The question catalog specifies
two explanatory query facets each for radiomics and EUS (including the EUS acronym); CT detection
keeps its original query. Each query retrieves five exact cosine results from the same collection
and encoder. Merge reserves one leading result per query, then uses reciprocal rank fusion with
constant60 and passage-ID tie breaks. Word-set Jaccard>0.8 removes heavily overlapping snippets.
This heuristic can discard useful overlap and is not semantic deduplication. Unknown internal
questions remain single-query; HTTP request allowlist is unchanged. No hardcoded result IDs.

Each returned passage retains the retrieval policy, query/rank/cosine provenance, fusion score,
and plan hash. Original passage identities/citations/rights remain unchanged. Frozen prior
responses remain immutable. New requests use the updated plan; retries read the original response.

Answer policy verified-extracts-v2 also drops later quotations repeating a complete substantive
sentence (>=40characters) from an earlier quotation. This preserves first-occurrence evidence and
avoids presenting a study twice through overlapping chunks. Exact quote validation still precedes
this step. It is not a general relevance validator; a unique unrelated excerpt can still pass.

## Development comparison

Same two papers, model and question wording; broad baseline had abstained on radiomics/EUS.
Improved context yields:
- Radiomics: definition/ROI feature calculation, CT example, workflow excerpts.9.17s local generation.
- EUS: specific dysplasia/IPMN CNN studies.13.72s. Initial three extracts repeated one study and
  attached an MRI comparison; deterministic deduplication of the retained result leaves two extracts
  without that repeated mixed-modality quotation. This specific repair does not guarantee future
  modality relevance.
- CT detection: retained cited study extracts.10.74s. One retained output also discusses PET/CT
  neuroendocrine work, so task/subtype scope still deserves reviewer scrutiny.
- Negative probe asking for randomized-trial survival benefit: insufficient_evidence with no quotes.

All quoted source statements remain authors' claims in reviews, not verified clinical conclusions.
These are source-informed development checks, not independent/held-out relevance scores. Query
facets were chosen after inspecting this corpus. No universal recall or truth claim follows.
Evidence: outputs/prowl/retrieval-review-20261014/comparison.json, answers.json and
reviewed-answers.json. The latter applies the final deterministic deduplication to retained model
outputs without rerunning or replacing original evidence. Other saved results remain intact.

31 focused Python checks pass (fusion coverage, overlap, deterministic merge, unknown-question
behavior, exact-quote/abstention/retry regressions);2actual browser scenarios pass against refreshed
APIs (CT answer and research search); production build and diff whitespace checks pass. Build's
existing large-chunk advisory remains. Browser checks include citations, retries and unavailable
service behavior, not new exhaustive relevance tests.

Running APIs: answer8014 session25018, retrieval8013 session17869. Drive/database remain in use;
stop both APIs and the dedicated DB before ejecting. No training or credited human-hours changes.

Next: review these visible answers with Quinton and define a small independent question set with
expected evidence/abstention before expanding the source batch or attempting paraphrased answers.
