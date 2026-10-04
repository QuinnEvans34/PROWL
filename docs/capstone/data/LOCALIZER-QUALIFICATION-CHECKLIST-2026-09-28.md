# First localizer: qualification checklist and source-verification scope

**Date:** September 28, 2026. **Owner:** Quinton Evans; prepared by Codex.
**Status:** D-266/D-267 principles and D-268 staged qualification approved; exact implementation/read scope remains to specify.
No case is promoted by this document. No new raw-source inspection was performed to write it.

## How to use this checklist

Qualification establishes that a requested use is permitted and the data can be interpreted correctly.
It does not certify a perfect annotation or an easy scan. Each future case assessment records evidence
IDs/hashes, requested purpose, outcome, unresolved issues and reason. Missing required evidence yields
a hold for that use, never an assumed pass. An assessment is not itself a training cohort.

The tables distinguish:

- **Qualification requirements:** identity, permitted use and trustworthy interpretation.
- **Smoke selection conditions:** the particular learning question, not universal eligibility.
- **Descriptive characteristics:** difficulty/variation to retain and report, not automatic exclusions.

Model predictions, loss and Dice cannot determine eligibility. If model errors reveal a possible
annotation defect, investigate independently, preserve the original evidence and apply a documented
rule consistently; do not retroactively prune the evaluation set to improve scores.

## Qualification requirements

| Requirement | Evidence we already have | Evidence still needed | Exact pass/fail rule |
|---|---|---|---|
| Original membership and protected role | Accepted 7,200/1,800/901 controls reproduced; protected-identity helpers | Complete frozen protection records, ancestry and consumer proof | Selected case must resolve to original train ancestry with matching pins and no conflicting protected role. Missing/changed/wrong-role record fails; original membership remains preserved. |
| Subject and duplicate protection | Approved study-as-subject fallback; existing identity rules | Applied grouping/version, known duplicate adjudications and required overlap checks for declared source scope | Fallback must be explicit, not claimed biological uniqueness. Known/probable unresolved cross-role duplicate blocks use; missing required checks block gate closure. No different-family bypass. |
| Source identity and file integrity | Pinned acquisition/extraction receipts and selected-file evidence | Scope reconciliation plus each selected CT/mask's verified bytes bound to source records | Each consumed file must match independently reviewed identity/hash and inventory linkage. Missing, altered or ambiguous source fails. Archive counts alone do not pass this row. |
| Annotation provenance and permitted purpose | Source-use review and original-source annotation contracts; no current eligible package | Release-applicable source-use/provenance evidence and explicit pancreas-localizer target permission | Annotation must have affirmative supported allowed use for the requested purpose. Missing permission or unresolved applicable source-use hold fails. Do not infer manual annotation or project verification from publisher provenance. |
| Defined target and decoding | Approved D-259 strict binary rule and tested lineage validation | Mapping explicitly bound to selected annotation; complete mask-value check under that policy | After NIfTI scaling, every value must be finite and within absolute 1e-6 of 0/1, relative tolerance zero. Anything else fails this mapping. Preserve original bytes. Empty foreground is handled separately below. |
| Physical geometry | Header readers and bounded audits; cases 2/266 remain unit-held | Verified units, usable/invertible affine and CT/mask grid relation for selected files | Physical units must be established; transform must be well-defined; grids must match the reviewed geometry contract or an explicitly verified mapping. Unknown units/misalignment fail affected use. Numerical affine tolerances must be specified/tested before this row can be executed. |
| Readable, finite CT and interpretable supervision | Bounded readers/audits; diagnostic evidence only | Full selected-array checks and recorded overlay/coverage assessment | Unreadable/nonfinite arrays or evidence that supervision does not correspond to the input fail the current pipeline. Noise/artifacts alone do not fail. Any interpretation-based hold needs a concrete defect and affected purpose, not “looks difficult.” |
| Holds and positive qualification | Rejection-only purpose helper; current package has ten quarantined annotations/22 holds | Positive qualification records and reviewed append-only resolution rules | No applicable unresolved hold, plus all required affirmative evidence. Passing the denial checker alone fails to establish eligibility. Unsupported/unclassified issues block until reviewed. |
| Frozen executable cohort | Cohort contracts and migration rules; no real frozen cohort | D-266 contract implementation, exact membership/profile/ancestor hashes, repeat build and completion marker | Every frozen member must pass purpose qualification and protected ancestry. Identical build inputs reproduce membership. Changed/held member causes consumer failure; no silent removal/refill. Protection-only parent cannot directly supply training inputs. |

These are intended rules, not claims that validators already implement them. Geometry tolerances,
source-scope assurance and annotation-uncertainty treatment require concrete specifications in the
implementation packet; they must not be guessed at runtime.

## Selection conditions for the first smoke

| Requirement | Evidence we already have | Evidence still needed | Exact pass/fail rule |
|---|---|---|---|
| Pancreas-present learning fixture | Selected diagnostic masks contain foreground; case 78 has pelvic/hip coverage | Qualified case's decoded foreground and coverage evidence | The initial pancreas-present smoke selects verified nonempty pancreas targets with relevant coverage. Otherwise not selected for this smoke; this does not declare the source corrupt or universally unusable. No empty lesion mask establishes disease absence. |
| Tiny reproducible selection | Proposed 1–4-case initial scope; deterministic selection design | Final candidate pool, fixed count, seed/tie-break and selection record | Freeze exact count/rule before the run. Fail on shortage instead of silently changing the request. No ranking cases by model performance or visual ease. |
| Limits of inference | Tiny-set fitting is the proposed learning check | Pre-run measurement rules and explicit scope in report | Report execution, alignment, recovery and learning separately. No generalization claim or claim of representative difficulty coverage from 1–4 cases. |

