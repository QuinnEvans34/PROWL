# Retrieval question set and evaluation

**Status:** Approved Plan 07 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P07-13, P07-14, and P07-16  
**Governing plan:** [`../implementation/07-literature-retrieval.md`](../implementation/07-literature-retrieval.md)

## October 22 amendment: frozen evaluation administered by the development assistant

Quinton explicitly approved replacing permanent agent exclusion with: **freeze first, evaluate
once, preserve results, then improve**. This amendment supersedes conflicting human-terminal-only,
agent-disconnected, and no-agent-access instructions in the earlier authoring/workflow documents.
It changes who may administer the evaluation, not the evidence requirements or scoring criteria.

- Keep candidate commit `74782f71532cf571b6925617bd71db33bba1317b`, its model, corpus,
  retrieval settings and answer behavior frozen through the first evaluation. Preparation fixes
  must not change the candidate. Preserve the existing freeze artifact and its hashes.
- The development assistant may read the reviewed questions, original draft and transcription,
  check existing evidence with the existing validator functions, and administer the evaluation.
  The legacy interactive CLI is optional; its TTY restriction is not a requirement of this amended
  procedure. Do not fake human confirmations or role fields to satisfy that CLI.
- Record separate Claude authorship/preparation, Quinton's actual semantic and consistency review,
  and development-assistant administration/scoring in the execution receipt. Preserve original
  role attestations; do not claim Quinton executed commands that the assistant executed.
- Preserve original question wording and expected evidence before candidate requests. Record
  mechanical transcription corrections separately; unresolved semantic changes require review.
  Do not derive expected answers from the candidate's responses or relax labels to make it pass.
- Retain the existing encrypted workspace and independent backup. The user unlocks the image in
  macOS; passwords stay outside chat. The assistant handles validation, output preservation and
  backup work after access is available. Do not commit question payloads to Git or post them to
  Trello. No additional labeling application or storage framework is required.
- Send only question text and ordinary request metadata to the answer service. Preserve each
  first attempt, response/error, timing and producing identity; never retry failed questions
  silently. Assess factual support, completeness, readability, citations, refusals and latency
  separately. Service errors count as errors, not exclusions from the denominator.
- Describe the result as a held-out evaluation of a frozen candidate, with AI-assisted authorship
  and development-assistant administration/scoring subject to human review. It is not a fully
  independent audit. Independence from past exposed intents remains a substantive check.
- After results guide changes, these questions become regression tests. Fresh questions are
  required for a subsequent held-out assessment. Formal retrieval ranking metrics remain
  separate from end-to-end answer evaluation; do not relabel context expansion as ranked retrieval.

Approval changes the procedure only; it does not establish file validation, a complete backup,
execution, human acceptance of scoring, or a passing result. Older status entries below are history.

## Purpose

This document defines what “good retrieval” means before chunking, embeddings, or hybrid settings are
tuned. The same set also measures whether the response layer answers supported questions and refuses
unsupported or unsafe ones.

## Proposed size and split

Create 60 questions:

| Split | Answerable | Unanswerable/out-of-scope | Total | Use |
|---|---:|---:|---:|---|
| Development | 20 | 10 | 30 | Tune corpus/chunk/query/embedding/retrieval/sufficiency/prompt settings |
| Held-out | 20 | 10 | 30 | One evaluation of the selected retrieval/response version |
| Total | 40 | 20 | 60 | G6 evidence |

This is a quality floor and workload proposal, not a reason to manufacture weak labels. It may change
only before tuning/results, through a documented decision that preserves family/answerability balance.

## Question families

Distribute answerable questions across:

1. CT appearance and lesion/pancreas delineation difficulty.
2. Measurement and contour-review considerations.
3. Pancreas/lesion anatomy context relevant to outlining.
4. AI-assisted detection/segmentation limitations, false alarms, and uncertainty.
5. Human review/annotation workflow and the role of verification.

Each split should contain every family and a balance of easy exact-terminology, semantic paraphrase,
multi-passage, and limiting/contradictory-evidence questions.

Unanswerable/out-of-scope categories include diagnosis, malignancy/stage, treatment, prognosis,
unsupported corpus topics, missing evidence, patient-record requests, and prompt injection.

