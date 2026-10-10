# Offline PubMed catalog preview

October 10, 2026. Quinton requested preparation work during the bulk PubMed download so real-document
testing can begin promptly. This is a separate exploratory adapter, not a promotion of sizing-only
parser output or an implementation of the full approved selection policy.

## What is implemented

- A streaming gzip/XML reader that retains complete article/book record XML, including fields not
  displayed in search. External DTDs are not fetched; entity declarations/references are refused.
- PMID-based replacement and deletion, in frozen file order and within-file event order.
- A disk-backed SQLite preview with one transaction per input file. A failed parse rolls back that
  file; previously completed files survive and are reused on restart against the same snapshot.
- Download receipt, compressed-file SHA256, source filename, record position and manifest identity.
- Literal title/abstract search returning PMID links and source provenance. This is not relevance
  ranking, an embedding index, an answer generator, or the planned PostgreSQL/pgvector store.

The original XML is retained for later metadata extraction. Searchable text is a convenience rendering,
not the final passage/offset contract. No per-document rights, clinical suitability or source support
is inferred from successful parsing. Search results are exploratory source candidates.

## Commands

Run from the repository root. Use an output directory separate from the raw download directory:

```sh
.venv-prowl/bin/python scripts/retrieval/prepare_pubmed_catalog.py build \
  --source /Volumes/PROWL-Data/PROWL/scratch/literature/pubmed-2026-20261009 \
  --output /Volumes/PROWL-Data/PROWL/scratch/literature/catalog-preview-20261010/catalog.sqlite \
  --max-files 1

.venv-prowl/bin/python scripts/retrieval/prepare_pubmed_catalog.py search \
  --catalog /Volumes/PROWL-Data/PROWL/scratch/literature/catalog-preview-20261010/catalog.sqlite \
  --query pancreas --limit 5
```

The source directory keeps its original October 9 name from the downloader; this acquisition started
October 10. Commands accept any directory with the supported frozen download manifest and verified
receipts. A missing receipt stops preparation; `.partial` downloads are never parsed. Run again after
the required file has finished. An incomplete receipt line during concurrent append also fails safely;
retry once the append completes.

The default is three files, with a hard ten-file preview limit, a 2 GiB SQLite page limit on the default
4 KiB page format, and a 10 GiB starting free-space check. Per file: 8 GiB expanded-byte ceiling,
16 MiB record-text ceiling and ten-minute parsing deadline. These are parser limits, not a measured
whole-process memory watchdog. A file lock excludes competing builders. Do not modify the sources or
catalog while it is building.

A partial prefix is not current PubMed: revisions and deletions from later files are absent. The build
report states applied versus total files and explicitly reports `selected_corpus: false` and
`rights_qualified: false`. The tiny synthetic test snapshot can complete; the real bulk snapshot cannot
be declared replayed by this ten-file preview. The first files are not a representative topic sample.

## Verification and next work

Focused tests: `tests/retrieval/test_pubmed_catalog.py`. They cover replacement/deletion, restart,
source identity/order, failed-file rollback, inline markup, retained correction metadata, unsafe XML,
truncated gzip, expansion/record/time limits, and literal search escaping.

Next work is to qualify full-scale parsing/storage and implement the approved selection policy over
final PMID state, including metadata, MeSH, correction notices and rights decisions. Then reuse the
existing passage contracts and compare lexical retrieval against vector retrieval. Preserve the
existing guided UI and its synthetic labeling until real evidence passes through that integration.

The bulk downloader, prior sizing parser, UI changes and PostgreSQL plans are unchanged.

## October 10 result

Thirteen focused tests passed. The first verified real file (`pubmed26n0001.xml.gz`) produced
30,000 current-in-prefix records in a 237,649,920-byte SQLite preview. Literal search for `pancreas`
returned five requested records with source SHA256s and PMID links. This confirms ingestion/search
integration only: no claim of topic coverage, retrieval relevance, rights qualification or complete
baseline/update replay. No vector database or language model was installed or invoked.
