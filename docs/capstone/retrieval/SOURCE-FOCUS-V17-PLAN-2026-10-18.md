# V17 — focus synthesis on the highest-ranked paper

V16 still fails manual review: the head answer imports chronic pancreatitis into an AIP age-context
claim without a citation for that association; the published-volume answer is rejected. Both original
results remain. The fixed corpus contains the needed facts, but multi-paper context keeps inducing
cross-source merges. Test a context-boundary change, not another prompt or model variant.

Keep all R8 retrieved evidence available for source inspection. For generation, retain only canonical
passages belonging to the first ranked paper, including that paper's already-appended abstract/method
context. No text rewriting, new facts, labels or question-specific source choices. Preserve original
rank IDs. Use exactly V16 generation, guards, one revision and isolated review. Report the source
scope explicitly as top_ranked_paper with its work identity; this cannot claim cross-paper synthesis
or complete corpus coverage. Formal original metrics and full-concept requirements remain unchanged.

First two fixed canaries (quality01/03), no question changes or retries, maximum8calls/4minutes,
60srequest generation and18GiBownedRSS, same external store/model identity/floors. A useful supported
and readable answer with appropriate qualifications is required for both before further evaluation.
If qualified, separately evaluate remaining cases and real UI before any limited development preview.
A paper-focused preview is not formal AI-expert completion or clinical acceptance. If this context
isolation also fails, retain the result and stop local candidate expansion at this checkpoint.
