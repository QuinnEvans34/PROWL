# Coverage review and bounded corpus freeze — October 17, 2026

**Disposition:** Completion-spec Step 4 is complete for a seven-source development corpus.
The frozen candidate has **693 passages in 23 batches** and rebuilt exactly in a separate collection.
Coverage review identifies **6 directly supported needs, 15 partially supported needs and 4 gaps**.
These are agent-authored coverage judgments, not adjudicated evaluation labels or an accuracy score.
The live demo remains on its original two-source, 274-passage collection. Response quality is open.

Quinton's continuation authorizes this bounded permitted-source step. The proposal, frozen needs and
refusal boundaries remain unchanged. Full selection and training stay parked. No generative model
calls, patient data, protected questions or human-hours entries were involved.

## Frozen identity

- Public [corpus/index manifest](../../../configs/evidence/corpus-coverage-v1.json): raw-source,
  normalized representation, rights, citation, metadata snapshot, producer and embedding-batch hashes.
- Public [coverage matrix](../../../configs/evidence/coverage-matrix-v1.json): all 25 frozen needs,
  60 paragraph-level anchors with half-open normalized code-point offsets, text hashes and intersecting
  passage IDs. It contains no article body text or evaluation questions.
- Candidate: `research-coverage-v1`; verified copy: `research-coverage-rebuild-v1`.
- Complete content SHA-256: `17f65adda92c288e9bfc587cd7edbb195cf75e232a44929296393954edb5b681`.
- Encoder: existing pinned MiniLM, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`,
  384 dimensions, normalized float32 vectors, 256-token maximum, CPU / four threads.
  Descriptor ID: `68c0c08b71fc04772bdb09fff408b4ce40c8c5ca734efb24215300499ad214d4`.
- Index behavior: exact pgvector cosine ranking, passage-ID tie-break; no approximate search index.
  This is a frozen candidate, not the measured lexical/dense selection required by Step 6 / D-202.

The prior 274 passages and nine embedding batches are reused byte-for-byte. Five additions contribute
419 passages in 14 batches. Source bundles and frozen vectors are authoritative; the database is
rebuildable. Raw XML, normalized article text, vectors and operational receipts remain ignored/local.
The Git manifests alone cannot reconstruct articles or guarantee future downloads have identical bytes.

## Acquisition and rights decision

Cutoff: **October 17, 2026**. Discovery was purposive web search against the five frozen need families,
followed by explicit Europe PMC core metadata and full-text JATS inspection. Search strings, candidate
IDs, endpoint URLs and retained snapshot hashes are in the manifest. Search-engine rankings were not
frozen; this is neither an exhaustive review nor a run of the parked journal selector. Coverage-led
selection was exposed to development and can bias later results; report that limitation.

The retained acquisition plan allowed at most seven new sources, 32 MiB per XML / 128 MiB aggregate,
2,048 total passages, 32-item embedding batches and 600 seconds per ingestion invocation. Five new
full texts were acquired. Existing 104 GiB internal / 408 GiB external free-space floors and the 8 GiB
literature-database cap passed. No model download or new storage allocation was needed.

| Source | Role and permitted scope | Passages |
|---|---|---:|
| [PMC8997008 / PMID 35406426](https://pmc.ncbi.nlm.nih.gov/articles/PMC8997008/) | Retained quantitative-imaging review; secondary evidence | 184 |
| [PMC10177524 / PMID 37173876](https://pmc.ncbi.nlm.nih.gov/articles/PMC10177524/) | Retained pancreatic AI review; secondary evidence | 90 |
| [PMC8357939 / PMID 34381070](https://pmc.ncbi.nlm.nih.gov/articles/PMC8357939/) | Interobserver/interdisciplinary contour variation and stated annotation protocol | 87 |
| [PMC9317715 / PMID 35877639](https://pmc.ncbi.nlm.nih.gov/articles/PMC9317715/) | Pancreatic subregion annotation; assumes an already outlined whole pancreas | 64 |
| [PMC8145900 / PMID 33925859](https://pmc.ncbi.nlm.nih.gov/articles/PMC8145900/) | Study-specific isoattenuation, indirect localization and acquisition limitations | 64 |
| [PMC12715409 / PMID 41414851](https://pmc.ncbi.nlm.nih.gov/articles/PMC12715409/) | General **prostate radiotherapy** review workflow; not pancreas-specific effectiveness evidence | 116 |
| [PMC13564768 / PMID 42738357](https://pmc.ncbi.nlm.nih.gov/articles/PMC13564768/) | Multicenter pancreatic tumor segmentation with prompting and annotation details | 88 |

All seven retained JATS snapshots explicitly link CC BY 4.0. Existing policy permits local text,
embeddings and attributed snippets; raw redistribution remains disabled in our records. Metadata
availability alone was not treated as permission. The prostate study's core metadata uses a January
2026 publication date; its online article date is December 19, 2025. These refer to different publication
stages and both precede this cutoff.

Metadata-only exclusions: PMC12701807 and PMC8316779 report CC BY-NC; PMC12873139 and PMC12084540
report CC BY-NC-ND. They fall outside this adapter's CC BY 4.0 profile; this is not a claim that every
other use is legally prohibited. A normal-aging review, PMC10237602, was a discovery-only candidate
with a reported CC BY-NC-SA licence. The PanTS NeurIPS paper was outside the selected PMC/JATS path;
no paper or dataset was acquired through that path. These exclusions help explain the remaining gaps.

Notice screening retained all seven Europe PMC core responses, publication types and source XML.
No `commentCorrectionList`, notice publication type or JATS `related-article` notice was found in
those inspected snapshots. Identifier-based PubMed/PMC web checks did not identify a linked notice.
This is a dated, bounded check, not certification that no correction/retraction exists elsewhere or
will appear later. A later notice requires review and a new freeze before reuse.

## Extraction qualification

The default `legacy-v1` behavior and existing artifacts are preserved. New `coverage-v1` extraction:

- Accepts only the exact observed JATS 1.4 PUBLIC declaration, stripping it for parsing while hashing
  the original bytes. It never loads the referenced DTD. Other declarations and entity definitions
  remain refused.
- Skips the explicit administrative tag/title list in the code and removes embedded figure/table/
  supplement/reference elements from paragraph text while retaining surrounding prose and tails.
- Retains normalized code-point provenance and exact source/representation identity. Existing
  token-aware character-window fallback prevents silent embedding truncation.

This is prose extraction, not a complete reconstruction of the publication. Tables, figures and
supplements are excluded for new sources; mathematical markup may flatten imperfectly, and the
administrative exclusion list is not exhaustive. Legacy source extraction is deliberately unchanged.
The reviewed support anchors avoid relying on flattened equations or excluded material. A printed
figure/table reference is not evidence that its contents are indexed.

Initial legacy parsing refused three new JATS headers. Provisional bundles are preserved. A later
provisional enumeration also selected the pytest XML report and refused it as a non-article; final
acquisition uses explicit `PMC*.xml` inputs. Before embedding, review found nested figure captions
inside paragraphs; the final profile removes them. This changed PMC8357939 from 118 provisional to
87 final passages. Earlier preflight/bundles remain local and are **not** inputs to the freeze.

## Coverage decisions

“Direct” means study-specific supporting material was identified, not comprehensive coverage or a
universal recommendation. “Partial” requires stating the missing part. “Gap” means adequate retained
support was not identified; it does not claim that no such literature exists. Exact anchors and
limitations are in the machine-readable matrix. These judgments still require human consistency
review during question authoring and must not be copied blindly into gold labels.

| Need | Status | Scope / remaining limitation |
|---|---|---|
| N1.1 Boundary difficulty | Direct | General literature factors only |
| N1.2 Phase/protocol | Partial | Specific protocols; no controlled optimum |
| N1.3 Isoattenuation | Direct | Study-defined criteria and limitations |
| N1.4 Indirect signs | Partial | Localization does not establish a boundary |
| N1.5 Thickness/noise/artifacts | Partial | Some partial-volume/acquisition discussion; incomplete artifact coverage |
| N2.1 Measurement conventions | Partial | Volume outlining; reproducible lesion-diameter convention missing |
| N2.2 Reader variation | Direct | Inter- and intra-reader results with stated conditions |
| N2.3 Diameter versus volume | Gap | No adequate comparative evidence identified |
| N2.4 Contour criteria | Partial | Specific protocols; incomplete internal-appearance coverage |
| N3.1 Neighbour confusion | Partial | Adjacency context without confusion-frequency evidence |
| N3.2 Head/body/tail | Partial | Study heuristics; no universal landmark convention |
| N3.3 Normal age/fat variation | Gap | Adequate permitted retained evidence missing |
| N3.4 Duct contour policy | Gap | Attenuation-ROI exclusion is not a contour rule |
| N4.1 False-positive regions | Partial | Low-overlap failures, not a spatial error taxonomy |
| N4.2 Missed/incomplete lesions | Partial | Reported limitations, not causal failure analysis |
| N4.3 Generalization | Direct | Held-center evidence with explicit prompting conditions |
| N4.4 Uncertainty reliability | Gap | No validated confidence/calibration method identified |
| N4.5 Localization-first effects | Partial | Reference crop/prompt dependency, not a matched ablation |
| N4.6 Performance comparison | Direct | Metrics/splits/targets/prompting must accompany claims |
| N5.1 Human review | Partial | General prostate workflow; no pancreas safety inference |
| N5.2 Automation bias | Partial | Possible interpretation; alternative explanation retained |
| N5.3 Time/agreement/quality | Partial | Agreement/quality; time benefit unmeasured here |
| N5.4 Dataset review steps | Direct | Study-specific roles, checks and resolution |
| N5.5 Label provenance | Partial | Publisher account; empty/missing labels and local audit unresolved |
| N5.6 Ambiguous/incomplete labels | Partial | Selected boundary/anatomy limits; no complete label policy |

Two particularly important interpretation boundaries: the multicenter study used reference-derived
point prompts for its main evaluation, so its scores do not establish autonomous detection performance;
the prostate workflow paper discusses possible automation bias alongside deliberate acceptance of
adequate contours, so causation is not established. Neither source proves PROWL's current contour is
correct, complete or safe. Publisher-reported dataset release is separate from a local patient-data audit.

## Verification and reproducibility

Final affected offline checks: **35 passed, 4 skipped**. The skipped checks require an explicit live
integration configuration; they are not counted as passes. The actual corpus build/rebuild below
provides separate live database evidence. Earlier pre-nested-caption pass: 34 passed / 4 skipped.

The final freeze verification re-extracted all seven raw sources with their named profiles and matched
retained bundles exactly; verified all frozen batches against those representations; checked all 25
need IDs against the unchanged frozen-needs document; and checked all 60 anchors and intersecting
passages. Full canonical inventory and the reference/rebuilt database inventories match. All three
existing guided queries have exact result parity; this is reproducibility, not a relevance test.

Local receipts: `outputs/prowl/corpus-freeze-20261017/`, including `commands.json`, build logs,
`ingestion-preflight-final.json`, `freeze-verification.json`, `source-checks-final.xml`, and
`rebuild/plan.json` / `rebuild/COMPLETE.json`. The rebuild took 4.34 seconds; new-source ingestion
reported 3.35 seconds excluding prior encoder/tokenization preparation. These are machine timings,
not human work hours or end-to-end cold-start promises.

To rebuild from the retained, manifest-pinned canonical inputs:

```sh
.venv-retrieval/bin/python scripts/retrieval/rebuild_corpus.py \
  --batches outputs/prowl/direct-ingestion-20261014/batches/*.batch.json \
    outputs/prowl/corpus-freeze-20261017/new-batches/*.batch.json \
  --bundles outputs/prowl/direct-ingestion-20261014/batches/rev-*.json \
    outputs/prowl/corpus-freeze-20261017/new-batches/rev-*.json \
  --reference research-coverage-v1 --destination research-coverage-rebuild-NEW-ID \
  --output outputs/prowl/corpus-freeze-20261017/rebuild-NEW-ATTEMPT \
  --verify-guided-queries
```

Use a new receipt directory; never overwrite historical attempts. Verify input hashes against the
public manifest first. A changed article, extraction policy, membership or embedding requires a new
freeze and review of affected labels. Rebuild uses frozen embeddings without re-embedding articles.

Final service checks: UI 5180 and workflow `/research-workflow/health` on 8015 return 200; Ollama's
model-list endpoint responds. An initial request to the wrong `/health` route returned 404 and is
retained separately. No inference was used as a health check. Database size was 20,477,619 bytes;
pgvector 0.8.2. Storage floors still passed. `research-v1` retained content SHA
`415ca84294b21864c1a12c1a24effec3fd99b3f64be04576cf35c41cd400acc9`. The existing live service was
not restarted or repointed; its already-loaded producer identity remains the prior checkpoint.

## Next checkpoint

**Step 5 / [AI-03](https://trello.com/c/NctoNxr8): evaluation authoring and label freeze.** Prepare
30 development cases and Quinton's protected-authoring template against this frozen candidate.
Quinton independently authors and protects the 30 held-out cases under the existing protocol.
Both splits require 20 answerable / 10 unsupported-or-out-of-scope cases, all five families, exact
support, leakage checks, adjudication and a second consistency pass. Do not invent supported answers
to fill the four gaps or treat partially supported needs as fully answerable. If authoring reveals
insufficient evidence, version the corpus and affected labels explicitly before tuning.

W02-07 closes for this bounded scope. W05-02 retains the candidate-freeze evidence but remains a
broader milestone roll-up pending retrieval selection and integrated prototype acceptance. Response
quality, finding integration and protected acceptance remain unfinished. No new standalone gap cards
are needed yet: the matrix and AI-03 carry the concrete dependencies without creating parallel work.
