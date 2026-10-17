# Live workflow storage and Docker cache review — October 17, 2026

The authorized one-question live workflow check has not run. Checked database startup refused
before Compose because internal free space was95.547GiB against the104GiB admission requirement.
External free1967.710GiB exceeds408GiB; the configured drive UUID matches. Ollama is available;
workflow8015/UI5180/old answer8014 were offline at preflight. No inference or database start occurred.

Quinton asked to verify Docker cache necessity before any deletion. All inspection was read-only;
no Docker or npm cache, image, container, volume, repository or model was deleted.

## Findings

- Docker reports71 regular build-cache records, all reclaimable and immutable, created May4–18,
  last used about five months ago. Descriptions and parent ancestry identify Astro/Airflow builds.
- Total cache11.31GB: about2.15GB shared with retained image storage and9.162GB private cache.
  The37 private records comprise approximately2.827GB of dependency-install layers,6.335GB of
  copied project snapshots, and0.000191GB of copied dependency-list files. Group totals are
  approximate because this installed CLI emits rounded human-readable sizes in JSON.
- The Airflow source location in its historical container mounts no longer exists. Its relocated
  project was found with Dockerfile, requirements, package list, DAGs, include/plugins/tests and
  Git history present. The Dockerfile uses the same Astro runtime identified in the cache.
  Its existing local changes were left untouched. No byte comparison against historical cached
  project snapshots was performed; completeness of historical source backups is not certified.
- PROWL uses a retained digest-pinned pgvector image. Its database is an external-drive bind mount,
  not a build-cache record. The running XML-Adventure database is in a separate named volume.
  Neither running existing images nor accessing these database stores requires the old build cache.

## Decision and limits

The old cache is an operational cleanup candidate: removing unused build cache loses build reuse,
not the existing application containers, retained images or database volumes. Future Airflow builds
may need to rerun installation/download steps. Cache can also retain old intermediate source states;
we cannot assert that those historical states have no archival value. The current source checkout
exists, but that is not proof of byte-identical historical backups.

Do not use system/image/container/volume pruning for this request. No deletion approval is inferred
from the request to inspect. Npm cache cleanup also remains unapproved. Prefer a reviewed private-cache
ID allowlist if cleanup is authorized, with fresh idle/reclaimability checks and verification that
container/image/mount inventories remain unchanged. Remeasure host free space afterward; Docker's
reclaimable-byte report does not promise immediate equal recovery on the macOS host.

Two proposed boolean filter forms (`shared=false` and `private=true`, with a30day age filter) returned
zero records on this installed CLI; a bare `private` selector was rejected as malformed. These are
retained failed preview attempts, not evidence that the37 private records disappeared. Do not execute
an unverified broad replacement command to compensate. A subsequent anchored exact-ID preview matched all37 intended private records and no others.
The resulting allowlist is retained locally with approved=false; no prune command was executed.

Local inventory/evidence: `outputs/prowl/workflow-live-20261017/` contains the blocked startup log,
preflight, complete cache inventory, classification and attempted filtered previews. The first
classification script incorrectly assumed numeric JSON sizes and stopped before any mutation;
it was corrected to parse the installed CLI's human-readable sizes.

Official references: [Docker build-cache disk usage](https://docs.docker.com/reference/cli/docker/buildx/du/)
and [cache pruning and filters](https://docs.docker.com/reference/cli/docker/buildx/prune/).

Next: resolve cleanup authorization or free space through another user-selected method, remeasure
against the unchanged floor, then perform the already-approved one-question live integration check
and saved-result reuse verification. No automatic model retry, full selector or training.
