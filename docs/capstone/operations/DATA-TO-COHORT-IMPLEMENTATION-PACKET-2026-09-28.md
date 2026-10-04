# Data-to-cohort implementation packet

**Date:** September 28, 2026. **Owner/reviewer:** Codex; **project owner:** Quinton Evans.
**Status:** Quinton requested starting the four steps. S1 pure synthetic implementation is complete;
S2 retained-control preparation and live metadata inventory are complete; the bounded content job is
implemented and [completed for ten files](../data/LOCALIZER-CONTENT-VERIFICATION-RESULTS-2026-09-28.md).
All matched retained hashes. S3 positive qualification and S4 publication remain pending.
See [the implementation handback](../data/SYNTHETIC-QUALIFICATION-IMPLEMENTATION-2026-09-28.md).
The original proposed file/layout details below are superseded where the handback records refinements.
**Outcome:** preserve the original protected membership while producing a positively qualified,
immutable pancreas-localizer smoke cohort that a consumer can resolve without bypassing holds.
This packet covers Phase A/B and the record-resolution portion of Phase C in the
[training plan](TRAINING-READINESS-IMPLEMENTATION-PLAN-2026-09-28.md).
It does not implement preprocessing, model training, workflow scheduling or the full cascade.

## 1. Settled rules and exact scope

D-266 locks original membership and purpose-specific permission. D-267 prohibits difficulty/model
performance as eligibility filters. D-268 approves broad verification plus detailed consumed-case
qualification, expanding through new frozen cohorts. Do not request approval of those principles again.

Keep all 9,901 original PanTS identities protected: 7,200 train, 1,800 validation and 901 test.
Use the approved study-as-subject fallback with `unverified_unique` assurance. Source partition and
PROWL role remain distinct: publisher training includes both PROWL train and validation.
No publisher-test image extraction, header/voxel inspection or model selection is in this packet.
No PANORAMA mixing, every-organ qualification, old-drive recovery, dependency installation or raw edits.

Source-wide accounting is not a claim of source-wide payload verification. Exact byte verification
of a consumed file is not proof of its label quality. Qualification requires both applicable integrity
and interpretation evidence. Difficult but interpretable cases remain candidates.

## 2. Evidence reuse and remaining checks

This table specifies required outputs, not completed gate claims. Revalidate evidence pins at use;
never copy historical success flags into a new source snapshot without checking their bindings.

| Check / coverage | Existing evidence to reuse | Required new evidence / pass rule |
|---|---|---|
| C01 — all original split controls | `src/data/protected_identity.py:BASE_INPUTS`, CURRENT-INVENTORY; accepted list hashes | Exact-byte hashes/counts, no duplicate members, disjoint union = all 9,901 expected IDs. Original roles preserved; legacy contaminated child lists rejected. Emit migration/overlap report. |
| C02 — all protected identities | `pants_identity`, metadata adapter and role guards | One canonical identity per source ID, explicit fallback, no cross-role subject/protection group; source partition agrees. A missing identity or conflicting role fails accounting. |
| C03 — declared acquired source inventory | Acquisition/extraction receipts; structural inventory observations | Per-file inventory joined to expected source members, explicit missing/unexpected/duplicate paths and unextracted status. No inferred ready state from aggregate counts or compressed size. Scope derives from release/receipts before case selection. |
| C04 — source integrity assurance | Retained label archive full-stream scan/hash; selected archive-to-extracted comparisons; pinned release linkage | Verify controlling receipt/manifest hashes and state what they cover. Current extracted payload verification remains separate. List assurance gaps explicitly. Source-wide checks required by the approved contract cannot be replaced by the candidate sample. |
| C05 — duplicate controls | Canonical ID/role checks; approved issue rules | Reject duplicate IDs/paths/records; compare available exact image hashes across recorded roles and ingest known duplicate findings. Cross-role matches/probable unresolved findings block affected use. Report hash coverage, not “no duplicates” outside that coverage. |
| C06 — each candidate CT and pancreas mask | `source_evidence`, bounded voxel-audit/evidence adapters | Independently pinned bytes, finite readable arrays, physical geometry, verified CT/target relationship, decoding and coverage evidence. Full selected-file validation; stop on mutation or unknown units. |
| C07 — each consumed target's permitted purpose | Annotation v2, D-259 lineage checks, source-use review, existing purpose issues | Affirmative pancreas-localizer qualification and exact dependencies. Every applicable source/subject/study/annotation issue accounted for; no unsupported dismissal. Provenance remains source-asserted unless independent verification exists. |
| C08 — executable cohort and consumer | Cohort protocol/schema, identity helpers; no production publisher/resolver | Exact approved train ancestry, selected qualification pins, deterministic selection, repeat hash, profile, completion verification and rejection before array loading. |

