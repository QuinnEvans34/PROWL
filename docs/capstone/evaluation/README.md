# Evaluation and experimentation design package

**Status:** Approved Plan 06 design package; implementation dependencies remain  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/06-evaluation-and-model-experimentation.md`](../implementation/06-evaluation-and-model-experimentation.md)

## Purpose

This directory defines how PROWL turns continuous model training into trustworthy knowledge. It
separates the fast development loop from formal baseline, controlled-comparison, and final holdout
claims while keeping every run reproducible and visible.

## Package map

**Standing future-model requirement (November8):** integrate and qualify the
[fixed5mm predicted-pancreas postprocessing policy](SEGMENTATION-POSTPROCESSING-POLICY-V1.md),
retain raw predictions and publish matched raw/filtered evaluation for every new
pancreas/lesion segmentation model. Do not alter currently frozen experiments.

| Document | Question answered |
|---|---|
| [`METRIC-SPECIFICATION.md`](METRIC-SPECIFICATION.md) | Exactly what is measured, on which cases, and how are empty/failure/multi-lesion states handled? |
| [`PREDICTION-SETS-AND-HOLDOUTS.md`](PREDICTION-SETS-AND-HOLDOUTS.md) | Which cohort/prediction roles may tune, compare, or confirm the system? |
| [`EXPERIMENT-PROTOCOL.md`](EXPERIMENT-PROTOCOL.md) | What makes a run exploratory, controlled, confirmatory, valid, or invalid? |
| [`CONTINUOUS-TRAINING-STRATEGY.md`](CONTINUOUS-TRAINING-STRATEGY.md) | How can training run throughout development without creating chaos or consuming the release buffer? |
| [`ERROR-ANALYSIS-AND-REPORTING.md`](ERROR-ANALYSIS-AND-REPORTING.md) | How are failures decomposed and converted into the next evidence-based experiment? |

## Non-negotiable rules

1. Training and experimentation are continuous after their per-run safety gates pass.
2. Weeks 5–6 are formal evidence milestones, not the only training weeks.
3. Week 9 allows only defect-driven stabilization reruns; Week 10 is frozen delivery.
4. Every run is classified before compute and cannot gain stronger status after seeing results.
5. Evaluation consumes registered prediction/cohort identities, never arbitrary first-N or free-form
   split paths.
6. Source-space raw output is evaluated and retained before any derived processing.
7. Every requested autonomous study remains visible as completed, warned, or failed.
8. A failed positive is not detected and a failed negative is not credited as correctly cleared in
   end-to-end task rates; completed-case specificity remains separately and correctly named.
9. Pancreas and lesion metrics remain separate and precisely named.
10. Multiple lesions remain available to tumor-wise evaluation; largest-lesion-only output is not the
    default.
11. Autonomous and pancreas-only provided-region results use distinct identities.
12. D-205 is chosen after autonomous baseline errors; D-208 is chosen from development evidence.
13. Null, rejected, invalid, interrupted, and operationally failed results remain in history.
14. The publisher-test cohort does not select any model, threshold, margin, processing, or score.
15. Machine-readable evidence is authoritative; manually copied numbers and project-board cards are
    summaries only.

## Planned schema families

- `metric-spec` — class/empty/failure/component/statistical conventions and version.
- `experiment` — question, class, preregistration, arms, fixed factors, bars, budget, and amendments.
- `experiment-run` — execution, inputs, outputs, health, terminal state, and lineage.
- `prediction-set` — requested membership and exactly one terminal prediction per study.
- `per-study-result` — segmentation, detection, localization, status, group fields, and costs.
- `component-match` — reference/predicted component identity and deterministic match evidence.
- `evaluation-result` — aggregates, intervals, curves, subgroup tables, and source artifacts.
- `release-selection` — frozen model/cascade/policy/metric identities before publisher-test use.

These are documentation contracts until Plan 06 becomes Ready. Plan 09 owns executable schema and
golden-fixture tests; Plan 10 owns storage, environment, resource, and retention implementation.

## Relationship to the living experiment notebook

[`../../experiments.md`](../../experiments.md) remains the active human-readable notebook by Quinton's
2026-09-18 direction. It contains the pre-run plan, every attempt's outcome, and the reasoning linking
one experiment to the next. New `CAP-EXP-NNN` entries link immutable capstone experiment/run/evaluation
artifacts rather than replacing the structured registry.

The preceding-project record and future ideas remain preserved below an explicit historical
boundary. Revisit those ideas under current data/holdout/run rules before scheduling them; no old
checkpoint becomes capstone initialization and no old test read becomes new held-out evidence.

## Next review

Quinton approved P06-01 through P06-15 on 2026-09-09, locking the evaluation architecture,
continuous-training guardrails, and experiment governance. Numerical model-selection bars and
D-205/D-208 remain intentionally evidence-dependent; Plans 09 and 10 still gate implementation.
