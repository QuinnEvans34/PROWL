# First localizer cohort: publication and consumer handoff

September 28, 2026. D-269 authorizes the bounded shared publication controls and S4 cohort
registry/resolver. It does not authorize training or the rest of the orchestration system.
The cohort is published, independently resolved, and reproducibly rebuilt as recorded below.

## Implemented scope

- `src/operations/artifact_store.py`: shared local artifact writer/reader. One cooperating writer
  per artifact area; exclusive creation, destination-local hidden attempts, file/directory flushes,
  persisted semantic validation, completion evidence and same-volume directory publication. Failed
  attempts remain retained and unresolvable. Same-ID/different-derivation/content is refused; verified
  identical content may be reused with a separate retained attempt journal.
- `src/operations/storage_roots.py`: validates the existing setup registry and the separate D-269
  capability, checks the actual mount/UUID/APFS/writability and root-role separation, and scopes
  access to `prowl_artifacts/cohorts`. It does not modify `roots.yaml`, activate source aliases or
  set `scientific_runs_enabled`. No missing-root fallback is allowed.
- `src/data/cohort_registry.py`: replays the pinned S3 history, all three qualification transitions
  and qualifications, then validates full train/validation/test protection parents and the exact
  two-case child. The resolver requires an independent completion pin and reviewed manifest pin
  before returning CT/target/geometry/mapping descriptors. It opens no raw arrays.
- `scripts/diagnostics/freeze_localizer_cohort.py`: separate prepare, pinned publish and fresh-process
  resolve commands. The prepare output is a candidate, never a completed artifact. Producing source
  and schema hashes are captured; publication rejects code changes after preparation.

The frozen envelope is a new artifact-store v1 contract. Embedded cohort-v2 records retain their
existing `validated_in_memory` field unchanged; production completeness belongs to the verified,
immutable envelope. No old schema was silently reinterpreted or overwritten.

## Membership and assurance

Cohort ID: `cohort:pants-localizer-smoke-0001:v1`.

| Role | Members | Permission |
|---|---:|---|
| Original train parent | 7,200 | Protection only |
| Original validation parent | 1,800 | Protection only |
| Original test parent | 901 | Protection only |
| Initial localizer child | Cases 3 and 26 | Private noncommercial pancreas-present smoke target use |

Selection is ascending qualified ID from the retained five-case candidate pool, count exactly two,
shortage fails, no substitution. Case 31 remains qualified and unselected. Cases 78/266 remain blocked;
case 2 remains outside this package and held. Thirteen active issues remain in the final manifest.
The selected pool is deliberately not representative and supports no generalization claim.

The bundle carries the entire prior S3 package, original memberships and evidence. Original source
files remain unchanged. Source integrity is explicitly partial: ten hashed source files within 18,000
observed CT/pancreas files; publisher-test scope is identity protection only. Biological uniqueness
remains the approved, honestly recorded study-as-subject fallback. Source-level protocol provenance
is not expert certification of every contour.

## Tests, budgets and limits

Focused coverage: **37 tests**. Full native suite: **985 passed**, two existing torch.jit warnings.
Tests cover content/receipt/event tampering, missing completion, extra files, symlink/traversal,
interruption before publication, collision preservation, cross-process writer contention/release, hard-link rejection, reserve failure,
volume mismatch, registry change, root overlap, ancestry omissions, role changes, missing qualification,
fixed-membership/selection changes and an incompatible current manifest pin.

The storage tests run on temporary local directories. Registry tests simulate volume responses;
actual UUID/APFS/writability and on-drive publication are separately checked during execution.
There is no destructive power-loss/disconnect test or hardware-durability certification.

Bound: 96 MiB member payload per artifact, at most 32 flat members; completion/journal control reads
are bounded to 1 MiB each and producing metadata to 64 KiB. Before staging, reserve two payloads plus
2 MiB controls and `max(100 GiB, 10% volume capacity)` headroom; recheck free space during writes.
No raw-source job, automatic cleanup, unbounded transfer or model allocation is involved.

