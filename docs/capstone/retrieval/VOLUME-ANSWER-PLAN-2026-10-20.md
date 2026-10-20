# Week 3 volume-answer slice

**Status:** Offline selector qualified; composition/integration pending; live policy unchanged.\
**Card:** [W03-03](https://trello.com/c/pnaJmVIz).\
**Inputs:** Existing reviewed volume facts and their source/review hashes; no corpus expansion.

## Behavior to deliver

| Question type | Required behavior |
|---|---|
| General average/mean whole-pancreas volume | Offer the reviewed normal-glucose-tolerance comparison group's MRI result as a selected-study example, with all qualifications |
| Type 2 diabetes whole-pancreas volume | Use only the reviewed well-controlled/metformin group; make that narrower population explicit |
| Explicit comparison of those two groups | Keep both groups and numbers separate; do not generalize to all diabetes or claim causation |
| “How large is the average pancreas?” | Clarify volume versus length/head diameter; do not silently choose a quantity |
| CT reference, normal range/percentile, children, healthy population, head/lesion size | Do not reuse these MRI whole-organ group means as an answer |
| Current scan, supplied measurements, diagnosis, treatment or mixed/instruction requests | Retain existing boundaries; no measurement interpretation |

“Normal glucose tolerance” is a study group descriptor, not proof that every member is healthy.
MRI, sample count, units, mean/SEM distinction, matching, group selection and applicability limits
are mandatory. Above/below a group mean is not a disease or normality decision.

## Sequence and finish conditions

1. Freeze the behavior above and qualify an isolated question-to-volume-record selector. It must
   admit canonical result anchors plus all context through the existing `FactCatalog`, never
   accept record IDs from users, and distinguish ambiguity from missing coverage.
2. Add reviewed wording and local-model composition with a separately versioned output contract.
   Keep disease behavior/pins intact; no unreviewed generated medical prose or expected-answer indexing.
3. Extend backend admission and exact UI reconstruction together. Explain source-only and
   application-summary fallback; citations stay available separately.
4. Before live promotion, freeze the bounded candidate check, preserve all failed attempts and
   manually inspect its claim/citation coverage. No broader quality or held-out acceptance inferred.

The first implementation block covers step1 only; no new live flag or service replacement.
Its tests use invented facts for source admission, and the retained public corpus may be used for
one offline admission check without database/model calls. W03-04 subsequently broadens the exposed
wording matrix; W03-05 is the weekly quality checkpoint.

[First-block results](VOLUME-ROUTING-RESULTS-2026-10-20.md): 64 focused checks pass and seven
offline corpus examples select the expected records or boundaries. Continue at step 2.

## Risks and limits

The finite English routing grammar is conservative and can miss paraphrases or nuanced exclusions.
Tests qualify named examples, not arbitrary-language understanding. Unknown populations/methods
must not silently map to the two available records. Shared corpus metadata and review hashes protect
identity; semantic correctness still relies on source review. Independent review remains pending.
