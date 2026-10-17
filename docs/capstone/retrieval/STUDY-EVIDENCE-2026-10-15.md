# Source-linked study evidence — October 15, 2026

## Pre-run design and acceptance

Quinton approved the source-linked evidence repair after the30B scope comparison. The remaining
nCLE mistake is a fragment of the Schultz EUS morphology study: the retained parent paragraph
contains its identity/cohort before the retrieved fragment. Restoring those exact source coordinates
is sufficient to expose the distinction; no new paper, embedding or corpus write is needed.

Experimental `study_evidence.py` builds one record for each selected source occurrence BEFORE
showing any question to the extractor. It restores the full parent paragraph through verified
representation offsets and includes same-heading adjacent paragraphs as orientation only. Facts
must cite numbered parent sentences. Adjacent paragraphs cannot silently supply facts. Long
adjacent paragraphs are explicitly omitted above2000characters; parents above6000characters or
30sentences are refused. Source revision, citation, rights, representation, original normalization
and focus offsets must match. The original selected occurrence, not string search, fixes identity.

A record distinguishes general explanation, empirical study or unknown. Study/method/cohort/result/
explanation fields contain exact sentence references; the server materializes their text and source
coordinates. Fields cannot leave the selected contiguous evidence unit, which must contain the
focus. Study records require study and method anchors; unknown records assert no facts. This checks
source binding, not the truth of model-assigned semantics or whether two sentences really belong
to one study. Record IDs include source identity and content. Cache reuse is question-independent,
with re-resolution against the same packet; cached text tampering is refused.

A separate matching call sees the question, anchored fields and allowed answer spans. It chooses
an explicit study/explanation intent, then compatible evidence. Server checks forbid a study record
from being used as a definition/workflow answer, out-of-unit expansion, duplicate records or foreign
spans. Final quotations still come only from the original retrieved passages and contain the original
selected excerpt. Missing context can inform rejection; it is not silently substituted into citations.
A malformed record/match rejects the entire answer; unavailable backend stops the experiment.
No unchecked fallback. Original live v2 remains unchanged.

One ten-case run reuses the frozen structured selections and existing corpus bundles. Same pinned
Qwen3:30B, nonreasoning, temperature0, seed42, context8192; output cap1200 for the new record/schema
format. Both representation and matching change from the earlier scope policy, so this is a pipeline
comparison, not an isolated model or context ablation. Keep the fixed rubric. Success requires7/7
supported answers,14/14 aspects, all8 useful selections retained and all4 irrelevant selections
excluded, with no invalid generations. Report failures and aspect loss as well as clean answers.
The three existing abstentions bypass model calls and are preservation checks only. Corpus-informed
development evaluation; final held-out evaluation stays separate.

Run limits600seconds total /60seconds per API call, no retry. Every completed call immediately saves
its full request/hash/raw response locally; each new evidence record saves its packet and extraction.
Producing sources and this pre-run plan are frozen before inference. No training or selector resume.

## Results

Completed one run:10cases,15model calls (10record extractions /5matching calls),8valid records,
24.311seconds total. Two invalid records stop their cases before matching; later candidates in those
cases remain unprocessed. The client exited0, Ollama reported all slots idle, and the existing answer
API health check passed. No timeout or automatic retry. Original demo remains unchanged.

| Fixed development measure | Previous30B scope | Study-linked pipeline |
| --- | ---: | ---: |
| Supported answers | 7/7 | 3/7 |
| Clean complete answers | 5/7 | 3/7 |
| Covered aspects | 14/14 | 6/14 |
| Useful original selections retained | 8/8 | 3/8 |
| Relevant / emitted excerpts | 8/10 | 3/3 |
| Invalid generations | 0 | 2 |
| Preserved existing abstentions | 3/3 | 3/3 |

**Rejected.** High precision among the three surviving quotations does not compensate for losing
five useful selections. No irrelevant quotations reach the output, but this is not four successful
wrong-study decisions: two cases are wholly rejected before the later wrong candidates are processed.

The radiomics definition becomes clean: the extractor labels the general explanation separately from
the empirical detection application, and the matcher retains only the explanation. CT detection and
MRI comparison stay clean. EUS and PET matching falsely abstain despite valid records with responsive
source facts and offered answer spans. The model supplied empty choices; no code exception caused
those two abstentions. No causal explanation for those model choices is proven.

The nCLE extractor places only its method/cohort sentence in the unit, while citing its preceding
study identity and following result outside the unit. The server rejects that inconsistent record.
For CT external validation, the extractor places only the result sentence in the unit and points the
cohort field to the neighboring Chu study, while study/method fields point to Chen. The same structural
check refuses this record. Expanding units automatically to encompass all nominated fields would
accept that cross-study cohort error; the guard remains strict. These records expose attribution
problems, but do not solve them. Even a structurally valid method field can omit the imaging modality;
typed fields and exact text are not semantic certification.

Supported-case total generation median2.140seconds, range0.868–8.941seconds, first case includes cold
loading. Early rejections and missing matching calls make this unsuitable for a speed comparison.
Largest observed prompt2556tokens, largest output73tokens, below8192/1200 limits; no output-length
termination. No record-cache hits occurred in this run because each processed focus differed; the
cross-question reuse behavior is verified with invented fixtures only.

## Verification and preservation

70 focused tests pass. They cover source/rights/revision binding, recovery of context before a chunk,
foreign-heading exclusion, missing method/foreign fields, repeated-text occurrence binding,
question-independent extraction/cache reuse, cached-text tampering, intent mismatch, out-of-unit
answer expansion, unknown records, backend failure and bounded-run interruption preservation.
One initial fixture assertion mistakenly joined sentences without punctuation; corrected the expected
string. No product repair or successful quality claim follows from that test correction.

Ten offline replays reproduce complete generation objects exactly. All15requests/hashes match the
saved requests; all8record packets/resolutions match. Extraction requests contain only source packets,
never question/gold labels. Both bundle hashes match the producing manifest. Offline rejected-record
inspection identifies the two field/unit violations above. The hash-bound public score recomputes
exactly using the unchanged scoring function. No replay model calls.

Local artifacts: `outputs/prowl/development-evaluation-20261015/study-linked-v1/` contains producing
sources/pre-run plan, bundle/input hashes, ten receipts,15immediate raw requests/responses, eight
record packets, completion, score and replay/link audit. Public review:
`configs/evidence/evaluation/study-linked-v1-review.json`. Article text/raw responses stay local.
The frozen producing report preserves pre-run criteria; this final report adds results.

## Decision and recommended next step

Keep this implementation experimental and preserve the failed comparison. Do not integrate it into
the demo or add another review stage. Existing30B scope review remains the best measured experimental
pipeline at5/7clean, still unqualified. We have not measured30B selecting evidence spans directly:
previous structured selection used8B, followed by30Breview. Next compare direct30Bspan selection
against that existing8Bbaseline on the same saved passages and unchanged selection prompt/schema.
This missing simpler baseline should precede more orchestration work. It is an answer-evidence test,
not resumption of the parked full corpus selector. No next experiment has been launched here.
