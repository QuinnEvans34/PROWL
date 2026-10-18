# V13 — bounded validation feedback and revision

V11's head answer still fails the percentage guard, and its gap answer falsely treats source absence
as a cited finding. V12's first case repeats the percentage problem despite publisher sampling.
Changing model/sampling alone is insufficient; retain both whole attempts and await v12 completion.

Implement a normal bounded repair path rather than discarding an otherwise recoverable draft:
collect claim-level citation/qualifier failures, or explicit source-review/readability/qualification
failures; send that feedback to the writer once; validate and review the revision. Never repair
provider/timeouts automatically and never show failed drafts. A second quality failure returns the
existing source-only fallback. No expected answers, question-specific prose or gold labels enter
this pipeline. A source-absence claim is a format error: return empty claims for a gap instead.

Use installed pinned8B with publisher non-thinking sampling (temperature.7/top_p.8/top_k20/min_p0,
seed42/context16384). A short claims-only schema removes the hidden grounding field that repeatedly
absorbed long reasoning despite its instruction to be short. No reasoning tokens are requested in
any stage. Final limit3paragraphs/3citations each. Source review separately records support,
readability and preservation of study/imaging qualifications. This remains fallible model review.

Maximum4calls (draft, review, one revision, final review), or3when mechanical checks reject before
first review. Same shared60s generation/90s request deadline. One revision is a declared policy,
not an experiment retry; no network retry or seed search. First run same10fixed exposed cases after
v12 completes, at most24calls/15minutes, exact retained canonical source context. Require five useful
supported readable answers, correct gap/four scope blocks, no unsupported displayed claims and no
provider failure for preview consideration. Original full-concept rubric remains separate/open.
Then, only if qualified, one declared small variation/live integration check and source review.
Do not claim clinical or independent acceptance. Preserve producing code/options/traces and failures.
