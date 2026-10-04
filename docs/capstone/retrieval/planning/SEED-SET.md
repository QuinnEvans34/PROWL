# Seed set

**Status:** protocol revision 7 (P2, 2026-09-28; candidate-list pointer and counts updated 2026-10-03).
- **Approved by Quinton on 2026-09-28**, adopting the Codex decision-sheet review: the rule 1
  designated-source route (Goddard 2012 designated) and the rule 12 correction of S-01.
- The rule 6 addition is still **proposed**.

The candidates are in [`SEED-CANDIDATES.md`](SEED-CANDIDATES.md) (draft 8, 2026-10-03):
- 28 section A candidates (16 accepted provisionally, 11 reserves, plus C-25 to verify in P5);
- 9 WORKFLOW candidates in section A2 (working priority accepted 2026-10-03);
- 7 proposed section A3 candidates chained from C-10;
- 2 scope probes and 3 optional negative seeds.

All are unverified. **Not frozen.**

Revision 6 (after the Codex review) changed these rules:
- rule 10: the title test is replaced by a topic-and-use test (R1);
- rule 12 (new): citation corrections (R2);
- rule 1: a route for a source Quinton designates (proposed in revision 6, approved in revision 7);
- rule 3: an exception for rule 12 corrections;
- rule 11: pre-run semantic term changes are not tuning.

Revisions 4-5 (P2) changed these rules:
- rule 1 adds second-level chaining;
- rule 3 adds named metadata lookups, the resolution order, the citation check and the outcomes;
- rule 6 carries a proposed addition for Quinton's review;
- rules 10-11 add scope probes and no-tuning;
- the `title_only_branches` field replaces `expected_branch`.

Rules 2, 4, 5, 7, 8 and 9 are unchanged.
**Purpose:** papers we already know belong in Tier 1, fixed before the selection policy runs. A missed
seed is objective evidence of a sensitivity gap (the known-item check from systematic-review search
design).

## Rules

1. **Independent of the selection policy.** Candidates come from citation-based sources, not from
   running our own query terms:
   - references in the approved proposal and appendix;
   - reference lists of the starter seeds and of the PanTS, PANORAMA and Medical Segmentation
     Decathlon papers (citation chaining);
   - reference lists of papers found by that chaining (second-level chaining). Each use is disclosed
     in `RUNNING-LOG.md`, naming the paper;
   - **(approved by Quinton, 2026-09-28)** the reference list of a source **Quinton
     designates in writing**, even if it was not chained. The disclosure says how the source was
     found (for example "search-suggested"), and the designation is recorded in `RUNNING-LOG.md`.
     The designated source itself is not automatically a seed;
   - papers Quinton has read;
   - stakeholder or librarian suggestions.
2. **Assisted discovery, then review.**
   - Claude proposes candidates, each with its source of knowledge.
   - Quinton reviews: accept, reject or add.
   - Quinton is not expected to supply all candidates alone.
   - Citation chaining is literature inspection. It is disclosed in `RUNNING-LOG.md`, and it happens
     before this selection run's results exist.
