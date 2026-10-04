# PROWL contracts

These contracts define meaning independently from Python, FastAPI, React, storage services, or an
orchestration framework.

## Governing contracts

- [`identity-and-versioning.md`](identity-and-versioning.md) — stable logical identity, derivation
  keys, content hashes, versions, and invalidation.
- [`artifact-layout.md`](artifact-layout.md) — file-first local artifact layout and publication rules.
- [`run-manifest.schema.json`](run-manifest.schema.json) — workflow execution and stage state.
- [`case-package.schema.json`](case-package.schema.json) — transport-neutral UI package.
- [`review-event.schema.json`](review-event.schema.json) — append-only accept/edit-required/reject
  event.
- [`source-snapshot.schema.json`](source-snapshot.schema.json) — pinned imaging-source version,
  license, root alias, inventory, and assurance.
- [`subject-record.schema.json`](subject-record.schema.json) and
  [`study-record.schema.json`](study-record.schema.json) — protected grouping identity and one-exam
  imaging identity.
- [`annotation-record.schema.json`](annotation-record.schema.json) — structure-specific annotation
  provenance, encoding, validation, and allowed use.
- [`data-issue.schema.json`](data-issue.schema.json) — exclusion/quarantine/adjudication evidence.
- [`manifest.schema.json`](manifest.schema.json) — unified record collections and reconciliation.
- [`cohort.schema.json`](cohort.schema.json) and
  [`cohort-member.schema.json`](cohort-member.schema.json) — parentage, protected role, selection,
  freezing, and canonical membership.
- [`VALIDATION.md`](VALIDATION.md) — schema and documentation verification record.

Synthetic examples are in [`examples/`](examples/). Their repeated placeholder hashes demonstrate
shape only and are not project artifact identities.

## Contract rules

1. JSON schemas use JSON Schema Draft 2020-12.
2. Files conforming to a schema carry `schema_version`.
3. Scientific artifacts carry derivation identity and content integrity separately.
4. Paths inside contracts are relative POSIX-style artifact URIs, never local absolute paths.
5. A schema change that breaks a consumer requires a major schema-version change or adapter.
6. Examples and golden fixtures will be added under `tests/fixtures/contracts/` during Plan 09.

The current synthetic examples validate against their Draft 2020-12 schemas. This confirms the
architecture contract itself; it does not replace the application-level tests required by Plan 09.


## September 28 staged qualification implementation

Explicit source v2, manifest v3, purpose-qualification v1 and cohort/member v2 schemas now support
pure in-memory synthetic validation under D-266–D-268. Old schema meanings remain unchanged.
The new cohort state is `validated_in_memory`, never a production frozen artifact. See
[the implementation handback](../data/SYNTHETIC-QUALIFICATION-IMPLEMENTATION-2026-09-28.md)
for trust inputs, current scope, native verification and publication prerequisites.

## September 29 role-specific extension

[`purpose-qualification-v2.schema.json`](purpose-qualification-v2.schema.json) and
[`cohort-v3.schema.json`](cohort-v3.schema.json) explicitly distinguish pancreas-localizer
training targets from validation references. Member v2 and manifest v3 remain the underlying
contracts. Consumer operations must match the protected role. These are pure validated records,
not a new disk registry or model loader. See the
[implementation record](../data/ROLE-SAFE-QUALIFICATION-IMPLEMENTATION-2026-09-29.md).

The subsequent D-282 [expansion publication](../data/LOCALIZER-EXPANSION-FREEZE-RESULTS-2026-09-29.md)
freezes 16 train/11 validation records through an immutable completed artifact bundle and verifies
fresh-process resolution. This adds a real published use of the role contracts; expanded array
loading and preprocessing still require their own verified consumer.
