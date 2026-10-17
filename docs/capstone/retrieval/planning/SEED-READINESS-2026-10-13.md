# Seed readiness — provisional local review, October 13

**Not a frozen seed set.** The title scan is incomplete; every lookup result below remains provisional.

Direct indexed PMID reads examined the 21 records already located without restarting the corpus scan. All 21 match title/year/venue; all supplied DOIs among those matches agree. Three located citations have no supplied DOI, so that test is not applicable. C-29 and C-42 are not located yet; this does not establish absence from PubMed.

| Candidate | Located PMID | Citation checks | Supplied DOI | MeSH present |
| --- | --- | --- | --- | --- |
| S-01 | 33840636 | True | Matches | Yes |
| S-02 | 39865461 | True | Matches | Yes |
| C-01 | 29785074 | True | Matches | Yes |
| C-05 | 37266655 | True | Matches | Yes |
| C-06 | 16009817 | True | Matches | Yes |
| C-07 | 33485792 | True | Not supplied | Yes |
| C-10 | 36055122 | True | Matches | Yes |
| C-11 | 38102442 | True | Matches | Yes |
| C-12 | 29427897 | True | Matches | Yes |
| C-13 | 37985692 | True | Matches | Yes |
| C-14 | 33328124 | True | Matches | Yes |
| C-17 | 35788343 | True | Matches | Yes |
| C-25 | 30194472 | True | Matches | Yes |
| C-27 | 34314356 | True | Not supplied | Yes |
| C-28 | 36223682 | True | Not supplied | Yes |
| C-29 | Pending scan | Pending | Pending | Pending |
| C-30 | 35840566 | True | Matches | Yes |
| C-31 | 15354301 | True | Matches | Yes |
| C-32 | 17409321 | True | Matches | Yes |
| C-33 | 18096536 | True | Matches | Yes |
| C-36 | 11719657 | True | Matches | Yes |
| C-40 | 33595105 | True | Matches | Yes |
| C-42 | Pending scan | Pending | Pending | Pending |

## Scope findings for review

- **C-25, PMID30194472:** the abstract lists liver and lung tumors, kidney contours and brain hematomas; it does not establish pancreas coverage. The working candidate rule explicitly requires pancreas coverage. Recommendation: classify as a scope probe under the existing condition, not a recall seed. This conclusion is about the available record, not an assertion about unseen full text.
- **C-36, PMID11719657:** the abstract directly studies how CAD cue quality affects human readers of mammograms. Recommendation: include as general imaging-AI workflow evidence for N5.2; describe the modality limitation and do not present it as pancreas-specific evidence. Its conditional promotion awaits Quinton’s scope decision.

## Missing-MeSH requirement

**Zero of the 21 located records lack MeSH.** The protocol target is at least three seeds without MeSH. Even if both still-unlocated candidates lacked MeSH, the current pool would not reach three. Do not mark that criterion complete. After the scan, propose additional candidates from the approved chaining sources for review, or explicitly review a limitation/amendment; do not silently waive the requirement or change search terms.

## Exposure controls

Created append-only INSPECTED-PMIDS.jsonl: 11 previously disclosed PMID exposures plus 21 events for this local review (32 events, 31 distinct PMIDs). Repeated PMID33840636 is intentional event history. All are ineligible for independent confirmation. Two new abstract exposures are explicitly marked. No relevance labels or policy predictions were produced.

EXPOSURE-MAPPING-PENDING.json keeps 17 explicit DOI/PMCID/article identifiers plus broader disclosed chaining groups unresolved. These need reconciliation before independent confirmation. The ledger is initialized, not a completed reserve_exposure admission receipt. Reserve/development/confirmation keys remain undrawn until P6 start; existing frozen needs and candidate definitions remain unchanged.

Private local review evidence: outputs/prowl/seed-readiness-20261013/provisional-matches.json and scope-review-source.json. Article abstracts remain outside repository documentation. No executable admission or selection run exists.

Next: finish scan; reconcile C-29/C-42 and possible additional matches; settle scope and missing-MeSH coverage; freeze accepted seed list; complete reserve/exposure admission and capacity review.
