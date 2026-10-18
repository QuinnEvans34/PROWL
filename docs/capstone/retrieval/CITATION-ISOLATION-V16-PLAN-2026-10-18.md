# V16 — isolate citation review and qualify numerical claims

V15 is rejected despite two model-approved summaries: head wording merges a CP head finding with
whole-organ AIP and cites no passage supporting the cancer-confusion assertion; volume generalizes
a selected study group and leaves ± undefined. Worker finished/reaped47.768s, ownedpeak14,835,433,472B,
no resource stop. Download provenance/blob verification passed separately; no weights changed.

Concrete verifier defect: previous reviews received ALL retrieved sources alongside each claim's
citations. That permits uncited context to contaminate an entailment decision. Remove unrelated
passages from the review request. Each numbered claim carries ONLY its bound citation quotes and
source titles. The checker must independently support each condition/anatomical association within
compound sentences. Writer/one revision may see full context; checker may not. This is a testable
information boundary, not a claim that model review becomes infallible.

Add mechanical checks: numerical averages must explicitly identify a study/sample/group/report,
not imply a universal population value; ± must name standard error/SEM or standard deviation/SD
and have that interpretation in the cited text. Source-absence statements are rejected. Preserve
citation, number, population, mandatory-strength, percentage and anatomical-scope guards. Failures
produce precise feedback, never a replacement answer. At most one revision followed by isolated
review; no retry on timeouts/provider faults and no failed draft displayed.

Use pinned V15 instruction model on11435, non-thinking/temperature0/seed42/context16384. Claims-only
writer schema and short writing/review prompts, max1536outputtokens/call. At most4calls/60seconds per
request, one shared deadline. First exactly the same two exposed canaries (head-size and published
volume), at most8calls/4minutes, ownedRSS18GiB and unchanged storage floors. Preserve new results and
prior failures. Both must pass source review/readability/qualifications before a separate continuation.
No expected answers/gold labels or case-specific corrections go into the runtime prompts. Formal
independent acceptance and clinical deployment remain outside this diagnostic.
