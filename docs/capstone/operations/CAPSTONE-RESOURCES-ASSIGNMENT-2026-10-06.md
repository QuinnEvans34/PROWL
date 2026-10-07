# Capstone Resources assignment

Quinton supplied the assignment and selected the balanced set on October 6, 2026:
**PanTS + nnU-Net + Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**.
This approves the research-resource selection and drafting, not new model or retrieval execution.
The preceding Capstone Setup assignment is complete and submitted by Quinton's confirmation.

## Required submission

- Three distinct credible resources directly related to PROWL.
- A complete reference for each: title, authors/organization, available publication date and link.
- One summary of approximately 3–5 sentences per resource, covering content, project relevance
  and anticipated application/benefit.
- One compiled Word, PDF or Google Doc. Use **QEvans_CapstoneResearch.docx** for the Word draft.
  The required filename is CapstoneResearch even though the assignment title is Capstone Resources.
- Each resource and summary is worth 10 points, for 30 total.
- Due text: Wednesday by 11:59 pm. Working date: October 7, 2026; confirm the LMS's exact date/time
  zone. Availability through October 21 is a separate date. The detailed submission instructions
  require a compiled document despite the generic text-entry/file-upload header.

## Source selection and verification

The approved proposal v3.8 and appendix v3.1 were read without modification and match their
recorded SHA-256 values in references/governance/APPROVED-SOURCES.md. The appendix's existing
key references include PanTS, PANORAMA, the Medical Segmentation Decathlon and Suman's pancreatic
CT study. PanTS is reused; nnU-Net and RAG add distinct method and retrieval coverage. PANORAMA
was discussed as an alternative and is not a fourth resource in the compiled submission.

| Selected resource | Verified publication | Intended PROWL use | Interpretation limit |
|---|---|---|---|
| PanTS | Li and colleagues, NeurIPS 2025, volume 38, Datasets and Benchmarks Track; DOI 10.52202/085713-1065 | Annotation meaning/provenance and overlap/detection evaluation | Published dataset findings do not establish results for PROWL's current small engineering cohort. |
| nnU-Net | Isensee, Jaeger, Kohl, Petersen and Maier-Hein; Nature Methods 18, 203–211 (2021); DOI 10.1038/s41592-020-01008-z | Review MONAI preprocessing and design controlled segmentation comparisons | A resource selection does not adopt the nnU-Net implementation or authorize a framework change/run. |
| RAG | Lewis and colleagues; NeurIPS 2020, volume 33 | Literature passage retrieval, citation identity and support evaluation | Original experiments are general NLP/Wikipedia; biomedical reliability, citation correctness and refusal need PROWL's own checks. |

Use the author list attached to the chosen version. PanTS's published proceedings list 16 authors;
the earlier arXiv version lists 18. The draft cites the proceedings version. nnU-Net's publisher
records first online publication December 7, 2020 and the journal issue year 2021; the reference
uses the conventional issue year 2021. Its full publisher text requires access; the verified
publisher abstract and author preprint provide the configuration overview used here. Two BibTeX
fetches were unsupported by the web reader; title, authors, venue/year and links were independently
available on the primary publication pages.

Primary sources checked October 6:

- [PanTS published paper](https://proceedings.neurips.cc/paper_files/paper/2025/hash/2dc24f4adc257251b2f3929c67ec1e3a-Abstract-Datasets_and_Benchmarks_Track.html)
  and [open preprint text](https://arxiv.org/html/2507.01291v1).
- [nnU-Net publisher record and abstract](https://www.nature.com/articles/s41592-020-01008-z)
  and [author preprint](https://arxiv.org/abs/1904.08128).
- [RAG proceedings paper](https://papers.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html)
  and [author preprint](https://arxiv.org/abs/2005.11401).
- Alternative only: [PANORAMA study protocol](https://zenodo.org/records/10599559), January 31, 2024.

## Draft and next review

The compiled review draft is saved as
`docs/assignments/capstone-resources/QEvans_CapstoneResearch.docx`.
All three references and their hyperlinks were checked against the authoring source; each resource
has four summary sentences. Both pages were rendered and visually reviewed: references and
summaries are readable, with no clipped text or split summaries. The required filename was checked.
Draft wording uses intended application rather than
claiming an unperformed implementation or a demonstrated model improvement. The editable source
and QA evidence, including the final DOCX hash in `verification.json`, are local/ignored under
`outputs/prowl/CAPSTONE-RESOURCES-20261006/`.

Next: review each summary with Quinton for understanding, accurate intended use and his voice;
verify the exact LMS deadline; then Quinton submits the compiled document and retains confirmation.
No assignment submission, instructor message, Git commit/push, scientific run, corpus acquisition
or Claude-owned source change is included in this work.
