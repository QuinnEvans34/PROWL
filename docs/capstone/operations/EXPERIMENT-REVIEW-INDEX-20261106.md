# Experiment review index — November 6

Additive retrospective supplement to the [living notebook](../../experiments.md).
This index does not amend frozen hypotheses, mint new training runs, or claim that
today's review existed before yesterday's results. Executed identities remain the
original immutable request, receipts and MLflow run IDs.

| Work | Execution identity | Status and interpretation | Evidence |
| --- | --- | --- | --- |
| Matched Mac KD treatment/control | Original matched arms; treatment terminal run `1e356a71e4f74d5192a091fc40d3f6b8`; full continuation identities in analysis JSON | 24k and twelve native validations each complete; descriptive only, small selected gain and worse component coverage | [Completion](MAC-KD-COMPLETION-20261105.md), [full analysis](KD-DESCRIPTIVE-ANALYSIS-20261106.md) |
| Pretrained Universal Swin screen | Request SHA `4654d46b730abe8c144b1cc57af607d579154b1c96ff707c37861fbce55fadc5`; MLflow `051c194b2e54428aba6b9420129e18b6` | Complete, four positives, mean Dice .710754, no fine-tuning; overlap unknown, no negative-case estimate | [Frozen plan](UNIVERSAL-SWIN-OVERNIGHT-20261105.md), [outcome](UNIVERSAL-SWIN-RESULTS-20261105.md), [Mac checks](UNIVERSAL-SWIN-MAC-REVIEW-20261105.md) |
| November 6 KD analysis | Exact completed report SHA `2679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b` | Post-hoc descriptive review, no new model/data reads or MLflow writes | [Reproducible derivation](../../../scripts/diagnostics/review_completed_kd_20261106.py), [derived JSON](KD-DESCRIPTIVE-ANALYSIS-20261106.json) |
| Universal provenance/next adaptation | Planning only; no new request or GPU dispatch | Shared source datasets confirmed; exact patient/checkpoint membership unresolved; future balanced screen/adaptation conditional on admission | [Findings and study sequence](UNIVERSAL-SWIN-PROVENANCE-AND-NEXT-STUDY-20261106.md) |

The KD selected/terminal comparison uses the full 70-case supplied-region cohort;
the Universal result uses four CT-only positive cases. Their aggregate Dice values
are not interchangeable. Neither record establishes independent generalization.

All historical statuses, failures, checkpoints and source pins remain preserved.
No extra MLflow RUNNING record, duplicate training-hours entry or model-registry
promotion is created by this index. Future execution requires its own prospective
record under the existing experiment protocol.

Lenovo follow-up `1e6760f`: the [retained patient-crosswalk review](UNIVERSAL-SWIN-RETAINED-CROSSWALK-20261106.md)
and companion JSON are retained byte-for-byte on Mac. All four screen cases remain
unknown; zero verified unseen is not proof of zero actual overlap. This review
uses retained metadata only and does not change the completed screen results.
