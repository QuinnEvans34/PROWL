# Protected evaluation authoring — Quinton's worksheet

**Status:** Preparation only. No protected questions, encrypted image, backup or evaluation exists as
part of this checkpoint. This document contains instructions and blank fields, not held-out content.

The [evaluation protocol](QUESTION-SET-AND-EVALUATION.md) requires independent protected authoring,
exact span labels and a second consistency pass. The [development draft review](DEVELOPMENT-SET-REVIEW-2026-10-17.md)
is public/exposed. The two sets must remain distinct. Do not paste protected questions, answers,
labels, source-span choices, mount locations or passphrases into this chat, Trello or Git.

## 1. Establish the private workspace before writing questions

Use the already specified encrypted-image procedure outside agent-connected folders. Confirm its
registered storage allocation and independent encrypted-backup capacity before image creation;
this preparation does not allocate storage or create an image. Do not use an ordinary repository
folder or a public document as temporary held-out storage. Agents have not checked any private mounts.

Quinton authors and reviews the protected content. While an image is mounted, processes with the
same OS user could technically read it: protection is procedural, not isolation from the account.
Author and review while agents are not operating against that location; unmount after each session.
Never share the mount path/passphrase. If safe private storage is not ready, leave authoring pending.

## 2. Select independently authored intents

Create **30 private cases: 20 answerable and 10 unsupported/out-of-scope**. Include all five families
among answerable cases. Aim for a reasonable spread rather than forcing four questions into each
family despite missing evidence. Include easy terminology, paraphrase, multi-passage and limiting
questions; label the difficulty explicitly. No protected questions are supplied here for copying.

Use the frozen seven-source corpus identified by
`configs/evidence/corpus-coverage-v1.json`, content SHA
`17f65adda92c288e9bfc587cd7edbb195cf75e232a44929296393954edb5b681`.
The four documented gaps are not supported answers waiting to be invented. If independent authoring
cannot produce adequate coverage, stop before tuning and version the corpus/labels through an explicit
revision. Do not weaken required concepts or mislabel an unsupported question to meet the counts.

Before writing final wording, privately compare intended questions against both exposed sets:

- `configs/evidence/evaluation/development-v1.json`: prior ten-case regression and its history.
- `configs/evidence/evaluation/development-v2-draft.json`: current 30 drafts, including `intent_group`.

Keep related intents and paraphrases in one split. A shared broad family or paper alone does not
prove duplication; a different wording or paper name alone does not prove independence. Check the
requested fact, target, comparison and expected concepts. Shared exact direct spans are a warning
that needs semantic review, not a substitute for that review. Move or revise a development draft
before freeze if needed; disclose only that development revision here, not the protected question.
Avoid having one paper serve as the only gold support for most protected answerable cases.

## 3. Private per-question worksheet

Complete these fields inside the protected workspace. All text remains private there.

| Field | What to record |
|---|---|
| Identity | Unique `q:heldout-NN`, question version and private intent group |
| Split | `held_out`; never relabel an exposed draft as held-out |
| Question | Exact original wording, at most 500 Unicode characters; no private patient facts |
| Finding fixture | Invented CT/pancreas coarse enums from `query.schema.json`; no IDs, reports, paths, masks, images or hidden expected source IDs |
| Family / need | One primary frozen information need; list secondary requirements explicitly |
| Difficulty | Easy terminology, paraphrase, multi-passage or limiting evidence |
| Provenance | Quinton; actual authorship basis and any prior exposure |
| Expected behavior | Supported answer, insufficient evidence or policy refusal, with reason and boundary |
| Concepts | Atomic required facts and required scope qualifications; identify each with a stable `c:` ID |
| Labels | Existing `span-label.schema.json`: representation ID/hash, half-open normalized Unicode offsets, grade and concept IDs |
| Source review | Every retained source considered; direct, partial, limiting, irrelevant and unresolved judgments with reasons |
| Adjudication | Resolve uncertainties, record reasoning, reviewer identity and review date |
| Second pass | Recheck labels, duplicate intents, alternate support, answerability and boundary conditions |
| Identity checksum | SHA-256 over canonical JSON, excluding its own checksum field; retain exact final bytes |

Use normalized representation text from the retained source bundles, not the publisher's HTML byte
positions or the current online version. Every direct span must be completely contained in at least
one passage in the frozen corpus. Partial overlap earns no direct credit. Verify every concept has
adequate support; a span checksum proves identity, not entailment. Review other passages, including
abstracts and conclusions, for additional known direct/partial evidence instead of choosing one
convenient passage. Uncertain labels must be resolved before freezing.

For unsupported/refused cases, the existing label contract uses `answerable=false`, no required
concepts and no gold spans. Keep absence-search notes or safety rationale separately; adjacent text
must not silently become a gold answer. Do not derive expected behavior from the existing keyword
gate, generated answers or whichever retriever happens to succeed.

The development-draft validator deliberately refuses held-out records and self-attested approval.
Do not point it at the protected store. This worksheet reuses the shared query/span conventions;
a private held-out authoring/validation runner has not been delivered or executed here.

## 4. Freeze only after both splits are ready

Complete Quinton's semantic adjudication and second consistency pass on the development set and the
private held-out set. This is single-reviewer labeling; the agent's preparation and technical checks
are not independent expert agreement. A repeat sample is optional and does not replace the second pass.

Freeze membership/order, questions, fixtures, labels and producing versions before any new tuning.
Use a private content manifest to hash all protected members, create the frozen encrypted image,
and verify an independent encrypted backup by the encrypted-image SHA-256. Retain original authoring
history and any revised versions. Image checksum equality is backup evidence; it does not by itself
prove semantic labels or restoration behavior.

Only share a completed **content-free receipt** derived from
`configs/evidence/evaluation/heldout-receipt-template-v1.json`: hashes, aggregate counts, review and
backup attestations. Do not fill the template with invented hashes or mark pending work complete.
No source IDs, question IDs/text, label offsets or filesystem paths belong in that public receipt.
The template is not proof that a store or backup exists.

Later, the selected retriever/prompt is evaluated once through the logged read-only mount procedure,
then the image is unmounted. Freeze the result hash and report errors without tuning against protected
content. The agent must not read protected content to perform duplicate checks or inspect a failure.
