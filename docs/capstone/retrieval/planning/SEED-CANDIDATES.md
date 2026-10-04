# Seed candidates (P2): proposed for Quinton's review

**Status:** **draft 8**, 2026-10-03. **Working seed list approved by Quinton on 2026-10-03:** 21
seeds, or 22 if C-36 verifies in P5. He answered "Yes" to approving the search policy and the
21-seed working list. This is still a working list: P5 verifies identifiers and scope, and P6
freezes it. It applies Quinton's decisions of 2026-10-03:
- the section A2 working priority is accepted;
- all 11 section A O candidates are kept as reserves;
- family 2 is left to Claude's judgment.

Quinton also asked Claude to continue without Codex's direction. **Claude's own steps in draft 8**
are tagged "(Claude)":
- section A3, chained from C-10's reference list;
- moving the C-25 and C-36 factual scope checks to P5, against the local snapshot.

Draft 7 applied the corrections from Codex's outline-application
review (`../CODEX-P2-OUTLINE-APPLICATION-REVIEW-2026-09-28.md`): direct versus related-background
needs, a qualified N5.2 claim, the combined coverage table, and a revised section A2 priority.
Draft 6 applied Quinton's decisions of 2026-09-28: he adopted the
Codex decision-sheet review as the outline (`P2-DECISION-SHEET.md`, `RUNNING-LOG.md`).
**Not verified and not frozen.**
- **Decided:**
  - the corrected S-01 is approved;
  - the 16 R candidates are accepted **provisionally**, as a candidate subset and not a freeze;
  - P-02 and P-03 stay probes;
  - the negative controls stay;
  - **(2026-10-03)** the section A2 working priority is accepted (R = C-31, C-32 and C-33; C-36 to
    verify; C-34, C-35, C-37 and C-38 as reserves; C-39 left out), and the 11 section A O
    candidates are kept as reserves.
- **New in draft 6:**
  - the C-25 scope check: **not performed**, because its sources were rate-limited; its scope is
    unresolved (see its row);
  - section A2: WORKFLOW candidates chained from the designated source Goddard 2012 (superseded:
    the working priority was accepted on 2026-10-03).
- The Codex recommendation column records the earlier review.

**Protocol:** [`SEED-SET.md`](SEED-SET.md) (revision 7). Disclosure: `RUNNING-LOG.md`, entries
"P2 started", "P2 handback", "Codex P2 review received; exposure disclosures", "P2 revision 2
handback", "Decisions applied; C-25 check; Goddard chaining" and "Quinton's round-2 decisions; family
2 resolved by chaining" (2026-10-03).

**What changed from draft 2 (drafts 3-4):**
- **Eligibility.** Rule 10 is now a topic-and-use test (Codex R1). Six of the eight draft-2 probes
  were reassessed individually and are recall-eligible again, as C-25 to C-30. P-02 and P-03 remain
  probes, each with a substantive reason.
- **S-01.** The citation conflict is confirmed. A corrected candidate is proposed under rule 12, and
  its needs are reassessed (Codex R2).
- **C-06.** N1.3 is dropped, following Codex.
- **Coverage.** Recomputed in one authoritative table.
- **Priorities.** Rebalanced as Codex recommends:
  - C-02 to C-04 are optional;
  - detection papers are a balanced subset;
  - measurement and workflow come first.
- **IDs are never reused.** C-21 to C-24 (draft 1) are retired. The former P-01 and P-04 to P-08
  are now C-25 to C-30.

**Rules applied:**
- **Discovery by citation chaining, plus one designated source:**
  - the approved appendix v3.1 key references;
  - the PanTS, MSD and S-02 reference lists;
  - Cao 2023's reference list (second-level chaining);
  - Goddard 2012's reference list, a source Quinton designated under SEED-SET rule 1
    (section A2);
  - C-10's reference list (second-level chaining, section A3, 2026-10-03).
- **Metadata only, with one exception.** Claude read only reference-list metadata (titles,
  authors, venues, years, DOIs). The exception is the corrected S-01: it comes from an NLM page that
  showed Codex its abstract and MeSH (disclosed in `RUNNING-LOG.md`). Named metadata lookups are
  marked [Crossref], [OpenAlex] or [NLM via Codex]. No identifier was recalled from memory.
- **Every candidate is `unverified`** until P5 resolves it against the final local snapshot.
- **Needs** refer to the frozen `INFORMATION-NEEDS.md` v1. They are Claude's reading of each title
  (plus stated background knowledge), for Quinton to correct.
- **Title-only branches are a diagnostic column, not an eligibility test.** It shows v0 **with**
  the approved amendment A1-A3 (`SEARCH-AND-SELECTION.md` section 13), which changed only S-01's
  entry.

## A. Proposed PubMed candidates (count toward seed recall only if accepted and verified)

Priority is Claude's recommendation after Codex's review: **R** = recommended for the frozen set;
**O** = optional (drop first when trimming).

