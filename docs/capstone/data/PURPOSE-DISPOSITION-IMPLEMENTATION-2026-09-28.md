# Next data slice: purpose-specific rejection and retained decisions

September 28, 2026. Quinton authorized this slice after checkpoint publication.
The synthetic rejection-only helper is now implemented: **44 focused tests and 631
non-retrieval tests pass**. See completion evidence below. No real diagnostic package,
cohort, source read or training run was produced. Original design text follows.

## Problem and outcome

The approved decisions in PURPOSE-ELIGIBILITY-DECISIONS are currently prose.
The v2 annotation contract has broad allowed uses such as training_target, while the
cohort contract separates train/validation/test roles. Neither alone distinguishes
pancreas-present localization from anatomy-absent robustness or geometry-dependent use.

Implement a narrow, fail-closed purpose check and append-only issues using existing
contracts. It must reject case 78 for pancreas-present localization and hold cases
2/266 for geometry-dependent training, with reviewed evidence linkage. It must never
grant eligibility just because those three exceptions do not apply.

## Inputs and trust boundary

- Explicit requested task/purpose and protected role; no default training purpose.
- Validated study/annotation records and exact source hashes from a pinned manifest.
- Retained decision/evidence bytes and independently reviewed expected hashes.
- The existing approved binary-lineage verifier when a later consumer requires mapping.

Do not trust hashes or permission claims supplied only by the record being evaluated.
Bind each decision to the correct study, annotation/CT as applicable, source snapshot,
evidence identity and requested purpose. A changed source or missing decision requires
review. Do not interpret arbitrary Markdown prose at runtime or route only by case number.

## Contract approach

Reuse data-issue v1 fields: rule_code, entity identity, severity, disposition, evidence,
supersedes_issue_id and resolution_artifact_id. Version the code's supported rule registry
and its purpose mapping; never recover purpose by parsing a human message.

Proposed rules:

| Rule | Applies to | Decision |
|---|---|---|
| PANCREAS_PRESENT_TARGET_EXCLUDED | Verified case-78 source/evidence, pancreas-present localizer | Exclude for that purpose; retain original study and protected membership. |
| PHYSICAL_UNITS_UNRESOLVED | Verified cases 2/266 source/evidence, geometry-dependent training | Hold pending applicable unit evidence. |

Unknown purposes, missing qualification or contradictory/stale evidence are rejected.
The checker returns rejection reasons or a statement that this narrow rule check found
no additional block. The latter is explicitly NOT an eligibility or training authorization.
It must not expose an unconditional eligible=True convenience result.

Keep general quarantine and all other unresolved issues. Do not change a study to globally
excluded because one purpose is inappropriate. Empty pancreas does not imply disease absence.
An anatomy-absent robustness candidate still needs its own qualification, task and metrics.
Broad training_target permission cannot bypass the requested-purpose check.

No new generic serialization layer or v1/v2 migration is proposed. If existing issue fields
cannot represent the required linkage unambiguously, stop and present the precise schema
gap before changing contracts. Future production cohort publication/resolution must invoke
this check alongside source, geometry, annotation, identity and ancestry checks.

## Bounded first implementation

Allowed proposed files: new src/data/purpose_disposition.py and
tests/test_purpose_disposition.py, plus this plan's completion evidence. Read existing
manifest/annotation/identity helpers; do not alter their historical behavior in this slice.
Use invented fixtures only. No real disposition publication until the helper and exact
publication inputs receive review. No legacy training-script integration or Plan 04 code.

Acceptance tests must cover:

1. Case-78-shaped fixture rejected for localizer use without changing membership/inputs.
2. Unknown-unit fixtures held even when their numeric spacing is plausible or grids match.
3. Correct-looking policy with wrong study, source hash, evidence hash or purpose rejected.
4. Missing/unknown/conflicting decisions fail closed; duplicate or dangling references rejected.
5. Broad annotation permission never overrides unresolved purpose/source/identity holds.
6. Absence of these specific exclusions grants no use; robustness receives no automatic promotion.
7. Existing issue history remains intact; later resolution requires new linked evidence.
8. Synthetic manifest/consumer boundary rejects held inputs before selecting members;
   this demonstration is not a completed production cohort loader.
9. Canonical replay is deterministic for identical persisted inputs, including issue IDs/times;
   no mutation, source access or protected-role reassignment.

Run the focused tests and existing non-retrieval suite, keeping Claude's active tests separate.
Review the change before any saved-evidence package publication. Such a publication must use
a new identity, verify retained inputs/outputs and preserve the five-study diagnostic package.

