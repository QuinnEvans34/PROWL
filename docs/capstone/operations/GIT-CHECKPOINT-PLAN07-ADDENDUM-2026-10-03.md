# Pending Git checkpoint — Plan 07 L4 addendum

**Proposal only; no staging, commit or push.** This addendum belongs to the pending
[V2 checkpoint review](GIT-CHECKPOINT-REVIEW-V2-2026-10-03.md). The imaging chat remains its sole
manifest/review writer. This support task does not overwrite its working manifest or supersede its
portability findings. Quinton must approve the freshly merged exact scope before a local commit,
and separately approve any public push after remote-state review.

## Include and reconcile

The [literature file manifest](GIT-CHECKPOINT-PLAN07-FILES-2026-10-03.json) inventories:

- every ordinary file currently under `docs/capstone/retrieval/planning/` (all9 Markdown files,
  including already-tracked unchanged PHASES/INFORMATION-NEEDS);
- all4 existing `docs/capstone/retrieval/CODEX-P2-*` reviews;
- `docs/capstone/retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md`.

It also records the Codex-owned L1–L6 additions, current DECISIONS hash and paths to merge. Unchanged
already-tracked files need no artificial commit diff, but their identities are explicitly retained.
No downloaded references, restricted corpus text, images, private questions, approvals, local root
registry, credentials or scratch payloads are included.

The latest V2 file manifest observed during this task already includes the changed planning files,
four reviews and new Claude handoff. The complete14-file literature inventory verifies those live
bytes and includes the unchanged frozen files. DECISIONS and the new support documents postdate that
review, so the pending exact manifest must be regenerated and rechecked before approval/commit.
This addendum is not an executable partial-staging list and does not claim the entire live617-file
proposal has been reverified by this task.

## Hash evidence and limits

Latest approval/correction entries in Claude's RUNNING-LOG govern each planning file. The frozen
needs hash appears on the next line after its filename, not on the same line. That multiline pin was
checked directly, avoiding an incorrect comparison against its original draft hash. Historical
intermediate hashes are not expected to equal current revisions.

ACQUISITION-PLAN, INFORMATION-NEEDS, P2-DECISION-SHEET, PHASES, SCOPE, SEARCH-AND-SELECTION,
SEED-CANDIDATES, SEED-SET and the Claude handoff match their latest explicit log pins. The
decision-sheet review also matches its logged4830b3e4 pin. RUNNING-LOG has no recursive self-hash;
its exact live byte hash is recorded here. The other three reviews are cited by name but not fully
hash-pinned in RUNNING-LOG; their newly recorded live hashes match their entries in the pending V2
manifest. Do not describe those three as having a full log-hash match.

Claude's planning files were read only, then rehashed unchanged. If Claude subsequently writes a new
entry/revision, freeze the writer window and refresh the file list/pins. Do not silently publish stale
approval text or reinterpret the new planning arrangement as permission to overwrite that lane.

## Checkpoint-owner starting point

1. Read this addendum and the support handback; retain its completed D-336–D-340 records.
2. Reconfirm that all writers are idle for the exact snapshot; there was no cross-chat dispatch.
3. Merge the manifest's required literature inventory and `owned_support_paths` into the new exact
   checkpoint scope. Rehash all included live files, including DECISIONS and this addendum.
4. Recheck the existing public-content exclusions and fresh review/verification evidence. Retain
   ignored irreplaceable experiment controls independently; do not broaden into raw/copyrighted data.
5. Present the concrete regenerated local-commit scope. Ask for commit authorization, then obtain
   distinct public-push authorization and reconcile the remote tip before publishing.

The two housekeeping leftovers remain excluded and untouched. Their deletion needs the separate
Quinton decision described in the support handback; never remove an active `.git/index.lock`.

## Exact literature hashes

| Path | SHA-256 | Check |
|---|---|---|
| `docs/capstone/retrieval/planning/ACQUISITION-PLAN.md` | `a2be620c6b03373bc6a84b6cd88bf4f2177313bddc1992da7f3991ca713fc826` | logged pin matches |
| `docs/capstone/retrieval/planning/INFORMATION-NEEDS.md` | `d71577c27cebd5d54f516a7b2120273c3afba7dc077be3799bae4ccecbde8ac0` | logged pin matches |
| `docs/capstone/retrieval/planning/P2-DECISION-SHEET.md` | `8f3abc520162a8edca3fc70bbe18c5ba48fc68b8e693724ad6c1f7b266074311` | logged pin matches |
| `docs/capstone/retrieval/planning/PHASES.md` | `b4abe42d9d1b43504087175ab8f168356fd16356e6868402713ada862d1da4ca` | logged pin matches |
| `docs/capstone/retrieval/planning/RUNNING-LOG.md` | `f7657b99d87fd418857b1067adeca65460819b8dc43321b4c70fe09ff543bc9e` | live log hash; no self-pin |
| `docs/capstone/retrieval/planning/SCOPE.md` | `8ebd22f023b744dfbd36e97a04053ecc628604085440156ea99fa6d960dd0273` | logged pin matches |
| `docs/capstone/retrieval/planning/SEARCH-AND-SELECTION.md` | `1cb96a960f04b58cb07a796a5ef0b2ea53e0337503279c8d373aa849f4b5c46a` | logged pin matches |
| `docs/capstone/retrieval/planning/SEED-CANDIDATES.md` | `eceaa8bf57c7863f9cb2c1842f893b5e1d386002f05786364ca12099eda195f2` | logged pin matches |
| `docs/capstone/retrieval/planning/SEED-SET.md` | `d68b0b18e1085f87cc413f91ca1ad8b720a86d9d7517cf4eea5dc6006fff604c` | logged pin matches |
| `docs/capstone/retrieval/CODEX-P2-DECISION-SHEET-REVIEW-2026-09-28.md` | `4830b3e48ceb60adacc9c5c5bfbc2603546da1ed973c00de94a15c21d152061e` | logged pin matches |
| `docs/capstone/retrieval/CODEX-P2-OUTLINE-APPLICATION-REVIEW-2026-09-28.md` | `45e7d373423acde0d30530835474af1f7eb2a2220991af1b4a94321146bde660` | V2 pin matches; log has no full pin |
| `docs/capstone/retrieval/CODEX-P2-REREVIEW-2026-09-28.md` | `8ac4fad463b44c7df80445fa238c859bc3cd2d636aaa0dbadd2beb56fc3434a2` | V2 pin matches; log has no full pin |
| `docs/capstone/retrieval/CODEX-P2-REVIEW-2026-09-28.md` | `b932c200fc6d20380f5617cce313ba56451b420e86fe11f9186e5119c4ad37d5` | V2 pin matches; log has no full pin |
| `docs/capstone/retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md` | `9978b8088d25fa9dc24bcc1999470a2feec51e4d822ab7352f1afb5d4e1142df` | logged pin matches |
