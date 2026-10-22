# Independent labeling: selected assisted workflow

**October22 amendment:** Quinton selected a separate Claude chat to draft fresh questions.
The [Claude handoff](CLAUDE-EVALUATION-PROMPT-2026-10-22.md) supplies public sources/exclusions and
records AI authorship with human semantic/consistency review. The earlier human-only authoring
arrangement below is historical. External Claude drafting is not all-local storage or proof of
independence; protected evaluation admission remains closed. No real questions are available here.


**Status:** Quinton selected the separate human-operated assisted workflow on October20.
Preparation is complete. October21: the [invented-data application](LABELING-APPLICATION-2026-10-21.md)
is implemented and running separately on5182; protected authoring remains unqualified/inactive.

The independence required here is separation from development exposure and tuning. Assisted labels
remain machine-proposed until reviewed; this process does not establish clinical or inter-rater
validation. The current private v1 schema cannot truthfully represent all these roles and must not
be used with invented author/reviewer fields.

## Selected arrangement

1. Quinton authors fresh natural questions privately, after public scope and admission are ready.
   He does not paste them into this chat, Trello, Git or an agent-connected terminal.
2. A separate human-operated labeling assistant searches the frozen source-reading corpus and
   prepares proposed concepts, attributed exact excerpts, limitations, source judgments and
   answerability. No independent person was nominated. The assistant does not use
   candidate system answers as gold labels or copies development expected answers.
3. The tool derives offsets and hashes from selected canonical text, never from free-form model
   offsets. It shows excerpt context and provenance next to the proposed meaning. Uncertain support,
   missing source judgments and conflicting evidence remain unresolved, not forced into acceptance.
4. Quinton reviews supplied meaning/evidence and completes a separate consistency pass. A separate
   reviewer may be designated and recorded if available. Human corrections/rejections are retained.
5. The operator checks exact and semantic overlap with all public exposures, including new matrices
   and prior conversational examples. Paraphrases of exposed intents stay in development. If the
   corpus cannot support the specified fresh-intent balance, stop and report protocol feasibility;
   do not manufacture30 independent questions or redefine independence after seeing results.
6. Validate the revised schema privately; freeze content, model/tool/source versions and review
   history; verify approved encrypted storage and independent backup. Publish only the closed
   content-free receipt. Run the frozen system under a human-operated evaluator after admission;
   only aggregate outcomes and hashes leave the private workspace.

## Required role/provenance fields for the new schema

Record question author, label preparer, actual assistant model/tool identity (or none), semantic
reviewer, consistency reviewer and private operator separately. Include timestamps, exact source
and content bindings, machine-proposal/human-correction lineage, public-exposure version and explicit
semantic-overlap adjudication. Identical human identities must remain visible; do not describe them
as independent raters. A development agent is not an eligible protected label preparer/reviewer.

## Before real protected use

- Qualify on invented cases: exact span reconstruction, duplicate/ambiguous matches, missing concepts,
  unsupported claims, contradictory evidence, changed corpus, exposed intent, role provenance and
  rejection of unresolved cases. Do not print private contents in errors or telemetry.
- Run separately from development agents and their terminals. Verify network/logging behavior and
  intended storage permissions. A local process or a new chat alone does not prove isolation.
- Have the human verify source context and labels before evaluating the candidate; assisted source
  search can miss evidence and same-model labeling may share the candidate's blind spots.
- Version admission and validator against current needs/corpus/exposure. Keep the existing CLI
  blocked until these conditions and the actual protected storage/backup receipt are satisfied.

## Implemented preparation boundary

`src/retrieval/assisted_labeling.py` is a pure prototype: no filesystem, network, model calls or
acceptance writes. It builds per-source requests from a question, proposed concepts and canonical
source text; validates source hashes; reconstructs exact unique quotes into Unicode character
offsets; rejects invented/ambiguous quotes, unknown concepts, missing sources and model offsets;
and renders an escaped review page with missing/contradicting/uncertain evidence visible.
Every output remains `machine_proposed_human_review_required`, with both acceptance/readiness false.
Seventeen invented-data checks cover these boundaries, malformed types and safe errors. Exact
matching is not entailment, completeness or semantic-independence verification.

This prototype is not the whole labeling application. The next implementation must supply a
separate human-operated host, actual model identity and token-budget/chunking policy, canonical
corpus passage alignment, concept/answerability proposals, role/history schema and human correction/
consistency controls. Qualify those on invented cases first, including failure logging, network
behavior, semantic-overlap adjudication and refusal to freeze unresolved labels. Only then complete
storage/backup and frozen admission before real private questions. Existing CLI access remains shut.

Quinton will enter fresh questions and review supplied meaning/citations, without paper search,
offsets or JSON editing. This development chat may implement/test the tool on invented content,
but may not operate it on the real held-out questions. No new chat, service, private image, model
run or protected-content access was created. No further operator-choice question is pending.


## October21 implementation update

The separate rehearsal now provides local-model proposals, source-linked sentence selection,
full source context, natural-language revision, explicit accept/reject, separate consistency,
readable history and export.44Python+2UI checks and a bounded real-model rehearsal are complete.
The local assistant still makes semantic/relevance errors; one corrected supported case passed
engineering rehearsal, while the gap case was rejected for unnecessary context. No Quinton
acceptance or independent-label quality is inferred. See the application report for exact limits,
latency, failed attempts and remaining real-corpus/private-use work. Earlier prototype-only language
above describes the prior checkpoint.
