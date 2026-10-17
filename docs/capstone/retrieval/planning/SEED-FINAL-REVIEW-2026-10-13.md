# Final citation lookup review — October 13, 2026

**Lookup complete; seed freeze pending.** This supersedes the incomplete-scan status in SEED-READINESS-2026-10-13.md, while preserving that provisional review as history.

**Follow-up:** [SEED-DECISIONS-2026-10-13.md](SEED-DECISIONS-2026-10-13.md) resolves the identifier concern and dataset scope, records accepted C-25/C-36 decisions, and proposes three missing-MeSH additions. The findings below are the earlier review state.

## Citation results

All 41,226,017 titles scanned. Each of the 23 candidates has exactly one located title match; all pass the documented normalized-title, ±1-year and venue checks. All 19 supplied DOIs match the located record; the other 4 candidates supplied no DOI. All records have MeSH headings. C-29 resolves to PMID39116766 and C-42 to PMID34507900.

The lookup is title-led. It verifies supplied DOI agreement on located records, **not global DOI uniqueness or exhaustive DOI-led resolution** under SEED-SET.md rule 3. Do not claim that stronger identifier audit complete or silently change the protocol. A targeted identifier-index route or explicit reviewed reconciliation remains needed before claiming all P5 requirements satisfied; do not restart the title scan.

| Candidate | PMID | Cited / catalog year | Supplied DOI | MeSH |
| --- | --- | --- | --- | --- |
| S-01 | 33840636 | 2021 / 2021 | Matches | Yes |
| S-02 | 39865461 | 2025 / 2025 | Matches | Yes |
| C-01 | 29785074 | 2018 / 2018 | Matches | Yes |
| C-05 | 37266655 | 2023 / 2023 | Matches | Yes |
| C-06 | 16009817 | 2005 / 2005 | Matches | Yes |
| C-07 | 33485792 | 2021 / 2021 | Not supplied | Yes |
| C-10 | 36055122 | 2022 / 2022 | Matches | Yes |
| C-11 | 38102442 | 2023 / 2024 | Matches | Yes |
| C-12 | 29427897 | 2018 / 2018 | Matches | Yes |
| C-13 | 37985692 | 2023 / 2023 | Matches | Yes |
| C-14 | 33328124 | 2020 / 2020 | Matches | Yes |
| C-17 | 35788343 | 2022 / 2022 | Matches | Yes |
| C-25 | 30194472 | 2019 / 2019 | Matches | Yes |
| C-27 | 34314356 | 2021 / 2022 | Not supplied | Yes |
| C-28 | 36223682 | 2022 / 2022 | Not supplied | Yes |
| C-29 | 39116766 | 2024 / 2024 | Not supplied | Yes |
| C-30 | 35840566 | 2022 / 2022 | Matches | Yes |
| C-31 | 15354301 | 2004 / 2004 | Matches | Yes |
| C-32 | 17409321 | 2007 / 2007 | Matches | Yes |
| C-33 | 18096536 | 2008 / 2008 | Matches | Yes |
| C-36 | 11719657 | 2001 / 2001 | Matches | Yes |
| C-40 | 33595105 | 2021 / 2021 | Matches | Yes |
| C-42 | 34507900 | 2021 / 2021 | Matches | Yes |

C-11's local XML records electronic publication in2023 and journal publication in2024. C-27's citation says2021 while the catalog's journal and electronic dates say2022; it passes the approved ±1-year rule, but this review does not establish the origin of the2021 citation date. Preserve both dates without claiming exact-year agreement. Earlier wording that all years “match” meant the protocol tolerance, not equality.

## Scope review and recommendations

- **C-25:** classify as a scope probe under its existing conditional rule. The inspected abstract identifies non-pancreatic structures and does not establish pancreas coverage. This is not a conclusion about unseen full text; it must not count in the recall denominator on the current evidence.
- **C-36:** recommend accepting as general imaging-AI workflow evidence for N5.2, retaining its mammography limitation. Human scope decision remains pending.
- **C-32 and C-33:** citation checks pass, but the candidate table explicitly leaves their direct need mapping open. Their abstracts describe CAD-assisted diagnostic performance; neither establishes automated contour review (N5.1), and performance changes alone do not demonstrate automation bias (N5.2). Keep direct mapping unresolved pending substantive review; do not automatically promote related background into direct evidence or silently remove previously proposed seeds.
- **C-27:** abstract explicitly includes pancreas segmentation and cross-dataset evaluation; the pancreatic topic connection is supported.
- **C-28, C-29, C-30:** dataset/annotation or benchmark roles are supported by their abstracts, but these abstracts do not enumerate pancreas targets. Prior candidate documentation gives the pancreas connection as background knowledge/appendix provenance awaiting confirmation. Preserve that distinction and verify against retained approved-source evidence or primary dataset documentation before asserting all scope checks complete.
- **C-42:** abstract supports pancreatic CT attenuation/body-composition research, consistent with its proposed N3.3 mapping. No clinical claim is made by this review.

## Coverage and next steps

1. Resolve the scope/direct-need items above and record Quinton's final eligibility decisions under rule10.
2. Propose at least three genuinely relevant seeds without MeSH from approved citation-chaining sources. Current coverage is **0/3**, not satisfied. Avoid a new whole-catalog title scan: prefer known PMID reads and indexed/bounded lookups. Do not select candidates by whether the policy retrieves them, or alter selection terms to fit seeds.
3. Reconcile the DOI-led verification limitation and unresolved prior-exposure mappings; recheck the final 15–25 seed count and at least two per question family after eligibility decisions/additions.
4. Freeze the reviewed seed manifest and hash, then complete remaining selection admission/resource checks. No selection or vectorization begins in this review.

## Evidence

Final results: `outputs/prowl/seed-verification-20261012-02/matches.json`; SHA256 `0f805fb630ff9a0086d0571046378f9930dd20fdf81243e7f1a00bb93c42052c`.
Indexed local XML reads (8 records, shared catalog writer lock, read-only SQLite) retained privately in `outputs/prowl/seed-readiness-20261013/final-review-sources.json`. Earlier C-25/C-36 source evidence remains in `scope-review-source.json`. Abstract text is not copied into tracked documentation. Added final metadata and abstract exposure events to INSPECTED-PMIDS.jsonl; none are independent-confirmation eligible. No policy predictions or relevance sample labels were generated.
