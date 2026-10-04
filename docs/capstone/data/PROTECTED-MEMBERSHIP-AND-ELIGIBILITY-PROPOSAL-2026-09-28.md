# Proposed boundary between protected membership and executable eligibility

**Status:** Governing policies D-266–D-268 approved; implementation/schema details remain draft. No eligibility promotion.
**Owner:** Quinton Evans; Codex prepares/reviews implementation. **Date:** September 28, 2026.
**Needed before:** production cohort publication in Phase B of the
[training plan](../operations/TRAINING-READINESS-IMPLEMENTATION-PLAN-2026-09-28.md).

## Locked policy — D-266

Quinton explicitly reaffirmed and locked the following on September 28:

> Keep original membership permanent, make permission purpose-specific, and allow training only
> through a frozen, positively qualified subset.

This records the already agreed principle, not a new request to approve it. See
[DECISIONS.md](../DECISIONS.md). The field names, schema versions, source-completeness scope and
implementation mechanics below remain proposals to make that approved policy enforceable.

## Qualification is not a difficulty filter — D-267

Quinton approved retaining realistic difficulty and treating it separately from qualification.
Poor model performance is never an eligibility criterion. Low contrast, artifacts, unusual anatomy,
small targets, verified protocol variation and documented annotation uncertainty are recorded, not
excluded merely because they are difficult. A specific defect can still block a use when it prevents
valid interpretation or supervision; its evidence and affected purpose must be stated explicitly.
Nonempty pancreas is a selection condition for the first pancreas-present smoke, not a universal
eligibility rule. See the [four-column checklist](LOCALIZER-QUALIFICATION-CHECKLIST-2026-09-28.md).

## Problem demonstrated by current contracts

Quinton approved preserving all originals/base membership while qualifying actual uses separately.
The existing [cohort protocol](COHORT-PROTOCOL.md) requires complete manifests and frozen parents,
and rejects quarantined members from training-purpose cohorts. Its initial migration must reproduce
all 7,200/1,800/901 members. Some of those members legitimately remain held or excluded for a purpose.

`src/data/manifest_records_v2.py` marks the package quarantined if any unresolved blocking issue or
quarantined subject/annotation exists. The current cohort schema does not distinguish a protected
membership record from an executable dataset. The current source schema's completeness and integrity
assurance fields do not fully specify inventory scope. The tested purpose helper rejects uses; it
neither grants qualification nor currently accepts issue-resolution/supersession chains.

Consequently, neither deleting held members from the original split nor declaring the diagnostic
package complete is acceptable. Passing the denial checker is necessary but insufficient for use.
This is an actual contract gap, not a request for another anomaly investigation.

## Recommended design for discussion

Use the existing record families with an explicit versioned distinction between complete accounting,
protected membership and purpose-qualified execution. Avoid a separate database or generic policy
framework. No approved schema is edited by this proposal.

### 1. Complete accounting retains unresolved cases

A new manifest version should expose independent concepts:

- **Inventory coverage:** complete only against an explicitly pinned expected inventory and scope;
  every expected member is accounted for, with missing/unavailable/unextracted states visible.
- **Integrity assurance:** which bytes were verified by which method and to what coverage; selected
  file hashes never become full-source verification by implication.
- **Qualification:** per subject/study/annotation and requested purpose, with evidence, mapping,
  source use and unresolved relevant issue references.

An inventory can be completely accounted for while some payloads are unavailable. That fact alone
must never make a source eligible for execution. Preserve the current v2 semantics and artifacts;
new consumers support the new version explicitly and reject unsupported versions. Do not globally
change `status='complete'` to mean something weaker in existing readers.

### 2. Protection-only parents preserve original membership

Proposed new cohort capability field: `protection_only` or `executable`, required in the new schema
version. This is a proposed interface, not a currently valid JSON field. The protection-only migration
records preserve the exact original counts and members, their source/control hashes, roles,
subject grouping and duplicate-group references. Unavailable or held targets remain visible there.

Protection-only records cannot yield model inputs. A training consumer must explicitly require an
executable cohort; it must never interpret frozen membership as permission to train. Parent role
inheritance and full ancestry checks apply to both capabilities. Publisher-test membership can be
protected using existing controls without opening its image payloads.

### 3. Executable children require positive qualification

For every selected member, the consumer checks all of the following together:

1. Presence in the frozen protected train parent, with no conflicting role anywhere in the relevant
   family/protection graph; approved grouping fallback recorded honestly.
