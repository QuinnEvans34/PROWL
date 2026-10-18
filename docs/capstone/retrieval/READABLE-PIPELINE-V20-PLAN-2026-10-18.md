# V20 — full paper-focused readable-answer checkpoint

V19's two rendering regressions are source-faithful and substantially clearer: head statement keeps
CP/enlargement association; volume keeps one MRI study's group counts and means while dropping scan
sequence detail. They remain partial against the original broader concept rubric (head differential
and feature limits; numerical uncertainty/generalization discussion). Do not claim formal acceptance.

Integrate the tested boundaries: fixed R8 canonical retrieval/context; generation focuses on the
first paper; V18 collects numerical feedback before one revision; V19 rewrites only claim text and
preserves original citation bindings; final review sees only bound citations. No expected answers,
gold labels, prepared responses or modified source facts. At most6 generation calls per literature
request (including at most one quality revision), no provider retry. Same pinned14B/temperature0/
seed42/16384context. Actual citations remain inspectable in the full retrieved package. Explicit
source_scope=top_ranked_paper prevents claims of cross-paper synthesis.

Bound model lifetime: one empty-prompt unload management call after each attempted request, with
no generated tokens, on the isolated11435 server. Reserve5seconds of the total60second model budget
for cleanup, leaving at most55seconds for inference; overall service request deadline90s and browser
100s. Cleanup failure returns an unavailable result, not a resource-success claim. Scope refusals
perform zero retrieval/model/cleanup work. Keep source-only fallback on any failed check.

First run the original ten exposed cases through the complete new pipeline using exact retained
canonical R8+study context (no ranking replay). At most36generationcalls/6unloads/15minutes,18GiBowned
RSS and unchanged storage floors. Record full generation+cleanup time, source scope, calls, revisions,
canonical bindings and manual source review. Require five useful supported readable answers, correct
insufficient result and four scope blocks, no unsupported displayed claims or provider failures for
this LIMITED preview. Report original required concepts separately; it is not full Step7 acceptance.
Only then allow a small separately declared variation/live integration test before preview selection.
If any gate fails, preserve it and do not deploy this candidate by calling partial coverage complete.
