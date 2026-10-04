# Role-safe qualification implementation — D-281

Quinton requested continuing the next best work after D-280. Implement isolated qualification v2
and cohort v3 contracts first, followed by the bounded candidate content job from the expansion
packet. Existing qualification v1/cohort v2 and fixed two-case runtime remain unchanged.

Qualification v2 has explicit pancreas-localizer train-target and validation-reference purposes,
with protected role and annotation use checked separately. The current manifest pin and all check
receipts bind the selected purpose; held/excluded cases remain records. Executable cohort v3 requires
same-role protected ancestry and the matching purpose. Consumer operations are explicit: optimizer
requires train, evaluator requires validation. No implicit default or auto-relabeling.

Regression requirements: wrong role/use/purpose refusal, stale identities/evidence, held members,
full expected membership, ancestry mismatch, duplicate CT hashes across roles, changed current
manifest and old-version rejection. Returned descriptors are not yet a filesystem array loader or
run authorization. The generalized filesystem consumer must independently verify source bytes and
bounds before a new multi-case run. Positive per-case qualifications require actual reviewed evidence;
synthetic success is not publication of the real candidates.

Implemented and verified: **1,122 native tests pass**, two existing upstream warnings. The bounded
content job and separate 28-case engineering review are complete; see
[results and exact next implementation](LOCALIZER-CANDIDATE-CONTENT-RESULTS-2026-09-29.md).
No new real qualification or cohort publication is claimed by this implementation checkpoint.
