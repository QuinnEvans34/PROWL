# Storage roots and artifact publication

**Status:** Approved design; scoped roots/capability checks passed; source activation/production resolver pending  
**Decisions:** P10-01 through P10-10, P10-17, and P10-18  
**Last reviewed:** 2026-09-19

September 19 execution: [D-258 setup evidence](STORAGE-SETUP-2026-09-19.md). Local setup roots and
the independent internal backup are registered; scientific source aliases remain null. The archive
downloader uses an isolated `sources/pants/acquisition-<revision>/` directory, not an activated source
snapshot. It retains `.part` files there for resume; none are discoverable through a source alias.
Production resolution, source-write protection, and generic publication remain unimplemented.

September 28 D-269 implementation: the shared bounded writer and reader now support cohort artifacts
through a separate pinned capability over the unchanged setup registry. See the
[publication handback](../data/LOCALIZER-COHORT-PUBLICATION-2026-09-28.md). The first cohort is published
and independently resolved. Earlier “unimplemented” wording below is historical for this narrow
slice; global scientific-run enablement, source activation and full workflow recovery remain pending.

## Purpose

Define how portable scientific identity is translated into local files without letting an absolute
path, mount name, partial directory, or convenience pointer become evidence.

## Physical role versus logical role

| Concept | Example | Governs |
|---|---|---|
| Physical device/failure domain | New 4 TB external device | What can fail at the same time and whether a copy is independent |
| Mounted volume | A verified UUID mounted below `/Volumes` | Current operating location and filesystem capabilities |
| Root alias | `prowl_artifacts` | Portable application configuration and allowed path boundary |
| Artifact identity | `model:...`, prediction/evaluation IDs and hashes | Scientific lineage independent of machine path |
| Relative member URI | `models/<id>/checkpoints/best.pt` | Portable location below an owning root/artifact |

Changing the mount path may require a root-registry update but does not change scientific identity.
Changing content, source snapshot, relevant configuration, or component version changes identity.

## Root aliases

| Alias | Intended content | Access policy | Candidate location |
|---|---|---|---|
| `pants_source` | Frozen PanTS imaging, labels, metadata, and source controls | Read-only to workflows | Fresh pinned acquisition on `PROWL-Data`; old-drive recovery optional |
| `panorama_source` | Frozen eligible PANORAMA imaging/labels/metadata and source controls | Read-only to workflows | New 4 TB after source snapshot verification |
| `literature_source` | Frozen PubMed baseline/updates, MeSH and permitted PMC source bytes | Unavailable until signed acquisition and verified snapshot; then read-only | PROWL-Data, `external_primary`; D-261/D-263 |
| `prowl_literature_db` | Derived PostgreSQL data/index/WAL and scoped recovery instance | Disabled pending P4a layout and separate execution approval; controlled DB writer thereafter | PROWL-Data, same `external_primary` as canonical literature; D-263 |
| `prowl_artifacts` | Published manifests, cohorts, models, predictions, evaluations, retrieval, case packages, reviews, tests, releases | Controlled writer; immutable after publication except append-only event container | New 4 TB candidate |
| `prowl_scratch` | Run-scoped temporary/cache/download-in-progress content | Controlled read/write; never scientific authority | New 4 TB candidate; bounded internal scratch only by explicit config |
| `prowl_backup` | Verified Tier A/B copies and backup catalogs | Backup writer only; separate failure domain required for “backup” claim | Internal SSD under D-258: 20 GiB cap, 100 GiB free-space floor; old drive excluded |

One physical drive can host multiple aliases, but the root registry records the shared failure-domain
ID. `prowl_backup` cannot resolve to the same physical failure domain as `prowl_artifacts` for a
record to claim independent backup status.

