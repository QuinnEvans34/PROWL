# Finish the development review

**October 17, 2026:** Review tracking is ready. No human decisions have been entered, neither split
is frozen, and retrieval tuning is not released. The existing positive topic feedback remains valid;
it is not expanded into evidence-label or second-pass approval.

## Start with the ten changes

Read questions **1, 3, 5, 7, 9, 10, 12, 16, 17 and 19** in the
[readable Q&A](DEVELOPMENT-QUESTIONS-AND-ANSWERS.md). Report `accept`, `revise`, or `unsure` by number.
For example, “Wording and answers: 1 and 3 accept; 5 unsure about the comparison.” You can review
several at once. This first decision concerns question usefulness, clarity and the proposed answer.
It does not claim that you checked every evidence label. Review the remaining twenty too before
the complete development set closes; earlier topic feedback alone does not establish that step.

## Then check the evidence

Use the exact excerpts in the local Markdown packet
`outputs/prowl/plain-language-20261017/source-evidence-v4.md`, alongside the Q&A. For each case check:

- The source actually supports each required fact, with the correct study, organ and comparison.
- Direct support, background context and limitations have the appropriate labels.
- The answer preserves important limitations; numerical ranges are not presented as averages.
- The source judgments account for known alternative support. If an excerpt is unclear, inspect
  its full source context rather than guessing.
- Refusals and missing-evidence responses have the right reason and do not invent an answer.

Record these separately, such as “Evidence labels: 1 accept; 3 revise because …”. Uncertainty stays
open until resolved. This is source-based review by the project owner, not clinical certification
or an independent expert rating. The current [draft](../../../configs/evidence/evaluation/development-v4-draft.json)
contains the complete concepts, spans and source judgments.

Once wording/answers and evidence are accepted for all thirty cases, do a second consistency pass:
compare related questions, duplicate intents, alternate support, answerability and limitations across
the set. Only report that pass complete after doing it. This is separate from the private cross-split
review described in the [protected-authoring worksheet](PROTECTED-EVALUATION-AUTHORING.md).

## How decisions are recorded

The [human-review record](../../../configs/evidence/evaluation/development-v4-human-review.json)
starts with an empty event list. It pins the exact draft and readable-answer file. Each later event
records the supplied human statement, reviewer, date, stage, decision and affected case hashes.
Codex may transcribe an explicit decision from Quinton; it must not invent one from a request to
continue, its own evidence review, or a passing test. No tool here authenticates who supplied a
statement: the record is an attestation backed by the conversation and Git history.

Append events; preserve earlier decisions when a correction supersedes them. Any new wording or
evidence decision reopens the set-wide consistency pass. Changing the draft or readable answers
invalidates the record binding; create a new version and retain the previous record. Do not simply
replace its hashes to carry old decisions forward. Contiguous sequence checks detect broken event
order, but cannot prove append-only history by themselves; Git preserves that history.

Run the read-only tracker from the repository root:

```sh
.venv-retrieval/bin/python -m src.retrieval.development_review \
  --development configs/evidence/evaluation/development-v4-draft.json \
  --review configs/evidence/evaluation/development-v4-human-review.json
```

It reports accepted/pending/revise/unsure counts without changing the draft. A valid record is not
evidence that all reviews are complete. Even a fully attested development record returns
`ready_for_tuning=false`: actual corpus/span validation, independent protected authoring, private
cross-split review, encrypted backup and the final versioned split-freeze artifact remain required.
The tracker never reads or validates protected questions. Do not provide private content or paths.

## This checkpoint

Nineteen new tests pass using invented cases and attestations. They cover stage separation, premature
or incomplete consistency passes, corrections, stale question/answer bindings, tampered hashes,
case identity, event order, closed fields and rejection of held-out/external inputs. The actual v4
record validates with **zero events and thirty pending cases in each review stage**. No tests establish
medical correctness or human review. The previous 42-check draft/corpus checkpoint is unchanged.

Local receipts are under `outputs/prowl/development-review-20261017/`; producing hashes are in
`configs/evidence/evaluation/development-v4-review-tracking-checkpoint.json`. No model, database,
service, selector, training or protected-storage operation occurred.
