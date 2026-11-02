# Assistant saved-answer review — November 2

CPU-only review while Mac KD and laptop baseline preparation continue. No model
calls, GPU work, prompt changes or quality promotion. This is exposed development
review, not independent evaluation.

## Current fast-preview evidence

Reviewed the three retained HTTP responses in
outputs/prowl/fast-preview-20261031-01/answer-{0,1,2}.json against their retrieved
passages. All cited quotations bind exactly to their cited text; this is not an
entailment guarantee. Historical timings below are warm end-to-end measurements,
not new timings or cold-start guarantees.

| Question | Support / completeness / readability | Citations / refusal | Prior latency |
| --- | --- | --- | --- |
| Why can pancreas boundaries be hard to outline on CT? | Relevant size/location/irregular-anatomy explanation, but adds an unrequested cancer-diagnosis statement and unexplained PC abbreviation. Needs relevance/readability repair; not a fabricated quotation. | Two citations repeat the same source sentence in overlapping chunks. Links bind; they are not independent corroboration. | 3.39s |
| What does a pancreas do? | Supported core statement, but exocrine/endocrine jargon is unexplained. Retrieved evidence also supports digestive-enzyme release/transport and glucose regulation; answer omits the latter explanation. Completeness/readability need repair. | Exact quote binding passes. No refusal needed. | 2.59s |
| What is the normal pancreatic stiffness range in kilopascals? | Correctly says the retrieved sources lack that range. Pass for this returned evidence, not proof no such range exists anywhere. | No invented range or unrelated citation. Pass. | 2.10s |

The prompt already instructs direct plain-language answers and excludes tangential
diagnosis. Another instruction alone cannot be claimed to fix these outputs. Keep
the working fast configuration until a bounded same-input comparison demonstrates
improvement. No answer text was hardcoded or retrospectively edited.

## Implemented UI repair

Changing study or saved prediction during a pending question previously cancelled
it but lost the submitted text after the chat composer cleared. Both cancellation
paths now restore that text unless a newer draft exists, invalidate the request,
clear transient answer/help state and explain the cancellation. Late responses
cannot enter the replacement study's conversation. Reproduction: two new tests
failed before the fix; both pass afterward. Newer-draft preservation also passes.

Earlier fast-preview answers also lost their preview label when moved into history.
History now keeps the same label, source links and edit action. No additional model
call or prompt change. Both page and Workbench panel variants are covered.

Validation: 84 focused component tests passed with Node24.21.0; production UI build
passed with the existing large-bundle warning. Tests prohibit network calls and use
synthetic responses. The first test invocation used the shell's older Node and
failed before collecting tests; rerunning with the repository's existing Node24
resolved that environment mismatch. No dependency changes were needed.

## Fixed next live packet

Prepared outputs/prowl/assistant-review-20261102-01/inputs.json with five exposed
questions, unchanged saved evidence, source SHA256s and the three v7 baseline
answers. The two additional evidence packets come from the retained October31
comparison; older 30B failures are explicitly not current-v7 results.

| Question | Required review |
| --- | --- |
| Why can pancreas boundaries be hard to outline on CT? | Direct explanation; no unrelated diagnosis claim or unexplained abbreviations. |
| What does a pancreas do? | Explain digestive and hormonal roles plainly, retaining their separate functions and cited support. |
| What is the normal pancreatic stiffness range in kilopascals? | Preserve the evidence-gap response; no guessed range. |
| How do papers measure pancreas volume on MRI? | Retain individual study methods/modality/population; do not turn one protocol into a universal method. |
| How can fat in the pancreas head look different from a tumor on CT? | Preserve PDAC-specific and anatomical scope; do not generalize every tumor or infer a diagnosis. |

At the next explicitly coordinated GPU window, run the current configuration once
on all five saved packets before changing it. Record factual support, completeness,
readability, citations, refusal and latency separately. Preserve raw responses and
failures. Saved-evidence timing is generation-only; measure actual Research and
Workbench end-to-end timing separately, including cold/warm conditions. Exercise
edit, cancel, replacement and citation navigation with these live responses. Keep
current speed as a comparison target; do not label mocked UI tests as live quality
or latency evidence. No GPU pause or live comparison has been scheduled here.