**Duplicate boundary:** Plan 02 explicitly defers expensive image fingerprints to Plan 03. Do not add
voxel fingerprinting of the full dataset to this packet. Exact-byte matches detect identical bytes,
not recompressed equivalents or biological identity. If a known unresolved duplicate implicates a
candidate, exclude it from execution pending adjudication, retaining original membership. A missing
required overlap check is a blocker, not equivalent to no match. PANORAMA overlap remains under G2.

**Source completeness boundary:** C01/C02 close identity accounting only. C03/C04 need a declared
expected-file universe and assurance policy. The current contracts must not label the full dataset
payload-ready merely because those identities are present. Section 3 specifies the proposed revised
representation; any change to G1's accepted assurance threshold remains a separate explicit amendment.

## 3. Proposed contracts and compatibility

These are concrete design proposals for review, not files created by this planning pass. Preserve
all accepted schema files and v1/v2 replay behavior. Introduce explicitly selected new schema versions;
never edit schema_version inside stored artifacts or reinterpret old `complete` values.

| Artifact | Proposed version / file | Required meaning and fields |
|---|---|---|
| Source snapshot | 2.0.0, `source-snapshot-v2.schema.json` | Keep source/version/license/root identity; replace ambiguous global readiness with `scope`, `accounting_status`, `integrity_coverage`. Scope pins expected identity/file inventories, source partition, included artifact kinds and exclusions. Accounting is complete/partial/quarantined against that scope. Integrity states method, expected/checked counts/bytes, inventory/evidence hashes and unverified members. Neither field alone grants use. |
| Manifest | 3.0.0, `manifest-v3.schema.json` | `accounting_status` describes complete reconciliation, not all-member eligibility; preserve all issues/held members. Pin source v2, exact record-schema versions, complete inventory references, qualification-policy reference and qualification collection. Consumer permission is assessed per requested member/purpose. |
| Cohort control | 2.0.0, `cohort-v2.schema.json` | Required `capability` = protection_only/executable. Preserve family/roles/parents, require ID+content-hash references for parents/manifests, membership/profile and definition. Protection-only may retain held members; executable additionally pins purpose, qualification policy and per-member qualification. |
| Cohort member | 2.0.0, `cohort-member-v2.schema.json` | Preserve study/subject/role/protection group. Protection-only uses no target/qualification claim; executable binds target, exact annotation reference and qualification reference. Unknown target status never defaults negative. |
| Purpose qualification | 1.0.0, `purpose-qualification.schema.json` | New immutable assessment with content-bound ID; study/subject/snapshot/annotation hashes, purpose, policy/config/component identity, evidence references, complete applicable-issue inventory, assessed checks and outcome qualified/held/excluded. No qualification from absence of issues. |

Qualification records are needed because the current denial helper deliberately never returns an
allow result. Keep that helper unchanged in the first implementation slice. Its supported denials
remain enforceable. Do not duplicate byte/geometry observations inside several competing authorities:
qualification references verified assessment artifacts and records the resulting purpose judgment.

Every reference must include a full content hash and a safe artifact-relative location resolved from
an independently trusted registry. Hashes supplied by an untrusted candidate are not their own trust
anchor. Require exact dependency inventories; an omitted subject/snapshot issue cannot disappear
because a caller supplied only annotation issues. Unrecognized issue applicability fails closed.

**Original-source records:** keep annotation v2 and original diagnostic records intact. Where a case
qualifies, emit new derived assessment/annotation records under the existing versioning rules with
explicit parent evidence and approved mapping/use. Do not set an old record's allowed uses in place.
Subject/study holds remain effective; a qualification wrapper cannot override them silently.

**Resolution scope:** the first slice does not need a generic issue-resolution framework. It must
reject unresolved relevant holds and accept only independently reviewed, pinned new evidence chains
supported by a narrowly specified rule. Until such a rule is implemented, those cases remain held.
If no candidate can qualify without resolving a common provenance/geometry issue, specify that one
resolution path before publication; do not widen a generic “ignore issue” option.

## 4. Data flow and consumer order

