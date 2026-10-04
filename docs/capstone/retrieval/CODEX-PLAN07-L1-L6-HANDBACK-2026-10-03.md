# Plan 07 support handback — L1–L6, October 3, 2026

**Finished:** recorded the already-approved P2 decisions as D-336–D-340, prepared S1 storage setup
and S2 sizing-tool drafts, verified the literature checkpoint file list, inspected both cleanup
leftovers and listed the three integration choices. Planning files and frozen needs stayed untouched.

**Next decision:** Quinton can approve S1 implementation/setup and dispatch the S2 draft separately,
or defer both. No storage writer, directory, sizing run, signature, install or database was enabled.
No accelerator work, literature reading, downloads, Git staging/commit/push, deletion or follow-on
dispatch occurred. This handback is the stop point.

## L1 — completed decision reconciliation

[DECISIONS](../DECISIONS.md) now contains:

| Record | Approval being recorded |
|---|---|
| D-336 | September28 A1–A3 and all seven written interpretations |
| D-337 | September28 S-01 correction/rule12, designated-source route/rule1 with Goddard2012,16 provisional R candidates and retained probe/control boundaries |
| D-338 | October3 A2 priority,11 sectionA reserves and family2 left to Claude; Claude's discovery/scope-check actions are distinguished from Quinton's decisions |
| D-339 | Whole selection policy v0/rev9 and21-seed working list approved;22 only if C-36 verifies; P5 verification/P6 freeze remain |
| D-340 | Claude continues Plan07 planning without waiting for Codex review; ownership and separate execution safeguards unchanged |

Each record cites exact RUNNING-LOG entry titles and relevant full hashes. Current policy SHA-256
`1cb96a960f04b58cb07a796a5ef0b2ea53e0337503279c8d373aa849f4b5c46a` matches both Quinton's
L1 packet and the latest approval entry. No earlier approval is backdated as whole-policy approval.
No downloads or GroupC permissions are inferred from these records.

## L2–L3 — prepared, not executed

- [S1 setup proposal](../operations/PLAN07-LITERATURE-S1-PROPOSAL-2026-10-03.md): existing registry
  unchanged; native read-only UUID/mount/APFS/writable check matches. Both requested child directories
  are absent. Exact scoped writer/volume checks, invented tests and native setup acceptance are
  specified. The fallback's internal path and tiny storage reserve remain part of the setup decision.
- [S2 draft packet](../operations/CLAUDE-PLAN07-S2-PACKET-DRAFT-2026-10-03.md): downloader subset,
  sizing-only parser, proposed path allowlist, network-denied invented tests and stop point. Its annex
  contains the exact source Run S and sizing-mode text; no cap/check was weakened. Native acceptance
  and any missing dependency/platform capability must be reported honestly after an actual dispatch.

S1/S2 completion does not sign Run S. Fresh S3 capacity readings and S4 signature of a frozen literal
copy are still required; signed-copy hashes, tested-code identity and cumulative counters govern the
eventual execution. Quinton's Mac is the executor, not Claude's Cowork VM.

## L4–L5 — checkpoint and cleanup prepared

[Checkpoint addendum](../operations/GIT-CHECKPOINT-PLAN07-ADDENDUM-2026-10-03.md) and
[file/hash manifest](../operations/GIT-CHECKPOINT-PLAN07-FILES-2026-10-03.json) cover all9 planning
files,4 CODEX-P2 reviews and the handoff. Ten explicit RUNNING-LOG file pins match. RUNNING-LOG's
own live hash is recorded without pretending a self-pin exists. Three P2 reviews lack full log pins
but match the pending V2 manifest. Latest V2 already includes the changed retrieval files; the
checkpoint owner must refresh the exact scope for new DECISIONS/support docs before publication.
That avoids a second writer on the imaging chat's manifest/review.

Both proposed deletion targets were inspected and preserved:

| File | Observed bytes | SHA-256 |
|---|---:|---|
| `_to_delete/claude-RUNNING-LOG.md.tmp` |114; one text line; regular file, no symlink| `0c1f14cffafe4293718b85a8ef52dfa9bd004be9ebeddea03150082e1b004fe9` |
| `.git/index.lock.stale-claude-20260928` |0; regular file, no symlink| `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

If approved later, recheck these exact paths/types/hashes, then delete only those two files. Do not
delete the whole `_to_delete` directory, any active lock or unrelated contents. No approval is inferred
from this cleanup listing or from an unrelated Git checkpoint decision.

## L6 — decisions for Quinton, options only

The [integration options](CODEX-PLAN07-INTEGRATION-OPTIONS-2026-10-03.md) give the details.

| Decision | Recommended option | Other option |
|---|---|---|
| S1 | Approve bounded adapter implementation/setup, exact two child areas plus necessary parent, capability-scoped writer and reviewed internal journal fallback; enable only after tests | Defer; keep S1 incomplete |
| S2 | Dispatch the exact draft to Claude for code and invented offline tests only | Defer; no tool implementation |
| Git | Have checkpoint owner merge/refresh the exact scope, then approve local commit; decide public push separately after remote review | Keep proposal uncommitted |
| Housekeeping | Approve deletion of exactly the two verified files above | Retain them |
| Shared contract checks | Include accepted12 retrieval schemas in a separate offline contract section; preserve runtime relationship checks | Keep lane-local until P4b |
| D-085 metrics | Approve span-hit/delivered metrics as additional separately reported measures, keeping existing official metrics and explicit tokenizer/rights/label controls | Keep provisional until P7/P9 evidence |
| P4a timing | Prepare concrete named install/trial scope after immediate imaging/checkpoint work; run in an idle window | Request scope now but defer trial, or defer until S1/S2 acceptance |

This task's explicit instructions require Quinton's OK for directories/writer activation, GroupC S2
dispatch, Git commit/push and the two deletions. The plan approvals recorded under L1 do not supply
those distinct execution permissions. Integration choices are listed, not decided here.

## Files changed and verification

Changed `docs/capstone/DECISIONS.md` by appending five records only. Created this handback,
the integration-options file and four operations files (S1 proposal, S2 draft, checkpoint addendum
and JSON manifest). No existing planning, shared operations/navigation, code, tests, registry or
checkpoint-manifest file was edited.

Verification: intended checkout/workspace passed; approval/input hashes and frozen-needs multiline
pin checked; original DECISIONS prefix preserved; source Run S/sizing annexes exactly reproduced;
relative document links and whitespace checked; planning/registry/cleanup bytes unchanged. No code
tests were appropriate to these documentation-only changes; future S1/S2 tests are requirements,
not reported passes. The first sandbox volume query failed to access DiskManagement; the native
read-only query succeeded. Initial hash extraction missed the frozen-needs multiline pin; the explicit
pin was corrected before the checkpoint manifest. No actual frozen-needs mismatch occurred.

## Exact next starting point

Quinton reviews the options above. If S1/S2 are approved, Codex starts from the S1 proposal and
Quinton dispatches the S2 packet to Claude, with its exact allowlist and offline-only stop point.
Neither implementer starts a live sizing job from this handback. Meanwhile the imaging/checkpoint
chat can merge the L4 addendum when ready. Hand this file to Claude/new Codex chat for context;
no message or follow-on dispatch was sent by this task. Stop here.
