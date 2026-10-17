# AI-02 — authoritative evidence choices

## Frozen pre-run design

Implement the [AI-01 contract](AI-EXPERT-CONTRACT-V1.md): one null or owned selectable span ID for
every supplied passage, at most three non-null choices. No independent assessment, status, intent
or rationale. Code derives final status and materializes exact source text in retrieval order.
Reject extra/missing/duplicate JSON keys, foreign/cross-source IDs, excessive choices, malformed or
truncated generation. Empty inputs/catalogs skip inference explicitly. The candidate remains
experimental; live `verified-extracts-v2` and the workflow are unchanged.

Hypothesis: removing contradictory model decisions will fix the five invalid outputs in the last
assessed candidate. It does not establish semantic relevance, correct study identity or completeness.
Use the same ten known development questions, frozen five-passage retrievals, sentence/span catalog
and unchanged scoring rubric. No gold labels/reference IDs/aspects enter the model. Preserve prior
attempts and immediate raw request/response records; no response mixing across runs.

Pinned Qwen3:30B digest `ad815644918f0eaab341c12b67837cc6dd4562342cdaf118f83d5d554cb37226`,
nonreasoning, temperature 0, seed 42, context 8,192, output cap 1,200. One run, maximum ten inference
calls, 60 seconds per call, 600 seconds total, zero retries or sweep, maximum 1 MiB provider response.
The prompt/schema change together; this is a policy comparison, not a single-variable ablation.

Acceptance remains **7/7 clean complete answers, 14/14 required aspects, 3/3 correct fresh
abstentions, zero invalid generations**. Best earlier experimental result: 5/7 clean and 14/14
aspects; last assessed result: 1/7 clean, 3/14 aspects, five invalid generations. Review every output
against its actual sources and required concepts, then make one accept/reject decision. Passing this
exposed suite is not held-out proof or automatic live promotion.

Scope: new selector and explicit comparison-runner option, synthetic tests, fresh local model/
resource checks, one saved-input comparison and offline replay/scoring. No database query/write,
new corpus text, embeddings, download, full selector, training, held-out access or human-hours credit.
On failure stop inference work for AI-02, preserve evidence and continue the independent Step 3
literature workflow/rebuild obligations. Summary quality stays open for Step 7.

## Results and decision

**Rejected; live policy unchanged.** Ten fresh inference calls completed in **16.250867 seconds**,
with no retry, timeout or output-length termination. The client exited 0; all ten cases have retained
receipts. Source review confirms four clean complete answers, below the required seven. The
representation removes the earlier independent assessment/status contradiction, but does not solve
selection relevance and introduces a failed required abstention.

| Fixed development measure | Assessed30B | Choices30B | Required |
|---|---:|---:|---:|
| Supported-question responses with nonempty valid excerpts | 2/7 | 6/7 | 7/7 |
| Clean complete answers | 1/7 | 4/7 | 7/7 |
| Required aspects covered | 3/14 | 10/14 | 14/14 |
| Relevant / emitted excerpts | 2/2 | 9/13 | All relevant |
| Exact / emitted excerpts | 2/2 | 13/13 | All exact |
| Fresh correct missing-evidence abstentions | 3/3 | 2/3 | 3/3 |
| Invalid generations | 5 | 1 | 0 |

“Nonempty valid excerpts” is the existing scoring counter, not a claim that the whole answer is
supported. Earlier direct30B also achieved 4/7 clean; the best prior experimental result remains
5/7. This candidate does not exceed that result and misses multiple frozen gates.

- Radiomics, general EUS, MRI differential and PET/CT questions are clean under the unchanged
  rubric. The general EUS response uses the correct EUS/IPMN source context and cohort/result;
  one duplicated study sentence is deterministically removed.
- CT detection includes an unrelated MRI result and a treatment/prognosis result. Its correct
  detection-study numerical sentence omits the method/detection-versus-normal context.
- CT external validation combines a different grading study with the correct detection-study
  numerical result. The wrong study's CT description cannot supply the missing method context.
- nCLE chooses four non-null spans, exceeding the fixed maximum of three. The resolver rejects the
  whole generation; no automatic truncation/salvage occurs. The actual nCLE source is null, while
  choices refer to other EUS/MRI studies. Offline replay reproduces the excessive-choice error.
- The PROWL-validation question incorrectly receives a general retrospective-PCL-study quotation.
  This is not evidence of prospective multicenter validation of PROWL and fails required refusal.
  The randomized-survival and guaranteed-future-detection questions correctly abstain.

The model returned exact quotes for every emitted excerpt, but four were irrelevant to their
questions. Structural source fidelity is therefore insufficient for semantic acceptance. No
post-result prompt/schema repair or additional model comparison was performed.

## Verification, operations and retained evidence

**50 focused synthetic checks passed in 0.24 seconds** before inference: authoritative choice
coverage/ownership, duplicate JSON keys, materialization/order/count limits, empty-input/catalog
handling, pin/truncation refusal, runner input separation, frozen-input identities, deadline handling
and unchanged scoring. All 50 retained retrieved rows passed source-content/rights validation before
the run; each case had five passages and a nonempty selectable catalog.

Ten offline replays reproduce each complete generation record and its exact request without another
model call. Every user message is identical to the direct30B baseline; all passages match the
structured-span baseline and its receipt hashes. Source snapshots, prompt/schema/catalog/request
hashes verify. The unchanged scoring implementation reproduces the public review. The score's
`errors=0` counts receipt-level failures; the one invalid generation is explicitly reported above,
not counted as a valid abstention. These are known development cases with engineering judgments,
not protected held-out results or independent clinical review.

Fresh preflight: pinned model available, no model loaded, AC power, 64 GiB machine with low reported
memory pressure, approximately 105.42 GiB internal free. A subsequent full-width process inspection
found no matching trainer/comparison process; the first abbreviated process-name listing could not
establish that alone. Only saved local passages were used; no DB startup or corpus mutation.
Postflight confirms no comparison process, Ollama reports all slots idle after the final response,
and internal free remains approximately 105.43 GiB. Existing live service code/configuration was not
changed or restarted; unrelated service health was not requalified by this experiment.

Public, hash-bound per-case judgments and score:
[`choice-spans-v1-review.json`](../../../configs/evidence/evaluation/choice-spans-v1-review.json).
Private requests/responses, original producing-source snapshots, manifest, receipts, score and replay:
`outputs/prowl/development-evaluation-20261015/choice-spans-v1/`.
Preflight: sibling `choice-spans-v1-preflight.json`; postflight: `postflight.json` in the run directory.
The report inside the producing-source snapshot contains the pre-run design; this outcome section
does not replace it. Raw article/model text remains off Git. No human-hours credit is inferred.

## Next step

AI-02 is complete as a rejected bounded investigation; response quality remains open. Proceed to
**Step 3 / W04-01 literature DAG and rebuild qualification**: review invalidation, reproducible index
rebuild and remaining recovery boundaries, reusing existing evidence and explicit fixture/evidence-only
behavior. No further prompt/model experiment is queued in this step. The later grounded-response
gate must still qualify a suitable response policy before full feature completion.