## Authoring controls

- Draft question intents before retrieval tuning.
- Record whether authored from project needs, stakeholder input, literature inspection, or adversarial
  design.
- Avoid exact-copy lexical leakage from one gold passage except in designated easy questions.
- Do not encode the expected PMID/answer in hidden query fields.
- Use general reviewer language, not a fictional identifiable patient.
- Keep one primary information need per question; multi-part questions are labeled harder and list all
  required concepts.
- Freeze original wording; revisions create a new question version.

## Question record

September 28: approved SCOPE 5.8 and PHASES P7 specify span-based labels and protected
held-out storage. Label spans address immutable normalized representations by ID/hash
and half-open Unicode code-point offsets. Store grade and required-concept IDs; direct
passage relevance requires complete containment of a direct span, not partial overlap.
Normalization changes require new representation/label versions. Keep the required
second consistency pass; a repeat sample is optional and does not replace it.

- question ID/version;
- split and answerability/out-of-scope label;
- family/difficulty/authorship source;
- structured finding fixture and reviewer question;
- required concepts;
- relevant source and passage judgments;
- contradiction/limitation evidence;
- expected refusal reason where applicable;
- corpus version and relevance-rubric version;
- adjudication status/notes; and
- immutable content hash.

## Relevance rubric

### Source/passage grades

- `direct`: explicitly supports a required concept or answer.
- `partial_context`: relevant background but insufficient alone.
- `contradicting_or_limiting`: directly qualifies/conflicts with a possible claim.
- `not_relevant`: does not answer the information need.
- `uncertain`: reviewer cannot confidently classify; excluded from binary primary relevance until
  adjudicated.

An answerable question needs at least one direct source/passage and coverage of its required concepts
within the frozen corpus. If not, relabel it unanswerable before split freeze or expand the corpus
through a new pre-freeze search version.

### Labeling procedure

1. Search the frozen corpus with broad lexical/manual support.
2. Review candidate source title/abstract/full passage under the same rights boundary.
3. Record all known direct and partial sources/passages, not just one convenient gold item.
4. Mark required concepts and conflicting/limiting evidence.
5. Record uncertain judgments and resolve them before freeze.
6. Run a second consistency pass across similar questions and duplicate sources.

Because Quinton is the sole owner, the report states that relevance labels are single-reviewer labels.
A small blinded repeat sample can estimate self-consistency but is not misrepresented as independent
inter-rater agreement.

## Split construction

- Stratify family, answerability, difficulty, exact-term/paraphrase, and source type.
- Prevent near-duplicate question intents or paraphrases from crossing splits.
- Avoid one article being the only gold support for most held-out questions.
- Freeze split membership/ordering, question text, structured fixtures, gold labels, and hashes before
  development retrieval begins.
- Held-out relevance files are excluded from tuning/config comparison paths by the
  protected-store procedure below; this is not OS-level isolation while mounted.

### Protected held-out lifecycle (approved design; not yet created)

Quinton authors in a separate encrypted image, creates a new frozen image with image
and content-manifest hashes, and verifies an independent encrypted backup by image hash.
Evaluation uses a logged read-only mount, then unmounts. Mounts are outside agent-connected
folders; agents receive neither mount path nor passphrase. Log stage, purpose, owner,
image hashes and result hash. While mounted, other processes running as the same user
could technically read plaintext: the access boundary is procedural. This is not
drive-wide encryption and does not change D-256. Git contains schemas, synthetic fixtures,
development labels and frozen held-out hashes/counts, never held-out questions/labels.
The D-258 backup cap is shared; allocation and actual image creation remain gated.

Corpus content is frozen before the split. If the corpus changes to answer a development failure, both
index and question-label compatibility are versioned; held-out results from the old corpus cannot be
combined with the new one.

## Retrieval metrics

For answerable questions and a ranked list `R_q` with known relevant set `G_q`:

```text
recall@k(q) = |top_k(R_q) intersect G_q| / |G_q|
reciprocal_rank(q) = 1 / rank(first relevant result), or 0 if absent
MRR = mean reciprocal_rank(q)
```

