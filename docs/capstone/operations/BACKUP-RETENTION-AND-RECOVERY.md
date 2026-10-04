# Backup, retention, and recovery

**Status:** Approved design; scoped target/budget and synthetic restore verified; keeper/release qualification pending  
**Decisions:** P10-02, P10-05 through P10-07, P10-11, P10-12, and P10-19  
**Last reviewed:** 2026-09-19

D-258 selected the internal `PROWL-Backups` directory with a 20 GiB cap and 100 GiB internal
free-space floor. The initial synthetic JSON/review/array restore passed and selected controls have
hash-verified copies on both devices. See [the setup evidence](STORAGE-SETUP-2026-09-19.md).
No routine backup service, trained-model restore, off-site backup, or full raw-data mirror exists.
Recheck the cap/free-space floor on every future copy; never automatically delete to make it fit.

## September 28 checkpoint recovery evidence

D-273 verified a synthetic trained localizer checkpoint on the registered external artifact root,
its independent internal backup, and fresh-destination MPS consumer recovery with primary reads
refused. See [the bridge handback](LOCALIZER-RUN-BRIDGE-HANDBACK-2026-09-28.md). This is an executed
checkpoint drill, not a real-data-trained keeper, off-site backup or raw-data mirror. Existing cap,
free-space, no-deletion and later release-drill requirements remain.

## Purpose

September 28 literature amendment (D-262/D-263/D-264): canonical literature and live
PostgreSQL share the external failure domain. Rebuilding the DB only works if canonical
inputs survive. Raw baseline/updates have no independent-copy commitment; future upstream
availability and unchanged PMC bytes are not guaranteed. P6 must measure the Tier 1 rebuild
set and propose an allocation within the shared 20 GiB cap or another approved target.
Do not silently take imaging backup capacity. Protect held-out material in encrypted
images on both devices; never put its questions/labels in Git. Development labels and
small permitted manifests/configs can join a reviewed Git checkpoint, but a local commit
is not an independent remote copy. Lost frozen embeddings require a new identity if
regenerated. See [approved inventory and lifecycle](../retrieval/planning/SCOPE.md).

Preserve the evidence that cannot be replaced, retain the expensive artifacts that matter, and allow
large rebuildable work to be reclaimed safely. This policy avoids two unhelpful extremes: attempting
to mirror every terabyte, or assuming an ignored local directory is safe.

## Definitions

- **Primary:** the authoritative complete published artifact used by PROWL.
- **Copy:** another set of bytes; not yet trusted.
- **Verified copy:** member counts/bytes/checksums match the primary at a recorded time.
- **Backup:** a verified copy on a distinct recorded failure domain with a recovery purpose.
- **Restore-tested backup:** a backup successfully restored and opened/consumed from the backup copy.
- **Rebuildable:** parents, recipe, code, environment, and expected checks are retained; no second
  output copy is promised.
- **Keeper:** an artifact explicitly preserved because it supports a decision, comparison, demo, or
  release.
- **Quarantine:** invalid/incomplete content isolated from normal discovery and retention decisions.

A folder called `backup` is not necessarily a backup. Two folders on the same external disk are not
independent backups.

## Failure domains

Record at least:

- internal Mac SSD;
- new 4 TB physical external device;
- old approximately 500 GB physical external device;
- GitHub remote for permitted version-controlled material;
- any future approved remote compute/storage as temporary/non-authoritative unless explicitly
  promoted through a new decision.

The project currently has no claimed off-site scientific-artifact backup. GitHub provides remote
protection only for committed permitted code/small records.

## Retention classes

### A — permanent control/source

Examples:

- source snapshot manifests, file inventories, checksums, licenses, and acquisition records;
- unified manifests, subject/study/annotation records, mappings, exclusions, duplicate decisions;
- frozen cohort definitions/memberships;
- schemas, decisions, risks, requirements, preregistrations, metric specifications, and question sets;
- experiment registry, terminal decisions, and the living `docs/experiments.md` notebook;
- final documentation and release manifests.

Rule: retain through the project and final archive. Commit small permitted records to Git; keep
restricted/large payloads off Git with verified copies or redownload evidence.

### B — permanent append-only review evidence

Examples:

