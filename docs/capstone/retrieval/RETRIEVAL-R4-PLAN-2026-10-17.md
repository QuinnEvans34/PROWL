# R4 — hierarchical source-section retrieval

R2/R3 failed their top5 criteria and remain rejected. New hypothesis: literature QA needs complete
source sections rather than five isolated600-character fragments. This is a distinct evidence
package; report its total passage/token budget and do not relabel its metrics as top5 improvement.

One fixed pipeline, before execution: original question unchanged → select up to2 papers from all14
titles and first1,000 normalized abstract/source characters → select up to4 sections from those
papers using canonical headings and first300 section characters → return every existing canonical
passage in those sections. No rewritten query, cross-encoder or new corpus. The selector receives
only question and corpus metadata/excerpts, never labels, expected answers or per-question boosts.
Use existing pinned Qwen3:30b for both closed-ID selection calls, think=false,temperature0,seed42,
num_ctx16384,num_predict768. Full retrieval deadline40seconds, two calls maximum, no retries.
Paper menus≤18,000characters; section menus≤50,000characters; no silent menu truncation. All source
IDs/section choices must exist and be unique. Returned passage text/rights/offsets bind canonically.
Evidence cap40passages/24,000characters including titles; if exceeded, fail closed, do not silently
clip the selected source. Record selectors' raw outputs and exact selected IDs. This is a research
scope convenience, not semantic privacy qualification; public scope guard precedes live model calls.

Evaluate all20exposed answerable v6cases once, maximum40selector calls/20minutes. Existing labels
remain fixed and provisional. Report source coverage, passage/span/concept coverage over the whole
evidence package, count/character cost and latency; separately show first5passage metrics without
comparing unequal budgets as equivalent. For development integration require direct evidence for
≥18/20questions, full labeled concept coverage on≥16/20, direct disease evidence with actual
inflammatory comparisons, median≤20seconds/max≤40seconds, no invalid source identities or question
intent drift. These are prospective package criteria, not a retroactive pass of R2/R3.

If qualified, adapt the live interface to the explicit larger bound and test unchanged answer v6.1
prompt semantics with only the versioned evidence-count/context-size amendment. Evaluate existing
10quality questions first,≤20answer-generation calls and no retries; record a separate answer plan
before execution. Clinical/free-text independence, corpus/human label acceptance and final freeze
remain open. Only measured development confidence is in scope.
