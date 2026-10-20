# Volume composition candidate check — October 20

## Frozen scope before execution

W03-03 candidate: source-volume-answer-v1 with source-linked-volume-search-v1. Disease answers
retain source-record-answer-v1 and their existing wording/prompt identities. The combined optional
service advertises source-literature-answer-v2 / source-linked-literature-search-v2; each response
retains its own family contract. Enable with `--volume-answers` only after this check passes.

Existing Qwen3:8b, one call per covered question, 30-second composition deadline, no model retry.
Model output selects reviewed units/wording; every unit and qualification is mandatory, with exact
citations attached by code. Invalid model output becomes explicitly labeled application assembly.
That fallback does not pass the live-composition gate. Source admission failures remain errors.

Fixed exposed development cases, declared in `scripts/retrieval/check_volume_answers.py`:

1. Average whole-pancreas volume reported in research: one NGT study record.
2. Mean volume in type 2 diabetes: one well-controlled/metformin study record.
3. Explicit NGT versus type 2 comparison: both records, separate populations and results.
4. Focal autoimmune pancreatitis versus PDAC: one unchanged disease record.
5. Ambiguous average size: clarification, no model call.
6. Average volume on CT: source-only, no MRI reference substitution or model call.
7. Lesion size in this scan: existing scope boundary, no model call.
8. Database/instruction request: existing refusal, no model call.

Temporary loopback HTTP server8017; existing UI/API remain selected during the check. Four maximum
chat attempts, eight requests, 240-second total watchdog, 20MiB retained output cap. Record candidate
file snapshots, every raw model plan, request/response and latency. All eight must pass expected
selection/calls/generation, exact canonical source identity, request binding and <40-second request
limit. No changing criteria after seeing results, no repeated prompt/model sweep. Report any failure.

After automated success, manually inspect every displayed claim and citation, including population,
numbers/units, MRI, SEM meaning, matching and limits. Independently verify the UI accepts all retained
responses using its actual validators. Only then promote and check a real browser answer/source and
clarification. Independent evaluation and broader W03-04/05 quality work remain open.

## Wording source review

Both variants of each of eight units were compared with the retained source and existing fact
review: PMID25950180 ordinals2 (MRI, analyzed n41/n14, population/treatment, matching),18 (whole-organ
volume and cm3),27 (mean±SEM),29 (T2DM55.5±2.8 versus NGT82.6±4.8). No new source findings are added.
SEM explanation is a statistical glossary; normality/CT limitations are application interpretation
limits, not author quotations. NGT is not labeled healthy. This is single engineering review, not
independent clinical approval. Expected evaluation answers are excluded from production material.

## Preflight checks

Backend: 86 existing focused checks passed on the first run; 18 new fixture setups refused an
incorrect Unicode JSON content hash. The hash was regenerated using the composer’s canonical bytes;
all 18 new checks then passed. No model calls preceded the fix.
UI: first run63pass/1fail from changing existing disease source-copy wording. Disease copy was
preserved and volume-specific copy separated; final64pass. Build passes (existing large-chunk warning).

## Attempt 1 result and bounded repair

Attempt1 completed 6/8, three actual model calls. The mean-volume diabetes question was blocked by
legacy scan-measurement routing before retrieval. The two-group model plan included every unit but
interleaved each group's qualification paragraph, which failed the contiguous-record layout rule.
Neither failure was hidden; outputs/prowl/volume-answer-v1-20261020 retains all plans/responses.
No promotion occurred.

Candidate1.1 changes code only: a separately scoped volume baseline may supersede only
measurement_unavailable for an admitted general study-mean intent; original refusal/case gates
retain precedence. Case/current wording is explicitly excluded. Stable grouping of volume paragraphs
precedes the same exact unit/order/qualification/citation validation. No wording or prompt change,
missing-fact repair, citation replacement, or relaxed clinical boundary. Disease behavior is unchanged.

Attempt2 is a single fresh repetition of the same eight cases and unchanged gates, at most four
model calls, under the same resource limits. It is a targeted integration repair check, not a model
or prompt sweep. Preserve both attempts separately. No further automatic retries follow a failure.

Attempt2 stopped at admission with zero chat attempts because the earlier model was still resident
within its keep-alive window. This is not evidence of another active request. Its failed receipt is
retained; the namespace is not reused. After residency naturally clears, attempt3 is the single
remaining eight-case code-repair check (same four-call ceiling/criteria). No model unload or concurrent
job interruption is performed. Final repair checks:83 pass, including the original scope gates,
volume selection, exact composition and interleaved-layout regression.
