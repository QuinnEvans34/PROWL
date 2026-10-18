# 10 — Baseline, reference integrity, and transfer

Packet prepared October 18, 2026. Branch: `codex/prowl-ui-redesign`.
Confirmed checkout: `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
Pre-package HEAD: `a723cff7924f0da26bef156eb5024c7c14f8a6bf`.
Initial audit HEAD: `5a86f27b7d5b36784f8ed4a4e557886e24ffa86a` (historical, do not reset to it).

## Concurrent work

The same branch advanced through literature changes while this package was prepared, including
`03a976c`, `0cdeba6`, and `a723cff`. Those changes are not this UI packet and must be preserved.
Current LiteratureSearchPanel includes source-record search and separate answer validation. Read
current source and its tests before refactoring it. Do not copy a stale component out of the audit.

The packet preparation begins with only the logo and UI-redesign folder untracked. A local scoped
commit will add those paths. No existing tracked code should change in that commit. Inspect the
actual Git status/log when starting; another worker may have advanced the branch after this record.

## Approved visual reference

- `prototype/prowl-workbench.html`: exact approved Concept 01 interactive source.
- `prototype/index.html`: standalone rendered preview of that source.
- `prototype/README.md`: limits and interaction guide.
- Repository root `PROWL_LOGO.png`: original provided logo, embedded unchanged in the reference.
- `REFERENCE-SHA256.txt`: hashes of these reference assets to identify the approved baseline.

Use files, not the temporary localhost address, as the portable reference. Run a loopback static
server from the prototype directory if needed. Do not overwrite the approved reference with production
output. Later approved iterations should get a new version and updated record.

## Local versus remote handoff

Claude in this checkout can read the branch files directly. For a separate clone, the branch and its
commit must be transferred through an explicitly authorized Git push/bundle or other file transfer.
The preparation task does not push publicly. Do not claim a local commit exists remotely.

A single local UI-packet commit makes these assets trackable, but this branch also contains the
concurrent literature commits above. The main conversation must review ancestry/diff before merging
or cherry-picking; do not assume everything on the branch is solely the visual redesign.

## Integration boundary

No production UI, backend, model, dataset, reference mask, database, service configuration, or training
state was altered to create this packet. The existing UI service on port 5180 was inspected; a separate
prototype server used 5191. Do not kill or replace either blindly; inspect ownership and availability.

No whole-project runtime verification is claimed. The packet's own checks cover local documentation
links, reference hashes, prototype JavaScript syntax, and previously recorded interactive browser checks.
