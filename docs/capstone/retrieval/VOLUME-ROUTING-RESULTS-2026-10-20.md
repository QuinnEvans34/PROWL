# Volume question selection — first implementation block

**Status:** Offline development qualification; live API and UI unchanged.\
**Plan:** [Volume-answer slice](VOLUME-ANSWER-PLAN-2026-10-20.md).\
**Tracking:** [W03-03](https://trello.com/c/pnaJmVIz), first checklist item complete; remaining three open.

## Change

`src/retrieval/volume_record_search.py` routes typed volume questions to the existing two
reviewed MRI study-group records. Source-derived lexical ranking is followed by exact
`FactCatalog` admission, canonical result anchors, complete context and deterministic
render/verification. It does not index expected evaluation answers.

General mean-volume questions can select a study example with its applicability limits.
Explicit group comparisons select both records. Ambiguous size questions request clarification;
the tested CT, healthy-population, head-size and individual-scan requests do not select these
records. This finite English grammar is conservative, not a general semantic classifier.

## Verification and retained failures

The focused command was:

```sh
.venv-retrieval/bin/python -m pytest -q tests/retrieval/test_volume_record_search.py tests/retrieval/test_fact_records.py
```

Final result: **64 passed**, comprising 31 selector checks and 33 existing source-fact checks.
The first attempt had **1 failed, 60 passed**: the supplied-number guard incorrectly rejected
the `2` in `T2DM`. Population-label normalization was corrected, and three additional
population/comparison boundary cases were added before the final run. No actual corpus
admission check preceded that correction.

One offline check then used all 1,179 canonical passages from the retained corpus and the
existing catalog/review hashes. Seven questions were saved before execution:

| Question | Observed selection |
|---|---|
| What is the average pancreas volume? | Normal-glucose-tolerance study group; four evidence passages |
| What is the mean pancreas volume in type 2 diabetes? | Well-controlled/metformin study group; four evidence passages |
| Compare mean pancreas volume in normal glucose tolerance versus type 2 diabetes. | Both records; four shared evidence passages |
| How large is the average pancreas? | Clarification; no record |
| What is the average pancreas volume on CT? | No matching record |
| What is the mean pancreas volume in healthy adults? | No matching record |
| What is the average pancreas head volume? | No matching record |

All seven matched the declared routing expectations. Both selected records also passed the
existing renderer's exact fact/citation verification. These are exposed development examples,
not independent evaluation or an estimate of arbitrary-question accuracy.

Retained artifacts: `outputs/prowl/volume-routing-20261020/cases.json` and `results.json`.
Source snapshot SHA256:
`611e7e2e70217a927b6c8feb753352de1892c4d3d4f29d3e69d55398f69cfe4d`.
This check made **zero database calls and zero model calls**, and changed no live policy.

## Remaining work

The source facts retain their October 18 engineering review; this run is not a new independent
medical-source review. The selector is not connected to the live API. Before promotion, add
reviewed wording, a versioned local-model output contract, backend admission and exact UI
reconstruction, then inspect readable answers and their citations in a fixed bounded check.
Record-selection success alone does not close the readable-output or quality checklist items.
