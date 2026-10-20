# Evaluation preparation and current coverage

**Status:** Public reconciliation delivered; human delta review and independent workflow choice pending.
AI-03 remains open. This preparation does not freeze private questions or admit evaluation/tuning.

## Current versions and preserved approvals

The current corpus is `corpus-disease-v1`:14 papers/1,179 passages. Proposed development v6 remains
30 questions:20 answerable,8 refusals,2 evidence gaps. The v4→v5 review chain verifies as complete;
the v6 review is a separate empty record. Quinton's Week3 answer/UI acceptance applies to that
exposed quality packet, not automatically to the formal v6 source-label changes.

The new [change-only packet](../../../outputs/prowl/evaluation-preparation-20261020/changes-to-review.md)
contains two replacement questions,23 added/changed spans and a separate appendix of100 changed
source judgments.28 retained cases have unchanged core fields/expected concepts. This avoids
repeating their entire review; it does not silently copy acceptance to new evidence. The two
corpus-gap judgments and consistency of modality, population and limits still need confirmation.
The earlier complete v6 packet and all v5/v4 records remain unchanged.

`scripts/retrieval/prepare_evaluation_delta.py` verifies the prior acceptance chain, current draft,
actual canonical evidence, content hashes and current review binding before rendering. It writes
only to a new fixed public-output directory and records no review events. It refuses overwriting
that directory. Review has been requested against this concrete packet.

## Exposures and admission

`public-exposure-v4-preparation.json` adds the24-question source-record screen and30-question Week3
matrix to v3, preserving every old origin. It records346 origins/182 distinct normalized wordings
and the previous33 known semantic intent IDs. New semantic intent grouping remains pending;
these are known named inventories, not exhaustive conversation/test/UI exposure certification.

The public preflight consumes and verifies v4, including exact matrix membership, hashes and union.
The normal private CLI remains disabled before any path prompt or protected read. Rehashing a
modified union, omitting a matrix/wording, changing the preparation status or referencing an external
parent does not admit it.71 focused tests pass, including8 delta tests and6 new exposure tests.
The actual public command reports both readiness flags false and `private_content_read=false`.

## Important coverage gap

An offline check of the existing disease and volume routers against the20 formally answerable v6
questions finds only4 with any candidate route. This is **not an end-to-end answer score**. It does
not run retrieval, generation or evaluation on protected content. One of those4, the inter-reader
outline question (`q:dev2-05`), routes to a disease comparison despite asking about contour variation;
therefore candidate routing must not be equated with evidence suitability or success.

The current demo covers selected disease comparisons and MRI study-volume examples. Formal v6
also tests tumor visibility, contour/reader variability, measurement definitions, anatomy, AI model
limitations and review workflows. Do not silently drop these questions or reclassify source-supported
cases as unanswerable to make the current system pass. Before formal acceptance, close demonstrated
record/selection/composition gaps under the approved evaluation sequence or explicitly review a
versioned product-scope change. No such scope reduction is proposed or applied here.

The immediate preparation output is a truthful coverage ledger, not more prompt tuning. Existing
reviewed source records can be extended later from canonical evidence; expected evaluation answers
must remain excluded from runtime prompts/indexing. No live answer policy changed in this checkpoint.

## Independent labeling workflow

See [the concrete workflow](INDEPENDENT-LABELING-WORKFLOW-2026-10-20.md). A choice between a separate
human-operated assistant and a nominated independent labeler has been requested. No person, model,
isolation, storage or qualification is claimed settled before that choice and its required checks.
Quinton supplies natural questions and reviews prepared evidence; he is not assigned article
search, offsets or JSON authoring. Protected prompts must not enter this development chat.

Private evidence: `outputs/prowl/evaluation-preparation-20261020/` includes validation, source delta,
public preflight, new exposure inventory and offline route results. No private content, model calls,
training, corpus expansion, source-label edits or inferred human hours occurred.
