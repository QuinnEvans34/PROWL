# Claude → Codex handoff: Plan 07 after P2 (2026-10-03)

**From:** Claude (Plan 07 lane). **Requested by:** Quinton ("write out a prompt for codex to work on
whatever it needs to work on").

This handoff states what the literature lane needs from Codex's owned areas. It does not dispatch
any work. Each item that needs authority names it.

**Arrangement Quinton set on 2026-10-03:** Claude continues Plan 07 planning on its own judgment,
without waiting for Codex review. Codex reviews are welcome but no longer gate this lane. Ownership
is unchanged:
- Codex owns the shared decisions, registry, operations, contracts, storage aliases and Git
  checkpoints;
- Claude owns `docs/capstone/retrieval/planning/` and the retrieval implementation.

## State of Plan 07

| Item | State |
|---|---|
| P1 | Needs frozen v1 |
| P3 | Synthetic foundation accepted |
| P2 approvals (Quinton) | **Selection policy v0 approved as a whole** on 2026-10-03: `SEARCH-AND-SELECTION.md` revision 9, SHA-256 `1cb96a960f04b58cb07a796a5ef0b2ea53e0337503279c8d373aa849f4b5c46a`. The 21-seed working list approved (22 if C-36 verifies). Seeds are verified in P5 and frozen in P6 |
| P2 still open | Only the S1 storage prerequisite (yours) and the run S signature it enables |
| Unsigned run records | S (sizing), A (baseline), B (PMC), P (PANORAMA protocol PDF, optional) |
| Evidence trail | Every decision and exposure is in `planning/RUNNING-LOG.md` and `planning/P2-DECISION-SHEET.md` |

---

## Prompt for Codex (paste as one packet)

> **Objective:** support Plan 07 after P2 without displacing the imaging queue (R-01 first). Work
> through the items below in order. For each, either complete it within its stated authority or
> prepare it for Quinton's decision. Stop after the handback.
>
> **Read first:**
> - `docs/capstone/retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md`;
> - `docs/capstone/retrieval/planning/RUNNING-LOG.md` (entries from 2026-09-28 onward);
> - `P2-DECISION-SHEET.md`, `SEARCH-AND-SELECTION.md` (revision 9), `SEED-SET.md`,
>   `SEED-CANDIDATES.md` (draft 8) and `ACQUISITION-PLAN.md`.
>
> **L1. Record the decisions** (`DECISIONS.md`; Codex-owned). Add records, citing RUNNING-LOG,
> for Quinton's approvals of:
> - **2026-09-28:** amendments A1-A3, the seven interpretations, the S-01 citation correction
>   (SEED-SET rule 12), the designated-source route with Goddard 2012 designated (rule 1), and the
>   16 R candidates as a provisional subset;
> - **2026-10-03:** the section A2 working priority, the 11 reserves, family 2 left to Claude,
>   **selection v0 approved as a whole** (revision 9 hash above), the 21-seed working list, and the
>   working arrangement above.
>
> Do not edit Claude's planning files.
>
> **L2. Storage prerequisite S1** (Plan 10; Codex-owned). Prepare the exact steps to:
> - create `prowl_scratch/literature/` and `prowl_artifacts/literature/receipts/`;
> - enable a controlled literature writer;
> - implement the volume-identity check that run S requires (ACQUISITION-PLAN, "Run S
>   prerequisites", S1).
>
> **Creating directories or enabling a writer needs Quinton's explicit OK.** Without it, deliver
> the plan and checks only.
>
> **L3. Sizing-tool packet S2** (SCOPE 12C; Group C, not granted). Draft the packet for Quinton to
> dispatch to Claude, the lane implementer. It covers the downloader subset and the sizing-only
> parser mode exactly as ACQUISITION-PLAN run S specifies:
> - frozen listings; streaming caps; 4 GiB memory; 20x expansion; DOCTYPE tolerated but never
>   fetched; the journal and fallback;
> - a write allowlist, tests on synthetic fixtures only (no network in tests), and the stop point.
>
> **Draft only.** No code, download or install.
>
> **L4. Git checkpoint.** In the pending checkpoint proposal, include the retrieval planning set:
> - `docs/capstone/retrieval/planning/*`;
> - the `CODEX-P2-*` reviews;
> - this handoff.
>
> Verify the hashes against RUNNING-LOG. **Commit or push only with Quinton's explicit
> authorization.**
>
> **L5. Housekeeping, for Quinton to approve.** Two leftovers from Claude can be deleted:
> - `_to_delete/claude-RUNNING-LOG.md.tmp` (one hash line);
> - `.git/index.lock.stale-claude-20260928` (0 bytes).
>
> Delete them only on his OK.
>
> **L6. Open integration decisions (list only).** Prepare a short options list for Quinton on:
> - whether the retrieval schemas (`docs/capstone/contracts/retrieval/`, 1.0.0) join the shared
>   contract checks;
> - the still-proposed D-085 amendment (span-hit and delivered-evidence metrics);
> - when to request P4a (Docker, PostgreSQL and pgvector platform trial; an install authorization).
>
> **Exclusions:**
> - no literature downloads, sizing runs, signatures, installs or database work;
> - no edits to `docs/capstone/retrieval/planning/` (Claude-owned) or to the frozen needs;
> - no new literature reading;
> - one writer per shared file;
> - the imaging packets keep priority, and this work must not compete for accelerator or storage
>   during a run.
>
> **Verification:**
> - L1 records cite the RUNNING-LOG entries and hashes;
> - L2 and L3 match ACQUISITION-PLAN run S word for word on caps and checks;
> - L4's file list hashes match.
>
> **Handback** (phone-screen first):
> 1. what finished;
> 2. files changed and checks;
> 3. decisions needed from Quinton, with options;
> 4. the exact next starting point.
>
> No follow-on dispatch.

## What Claude does next

Within its own lane, Claude does only planning that needs no new authority. Nothing in this
handoff authorizes P4 or P5 work.

The next lane steps that need authority:
- signing run S, after S1 and S2;
- run A;
- P4a.
