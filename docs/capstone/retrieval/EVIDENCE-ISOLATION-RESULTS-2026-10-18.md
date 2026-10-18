# Controlled experiment: evidence, generation and validation each contribute failures

The approved three-question/three-arm experiment completed without timeout or resource stop.
The diagnosis is useful, but **no candidate is promoted**: none of nine drafts satisfies the unchanged
original completeness requirements. The selected live dense/v6.1 policy remains unchanged. Plan and
implementation were committed as `d090127` before generation. Eight new focused tests pass.

## What changed between the arms

Three real source-only API searches supplied the current dense top5. The two curated arms use the same
manually checked original passages, in identical order, with identical source IDs and text. Only the
linked arm adds within-paper role references. The prompt/model/options are fixed across all arms;
there are no revisions or reruns. All drafts are saved before mechanical checks and a frozen V22
factual reviewer. No expected-answer or evaluation-label fields enter model requests.

| Question | Current dense search | Checked passages | Same passages with links |
|---|---|---|---|
| Head size/disease | Wrong anatomical narrowing and carcinoma-size/head-size substitution | Broad association; missing focal-mass/overlap/single-feature qualifications | Exact same draft and citations; no observed improvement |
| Inflammation versus tumor | Diagnostic difficulty, not distinguishing findings; an unsupported causal statement | Relevant duct/MRCP and inflammatory features; omits combination/AIP-CT context | Adds PDAC signs, but loses MRCP labeling; still omits combination/AIP-CT context |
| Published volume | Broadens selected groups into general populations; missing study context | Correct numbers but population qualifiers lack bound citations | Same answer text, now correctly citing result/population/statistics; still missing count/method/SEM explanation/limits |

The curated recipes supply4,6,3passages respectively. Current top5 exact overlap is0,0,1; this is
selected-passage overlap, not corpus recall. Manual reading confirms the relevant differential
passages are absent and the numerical result lacks population/statistic context. Retained R8+context
has2/4,3/6,3/3selected passages respectively: it improves evidence coverage, but still misses the
single-feature limitation for both disease questions and the focal-AIP CT/PDAC-sign passages for the
second. No ranking replay was needed. Do not equate passage overlap with all semantic coverage.

## Citation review and validator behavior

One engineering agent inspected all16paragraphs against their bound original citations and the
unchanged completeness requirements. Six are supported, six contain definite unsupported content,
and four have uncertain scope/strength requiring independent review. These are paragraph judgments,
not16atomic facts or a clinical accuracy estimate. Uncertain judgments are excluded from definite
reviewer-error counts. Detailed reasons and claim-text hashes are in
`configs/evidence/evidence-isolation-v1-results.json`.

- The reviewer approves five of the six definitely unsupported paragraphs. Most decisively, the
  source describes carcinomas located in the pancreatic head; the draft changes the measured object
  into the head itself. Both the numerical/citation checks and model reviewer accept it. The original
  article's neighboring ordinal32 explicitly identifies the size as carcinoma size.
- The reviewer rejects one factually supported paragraph because it does not answer the question.
  That is a factual-review category error, not evidence that the whole irrelevant answer should
  have been displayed. Factual support and responsiveness must remain separately reported.
- Five scope reviews request revision. Several explanations acknowledge no patient diagnosis or
  treatment while still demanding an unspecified scope repair. The volume reviews also describe
  statistical details not actually written, or demand a general-population mean for a question
  explicitly requesting a published example. They are not dependable safety/quality judgments.
- Mechanical checks flag four drafts: one for unrequested percentage and all three volume drafts
  for missing qualifications; the flat curated volume also has an uncited population descriptor.
  Those issues are legitimate, but these checks miss the anatomical measurement substitution and
  cannot establish semantic support. A percentage-policy flag is not itself a factual error.

The linked volume answer provides a useful limited improvement: its text is byte-for-byte identical
to the flat answer, but it cites all three relevant passages instead of the result alone. This repairs
binding of stated population qualifiers. It does not make the model state the14-person group, MRI
method, meaning of uncertainty, matching or limits. The head answer is byte-for-byte identical across
both curated arms, including citations. Metadata relationships alone are insufficient in this trial.

## Runtime and reproducibility

The isolated fresh server initially reported no resident models. One empty-prompt readiness/load
call completed in1.022s; this is not a cold-machine benchmark because filesystem cache was uncontrolled.
Nine drafts plus nine factual reviews completed:18chat attempts/18responses, one readiness call and
one successful unload. No retries, incomplete outputs, provider errors or timeouts. Batch166.434s;
supervisor167.914s,15,269,724,160B peak sampled owned RSS (14.221GiB), both server and worker reaped
exit0, no resource stop. Candidate port11435 is closed; original service selection unchanged.

| Question | Dense draft / draft+review | Curated draft / draft+review | Linked draft / draft+review |
|---|---:|---:|---:|
| Head | 5.621 /16.505s | 4.758 /12.845s | 3.654 /10.699s |
| Findings | 10.100 /20.165s | 10.681 /27.141s | 10.008 /26.813s |
| Volume | 6.719 /20.338s | 7.883 /16.379s | 5.628 /14.503s |

Search requests separately took5.268s,0.352s,0.348s. These are single observations, not percentile
latencies or a live-answer benchmark. Compared with V22, this run also changes the prompt, number of
reviews, revision policy and resident-model lifecycle. Do not attribute faster completion solely to
evidence links. It does show that this pinned local model can finish these bounded draft/review tasks
within the declared call budget; timeout was not the reason for their quality failures.

All producing pins match; canonical1,179passages were verified against representation offsets and
text hashes before selection, and each actual search result equals its canonical record. Flat/linked
source equality was checked before execution. Full prompts/responses/timings, immutable preparation,
source snapshots and supervisor logs remain under `outputs/prowl/evidence-isolation-v1-20261018/`.
Readable `all-answers.md` links each actual draft to original passages in `evidence.md`. These source
payloads stay local. Historical failed trials, corpus, labels and exposure identities are unchanged.

## Decision and next implementation

The working hypothesis is narrower now: retrieval misses needed evidence, the generator loses
relationships/qualifications even when they are supplied, and same-model review can repeat those
errors or mix review criteria. No single change has fixed all three. This three-case exposed diagnostic
cannot establish a general local-model ceiling or prove that another model would solve the problem.

Recommend a small source-linked **fact record** prototype next, starting with the volume example:
explicit measured object, quantity, population, method, statistic and limitations, with a source span
for each field. This is stronger than the relationship hints tested here. Required qualifiers should
be assembled with the result by code; do not leave their inclusion or reassignment to unconstrained
paraphrasing. Keep human-verified public-literature records distinct from generated interpretation.
Do not build question-to-answer lookup tables or insert evaluation answers into prompts.

Then test selection and a minimal rendering step separately, including deliberate organ-versus-lesion
and population/statistic mismatches. Broader retrieval should bring the whole relevant record, rather
than a result fragment. Use the model only where it adds readable explanation without controlling
measurement identity. Keep factual support, completeness, readability and scope judgments separate;
same-model approval is diagnostic evidence, not an acceptance certificate. Qualify any new flow before
replacing the live policy. No new implementation/run follows automatically from this report.

AI-04 remains In Progress. Formal independent evaluation/retrieval gates and the required measurement
extension remain open. No protected-set access, training/full selector, corpus growth, public source
payloads, model downloads, patient measurements or human-hours credit occurred.