- review events and durable receipts;
- revision chain;
- content-hashed event snapshots used by evaluation/release;
- stakeholder session record under Plan 11.

Rule: never delete or edit individual events. Snapshot after a review session or material change and
copy the snapshot/catalog to a distinct available medium. Privacy/sensitivity rules remain.

### C — release/keeper

Examples:

- selected localizer/segmenter checkpoints and bundle manifests;
- model-comparison keeper required to support a final claim, including a decisive negative control;
- selected prediction/evaluation sets and operating policy;
- final permitted corpus/index representation needed by the demo;
- release case packages, test reports, diagrams, screenshots, and presentation.

Rule: retain primary plus verified second-media copy when feasible. Validate checkpoint/index/package
with a real consumer during restore. A checksum alone does not prove the binary can be used.

### D — controlled/confirmatory evidence

Examples:

- preregistration and complete run manifest;
- resolved config/environment/code identity;
- metrics and per-case/per-lesion results;
- logs necessary to understand success/failure;
- best/terminal checkpoint where needed to reproduce the comparison.

Rule: retain at least through final reporting/audit. Preserve small evidence permanently. Binary
retention depends on whether the claim can be reproduced without it and whether it is a keeper.

### E — exploratory pending decision

Examples:

- short diagnostic checkpoints;
- unselected candidate predictions;
- provisional index candidates;
- browser traces and local snapshots used during defect diagnosis.

Rule: retain until the result has a terminal decision and the weekly evidence consolidation is
complete. Keep the manifest/metrics/decision; checkpoint/payload may then be proposed for cleanup.

### F — reproducible derived

Examples:

- preprocessing caches;
- regenerated meshes or thumbnails;
- nonkeeper prediction sets;
- rebuildable retrieval indexes;
- dependency/browser caches.

Rule: no full backup required. Before deletion, prove the complete parent/recipe/environment chain and
one bounded rebuild. Verify no retained descendant points only to the candidate bytes.

### G — scratch and quarantine

Scratch belongs to one active attempt and is removed only after the final artifact or failure record
is safe. Quarantine defaults to 14 days so it can support defect diagnosis. Extension is allowed when
a defect/evidence record names why it remains.

## Backup tiers

| Tier | Contents | Target policy | Frequency/trigger |
|---|---|---|---|
| Tier A | Permitted code/docs/control records | Local Git + GitHub; selected local snapshot | At every coherent commit/push and milestone |
| Tier B | Review/release/keeper scientific artifacts | Primary 4 TB plus verified distinct device when capacity permits | On keeper designation, after review session, and release candidate |
| Tier C | Large reproducible derived artifacts | Primary only by default; manifest/recipe protected | On creation; selectively copy if rebuild cost is unusually high |
| Tier D | Scratch/quarantine | No backup | Remove only under exact policy |

### Intended use of the old drive

As of September 18, the old drive is unavailable and Quinton accepts source redownload. Preserve it
for optional recovery and exclude it from all available backup-capacity claims. A healthy independent
target must replace that assumption. The internal SSD may hold a bounded copy of small controls and
selected keepers after a size/reserve check; raw sources and caches need not be mirrored there.
Neither successful redownload nor a second folder on the primary drive supplies keeper backup.

### Source data

For publisher-hosted data, retain:

- source/version/repository identifiers and retrieval date;
- terms/license record;
- archive or file checksums supplied by the publisher;
- PROWL file inventory/content checksums after acquisition;
- extraction/reconciliation recipe;
- exact retained local location/failure domain;
- whether a tested second local copy actually exists.

“Can probably redownload” is documented as a recovery path, not a tested backup. If publisher access
or version stability is uncertain, local source copy becomes higher priority.

## Backup catalog

Every backup operation creates an immutable catalog with:

- catalog ID/schema/version;
- operation and verification timestamps;
- source artifact/root/failure domain and snapshot state;
- destination root/failure domain;
- copy tool/version/options;
- sorted relative member inventory, bytes, and hashes;
- controlling record and completion-marker validation;
- omissions with reason;
- verification status and errors;
- restore-test record(s);
- operator and approval reference;
- retention class and next verification date.

The backup catalog itself is Tier A control evidence and should be small/permitted enough to protect
separately.

## Backup sequence

