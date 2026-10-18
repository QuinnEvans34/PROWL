# Retrieval development results — October 17, 2026

**Decision: keep live dense search. Neither candidate met the predeclared promotion criteria.**
The hybrid is promising, but does not yet solve the disease evidence problem. This is exposed,
single-reviewer development work on provisional v6 labels, not formal Step 6 selection, held-out
evaluation, clinical accuracy or human acceptance. [Plan and recovery decision](RETRIEVAL-DEVELOPMENT-COMPARISON-2026-10-17.md).

## What ran

Unchanged14 papers / 1,179 passages, existing encoder and exact corpus identity. All 20 answerable
v6 questions, three fixed rankings: dense cosine, English FTS OR, equal RRF 60. Each input list and
output list has depth 50; every actual list filled 50. No model generation, new corpus, query rewrite,
expected-answer input or label edits. Scoring follows ranking generation. Eight refusal/two gap
questions are excluded from answerable means, not credited as successful answers.

Attempt 1 stopped at its first lexical query: PostgreSQL backend exited 2 and recovered automatically.
One embedding/dense query occurred; no complete comparative ranking or scores. Full canonical
inventory, a synthetic FTS canary and corpus-wide FTS match count passed after recovery. One explicitly
documented recovery attempt completed in4.364 seconds including admission/model loading,21 embeddings
and comparison. No repeated question generation or model-policy experiments. The backend failure's
cause remains unproven; OOMKilled=false is only the container flag, not a general memory guarantee.

## Measured results

| Provisional development metric | Dense baseline | Keyword | Hybrid |
|---|---:|---:|---:|
| Mean source recall@5 | .8775 | .7550 | .8800 |
| Source MRR | .7363 | .6450 | .8321 |
| Mean passage recall@5 | .1988 | .2438 | .2231 |
| Passage MRR | .2448 | .2160 | .3601 |
| Questions with ≥1 labeled direct passage in actual top 5 | 9/20 | 10/20 | 10/20 |
| Head-size disease question: direct passages in top 5 | 0 | 0 | 0 |
| Inflammation/tumor question: direct passages in top 5 | 0 | 1 | 2 |

Source metrics deduplicate the depth 50 passage list by paper, then renumber. **Source recall@5 does
not describe the five passages supplied to the answer model.** A source can rank well while its
returned paragraph is irrelevant. Passage recall counts complete containment of labeled spans;
unlabeled text is not automatically proven irrelevant. These exposed, bounded labels are not
exhaustive independent gold. The small aggregate gains do not establish generalization.

Hybrid passed the aggregate source-recall/MRR/passage-recall checks but failed the required
head-size improvement. It also regressed source recall@5 on q:dev2-01 (.8→.6) and q:dev2-05
(1→0). Keyword search regressed aggregate source recall/MRR. Neither is deployed. Diagnostic
span-hit mean actually declined slightly for hybrid (.2097→.2085); it is not a selection metric.

## Why the misses matter

For the head-size question, dense finds three labeled direct passages at ranks 15, 36, 48; hybrid
retains only one at 34. Anatomical dimensions and general size studies dominate the visible five.
Keyword-only has no labeled direct passage within 50. Generic OR terms do not adequately connect
the natural size question to enlargement/inflammatory mass terminology. This is an inference from
the retained ranks/text, not a proven isolated causal factor.

For inflammation versus tumor, hybrid moves two passages from the same cancer-only cohort into
positions 2/3. These support reported cancer signs, **not discrimination from inflammation**.
The directly comparative inflammatory passages are absent from all three top 50 lists. More direct
hits therefore do not mean a complete answer. Reranking only these existing candidates cannot
recover a passage absent from the candidate pool.

Next bounded development step: improve candidate coverage through general question terminology
and source-aware retrieval, then consider reranking. Record a fixed plan before another comparison;
do not inject reference answers, label IDs, disease-question-specific source boosts or memorized
responses. Preserve all 20 cases and report regressions. Assemble surrounding source context only
with canonical offsets/identity so qualifiers remain inspectable. No additional ingestion is
justified by this result: relevant comparative evidence already exists locally.

## Verification and retained evidence

41 focused checks pass:13 ranking/input checks,4 hand-oracle scoring checks and24 existing metric checks.
The hand oracle explicitly distinguishes finding a relevant paper from finding its relevant passage.
Dense top 5 IDs and scores matched the existing implementation on the first comparison question.
A separate final HTTP query for the head-size question returned five canonical passages with exactly
the dense comparison IDs in .358seconds; generation=not_called. This adds one embedding, bringing
the whole checkpoint to23 query embeddings and zero answer-model calls. No UI or live-policy changes;
API 66878 remains owned/live, policy v6.1, UI 5180. Health alone does not establish database readiness;
the final query additionally exercised actual DB admission and retrieval.

Local evidence:

- `outputs/prowl/retrieval-comparison-v1-20261017/`: failed receipt, original producing snapshots,
  original plan, recovery logs and canaries. No failed-run rankings replaced.
- `outputs/prowl/retrieval-comparison-v1-attempt2-20261017/receipt.json`: complete rankings,
  pre-run pins, per-question metrics, aggregate results and failed promotion checks.
- `readable-review.md` in the successful directory: all 20 question outcomes plus the five returned
  passages from each method for both disease questions. Source text stays ignored/local.
- `live-parity-check.json` and checkpoint manifest: final source-only API check and evidence pins.

Corpus, original labels/approvals, protected evaluation, prompts, model weights, training, selector
and human-hours records remain unchanged. Step 5 review/freeze and AI-04 quality acceptance stay open.
