# Pancreatic disease reference corpus

PROWL's expert is being developed around the scan a radiologist is reviewing: verified measurements,
inspectable findings and cited disease context. Quinton approved retaining PanTS and starting the
literature expansion with pancreatitis and pancreatic cancer. Cystic-lesion expansion follows later.
This is the first completed source-data slice of that direction, not a working diagnostic feature.

## Delivered source collection

The separate `research-disease-v1` collection contains **14 papers and 1,179 passages**. Four new
papers contribute 232 passages; all ten existing sources and their 32 batches are reused unchanged.
The independent `research-disease-rebuild-v1` collection has the exact same source, text and vector
inventory. The live demo still uses its original collection.

The [manifest](../../../configs/evidence/corpus-disease-v1.json) records immutable sources, metadata,
licenses, extraction versions and all 41 batches. Corpus content SHA:
`eae607b2aaeec5e55bb15a71cd0cd49b54e2c110f2989a2b21de4d052d673fd8`.

| New source | Added passages | Intended reference use |
|---|---:|---|
| [The role of imaging in acute pancreatitis, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8292294/) | 70 | Inflammatory enlargement, surrounding findings and imaging terminology; preserves the need for clinical context. |
| [Mass-forming pancreatitis versus pancreatic ductal adenocarcinoma, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7376657/) | 52 | Chronic inflammatory masses, atrophy/calcifications, overlap with cancer and limitations of individual imaging signs. |
| [Imaging diagnosis of autoimmune pancreatitis, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8578112/) | 31 | Focal/diffuse swelling, phase-dependent enhancement, rim and duct findings; keeps CT and MRI evidence distinct. |
| [Imaging diagnosis and staging of pancreatic ductal adenocarcinoma, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7183518/) | 79 | Small/isoattenuating lesions, secondary findings and mimics. The article's staging/treatment discussions do not authorize patient-specific staging or treatment outputs. |

These are narrative imaging reviews, not a current guideline collection or a systematic disease
survey. Their reported diagnostic performance is not PROWL performance. The existing corpus retains
primary studies and anatomical context, but does not establish a universal normal-size interval.

All four additions explicitly license article text under CC BY 4.0 in retained publisher JATS.
Only prose is extracted; figures, tables, supplements and reference lists are excluded. Current
Europe PMC core metadata and retained JATS show no correction/retraction relations for these four
snapshots. This is a bounded notice check, not exhaustive notice surveillance.

PMC10887967 was acquired and inspected, then excluded from this slice because its emphasis is AI
methods. Its metadata's preprint relation was retained, not misreported as a correction. The more
directly relevant PMC7183518 replaced it before embedding. The previously researched PMC10864763
has an NC-ND license and remains excluded under the current adapter. ACG/Kyoto guidelines and
Pancreapedia are discovery/reference candidates; none was silently imported or treated as admitted
full text. Exact reuse rights and revision status still need review for any future addition.

## What the evidence supports

The [coverage record](../../../configs/evidence/disease-coverage-v1.json) binds nine needs to the
new corpus. Five have general reference context: inflammatory enlargement; chronic-pancreatitis
atrophy/calcification; inflammatory mass versus cancer; small/isoattenuating cancer visibility;
and duct/enhancement context. Applicable normal CT size references remain partial. Measurement of
the selected pancreatic head and disease probability from size alone remain gaps. Dedicated cystic
coverage is deferred. These are engineering coverage judgments, not gold evaluation labels.

Each locator has a source identity, representation hash, exact paragraph offsets/hash and overlapping
passage IDs. A coverage paragraph may span several passages; its presence does not demonstrate that
retrieval supplies the full answer. No generated expected answers are indexed.

## Product behavior and remaining work

The intended response combines three distinguishable pieces:

1. **Measured fact:** a defined size/volume calculated from the selected geometry and outline, with
   units and a viewer location. Pancreatic head measurements require a qualified subregion definition.
2. **Cited context:** what the literature reports about that kind of finding, including limitations
   and accompanying features that matter. A measurement above a cohort mean is not automatically abnormal.
3. **Available information:** which relevant features the software measured or the reviewer confirmed,
   and which remain unknown. A model-generated explanation cannot invent enhancement, duct changes,
   inflammation or a diagnosis from an organ outline.

PanTS remains the imaging dataset. Its public documentation advertises subregions, ducts and paired
reports; this work has not established local availability, report authorship/verification or model
support for those outputs. Case reports remain separate from general disease-reference evidence.
Protected cases/reports must not enter the literature retrieval pool.

Next is a versioned capability and evidence contract mapping each radiologist task to actual inputs,
measurement tools, retrieval and fallback behavior. General disease associations can be explained;
patient diagnosis, probability, stage, prognosis, treatment and contour certification are not enabled
by adding sources. Current coarse query inputs, guided-only UI and quotation behavior remain unchanged.
The new corpus is a development candidate; it has not been promoted into the live expert.

Quinton supplies realistic questions without locating passages or technical labels. Engineering must
provide an independently checked labeling workflow before requesting those questions. The original
30-case development acceptance remains valid for its original corpus/scope, not proof of this expanded
role. The current 60-case protocol/counts and frozen thresholds are not silently changed: the next
contract must reconcile task coverage and labeling responsibility before a revised evaluation freeze.
No held-out material has been opened, and no configuration tuning or answer-quality score is claimed.

## Verification and preservation

- 58 affected extraction/ingestion/inventory/rebuild tests pass; five optional database tests skip
  without their dedicated test configuration. The real build/rebuild supplies separate live evidence.
- All ten older raw sources reproduce their canonical bundles exactly. A new `disease-v1` profile
  excludes additional publisher administrative headings; `legacy-v1` and `coverage-v1` behavior stays fixed.
- Actual canonical source/text/vector checks and the independent database rebuild match. The three
  existing guided-query results also match across the two new collections; this is reproducibility,
  not disease-answer quality or a selected retrieval configuration.
- The five pre-existing live/coverage collections retain their complete inventories. Existing source
  rights, v5 questions/answers, human-review events and prior producing receipts are preserved.

Local evidence: `outputs/prowl/disease-corpus-20261017/`, including acquisition/amendment records,
raw XML/core metadata, earlier extraction previews, build producer and hashes, test report, build and
rebuild receipts. Full text, embeddings and runtime evidence remain in ignored local storage. The
104 GiB internal / 408 GiB external free-space floors and 8 GiB database cap remain enforced.
No training, generation, full selector, service restart or human-hours credit follows from this work.

Tracking: [AI-08 source corpus](https://trello.com/c/HmDLnOYF), with downstream measurement/context
work under [AI-05](https://trello.com/c/Ob3VE0MN) and [AI-06](https://trello.com/c/TKCLH5PZ).