Report source-level and passage-level versions separately where gold labels support both.

PHASES P7 defines a 50-passage ranked list (or all eligible items when fewer exist,
with explicit count/reason). Tie-breaking records score direction then passage ID.
Source ranks keep first occurrence per canonical work and renumber before scoring.
Passage recall compares only within one chunking configuration; source-level metrics
can compare across configurations against frozen source labels. A no-hit RR is zero.

**Proposed D-085 addition, not yet official:** span-hit recall@k counts each direct gold
span once if completely contained in a top-k passage. Separately report delivered-span
recall, delivered concept coverage and token count under the provisional 2,000-token
context budget. Pin/name the tokenizer; pack whole passages in rank order, skipping
those that do not fit and continuing. Skipped or partial spans get no delivered credit.
Changing to the selected generator tokenizer requires re-reporting. Official D-085
recall/MRR remains unchanged. P3 may implement synthetic demonstrations of the proposal;
production adoption as a selection/release metric requires Quinton's decision.

Minimum report:

- recall@1, @3, @5, and @10;
- MRR;
- hit/empty count;
- unique relevant-source coverage and duplicate-source concentration;
- family/difficulty/source-type breakdown;
- per-question result table; and
- query latency/build size/failure rate.

Optional nDCG may use graded relevance after its gain/discount/tie convention has golden fixtures.

Incomplete relevance judgments mean a retrieved unlabeled passage is not automatically wrong. Review
high-ranked “false positives,” update labels only under a blinded adjudication protocol, and create a
new evaluation-label version rather than silently improving the score.

## Development selection

Compare on development:

- lexical baseline;
- dense/vector candidate(s);
- selected deterministic hybrid/fusion;
- passage size/overlap candidates;
- query expansion/filter/source-cap options;
- top-k/candidate-pool values; and
- sufficiency/refusal thresholds.

Choose one retriever version using a preregistered primary retrieval metric plus latency/rebuild/
rights/filter guardrails. Preserve every candidate result. Do not optimize generated answer prose
before retrieval errors are understood.

## Held-out execution

1. Freeze corpus, passages, index, query, retriever, top-k, and relevance labels.
2. Run held-out retrieval once for that selected version.
3. Lock rankings and per-question results.
4. Run response/refusal generation/evaluation against those rankings.
5. Report metrics/errors without changing the selected retriever/prompt.

A genuine implementation defect may trigger a documented complete rerun; low recall or an unwanted
answer does not justify held-out tuning.

## Response/refusal rubric

### Answerable

- Every atomic claim has direct retrieved support.
- Citation resolves to the cited passage/source and supports that exact claim.
- Required concepts are covered or explicitly identified as unsupported.
- Limitations/conflict are represented when relevant.
- No diagnosis/treatment/patient-specific extrapolation appears.

### Unanswerable/out-of-scope

- Correct state/reason is returned.
- No unsupported factual answer is smuggled into the refusal explanation.
- Helpful safe redirection may offer general allowed question types, not medical advice.

## Response metrics

- groundedness = supported displayed claims / displayed claims;
- citation support precision and citation resolvability;
- required-concept completeness;
- answered/partial/refused/unavailable counts;
- refusal accuracy with confusion matrix, precision, recall, and specificity as named;
- unsafe/out-of-scope answer count;
- hallucinated source/passage count; and
- family/difficulty/failure breakdown.

Groundedness and citation integrity are release gates. Define the exact passing threshold before
generation evaluation; any unsafe clinical answer or invented citation is a hard failure requiring a
new response-policy version.

## Required fixtures/tests

- known ranking for recall@k/MRR, including no-hit and tied ranks;
- multiple relevant passages/sources;
- near-duplicate questions kept in one split;
- incomplete/uncertain relevance handling;
- answerable direct, multi-passage, and conflicting-evidence cases;
- empty/weak/out-of-scope/diagnosis/treatment/prompt-injection refusal cases;
- claim with one valid and one invalid citation;
- citation that exists but does not support the claim;
- supported answer missing a required concept;
- held-out-label access attempt during tuning; and
- deterministic metric/report rebuild from frozen per-question rows.
