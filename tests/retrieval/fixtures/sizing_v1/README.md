# sizing_v1 fixtures: all invented

Every file here was written by hand by Claude for the S2 offline tests (2026-10-03). They are
PubMed-*style* in shape only. The PMIDs are in the invented 9000000xx range, and every title,
abstract, MeSH-like label and DOI-like string is made up. None is copied from,
or derived from, real PubMed records or abstracts.

Listings, `.md5` bodies and gzip samples are generated inside the tests from these files or from
literal strings.

- `pubmed_style_doctype.xml`: three invented articles (one with a MedlineDate and inline
  markup), a DOCTYPE naming an external DTD, and one book-style record.
- `update_with_deletes.xml`: one invented article plus a DeleteCitation with two invented PMIDs.
- `external_entity.xml`: an external SYSTEM entity. It must be refused, with no fetch.
- `billion_laughs.xml`: nested internal entity expansion. It must be refused.
- `internal_entity.xml`: a single benign internal entity. It is refused, because the expansion
  bound is zero user-defined entities.
- `undeclared_entity.xml`: a reference to an entity that is never declared. It must be refused.
- `malformed.xml`: an unclosed element. It must be refused.
- `wrong_root.xml`: a well-formed file whose root is not PubmedArticleSet. It must be refused.
