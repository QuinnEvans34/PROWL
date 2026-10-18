# Literature adapter and disease evidence preparation

Version 1 — October 17, 2026. Offline evidence contract delivered; retrieval and answer quality remain unqualified.

## What is implemented

`src/retrieval/literature_adapter.py` binds a literature candidate to the frozen corpus and a supplied
ranked snapshot. It reconstructs displayed source text and citation metadata from verified canonical
records. Returned evidence is explicitly unassessed; neither a hit nor an empty result becomes a
supported answer or a semantic refusal.

`FrozenLiterature` verifies the complete batch inventory and canonical source bindings, then retains
isolated copies of the target and passage records. The trusted loader must verify manifest file pins
before construction; actual replay used the existing bounded hash-checking loader. Client input must
never choose the corpus, configuration, scope-review record or source files.

The interface is versioned and closed:

| Record | Required content | Boundary |
|---|---|---|
| Scope review v1 | Exact request/plan hashes, general-literature-only decision and reviewer | Caller-owned review, not a client field or a decision inferred from keyword routing. |
| Ticket v1 | Original question, request/plan/review identities, manifest hash, inventory, retriever ID/configuration hash and limit | Limits 1–50; no question rewriting, expected answer or gold labels. |
| Snapshot v1 | Ticket hash, complete/failed state, bounded failure code and ordered passage ID/record hash/score entries | Unknown fields, wrong identities, duplicate/foreign passages and nonfinite scores fail. Provider text is not accepted. |
| Evidence v1 | Verified records in supplied order, ranks/scores, target/snapshot identities and state | Answer is null; assessment not performed; generation not called. |

`prepare()` checks the caller-bound routing plan and scope review before making a ticket. Unavailable
measurement/comparison/case-finding routes cannot be overridden by a fresh review. `accept()` rebuilds
that ticket, validates the supplied snapshot and resolves exact canonical records. `verify()` compares
canonical result bytes with the expected result from trusted original inputs; a new hash alone cannot
legitimize a changed answer, source or score type.

Evidence states are `evidence_unassessed`, `no_results` and `retrieval_failed`. Contract violations
raise an error rather than masquerading as no results. Failure messages are fixed codes, not provider
tracebacks. Scope-review identities are procedural provenance, not authenticated credentials or proof
of clinical review. Passage content remains untrusted material for any future generator.

## Two development questions and candidate evidence

The [candidate labels](../../../configs/evidence/evaluation/development-disease-candidates-v1.json)
contain ten exact, fully contained source spans across these two already-exposed questions. They
record representation/source identities, offsets, text hashes, passage membership and concept roles.
No source text or prepared answer is inserted into the literature index or adapter request.

| Question | Intended answer scope | Candidate evidence and remaining limit |
|---|---|---|
| Could the size of the pancreas head indicate any specific diseases? | General context only; do not infer a disease from an individual head measurement. | Five spans: inflammatory enlargement, inflammatory head masses, inflammatory mimics, the limitation of individual imaging features, and reference-population context. No validated numeric head-size-to-disease rule is established. |
| What additional findings help distinguish inflammation from a pancreatic tumor? | Describe cited general imaging features and their limitations; identify modality/phase and avoid attributing them to this scan. | Five spans: combinations of findings, inflammatory features, PDAC secondary signs, phase-specific CT context and MRCP context. No automatic feature detection or patient-specific differential ranking is implemented. |

Sources inspected for this candidate preparation are the selected relevant sections of PMC8292294,
PMC7376657, PMC8578112 and PMC7183518. This is not exhaustive adjudication across all fourteen papers;
unreviewed sources are unjudged, not irrelevant. Candidate answerability remains pending adjudication.
The reference-context concept for the head question is background, not a required direct gold target.
All ten spans fit completely inside at least one frozen passage; overlapping partial text is not
credited as full containment.

Labels are development-agent judgments. Independent verification and human evidence acceptance are
not recorded. The older accepted v5 set remains unchanged and does not approve these new labels.
Exact local excerpts are retained in `outputs/prowl/literature-adapter-v1-20261017/candidate-excerpts.json`.
These candidate labels do not satisfy the full 30-case draft checker or release tuning.

## Verification

- Final targeted run: **127 passed** — 34 adapter, 69 routing, 15 corpus-inventory and nine span-label
  checks. Initial 125 passed; review added oversized-number and boolean/numeric-integrity checks,
  then the final affected run passed. No failed attempt was discarded.
- Verified source bindings against all 14 papers, 41 batches and 1,179 passages without changing them.
- Two actual-corpus replay packets each contain the first three canonical passage IDs, with zero
  scores. This deliberately arbitrary ordering proves membership/provenance only. It is **not search**,
  a retrieved answer, gold-assisted ranking, or a retrieval-quality measurement.
- Both packets replay under the final adapter; target, request, original wording and scope-review
  identities remain bound. Raw evidence stays local. The public scope-review file labels this as
  development engineering admission for offline contract replay, not clinical or live approval.
- A new [exposure supplement](../../../configs/evidence/evaluation/public-exposure-scan-supplement-v1.json)
  records 44 known wordings and source-file hashes, preserving the previous inventory. It still needs
  integration into the versioned private checker before protected authoring. Exact word matching alone
  cannot establish semantic independence.

No database search, model call, service change, endpoint integration, protected-content access,
training or full selector ran. Existing demo, query/routing contracts, corpus and prior producing
receipts are unchanged. Local evidence and both test reports are under
`outputs/prowl/literature-adapter-v1-20261017/`; checkpoint pins retain their exact identities.

## Next step

Reconcile the disease development labels and independent labeling workflow with the evaluation
protocol, including the exposure supplement and the distinction between general literature and
case-dependent requests. Quinton supplies natural questions and product feedback; engineering
prepares evidence labels and arranges verification. Do not ask him to search papers or enter offsets.
The independent reviewer/process is still unresolved; do not claim it exists or expose protected
questions to this development chat. No protected questions are requested yet.

After the applicable freeze, connect a frozen retrieval implementation to this boundary and measure
retrieval before evaluating cited responses. Then qualify the scope policy and live free-text path.
This adapter has no search callback or live execution authorization by itself. Measurement/comparison
implementation remains after core acceptance. Counts and quality thresholds have not been relaxed.

Tracking: [AI-03](https://trello.com/c/NctoNxr8). See the
[completion specification](AI-EXPERT-COMPLETION-SPEC.md) and
[routing foundation](QUESTION-ROUTING-FOUNDATION-2026-10-17.md).
