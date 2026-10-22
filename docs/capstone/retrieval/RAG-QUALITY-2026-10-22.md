# October 22 public development quality pass

Authorized scope: the four-block work order (baseline, interpretation, largest
evidence-to-answer gap, verification/integration), with at most two targeted repair
rounds. Preserve the current corpus, model and independent evaluation boundaries.
No training, new real-case inference, labeling application expansion or model sweep.

## Baseline

Producer: main c978d65. Full HTTP answer path through port 5180, approved public
development-v6 questions. Raw results: `outputs/prowl/rag-quality-20261022/baseline-ready/`.
Expected answers and evidence labels are evaluator inputs only, never application requests.

| Outcome on 20 answerable questions | Count | Meaning |
| --- | ---: | --- |
| Relevant complete answers | 4 | Head enlargement, inflammation comparison, CT diameter/volume, study mean pancreas volume |
| Misunderstanding / wrong record | 1 | Reader contour differences incorrectly selected inflammation-versus-cancer records |
| Unnecessary scope refusal | 6 | Questions 6, 13, 14, 17, 18, 20; pancreas-topic and conservative wording gates |
| No reviewed answer coverage | 9 | Search returned passages, but no answer record/composition was selected |

All 10 boundary questions returned no composed answer; eight scope refusals and two
retained corpus gaps. All returned passages matched canonical records and displayed
citations matched those passages. Five local-model compositions completed in
3.91–7.08 seconds, including the irrelevant answer. Successful generation is not
semantic success. This is an exposed development result, not independent acceptance.

## Readiness incident

At 13:13 UTC PostgreSQL reported its data directory as “Not a directory”; at 13:16
it shut down after its lock-file check failed. The mounted Mac drive later matched
the registered UUID and contained the expected pgdata files, but Docker's host mount
was stale. One container start failed at mount admission. With explicit user approval
for the unrelated XML-Adventure interruption, Docker Desktop was restarted and both
containers restored. A first baseline attempt reached readiness before PostgreSQL
finished recovery and is retained separately as a service failure (zero questions).
The subsequent inventory/vector health check passed. No data directories were deleted
or rebuilt. This identifies today's stale-share incident; it does not prove the cause
of every October 21 backend exit.

## Fixed comparison and repair scope

The 32-case `rag-interpretation-development-v1.json` matrix was written before
candidate changes. It includes abbreviations, natural wording, ambiguity, negation,
modality mismatch, patient context and instruction/privacy boundaries. These questions
are exposed development material and must not enter protected evaluation.

1. Compare current rules with the existing encoder's cosine similarity to canonical
   record-anchor embeddings. Do not index expected answers or choose a threshold on
   this matrix and call it independently validated.
2. Stop the observed contour-to-disease misroute; give useful clarification for
   ambiguity/negation; handle bounded abbreviations and measurement paraphrases.
3. Reuse the existing source-bound composition/citation machinery for CT visibility
   and the limitations of the isoattenuating-tumor study. Keep modality, population,
   reference-standard limitations and source-specific meaning explicit.
4. Replay the same questions, retain failures, inspect prose/citations separately,
   check existing supported/boundary regressions and UI contracts. Promote only after
   source integrity and safety checks pass. Broad acceptance remains incomplete if
   the unchanged 18/20 answerable criterion is missed.

Candidate findings and final disposition will be appended here rather than creating
another planning framework.

## Interpretation comparison and two repair rounds

The existing encoder and frozen canonical anchor vectors were used unchanged. Raw
cosine ranking is **not promoted as a router**: an explicit MRI question ranked the
CT visibility record first (0.636), a negated CT question scored 0.748 against that
record, and the two population-specific volume records tied because their anchor
passage is shared. Even an MFCP question ranked focal-AIP evidence first. Similarity
is useful for retrieval, but does not establish task, modality, negation or population
compatibility. The retained experiment is `semantic-comparison.json` and its producing
script in the private output directory; no expected answer was embedded.

Round 1 introduced a small shared matching interpretation (subject, task, modality,
scan/literature context and negation), task/modality exclusions, useful clarification,
and natural measurement phrasing. CT visibility and the isoattenuating-carcinoma
study's limitations reuse the existing bound-source catalog/composer/UI contracts.
The original public suite improved to 6/20 supported answers and the incorrect
contour-to-disease response became an honest abstention.

Round 2 addressed that contour question using the actual CT reader-variability study,
plus its acquisition/voxel limitations and contouring protocol. A separate 12-case
exposed matrix was frozen before implementation. The original 32-case matrix is
preserved: its contour row originally requested abstention while uncovered; the new
supported answer is assessed against the unchanged formal public question's evidence,
not counted as satisfying that old abstention expectation.

The first round-2 replay exposed an internal identifier typo: the model returned
`ct-radi.omics-limits-1`. Validation rejected it and used the explicitly labeled
source fallback. A retained single diagnostic reproduced the typo. Generation now
receives exact record/unit enums derived from the same pinned source records; the
assembler still rejects omissions, duplicates and wrong-record assignments. There
is no string correction or weakening of the validator. The generic prompt/schema
template hash remains fixed; concrete enums and source content are bound by the
catalog/wording pins and retained producer snapshots.

Both study-record versions are retained. The contour example preserves the paper's
35.6 ± 15.0 versus 54.1 ± 15.9 cm³ values and says the cited passage does not define
the ± terms; it does not guess SD/SEM. Every new fact and both wording variants were
checked against canonical source passages. Engineering review is not independent
or clinician acceptance.

## Final public-suite review

| Dimension | Baseline | Final candidate |
| --- | ---: | ---: |
| Relevant, complete answers / 20 | 4 | 9 |
| Wrong-topic composed answers | 1 | 0 |
| Unnecessary scope refusals | 6 | 6 |
| Missing reviewed answer coverage | 9 | 5 |
| Correct no-answer boundaries / 10 | 10 | 10 |
| Model compositions among relevant answers | 4 | 9 |
| Relevant-answer latency | 3.91–7.08 s | 2.95–6.45 s |

All nine final answers passed manual factual-support, completeness and readability
review, with exact canonical citation identity checks. Source qualification is
preserved in separate paragraphs. Public acceptance **fails** the unchanged 18/20
answerable criterion. Independent acceptance remains unperformed. Remaining questions
are TAGS reader/reference/transfer comparisons, subregion workflow, reviewer/automation
effects and anatomy; existing conservative scope rules also reject some legitimate
research phrasing. These are not relabeled as unanswerable to improve the score.

The readable packet is `outputs/prowl/rag-quality-20261022/all-questions.md`; the
per-case table and separate-dimension judgments are `results-table.md` and
`public-engineering-review.json`. Raw responses, failed attempts and producer snapshots
remain beside them. The new exposure supplement must be consolidated before private
authoring; the private checker was not changed and no hidden questions were read.