## Route from this slice to the first smoke run

| Step | Required exit evidence |
|---|---|
| Purpose guard | Tests above pass; no eligibility promotion; code/decision linkage reviewed. |
| Source/annotation qualification | Resolve applicable source protocol, geometry, encoding, identity/duplicate protection and allowed-use evidence; explicit holds remain for unresolved cases. Complete G1's required coverage rather than treating five examples as a qualified source. |
| Frozen cohort publication/resolution | Train-role parent/ancestor enforcement, versioned purpose, qualified membership and profile hashes, immutable completion marker, exact replay and altered-package rejection. |
| Preprocessing/run slice | Synthetic orientation/spacing/label and source-space round-trip tests; scratch lineage; immutable run/config/environment/checkpoint records and reload/interruption checks. |
| Exact smoke plan | Pancreas-localizer wiring question, specific cohort/config, seed, steps/time/memory/disk caps and numerical pass/stop criteria recorded before compute. |
| Launch review | R0–R8 in FIRST-EXPERIMENT-READINESS satisfied for that run, storage/restore and exclusive accelerator ownership checked; explicit launch review. |

No numeric training budget or cohort size is invented here. Those follow actual qualified
inputs and small-fixture resource evidence. Every attempt belongs in docs/experiments.md.
No prior project-trained checkpoint reuse, protected-test tuning, source rewriting or
assumption that retrieval must finish before imaging. The publisher reply can resolve a
specific hold later; waiting for it need not stop synthetic engineering or other qualification.

## Implementation and verification

Implemented in `src/data/purpose_disposition.py`, tested in
`tests/test_purpose_disposition.py`. No existing runtime module or schema was modified.

- `make_purpose_issue` creates a proposed existing-schema data-issue v1 record. Explicit
  IDs/timestamps make identical inputs replayable. Construction itself is not attestation.
- `check_purpose` requires independently reviewed canonical study, annotation and issue
  hashes plus retained decision/evidence bytes and their independent pins. Every purpose
  issue binds policy version, requested purpose, study, snapshot, CT and annotation hashes.
  It validates prior issue references, rejects conflicts/duplicates/dangling references,
  and checks already attached purpose issues as well as new proposals.
- Rules are chosen by reviewed evidence, never inferred from case number, plausible
  spacing or an empty mask. Synthetic fixtures use case-78 and case-2/266-shaped contexts;
  no actual case decision has been materialized or published by this task.
- This first version is deliberately rejection-only: missing purpose decisions reject;
  there is no clearance rule. It returns no allowed uses and never promotes eligibility.
  The units hold applies conservatively to all three supported purposes, including
  anatomy-absent robustness. A future non-geometric robustness workflow needs its own
  reviewed purpose definition, not reuse of a permissive default.
- Supersession/resolution is unsupported and rejected. A later resolution needs reviewed
  evidence and a separately implemented path. Original records are never mutated.
- Caller-supplied train role is checked, but full frozen ancestry, subject/snapshot
  qualification, actual geometry, approved binary lineage and source-byte integrity
  remain separate consumer responsibilities. Hashes establish identity, not truth.
  The synthetic consumer/manifest tests are not a production loader or frozen cohort.

Focused run: **44 passed**, 0.17 seconds. Full existing suite excluding Claude's active
retrieval lane: **631 passed**, two existing torch.jit deprecation warnings, 5.23 seconds.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/test_purpose_disposition.py -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests --ignore=tests/retrieval -q -p no:cacheprovider
```

Tests cover every acceptance category above: deterministic/no-mutation issue creation,
wrong source/study/snapshot/purpose bindings, evidence/pin tampering, unsupported rules,
duplicate/conflicting issues, missing qualification, broad permission bypass attempts,
history retention, resolution refusal and synthetic consumer rejection before selection.
A real v2 manifest assembled from invented inputs stays quarantined after attaching the
new blocking issue and replays exactly. Initial focused failures exposed invalid test
fixtures (eligible without geometry, then quarantined without an issue); fixtures were
corrected to a valid discovered state without relaxing existing schema checks.

No source data, existing evidence packages, Claude files, memberships or training inputs
were changed. No new Git commit/push occurred in this implementation task.

Next: review exact retained evidence and publication inputs for an append-only diagnostic
disposition package, including how case 2's earlier evidence relates to the five-study
v2 package (which contains case 266 and case 78, not case 2). Do not silently extend that
package or mark qualification complete. The remaining source/cohort/smoke gates above
still apply.