September 28: literature aliases are defined in this design and as optional disabled
entries in the setup-only schema/example. The ignored real `roots.yaml` is not activated
or changed by planning reconciliation. An actual path/UUID/layout binding requires the
appropriate signed acquisition or approved platform trial. Canonical/derived literature
artifacts use `prowl_artifacts/literature/`; database state is never canonical.
Both new aliases share `external_primary`, so a second folder there is not a backup.
No global Docker disk relocation is implied. Quinton must approve any such change after
cross-project inventory. Tier 1 and database+recovery each have provisional 100 GiB
ceilings, not reserved capacity or permission to write. D-258 backup allocation remains shared.

## Local root registry

### Proposed files

- `configs/local/roots.yaml` — ignored, machine-specific, real paths and volume identities.
- `configs/local/roots.example.yaml` — committed, fake/path-free teaching example.
- environment variable `PROWL_ROOTS_FILE` — optional pointer to a different local registry.
- `PROWL_ARTIFACT_ROOT` — temporary compatibility override only; must resolve to the same registered
  artifact root and cannot bypass volume checks for formal runs.

### Proposed registry shape

```yaml
schema_version: 1.0.0
failure_domains:
  external_primary:
    kind: physical_volume
    volume_uuid: EXAMPLE-ONLY
roots:
  prowl_artifacts:
    path: /example/PROWL/artifacts
    role: artifact
    access: controlled_write
    failure_domain: external_primary
    filesystem: apfs
    verified_at: 2000-01-01T00:00:00Z
```

The example is illustrative; the actual schema and fake values are implemented only after approval.
Secrets never enter the registry.

### Resolver behavior

Resolution occurs before file access:

1. validate registry schema;
2. find the alias and requested role;
3. obtain the canonical/real path and mounted-volume metadata;
4. compare expected and current volume UUID/filesystem/failure domain;
5. join and normalize only an approved relative member path;
6. reject escape, alias-role mismatch, mount mismatch, or forbidden overlap;
7. record alias and relative URI in scientific evidence; record absolute path only in a redacted
   local operational log if necessary.

No formal run silently falls back to the repository, current working directory, `/tmp`, or internal
SSD when an external alias is missing.

## Filesystem acceptance

APFS is the preferred primary format for this macOS-only canonical writer because the project relies
on local file permissions, append behavior, locking, and atomic same-volume publication. The actual
4 TB drive is not assumed to be APFS.

An existing non-APFS filesystem may be accepted only after a scoped capability record proves:

- write/read/flush and content-hash equality;
- rename publication within the same volume;
- exclusive lock or lock-file semantics used by PROWL;
- append followed by reopen/read-back;
- Unicode/case/long-name behavior for chosen safe IDs;
- permission/error behavior expected by the writer;
- interrupted/incomplete content remains distinguishable;
- remount/disconnect does not expose a partial as complete.

Reformatting is destructive and outside design approval. If needed, first preserve/verify existing
content, present exact format/partition/encryption alternatives, and obtain explicit Quinton approval.

## Artifact areas

The Plan 01 logical structure remains authoritative and is extended operationally:

```text
<prowl_artifacts>/
├── sources/
├── manifests/
├── cohorts/
├── cache/
├── workflows/
├── models/
├── predictions/
├── evaluations/
├── retrieval/
├── case-packages/
├── reviews/
├── tests/runs/
├── environments/
├── benchmarks/
├── backup-catalogs/
├── releases/
└── quarantine/
```

Run attempts use a destination-local private temporary path, not a shared project `tmp` path. Scratch
may hold large intermediate work, but the final validated bytes are staged/published on the artifact
filesystem so publication never depends on a cross-volume rename.

## Identity model

### Derivation hash

Canonical SHA-256 over:

- artifact type/schema version;
- producing component and contract version;
- ordered parent artifact IDs and content hashes;
- complete relevant resolved configuration;
- deterministic source/cohort/policy IDs;
- declared randomness inputs where relevant;
- environment factors only when they are part of the artifact's declared equivalence policy.

Irrelevant operational values such as local mount path, display name, wall-clock start, and hostname do
not change derivation identity.

