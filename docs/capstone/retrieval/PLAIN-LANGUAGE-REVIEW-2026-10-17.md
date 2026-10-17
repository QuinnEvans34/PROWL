# Plain-language development revision and anatomy coverage review

**Result:** Draft v4 revises ten questions, two in each answerable family. It preserves twenty
other records, all thirty case IDs and the 20-answerable / eight-refusal / two-gap balance.
The seven-source corpus is unchanged. No retrieval tuning or generation occurred.

Read the [questions and expected answers](DEVELOPMENT-QUESTIONS-AND-ANSWERS.md). Review the changed
questions **1, 3, 5, 7, 9, 10, 12, 16, 17 and 19**; the previous topic approval does not establish
approval of revised evidence labels. The exact local source-text packet is now Markdown too:
`outputs/prowl/plain-language-20261017/source-evidence-v4.md`.

## Changes that matter

| Cases | Revision | Evidence impact |
|---|---|---|
| 01 | Why can a pancreatic tumor blend in with surrounding tissue on CT? | Broader mechanism question replaces one study's density-threshold question. Four retained sources now have direct support; additional context retained. |
| 03 | Describe limitations of the study of tumors that look like surrounding tissue. | Same study-specific limitations, with terminology reduced in the question and explained in the answer. |
| 05 | Can specialists from different fields draw different-sized outlines? | Added explicit same-cohort study design evidence; retained numerical comparison and background review. |
| 07 | How did one study handle uncertain edges and nearby structures? | Same research-protocol scope; no universal contour rule. |
| 09 | What part of the intestine curves around the pancreatic head? | Same duodenal relationship with simpler wording. |
| 10 | How long is the pancreas? | Replaces the anatomy-priors question with a directly cited length range under needs v2; not a population average. |
| 12 | Can an AI that divides the pancreas into parts necessarily find it on its own? | Same reference-crop counterexample; no autonomous localization claim. |
| 16 | Does better outlining prove that an AI saves doctors time? | Same pancreatic-study example and unmeasured-workload qualification, with model comparisons preserved in the answer. |
| 17 | Can reviewers agree more with AI but draw less accurate outlines? | Same agreement-versus-accuracy evidence; prostate scope remains explicit. |
| 19 | How were disagreements about pancreas-part labels settled? | Same shared-review/mutual-agreement process; no independent agreement claim. |

Changed question records have version 2 and label version `dev2-draft-v3`. Question 10 changes intent;
it is not presented as a paraphrase of its predecessor. Prior versions remain exposed development
material and must remain excluded from protected near-duplicate intents. No change was made to the
existing refusal questions or the two corpus-gap cases. Technical cases remain intentionally present.

## Anatomy and size decision

[Information needs v2](planning/INFORMATION-NEEDS-V2.md) explicitly adds basic size/reference-statistic
context to N3.3. It incorporates the pinned, unchanged v1 plus one documented amendment, keeps all
25 needs/five families and RF1–RF9, and does not authorize current-patient comparisons. The user's
plain-language request and continuation authorize this preparation; it is not an inferred approval
of final labels. The amendment discloses prior source/experimental exposure in this lane.

PMC9317715 body-11 supports a reported **12–15 cm length range**. That is enough for the revised
length question, with its limitation. It does not support treating the midpoint as an average or
turning length into volume. PMC10177524 adds context that pancreas size/shape/location vary.
The broader “How large is the average pancreas?” remains a clarification/reference-coverage task;
the system must not silently replace it with question 10 or imply that the length range answers a
population-average request. No clarification wire state or free-text endpoint was implemented here.

Two previously identified reference leads received a bounded browser check:
[PMID 22434256](https://pubmed.ncbi.nlm.nih.gov/22434256/) exposes a retrospective CT volume-study
abstract with cohort and measurement information; [PMID 22158073](https://pubmed.ncbi.nlm.nih.gov/22158073/)
returned incomplete browser content in this check. These are discovery leads, **not admitted sources**.
Full-text reuse rights, normalized evidence, corpus admission and applicability have not been qualified.
No average from those leads enters the frozen corpus, expected answer, prompt or reference-comparison
feature. Actual measurement-aware comparisons remain required later, after core RAG acceptance.

## Labels and consistency

V4 has **70 spans: 49 direct, 16 partial context and five limiting**. All required concepts have
source-linked direct support and every direct span is fully contained in a frozen passage. Question
01 now has four direct works; the other nineteen answerable cases each have one. The source recall@5
ceiling is still 1.0, a feasibility calculation, not measured retrieval performance.

The same authoring agent reviewed revised questions, proposed answers, source scope, source judgments
and related intents. For question 01, the broader wording was checked across all seven retained
representations with lexical/manual inspection; direct support was retained from PMC8145900,
PMC10177524, PMC8357939 and PMC8997008, with TAGS context distinguished from direct mechanism support.
Case 05's exact cohort design and case 10's full anatomical sentence were checked in source context.
Other revisions preserve the narrower original evidence task. Bounded review does not prove exhaustive
relevance; newly retrieved plausible sources still require the documented blinded adjudication process.

Shared source does not itself mean duplicate intent. The existing 06/20, 11/12 and 17/18 relationships
remain disclosed, along with all prior wording/intent exposure. The removed anatomy-priors intent
remains exposed too. No protected split was read or authored, so no cross-split independence claim is
made. Difficulty labels remain author judgments, not measured difficulty or chunk requirements.

## Versioned checker and verification

- New closed schema `development-draft-v2.schema.json` permits positive question revision numbers
  and requires both the information-needs amendment and inherited v1 hashes. V1 stays unchanged and still rejects question version 2.
- The offline checker explicitly dispatches only known draft schemas and binds v2 to the actual
  needs-v2 amendment and inherited v1 files. Unknown schema names, missing/stale needs bindings, held-out labels, human approval,
  private fields and frozen status remain rejected. Existing input-path guards remain in force.
- **42 focused checks passed**, including eleven new revision/binding/guard checks. The new schema and
  checker were exercised with invented inputs; both real v3 and v4 pass separate corpus validation.
- `--require-ready` still refuses v4. Mechanical validity is not semantic/human approval or tuning release.
- Exact question ordering/text matches the readable copy; exactly ten records changed, two per family.
  Prior draft data, v1 schema, source bundles and prior receipts remain unchanged. Checker/test source
  hashes intentionally changed; historical receipts remain producing-version records, not current-code claims.

Current canonical draft SHA-256:
`7db15aa85606247134675681bb077e056045c9beecce6e2960634bbba0f786aa`.
Public receipt: `configs/evidence/evaluation/development-v4-review.json`.
Local test/validation/quote artifacts: `outputs/prowl/plain-language-20261017/`.

## Next

Quinton reviews the revised wording and expected support, then completes semantic adjudication and
the consistency pass. Independently protected authoring and split-freeze/backup receipts remain
required under the existing protocol. Do not restart tuning because technical checks pass.
No model/encoder/database calls, service changes, training, full selector or inferred hours occurred.
