# External CT evaluation cohort screening — 6 November 2026

**Result: a practical public candidate exists, but no screened cohort is yet cleared for an unseen-patient claim.** Prioritize **PDAC-TAGS** for bounded admission work. Its public repository is accessible without contacting researchers; its public metadata does not establish separation from all upstream and PROWL exposures. Access and independence are separate decisions.

This is a metadata-only extension of [09 — clearance follow-up](09_clearance_followup.md), not a new experiment. No clinical archive, CT, mask, model prediction or protected PROWL test image/label was downloaded or opened during this screen. Author drafts remain local. No training or GPU job was started, and the supplied outline's no-commit instruction remains in force.

## Recommended candidate: PDAC-TAGS

The [publisher's OSF project](https://osf.io/g6rv5/) describes 500 contrast-enhanced CT examinations from 500 PDAC patients, with expert pancreas and tumor masks. Its [public Home documentation](https://api.osf.io/v2/wikis/t3dpr/content/) supplies binary label definitions, matching image/mask names, and a statement that pancreas masks include the tumor. These are publisher statements; we have not inspected the clinical files to verify them.

Both the project-associated [license record](https://api.osf.io/v2/licenses/60bf992258510b0009a5a9a6/) and Home documentation declare **CC BY-NC 4.0**, with direct downloads and no registration/DUA required for the stated research use. Public accessibility does not authorize commercial deployment or establish patient independence.

The [study's Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13564768/) describe PACS collection at four centers during 2015–2025, predominantly late-arterial imaging, manual masks with senior review, and patient-level cross-validation. Centers are presented as A–D. Author affiliations do not identify each center's files. These details support task suitability, not a verified patient crosswalk. Publication in 2026 does not make every patient or scan new to earlier pretraining.

I verified the actual public OSF storage hierarchy and complete center listings. The API works even where the browser's OSF page fetch failed. The files are **split archive parts**, not individual case downloads:

| Center | Publisher case count | Parts | Exact compressed bytes | GiB |
| --- | ---: | ---: | ---: | ---: |
| A | 101 | 4 | 15,906,769,079 | 14.8143 |
| B | 93 | 2 | 8,292,036,315 | 7.7226 |
| C | 210 | 2 | 9,235,163,819 | 8.6009 |
| D | 96 | 2 | 6,247,131,003 | 5.8181 |
| **Total** | **500** | **10** | **39,681,100,216** | **36.9559** |

Each part has a publisher-reported SHA256 and MD5, saved in `external_cohort_screen.json`. **Only metadata was fetched; these are not local archive checksum verifications.** Do not concatenate or extract until the archive format and complete part sequence have been checked. Current inventories expose no separate case ledger, acquisition-date table, source crosswalk or README alongside the parts. Such records might exist inside the archives; their absence there has not been established.

### What it can and cannot answer

- Suitable prospective endpoints, after admission: PDAC lesion Dice/recall, missed components, pancreas Dice, and false-positive components on these positive scans. Report metrics by center and pooled patient-level uncertainty.
- **Not suitable by itself for negative-patient specificity or false-alarm rate:** every declared patient has PDAC. Background voxels and healthy slices within a positive patient are not negative patients.
- PDAC performance would not establish performance on every pancreatic lesion type. The arterial-phase distribution also differs from other source populations; retain that limitation rather than pooling scores indiscriminately.
- A new evaluation cohort does not retrospectively clean our current PanTS development set, restore the public 901-case benchmark to untouched status, or validate every existing teacher/initialization's history.

## Alternatives and why they are lower priority

These are screening dispositions, not accusations of actual patient overlap.

| Candidate and primary source | Access / endpoint | Provenance or practical issue | Disposition |
| --- | --- | --- | --- |
| [PDAC-TAGS, 500](https://osf.io/g6rv5/) | Public CC BY-NC 4.0; expert PDAC and pancreas masks; 39.68 GB | Four anonymous center identifiers; no public crosswalk found outside archives; positive-only | **First admission candidate; independence unresolved** |
| [Rare pNET, 469](https://arxiv.org/html/2501.17555v1) | Paper describes CT and tumor annotation from Fudan University Shanghai Cancer Center | No verified public file release or access route located in the inspected paper/search; source identity alone is insufficient | Reserve candidate; do not promise immediate download |
| [CURVAS-PDACVI](https://zenodo.org/records/15720085) | Public CC BY 4.0; train archive 5,451,385,494 bytes; PDAC masks | [Challenge source](https://curvas-pdacvi.grand-challenge.org/dataset/) identifies PANORAMA-derived scans; CURVAS aliases do not give us a verified original-case join | Not a fresh independent dataset by default |
| [PANORAMA public cohort](https://github.com/DIAGNijmegen/panorama_labels) | CT; expert-positive subset and many other label types | PROWL already trained on 345 admitted expert studies / 344 source subjects; public source includes MSD and NIH imports | An unused subset would require a full exposure/patient join and annotation audit |
| [Basel pancreatic cysts, 221](https://zenodo.org/records/4621057) | Public CC BY 4.0; 3,217,052,760-byte archive; cyst-specific masks | Basel source institution intersects TotalSegmentator provenance; patient independence unverified | Lower priority; not automatically clean or a general lesion endpoint |
| [CURVAS organ cohort, 90](https://zenodo.org/records/13767408) | Public CC BY 4.0; pancreas/kidney/liver annotations | No tumor reference endpoint; absence of a tumor label is not a verified negative patient | Organ-only candidate, not a substitute for lesion evaluation |
| [PANCREATIC-CT-CBCT-SEG](https://www.cancerimagingarchive.net/collection/pancreatic-ct-cbct-seg/) | CT/CBCT with radiotherapy structures | Listed among PanTS source collections; structure suitability and patient membership need checking | Not a clean new source by default |
| [NIH Pancreas-CT](https://www.cancerimagingarchive.net/collection/pancreas-ct/) | CT and pancreas masks | Established reused source family; no comprehensive tumor reference for our endpoint | Do not recycle as new final lesion validation |
| [CPTAC/MSD resegmentation](https://zenodo.org/records/5510650) | Public pancreas/tumor annotations | Publisher describes existing CPTAC-PDA and MSD scans, not newly acquired patients | Additional annotations do not create independent images |
| [PANTHER](https://zenodo.org/records/15192302) | MRI; restricted access | Wrong modality for the frozen CT task and access request needed | Exclude from this CT screen |

For alternatives whose license or download size was not verified, do not infer either from a paper's open-access status. No archive was acquired for any row. The public pNET data availability remains unresolved rather than “proved unavailable.”

## Reconciliation with our exposure history

The retained [PANORAMA admission](../capstone/operations/PANORAMA-EXPLORATORY-ADMISSION-20261012.md) and [completed experiment](../capstone/operations/PANORAMA-POSITIVE-RESULTS-20261013.md) record actual training on 345 expert-positive PANORAMA studies from 344 source subjects. Therefore PANORAMA and its CURVAS-PDACVI derivatives need original-case and patient-level reconciliation before an unused subset could become a new holdout. A new dataset name is not new evidence of independence.

The existing `selected_source_metadata.json` contains the whitelisted PanTS provenance fields for 1,408 train/development records. Turkish source entries include Dokuz Eylul and Istanbul Medipol; US records include multicenter collections. PDAC-TAGS author affiliations cannot be turned into a source-disjointness result against those rows. No anonymous center code was equated across datasets and no fictional case-level crosswalk was created.

Our comparison exposure ledger must include **each** initialization, inherited checkpoint, teacher, training cohort, development/model-selection cohort and historically used benchmark. A cohort might be admissible for one model and unresolved for another. In particular, existing KD's teacher history and the Universal model's public-source history cannot be cleared solely by auditing STU-Net's TotalSegmentator source. Ordinary overlap between permitted downstream training data and pretraining is a separate methodological disclosure; the unseen-evaluation requirement applies to the held-out evaluation patients and all relevant model-selection paths.

## Concrete next admission plan

1. **Preserve the screen and obtain archive authorization.** Full PDAC-TAGS is 39.68 GB. The smallest complete center is D: two parts totaling 6.247 GB, with 96 publisher-declared patients. Choosing D for an initial provenance/integrity inspection is a storage decision, not a decision based on model performance. It does not freeze D as the final test. The adopted outline says to request authorization above 5 GB; splitting the download into individually smaller parts does not avoid that requirement.
2. **Check existing copies and storage before acquisition.** Record available space, archive/staging/extraction budget, network limits and exact URLs/checksums. Preserve failed partials; no unbounded retries. Inspect complete archive membership safely for path traversal, symlinks, expanded-size limits and schema. Downloading is not permission to read every mask or start inference.
3. **Inspect permitted provenance records before clinical content.** Search the admitted archive inventory for README, license, source/acquisition/patient grouping and release history. Determine whether A–D are original institutional cohorts or reused public datasets, and whether a stable pseudonymous patient ledger can be reconciled against our exposure graph. The public statement of one scan per patient supports declared within-cohort uniqueness; cross-cohort separation remains a separate check. Do not upload patient information or contact owners without authorization.
4. **Apply an explicit decision rule.** Adequate public provenance can qualify a cohort without an author email. It must establish a defensible separation from the conservatively defined source pools and our prior exposures, including repeat acquisitions. Positive duplicate findings reject affected membership; negative fingerprints alone cannot establish missing patient history. If records are insufficient, stop the independence claim and label the candidate unresolved. Do not spend another whole archive download merely hoping more negative image searches will prove it clean.
5. **If provenance passes, freeze the evaluation protocol before predictions.** Pin admitted patient membership, source versions, model artifacts, endpoint/phase/lesion definitions, geometry policy, exclusions and failure accounting, confidence intervals and one evaluation/reporting policy. Keep an explicitly designated engineering subset separate from the final evaluation. Choose all-center versus single-center scope on scientific and resource grounds before results. No training, threshold choice, preprocessing tuning or checkpoint selection on final evaluation outcomes.
6. **Qualify integration separately.** Use synthetic fixtures and then the designated engineering subset for units, image/mask alignment, native reconstruction and resource/recovery checks. No silent unit assumptions, ground-truth-assisted localization or dropped failures. Technical qualification is not clinical performance evidence.
7. **Run only a separately authorized bounded comparison.** Report the attributed pretrained initialization versus matched scratch initialization and relevant fixed baselines separately; include computational budgets and limitations. Obtain a separately verified negative-patient cohort before claiming negative-case detection performance. If a result drives another modification, record that exposure and reserve a different final evaluation.

### Decision at the end of this screen

**GO for further bounded PDAC-TAGS admission planning; HOLD for archive acquisition pending the required size approval; NO-GO for an independently verified or leakage-free evaluation claim today.** We can avoid an access-request wait, but public download access is not a substitute for provenance. If the archive contains no adequate provenance, the defensible choices are an explicitly exploratory external study or a cohort with stronger original source records—not an unsupported clean-test claim.

## Retained evidence

`external_cohort_screen.json` records candidates, exact OSF parts, source URLs, statuses and open gates. `external_cohort_screen_manifest.json` hashes this report, the structured screen, all small public API/HTML responses and the existing local exposure documents. It also binds the prior audit execution manifest without rewriting it.

Raw metadata is retained in the ignored local `outputs/prowl/stunet-audit-20261106/external-screen-01/` and copied to a fresh external `external-cohort-screen-01/` beneath the existing audit artifact root. No medical archive, weights or images belong in Git. This screen did not rerun earlier CT comparisons or tests, change producing pins, send correspondence, or alter any scientific cohort. Dataset integrity and patient independence are still future gates.
