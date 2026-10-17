# Scope verification — October 15, 2026

Quinton approved the next stage after structured selection removed copying failures but retained
study mismatches. This implementation is experimental; the live quotation policy stays unchanged.

## Contract fixed before comparison

Review each selected excerpt separately with its entire retrieved source passage and question.
The pinned local Qwen3:8b model supplies explicit technique, disease, task, named-study, cohort,
design and directness assessments: match/mismatch/uncertain/not_requested. Directness cannot be
not_requested. Server aggregation requires every requested dimension to match; mismatches and
uncertainty remove the excerpt. A kept excerpt must identify an offered same-passage span containing
the original selection, optionally expanding to retain method, cohort, requested result and
qualifications. No cross-source reassignment or substitution of another selected result is allowed.
Exact quotation validation still follows model-assisted scope review. It is not a semantic proof.

Keep the original selection, catalog/question/prompt/schema hashes, every assessment and reason,
model-response hashes, decisions, and scope duration. Invalid/incomplete assessments fail closed
for the whole answer; unavailable model raises a service error, never returns unchecked evidence.
Valid abstentions skip review. The same model reviewing its own selection is not independent
verification. Human/agent engineering judgments against the frozen rubric remain the evaluation.

First comparison: reuse all ten saved structured-span selections and their exact baseline passages,
not another selection run. This isolates added review from stochastic/selection changes. No gold
aspects, scope labels or reference IDs enter the model. Up to12 review calls are expected from the
saved12 excerpts; no calls for the three existing abstentions. Retain rejected and malformed output.
Assess per-excerpt removals/expansions, lost relevant evidence, clean answers, aspect coverage,
correct abstention, generation failures and latency. Seek more than4/7 clean answers, no lost
baseline aspects,3/3 correct abstentions and no validation failures before proposing promotion.
One bounded comparison, no prompt/model sweep. Final held-out evaluation remains separate.

The experimental CLI `--selector scoped-spans` can run selection followed by verification. With
`--reuse-selection`, it instead checks question/suite/retrieval identity and reviews frozen inputs.
Per-request worst-case time can exceed the existing live UI timeout because each stage uses the
existing90-second model deadline; live activation requires a separate total-deadline integration.
No current UI or API default is changed by adding this experiment.

## Results

First comparison completed:10 review calls (two cases stopped on invalid assessments),5/7 supported
answers,4/7 clean answers,9/14 aspects,5/6 relevant extracts,3/3 preserved correct abstentions,
two generation rejections. Rejected for lost EUS/nCLE evidence and erroneous CT study approval.
The non-reasoning model treated unrequested study design as uncertain, then supplied a keep-span,
violating the assessment contract. It also accepted an unrelated CNN study while claiming550
subjects exceed1000. Raw failures and producing sources are preserved, not rewritten.

**Evidence-driven follow-up, fixed before execution:** test the same verifier with Qwen3:8b's
reasoning mode enabled. This changes `think` to true, replaces the mode directive `/no_think`
with `/think`, and raises the output ceiling900→4096 to accommodate reasoning. The actual scope
instructions, schema, source selections, model/digest, temperature, seed and scoring remain fixed.
This is one explicit inference-profile comparison prompted by the failed scope judgments, not
another prompt wording variant or a model sweep. Reasoning mode is an explicit experimental flag,
recorded in manifest/provenance; existing defaults remain unchanged. At most12 review calls,90s
HTTP timeout each; no automatic retry. Assess the same promotion criteria and preserve both runs.

## Outcome: retain experimentally; do not activate

| Measure | Structured selection alone | Added review, reasoning off |
| --- | ---: | ---: |
| Supported questions answered | 7/7 | 5/7 |
| Clean complete answers | 4/7 | 4/7 |
| Covered aspects | 12/14 | 9/14 |
| Strictly relevant extracts | 8/12 | 5/6 |
| Exact published citations | 12/12 | 6/6 |
| Correct missing-evidence abstentions | 3/3 | 3/3 (selection preserved) |
| Generation rejections | 0 | 2 |

