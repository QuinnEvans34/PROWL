# Protected cohort protocol

**Status:** Approved Plan 02 baseline  
**Version:** 1.0

September 28 implementation: [first frozen localizer cohort](LOCALIZER-COHORT-PUBLICATION-2026-09-28.md)
is published and resolved under D-269. Cohort-v2 protection parents preserve all original members;
only the 3/26 executable child grants the reviewed target purpose. Complete publication is asserted
by the independently pinned artifact envelope, not the embedded in-memory state field. Future source
or membership changes require new frozen identities/versions; never rewrite this bundle.

## Purpose

This protocol prevents evaluation leakage, wrong-parent sampling, irreproducible membership, and
silent cohort repair. It applies to every training, validation, testing, development, smoke, and
analysis cohort in PROWL.

## 1. Build inputs

A cohort build must name:

- complete manifest ID(s) and hashes;
- cohort family ID;
- purpose and protected role;
- direct parent cohort ID(s) and hashes;
- subject grouping field/version;
- eligibility filters and allowed annotation uses;
- target and stratification fields plus exact requested counts/fractions;
- deterministic seed and tie-breaking method;
- shortage behavior, which defaults to fail;
- builder component version and relevant configuration hash.

An arbitrary filename or directory scan is not a valid parent.

## 2. Protection model

Within one cohort family:

- a subject may have only one of train, validation, or test;
- all studies for a subject inherit that role;
- a child inherits the parent role unless it is `none`;
- training/development/smoke purposes require train-role ancestry;
- validation/test parents create only evaluation or analysis children;
- publisher test studies can never receive train role;
- a declared cross-source duplicate is treated as the same protection group even when source IDs
  differ.

Creating a different cohort family does not authorize using protected evaluation data for training
in a comparison that reports against the original family.

## 3. Initial PanTS family

The migration build reproduces the accepted current membership rather than resampling:

| Cohort purpose | Publisher parent | Protected role | Expected studies |
|---|---|---|---:|
| Capstone PanTS train v1 | Publisher train pool | train | 7,200 |
| Capstone PanTS validation v1 | Publisher train pool | validation | 1,800 |
| Capstone PanTS test v1 | Publisher test pool | test | 901 |

The three legacy list hashes in `CURRENT-INVENTORY.md` are verified as migration inputs. New JSONL
member records then become canonical; the legacy files remain unchanged and noncanonical.

## 4. Subject-grouped deterministic selection

For any newly selected cohort:

1. Resolve and validate the frozen parent.
2. Filter only eligible records and allowed annotations.
3. Group all studies by canonical `subject_id` before randomization.
4. Derive group-level stratification values using a declared rule. For a named target, default to
   positive if any study is positive, negative only if every study is negative, otherwise unknown.
5. Sort groups by canonical ID before seeded selection.
6. Select groups, then include their permitted studies using a declared all-studies or one-study
   policy.
7. Assert exact requested counts/constraints; fail on shortage unless the definition explicitly
   names another policy.
8. Canonically sort members, calculate membership hash, validate, and publish atomically.

The seed is reproducibility metadata, not proof of membership; the membership hash is proof.

## 5. Ancestry check

Before publication, compute the full ancestor set and verify every requested study is present in an
allowed direct parent. A training-purpose cohort fails if any member:

- is absent from the frozen train parent;
- belongs to a validation/test role in the family;
- belongs to an excluded/quarantined subject, study, or annotation;
- is a declared/probable protected duplicate of an evaluation study;
- lacks an annotation allowed for the cohort purpose.

The failure report names every offending ID and rule. It never silently removes rows and continues.

## 6. Duplicate handling

- Repeated canonical study ID in a manifest: hard failure.
- Repeated study/member line in a cohort: hard failure.
- Multiple studies for one known subject: valid, but grouped.
- Exact same image bytes under two IDs: blocking duplicate candidate pending adjudication.
- Probable fingerprint match: quarantine from cross-role use pending adjudication.
- Same subject/study proven across sources: create a protection-group record; do not merge source
  identities or overwrite annotations.
- Uncertain similarity: retain evidence and either quarantine or keep source arms separate.

Plan 03 selects and validates the image-fingerprint method. Plan 02 freezes the statuses and consumer
behavior so the method can change without changing protection semantics.

## 7. Freeze protocol

1. Write draft records to a run-scoped temporary directory.
2. Validate record schemas, uniqueness, referential integrity, parentage, roles, and exact counts.
3. Produce cohort profile, ancestry report, and subject/study overlap matrix.
4. Canonically serialize and hash `members.jsonl` and `profile.json`.
5. Write `cohort.json` with immutable IDs/hashes.
6. Publish the directory and `COMPLETE.json` atomically.
7. A consumer verifies the completion record and hashes before reading members.

A changed member, annotation allowance, grouping rule, filter, or parent creates a new cohort version.

## 8. Consumer contract

Training and evaluation entry points accept a `cohort_id`, not a path. The resolver returns validated
study and annotation records only after checking:

- frozen state and completion marker;
- manifest/cohort schema support;
- file content hashes;
- expected protected role for the requested operation;
- no blocking unresolved issue;
- source roots currently resolve.

For a transition period, a compatibility adapter may emit the legacy dictionary shape expected by
MONAI. The adapter cannot omit canonical study/subject/cohort lineage from run manifests.

## 9. Required reports

- Membership profile by source, subject/study, target status, phase, and annotation provenance.
- Requested-versus-achieved selection table.
- Pairwise study/subject/protection-group overlap matrix.
- Complete parent/ancestor graph with hashes.
- Excluded/quarantined counts and rule codes.
- Repeat-build hash comparison.
- Migration comparison against accepted legacy base memberships.

## 10. Stop conditions

Do not freeze or consume a cohort when:

- source snapshot or manifest is incomplete;
- subject grouping is absent or ambiguous without a documented fallback;
- protected-role overlap is nonzero;
- an intended training child has any member outside its train parent;
- requested counts were silently reduced;
- blocking duplicate candidates cross roles;
- membership changes between identical repeat builds;
- a consumer can bypass the cohort registry with an arbitrary list.


## September 28 staged membership implementation (D-266–D-268)

Original membership is permanent; permissions are purpose-specific. Explicit cohort/member v2
contracts distinguish protection-only membership from qualified executable descendants. The current
implementation validates in-memory records only and does not satisfy the freeze/publication steps
above. Difficulty/model performance cannot determine qualification. Read
[S1 verification and compatibility](SYNTHETIC-QUALIFICATION-IMPLEMENTATION-2026-09-28.md)
before using the new entry points; no G1 or source-readiness waiver is implied.
