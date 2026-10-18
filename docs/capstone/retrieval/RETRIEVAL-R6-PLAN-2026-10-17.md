# R6 — bounded native reasoning for evidence selection

R5 improves several study-specific selections but its retained head-size output still selects
whole-pancreas diabetes volume and a quantitative-imaging review; it misses the requested regional
disease evidence. Its rationale uses its500-character allowance to begin an unfinished review of
the menu rather than justify selected IDs. R5 cannot pass its disease requirement; finish and retain
its fixed run. This suggests testing native reasoning, not accepting a plausible-looking rationale.

One prospective candidate after R5: same compact two-stage menus, original question, source corpus,
canonical whole-section expansion and limits. Enable native thinking for the existing pinned
Qwen3:30b selector, maximum2,048output tokens per stage; request brief reasoning focused on the
information need. Structured output still contains a short reason and closed IDs. Strengthen the
generic instruction to match organ subregions and distinguish whole-organ measurements from
regional findings; no diseases, answers, source IDs or question-specific rules are supplied.

At most40selector calls over20exposed cases, no retries. Record incomplete outputs. Retrieval
deadline60seconds, total experiment30minutes. This prospective latency tradeoff is explicit:
median≤30seconds/max≤60seconds for selection; if integrated, enforce≤90seconds for the full
retrieval-plus-answer request. The user-facing target remains useful answers without multi-minute
silence. Same R4 quality criteria (≥18direct-hit cases,≥16full-concept cases, both disease cases
and independent engineering source reading); disclose higher token/runtime costs and regressions.
No deployment on mechanical coverage alone. No label changes or protected-set access.