1. Load independently pinned source controls and approved original split bytes.
2. Build complete protected identity accounting, including unavailable/held members.
3. Join declared file inventory and evidence, retaining every discrepancy and its scope.
4. Validate selected targets and publish purpose assessments only through supported evidence rules.
5. Select from qualified train-role candidates by a frozen deterministic rule, never model score.
6. Build executable descendant with exact parent, manifest, annotation and qualification pins.
7. A consumer resolves by cohort ID; verify schema, immutable registry binding, completion inventory,
   hashes, ancestry/roles, qualification dependencies, current holds and source roots before arrays.
8. Return a validated input description carrying lineage, not an anonymous list of filenames.

No consumer bypass accepts raw legacy ID files. Do not infer permissions from a frozen state or a
protection-only parent's role. A changed input or qualification creates a new version; a frozen
consumer fails instead of substituting a different case. Previously produced evidence is retained;
a newly discovered hold blocks new execution and marks affected descendants for review.

## 5. Ordered implementation slices and permitted files

Paths here are proposed and currently absent unless identified as existing. Synthetic fixtures only
in the first slice. Each slice needs its own handback; passing it does not launch the next real job.

### S1 — pure contract and protected-membership implementation

**Purpose:** make D-266–D-268 executable on invented records before any drive work.

Proposed new files: the five schemas in section 3;
`src/data/source_inventory_records.py`, `src/data/manifest_records_v3.py`,
`src/data/purpose_qualification.py`, `src/data/cohort_records.py`,
`tests/test_source_inventory_records.py`, `tests/test_manifest_v3.py`,
`tests/test_purpose_qualification.py`, `tests/test_cohort_records.py` and synthetic fixtures
under `tests/fixtures/contracts/`. Reuse existing canonicalization/schema/identity helpers.
Edit shared contract index/validation/protocol documentation only to describe the reviewed new versions.

Pure builders accept records plus independent pins and return canonical bytes/reports; no disk
publication, real root resolver, source activation, network access, live inventory or workflow locks.
Validation dispatch must name exact versions, not auto-upgrade unknown records. Keep old tests intact.

**Exit:** a synthetic family preserves a held member, refuses direct protection-parent consumption,
builds a qualified executable child, rejects held/wrong-role/altered dependencies and reproduces hashes.
Also show a difficult qualified fixture stays eligible when only its difficulty flags/model scores
change. Unknown issues and self-attested qualification must fail. No claim of real G1 closure.

### S2 — retained evidence and exact source-job specification

Use repo-local metadata/control receipts first. Recheck actual input hashes and record the expected
inventory, required/optional reads and evidence gaps. Proposed artifact:
`docs/capstone/data/SOURCE-VERIFICATION-SCOPE-2026-09-28.json` plus a concise review note, created
only when actual inputs are known. Do not fill it with invented mount status or archive lists.

The job plan must bind explicit registered roots, source/archive identities, relative-file allowlist,
expected counts, read methods, byte/time/memory/output caps, stop rules and output/evidence locations.
Separate cheap enumeration/control checks from content reads. Estimate read time from actual declared
bytes and a bounded measured throughput sample, with at least 25% contingency. If source-wide
verification exceeds this week's capacity, expose that fact before launching rather than silently
reducing assurance. No exact numeric job budget is claimed here without those measurements.

**Exit:** concrete reviewable read plan and assurance matrix; outstanding source-use or integrity
requirements named. Reuse the existing inventory tool only for structural observations; it does not
produce authoritative per-file records and must not be relabeled as doing so.

### S3 — inventory and bounded target qualification

After S2's scope is reviewed, implement a narrowly scoped per-file inventory adapter and candidate
assessment runner using existing safe path/header/hash/voxel helpers. Proposed paths:
`scripts/diagnostics/qualify_localizer_inputs.py`, `tests/test_localizer_input_qualification.py`.
It must support synthetic inputs and a dry-run file/read budget before real use.

Candidate selection records its original train parent, candidate pool and deterministic order before
reading outcomes. Prefer reusing sufficient retained evidence but disclose its nonrepresentative
selection. No new candidate is chosen by model performance, apparent visual ease or small file size.
Do not silently extend the candidate budget if holds leave too few usable cases.

Use the existing approved decoding policy. Reuse reviewed geometry checks where applicable, with
exact tolerances/version pinned and boundary tests; do not loosen tolerances to admit a case. Record
whether geometry is directly established or follows an already approved evidence-backed rule.
No new inference of physical units. No requirement that difficult masks look ideal.

