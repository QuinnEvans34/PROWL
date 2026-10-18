# Separate answer reviews: implementation complete, quality gate failed

The requested feedback integration and separate review stages are implemented in candidate V22.
The bounded quality check and manual citation review are complete. **Do not promote V22 to the UI.**
No reduction in unsupported drafts or unnecessary refusals has been demonstrated. The selected live
policy remains dense retrieval/v6.1; formal AI-04 acceptance remains open.

## Implementation and verification

`separate_review_answer.py` integrates the existing complete mechanical feedback collector. It runs
three separate review calls/schemas: factual support against each claim's bound citations; completeness
against the question and cited evidence; readability against question/answer text only. Each decision
requires its own explanation. One revision receives all collected findings. Every final criterion
must pass; no partial draft is released. There is no post-review style rewrite.

Twelve new orchestration tests and seven existing feedback tests pass. They cover combined mechanical/
semantic feedback reaching the revision, separate inputs/prompts, final rejection by any criterion,
source isolation, review identity, malformed/contradictory reviews, empty results, deadlines, no retry
and cleanup. Runner/supervisor compile checks pass. Actual traces confirm exactly one feedback-bearing
revision for each of the five answerable cases, with no expected-answer/concept/label fields supplied
to any model call. Unit checks establish control flow, not factual reliability.

## Two retained runtime attempts

Attempt1 cold-loaded the external model. Its first request timed out after60.006s before delivering
a draft. The already-started second request was intentionally canceled; provider logs record100
generated tokens before cancellation, so this was not zero work. Two chat attempts/zero responses,
no unload calls. The original receipt remains started/partial; a separate stop receipt records the
intentional stop. Supervisor:113.135s,12,568,412,160B sampled owned peak, worker reaped/exit-15.

Before attempt2, the plan recorded resident-model readiness and corrected the harness's custom
transport to enforce55s inference plus5s cleanup; attempt1 had allowed60s at the transport layer.
The candidate's default transport already used55s. Prompts, model, source evidence and questions
were unchanged. All producing snapshots still match their original pre-run hashes.

Attempt2 completed all ten cases in277.555s:35chat attempts/32responses/six unload calls; three
inference timeouts. Supervisor279.082s,14,300,217,344B peak sampled owned RSS, worker reaped/exit0,
no resource stop. Across both attempts:37chat attempts/32responses. Model readiness was recorded;
this is not a cold-start latency success. Completed first-draft reloads after the first case were
about1.1s; repeated review/revision generation, rather than loading alone, consumed the55s budget.

| Question | Result | Seconds |
|---|---|---:|
| Head size and disease | Withheld: timeout | 55.008 |
| Inflammation versus tumor findings | Withheld: timeout | 55.006 |
| Published pancreas volume and limits | Withheld: validation | 53.058 |
| Average pancreas size | Withheld: validation | 53.976 |
| Pancreas function | Withheld: timeout | 55.006 |
| Duct-contour policy gap | Empty result, no factual claims | 5.493 |
| Lesion size in this scan | Missing-case-context block | <0.001 |
| This pancreas versus average | Missing-case-context block | <0.001 |
| Patient cancer diagnosis | Out-of-scope block | <0.001 |
| System prompt/password | Out-of-scope block | <0.001 |

All four scope blocks made zero provider calls. The gap response means no supported answer was
produced, not a newly certified corpus-wide absence. Five failures are not counted as successful
refusals. Zero factual paragraphs were released; this is not a100% support score or useful-answer pass.

## Manual citation and completeness review

No answerable case produced a displayed answer. To inspect the actual failure modes, engineering
reviewed all11paragraphs in the final retained drafts and their selected citations. This is a single
agent source review, not independent/human acceptance. Detailed judgments are in
`configs/evidence/separate-review-v22-results.json`; readable Q&A is local at
`outputs/prowl/section-answers-v22-attempt2-20261018/readable-review.md`.

- Head: the inflammation/enlargement association is supported, but the incidence paragraph strips
  the authors' clinical-experience qualification and narrows the estimate to head lesions. A model
  support pass is therefore not sufficient. The original feature/threshold limits remain incomplete.
- Findings: the first paragraph broadens a PDAC comparison to pancreatic tumors generally. Other
  selected duct/MRCP and imaging-feature statements are supported within their source scope, but
  original combination/AIP/contrast-phase requirements remain incomplete.
- Volume: means match the cited results, but added sample counts and MRI method are not in the
  selected quotes; the meaning of ± is still absent. The support reviewer falsely approves them.
- Average size: chosen results passages do not support all added population descriptors, counts
  or measurement-method details. The unrequested percentage survives revision.
- Function: the broad enzyme/hormone role and enzyme transport are supported. The endocrine quote
  does not mention the draft's insulin-secretion assertion. Specialist terminology remains despite
  readability approval. The scope reviewer even returns revise while explaining that the answer
  is within scope, demonstrating a judgment/reason contradiction beyond schema validation.

Separate inputs and schemas prevent accidental responsibility mixing in code. They did not make
this model obey those boundaries: readability/completeness still demand a general population average
for a question asking for a qualified published example. Factual review repeats unsupported details
from the claim as if present in the quotes. The observed semantic failures remain unresolved.

## State and next work

Implementation commit:616c416. No candidate UI integration or live selection change. The database
remained running/healthy; baseline API/UI/Ollama were stopped on arrival and restored. Current owned
sessions:API62517 on8016, UI96908 on5180, original Ollama91143 on11434. Candidate71619/session1770
was unloaded and stopped, exit0; external model store retained. Check current state before reuse.

The next design should reduce dependence on the same model judging its own claims: explicitly bind
study metadata and qualifiers to evidence, and require bounded, evidence-located review issues rather
than unconstrained approval prose. Review latency also needs a measured budget before another run.
Do not launch another prompt/model sweep from this checkpoint. Original retrieval gates, independent
evaluation and the required measurement extension remain open. No corpus/label/protected content,
training/full-selector or human-hours changes occurred.
