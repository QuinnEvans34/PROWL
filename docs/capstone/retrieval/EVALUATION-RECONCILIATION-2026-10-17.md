# Expanded evaluation reconciliation — October 17, 2026

The public exposure inventory is now consolidated and consumed by the evaluation preflight.
The private command no longer silently loads the obsolete ten-source evaluation scope. It stops
before requesting a private path while the expanded development set and labeling process remain
unfinished. Live search, synthesis, corpus and retrieval settings are unchanged.

## Delivered

`public-exposure-v2.json` combines all six named inventories: the original development/demo inventory,
scan/routing supplement, live-search supplement, both natural-answer versions and the fixed quality
checkpoint. It retains **262 recorded entries / 136 distinct normalized wordings / 31 known intent
IDs**. Case folding, NFC and whitespace normalization follow the existing question normalization.
Every wording retains its original variants and source locations. Duplicate origins remain visible.

The count includes conservative artificial-fixture and UI strings inherited from earlier inventories;
it is not 136 authored evaluation questions. Known intent IDs come from the old development sets;
the supplements still need semantic intent review. Exact matching cannot detect every paraphrase or
establish independence, and the inventory cannot prove complete coverage of past conversations.
Historical supplements pin producer files that have since changed. Their extracted strings remain
exposed: the new loader verifies each immutable inventory itself, without falsely requiring today's
UI/tests to match obsolete producer hashes. Original development/demo files remain hash-checked.
Prior inventories are unchanged.

The new public command reads bounded named public metadata only:

```sh
.venv-retrieval/bin/python -m src.retrieval.private_evaluation --public-preflight
```

It reports the current **14-paper / 1,179-passage** target, the prior 30 cases, two additional disease
candidates, exposure counts and pending work. Successful execution means the status was read and
verified, **not** that evaluation is ready. `ready_for_private_authoring` and `ready_for_tuning` remain
false. This preflight does not load source payloads or test questions.

Normal private validation and `--prepare` now stop before TTY checks, hidden path prompts or private
reads. The previous hardcoded ten-source loader is retired; its implementation and records remain
in Git history. Changing a readiness boolean cannot activate a freeze: that requires a separate
reviewed admission version bound to the actual revised labels. Low-level private validation remains
available for invented-input tests and future human-operated tooling; this is a procedural CLI guard,
not OS isolation or a claim that arbitrary Python callers cannot read files.

## Preserve the reviewed work

An actual public-corpus compatibility audit verifies all **80 retained span locators** from accepted
development v5 against the expanded corpus. All **56 direct spans** are still fully contained in
canonical passages. These mechanical checks preserve valid evidence identities; they do not assert
that all old source judgments or gap labels remain complete after adding sources.

The [scope ledger](../../../configs/evidence/evaluation/development-scope-reconciliation-v1.json)
keeps the prior 30 cases and two disease additions as candidates. It does not silently create a
32-case final evaluation or replace accepted questions. The unchanged target is 30 development
cases: 20 answerable and 10 unsupported/refused, covering all five families.

The outstanding evidence work is explicit:

- For the 20 prior answerable cases, review the **four added papers**: 80 new source/case judgments.
  Existing ten-source acceptance is retained; it is not automatically extended to new sources.
- Recheck the two prior evidence gaps against the expanded corpus.
- Complete full-corpus source judgments for the two disease candidates; their selected supporting
  contexts are prepared, but other sources are not automatically irrelevant.
- Select final membership and reconcile information needs, preserving family and answerability balance.
- Record the independent disease-evidence decisions and the cross-question consistency review.

The local [added-source reading pack](../../../outputs/prowl/evaluation-reconciliation-20261017/added-source-reading/README.md)
contains all **232 canonical passages from the four added papers**, with titles, attribution,
licenses, offsets and identities. Overlapping passages are not independent evidence. Source text
remains local under the retained redistribution policy. This supports engineering labeling and
review without asking Quinton to find articles or type offsets.

## Independent review and protected workflow

The [two-question evidence pack](../../../outputs/prowl/answer-quality-20261017/disease-evidence-review.md)
is ready for Quinton's separate review of the proposed scope, supplied support and consistency.
The request is pending; no acceptance is inferred from permission to continue development. This
would be human verification of agent-proposed labels, not independent clinical/inter-rater validation.

Protected questions require a separate process: Quinton supplies natural questions privately;
an independent operator must perform or assist source search/technical labeling, and the designated
reviewer checks supplied evidence and consistency. The development agent cannot see the protected
questions or produce their labels. A local human-operated labeling aid can be designed and tested
with invented cases, but no such tool or operator is qualified by this checkpoint. Do not assign
manual article searching, JSON authoring or offset entry to Quinton to get past the gate.

The old private v1 schema also names Quinton as both author and reviewer. If the agreed process uses
another operator/reviewer or assisted label preparation, a new schema must record those actual roles
and provenance before use; do not impersonate Quinton in old fields. The old templates remain historical.
No protected questions are requested now, and no private storage or backup is created or accessed.

## Next implementation

Finish the source-impact review and proposed final development membership using the supplied corpus.
Resolve independent review and the protected-labeling workflow, then version the full evaluation
admission. After the required freeze, compare lexical, dense and hybrid retrieval against the same
labels. The fixed quality checkpoint's failures remain unchanged evidence for that comparison.

This work closes public exposure consolidation and stale-loader prevention. It does not close AI-03,
qualify an answer policy, or release retrieval tuning. The protected set, backup and freeze remain
pending. Training, full selector, model calls, live queries and human-hours credit were not involved.

## Verification and records

Focused invented-input checks cover omitted/changed inventories, rehashed union tampering, stale
original development files, path/symlink/size bounds, invalid readiness changes, old-corpus fallback,
and stopping before private prompts. Existing private-validator tests remain applicable to the
unchanged low-level validator. Test results and file hashes are recorded in the checkpoint receipt.

- [Consolidated exposure inventory](../../../configs/evidence/evaluation/public-exposure-v2.json)
- [Current reconciliation state](../../../configs/evidence/evaluation/evaluation-reconciliation-v1.json)
- [Scope/compatibility ledger](../../../configs/evidence/evaluation/development-scope-reconciliation-v1.json)
- [Checkpoint receipt](../../../configs/evidence/evaluation/evaluation-reconciliation-checkpoint-v1.json)
- Local audit, preflight and reading pack: `outputs/prowl/evaluation-reconciliation-20261017/`.