Locks use OS-held advisory `flock`, not age-based lock-file deletion. The persistent lock inode is
never unlinked. Journals record attempt, run/stage, host/process, timestamps and state. A killed
writer releases the OS lock but leaves its hidden attempt; no interrupted attempt is promoted by
inference. The complete workflow DAG/event schema, heartbeat recovery/takeover and Prefect spike
remain outside this slice. File immutability is enforced by writer policy and verified hashes,
not by a claim that other applications cannot edit an ownership-disabled external volume.

The resolver checks the manifest pin supplied by its trusted caller. It is not a background
revocation service: a newly recorded hold requires updating/revoking that authorization, and an
old bundle is refused against the new pin. The narrow first-cohort CLI pins the currently reviewed
manifest; it must not be reused as a generic “latest cohort” resolver.

## Readiness handoff

C01/C02: exact original split bytes and complete protected identity mapping rechecked.
C03/C04: retained source accounting and declared staged integrity evidence carried forward.
C05: known identity/available-content duplicate checks remain enforced; wider duplicate coverage is
not claimed. C06/C07: consumed CT/pancreas evidence, D-259 mapping and purpose qualifications replayed.
C08: production publication and fresh consumer verification are the execution checks below.

This is a bounded cohort-level readiness result, not blanket source/G1 clearance for all PanTS
uses. Next is Phase C: bind the verified descriptors to an approved read-only source root; enforce
pancreas-only loading; test orientation, spacing, resampling, label values, source-space round trip
and train/inference parity; inspect the transformed real cases. Run/checkpoint identity, recovery,
synthetic learning and the smoke resource budget still follow before training.

The source aliases and global scientific-run flag remain disabled. Claude's files are untouched.
No commit, push, model run, database installation or independent backup is implied.

## Execution evidence

Prepared candidate: `outputs/prowl/cohort-candidate-e1082d23-c566-427d-9e67-016737f1ed9f/`.
The reviewed plan hash was
`10b9b7e72fd08ac3361ece4cc31cf1c059f46cbe5b0ea57c1b2148314e1a096a`.
Its 13 payload members total 36,721,488 bytes. Publication succeeded on the registered APFS volume;
after publication the artifact contains 15 files, **36,728,338 bytes** including completion/journal.
A final free-space observation was 2,875,392,000,000 bytes. The unchanged setup registry still matches
the capability's hash; source paths and scientific-run enablement were not modified.

| Identity | Value |
|---|---|
| Root alias | `prowl_artifacts` |
| Relative URI | `cohorts/bdc3bf76881009824b678b0e38707b5bb733c2666aa22c92c2c9f396b1773cd0` |
| Completion SHA-256 | `37a4f6a8e248200de579a31631d740b5009b0836147b382aff50212084cb632c` |
| Derivation SHA-256 | `cbb2c53b9dff2b3f3deefd635692d6fcbf32e741f96e5388407ec88d10289c47` |
| Producer code/schema inventory SHA-256 | `5eeb0a55e768801d3f7f4b0f920005bbd8deffa1107c00da2e9f28f974171bc9` |
| S3 dependency receipt SHA-256 | `7018583fa42310a4a179efc0d5570eebb605a4b2d49c2f9883c33315b43872b2` |
| Reviewed manifest SHA-256 | `12ba8fe0a7013db13d06b0e0ea87ea949f167896bee9d2712b2d1d0f18d83220` |

A separate native process resolved that exact cohort/completion pin through the volume-checked store.
It replayed the source migration, three transitions and three final qualifications, checked all three
protection parents, and returned two CT/pancreas descriptors with their hashes, original geometry and
D-259 mapping. It reported `source_arrays_opened=false`.

A further independent process rebuilt the bundle from the pinned S3 package: **all 13 member hashes
were identical** to the reviewed candidate, including exact parent and child membership bytes. This
checks deterministic reproduction, separately from reopening a saved artifact. The full suite's last
run was 985 passes / two upstream warnings, in 8.88 seconds. `git diff --check` passed.

**R2 is closed for this exact smoke cohort.** The run is still not launch-ready. The returned source
references retain the inactive `followup_source` alias; Phase C must explicitly bind it through verified
read-only source configuration and check bytes/geometry before arrays reach the model. No consumer
may invent a filesystem path or fall back to a historical manifest. The producer's selected code/schema
hash inventory identifies its working bytes; a later reviewed Git checkpoint and independent backup
remain separate preservation work, and full run/environment identity remains a training gate.