### Content hash

- Single files: SHA-256 of exact bytes.
- Canonical JSON: canonical serialized bytes, not pretty-print layout.
- JSONL: per-record schema plus exact file-byte hash; append-only live containers use frozen snapshot
  hashes for downstream/release lineage.
- Multi-file artifact: sorted relative-path inventory containing type, bytes, and member SHA-256,
  plus hash of the canonical controlling record/inventory.
- NIfTI/checkpoint/index: exact byte hash plus format-specific validation/load test; a hash alone does
  not prove semantic validity.

Hash algorithms are not invented per component. SHA-256 is the content standard unless a source
publisher supplies a different checksum, which is retained as additional provenance rather than a
replacement for the PROWL hash.

## Publication states

```text
planned -> attempt/running -> validating -> complete
                       \-> failed/quarantined
```

Only `complete` is consumable. A directory does not become complete because all expected filenames
appear to exist; the writer must validate and publish the completion evidence last.

### Required publication evidence

- artifact ID/type/schema/component version;
- parent IDs/hashes and derivation hash;
- sorted member inventory and checksums;
- record counts, bytes, and format-specific validation summary;
- created/completed timestamps and producing run/stage/attempt;
- retention class and license/sensitivity flags;
- completion marker or frozen controlling record hash.

### Collision behavior

| Situation | Behavior |
|---|---|
| Same derivation and same verified content | Reuse may be recorded without rewriting |
| Same derivation and existing incomplete attempt | Create new attempt or resume only under component policy; never publish by inference |
| Same derivation and different complete content | Stop, retain both attempts in quarantine, open nondeterminism/collision defect |
| Different derivation, same content | Preserve distinct lineage records; optional deduplication only below the logical contract |
| Requested artifact ID already belongs to another type/version | Hard failure |

## Lock policy

Locks are scoped to the smallest resource that prevents corruption:

- one accelerator lock for an MPS/CUDA job;
- one writer lock per artifact family/root where publication or append can conflict;
- one review-event append lock;
- one backup/migration target lock;
- optional source-acquisition lock per source snapshot.

A lock record includes lock schema/version, resource ID, run/stage/attempt, host/process identity,
created/heartbeat time, and intended output. A lock is not declared stale by age alone. Takeover needs
evidence that the owner is terminal/unreachable, the destination has no complete conflicting artifact,
and the partial is validated/quarantined. The takeover itself is an event.

## Capacity policy

Before a write:

```text
required_free = expected_final_bytes
              + worst_case_temporary_bytes
              + checkpoint/retry_reserve
              + operational_headroom
```

Initial operational headroom is `max(100 GiB, 10% of usable volume capacity)`. Component estimates
must state how they were derived and whether compression can temporarily expand. Unknown-size bulk
work requires a measured small sample and conservative projection first.

Readers also monitor remaining space while writing. Crossing the run's reserved limit produces a
controlled stop/partial state; it does not start deleting caches automatically.

## Historical compatibility

- Existing `outputs/manifest.csv`, `outputs/splits/`, MLflow data, checkpoints, evaluations, and UI
  cases remain historical.
- Historical absolute paths may be recorded in migration evidence but are not copied into new
  portable contract fields.
- An adapter may validate and import a named historical artifact under a new capstone record.
- Copying a directory does not make it conforming.
- Historical `best.pt`/`last.pt` names are subordinate to run archive/manifests and hashes.
- Unknown historical content stays in place until classified.

## Required tests before a real root is approved

- registry schema/alias/role positive and negative cases;
- wrong UUID and same-name/wrong-volume failure;
- relative-path traversal and symlink escape rejection;
- root overlap/source-write rejection;
- capability test on the candidate volume;
- same-filesystem publication and interrupted-write quarantine;
- content/derivation collision behavior;
- lock contention and controlled stale takeover;
- capacity projection and reserve enforcement;
- complete artifact discovery ignores temp/quarantine/convenience pointers.
