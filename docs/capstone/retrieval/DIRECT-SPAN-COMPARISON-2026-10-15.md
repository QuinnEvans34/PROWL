# Direct evidence-span model comparison — October 15, 2026

## Frozen design

Quinton approved the missing direct30B selection baseline after the source-linked pipeline regressed.
Reuse the ten question/retrieval receipts from `structured-spans-v1`; do not reuse its selections.
Run the existing span selector once with installed pinned Qwen3:30B. Only model identity changes
from the saved8B baseline: same prompt, allowed-span schema, source order/text, nonreasoning mode,
seed42, temperature0, context8192 and output900. No review, record extraction or context expansion
stage. Explicit model/pin provenance; default selector remains8B and live quotation API unchanged.

Use the existing bounded runner with policy `spans`,600seconds total/60seconds per API call,
no retries. Save immediate requests/responses, source snapshots, input hashes and final receipts.
Negative cases now invoke direct selection: their abstentions are measured, not just inherited.
No database query/write, embedding, model download, full corpus selector or training.

Fixed comparison rubric:7supported/3missing questions;14required aspects. Improvement requires
more than4/7clean complete answers (saved8B selector), preserving7/7supported answers, at least
12/14aspects,3/3correct missing-evidence abstentions and no invalid generations. Full development
acceptance target is7/7clean and14/14aspects with no irrelevant excerpts. Also compare with best
experimental30Bscope result5/7clean and14/14aspects. Known corpus-informed questions are not held-out
validation. No automatic live promotion follows a single small run; report all regressions.

## Results

Completed10fresh selection calls in12.699seconds, zero retries/timeouts/invalid generations. Owned
client exited0; Ollama reported all slots idle and the existing answer API health check passed.

| Fixed development measure | Direct8B baseline | Direct30B |
| --- | ---: | ---: |
| Supported answers | 7/7 | 5/7 |
| Clean complete answers | 4/7 | 4/7 |
| Covered aspects | 12/14 | 9/14 |
| Relevant / emitted excerpts | 8/12 | 6/6 |
| Exact source quotations | 12/12 | 6/6 |
| Correct missing-evidence abstentions | 3/3 | 3/3 |
| Invalid generations | 0 | 0 |

**Not promoted.** Irrelevant selections disappear and nCLE study matching improves, but supported
answer retention and coverage regress. The earlier8Bselection+30Bscope pipeline remains the best
measured experimental coverage result (5/7clean,14/14aspects), itself unqualified. No automatic
fallback mixing outputs from different experimental runs.

- Radiomics: false abstention despite the supplied definition and extraction workflow.
- EUS: chooses the Schultz EUS/IPMN study and43-patient cohort. Three overlapping model selections
  deduplicate to one exact excerpt. Cohort is sufficient under the fixed cohort-or-result rubric.
- CT detection: clean method/cohort/AUC excerpt, without PET or CNN substitution.
- nCLE: correctly selects only35-patient nCLE evidence and82%accuracy from the same passage;
  excludes the two different EUS-study fragments. Three overlapping selections deduplicate to two
  exact excerpts, retaining both required aspects.
- CT external: correct >1000-subject local/external AUC result, but contrast-enhanced CT context
  still omitted. Partial evidence is relevant but not a complete answer.
- MRI: clean named-study and different-institution comparison.
- PET: false abstention despite explicit tracer, tumor grades and named study in the source.
- All three unsupported questions: fresh direct calls abstain correctly. These results are not
  inherited from the earlier selections as in the scope-review comparisons.

All-case selection wall median0.969seconds, range0.679–3.992seconds (first case includes cold load).
Single sequential observation with different answer lengths/abstentions; no general speed benchmark.
The parser accepted both false abstentions as valid JSON; no transport, pin, span-lookup or
validation rejection caused them. The source evidence and allowed IDs were present. A cause for the
model's semantic decisions has not been established.

## Verification and evidence

56focused checks pass, including exact unchanged request structure across model selection, pin
refusal, and direct-mode integration with no saved generation field and a forbidden review stage.
Default experimental selector still8B; original live quotation module unchanged. Twenty offline
replays reproduce both ten-case generation objects exactly. All ten old/new request pairs are
identical after removing only the model name; all ten new raw request hashes verify. The public
score recomputes exactly. Replays do not invoke the model.

Local evidence: `outputs/prowl/development-evaluation-20261015/direct-spans-30b-v1/`, with frozen
pre-run plan/producing sources, manifest, ten case receipts, ten raw requests/responses, completion,
score and replay/input comparison. Public review:
`configs/evidence/evaluation/direct-spans-30b-v1-review.json`. Raw article/model text stays local.
No live policy change, corpus writes, downloads, full selector/training or inferred human hours.

## Recommended next decision

Keep the direct path as the simpler experimental candidate, without promoting it. Diagnose its two
false abstentions and missing CT context before adding orchestration. A narrow30Breasoning-mode
probe on those three failures, one positive control and one unsupported control would test whether
nonreasoning selection is the limitation. Keep sources/schema fixed, change only the explicit
reasoning profile with a declared token/time cap, retain all failures, and do not generalize a
five-case diagnosis into full acceptance. Earlier8Breasoning exhausted its budget; this larger model
has not been tested in that profile. No diagnostic or second run launched here.
