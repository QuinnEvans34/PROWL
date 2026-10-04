# Codex P2 revision 2 review

September 28, 2026. **R1–R3 are addressed at the planning-document level.** This accepts the
corrections for further planning, not P2 exit, seed freeze, sizing-tool dispatch or a signed download.
Claude's files were read and left unchanged. No selection code or download was executed for this review.

## Verified inputs

| File in planning/ | Measured SHA-256 |
|---|---|
| SEARCH-AND-SELECTION.md | 7f9cf5283d72983de8f61086039c1772f33e97833c021d8e5cb5472f66ad3964 |
| SEED-SET.md | e9801dac45bde04603396055101a70da9ddd2f8eecd0d383de75e0b61289d569 |
| SEED-CANDIDATES.md | 6d57a7bf23f91169092c8400bf11d5e6cb198b909538c7976169e61c0f06565c |
| ACQUISITION-PLAN.md | 0867311c8d6304821dcdf8e088c23bf0353959b06938e7546b6c375b071eacc6 |
| SCOPE.md | 8ebd22f023b744dfbd36e97a04053ecc628604085440156ea99fa6d960dd0273 |
| RUNNING-LOG.md | c5667dfee9719f49308b64bf5e58cd51d34f995c7a8eae4b33768b3124041d78 |

The candidate file matches the full hash in the running log, **not** the `023a3254…` prefix in the
forwarded message. This review covers draft 4 at the measured hash above. Reconcile the message in
Claude's next handback; do not roll the file back merely to match the earlier short hash.
INFORMATION-NEEDS v1 still matches `d71577c27cebd5d54f516a7b2120273c3afba7dc077be3799bae4ccecbde8ac0`.

## Findings against the earlier review

- **R1 addressed:** rule 10 now defines relevance from topic and reviewer use independently of the
  search terms. Title-only matching is diagnostic. Six former probes are candidates again; C-25's
  pancreas relevance remains explicitly conditional. Relevant misses cannot leave the denominator.
- **R2 addressed:** the S-01 correction preserves the historical citation, proposes the corrected
  Suman work and reassesses its needs. C-06 drops the unsupported isoattenuation mapping. The single
  coverage table now consistently identifies ten uncovered needs, conditional on accepting corrected
  S-01. Family 2 and WORKFLOW gaps are visible. P5 still must resolve identifiers against its snapshot.
- **R3 addressed in specification:** frozen listings, exact filenames, MeSH allowance, streaming and
  cumulative caps, no overwrite, parser limits, failure journals and fallback are specified. S1–S4
  remain incomplete/unsigned. Those promises need implementation and fault tests before signing.
  The proposed 4 GiB parser ceiling and 20× expansion limit are conservative stop rules, not measured
  PubMed requirements; reaching one means report and review, never silently relax it.
- A1–A3 remain proposed, with exact token semantics and distinct reader-study concept counting.
  The widened WORKFLOW behavior from `AI-assisted` is disclosed. E34 usefully detects double counting.
  Codex continues to recommend these amendments and the seven clarified interpretations.

## Small corrections for Claude's next edit

1. SEED-SET's heading **“References outside PubMed seed recall”** now contains recall-eligible C-30
   (MSD). Rename the section or move that row so the heading does not contradict rule 10.
2. SEED-CANDIDATES says “28 recall-eligible candidates,” although C-25's eligibility is pending.
   Say **28 proposed candidates: 27 with stated scope bases, plus one scope-pending candidate**.
   All remain subject to Quinton's review and P5 verification. Freeze counts must use actual accepted,
   verified eligibility, not this provisional total.
3. Run S's first/middle/last baseline positions are useful deterministic samples, but do not assert
   they cover the oldest-to-newest publication dates without evidence. Describe them as file-sequence
   positions; any observed year distribution belongs in the sizing receipt.

These wording fixes do not reopen the corrected denominator or require another broad redesign.

## Recommended next handoff

Keep the list unfrozen. Prepare a compact decision sheet for Quinton covering the corrected S-01,
A1–A3 and seven interpretations, the proposed seed subset, and a designated WORKFLOW chaining source
(such as the already disclosed Goddard review). A factual scope check for C-25 should establish whether
it covers the pancreas; do not ask Quinton to certify an unread paper merely to meet the family quota.
If it does not, obtain another family-2 candidate through the approved discovery route. Keep prior
exposure in the ledger; it cannot become independent confirmation evidence.

The 10 uncovered needs do not each require a separate seed. The genuine pre-freeze requirements are
15–25 accepted seeds, at least two per family, the missing-MeSH check against the final snapshot,
and meaningful testing of WORKFLOW. Retain the 90% bar and report misses honestly.

No new literature exposure was needed in this rereview. The supplied Crossref citation is covered by
the retained prior review and corrected handback; this pass makes no new live bibliographic claim.
No database installation, PANORAMA PDF download, run signature or Claude dispatch is implied.
