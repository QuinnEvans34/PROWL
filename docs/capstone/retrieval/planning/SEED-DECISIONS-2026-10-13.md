# Seed decisions and additions — October 13, 2026

Status: existing C-25/C-36 decisions accepted by Quinton ("Great, I agree. Let’s move on that."); three new additions and C-32/C-33 background disposition below are proposed for final review. No frozen set or selection run.

## Decisions applied

C-25 is a scope probe, excluded from recall under its existing conditional rule. C-36 is accepted as general imaging-AI workflow evidence for N5.2, with its mammography limitation. The earlier candidate file is preserved byte-for-byte as the lookup's producing input; this dated addendum supersedes its pending scope language for these two items.

## Identifier concern resolved without another scan

The earlier final review overstated the need for global DOI uniqueness. Rule3 requires exactly one DOI-bearing record that **passes the citation check**, which necessarily includes exact normalized title equality. The completed exhaustive title scan found exactly one title match per candidate. Each passes the remaining citation criteria and every supplied DOI agrees. Thus no second record can pass the DOI-plus-citation conjunction. This proves the required resolution result without proving or requiring DOI uniqueness among unrelated titles.

Verified completed status/count, checkpoint match lists, result records, unchanged catalog stat, producing script and candidate hashes. All23 resolve; two use supplied PMIDs,17 use DOI plus exhaustive title evidence, four use citation evidence. Evidence: `outputs/prowl/seed-readiness-20261013/identifier-reconciliation.json`. This is a logical reconciliation of existing evidence, not a protocol waiver or new corpus scan. It supersedes the identifier blocker in SEED-FINAL-REVIEW-2026-10-13.md.

## Dataset scope confirmed

- C-28 WORD: author manuscript v4 Table1 explicitly lists pancreas; sections3.2 and4.2.2 describe annotation checking and human correction. Supports existing N5.4/N5.5 mappings. https://arxiv.org/html/2111.02403v4
- C-29 AbdomenAtlas: authors' project links the2024 paper and documents pancreas in its annotation class maps. Supports the pancreatic dataset connection for existing N5.3/N5.5 mappings. https://github.com/MrGiovanni/AbdomenAtlas
- C-30 MSD: original paper Figure1 identifies pancreas among its tasks; publisher indexing also identifies pancreas-tumor evaluation. Supports the pancreatic benchmark connection for N5.5/N4.6. https://www.nature.com/articles/s41467-022-30695-9

These establish topic scope; they do not certify downstream retrieval performance or independently validate the authors' numerical claims.

## Three proposed additions

All three are present by supplied-reference PMID in the final local snapshot, with no MeshHeadingList headings. Source PMIDs are from actual reference lists, not recalled identifiers. DOI/title/venue/year below are completed from local metadata. No selection policy predictions were inspected.

| ID | Paper | Local identifiers | Approved reference chain | Direct need and basis |
| --- | --- | --- | --- | --- |
| C-47 | A Bottom-Up Approach for Pancreas Segmentation Using Cascaded Superpixels and (Deep) Image Patch Labeling. IEEE Trans Image Process,2017 | PMID27831881; DOI10.1109/tip.2016.2624198 | C-10 PMID36055122, local reference11 (second-level chain) | N4.6: abstract describes abdominal CT pancreas segmentation, cohort, cross-validation and evaluation metrics. |
| C-48 | Using Quantitative Imaging for Personalized Medicine in Pancreatic Cancer: A Review of Radiomics and Deep Learning Applications. Cancers,2022 | PMID35406426; DOI10.3390/cancers14071654 | S-02 PMID39865461, local reference97 | N4.6: section3.2 reviews pancreatic cancer detection studies and evaluation; section4 discusses acquisition/segmentation variation and limitations. |
| C-49 | Artificial Intelligence in the Diagnosis and Treatment of Pancreatic Cystic Lesions and Adenocarcinoma. Cancers,2023 | PMID37173876; DOI10.3390/cancers15092410 | S-02 PMID39865461, local reference115 | N4.3/N4.6: sections3.1.2 and3.2.5 discuss CT detection models, external evaluation and limited generalizability. |

C-48/C-49 also cover diagnosis/treatment beyond PROWL's question scope; only relevant research passages would support answers. This proposal is not permission for patient diagnosis. Full texts obtained via Europe PMC's public open-access API and retained privately as PMC8997008.xml and PMC10177524.xml. Web publisher requests returned429 and PMC pages presented browser checks; those routes were not bypassed. Metadata/abstracts remain local evidence, not copied into Git.

## Proposed final membership

Keep the existing accepted working candidates including C-36, with **C-32/C-33 retained as related background outside the recall denominator** unless a direct frozen-need mapping is established. Their current abstracts do not establish contour-review evidence or over-trust mechanisms. This disposition is substantive and proposed before any selection results, not a reaction to a retrieval miss.

Add C-47/C-48/C-49. Result: **23 recall seeds**, **3 without MeSH**. C-25 remains a scope probe. This is still proposed, not frozen.

Minimum family coverage is retained: family1 C-01/C-05; family2 C-10/C-40; family3 C-06/C-07/C-42; family4 multiple existing studies plus new additions; family5 S-01/C-27/C-28/C-29/C-30/C-31/C-36. These count existing reviewed family assignments, not a claim that every need has two papers. In particular C-06's N3.1 mapping is inherited from the approved working list; no new full-text claim was made here.

## Bounded search and disclosure

Read stored reference lists from S-02,S-01,MSD,C-12,C-10,C-27,C-28,C-29. S-02/MSD yielded150 PMID-linked references; C-10 yielded31. Other queried local records had no reference list. Metadata/MeSH checks are indexed PMID reads under a shared writer lock. Twenty missing-MeSH records appeared in the first150; one further segmentation paper appeared in C-10. Seven candidate abstracts were inspected; three classification-only studies were not proposed because a direct reviewer need was not established, and the broad Cureus review was not needed once stronger evidence was available.

All checked reference PMIDs are added to the exposure ledger, with seven abstract exposures and two full-text exposures identified. Search-result incidental exposures are disclosed in RUNNING-LOG.md; no independent sample or reserve keys have been drawn. Unknown mappings remain pending; this does not complete reserve/exposure admission.

## Review decision and next step

Requested decision: accept C-47/C-48/C-49 and retain C-32/C-33 as background, giving23 seeds including3 without MeSH. After that decision, assemble and hash the frozen manifest (including required fields/diagnostics), complete exposure reconciliation and selection sizing/admission. Selection has not started.
