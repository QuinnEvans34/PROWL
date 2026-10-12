# Search and selection policy v0.1 — journal records first

**Approved by Quinton:** October 10, 2026. In response to the journal-only first-corpus proposal:
“Yes, that is fine. If we start with the journals and make sure the system works we can expand to
the larger dataset later.”

This amendment and [policy v0, revision 9](SEARCH-AND-SELECTION.md) together define v0.1.
The original v0 text remains unchanged. The implementation records the hashes of both documents.
This is a pre-run scope clarification prompted by the PubMed record formats, not tuning against
selection results or relevance labels. It does not freeze a candidate corpus or initiate evaluation.

## Record-type rule

- `PubmedArticle` records follow all existing v0 field, topic, exclusion, cap and accounting rules.
  “Journal records” here identifies the XML record type; it does not assert peer review or override
  publication-type exclusions such as Editorial and Comment.
- `PubmedBookArticle` records remain in raw storage and the catalog, but receive the hard-exclusion
  reason `record_type_excluded`. They cannot enter the first candidate/evidence corpus.
- For book records, extract only `BookDocument/PMID` and record type for selection accounting.
  Do not apply the journal-specific topic, date, language, abstract or publication-type field mappings
  to books. Blocks/branches are empty (not evaluated), abstract availability is null (not evaluated),
  and no `not_candidate`, `no_mesh`, `language_missing` or `date_missing` reason is invented.
- Deletion remains highest precedence. A deleted PMID with retained book metadata has disposition
  `deleted` and retains both `deleted_by_update` and `record_type_excluded` reasons.
- A deleted PMID with no retained prior record has unknown type; do not guess that it was a book.
- A re-added record follows its latest actual XML type. All PMIDs remain represented exactly once
  in the reconciliation universe. Book records never consume WORKFLOW cap slots.
- Report total known book records, live excluded books and deleted books separately, alongside
  record-type counts and the existing dispositions/reason counts.
- Unknown XML record types and missing/invalid PMIDs still stop processing; this is not a blanket
  skip rule for unrecognized input.

No raw data is deleted or redownloaded. Book inclusion later requires a new policy version with
explicit field mappings and eligibility rules. All other v0 rules, rights decisions, seed/reserve
controls and evaluation requirements remain in force.
