# Section retrieval: development results and limits

The useful change is retrieval of complete source sections with general terminology normalization.
The original 14-paper/1,179-passage corpus is unchanged. No candidate is a formally accepted
retrieval configuration. Live dense search remains the fallback while answer quality is investigated.

| Experiment | Actual outcome | Decision |
|---|---|---|
| R4, hierarchical local-model source/section selection | 15 of 20 complete; question 16 exceeds section-menu bound; 31 selector calls | Reject; no silent clipping or retry |
| R5, compact menu plus explicit selection reason | 20 complete; 15 packages contain known direct evidence, 10 cover all labeled concepts; median 9.438s, max 19.816s; 40 calls | Reject; both disease cases miss provisional direct labels |
| R6, native reasoning for selection | First question exceeds combined 60s deadline; first stage completes, second times out | Reject; no completed package or retry |
| R7, deterministic section/window cross-encoder | First head-size screen fails known-span criterion after 7.097s | Stop at declared gate |
| R8, general terminology plus R7 | Head-size screen still fails original labels after 7.043s, but source reading finds directly relevant unlabeled material | Preserve original failure; separately document continuation |
| R8 continuation | Remaining 19 cases complete; inherited first result not replayed; zero generative calls | Promising development candidate, original promotion criteria unmet |

R8 across 20 exposed answerable cases: source recall@5 .9200; source MRR .8833; passage recall@5
.3238; 10/20 questions have a known direct passage in the first five results. Complete section
packages contain known direct evidence for 13/20 and all labeled concepts for 8/20. Median ranking
6.977s, maximum 7.318s; average 14.4 canonical passages from 2.9 papers. These are single-run local
observations. Section-package metrics are not interchangeable with top-five-passage metrics.

A material label limitation emerged: the head-size top section in PMC7376657 (`body-5`) explicitly
discusses focal inflammatory enlargement, usually in the head, and overlap with cancer location.
The inflammation-versus-tumor package includes the same paper's duct-penetrating-sign section,
including its MRCP context. Neither appears in the provisional disease-label spans used by the
original automatic gate. Zero known-span hits therefore does not prove zero relevant evidence.
Original labels, failed screens and numeric results remain unchanged. This is post-hoc engineering
source assessment, not independent relabeling or a passing protected evaluation.

The context amendment appends canonical abstracts and study-method sections from selected papers,
deduplicated under 50 passages/30,000 characters. It supplies population and statistical definitions
needed to qualify numerical examples. It also adds distraction; answer experiments must measure
that cost. Retrieval alone cannot establish correct answers, and the model has demonstrably
combined whole-organ findings with head-specific claims. See the v6.2/v9/v10 answer plans.

All experiment plans precede their respective runs. Receipts, producing snapshots, source text and
raw model traces are retained under `outputs/prowl/section-*20261017/`; public aggregate hashes are
in `configs/evidence/section-retrieval-results.json`. Raw source text is not republished. These runs
read exposed development questions only. Protected content, training, selector state and human
hours are untouched. Formal Steps 5–7 and independent evidence review remain open.
