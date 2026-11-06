# Universal Swin: retained patient-crosswalk review

**Source-dataset overlap is established; exact patient exposure remains unknown.** None of the four screen cases can be classified as verified unseen from the retained records reviewed here. This does not establish that any of them was seen. The .710754 four-case Dice remains exploratory.

## Bounded evidence inspected

Eight named case-metadata JSONs were inspected: the October10 cache metadata and original transferred prepared metadata for each of 2028, 1347, 2514 and 8743. Both versions expose `transform.source_identity.study_id` as the PanTS alias, together with file hashes. Neither version supplies an original collection, original patient identifier or DICOM study/series crosswalk. The full field names and evidence hashes are recorded in the [companion JSON](UNIVERSAL-SWIN-RETAINED-CROSSWALK-20261106.json).

Also inspected: 70 identity/exposure records in the existing autonomous development request; the Universal acquisition receipt; the retained SuPreM source-use review; and the Mac publication review at commit `209e0cb`. These make 12 hashed evidence files/documents, containing eight named case-metadata records and 70 request case records. All 70 request records retain unknown teacher membership and unverified biological independence. This is not a fresh audit of 70 original source rows.

| Screen case | Retained identity | Original collection / patient / series | Exact checkpoint training / selection membership |
| --- | --- | --- | --- |
| 2028 | PanTS_00002028 | Unknown | Unknown / unknown |
| 1347 | PanTS_00001347 | Unknown | Unknown / unknown |
| 2514 | PanTS_00002514 | Unknown | Unknown / unknown |
| 8743 | PanTS_00008743 | Unknown | Unknown / unknown |

**Established original-source matches: 0/4; established patient matches: 0/4; verified unseen: 0/4; unresolved: 4/4.** Zero established matches means missing linkage, not zero true overlap.

## Published membership versus checkpoint membership

The pinned [training code](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/train.py#L211) defaults to `PAOT_123457891213` and `PAOT_10_inner`. Its retained loader reads the corresponding `_train.txt` and `_val.txt` lists. The first [training list](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/dataset/dataset_list/PAOT_123457891213_train.txt) explicitly includes TCIA Pancreas-CT filenames; the second [training list](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/dataset/dataset_list/PAOT_10_inner_train.txt) includes MSD Task07_Pancreas filenames. Six upstream train/validation list documents were reviewed through web excerpts, including the alternative PAOT pair. No exhaustive row join/count or test-list inspection was performed.

The Mac publication review at `209e0cb`, `UNIVERSAL-SWIN-PROVENANCE-AND-NEXT-STUDY-20261106.md`, independently documents shared source families from both papers. That supports dataset-level overlap, not assignment of these four aliases to either collection.

The acquisition receipt binds weight revision `76f0304ff9387c1baccbbc1d9eac78c5c5ccfeed` and checkpoint SHA `cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07`. It has no training or model-selection ledger. Published code defaults and list filenames do not prove which lists produced this released checkpoint, including any inherited initialization. The older SuPreM approval expressly retains unknown pretraining membership; it does not clear this checkpoint.

## Minimum missing evidence and decision

1. An authoritative crosswalk from each intended evaluation PanTS alias to original collection/release, original case/series and stable patient group, including repackaged aliases.
2. A ledger bound to the exact released checkpoint covering optimizer training, inherited pretraining and model-selection exposure, or an authoritative publisher attestation sufficient to establish separation.

Without those, retain unknown exposure and use these cases only for exploratory development. A clean evaluation requires separately justified patient/source separation; random resplitting, replacing the output head or renaming IDs cannot establish it.

This review did not read CTs, masks, arrays, model weights, protected test records or the mixed-partition publisher workbook. It does not claim that no crosswalk exists elsewhere. No data download, new duplicate audit, GPU job, training, exclusion, reclassification or changed scientific gate occurred. Frozen producing files remain untouched. No next experiment is launched by this report.
