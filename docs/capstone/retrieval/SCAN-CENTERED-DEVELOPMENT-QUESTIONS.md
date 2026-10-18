# Shared scan-centered development questions

Version 1 — October 17, 2026. Joint product-discovery list; exposed development material.

Quinton confirmed the five assistant examples were exactly the kind of questions he would ask,
then supplied three more wordings. This accepts their product relevance, not evidence labels,
implemented capabilities or clinical validity. These eight wordings form five related task groups;
variants are useful for usability and paraphrase checks, not eight independent evaluation needs.

## Questions and intended behavior

| Group | Question wording | Authorship | Intended behavior and dependency |
|---|---|---|---|
| Head measurement | “What is the size of the pancreatic head in this scan?” | Assistant; relevance accepted by Quinton | Calculate a defined dimension or volume from valid geometry and a qualified head outline; show units, method and outline provenance. Clarify the requested quantity when ambiguous. |
| Reference comparison | “Is this pancreas enlarged?” | Assistant; relevance accepted by Quinton | Require a qualified measurement and an applicable reference definition. Do not equate above-average size with abnormality. |
| Reference comparison | “How does the size of this pancreas look compared to the average?” | Quinton | Identify dimension versus volume and use a compatible published statistic and population; explain when a reliable comparison is unavailable. Do not invent a universal average. |
| Disease context | “What conditions can cause this pattern of pancreatic enlargement?” | Assistant; relevance accepted by Quinton | Retrieve cited general associations for confirmed findings; do not invent a pattern or infer a diagnosis from an outline. |
| Disease context | “Could the size of the pancreas head indicate any specific diseases?” | Quinton | Distinguish a measured finding from general disease context. State what evidence and accompanying findings are needed; do not turn size alone into a patient-specific disease label or probability. |
| Lesion measurement | “How large is the outlined lesion, and where is it located?” | Assistant; relevance accepted by Quinton | Report defined lesion dimensions/volume and qualified anatomical location. This is a multi-part variant: both outputs need validation. |
| Lesion measurement | “What is the size of the lesion in this scan?” | Quinton | Measure the selected outline using a defined method; resolve which lesion if several exist. Missing or invalid outlines must not yield invented numbers. |
| Differentiating findings | “What additional findings help distinguish inflammation from a pancreatic tumor?” | Assistant; relevance accepted by Quinton | Retrieve supporting and limiting imaging evidence; distinguish literature-described signs from findings actually measured or reviewer-confirmed in the selected scan. |

These are behavior requirements to qualify, not prepared answers. No source passages, gold labels,
measurements, disease probabilities or answer-quality scores are supplied by this list. Measurement
implementation remains in the required extension after core RAG acceptance. The new disease corpus
is a candidate reference collection, not proof that these questions are currently answerable.

## Drafting and evaluation responsibilities

We can draft and refine development questions together. Quinton supplies realistic wording and
judges whether the interaction serves the intended review workflow. Engineering handles capability
mapping, evidence discovery and label preparation, and must arrange the independent verification
process. Quinton is not assigned article searching, passage offsets or technical evidence labels.

Quinton offered to write 30 non-overlapping questions when evaluation is ready. Record that as a
future authoring commitment, not a completed test set or a request to create it now. Broad capability
categories may occur in both splits; near-duplicate intents and paraphrases must stay together.
Different wording alone does not establish independence. The existing protocol also requires family,
answerability and difficulty balance, including unsupported and refusal cases.

All eight wordings here and their intent groups are known development exposures. Before creating
any protected set, include this document and the additional conversation exposures in a new version
of the exposure inventory. Preserve the older pinned inventory and accepted v5 checkpoint unchanged.
Do not label this list held-out, add it to the literature corpus, or use its behavior notes as model
answer text. No protected questions have been requested or accessed in this update.

## Next work

Map these five task groups to the actual case inputs, measurement tools, reference eligibility,
retrieval and unavailable-information behavior in a versioned capability contract. Reconcile the
independent labeling workflow and evaluation coverage before asking for the final private questions.
Counts, thresholds and existing acceptance records are unchanged by this draft.

References: [completion spec](AI-EXPERT-COMPLETION-SPEC.md),
[measurement extension](MEASUREMENT-AWARE-EXPERT-PLAN.md),
[disease-source report](DISEASE-REFERENCE-CORPUS-2026-10-17.md),
[evaluation protocol](QUESTION-SET-AND-EVALUATION.md), [AI-03](https://trello.com/c/NctoNxr8).
