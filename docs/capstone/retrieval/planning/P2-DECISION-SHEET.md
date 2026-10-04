# P2 decision sheet for Quinton

**Prepared by:** Claude, 2026-09-28, as Codex's P2 re-review recommended.

**Status: decided (2026-09-28).** Quinton adopted
`../CODEX-P2-DECISION-SHEET-REVIEW-2026-09-28.md` as the outline: its recommendation table, with its
item-6 wording correction (see `RUNNING-LOG.md`).
- **Items 1-9:** approved as that review recommends.
- **Item 10:** approved in principle only. It still needs a signed one-file run record.

The table below is kept as prepared, except for the item-6 wording and the decision column.

**Not decided by this sheet:**
- the seed freeze (P6, after P5 verification);
- signing run S;
- dispatching the sizing tool;
- any download.

**Files at review:**
- `SEED-CANDIDATES.md` draft 5;
- `SEED-SET.md` revision 6;
- `SEARCH-AND-SELECTION.md` revision 7;
- `ACQUISITION-PLAN.md` revision 7.

Hashes are in `RUNNING-LOG.md`.

| # | Decision | Options | Recommendation | Your decision |
|---|---|---|---|---|
| 1 | **S-01 correction** (SEED-SET rule 12). The appendix citation does not match PMID 33840636. The live record is Suman et al. 2021, "Quality gaps in public pancreas imaging datasets", *Pancreatology* | Approve the corrected candidate (needs N5.5, N5.6, N4.3) / Reject (S-01 leaves the list) | Codex and Claude: approve | Approved |
| 2a | **Amendment A1:** case-sensitive token `AI` in block A | Approve / Reject | Codex: approve. Side effect: `AI-assisted` then supplies both W and A | Approved |
| 2b | **Amendment A2:** `intra-observer` in block M | Approve / Reject | Codex: approve | Approved |
| 2c | **Amendment A3:** `reader studies` in W, counted as one concept with `reader study` | Approve / Reject | Codex: approve | Approved |
| 3 | **Seven interpretations** (the status block of `SEARCH-AND-SELECTION.md`) | Approve all / Amend any by number | Codex: keep all seven | Approved (all seven) |
| 4 | **Proposed seed subset** | Accept the 16 R candidates, plus C-25 if item 5 resolves; accept/drop any of the 11 O candidates; or edit | Claude: the R set. The frozen set must be 15-25 accepted, verified seeds, with at least two per family | Accepted provisionally (candidate subset, not a freeze; room kept for WORKFLOW and a family-2 replacement). C-25 only if supported. The 11 O candidates are undecided |
| 5 | **C-25 scope** (Joskowicz 2019, CT contour variability). It is unknown whether it covers the pancreas. You are **not** asked to certify an unread paper | (a) Authorize Claude to read its abstract for a factual scope check. That is new literature exposure, so it is logged and entered in the ledger. (b) Drop C-25 and find another family-2 candidate by an approved discovery route | Codex: a factual check, not certification. Family 2 has only C-10 until this resolves | Option (a): a factual abstract check, with exposure logged. An inconclusive result is reported as such |
| 6 | **WORKFLOW / family 5 source (N5.1, N5.2).** No candidate tests WORKFLOW | Designate Goddard, Roudsari and Wyatt 2012 (*JAMIA*, doi:10.1136/amiajnl-2011-000089) for chaining. It was search-suggested by Codex, which needs the proposed SEED-SET rule 1 route approved. / Name papers you have read / Name another source | Codex: designate Goddard. Designating Goddard authorizes the disclosed reference-chaining route; it does not itself approve the review as a seed. If Quinton also wants the review considered as a candidate, that separate decision and its discovery-route basis are recorded explicitly, and the same relevance, verification and pre-freeze rules apply. It is never added silently through the designation (wording corrected per the decision-sheet review) | Designated. The review itself is **not** a candidate unless separately decided |
| 7 | **Rule 1 designated-source route** (proposed, SEED-SET revision 6) | Approve / Reject | Needed if you choose Goddard in item 6 | Approved |
| 8 | **Scope probes** P-02 (nnU-Net) and P-03 (ITK-SNAP) | Keep as probes / Move one to candidates | Claude: keep both | Keep both as probes |
| 9 | **Negative seeds** NEG-01 to NEG-03 | Keep as optional controls / Drop | Codex: keep | Keep |
| 10 | **PANORAMA protocol PDF** (6.3 MB, Zenodo), to read its reference list | Authorize one bounded download under its own small signed run record / Decline | Codex: allow. One file only, capped at 10 MiB, checked against MD5 `3c89347570dc4bb327924abfd7f001c0` plus SHA-256, with a receipt, and not ingested | In principle only. Needs a separate signed one-file run record; lower priority |

**Still open whatever you decide** (these are pre-freeze requirements, not decisions for today):
- the missing-MeSH check against the final snapshot (P5);
- meaningful WORKFLOW testing (item 6);
- the 90% seed-recall bar, which stays as is, with misses reported honestly.

The 10 uncovered needs do not each need their own seed.

## Round 2 decisions (Quinton, 2026-10-03)

Quinton: "I think we should continue on without codex's direction. I trust you, you know what to
do, and you should continue on."

| Item | Decision |
|---|---|
| Section A2 working priority (C-31, C-32 and C-33 accepted provisionally; C-36 to verify; C-34, C-35, C-37 and C-38 as reserves; C-39 out) | Accepted |
| Keep all 11 section A O candidates | Yes, as reserves |
| Family 2 second candidate | Left to Claude. Claude chained C-10's reference list and proposes C-40 (pancreas intra- and inter-reader reliability), which restores the family-2 minimum. C-25's check moves to P5 (local) |
| PANORAMA | Question only ("don't we already have PANORAMA downloaded?"). Answer: the dataset yes, the protocol PDF no. Run record P stays unsigned and optional |

## Round 3 decisions (Quinton, 2026-10-03)

Claude asked: "Do you approve the search policy and the 21-seed working list, so I can close P2
apart from run S?" Quinton: "Yes, I agree on the search policy, continue with that."

| Item | Decision |
|---|---|
| Selection policy v0 as a whole (`SEARCH-AND-SELECTION.md` revision 9) | Approved |
| 21-seed working list (22 if C-36 verifies), including section A3's C-40 and C-42 | Approved as the working list. Not a freeze: P5 verifies and P6 freezes |