1. Confirm the source artifact is complete and not actively written.
2. Confirm source/destination failure domains and destination capacity.
3. Acquire backup target lock.
4. Copy into a destination-local attempt path.
5. Verify counts, bytes, and every declared member checksum.
6. Validate schemas and controlling completion evidence.
7. Publish the backup copy/catalog and read it back.
8. Run a restore drill when required by tier/gate.
9. Mark the catalog `verified` or `restore_tested`; never infer either from exit code alone.

Incremental copying is allowed only if the catalog still proves the complete selected snapshot and
cannot mistake deleted/changed primary members for a valid backup.

## Restore sequence

1. Choose the exact backup catalog and recovery objective.
2. Treat the primary as unavailable; do not use its payload for validation beyond known expected
   control hashes.
3. Restore to a new scoped destination, never over the damaged/primary path.
4. Validate all members and control records.
5. Open/use the restored artifact in the smallest real consumer:
   - checkpoint: instantiate and load the model;
   - NIfTI/prediction: open, validate affine/shape/label contract;
   - retrieval index: reopen and run fixed queries;
   - review snapshot: validate/replay current-state projection;
   - release: validate manifest and start the bounded demo path.
6. Record time, result, errors, and exact source/destination identity.
7. Promote the restored copy to primary only through an explicit recovery event.

## Required restore drills

### Initial storage gate

- one small permanent control artifact;
- one representative keeper checkpoint or equivalent loadable artifact when available;
- one append-only review snapshot/control fixture;
- one corrupted-copy negative control.

### Pre-G8 release gate

- final/near-final keeper model bundle;
- final selected review snapshot;
- retrieval index or exact rebuild if classified reproducible;
- representative case package;
- release manifest/control records.

The pre-G8 drill must complete early enough to fix a broken procedure before Week 9.

## Cleanup protocol

There is no automatic broad “old outputs” or least-recently-used deletion command.

Every cleanup proposal contains:

- generated cleanup ID and timestamp;
- exact canonical paths (no unresolved variables, globs, or symlink targets);
- artifact IDs/types/retention classes;
- bytes expected to recover;
- completeness/keeper/backup/descendant/reference status;
- reason and reconstruction recipe where applicable;
- quarantine/diagnostic expiry;
- proposed recovery method if removal was mistaken;
- Quinton approval state;
- deletion result and post-delete free-space evidence.

Source, keeper, release, review, unclassified, active-run, or sole-copy material is rejected from the
cleanup manifest. Destructive execution is a separate user-authorized action after review.

## Recovery scenarios

| Scenario | Recovery order |
|---|---|
| Laptop/git checkout loss | Restore clone from GitHub; recreate locked environment; reconnect verified roots; validate local-only control records |
| New 4 TB primary loss | Stop writes; restore Tier A/B from distinct media/GitHub; redownload/reconcile source where allowed; rebuild Tier C from recipes |
| Old legacy drive loss | Use verified migrated source/copies only; otherwise redownload from pinned source and reconcile; disclose unrecoverable history |
| Accidental artifact removal | Do not overwrite evidence; restore to new location from verified backup or rebuild under a new recovery record |
| Partial/corrupt run | Quarantine attempt; validate last complete parent; resume/rebuild affected stage only |
| Review JSONL partial append | Preserve bytes; validate to last complete event boundary; append a recovery event/snapshot—never edit old valid events in place |
| Wrong environment run | Mark result ineligible; preserve diagnostic evidence; rerun from the approved clean environment |
| Remote instance loss | Local primary remains; retry only from local verified inputs under a new remote run; no cloud-only parent permitted |

## Verification tests

- same-disk copy is not labeled independent backup;
- changed/corrupt member causes catalog/restore failure;
- backup of active/incomplete artifact is refused;
- restore proceeds without reading primary payload;
- checkpoint/index/NIfTI/review consumer load catches semantic corruption;
- cleanup manifest rejects glob, unresolved alias, symlink escape, keeper, unclassified, active, and
  sole-copy paths;
- review snapshots preserve event order/content hash/current-state derivation;
- a rebuildable cache is deleted only after recipe/parent and bounded-rebuild proof;
- backup/restore evidence itself is retained and linked to the release audit.