Review removed the irrelevant radiomics application sentence, making that answer clean. It kept
the correct CT, MRI and PET answers. But it lost the general EUS answer, failed to retain nCLE
evidence, and still endorsed the unrelated CNN result for the specific CT-radiomics question.
The smaller number of irrelevant published excerpts does not offset lost useful evidence.
Ten actual review calls produced6 keep,2 reject and2 invalid decisions. Two remaining candidates
were never reviewed because their case stopped on an invalid assessment. Review-stage latency
for the seven supported cases: median4.020s, range2.951–7.764; this excludes reused selection time.
The three abstentions skipped the verifier, so3/3 is preservation, not newly demonstrated rejection.

The reasoning-mode comparison was stopped early. Radiomics consumed4096 output tokens in88.16s
and returned `done_reason=length` without final JSON, correctly causing generation rejection.
By the time the owned client was interrupted, four cases had completed: radiomics rejected, EUS
and CT detection retained complete relevant answers, and nCLE failed on another invalid assessment.
The client was interrupted during CT external review; no final receipt for that case or the five
remaining cases exists. They are **unscored**, not assumed to pass/fail. No full-suite reasoning
score is claimed. The owned client exited130; Ollama logged cancellation and all slots idle.
Other services were left running, and the answer API health route still responded successfully.

The two profiles do not establish a reliable scope verifier. Same-model self-review can approve
an incorrect interpretation while producing plausible structured checks. The current small-model
configuration should not be presented as semantic validation or used to upgrade the demo's claims.

## Offset-binding repair

Code review found a separate deterministic defect: identical text repeated within one passage
could offer context around the wrong occurrence. A new regression failed before repair. Support
candidates now derive from the original selected IDs and their exact offsets, rather than every
matching string in that passage. The regression and all53 focused checks pass after repair.
This is a source-binding repair, not a claimed model-relevance improvement.

Producing source snapshots were preserved before amendments. Ten non-reasoning raw-response
replays after the offset repair reproduce answers, validations, assessments, duration and output
hashes exactly (explicit inference-profile metadata was added afterward). All four completed
reasoning receipts replay to identical entire generation objects. These14 checks used no model
or database calls and do not replace live semantic evaluation.

## Artifacts and use

Implementation: `src/retrieval/scope_answer.py`; evaluator `--selector scoped-spans`, optional
`--scope-reasoning`, and `--reuse-selection` for the isolated comparison. The span selector now
accepts an injected API callable so full selection+verification can retain both stages' raw outputs.
Existing default generation and APIs remain unchanged; no UI edits or service restart occurred.

Public judgments:
- `configs/evidence/evaluation/scope-checked-spans-v1-review.json` (complete failed run)
- `configs/evidence/evaluation/scope-reasoning-v1-partial-review.json` (explicitly partial)

Ignored local evidence under `outputs/prowl/development-evaluation-20261015/`:
- `scope-checked-spans-v1/`: manifest,10 case receipts, raw responses, score, producing sources.
- `scope-reasoning-v1/`: manifest,4 completed receipts, raw responses, interruption receipt and
  producing sources. No result retained from the interrupted CT-external inference.
- `scope-replay-after-offset-fix.json`:14 offline replay results.

Recompute the complete non-reasoning score without inference:

```sh
.venv-retrieval/bin/python -m src.retrieval.evaluation --run outputs/prowl/development-evaluation-20261015/scope-checked-spans-v1 --review configs/evidence/evaluation/scope-checked-spans-v1-review.json
```

For an intentionally new scope experiment, provide a fresh output directory:

```sh
.venv-retrieval/bin/python scripts/retrieval/evaluate_answers.py --selector scoped-spans --reuse-retrieval outputs/prowl/development-evaluation-20261015/baseline --reuse-selection outputs/prowl/development-evaluation-20261015/structured-spans-v1 --output outputs/prowl/development-evaluation-20261015/NEW-RUN-NAME
```

Next should be a bounded evaluator-capability comparison on the known scope failures, with a hard
time budget and explicit loss-of-evidence checks, before adding more model-review stages or live
orchestration. The experimental source-binding and audit interfaces are reusable. A different
evaluator or request-scope design must earn its own evidence; neither is implemented here.
No full selector, training, corpus write, download, model change or human-hours credit.
