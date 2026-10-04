# Real localizer qualification records — S3

September 28, 2026. Codex implemented the retained-evidence adapter and completed its dry run.
The results qualify cases **3, 26 and 31** for the narrow private, noncommercial pancreas-present
smoke purpose. These are S3 qualification artifacts, **not a frozen production cohort or permission
to launch training**. Package verification is recorded below.

## What changed

`src/data/localizer_qualification_records.py` carries the old five-study quarantine context into
source accounting v2 / manifest v3, then constructs one checked successor per candidate.
`scripts/diagnostics/qualify_localizer_inputs.py` supplies the independently pinned real evidence.
It checks five prior package receipts and their covered files, source controls, original base split
bytes, D-259 approval/implementation, and the source/use/alignment review. It opens no raw arrays.

All 9,901 protected identities retain their original 7,200/1,800/901 roles. The inventory accounts for
18,000 observed training-source CT/pancreas files; ten have current retained full-byte hashes.
The 901 test identities are protection-only: this artifact makes no test-payload observation claim.
Source accounting is complete **within that declared scope**, while source integrity remains partial.
This is not a full-source qualification or proof of biological patient uniqueness.

The migration changes only source-snapshot links on existing subject/study/annotation records.
Logical IDs survive this accounting migration; content pins identify the particular record version
inside its manifest. Consumers must never resolve these IDs without the manifest/content pin.
All 22 old issues survive the migration byte-for-byte. Specific purpose issues retain their original
historical bindings; they remain active blockers, not newly rebound evidence or clearance.

Each subsequent transition changes only one subject, study, pancreas annotation and its three generic
holds. It introduces a new qualified annotation identity, retains original CT/mask hashes and measured
geometry, verifies approved binary mapping lineage, and pins all five positive check receipts.
The previous manifests and issues remain in history. Unrelated lesions retain their holds.

| Candidate | Recorded outcome | Scope |
|---|---|---|
| 3 | Qualified | Private pancreas-present smoke training target; 7.5 mm slice spacing retained |
| 26 | Qualified | Same narrow purpose; no lesion-target permission |
| 31 | Qualified | Same narrow purpose; candidate retained even though only two proposed smoke members are needed |
| 78 | Blocked | Existing pancreas-present exclusion and other unresolved holds preserved |
| 266 | Blocked | Existing physical-unit restriction and other unresolved holds preserved |

There are **13 active issues** after the three transitions, down from 22: nine generic holds have
supported successors. This does not mean nine bad files were repaired. No original bytes changed.
Case 2 remains outside this five-study package and retains its separately documented unit hold.

The five positive checks are review attestations, not newly measured source audits. Their truth is
supported by the pinned prior evidence and Codex's review; the builder verifies dependency bindings
and consistency. Source protocol remains `human_validated` / `source_asserted` / `publisher_protocol`,
not per-file expert contour certification. Distribution and model release remain outside this use.

## Validation and bounded execution

Seven new synthetic tests check repeatability, preservation of history/unrelated holds, specific and
unknown hold rejection, missing evidence, absent use evidence, and unsupported per-file assurance.
The full native command passed **948 tests**, with the same two upstream torch.jit warnings:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

The adapter's `--check` dry run validated the actual records without writing outputs. Its first attempt
refused legitimate nested evidence filenames because the path rule only allowed basenames; that was
corrected to allow canonical relative descendants while still rejecting traversal and symlinks.
No output package was created by that failed attempt.

The separate `--run` requires the four exact manifest hashes reviewed in the dry run, before writing
through the existing bounded diagnostic Package class. Limits: ten minutes, 2 GiB observed process
RSS checked between case builds (not a continuous memory supervisor), 96 MiB output, and 100 GiB
internal free-space floor. This is a local retained-evidence job, not a new Plan 04 publisher.

## Next: production cohort publication and input resolution

The fixed two-case proposal remains **3 and 26**, ascending qualified IDs from the retained five-case
candidate pool, with no replacement/refill. Case 31 stays qualified for later frozen versions.
This deliberately small, source-positive/flag-selected pool tests learning mechanics; it cannot
establish generalization, specificity or representativeness. No filtering by model performance occurred.

S4 must use the shared Plan 04/10 publication and ownership controls, as required by the approved
[data-to-cohort packet](../operations/DATA-TO-COHORT-IMPLEMENTATION-PACKET-2026-09-28.md), section S4:
“writing a second unofficial publisher is out of scope. Plan 04 coding authorization remains separate.”
The next concrete implementation scope is that shared publication prerequisite plus the cohort
registry/resolver: protection parents, exact two-case members, dependency/transition checks,
no-overwrite/conflicting-ID/partial-artifact rejection and verified input descriptors. A production
reader must validate the complete history chain, including this source migration; a transition
certificate alone is insufficient. Existing pure cohort builders do not provide these disk guarantees.

S3 completion does not close G1 or enable disabled roots. Loader/preprocessing alignment, checkpoint
recovery, run identity and the recorded resource budget still follow before a real smoke launch.

## Saved artifact and independent replay

Package: `outputs/prowl/localizer-qualified-4123a108-7f14-453a-a741-e46d62344562/`.
Ten files, **34,570,184 bytes**. Receipt SHA-256:
`7018583fa42310a4a179efc0d5570eebb605a4b2d49c2f9883c33315b43872b2`.

A separate native process verified all nine covered file hashes against that independent receipt
pin, matched all four dry-run manifest hashes, rebuilt the source migration from persisted history,
replayed all three transition certificates, and validated all three qualifications against the final
manifest using the persisted evidence/base bytes. It confirmed 7,200/1,800/901 roles, ten hashed
source files and 13 active issues. This is a persisted S3 replay, not an S4 cohort resolver test.

Final manifest content SHA-256:
`12ba8fe0a7013db13d06b0e0ea87ea949f167896bee9d2712b2d1d0f18d83220`.
The `inputs.json` receipt pins link prior evidence; `history.json` retains the predecessor records;
`manifests.json`, `transitions.json`, `qualifications.json`, `evidence.json` and `membership.json`
retain the new chain and exact dependencies for replay. The production reader remains disabled.
No files were committed or pushed, and this local package is not an independent backup.
