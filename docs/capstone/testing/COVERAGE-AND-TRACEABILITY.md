# Coverage and test traceability

**Status:** Approved design; implementation remains gated  
**Decision:** P09-16, P09-18, P09-19, and P09-20  
**Last reviewed:** 2026-09-09

Current 43-requirement evidence/check reconciliation: [October 12 closeout](../weeks/WEEK-01-CLOSEOUT-2026-10-12.md).
This mapping does not establish a coverage percentage or fresh full-suite pass.

## Governing principle

September 20 implemented foundation families and their independent oracles are recorded in
[the contract/metric checkpoint](CONTRACT-METRICS-2026-09-20.md). This is bounded traceability,
not full requirement coverage or a line/branch coverage claim.

Coverage answers “which executable lines/branches ran?” Traceability answers “which requirement,
risk, and failure mode was actually challenged?” PROWL uses both, with traceability as the gate.

## Check record

Every planned/implemented check receives:

```text
check_id
title
requirement_ids[]
risk_ids[]
plan_ids[]
layer
automated_or_manual
fixture_ids[]
oracle
determinism_class
command_or_protocol
expected_result
status
last_evidence_id
owner
blocker_or_expiry
```

## Stable check ID families

| Prefix | Area |
|---|---|
| `T-GOV` | Governance, paths, source hierarchy, release identity |
| `T-DATA` | Source/identity/cohort/PANORAMA |
| `T-WF` | Orchestration/state/retry/idempotency |
| `T-IMG` | Imaging/preprocessing/localization/spatial/model |
| `T-MET` | Metrics/holdouts/experiments/reports |
| `T-RET` | Corpus/query/index/retrieval/response |
| `T-UI` | Interface/adapters/accessibility/review persistence |
| `T-OPS` | Environment/storage/backup/compute |
| `T-E2E` | Integrated workflow/release |
| `M-*` | Manual scientific, visual, claim, and stakeholder checks |

IDs persist when files/functions move. A materially different assertion gets a new ID.

## Coverage use

- Collect statement/branch/function coverage for new pure capstone Python and UI domain/adapter code.
- Define inclusion patterns so unimported source files remain visible.
- Establish the first trustworthy baseline after test configuration is stable.
- Review declines by changed module and missing scenario; do not game totals with exclusions.
- Generated schemas, third-party code, large model definitions, migration scripts, and rendering glue
  may have different expectations, but their required behaviors still need checks.
- No repository-wide percentage can override a missing high-impact scenario.

## Required completeness audits

Before G0/G7/G8:

- every approved requirement has at least one planned check;
- every high-impact risk has prevention verification and contingency/failure test where feasible;
- every locked decision with executable consequences is covered;
- every contract branch and cross-record invariant is represented;
- every known high-impact historical defect has a regression or explicit manual control;
- every `skip`, `xfail`, quarantine, or manual-only item has owner/status/evidence;
- every completed plan links to current passing evidence.

## Defect lifecycle

1. Preserve failure evidence.
2. Assign severity, affected requirement/risk/artifacts, and reproducibility.
3. Add or identify a failing regression.
4. Fix the smallest owning component.
5. Run targeted test, affected suite, and appropriate broader gate.
6. Record fix identity and close only when evidence passes.

If automation is infeasible, record a repeatable manual protocol and why automation was deferred.
