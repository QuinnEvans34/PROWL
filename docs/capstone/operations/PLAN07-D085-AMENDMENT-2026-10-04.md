# D-085 additional metrics — approved policy record

October3 approval, recorded October4 as D-344. Authority: Quinton's “Accept all three” in
[RUNNING-LOG](../retrieval/planning/RUNNING-LOG.md), confirmed by the present M1–M6 dispatch.
This supersedes the earlier decision-pending **proposal status**, preserving its historical record.
Official source/passage recall@1/3/5/10 and MRR, diagnostics and release bars stay unchanged.

| Additional separately reported measure | Numerator / denominator per answerable question |
|---|---|
| Ranked span-hit recall@1/3/5/10 | Distinct direct spans completely contained in any top-k passage / all distinct direct spans |
| Delivered-span recall | Distinct direct spans completely contained in actually packed, display-permitted passages / all distinct direct spans |
| Required-concept coverage | Distinct required concepts supported by delivered direct spans / all distinct required concepts |
| Delivered token count | Sum of tokens in actually packed passages; a count, no recall denominator |

Span keys are `(representation_id, representation_sha256, start, end)` on immutable normalized
text, with half-open Unicode code-point offsets. Complete containment is required; overlap,
partial/uncertain grades and retrieved-but-skipped passages receive no direct credit. Repeated
containment counts a span/concept once. Macro question averages disclose answerable/refusal counts
and undefined cases; a zero eligible denominator is undefined with a reason, never 1. Official
source aggregation collapses duplicates; passage scores remain within-configuration and disclose
undefined gold-passage cases. No real labels or questions were opened for this record.

Before measured use, verify accepted query/question/ranking/corpus and configuration binding,
representation hashes/exact slices, label version and rights-record identity. Local indexing
permission is insufficient for snippet delivery: display permission is separately enforced, unknown
or missing rights fail closed. Packing/version/budget and a named, versioned, immutable-hash-pinned
reference or generator tokenizer must be frozen. Starting context budget is provisional2,000tokens
(D-265); synthetic words/fixture counts cannot establish actual model token-budget delivery.

Additional metrics may inform **development-only configuration selection** after those controls and
the comparison rule are frozen. Held-out labels remain sealed from implementers and selection;
held-out verification does not retune the selected configuration. No retrospective release-bar change.

Migration still owed: P3 metric/context producers and two schemas currently label these outputs
`proposed_provisional_not_official` and only support synthetic/fixture counters. Leave their accepted
bytes and historical results intact. Claude needs a separately scoped version/compatibility/tokenizer
packet before changing them. This record approves policy, not a production tokenizer, schema
migration, live measurement, eval-label exposure or experiment.
