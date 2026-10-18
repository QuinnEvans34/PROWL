# Source-grounded answer development

Section retrieval recovers useful disease evidence, but it does not guarantee useful or correct
synthesis. These candidates are rejected and have not replaced the live v6.1 preview.

| Candidate | Summaries / insufficient / failures / scope blocks | Observations |
|---|---|---|
| v6.2: larger canonical section package, original prompt | 3 / 1 / 2 / 4 | Head answer promotes an author's experience estimate into incidence and narrows a whole-pancreas finding to the head; same-model reviewer accepts it. Findings gives unrequested accuracy/specificity without full context. Volume rejected. |
| v9: abstract/method context, plain-language instructions, extra guards | 3 / 0 / 3 / 4 | Head's unsupported AIP narrowing is rejected; general-size percentage rejected; gap's absence claim rejected. Displayed volume omits method/sample size; findings and function retain jargon. |
| v10: extract, write, reasoning review | 0 / 0 / 6 / 4 | Writer reintroduces facts outside extracted statements because it still sees full sources. One qualifier rejection and five 60s timeouts; no usable result. |

V6.2 received 11 generation responses across six literature cases in 83.740s including three new
retrievals. V9 received 11 in 88.558s using retained rankings. V10 received nine completed generation
responses in 316.741s; timeouts also represent attempted provider calls and must not be counted as
zero work. All scope cases stop before retrieval/model calls. No retries or raw drafts displayed.
V9 context sizes are 21–35 passages/10,969–20,302 characters including titles, versus v6.2's9–15
passages/4,868–8,111 characters. Abstracts/methods add study context but also distract the model.

The v6.2 candidate JSON inherited a top-level8192context field while the plan/code/traces used16384;
original bytes are preserved. Later candidate metadata corrects this; no retroactive claim that the
old JSON was consistent. Producing snapshots are hash-verified against each pre-run receipt. V11's
original natural_answer.py snapshot was reconstructed from retained v9 bytes and exact recorded edits,
then matched to the pre-run SHA after the working file advanced; no producing pin was rewritten.

All raw evidence/traces remain local under outputs/prowl/section-answers-*-20261017. Aggregate
outcomes and hashes are in configs/evidence/section-answer-results.json. These questions are exposed
engineering diagnostics, not protected evaluation. Formal labels, human acceptance and clinical
claims remain unchanged. The existing corpus, training/selector state and human hours are preserved.

Subsequent controlled comparisons are separately preregistered: v11 compares the installed8B model
on the v9 task; v12 applies the publisher's recommended sampling to v11. Qwen explicitly discourages
greedy decoding in thinking mode. That configuration mismatch is real, but its causal contribution
to these failures is unproven. [Publisher guidance](https://huggingface.co/Qwen/Qwen3-8B#best-practices).

V11 completed: five summaries, one qualifier failure, four scope blocks (11 received generation
responses). Reject: the supposed gap is answered with unsupported source-absence claims; numeric
examples still omit method/sample size/statistical meaning, and broad function answers retain jargon.
V12 completed: three summaries, one correct insufficient answer, two qualifier failures, four scope
blocks (10 received generation responses). Reject: both size-related questions fail unrequested
percentage guards; volume still lacks MRI/sample size/SEM/limits. The corrected gap alone is not a
broad improvement claim. Sampling remains publisher-aligned in the next implementation, not proof
that it solved the observed problems. No seed search, prompt replay or hidden retry occurred.

V13 is a separately planned implementation: claims-only, non-thinking output and one quality-feedback
revision under the shared60s deadline. Unit checks cover the two-call success, three-call mechanical
repair, four-call review repair, second-failure stop, no timeout retry and absence-claim handling.

V13 rejected: one summary/five support failures/four scope blocks. The volume summary still lacks
method/sample size/SEM and a universal-average limit despite a positive qualification flag. Head
and function revisions often repeat rejected material; gap draft infers a duct-contouring policy
from imaging signs and is withheld. V14 plain-text diagnostic also rejected both canaries: head
answer repeats incidence/anatomical scope errors; volume centers the diabetes comparison rather
than supplying the requested qualified reference. Both raw calls completed (5.414/5.021s), but exact
citation/qualifier parsing failed. Do not mistake fluent output or shorter runtime for correctness.

Stop prompt variants on these models. V15 is a bounded scope amendment to compare one different
instruction model on the external drive, with an isolated loopback service and pinned9.0GB download;
see INSTRUCTION-MODEL-V15-PLAN-2026-10-17.md. Existing live service/model store remains unchanged.
