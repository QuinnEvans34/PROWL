# Development evaluation draft and review checkpoint — October 17, 2026

> Follow-up: [all-30 agent review and four label corrections](DEVELOPMENT-FOLLOWUP-REVIEW-2026-10-17.md).
> Use the revised v3 draft/packet linked there; this preparation checkpoint and its v2 evidence remain historical.

**Disposition:** Step 5 / [AI-03](https://trello.com/c/NctoNxr8) preparation is delivered; the complete
60-question freeze is **not complete**. Thirty exposed development drafts and a protected-authoring
worksheet are ready. Quinton's semantic adjudication, second consistency pass and private held-out
work remain required before new retrieval tuning. No protected questions were created or read.

## Review first

The local review packet is `outputs/prowl/evaluation-authoring-20261017/development-review.html`.
It presents every development question, expected concepts, scope limits and exact rights-permitted
source excerpts with source links and normalized offsets. Open it locally; it is ignored by Git.
For each case, Quinton should accept, correct or reject the proposed support and record why. In chat,
refer to **development** IDs such as `q:dev2-01`; these drafts are already public. Do not submit any
protected question or label here.

Check that each concept is actually supported, numerical values retain the right study/target,
limitations are required where needed, and alternative relevant passages have not been omitted.
Review the complete source context where an excerpt is ambiguous. Recheck related cases together
in a second pass. A question with inadequate support must be revised or marked unsupported before
freeze; the counts do not justify manufacturing evidence. These are proposed labels, not generated
answers, independent expert judgments or a clinical recommendation.

The [protected-authoring worksheet](PROTECTED-EVALUATION-AUTHORING.md) describes Quinton's separate
30-case task and the content-free receipt. Storage allocation, image creation and backup have not
been performed. The blank receipt is explicitly `not_created`, with null hashes/counts and false
attestations. It must never be used as evidence of a completed protected store.

## Delivered artifacts

- [Development draft](../../../configs/evidence/evaluation/development-v2-draft.json): 20 answerable,
  eight policy refusals and two corpus-gap cases; complete draft hashes, concepts, labels and source judgments.
- [Closed draft schema](../contracts/retrieval/development-draft-v1.schema.json): reuses the existing
  coarse finding and span-label definitions. Only exposed development drafts and pending human review
  are accepted; neither held-out content nor a self-attested frozen state can pass this draft reader.
- [Offline checker](../../../src/retrieval/development_set.py): verifies corpus inventory, canonical
  bundle/batch hashes, case identity, input allowlists, source bindings, complete direct-span containment,
  required-concept references, source judgments, family/answerability counts and feasibility.
- [Preparation receipt](../../../configs/evidence/evaluation/development-v2-preparation.json): producing
  file/test/receipt hashes and explicit incomplete human/protected gates.
- [Blank protected receipt](../../../configs/evidence/evaluation/heldout-receipt-template-v1.json): only
  aggregate counts, hashes and review/backup attestations; no protected source choices or paths.

The draft's canonical content SHA-256 is
`e01f456c7f96e8fce39963277b54709653ad705f9c012f9ce824681404cdaf47`.
It binds the Step 4 manifest and corpus content
`17f65adda92c288e9bfc587cd7edbb195cf75e232a44929296393954edb5b681`.
The existing ten-case `development-v1.json` regression remains separate, unchanged and explicitly
exposed. The new file is a **draft v2**, not a replacement run or a relabeled held-out set.

## Distribution and evidence limits

| Answerable family | Cases |
|---|---:|
| CT appearance | 4 |
| Measurement / contour review | 4 |
| Anatomy | 3 |
| AI limitations | 5 |
| Review workflow | 4 |

Answerable difficulty: five easy terminology, three paraphrase, six multi-passage and six limiting
questions. Labels contain **58 exact spans: 47 direct, six partial/context and five limiting**.
Every direct span is wholly contained in at least one frozen passage. Concepts are proposed answer
requirements; matching IDs/offsets does not prove entailment. All 30 cases remain human-review pending.

All twenty answerable drafts currently have one direct gold source each. The five new primary sources
supply direct support for 3 / 4 / 6 / 5 / 2 questions; no one source exceeds six of twenty. One retained
review supplies additional partial context. This is a study-focused, limited-corpus evaluation draft,
not broad open-domain validation. It includes questions without explicit study names, but many
questions name a study or method intentionally. That source cue and author inspection can make
retrieval easier and must be disclosed. Human review should assess whether this balance fits the
intended reviewer workflow; revisions precede tuning.

The theoretical source recall@5 ceiling is **1.0 for these proposed labels**, because each answerable
case currently has one direct source. It is not an observed recall score. Additional valid source
judgments must be retained even if they change feasibility; never prune gold to pass the 0.8 floor.

The eight refusal cases cover RF1/RF2/RF3/RF4/RF6/RF7/RF8/RF9 without real patient facts or credentials.
The two unsupported questions concern duct contour policy and validated segmentation uncertainty.
Their rationale distinguishes adjacent attenuation-ROI/probability-map material from the requested
method evidence. The existing coverage matrix and a supplemental local lexical scan support these
proposed absence judgments; they remain reviewable, not mathematical proofs of absence.

## Consistency pass and exposure controls

The first pass used retained source paragraphs and manual/lexical inspection, not tuned rankings or
model-generated answers. The agent's second pass checked attribution, source scope, repeated evidence,
concept granularity and near-duplicate intents. Additional abstract/conclusion support was retained.
The prostate evidence explicitly carries its anatomical scope and possible-bias versus deliberate-
acceptance qualification. Reference-derived TAGS prompts remain explicit; no autonomous-detection
claim is allowed. This pass is preparation by the same agent, not Quinton's required review or an
independent second annotator.

Related subregion applicability/input cases, TAGS annotation/reliability cases and prostate review
cases share development intent groups. All other draft groups are recorded as well. No exact question
wording duplicates the exposed ten-case regression. That string check cannot detect paraphrases:
Quinton must privately review semantic overlap against both exposed sets before freezing held-out
content. A broad family or paper in common alone does not define duplication. No claim of cross-split
independence is made while the protected split does not exist.

Initial local draft and verification receipts are preserved under
`outputs/prowl/evaluation-authoring-20261017/`. Revisions before this checkpoint expanded support,
split the reader-design and agreement-value concepts, removed ambiguity from the gap questions,
added paraphrases and linked related intents. The public file is the resulting review draft;
future frozen-question revisions must version wording/labels and retain prior evidence.

## Verification

**31 offline checks passed** using invented sources: private/unknown input rejection, stale corpus/
regression/question/span bindings, duplicate wording, missing concepts, partial overlap, wrong source
judgments and attempted draft/held-out/approval promotion. Existing span-label checks also pass.
An initial test attempt had four failures because schema errors use a different exception type;
rejections already occurred. The checker now gives one sanitized schema error without echoing rejected
question/field content, and the corrected checks pass. Both attempts are retained.

The actual development draft passes a separate offline canonical-corpus validation. All required
concepts reference direct support, all direct spans fit complete frozen passages, all five answerable
families are present and all source/case hashes match. The explicit `--require-ready` invocation exits
with a refusal because human/protected gates remain pending. It performs no tuning or model call.

```sh
.venv-retrieval/bin/python -m src.retrieval.development_set \
  --development configs/evidence/evaluation/development-v2-draft.json
```

This produces mechanical diagnostics and `ready_for_tuning: false`. The checker accepts only repository-local `development-*` files in the evaluation configuration
directory, rejecting external paths, escaping symlinks and other names before opening question content.
This is a CLI guard, not OS-level isolation. It is an offline draft reader, not the final protected evaluator. Neither a keyword-gate classification nor a successful
technical validation is used as the semantic answer key. Do not pass protected files to this command.

No database queries, encoder calls, generation calls, new sources, service restarts, encrypted images,
training or full-selector work occurred. Existing services and the frozen corpus were not changed;
this turn does not make a fresh service-health claim. No human working time was inferred.

## Remaining Step 5 work

1. Quinton reviews/adjudicates the 30 development cases and performs the second consistency pass.
2. Quinton independently authors and protects 30 held-out cases, checks semantic overlap against both
   exposed suites, and verifies the permitted storage/backup procedure.
3. Freeze both finalized splits and obtain the content-free protected receipt. Resolve incomplete
   labels or source coverage through versioned changes before tuning.

Only then start Step 6 retrieval selection. AI-03 remains In Progress, awaiting human review and
protected authoring. Broader answer quality and protected acceptance are still open.
