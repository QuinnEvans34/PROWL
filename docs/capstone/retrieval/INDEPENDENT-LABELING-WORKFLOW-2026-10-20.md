# Independent labeling: concrete workflow for selection

**Status:** Preferred process prepared; operator choice pending. Not an active private authoring tool.

The independence required here is separation from development exposure and tuning. Assisted labels
remain machine-proposed until reviewed; this process does not establish clinical or inter-rater
validation. The current private v1 schema cannot truthfully represent all these roles and must not
be used with invented author/reviewer fields.

## Recommended arrangement

1. Quinton authors fresh natural questions privately, after public scope and admission are ready.
   He does not paste them into this chat, Trello, Git or an agent-connected terminal.
2. A separate human-operated labeling assistant searches the frozen source-reading corpus and
   prepares proposed concepts, attributed exact excerpts, limitations, source judgments and
   answerability. An independently nominated person can fill this role instead. Neither uses
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

The next decision is the operator arrangement, not writing30 questions now. Implementation and
qualification follow that selection. No new chat, service, private image, assistant model run or
protected data access was created by this preparation.
