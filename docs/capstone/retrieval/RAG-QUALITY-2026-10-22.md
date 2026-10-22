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