| ID | Citation (as given by the source; [lookup] where marked) | Identifier (per source) | Families / needs | Title-only branches (diagnostic) | Note | Source of knowledge | Priority | Codex review |
|---|---|---|---|---|---|---|---|---|
| S-01 | **Corrected candidate (rule 12; approved by Quinton, 2026-09-28):** Suman, G., Patra, A., Korfiatis, P., et al. (2021). Quality gaps in public pancreas imaging datasets: Implications & challenges for AI applications. *Pancreatology* 21(5):1001-1008. [NLM via Codex; Crossref]. **Original appendix citation, kept for provenance:** "Assessment of pancreatic ductal adenocarcinoma using CT imaging" (live-record conflict; the P5 outcome is pending) | PMID 33840636 (appendix; NLM record read by Codex); doi:10.1016/j.pan.2021.03.016 [NLM via Codex; Crossref] | 5, 4; N5.5, N5.6, N4.3 (reassessed from the corrected title; the old N1.1/N2.1 mapping is not carried over) | AI (via the `AI` token, A1) | Supports dataset-quality and label needs. Does not help WORKFLOW | Appendix v3.1 key references (identifier), corrected by the NLM record | R (accepted provisionally) | **Edit** as corrected; keep the conflict in the log |
| S-02 | Podină, Gheorghe, Constantin, et al. (2025). Artificial Intelligence in Pancreatic Imaging: A Systematic Review. *United European Gastroenterology Journal*. | PMID 39865461 (appendix; [OpenAlex] agrees); doi:10.1002/ueg2.12723 [Crossref] | 4; N4.1, N4.3, N4.6 | AI | CORE too if CT is in MeSH or abstract | Appendix v3.1 A6 example record | R | Keep (broad AI background) |
| C-01 | Zhang, L., Sanagapalli, S., Stoita, A. (2018). Challenges in diagnosis of pancreatic cancer. *World J Gastroenterol* 24(19):2047. | doi:10.3748/wjg.v24.i19.2047 (S-02 references) | 1; N1.1 | (none) | CORE if CT is in MeSH or abstract | PanTS ref. 65 **and** S-02 references (convergent) | R | Keep (general visibility/background) |
| C-02 | Toshima, F., Watanabe, R., Inoue, D., et al. (2021). CT abnormalities of the pancreas associated with the subsequent diagnosis of clinical stage I pancreatic ductal adenocarcinoma more than 1 year later: a case-control study. *AJR* 217(6):1353-1364. | doi:10.2214/AJR.21.26014 (from C-10's deposited reference list, 2026-10-03) | 1; N1.4, N1.1 | CORE |  | PanTS ref. 58 | O | Keep, optional for trimming (overlap with C-03, C-04) |
| C-03 | Singh, D. P., Sheedy, S., Goenka, A. H., et al. (2020). Computerized tomography scan in pre-diagnostic pancreatic ductal adenocarcinoma: stages of progression and potential benefits of early intervention: a retrospective study. *Pancreatology* 20(7):1495-1501. | doi:10.1016/j.pan.2020.07.410 (from C-10's deposited reference list, 2026-10-03) | 1; N1.4, N1.1 | (none) | "Computerized tomography" does not match `computed tomograph*`, and the title has no `CT` token. CORE only if CT is in MeSH or abstract | PanTS ref. 54 | O | Keep, optional for trimming (overlap with C-02, C-04) |
| C-04 | Konno, Y., Sugai, Y., Kanoto, M., et al. (2023). A retrospective preliminary study of intrapancreatic late enhancement as a noteworthy imaging finding in the early stages of pancreatic adenocarcinoma. *Eur Radiol* 33(7):5131-5141. | none given (citation match) | 1; N1.2, N1.4 | (none) | CORE if CT is in MeSH or abstract (the title names no modality) | PanTS ref. 31 | O | Keep, optional for trimming (overlap with C-02, C-03) |
| C-05 | LeBlanc, M., Kang, J., Costa, A. F. (2023). Can we rely on contrast-enhanced CT to identify pancreatic ductal adenocarcinoma? A population-based study in sensitivity and factors associated with false negatives. *Eur Radiol*. | doi:10.1007/s00330-023-09758-y (Cao 2023 references) | 1; N1.1, N1.2 | CORE |  | Cao 2023 ref. 32 | R | Keep (visibility/false-negative context) |
| C-06 | To'o, K. J., et al. (2005). Pancreatic and peripancreatic diseases mimicking primary pancreatic neoplasia. *RadioGraphics* 25:949-965. | doi:10.1148/rg.254045167 (Cao 2023 references; [Crossref] confirmed) | 3; N3.1 (N1.3 dropped on Codex review: mimics are not evidence about isoattenuating lesions) | (none) | CORE if CT is in MeSH or abstract | Cao 2023 ref. 28 | R | Keep; **edit**: drop N1.3, map N3.1 |
| C-07 | Hoogenboom, S. A., Bolan, C. W., Chuprin, A., et al. (2021). Pancreatic steatosis on computed tomography is an early imaging feature of pre-diagnostic pancreatic cancer: a preliminary study in overweight patients. *Pancreatology* 21(2):428-433. | none given (citation match) | 3, 1; N3.3, N1.4 | CORE |  | PanTS ref. 22 | R | Keep; needs provisional |
| C-08 | Chung, H. H., Lim, K. S., Park, J. K. (2022). Clinical clues of pre-symptomatic pancreatic ductal adenocarcinoma prior to its diagnosis: a retrospective review of CT scans and laboratory tests. *Clinics and Practice* 12(1):70-77. | none given (citation match) | 1; N1.4 | CORE |  | PanTS ref. 16 | O | Keep optional |
| C-09 | Chu, L. C., Goggins, M. G., Fishman, E. K. (2017). Diagnosis and detection of pancreatic cancer. *The Cancer Journal* 23(6):333-342. | none given (citation match) | 1; N1.1, N1.2 | (none) | CORE if CT is in MeSH or abstract | PanTS ref. 15 | O | Keep optional |
| C-10 | Khasawneh, et al. (2022). Volumetric Pancreas Segmentation on Computed Tomography: Accuracy and Efficiency of a Convolutional Neural Network Versus Manual Segmentation in 3D Slicer in the Context of Interreader Variability of Expert Radiologists. *J Comput Assist Tomogr*. [Crossref title] | doi:10.1097/RCT.0000000000001374 (S-02 references) | 2, 5, 4; N2.2, N5.3, N4.6 | CORE, AI, MEASURE | MEASURE via `manual segmentation` | S-02 references | R | **High-priority keep** |
| C-11 | Kawamoto, et al. (2023). Deep neural network-based segmentation of normal and abnormal pancreas on abdominal CT: evaluation of global and local accuracies. *Abdominal Radiology*. [Crossref title] | doi:10.1007/s00261-023-04122-6 (S-02 references) | 4; N4.1, N4.2, N4.6 | CORE, AI |  | S-02 references | R | Keep (segmentation) |
| C-12 | Roth, et al. (2018). Spatial aggregation of holistically-nested convolutional neural networks for automated pancreas localization and segmentation. *Medical Image Analysis*. [Crossref title] | doi:10.1016/j.media.2018.01.006 (S-02 references) | 4; N4.5, N4.6 | AI | CORE too if CT is in MeSH or abstract | S-02 references | R | Keep (localization/segmentation) |
| C-13 | Cao, K., Xia, Y., Yao, J., et al. (2023). Large-scale pancreatic cancer detection via non-contrast CT and deep learning. *Nature Medicine* 29(12):3033-3043. | doi:10.1038/s41591-023-02640-w (S-02 references; [Crossref]) | 4; N4.3, N4.6, N4.1 | CORE, AI |  | PanTS ref. 11 **and** S-02 references (convergent) | R | Keep; balanced subset |
| C-14 | Liu, K.-L., et al. (2020). Deep learning to distinguish pancreatic cancer tissue from non-cancerous pancreatic tissue: a retrospective study with cross-racial external validation. *Lancet Digit Health* 2:303-313. | doi:10.1016/S2589-7500(20)30078-9 (Cao 2023 references; [Crossref] confirmed) | 4; N4.3 | AI | CORE too if CT is in MeSH or abstract | Cao 2023 ref. 31 | R | Keep; balanced subset |
| C-15 | Park, H. J., et al. (2023). Deep learning-based detection of solid and cystic pancreatic neoplasms at contrast-enhanced CT. *Radiology* 306:140-149. | doi:10.1148/radiol.220171 (Cao 2023 references) | 4; N4.1, N4.2, N4.6 | CORE, AI |  | Cao 2023 ref. 30 **and** S-02 references (convergent) | O | Keep; balanced subset |
| C-16 | Chen, et al. (2023). Pancreatic Cancer Detection on CT Scans with Deep Learning: A Nationwide Population-based Study. *Radiology*. [Crossref title] | doi:10.1148/radiol.220152 (S-02 references) | 4; N4.3, N4.6 | CORE, AI |  | S-02 references | O | Keep; balanced subset |
| C-17 | Mukherjee, S., Patra, A., Khasawneh, H., et al. (2022). Radiomics-based machine-learning models can detect pancreatic cancer on prediagnostic computed tomography scans at a substantial lead time before clinical diagnosis. *Gastroenterology* 163(5):1435-1446. | doi:10.1053/j.gastro.2022.06.066 (S-02 references; [Crossref] title) | 4, 1; N4.2, N1.4 | CORE, AI |  | PanTS ref. 48 **and** S-02 references (convergent) | R | Keep; balanced subset |
| C-18 | Abel, L., Wasserthal, J., Weikert, T., et al. (2021). Automated detection of pancreatic cystic lesions on CT using deep learning. *Diagnostics* 11(5). | doi:10.3390/diagnostics11050901 (PanTS; [Crossref] confirmed) | 4; N4.1, N4.2 | CORE, AI |  | PanTS ref. 1 | O | Keep optional |
| C-19 | Man, et al. (2019). Deep Q Learning Driven CT Pancreas Segmentation With Geometry-Aware U-Net. *IEEE Trans Med Imaging*. [Crossref title] | doi:10.1109/TMI.2019.2911588 (S-02 references) | 4; N4.5, N4.6 | CORE, AI | AI via `segmentation` and `U-Net` ("Deep Q Learning" is not the phrase `deep learning`) | S-02 references | O | Keep optional |
| C-20 | Zhang, et al. (2021). A deep learning framework for pancreas segmentation with multi-atlas registration and 3D level-set. *Medical Image Analysis*. [Crossref title] | doi:10.1016/j.media.2020.101884 (S-02 references) | 4; N4.6 | AI | CORE too if CT is in MeSH or abstract | S-02 references | O | Keep optional |
| C-25 | Joskowicz, L., Cohen, D., Caplan, N., Sosna, J. (2019). Inter-observer variability of manual contour delineation of structures in CT. *Eur Radiol* 29:1391-1399. (draft 2: P-01) | doi:10.1007/s00330-018-5695-5 (**not per source**: from a locating web search result; P5 must confirm it) | 2; N2.2 | (none) | **Scope check 2026-09-28: not performed; scope unresolved.** The authorized abstract check could not run: Crossref returned HTTP 429, and the fetch proxy rate-limited the Springer page with the instruction not to refetch that page. No abstract was read, so there was no abstract exposure; the article URL and the other search-result titles were seen, and are logged in the exposure list. Nothing is inferred about pancreas coverage. **2026-10-03:** an official E-utilities DOI lookup was refused by the fetch tool (robots.txt), and was not worked around. Its factual scope check moves to **P5**, which reads its record and abstract from the local snapshot and logs the exposure. Family 2 no longer depends on C-25 (see C-40). Rule 10 needs contour-review methods that cover the pancreas, and the title names only "structures in CT". Eligible only if a factual check of its abstract or record shows that it covers the pancreas **and** supports N2.2; otherwise it becomes a probe. If eligible, a miss is reported as a coverage limitation for N2.2 | MSD ref. 21 | R if its scope is accepted (pending) | Reassess under R1: measurement usefulness |
| C-26 | Wasserthal, J., Breit, H.-C., Meyer, M. T., et al. (2023). TotalSegmentator: robust segmentation of 104 anatomic structures in CT images. *Radiology: Artificial Intelligence* 5(5). (draft 2: P-04) | none given (citation match) | 4, 5; N4.3, N5.5 | (none) | Multi-organ CT model (Claude's background knowledge: it includes the pancreas; Quinton to confirm). Depends on abstract or MeSH | PanTS ref. 61 | O | Reassess under R1 |
| C-27 | Ma, J., Zhang, Y., Gu, S., et al. (2021). AbdomenCT-1K: Is abdominal organ segmentation a solved problem? *IEEE Trans Pattern Anal Mach Intell*. (draft 2: P-05) | none given (citation match) | 5, 4; N5.5, N4.3 | (none) | Multi-organ dataset (background knowledge: it includes the pancreas). `AbdomenCT` is one token, so no `CT` match. Depends on abstract or MeSH | PanTS ref. 43 | R | Reassess under R1: dataset provenance |
| C-28 | Luo, X., Liao, W., Xiao, J., et al. (2022). WORD: A large scale dataset, benchmark and clinical applicable study for abdominal organ segmentation from CT image. *Medical Image Analysis* 102642. (draft 2: P-06) | none given (citation match) | 5; N5.4, N5.5 | (none) | **Scope basis:** a multi-organ abdominal CT dataset (Claude's background knowledge: it includes the pancreas; Quinton to confirm). Diagnostic: C and A match on the title; P only through the abstract or MeSH | PanTS ref. 41 | R | Reassess under R1: annotation/dataset provenance |
| C-29 | Li, W., Qu, C., Chen, X., et al. (2024). AbdomenAtlas: A large-scale, detailed-annotated, & multi-center dataset for efficient transfer learning and open algorithmic benchmarking. *Medical Image Analysis* 103285. (draft 2: P-07) | none given (citation match) | 5; N5.3, N5.5 | (none) | **Scope basis:** a multi-organ abdominal CT annotation dataset (background knowledge: it includes the pancreas; Quinton to confirm). Diagnostic: M matches on the title (`annotat*`); P only through the abstract or MeSH | PanTS ref. 34 | R | Reassess under R1: annotation/dataset provenance |
| C-30 | Antonelli, M., Reinke, A., Bakas, S., et al. (2022). The Medical Segmentation Decathlon. *Nature Communications* 13:4128. (draft 2: P-08) | doi:10.1038/s41467-022-30695-9 (appendix) | 5, 4; N5.5, N4.6 | (none) | **Scope basis:** a segmentation benchmark with a pancreas task (background knowledge; cited in the approved appendix as a PROWL data source; Quinton to confirm). Diagnostic: A matches on the title; P only through the abstract or MeSH | Appendix v3.1 key references; PanTS ref. 6 | R | Reassess under R1: dataset provenance |

**Counts (section A):**
- **R = 16 (accepted provisionally by Quinton, 2026-09-28):** S-01, S-02, C-01, C-05, C-06, C-07, C-10, C-11, C-12, C-13, C-14, C-17, C-27, C-28,
  C-29 and C-30. **C-25 is R if its scope is accepted**, which makes 17. It was the only possible
  second family-2 seed before section A3; C-40 now provides one.
- **O = 11:** C-02, C-03, C-04, C-08, C-09, C-15, C-16, C-18, C-19, C-20 and C-26.
- **Total:** 28 candidates in section A: 27 with stated scope bases, plus one scope-pending
  candidate (C-25). Section A2 adds 9 WORKFLOW candidates, and section A3 adds 7. All are subject to Quinton's review and P5 verification. Freeze counts use the
  actual accepted, verified candidates, not this provisional total. Rule 5 allows at most 25 frozen seeds. Accepting every section A
  candidate would require trimming at least 3. With sections A2 and A3 as well (44 in total), it
  would require trimming at least 19.

**Detection papers (C-13 to C-17):** including them authorizes **no** subtype or diagnostic
questions (Codex).

**Dependence on MeSH or abstract (diagnostic).** Eleven of the 28 have an empty title-only set (C-01, C-03, C-04, C-06, C-09, C-25 and C-26 to
C-30).
Six of those are in the R set: C-01, C-06, C-27, C-28, C-29 and C-30 (S-01 now has AI under
A1). Most
are dataset-method or non-pancreas-specific works. If they miss, that is the protocol working as
designed: it shows that the policy's pancreas anchoring misses that literature, and the remedy is a
recorded policy revision, not reclassifying seeds.

**Bar arithmetic (information only; the set size must follow scope, coverage and verification,
never the bar):**
- 16 seeds: 15/16 = 93.8% passes, 14/16 = 87.5% fails, so at most one miss.
- 17 seeds (with C-25): 16/17 = 94.1% passes, 15/17 = 88.2% fails, so at most one miss.
- 25 seeds (the rule 5 maximum): 23/25 = 92.0% passes, 22/25 = 88.0% fails, so at most two misses.

## A2. WORKFLOW candidates (designated source: Goddard 2012; working priority accepted by Quinton, 2026-10-03)

- **Source and route.** These come from the reference list of Goddard, Roudsari and Wyatt (2012),
  *JAMIA* 19(1):121-127, doi:10.1136/amiajnl-2011-000089. Quinton designated it on 2026-09-28 under
  the SEED-SET rule 1 designated-source route; it was originally search-suggested by Codex.
- **What was read.** Its Crossref-deposited reference list (75 entries, mostly DOIs). Titles were
  looked up in Crossref, metadata only and no abstracts, for **9** imaging-related DOIs: refs. 16,
  33, 34, 36, 37, 38, 39, 42 and 54.
  - Ref. 53's title (C-38) was already in the deposited list.
  - Ref. 42 (Moberg 2001, "Computed assisted detection of interval breast cancers", *Eur J Radiol*)
    was looked up but **not proposed**: from its title, it audits the detection system rather than
    reader behaviour.
- **The review itself is not a candidate** (not separately decided).
- **Chosen for** general imaging-AI review and workflow evidence (rule 10, third scope item):
  human readers using computer output, including incorrect output.
- **Title-only branches:** none of these titles contains a W term. W has no MeSH rule, so these
  papers reach WORKFLOW only through W terms in their abstracts or keywords, and WORKFLOW's narrow W
  list may miss them. CORE, AI and MEASURE need P, which these non-pancreas papers are not expected
  to have. That is
  reported as a coverage finding, not tuned (rule 11).
- **Family 2 is not helped:** none of these is a measurement or contour-review paper.
- **Needs mapping (revised after Codex's outline-application review).** The "Families / needs" column
  now separates **direct** needs from **related background**.
  - **N5.2 (automation bias):** C-31 is a strong direct candidate, since its topic is incorrect CAD
    output. C-36 is a plausible fit (cueing environments) that still needs scope verification.
  - C-32, C-33 and C-35's titles show changed reader performance, which is **not** evidence of
    over-trust. They do not establish N5.2.
  - **N5.1 (errors human review can catch in contours) stays directly uncovered.** These are
    detection reader studies, not contour review, so N5.1 is recorded only as related background.
    The frozen need is not reinterpreted to fit them.
  - A candidate whose direct need is "to verify" must have a frozen need confirmed before any seed
    freeze (rule 10).

| ID | Citation (as given by the source; [Crossref] title) | Identifier (per source) | Families / needs | Title-only branches (diagnostic) | Note | Source | Priority (Claude, revised to follow Codex) | Codex review (recommendation, not a decision) |
|---|---|---|---|---|---|---|---|---|
| C-31 | Alberdi, et al. (2004). Effects of incorrect computer-aided detection (CAD) output on human decision-making in mammography. *Academic Radiology*. [Crossref] | doi:10.1016/j.acra.2004.05.012 | 5; direct: N5.2; related background: N5.1 | (none) | The most direct automation-bias evidence found (incorrect AI output) | Goddard ref. 16 | R (high priority) | Keep, high priority. Strong N5.2 candidate; N5.1 is related background only |
| C-32 | Fenton, et al. (2007). Influence of Computer-Aided Detection on Performance of Screening Mammography. *N Engl J Med*. [Crossref] | doi:10.1056/NEJMoa066099 | 5; direct: to verify; related background: N5.1, N5.2 | (none) | Large-scale effect of computer aid on readers | Goddard ref. 34 | R (provisional) | Keep provisionally. Reader-performance context; the title does not prove automation bias or contour-review benefit |
| C-33 | Petrick, et al. (2008). CT Colonography with Computer-aided Detection as a Second Reader: Observer Performance Study. *Radiology*. [Crossref] | doi:10.1148/radiol.2453062161 | 5; direct: to verify; related background: N5.1 | (none) | CT reader-with-aid study. A and IMG match on the title; W only through the abstract or keywords | Goddard ref. 39 | R (provisional) | Keep provisionally. CT second-reader context; direct N5.1 stays open; confirm a frozen need before freeze |
| C-34 | Walsham, et al. (2008). The Use of Computer-Aided Detection for the Assessment of Pulmonary Arterial Filling Defects at Computed Tomographic Angiography. *J Comput Assist Tomogr*. [Crossref] | doi:10.1097/RCT.0b013e31815b3ed0 | 5; direct: to verify; related background: N5.1 | (none) | CT reader-with-aid study. A and IMG match on the title | Goddard ref. 54 | Reserve | Reserve. Detection-assistance background |
| C-35 | Li, et al. (2006). Improving Radiologists' Recommendations With Computer-Aided Diagnosis for Management of Small Nodules Detected by CT. *Academic Radiology*. [Crossref] | doi:10.1016/j.acra.2006.04.010 | 5; direct: to verify; related background: N5.1 | (none) | CT reader-with-aid study | Goddard ref. 33 | Reserve | Move to reserve. The title centres on management recommendations, a weaker fit for contour review |
| C-36 | Zheng, et al. (2001). Soft-Copy Mammographic Readings with Different Computer-assisted Detection Cuing Environments: Preliminary Findings. *Radiology*. [Crossref] | doi:10.1148/radiol.2213010308 | 5; direct: N5.2 (plausible; to verify); related background: N5.1 | (none) | Interface cueing and its effect on readers (N5.2 is tied to interface and workflow) | Goddard ref. 36 | Verify scope first | Prioritize for scope verification (a plausible N5.2 fit), ahead of C-35 |
| C-37 | Hadjiiski, et al. (2004). Improvement in Radiologists' Characterization of Malignant and Benign Breast Masses on Serial Mammograms with Computer-aided Diagnosis: An ROC Study. *Radiology*. [Crossref] | doi:10.1148/radiol.2331030432 | 5; direct: to verify; related background: N5.1 | (none) | Reader-with-aid ROC study | Goddard ref. 37 | Reserve | Reserve. Characterization/ROC topic is a weaker fit |
| C-38 | Marten, K., Seyfarth, T., Auer, F., et al. (2004). Computer-assisted detection of pulmonary nodules: performance evaluation of an expert knowledge-based detection system in consensus reading with experienced and inexperienced chest radiologists. *Eur Radiol* 14:1930-1938. | doi:10.1007/s00330-004-2389-y (Goddard reference list) | 5; direct: to verify; related background: N5.1 | (none) | Reader experience and CAD | Goddard ref. 53 | Reserve | Reserve. Reader-experience background only |
| C-39 | Helvie, et al. (2004). Sensitivity of Noncommercial Computer-aided Detection System for Mammographic Breast Cancer Detection: Pilot Clinical Trial. *Radiology*. [Crossref] | doi:10.1148/radiol.2311030429 | 5; direct: to verify; related background: N5.1 | (none) | A weaker fit (system sensitivity rather than reader behaviour) | Goddard ref. 38 | Not in the initial subset | Leave out of the initial subset; keep its discovery record |

**Working priority, accepted by Quinton on 2026-10-03:**
- **R:** C-31, C-32 and C-33.
- **Verify scope first:** C-36. (Claude, 2026-10-03: its factual scope check happens in P5, against
  the local snapshot.)
- **Reserve:** C-34, C-35, C-37 and C-38.
- **Not in the initial subset:** C-39.

With the 16 section A R candidates, that is 19 R, or 20 if C-36 is verified. With section A3's
proposed R it is 21 or 22 (see section A3). Either is within
15-25. The set size follows scope and coverage, never the bar.
- **Not looked up** (unread; not candidates): Goddard refs. 35, 40 and 43 (imaging-venue DOIs),
  and every non-imaging reference.

## A3. Candidates chained from C-10's reference list (second-level chaining, 2026-10-03)

- **Route:** second-level chaining (SEED-SET rule 1) from provisionally accepted candidate C-10 (Khasawneh 2022,
  doi:10.1097/RCT.0000000000001374). Claude chose this route for family 2 under Quinton's
  2026-10-03 instruction.
- **Read:** C-10's Crossref-deposited reference list, with titles, venues and years as deposited.
  It has 32 entries; their keys run from bib1 to bib34, with bib13 and bib18 absent. No abstracts.
- **Convergence found:**
  - the corrected S-01 (C-10 bib. 11);
  - C-02 Toshima (bib. 30) and C-03 Singh (bib. 32), whose DOIs are now recorded;
  - C-40's DOI also appears in S-02's reference list;
  - P-03 (ITK-SNAP) is bib. 17.
- **Coverage warning (reported, not tuned; rule 11):** C-40's title says "intra-reader and
  inter-reader". Block M has no `reader` variant, so M does not match its title. It still enters as
  CORE and AI.

| ID | Citation (as deposited in C-10's reference list) | Identifier (per source) | Families / needs | Title-only branches (v0 with A1-A3) | Note | Priority (Claude) |
|---|---|---|---|---|---|---|
| C-40 | (2021). Two-stage deep learning model for fully automated pancreas segmentation on computed tomography: comparison with intra-reader and inter-reader reliability at full and reduced radiation dose on an external dataset. *Med Phys* 48. | doi:10.1002/mp.14782 (C-10 bib. 12; also in S-02's references) | 2, 4; direct: N2.2; related: N4.6 | CORE, AI | Pancreas intra- and inter-reader reliability on CT. **Restores the family-2 minimum** with C-10 | **R** |
| C-41 | (2020). Development of a volumetric pancreas segmentation CT dataset for AI applications through trained technologists: a study during the COVID 19 containment phase. *Abdom Radiol (NY)* 45. | doi:10.1007/s00261-020-02741-x (C-10 bib. 7) | 5, 2; direct: N5.4; related: N2.2, N2.4 | CORE, AI | How a pancreas contour dataset was produced and checked | Reserve |
| C-42 | (2021). Determining age and sex-specific distribution of pancreatic whole-gland CT attenuation using artificial intelligence aided image segmentation: associations with body composition and pancreatic cancer risk. *Pancreatology* 21. | doi:10.1016/j.pan.2021.08.004 (C-10 bib. 4) | 3; direct: N3.3 | CORE, AI | Normal pancreas appearance by age and sex on CT | **R** |
| C-43 | (2014). Differences in pancreatic volume, fat content, and fat density measured by multidetector-row computed tomography according to the duration of diabetes. *Acta Diabetol* 51. | doi:10.1007/s00592-014-0581-3 (C-10 bib. 33) | 3; direct: N3.3 | CORE | Pancreas fat and volume variation on CT | Reserve |
| C-44 | (2018). Advances in pancreatic CT imaging. *AJR Am J Roentgenol* 211. | doi:10.2214/AJR.17.18665 (C-10 bib. 23) | 1; direct: to verify (N1.2, N1.5 plausible) | CORE | A protocol review; may address phase and slice thickness | Reserve |
| C-45 | (2009). Pancreatic duct evaluation: accuracy of portal venous phase 64 MDCT. *Abdom Imaging* 34. | doi:10.1007/s00261-008-9396-4 (C-10 bib. 10) | 1, 3; direct: N1.2; related: N3.4 | CORE | Duct visibility by phase. Not an annotation protocol, so N3.4 is related only | Reserve |
| C-46 | (2020). Technical and clinical factors affecting success rate of a deep learning method for pancreas segmentation on CT. *Acad Radiol* 27. | doi:10.1016/j.acra.2019.08.014 (C-10 bib. 6) | 4, 1; direct: N4.2; related: N1.5 | CORE, AI | Factors linked to segmentation failure | Reserve |

**Section A3 priority:** R = C-40 and C-42; the other five are reserves.
- Not proposed from this list: radiomics, diabetes-treatment, drug-toxicity and pediatric papers;
  general tools (3D Slicer, STAPLE); and a pancreas-segmentation systematic review (bib. 8), held
  back to avoid over-weighting family 4.

**Working recommended set** (provisional; not a freeze):
- section A R: 16;
- section A2 R: C-31, C-32 and C-33;
- section A3 R: C-40 and C-42.

That is **21**, or **22 if C-36 verifies**. Both are within 15-25.
- **Bar arithmetic (information only):** 21 seeds: 19/21 = 90.5% passes, 18/21 = 85.7% fails, so at
  most two misses. 22 seeds: 20/22 = 90.9% passes, 19/22 = 86.4% fails, so at most two misses.

## B. Scope probes (reported, not counted)

Each is judged outside the Tier 1 topic-and-use scope (rule 10), with the reason stated.

| ID | Citation (as given by the source) | Identifier (per source) | Reason it is out of scope | Title-only branches | Source |
|---|---|---|---|---|---|
| P-02 | Isensee, F., Jaeger, P. F., Kohl, S. A., et al. (2021). nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. *Nature Methods* 18:203-211. | doi:10.1038/s41592-020-01008-z (Cao 2023 references) | A model-architecture and tooling paper. It answers no reviewer need directly, and pancreas benchmark results are represented at the dataset level by C-30 | (none) | PanTS ref. 24; MSD ref. 8; Cao 2023 ref. 23 |
| P-03 | Yushkevich, P. A., et al. (2006). User-guided 3D active contour segmentation of anatomical structures: significantly improved efficiency and reliability. *NeuroImage* 31:1116-1128. | doi:10.1016/j.neuroimage.2006.01.015 (Cao 2023 references) | A general interactive segmentation-tool paper in a neuroimaging venue. It is not about CT and not AI-assisted, and it supports N5.3 only by analogy | (none) | Cao 2023 ref. 50 |

The former P-01 and P-04 to P-08 were reassessed individually and are now C-25 to C-30. Codex
judged P-02 a reasonable probe, "unless a concrete approved reviewer need establishes intended
Tier-1 usefulness". Quinton kept both P-02 and P-03 as probes (2026-09-28, decision-sheet item 8).

## C. References outside PubMed seed recall (rule 7)

These were used for chaining, or are relevant but probably not PubMed-indexed. If P5 finds that a
DOI maps to a PMID in the local snapshot, **only Quinton** may promote the item, to section A or
section B under rule 10's topic-and-use test. A promotion after the freeze is reported as a late
addition.

| Reference | Why listed |
|---|---|
| Li, W., et al. (2025). PanTS. arXiv:2507.01291 | Chaining source; N5.5 |
| Alves, N., et al. (2024). PANORAMA study protocol. Zenodo doi:10.5281/zenodo.10599559 | Chaining source (reference list not yet read); N5.5 |
| Qu, C., et al. (2023). AbdomenAtlas-8K: annotating 8,000 abdominal CT volumes for multi-organ segmentation in three weeks. NeurIPS | N5.3 (AI-assisted annotation) |
| Zhang, T., et al. (2024). Leveraging AI predicted and expert revised annotations in interactive segmentation: continual tuning or full training? IEEE ISBI | N5.3 |
| Bassi, P. R. A. S., et al. (2024). Label critic: design data before models. arXiv:2411.02753 | N5.1, N5.4 |
| Li, W., et al. (2025). ScaleMAI. arXiv:2501.03410 | N5.3, N5.4 |
| Xia, Y., et al. (2022). The FELIX project: deep networks to detect pancreatic neoplasms. Preprint, doi:10.1101/2022.09.24.22280071 | N4.1, N4.6 |
| Xia, Y., et al. (2021). Effective pancreatic cancer screening on non-contrast CT scans via anatomy-aware transformers. MICCAI, doi:10.1007/978-3-030-87240-3_25 | N4.6 |
| Roth, H. R., et al. (2015). DeepOrgan: multi-level deep convolutional networks for automated pancreas segmentation. MICCAI | N4.5, N4.6 |
| Simpson, A. L., et al. (2019). A large annotated medical image dataset for the development and evaluation of segmentation algorithms. arXiv:1902.09063 | N5.5 |

## D. Optional negative seeds (rule 8)

Each is outside the Tier 1 topic scope for a stated topic reason, and is also predicted to fail the
candidate logic. P6 reports the result either way. **A surprising selection is a finding** about the
policy, not a reason to drop the control (Codex).

| ID | Citation (as given by the source) | Identifier (per source) | Why it should fail | Source |
|---|---|---|---|---|
| NEG-01 | Esteva, A., et al. (2017). Dermatologist-level classification of skin cancer with deep neural networks. *Nature* 542:115-118. | doi:10.1038/nature21056 (Cao 2023 references) | **Topic:** dermatology photographs, not pancreas or CT review. **Predicted:** no P block, no IMG context | Cao 2023 ref. 12 |
| NEG-02 | Liang, S., et al. (2019). Deep-learning-based detection and segmentation of organs at risk in nasopharyngeal carcinoma computed tomographic images for radiotherapy planning. *Eur Radiol* 29:1961-1967. | none given (citation match) | **Topic:** head-and-neck radiotherapy planning, not pancreas contour review. **Predicted:** no P block; W terms not expected | MSD ref. 5 |
| NEG-03 | Ardila, D., et al. (2019). End-to-end lung cancer screening with three-dimensional deep learning on low-dose chest computed tomography. *Nat Med* 25:954-961. | doi:10.1038/s41591-019-0447-x (Cao 2023 references) | **Topic:** lung-cancer screening, not pancreas. **Predicted:** no P block. If WORKFLOW selects it, that measures how broad WORKFLOW is | Cao 2023 ref. 14 |

## Coverage (the one authoritative table; the combined pool, sections A, A2 and A3)

**Counts by status:**
- **accepted provisionally (Quinton):** the 16 section A R candidates, and C-31, C-32 and C-33
  (section A2);
- **reserves (Quinton, 2026-10-03):** the 11 section A O candidates, and C-34, C-35, C-37 and C-38;
- **proposed (Claude, 2026-10-03):** C-40 to C-46 (section A3; R: C-40 and C-42);
- **to verify in P5:** C-25 and C-36;
- **left out of the initial subset:** C-39;
- **verified or frozen:** none (P5 and P6).

The requirement is 15-25 frozen seeds and at least two per family, with meaningful coverage. Not
every need must have its own seed (Codex).

| Family | All candidates | R set | Assessment |
|---|---|---|---|
| 1 CT appearance | C-01 to C-05, C-07 to C-09, C-17, C-44, C-45, C-46 | C-01, C-05, C-07, C-17 | Adequate. N1.3 is uncovered. N1.5 is only "to verify" (C-44) or related (C-46) |
| 2 Measurement and contour review | C-10, C-40, C-41 (related), C-25 (to verify in P5) | C-10, C-40 | **Minimum met (2) in the working set, but fragile.** It depends on C-40, which is proposed, and on both C-10 and C-40 passing P5. N2.1, N2.3 and N2.4 are directly uncovered |
| 3 Anatomy context | C-06, C-07, C-42, C-43, C-45 (related) | C-06, C-07, C-42 | Strengthened (3 in R). N3.2 and N3.4 are directly uncovered |
| 4 AI limitations | S-01, S-02, C-10 to C-20, C-26, C-27, C-30, C-40, C-46 | S-01, S-02, C-10 to C-14, C-17, C-27, C-30, C-40 | Good. N4.4 is uncovered |
| 5 Review workflow | S-01, C-10, C-26 to C-30, C-31 to C-39, C-41 | S-01, C-10, C-27 to C-30, C-31, C-32, C-33 | Minimum met. **Direct** N5.2 coverage rests on C-31 (and C-36 if verified). **N5.1 stays directly uncovered**; the section A2 links to it are related background only. WORKFLOW-type papers exist now, but none reaches WORKFLOW on its title |

**Needs with no direct candidate in the combined pool: 9 of 25.** Section A2 adds N5.2 (C-31).
Section A3 adds direct support for needs that were already covered (N2.2, N3.3, N4.2, N5.4), and
N1.2 again. It adds **no** previously uncovered need: N1.5 (C-44) is only "to verify".
**N5.1 stays open.** Related-background and "to verify" links do not count as coverage.

| Family | Needs |
|---|---|
| 1 | N1.3, N1.5 |
| 2 | N2.1, N2.3, N2.4 |
| 3 | N3.2, N3.4 |
| 4 | N4.4 |
| 5 | N5.1 (N5.2 was uncovered before section A2; C-31 now covers it directly) |

This supersedes draft 2's "eleven" and SEED-SET revision 5's "nine".
- N5.6 is covered **only** by the corrected S-01 (approved 2026-09-28).
- N2.2 is covered by C-10 and C-40 (proposed), and by C-25 only if its scope is accepted.

| Check | Status |
|---|---|
| Missing-MeSH condition (rule 6) | Unknown until P5. The proposed rule 6 addition still stands |
| WORKFLOW branch | Section A2 provides WORKFLOW-type candidates. Whether v0 reaches them depends on W terms in their abstracts, which the P6 run will show |

## Remaining decisions for Quinton (draft 8)

Decided on 2026-10-03: the section A2 priority and the O candidates kept as reserves. Quinton left
family 2 to Claude. Claude's judgment: C-40 restores the minimum, and C-25 is checked in P5.

1. **Section A3** (C-40 to C-46): **approved on 2026-10-03** as part of the 21-seed working list
   (C-40 and C-42 as R; the other five as reserves).
2. **PANORAMA protocol PDF** (run record P): optional. The PANORAMA **dataset** (CT batches and
   labels) was acquired in September, but the protocol document is a separate Zenodo record (10599559)
   and is **not** on disk. Its reference list could add family 2 and 3 candidates (annotation
   protocol). It needs Quinton's signature as a download.

**Still open before any freeze** (P5 and P6):
- 15-25 accepted seeds, at least two per family;
- the missing-MeSH check;
- P5 identifier verification;
- the C-25 and C-36 factual scope checks (local);
- the exposure ledger.

The 90% bar is unchanged.
