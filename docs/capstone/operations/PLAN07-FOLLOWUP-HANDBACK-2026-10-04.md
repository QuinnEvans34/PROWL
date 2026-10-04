# Plan07 follow-up handback — October 4, 2026

**Finished:** the separate shared retrieval contract section and reviewed preservation scope.
S1 remains qualified; Claude delivered S2 v1.1 and the other Codex chat completed native N2.
**N4 is incomplete:** the delivered parser watchdog still writes uncapped stderr outside SizingFs.
The concrete Claude interface request is saved below; the binding backend/rehearsal is not enabled.

## Files and evidence

- D-346–349 record the approved order, local commit/no push, shared checks and delivered hook status.
- Added `tests/test_retrieval_contracts.py` and14fixture/pin/provenance files. The12 accepted schemas
  and legacy Plan01/02 module/fixtures are unchanged. The contract README's status is reconciled.
- Shared module results:118new/173combined pass. Latest contract gate:198pass,3054deselected,
  two existing torch.jit warnings in4.11s. [Exact results](PLAN07-SHARED-CONTRACT-RESULTS-2026-10-04.md).
- [Native N2, performed by the other Codex chat](CODEX-S2-V1.1-NATIVE-REVIEW-2026-10-04.md):
  144sizing/326retrieval pass, no skips, Python3.12.13/expat2.7.4. That chat's ownership was N2 only.
  This chat independently reverified all22pins and identity
  `df585e2b10a69f55e24db8cc0f96822151a43d52be15ad5bb4917bd9a0a24d4e` without duplicating its tests.
- Prior S1 evidence remains49passing tests, four approved areas and61,440invented payload bytes;
  its five code/helper/test/fixture hashes and registry hash are unchanged. No new external writes.
- Added the [binding packet](PLAN07-S1-S2-BINDING-PACKET-2026-10-04.md) and
  [delivered-hook review/interface request](PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md).
  Hook forwarding, parser descriptors, parent manifest and code inventory are implemented.
  Guarded stream budgets/lease checks remain Codex responsibilities; bounded diagnostics require
  a Claude-owned response. Native compatibility tests alone do not close N4.
- [Local preservation record](PLAN07-LOCAL-PRESERVATION-2026-10-04.md) and its new exact scope
  supersede the older40-file pending list for staging. That older list remains historical.
  The prechange ignored snapshot retains original sizing_v1 bytes locally.

The reviewed checkpoint contains the qualified current v1.1 bytes, both original/new Claude
handbacks, original R2/new R3 prompts, hook proposal, N2 review and the latest Claude-owned log,
plus S1/shared-check changes and Codex records. Claude-owned files are preserved without edits.
Unrelated draft documents/binaries, ignored controls, registry, external receipts/source data and
imaging evidence are excluded. D-335 and its consumed requests, holds/cohorts and backup ceiling
remain fixed. No full expanded-project suite or gate closure is claimed.

## Decisions and exact next starting point

No approval is needed to finish the already authorized local preservation; pushing remains separate.
The next engineering step is Claude's concrete response to the bounded-diagnostics request, followed
by a fresh complete handback/pins and native qualification of changed code. This chat could not
verify a destination conversation in Claude's app and sent no message. Quinton can relay the
request at the top of [the hook review](PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md).

Then Codex implements and tests the approved descriptor binding against that exact interface,
including quotas, lease/identity failure, retained prior counters and primary/fallback failure.
Its separately frozen invented native rehearsal belongs only in binding-qualification child areas,
with imaging idle; no top-level `sizing-*` orphan or real Run S history. No new implementation or
rehearsal was dispatched here. S3/S4/signature/download, P4a/install/DB and metric-producer migration
remain separate. Stop at this handback; no follow-on dispatch.
