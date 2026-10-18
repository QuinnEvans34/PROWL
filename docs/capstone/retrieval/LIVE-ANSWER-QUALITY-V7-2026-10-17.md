# Live answer quality v7: development repair plan

Quinton explicitly requested moving to live answer quality after the source-review checkpoint.
This authorizes a bounded development answer-policy repair before final evaluation. It does not
attest acceptance of v6 labels, change formal quality thresholds, release retrieval tuning or
complete the protected evaluation. Previous v6 observations and evaluation records remain intact.

## Planned change and observation

Use the same corpus, exact dense top5 retrieval, pinned local Qwen3 model, two-call maximum and
60-second generation deadline. Strengthen the generic answer/review contract for direct relevance,
recommendation strength, source qualifications and plain language. Reject a mandatory instruction
introduced where its cited passages do not express one. Keep insufficient retrieved evidence
distinct from model failure. Do not inject expected answers, required concepts or labels into prompts.

Before any model invocation, pin the candidate and six retained input snapshots. Replay the six
literature cases from the fixed v6 diagnostic once each, in order, with their exact old top5 passages.
Retain every request, draft, review, failure, elapsed time and resulting answer locally. No retries,
prompt sweep, additional evidence, new model or source downloads. At most12 generation calls and
600 seconds for this replay; source text remains ignored/local. Test scope blocks separately with
invented inputs. Candidate changes after observation require a separate disclosed attempt.

Judge displayed claims against their citations, question relevance, qualifiers and readability.
Record incorrect/overbroad abstentions and failures separately from answer completeness. A safe
abstention on missing retrieved evidence is not a successful answer to an answerable corpus question.
Do not use the six exposed examples to claim independent performance or improved retrieval.

Promotion to the local preview requires meaningful offline checks, no newly observed unsupported
displayed claim, removal of the known mandatory-strength/background-only failure, and at least one
readable supported answer on this small diagnostic. Otherwise preserve the result and leave the
candidate unpromoted. Same-model review remains fallible; no general safety guarantee follows.

After a qualifying replay, update the UI policy pin and explicit failure/insufficiency wording,
restart only the owned literature process, and perform two fixed live/browser smoke questions:
“What does the pancreas do?” and “Could the size of the pancreas head indicate any specific diseases?”
These check delivery/source navigation, not a second opportunity to tune the candidate. Preserve
all outcomes. Retrieval coverage and the independent evaluation remain subsequent work.