**Exit:** source reconciliation evidence plus positive/held/excluded per-candidate outcomes with
supported provenance/use decisions. Preserve every previous package. No eligible count promised.

### S4 — publication, cohort resolution and model-input handoff

Proposed `src/data/cohort_registry.py`, `tests/test_cohort_registry.py`, and a capstone input adapter
with tests. Use registered roots and approved shared Plan 04/10 publication/ownership controls;
writing a second unofficial publisher is out of scope. Plan 04 coding authorization remains separate.

Publication includes cohort control, members, profile, ancestor/dependency report, selection report
and content-pinned completion evidence. Repeat the build and resolve it by ID in a fresh process.
Registry rejects reused ID with different content, partial artifacts, unsafe paths and concurrent
publication. Test corrupt/missing member and revoked/held target before returning any array input.

**Exit:** exact qualified cohort passes resolver and negative tests; G1 review cites C01–C08 evidence
and assurance limits. Then hand off to loader/preprocessing Phase C. No model run is launched here.

## 6. Verification and handback

S1 focused native command after those proposed files exist:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/test_source_inventory_records.py tests/test_manifest_v3.py tests/test_purpose_qualification.py tests/test_cohort_records.py -q -p no:cacheprovider
```

After integration, run the existing full suite:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Required fault cases: altered split, omitted identity, wrong grandparent role, contradictory protection
group, incomplete inventory mislabeled complete, source-wide hash assurance inflated from a sample,
held member hidden by omission, qualified record with wrong target/hash/purpose, forged trusted pins,
unapproved mapping, unknown geometry, model-score filtering, silent shortage repair, unknown schema,
changed frozen member, and publication incomplete or content-conflicting. Test native filesystem
publication only in S4 under its operational prerequisites; real data never becomes a corruption fixture.

Handback includes changed paths, schema compatibility table, focused/full test commands/results,
repeat-build hashes, old-package replay evidence, planted-error results, unresolved requirements and
precisely what the next slice may do. No arbitrary coverage percentage or test-count target.

## 7. What remains to review, and what does not

The preservation, difficulty and staging policies are settled. The substantive technical review is
section 3's new schema semantics and the C03/C04 source assurance scope. The proposed source-v2 /
manifest-v3 / cohort-v2 split deliberately preserves all old meanings. Review this before coding;
selecting these versions does not approve unmeasured source jobs.

Source-use qualification remains evidence work, not a request for Quinton to make a legal finding.
Publisher clarification stays independent; do not infer unrestricted release permission from local
research planning. Current held cases remain held. No perfect-data requirement is introduced.

Recommended next action: review the concrete contract structure, then start S1 when implementation
is requested. While S1 is being developed, S2 can be prepared from retained controls; that does not
require new agents or permit concurrent source writers. Avoid another broad planning document unless
a specific unresolved requirement changes this packet.


S2 metadata handback: [live preflight](../data/LOCALIZER-METADATA-PREFLIGHT-2026-09-28.md).
All 18,000 expected CT/pancreas files observed; no payload reads or qualification. The actual inventory
is now available for the next content-read/candidate scope. No need to repeat metadata enumeration
unless source changes or a verification requirement justify it.

## Qualification transition follow-up

The [transition checker and retained-input review](../data/LOCALIZER-QUALIFICATION-TRANSITION-2026-09-28.md)
are implemented. S3 is in progress: exact generic holds and D-259 mapping evidence are accounted for;
source/use and visual alignment evidence, v3 migration and real qualification remain pending.
The checker is not yet wired into production publication or consumers. S4 remains unexecuted.


S3 subsequent handback: [real qualification records](../data/LOCALIZER-QUALIFICATION-RECORDS-2026-09-28.md).
Cases 3/26/31 now have pinned positive qualifications and checked successor history; 13 active
holds remain. The source accounting v3 context preserves all original roles. S4 remains unexecuted
and requires the shared publication/ownership controls specified above; no alternate publisher was
introduced. Native suite: 948 passes, two existing upstream warnings.


S4 subsequent handback: [first production cohort](../data/LOCALIZER-COHORT-PUBLICATION-2026-09-28.md).
D-269 authorized and implemented the required shared publication slice. Cases 3/26 are frozen under
`cohort:pants-localizer-smoke-0001:v1`; fresh-process resolution checks saved ancestry/qualifications
before returning descriptors. Full native suite: 985 passes, two existing warnings. Phase C raw-input
binding and preprocessing are next; no training or global source activation occurred.
