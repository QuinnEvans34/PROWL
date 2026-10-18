# Disease-source review and proposed development v6

The four added papers have been reviewed against the existing development questions. The proposed
30-question set includes both disease questions while preserving 20 answerable cases, eight refusals,
two evidence gaps and all five families. This completes the engineering source-impact work from
[the reconciliation checkpoint](EVALUATION-RECONCILIATION-2026-10-17.md); human review and the
independent protected evaluation remain pending. It does not improve or qualify live model answers.

## Read the changes

- [Short change review](../../../outputs/prowl/development-v6-review-20261017/changes-to-review.md)
- [All 30 questions, expected content and expandable supplied evidence](../../../outputs/prowl/development-v6-review-20261017/all-questions.md)

These local files contain exact attributed evidence. Expected content is an evaluation reference;
it is not indexed as literature or supplied to the model. Earlier approvals are preserved. Quinton
can review the changes in one pass without searching papers, writing JSON or entering offsets.

## Membership and source judgments

| Change | Reason |
|---|---|
| Replace q:dev2-02 with q:dev6-31: “Could the size of the pancreas head indicate any specific diseases?” | Quinton's exact question addresses the accepted disease-context direction instead of one study's phase timing. |
| Replace q:dev2-15 with q:dev6-32: “What additional findings help distinguish inflammation from a pancreatic tumor?” | The assistant-authored, stakeholder-relevant example tests cited imaging context instead of TAGS metric/grid details. |
| Add support to q:dev2-01 | The PDAC review directly addresses low tumor-to-parenchyma contrast. |
| Add optional context to q:dev2-10 | AIP review discusses age/background volume context; it does not replace the original small MRI control-group mean/SEM qualifications. |

The two displaced questions remain in v5 and the exposure history. The other 28 question wordings,
expected scope boundaries and required concepts are unchanged. Answerable families are appearance5,
measurement4, anatomy3, ai_limits4 and review4. [Needs v3](planning/INFORMATION-NEEDS-V3.md) adds N1.6
for general disease context, inheriting the v2 and v1 needs and all refusal boundaries. This follows
the exposed answer-quality diagnostic; it is not blind preregistration or held-out evidence.

The [source-impact ledger](../../../configs/evidence/evaluation/disease-source-impact-v1.json) records:

- 80 added-source judgments: four full normalized papers against all 20 prior answerable concept sets.
- 28 disease judgments: both candidates against all 14 sources. The ten prior papers were screened
  with broad lexical/context searches; the four added papers were read in full. This is bounded
  engineering review, not exhaustive independent gold relevance.
- Two gap rechecks: duct imaging does not specify inclusion in a pancreas contour; diagnostic
  uncertainty does not supply calibrated segmentation-boundary uncertainty. Both stay insufficient.

The proposed final set has 280 answerable source/case judgments, 100 labeled spans and 73 direct
spans. All direct spans fit an actual indexed passage. Its source-recall@5 theoretical ceiling is
1.0; this is feasibility arithmetic, not measured retrieval performance. No retrieval run occurred.

Both disease questions retain their prior required concepts, expanded evidence and modality/subtype
limits. A cancer-only cohort supports reported signs but cannot establish discrimination against
inflammation. A limiting span makes that population restriction explicit. No numerical head-size
diagnosis rule, current-scan interpretation, treatment advice or inferred finding from an outline
is introduced. These are source-bound development labels, not current clinical recommendations.

## Versioned tooling and review state

Development schema v3 admits N1.6 and the user's authorship explicitly; older development/private
schemas do not silently inherit the new need. The v6 draft binds all three need documents. Review
schema v2 supports new case identities with exact content/answer bindings, closed event fields and
the same consistency rules. The new v6 record has zero events: no decision is inferred from “continue.”
The accepted v5/v4 records remain intact. Empty v6 bookkeeping does not revoke old approvals;
no automatic cross-generation carry is claimed. Record the actual changed-scope decision and any
verified inherited decisions separately when resolving the review, without asking to redo old work.

Exposure v3 preserves v2 and adds v6 origins: 292 entries, 136 normalized wordings and 33 known intent
IDs. Both new wordings were already exposed. The current public preflight checks these bindings and
reports engineering review complete, human review pending. Normal private CLI still stops before
private prompts/reads. Readiness remains false; changing a JSON flag cannot authorize a freeze.

Validation: 132 distinct focused checks passed across retained attempts (90 initial passes, 11
repaired fixture checks, 31 review checks). The first v6 preparation failed on an undeclared concept
ID before writing the draft; the corrected existing ID is retained. Eleven first test setups lacked
an imported dependency fixture; after repair only those failed tests were rerun. One review-test
command named a nonexistent module and collected no tests; the corrected command passed31. Logs
and original failed producer/test files are kept locally. Actual-corpus CLI validation, current
public preflight and the empty human-review record/CLI also pass. No synthetic review events were
written to the actual record.

Next: review the proposed replacements, added evidence and consistency delta, then resolve the
independent protected-labeling operator/schema, storage/backup and final admission. Quinton supplies
natural questions; engineering handles evidence preparation. After the required freeze, compare
retrieval configurations, address the documented generation/readability failures, and complete core
acceptance before the required measurement-aware extension. Training/full selector stay unstarted.
