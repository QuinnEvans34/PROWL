# V10 — separate evidence extraction, readable writing, and support review

V9 completed all ten exposed cases: three summaries, three validation/support failures, four correct
scope blocks. The summaries remain jargon-heavy and incomplete (volume omits MRI/sample size/limits;
findings omits modality). Head enlargement again improperly inherits a whole-organ AIP feature;
the review catches it. Gap draft makes an unsupported absence claim and is rejected. Do not deploy.
Original producing source snapshots and traces remain in section-answers-v9-20261017.

Replace the overloaded single drafting task with three narrowly scoped calls: extract source-bound
facts and their qualifications; rewrite only those facts in readable language; independently prompt
the same model to check support against original source passages. This is NOT independent scientific
review. Exact binding, number/population/percentage/subregion guards remain. Extraction may contain
six short facts; final answer at most three paragraphs/180 words, with up to three citations each.
Empty extraction produces a correctly formatted insufficient answer without inventing an absence
claim. Review uses native reasoning, not a capped explanation in place of reasoning.

Same pinned Qwen3:30b, temperature0/seed42/16384context; maximum three calls per request, one shared
60-second generation deadline, no retries. Reuse exact v9 evidence for the same ten cases, at most
18 generation calls/15 minutes. Never supply expected answers, concept labels or authored prose.
Five intended answerable cases must give useful, source-supported readable answers; report exact
concept completeness separately, not as independent acceptance. Gap/four scope blocks must behave
correctly. No provider failures or unsupported displayed claims allowed for candidate preview.
If this fails, preserve the failure and reassess architecture rather than blindly repeat prompts.
