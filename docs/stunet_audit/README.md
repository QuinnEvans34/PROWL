# STU-Net audit — review entry point

**Latest:** [clearance follow-up](09_clearance_followup.md). Current leakage-free/unseen-patient claim: **NO-GO**; model remains conditionally usable for a future controlled study. The public 901-case cohort has documented historical test/selection use. Author outreach drafts are local only by user direction; sending is not authorized.

Status: **bounded audit complete, with declared blockers and uncertainty**. Recommendation: **CONDITIONAL GO for a controlled transfer study; no leakage-free/unseen-patient clearance and no training launch**. Read the final decision first. All 75 development scans were compared with 1,203 valid original-v1 reference CTs; one corrupt source member remains blocked. Five cases are suspected and 70 unresolved; none is confirmed or cleared.

| Report | Purpose |
| --- | --- |
| [01 — inventory](01_project_inventory.md) | Actual cohort, current models/metrics and methodological limits |
| [02 — provenance](02_checkpoint_provenance.md) | Original checkpoint identity, upstream split uncertainty and loader map |
| [03 — verification](03_checkpoint_verification.md) | Acquisition, restricted loading and actual synthetic evidence |
| [04 — overlap](04_dataset_overlap_report.md) | Source matrix, duplicate methodology, reference coverage and case findings |
| [05 — feasibility](05_transfer_feasibility.md) | Geometry, targets, optimization and unqualified resource limits |
| [06 — proposed protocol](06_experiment_protocol.md) | Matched initialization comparison and final-evaluation requirements |
| [07 — final decision](07_final_decision.md) | Recommendation, confidence, unresolved evidence and ranked next steps |
| [08 — author questions](08_author_questions.md) | Draft questions only; nothing sent |

Machine-readable inputs/results: `source_manifest.json`, `checkpoint_manifest.json`, `archive_manifest.json`, `source_provenance.csv`, `selected_source_metadata.json`, `pants_metadata_schema.json`, `upstream_plan_summary.json`, `overlap_results.csv`, `overlap_summary.json` and `execution_manifest.json`. Exact field names and caveats are documented in the inventory and overlap report. The final synthetic suite has 28 passing tests; optional translation diagnostics stopped at their allocation guard and are reported as partial, not completed negative checks.

## Reproduction and boundaries

Run synthetic tests from the repository root:

```sh
PYTHONPATH=. OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv312/bin/python -m unittest discover -s tests/stunet_audit -v
```

Image-read tools require an explicit pinned manifest/request and a fresh output directory. They are not a training launcher. Do not rerun them casually: retained supervised evidence is under `/Volumes/PROWL-Data/PROWL/artifacts/stunet-audit-20261106` and local ignored logs under `outputs/prowl/stunet-audit-20261106`. Reuse verified fingerprints before considering another CT read. Source metadata tooling intentionally refuses an existing output, preserving earlier results.

The original author-linked checkpoint and upstream source checkout live externally under `/Volumes/PROWL-Data/PROWL/teachers`. Original TotalSegmentator v1 acquisition attempts and completed parts are retained under `/Volumes/PROWL-Data/PROWL/sources/totalsegmentator-v1-audit-20261106*`. No archive, weights or CT pixels belong in Git.

Publication checkpoint, November 20: the owner authorized committing and pushing the audit code and reports. The case-level `source_provenance.csv` and `overlap_results.csv` remain local by explicit owner decision; references to them describe retained local evidence, not files distributed in this repository. Original reports and evidence manifests preserve their historical status. The proposed protocol is a design for review, not a scientific launch request, producing recipe or model-promotion decision.

Follow-up machine-readable decisions: `leakage_clearance.json`, `test_use_ledger.json`. Concrete unsent correspondence: `10_author_outreach.txt`. The follow-up manifest supersedes the initial execution manifest while preserving its exact release externally.
