# Volume composition and UI integration results

**Outcome:** W03-03 complete for its bounded development scope; candidate1.1 promoted locally.\
**Review sheet:** [Actual volume answers](VOLUME-ANSWER-REVIEW-2026-10-20.md).\
**Declared check:** [Scope, attempts and criteria](VOLUME-COMPOSITION-CHECK-2026-10-20.md).

## Delivered behavior

Typed whole-pancreas volume questions select the existing reviewed MRI study records and use local
Qwen3:8b to choose reviewed wording and paragraph arrangement. Code requires every fact, population
qualification, method, unit, SEM explanation, matching statement and interpretation limit. It
attaches canonical citations; the UI independently reconstructs the displayed text and citations.
The two groups remain separate. This is constrained composition, not unrestricted generated prose.

“How large is the average pancreas?” asks whether the user means volume or a linear measurement.
CT references and unsupported populations do not acquire an MRI study answer. Current-scan and
instruction requests retain the existing boundaries. Model failures produce an explicitly labeled
application summary; source admission failures remain errors.

## Evidence and limitations

| Check | Result |
|---|---|
| Initial candidate | 6/8; three model calls. Legacy measurement routing blocked diabetes mean; complete comparison plan failed paragraph contiguity |
| Admission-only attempt2 | Zero model calls; resident-model preflight stopped before execution; retained |
| Corrected candidate, attempt3 | 8/8; four model-composed answers, four no-model boundary cases |
| Covered-request timings in attempt3 | Average7.524s; diabetes6.531s; comparison12.450s; disease regression3.759s |
| Canonical corpus | 1,179 passages admitted; every returned source matched |
| Manual citation review | All ten displayed answer paragraphs inspected; source facts, glossary and application limits distinguished |
| UI replay | All eight retained HTTP responses accepted by the actual UI validators; no new model calls |
| Backend repair suites | 83 passed, including26 volume-composition checks,31 selector checks and26 original development-search checks |
| Existing disease regression suites | 55 passed earlier in this implementation block |
| UI suites across this block | 68 distinct checks:47 literature,17 volume,3 AskPanel and1 retained-response replay |
| Build | Pass; existing large-chunk advisory remains |

The initial backend fixture hash error (18 setups refused) and one UI copy-regression failure are
also recorded in the check document. No failures were removed or counted as successes.
This is an exposed development check, not held-out evaluation, clinical validation, or a general
latency/wording guarantee. Source review remains a single engineering review.

The layout repair changes only grouping of complete volume paragraphs. Shared exact validation
still rejects omissions, duplicates, changed words, reordered units within a group, mixed
qualification paragraphs and invalid citations. The scope repair applies only to a general
study-mean intent already admitted by the volume selector; it does not loosen the original
disease/scan policy.

## Local promotion and browser verification

After the check, manual review and UI replay passed, the verified previous API PID73251 was stopped.
Replacement API **PID9015 / owned session21308** started with:

```sh
PYTHONPATH=.:scripts .venv-retrieval/bin/python scripts/serve_literature_search.py --volume-answers
```

The health endpoint, including through UI5180, advertises `source-literature-answer-v2` and
`source-linked-literature-search-v2`. Volume responses identify `source-volume-answer-v1.1`;
disease responses preserve `source-record-answer-v1`. Corpus and pinned model identity are unchanged.
Ollama and Vite remain running; no database restart/ingestion, model download or training.
Rollback after inspecting the current owned process is the prior `--record-answers` launch.

Two browser requests were verified: the size clarification (no model call), then one real
average-volume answer (one additional composition call). The latter displayed the expected two
paragraphs and four source passages. Citation4 opened PMID25950180/body-17, characters11231–11769,
with the matching group values. Returned to Answer and saved the screenshot. Eight actual model
calls across this work block:3 in attempt1,0 in attempt2,4 in attempt3,1 browser check.

Retained outputs:

- `outputs/prowl/volume-answer-v1-20261020/` — first candidate, all raw plans and producing files.
- `outputs/prowl/volume-answer-v1-attempt2-20261020/` — admission refusal, zero calls.
- `outputs/prowl/volume-answer-v1-attempt3-20261020/` — successful receipt, plans, responses,
  producing files, `manual-review.json` and `live-volume-answer.png`.

## Next

W03-04 broadens the exposed wording/selection matrix; W03-05 performs the weekly quality review
and Quinton walkthrough. The finite English grammar can still miss paraphrases or fail on nuanced
mixed requests. Those tasks and formal AI-03/04 acceptance remain open. Measurement-aware
pancreas/lesion integration is still required after core acceptance.