3. **Verified identifiers only.**
   - A candidate becomes a seed only after it resolves to exactly one PMID in the **final
     baseline-plus-updates snapshot** (P5), after deletions and replacements are applied.
   - No recalled-from-memory identifiers. No copied abstracts.
   - **Recording identifiers.** Candidate lists record identifiers and citation details as given by
     the chaining source ("per source"). A **named metadata lookup** (for example Crossref or
     OpenAlex) may complete or confirm a chained reference's DOI, title or PMID. Each such value is marked with the service's name in the candidate list, and the
     lookups are disclosed in `RUNNING-LOG.md`. A lookup never adds a candidate, except for a
     citation correction under rule 12.
   - Verification uses local data, so no live lookup is needed.
   - **Resolution order (P5).** Rules are tried in order:
     1. **PMID given:**
        - the PMID is absent from the final state: `unresolved`, or `deleted_in_snapshot` if its
          last event is a delete;
        - the PMID is present but fails the citation check: `identifier_conflict`;
        - a DOI is also given, and the record carries at least one DOI, none of which equals the
          given one: `identifier_conflict`;
        - otherwise: `resolves_in_final_snapshot`.
     2. **DOI given** (and no PMID): take the final-state records carrying that DOI, compared
        case-insensitively in `ArticleIdList/ArticleId[@IdType="doi"]` or
        `ELocationID[@EIdType="doi"]`.
        - Of those, exactly one passes the citation check: `resolves_in_final_snapshot`.
        - Several pass: `ambiguous`.
        - Records carry the DOI but none passes: `identifier_conflict`.
        - **No record carries the DOI:** fall through to rule 3. A success there is reported as
          `resolved_by_citation_after_doi_miss`.
     3. **Citation match** (no identifier, or after a DOI miss): the records that pass the citation
        check.
        - Exactly one passes: `resolves_in_final_snapshot`.
        - Several pass: `ambiguous`.
        - None passes: `unresolved`.
   - **Citation check:** all three must hold:
     - **Title:** equal after normalization. Normalization is: NFKC, casefold, then remove **every**
       character that is not alphanumeric, including spaces. So "multi-atlas" and "multi atlas"
       compare equal.
     - **Year:** the derived publication year (`SEARCH-AND-SELECTION.md` section 5.3) is within ±1
       of the cited year. If the record has no derived year, the year test is skipped and the
       result is flagged `year_unchecked`.
     - **Venue:**
       1. Each form is normalized: NFKC, casefold, parenthetical parts removed, a leading "the"
          removed, then split into alphanumeric word tokens.
       2. The cited venue matches if its tokens equal, or are the leading tokens of, the tokens of
          any of the record's `MedlineTA`, `ISOAbbreviation` or `Journal/Title`. For example, "AJR"
          matches "AJR. American journal of roentgenology", and "Diagnostics" matches
          "Diagnostics (Basel)".
       3. If the source gives no venue, the venue test is skipped and the result is flagged
          `venue_unchecked`.
       4. The venue test is deliberately loose (for example, "Radiology" also matches "Radiology:
          Artificial Intelligence"). The **exact title test is the primary check**; the year and
          venue tests guard against same-title collisions.
   - **`not_in_pubmed`** is never assigned by an automatic lookup, because local data cannot tell
     "not in PubMed" apart from `unresolved`. Only Quinton assigns it, to references known to be
     preprints or other non-PubMed works (rule 7).
   - **Unresolved outcomes** (`unresolved`, `ambiguous`, `identifier_conflict`,
     `deleted_in_snapshot`) are **never auto-repaired and never replaced by the nearest match.**
     Quinton decides whether the candidate is corrected, dropped or kept as unresolved. Each case
     is reported.
4. **Frozen before the first selection run** (start of P6), with the list's SHA-256 recorded in
   `RUNNING-LOG.md`. Later additions are reported separately and do not count toward that version's
   recall.
5. **Coverage target:** 15-25 seeds, at least two per question family, mixing study types.
6. **Actual MeSH absence, not year or status.** To test missing-MeSH handling, include **at least
   three seeds whose final-snapshot record has no MeSH headings** (the `MeshHeadingList` is absent
   or empty). Verify this directly in P5.
   - `MedlineCitation/@Status` is recorded as context only. Non-MEDLINE status alone is not the test
     condition.
   - A recent publication year is not evidence either.
   - **Proposed addition (P2, for Quinton's review):** if fewer than three accepted seeds lack MeSH
     in the final snapshot, P5 proposes more candidates from the disclosed chaining sources, for
     Quinton's review before the freeze. If none can be found, the shortfall is reported as a
     limitation of the missing-MeSH test.
7. **Only PubMed-indexed works count toward seed recall.** arXiv and Zenodo references are listed
   separately.
8. **Negative seeds (optional)** must be genuinely outside the policy: records that fail the
   candidate logic, or hit a hard exclusion rule, in `SEARCH-AND-SELECTION.md`. Examples:
   - an animal-only study;
   - an editorial;
   - an imaging-AI paper on a non-pancreatic organ without the WORKFLOW terms.

   **Treatment-focused pancreas CT papers are not negative seeds.** The current rules do not
   exclude them by design; precision sampling measures them.
9. **Prior exposure disclosed.** The project has already inspected literature (proposal, appendix,
   earlier project, planning research). The defensible rule is that seeds and needs are frozen
   before inspecting **this run's** results, not that nobody has read anything.
10. **Recall eligibility is decided by topic and use, never by policy terms.**
    - **A candidate counts toward seed recall** if Quinton judges that it:
      1. directly supports at least one approved need in `INFORMATION-NEEDS.md` v1; **and**
      2. lies in the Tier 1 topic scope, which is:
         - pancreas or pancreatic-lesion CT imaging, including appearance, delineation,
           measurement, anatomy, and AI detection or segmentation;
         - annotation, contour-review and dataset-construction methods for CT segmentation that
           cover the pancreas (families 2 and 5);
         - general imaging-AI review and workflow evidence, such as automation bias and human
           review of AI output (family 5).
    - **No policy term has to match**, in the title or anywhere else. Title-only branches are
      recorded as a **diagnostic column only**, never as the eligibility test.
    - **A scope probe** is a candidate judged outside that scope, with a **written substantive
      reason**. An example is a general model-architecture paper that answers no reviewer need.
      Each probe is reported as selected or not, with the deciding rule. It never counts toward
      seed recall or the 90% bar, and it is never used to tune the policy after results exist.
    - **A known relevant work the policy may fail to reach stays in the denominator.** Examples
      are dataset-method papers whose records never name the pancreas. A miss there is reported as
      a coverage limitation against the frozen needs. Any fix is a recorded policy revision under
      the revision limits; the seed is never reclassified as a probe.
11. **No tuning to seeds.** Seed titles are not used to add or change policy terms before the run.
    Seeds measure the policy's sensitivity; they are not a training set. A miss is diagnosed after
    the run, and any fix becomes a new policy version under the revision limits.
    Term changes argued from language semantics before any run (for example obvious spelling
    variants) are not tuning to seeds. They are recorded as pre-run amendments with their reason.
12. **Citation corrections.** When a given identifier resolves to a different work than the one
    cited:
    - the original citation and the conflict are kept, in `RUNNING-LOG.md` and in the candidate
      list;
    - the approved source document (for example the appendix) is **never edited**;
    - a corrected candidate may be proposed, carrying the live record's citation. It is still
      unverified until P5;
    - it becomes a candidate only on **Quinton's approval**;
    - its needs and families are reassessed from the corrected work, never carried over from the
      old citation;
    - in P5 it is still resolved against the final snapshot like any other candidate. P5 never
      substitutes a live record silently.

## Seed record fields

| Field | Meaning |
|---|---|
| `seed_id` | S-01, S-02, ... |
| `citation` | Authors, year, title, venue |
| `identifier` | PMID (verified) and/or DOI |
| `families / needs` | Families 1-5 and need IDs |
| `source_of_knowledge` | Where it came from |
| `proposed_by / reviewed_by / date` | Claude or Quinton; review outcome |
| `verification` | `unverified`, `resolves_in_final_snapshot` (with the flags `resolved_by_citation_after_doi_miss`, `venue_unchecked` or `year_unchecked` where they apply), `unresolved`, `ambiguous`, `identifier_conflict`, `deleted_in_snapshot`, `not_in_pubmed` (Quinton only) |
| `indexing_status` | `MedlineCitation/@Status` in the final snapshot (context) |
| `mesh_present` | Whether MeSH headings exist in the final snapshot (the missing-MeSH test condition) |
| `title_only_branches` | The set of branches (CORE, AI, MEASURE, WORKFLOW) the policy gives on the title alone, possibly empty, recorded before the run. A note says what MeSH or the abstract could add |

## Starter candidates (from approved appendix v3.1; unverified)

Kept here for history. The current list, including these two, is in `SEED-CANDIDATES.md`.

| ID | Citation | Identifier | Families | Source | Verification |
|---|---|---|---|---|---|
| S-01 | Suman, G., Patra, A., Korfiatis, P., et al. (2021). Assessment of pancreatic ductal adenocarcinoma using CT imaging. | PMID 33840636 (per appendix) | 1, 2 | Appendix v3.1 key references | **Live-record conflict (NLM record read by Codex, 2026-09-28):** the PMID is a different Suman et al. 2021 paper. The correction was **approved** by Quinton on 2026-09-28 (rule 12; `SEED-CANDIDATES.md`). The P5 outcome is still pending |
| S-02 | Artificial Intelligence in Pancreatic Imaging: A Systematic Review. *United European Gastroenterology Journal*, 2025. | PMID 39865461 (per appendix) | 4 | Appendix v3.1 A6 example record | unverified |

Coverage and remaining gaps: the one authoritative coverage table is in `SEED-CANDIDATES.md`
(draft 8).

## Appendix references: where each now sits

| Reference | Status |
|---|---|
| Antonelli, M., et al. (2022). The Medical Segmentation Decathlon. *Nat Commun* 13, 4128. doi:10.1038/s41467-022-30695-9 | Candidate C-30 in `SEED-CANDIDATES.md` (section A, an R candidate accepted provisionally on 2026-09-28), under rule 10's topic-and-use test. P5 verification is still pending |
| Li, W., et al. (2025). PanTS. arXiv:2507.01291 | Not a PubMed seed; used for citation chaining |
| Alves, N., et al. (2024). PANORAMA protocol. Zenodo doi:10.5281/zenodo.10599559 | Not a PubMed seed; used for citation chaining |

## Next steps

1. **P2:** Claude proposes candidates by citation chaining (disclosed). **Done: see
   `SEED-CANDIDATES.md`.** Quinton reviews them and fills the gaps.
2. **P5:** verify identifiers and MeSH presence against the final baseline-plus-updates snapshot.
3. **P6 start:** freeze and record the hash.
