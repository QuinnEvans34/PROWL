# Literature retrieval design package

**Current execution plan (October 17):** [AI expert completion specification](AI-EXPERT-COMPLETION-SPEC.md).
Nine ordered steps define the remaining feature, acceptance evidence and linked Trello tasks.
Step 1: [frozen acceptance/query/response mapping](AI-EXPERT-CONTRACT-V1.md), 83 offline checks pass.
Step 2: [choice comparison rejected](CHOICE-SELECTION-2026-10-17.md); response quality remains open.
Next: [W04-01 — literature workflow/rebuild qualification](https://trello.com/c/Z9QSh78P), Step 3.
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