Verified empty-target or limited-coverage cases may support other explicitly defined purposes later.
Their label meaning, coverage and sampling/evaluation treatment must be established first. D-267 does
not override case 78's current pancreas-present exclusion or cases 2/266's unit holds.

## Characteristics to retain and describe

| Requirement | Evidence we already have | Evidence still needed | Exact pass/fail rule |
|---|---|---|---|
| Preserve difficulty | Quinton's D-267 approval | Available descriptors for contrast, noise/artifacts, anatomy, target size, scanner/protocol and verified spacing | Difficulty is not a qualification failure. Record unknown descriptors as unknown rather than inventing values or excluding solely for missing descriptive metadata. |
| Represent annotation uncertainty honestly | Provenance contracts distinguish source assertions from project verification | Documented uncertainty categories and purpose-specific treatment where needed | Uncertainty alone is not automatic exclusion or permission. Retain documented uncertainty when target meaning remains usable; unresolved target meaning requires a specific hold. No “perfect contour” requirement. |
| Assess selection bias as cohorts grow | With/without qualified unusual cases and fixed ordinary/unusual evaluation groups already agreed | Prespecified categories, cohort profiles, counts and matched comparison plan | Report candidate/selected/held distributions and reasons. No silent easy-case filtering or post-result redefinition of groups. Keep all compared methods on the same role-valid evaluation groups. |

## Evidence references

- [Current checkpoint](../operations/CURRENT-CHECKPOINT.md): latest status and test evidence.
- [Current inventory](CURRENT-INVENTORY.md) and [cohort protocol](COHORT-PROTOCOL.md): base controls/protection rules.
- [Source-use review](PANTS-SOURCE-USE-REVIEW-2026-09-28.md): release/provenance questions.
- [Binary approval](BINARY-DECODING-APPROVAL-2026-09-28.md) and [lineage verification](BINARY-POLICY-LINEAGE-2026-09-28.md).
- [Purpose package](PURPOSE-DISPOSITION-PACKAGE-2026-09-28.md): current holds, not qualification.
- [Membership/eligibility proposal](PROTECTED-MEMBERSHIP-AND-ELIGIBILITY-PROPOSAL-2026-09-28.md): representation remains to implement.

## Approved staging direction — D-268

Quinton approved staged qualification: broad source and split verification, detailed qualification
of every consumed case, then expansion through new frozen cohorts. Difficult cases remain candidates
throughout. The table operationalizes that direction; exact inventory/read/check scope still needs
specification against G1 and the existing complete-source requirements.

| Scope | Proposed work before consuming real training cases | Boundary |
|---|---|---|
| Entire protected family | Reconcile all 9,901 original identities, original split hashes/counts, source/control linkage, available/missing/unextracted status and required identity/overlap evidence | Protection/accounting only; no publisher-test image inspection and no claim all payload bytes or annotations are qualified |
| Declared acquired PanTS source scope | Reconcile expected inventory with retained receipts and actual records; identify required integrity coverage, unresolved discrepancies and duplicate-check assurance | Define scope from pinned release controls before choosing easy-to-verify cases. Full-source requirements remain binding; inventory counts are not content verification |
| Candidate/selected CT and pancreas masks | Verify exact bytes, geometry, target semantics, purpose permissions and applicable holds; expand bounded candidates only by recorded rule | Every file consumed by the run must pass. No default audit of unrelated organ labels or all tasks |
| Subsequent larger cohorts | Extend per-case qualification, report coverage/selection bias and freeze new executable subsets | Never claim uninspected cases are qualified; difficult cases remain candidates |

**Approved strategy:** staged qualification with broad protection/source accounting and detailed
checks on consumed files, while explicitly completing any wider integrity/duplicate checks that G1
requires. Do not require every annotation for every future task to become eligible before this smoke.
Do not treat staged qualification as permission to skip required source-integrity checks.

Before approving an exact execution scope, the packet must list the expected source universe,
existing receipts, required versus optional reads, integrity/duplicate assurance, cost estimate and
pass/fail conditions. If this changes the current complete-manifest/source contract, show the exact
amendment for review. This document does not resolve that amendment or authorize an on-drive job.


## Next planning deliverable

Prepare the concrete verification/implementation packet from the retained source controls: name each
required check, input evidence, coverage, expected output, remaining read cost and acceptance rule.
Separate source-wide requirements from per-consumed-case requirements. Show any necessary contract
amendment explicitly. Choose routine implementation details within D-266–D-268 rather than asking
Quinton to reapprove the same strategy. Bring back substantive evidence/coverage tradeoffs before
execution; planning is still the active scope.


Implementation handoff: [data-to-cohort packet](../operations/DATA-TO-COHORT-IMPLEMENTATION-PACKET-2026-09-28.md)
now names the checks, proposed contracts, implementation slices and acceptance commands. Exact live
source-job inputs/budgets remain S2's deliverable; no real eligibility is claimed by the packet.