2. Exact independently pinned study, CT, annotation and mapping identities.
3. Positive source/target-use qualification for the requested purpose, supported by reviewed evidence.
4. Physical units, affine/grid compatibility, finite values and target semantics established.
5. No unresolved applicable source, identity, geometry, annotation or purpose issue.
6. Required source completeness/integrity checks and G1 evidence accepted for the declared scope.

Filtering is performed before deterministic selection. Once exact members are frozen, the consumer
fails on a changed/held member; it cannot quietly drop or replace that member. Allowed use changes
produce a new artifact and descendant cohort version. A lesion-only issue may be irrelevant to a
pancreas-only use only under an explicit reviewed dependency rule; unclassified issues block.

### 4. Resolve issues append-only with evidence

Keep the current rejection helper's behavior until a separately reviewed extension exists. Proposed
resolution evidence binds the original issue ID/hash, affected entity/version, requested purpose,
new evidence hashes, qualifying policy/version and reviewing decision. A resolution creates a new
artifact; the original issue/package remains unchanged. Missing, circular, conflicting, stale or
wrong-purpose resolutions fail. Independent pins must prevent callers manufacturing their own trust.

Case 78's localizer exclusion and cases 2/266's unit holds remain effective. This proposal does not
resolve any of them. No case-2 pilot-format adapter is required to qualify other independent cases.

## Source completeness: the decision that must not remain implicit

The existing G1/protocol requirement remains binding until explicitly amended. Before implementation,
produce a short inventory-scope table with expected member universe, available receipts, missing
assurance, required checks and estimated read cost. Include all original protection identities and
account for publisher-test payloads without adding test-image reads.

**D-268 approved staging direction:** separate full protected-identity accounting from the fully reconciled
payload scope needed by the PanTS training source and exact executable descendants. Define that
scope from pinned release/control evidence before qualification, not by selecting whichever files
happen to pass. Any narrower qualification claim must be named explicitly and reviewed against G1.
This proposal does not establish that selected-file checks satisfy today's full-source requirement.

If the approved interpretation requires broader reconciliation before a tiny run, perform and budget
that reconciliation, or discuss an explicit contract/gate amendment. Until then, real training stays
blocked. A one-case manifest is not a substitute for the protection and source checks.

## Alternatives and tradeoffs

| Option | Benefit | Problem / disposition |
|---|---|---|
| Qualify every annotation in the full base first | Fits a globally ready package model | Couples first training to unrelated labels/cases; potentially substantial work; not recommended as default |
| Remove held members or mark them all resolved | Appears quick | Violates preserved membership/evidence and grants unsupported use; reject |
| Keep old contracts; introduce separate protection registry | Leaves existing artifacts untouched | Adds another identity authority and join; viable only if simpler after concrete interface review |
| Explicit versioned protection-only parents and qualified children | Preserves membership with enforceable usable subsets | Requires coordinated manifest/cohort/consumer changes and exact completeness policy; recommended |

## Proposed implementation packet boundaries

- Codex owns shared contracts, protocol amendments and data implementation. Preserve Claude's lane.
- Review exact manifest/source/cohort/member/issue schema changes, examples and migration behavior
  together before coding. Choose versions under the existing versioning policy; do not reuse an
  accepted schema version for changed semantics.
- Preserve original v1/v2 validators and historical packages; provide explicit new entry points or
  version dispatch. No automatic migration of real packages and no source rewriting.
- Implement pure synthetic builders/validators first, then bounded real qualification, then atomic
  publication under approved shared Plan 04/10 controls. No free-form ID-list training bypass.
- Evidence outputs: scope reconciliation table, contract diff, original-membership comparison,
  qualification report, issue graph, overlap/ancestry report, repeat-build hashes and consumer tests.

## Acceptance cases required before production publication

A frozen parent with a held member must preserve that member while refusing direct consumption.
A qualified child excluding it must be possible only when completeness/qualification prerequisites
are satisfied. A held child, cross-role ancestor, ambiguous duplicate, unsupported issue,
self-authored unpinned resolution, stale evidence or changed target must fail. A no-denial result
without positive allowed-use evidence must fail. Unextracted test payloads must not become usable
through protection registration. Identical inputs must reproduce membership hashes; all old package
hashes must remain unchanged. No implicit size reduction or repair is permitted.

## Next planning step

D-266–D-268 settle preservation, difficulty handling and staged qualification. The checklist is drafted. Next specify exact source-inventory/check scope,
then review the concrete schema/consumer packet. No further approval of the preservation-versus-use
principle is needed. Current fail-closed contracts and holds remain effective until their approved
replacement is implemented and verified; record any actual completeness/gate amendment separately.
