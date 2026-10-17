# Literature retrieval design package

**Current execution plan (October 17):** [AI expert completion specification](AI-EXPERT-COMPLETION-SPEC.md).
Twelve ordered steps define the remaining feature, acceptance evidence and linked Trello tasks.
Steps 1–9 qualify core RAG; the [required measurement-aware extension](MEASUREMENT-AWARE-EXPERT-PLAN.md)
follows in Steps 10–12 and is part of final delivery, not a stretch goal.
Step 1: [frozen acceptance/query/response mapping](AI-EXPERT-CONTRACT-V1.md), 83 offline checks pass.
Step 2: [choice comparison rejected](CHOICE-SELECTION-2026-10-17.md); response quality remains open.
Step 3: [bounded literature workflow qualified](LITERATURE-WORKFLOW-CLOSURE-2026-10-17.md); broader G3 remains open.
Step 4: [seven-source corpus frozen](CORPUS-FREEZE-2026-10-17.md), 693 passages; 6 direct / 15 partial / 4 coverage gaps.
Step 5: [plain-language revision](PLAIN-LANGUAGE-REVIEW-2026-10-17.md) delivered: ten revised questions, 70 spans, 42 checks; v4 remains human-review pending.
Read the [plain-language questions and expected answers](DEVELOPMENT-QUESTIONS-AND-ANSWERS.md), grouped in batches of five.
These are grading references, not indexed evidence or prepared runtime responses; [six current-path separation checks pass](ANSWER-KEY-BOUNDARY-2026-10-17.md).
For source review, read all questions and evidence in `outputs/prowl/development-review-q01-q15-20261017/all-questions.md`.
Each of the 30 Markdown pages includes the expected answer, exact excerpts, limitations and all source judgments.
Quinton accepted Q1–15's wording/answers and evidence; Q16–30 remain. He prefers one reading pass and consolidated feedback, not more small-batch prompts. The renderer is `scripts/retrieval/build_development_review_packet.py` and accepts only the fixed public v4 inputs.
Next: follow the [development review workflow](DEVELOPMENT-REVIEW-WORKFLOW.md). Exact-version human-review tracking is delivered (19 new checks); no decisions inferred. Complete semantic/consistency review and independent protected authoring; AI-03 remains open.
The bounded demo/workflow exists; semantic quality, broader evaluation and finding integration remain
open. Full selection and training stay parked. See the [current handoff](CHAT-HANDOFF-2026-10-15.md)
for implementation evidence and dated service observations.

Design authority: D-260–D-265 and the approved [scope](planning/SCOPE.md) /
[phases](planning/PHASES.md). [Revised P3 packet](../operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md)
is issued for Quinton dispatch. Additional span/delivered metrics remain a proposed
D-085 amendment; models and execution permissions remain separately gated.

**Status:** Approved Plan 07 design baseline; implementation dependencies remain  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/07-literature-retrieval.md`](../implementation/07-literature-retrieval.md)

## Purpose

This directory defines the public-literature side of PROWL: acquire permitted sources, create stable
passages, build a local vector/search index, retrieve evidence for a bounded question, and answer only
with claim-level support or refuse.

## Package map

| Document | Question answered |
|---|---|
| [`CORPUS-AND-RIGHTS.md`](CORPUS-AND-RIGHTS.md) | What literature enters, how is it acquired/versioned, and what text may be stored or released? |
| [`QUERY-AND-RETRIEVAL.md`](QUERY-AND-RETRIEVAL.md) | What context may form a query and how are lexical/vector/hybrid ranks produced? |
| [`QUESTION-SET-AND-EVALUATION.md`](QUESTION-SET-AND-EVALUATION.md) | Which questions/relevance labels test recall@k, MRR, and refusal without tuning leakage? |
| [`GROUNDED-RESPONSE.md`](GROUNDED-RESPONSE.md) | How are retrieved passages converted into supported claims or a safe refusal? |
| [`TOOL-SELECTION.md`](TOOL-SELECTION.md) | What must a local vector stack prove before D-202 is resolved? |

## Non-negotiable rules

1. Imaging and literature remain separate until the review interface.
2. No patient image, mask, source report, identifier, ground truth, or diagnosis enters retrieval.
3. Corpus scope follows approved annotation/review question families.
4. PubMed/PMC acquisition uses approved NCBI services and current limits.
5. PMC visibility/free access does not automatically prove reuse rights.
6. Rights are decided per document/text representation before indexing.
7. Restricted text remains local/off-Git; releases contain manifests/citations as allowed.
8. Every passage resolves to exact source identity and locator.
9. Corpus/chunk changes create new corpus/passage identities; index changes do not rewrite corpus.
10. Lexical retrieval is the control; vector/hybrid must be measured.
11. D-260 selects PostgreSQL + pgvector; D-202 selects configurations after platform, rebuild, filter and evaluation evidence.
12. Development questions tune; held-out questions do not.
13. Every displayed claim cites one or more retrieved passages that support it.
14. Unsupported, conflicting, weak, out-of-scope, or unavailable evidence produces limits/refusal.
15. Retrieval failure cannot block imaging or create a simulated answer.

## Planned records

- source/work and source-version notice;
- document/text representation and rights decision;
- passage and exact locator;
- corpus snapshot;
- embedding/index manifest;
- structured finding/question/query;
- ranked retrieval result with component scores;
- frozen question/relevance/refusal labels;
- atomic claim/citation/response;
- retrieval/response evaluation; and
- G6 release selection.

Plan 09 owns executable schemas/fixtures. Plan 10 owns roots, secrets, dependencies, generation
provider, cost, retention, and release packaging.

## Existing files

- [`../../../references/literature/README.md`](../../../references/literature/README.md) is the
  intended reference/governance area.
- `../../../pubmed_samples.xml` is an exploratory parser candidate only. It is not an approved source
  snapshot or corpus and may contain records outside the final scope.

No existing text file is promoted merely because it is already in the repository.

## Next review

Quinton approved P07-01 through P07-16 on 2026-09-09. The design and question-set boundary are
approved; September 28 amendments govern current engine, acquisition, storage and phase choices.
D-202 configuration evidence and P1/P2 human review remain open.
