# Purpose-disposition diagnostic package

September 28, 2026. Quinton authorized the next reviewed publication step. **Completed:**
two purpose-specific denial issues are now attached in a new diagnostic manifest.
Five studies, ten quarantined annotations, twenty historical blocking issues plus two new
issues, zero eligibility. This is local evidence publication, not a remote release or cohort.

## Result and scope

| Study | Requested purpose | New rule | Result |
|---|---|---|---|
| PanTS_00000078 | pancreas_present_localizer | PANCREAS_PRESENT_TARGET_EXCLUDED | Rejected; purpose-specific exclusion |
| PanTS_00000266 | pancreas_present_localizer | PHYSICAL_UNITS_UNRESOLVED | Rejected; unresolved-unit hold |

Both also report existing blocking issues, pending record qualification and no training-target
permission. Case 266 additionally reports unresolved geometry. Attached-issue replay retains
these same reasons. The helper never returns an eligibility grant.

Case 78 is not globally excluded, declared corrupt or qualified as a disease-negative example.
Case 266 has no inferred unit conversion. Case 2 remains held outside this five-study package;
its older two-study package contains no annotation record to pass to the v2 helper.

The study/subject outputs are byte-identical to the prior five-study manifest. All twenty
historical issues remain unchanged; only the two selected pancreas annotation issue lists
receive one appended issue each. Annotation status, allowed uses, source-file hashes and
null mappings remain unchanged. Original packages and protected membership are preserved.

## Artifact and independent pins

Repository-relative package directory (ignored by Git):
`outputs/prowl/purpose-disposition-b515fd42-29b1-4203-9c62-424856fd523c`.

Manifest ID:
`manifest:purpose-denials-2026-09-28:523da1f0596c83ae140afd07cb6341f304090bb7c0cf0227ad5c0d12ba971212`.

Exact verification.json SHA-256:
`6ca6afc88ae7bdcf02458350908bf5a074c46d7c1f384f7f19d07666c759fd1e`.

New independently reviewed issue IDs and canonical SHA-256:

- `issue:6cbe5dda-6c67-4ac2-a393-02f2e3fdda69` (78):
  `26407fa042f0739fedab26a8069b54fc5fe839d47e3056db7576e6057868808f`.
- `issue:bb6e4911-ef12-4db6-abc6-2ce2fb3cfe2f` (266):
  `62022ae39b6a1dda99d47610b409de7908645908a375766d03aaef137ff3aa29`.

Reviewed input inventory SHA-256:
`51c70d3866ab23b355d4aed0f10245f538136fd2640e5195ed98aaba5eb40441`.
See [input review](PURPOSE-DISPOSITION-INPUT-REVIEW-2026-09-28.md).
The issue proposals were inspected separately and their pins were fixed before consumption.
New annotation-record pins follow an explicit comparison allowing only the appended issue ID;
they are retained in config.json with the original record pins and precise change description.

## Retained package contents and verification

The package occupies 440,923 bytes across 56 files: 55 receipt-covered files plus the receipt.
It retains assembly inputs, parent assembly/control evidence, input review and issue proposals,
pre-attachment and attached purpose results, decision/evidence document bytes, all twelve pair
audits, original snapshot/linked evidence references, train membership, implementation hashes
and exact implementation/schema copies. Root bindings remain diagnostic; no source alias is
activated. The coverage document retains its links to the earlier coverage package; that
historical package remains required for the underlying PNG/coverage evidence.

The publication runner is archived for audit, not offered as a generic production publisher.
It refers to the staged proposal location used for this run; deterministic verification uses
the persisted package inputs instead. Code identity includes the uncommitted helper and exact
source copies; a Git diff alone would omit untracked implementation bytes. Existing production
source, schemas and tests were not changed during this publication task.

Before publication, old control and reviewed file/record pins were rechecked, the original v2
manifest replayed, and train membership verified. Proposed issues regenerated identically from
explicit IDs/timestamps. Both checks passed before and after attachment. Package size was bounded
below 5 MiB; files were written to a fresh sibling staging directory, checked, then renamed to
the new final directory. No prior output was overwritten.

A separate readback verified all 55 receipt-covered hashes, all five manifest output bytes from
persisted assembly inputs, both attached-purpose results from persisted records/evidence, and
the complete retained inventories of the prior two manifest packages. All passed. Replaying
check_purpose uses the reviewed record and issue pins in publication-inputs/config, not values
inferred from untrusted records. The receipt itself is anchored by the hash above.

Native regression command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests --ignore=tests/retrieval -q -p no:cacheprovider
```

Result: **631 passed**, two existing torch.jit warnings, 5.32 seconds. The prior P3 review's
120 retrieval / 751 full-suite result remains historical; retrieval tests were not rerun in
this data-only task. No new source scan, external-drive access, mapping activation, frozen
cohort, training, Git commit/push or separate backup was performed. Ignored evidence is not
protected by the prior Git checkpoint.

## Next bounded step

Review a separate case-2 annotation/evidence slice using its retained audit, provenance and
v2 contract requirements; identify any missing evidence before authorizing new source reads.
Do not fabricate units or merge it into the five-study package. Then continue qualified-source
and frozen-cohort prerequisites for the localizer smoke. Purpose denials now have executable
records, but they do not close G1 or establish that any candidate is training-ready.
