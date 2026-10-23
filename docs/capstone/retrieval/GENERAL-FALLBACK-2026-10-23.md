# Evidence-based general fallback

User approved implementation after the pancreas-function question retrieved useful evidence but
received no answer. Existing reviewed record answers remain first choice. Unmatched general
questions should use relevant retrieved passages, never expected answers or a topic-specific rule.

Fixed initial public probes: pancreas function; function paraphrase; anatomical location; MRI volume
methods; focal-fat comparison; normal stiffness range (gap). Preserve baseline responses and raw
candidate calls. These are exposed development questions, not independent evaluation.

Reuse the existing local8B model, canonical source bindings and separate support/completeness/
readability review. One revision must receive all failures. Keep source identities and context;
partial supported answers are useful, but never invent missing details or assert unsupported absence.
No clinical/scan/refusal boundary bypass. An empty draft must be checked for missed relevant evidence.

Promote only after manual support, completeness, citations and prose inspection, affected regression
checks and a real browser walkthrough. Report latency separately. If a focused repair still fails,
retain the candidate outside the live UI and document the specific failure rather than weakening
acceptance. Existing exposed regression and later fresh independent evaluation remain required.

Initial experiment uses actual five-passage retrieval packets across papers instead of the previous
single-paper restriction, and the installed8B instead of the unavailable experimental14B server.
There is no new application, corpus, model download or training.


## Interim manual finding: promotion blocked

The first candidate returned a verbose function answer but failed the paraphrase and MRI-method
checks. The focused repair shortened the answer but added insulin without that term or its identity
being established in the cited passage. The support checker approved it by supplying outside knowledge
about beta cells. It also inferred enzyme substrates beyond the cited wording. Mechanical checks
rejected the draft, but a model “supported” flag is not dependable evidence of entailment.

The initial function answer included unnecessary anatomical location and cell lists. Its readability
review approved that text, despite the prompt asking to omit unrelated detail. The location question
was classified measurement_unavailable before retrieval; that is a distinct routing failure, not
missing literature. Remaining fixed repair results follow. Do not promote this module or claim it
solves the reported user issue. The live service does not import it.

## Focused repair results

The repair reused the same saved packets (no expected-answer text), limited prose to100words and
made completeness review inspect the full packet, including empty drafts. Model and all calls are
retained under outputs/prowl/general-fallback-20261023/, with separate initial and repair receipts.
This experiment did not implement a new relevance selector: unrelated retrieved passages remain a
known contributor. No topic-specific function facts were added.

| Question | Initial candidate | Focused repair / manual judgment |
| --- | --- | --- |
| What does a pancreas do? | Verbose answer returned, excessive cell/anatomy detail | Rejected after48.69s; unsupported insulin inference approved by model reviewer, unbound numerical citation markers rejected mechanically |
| What jobs does the pancreas have? | Rejected after37.95s | Returned after20.18s but manual FAIL: insulin unsupported by citation, unrelated anatomy |
| Where is the pancreas located? | No evidence; existing measurement routing gate | Preserved boundary; no model call; general location misclassification remains unresolved |
| How do papers measure pancreas volume on MRI? | Rejected after33.35s | Rejected after23.88s: reviewer says pass while listing missing requirements, including irrelevant statistical demands |
| How can fat in the pancreas head look different from a tumor on CT? | Inconsistent review after22.95s | Rejected after37.16s; initial repair draft confuses similar density to pancreatic tissue with similarity to fat; revised draft retains unexplained PDAC |

Twenty-five canonical source records across five nonempty baseline packets were verified. Exact
citation bindings do not establish semantic support. The gap probe's final result is recorded below.
25 focused utility/candidate tests pass, including empty-draft completeness repair, bounded one-revision
behavior and rejection of persistent unsupported claims. Initial mock test failure (extra quote field
not allowed in source-ID schema) was corrected; no production schema was loosened.

No candidate qualifies for promotion. Per the agreed stopping condition, no full exposed regression
or live UI installation follows this failure. The existing study-answer service remains healthy and
unchanged. This task has NOT delivered a general-answer feature ready for user acceptance.

The next concrete design should first select a small set of directly responsive source sentences
while retaining their qualifying context, then constrain the answer to those facts. An explicitly
labeled source-extract answer can be tested as the baseline; free paraphrasing should only replace it
when it demonstrably preserves meaning. A further prompt-only review cycle is not justified by these
results. General-anatomy routing is a separate repair; it must preserve current-scan boundaries.

Final gap probe:39.10s, rejected after one revision. First draft supplied age-related stiffness facts
instead of a normal kPa range; revised draft asserted source absence with citations. The guard withheld
it. This is a correct withholding outcome with an inadequate attempted answer, not a complete gap
explanation. Five generation attempts in the repaired set produced zero manually qualifying summaries;
the sixth question was blocked upstream. These six prompts are not the full exposed regression set.
