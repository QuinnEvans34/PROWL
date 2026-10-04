# Shared retrieval offline shape controls

All 12 records are hand-authored and invented. Text, questions, notices and rights statements are
fictional; work IDs use `work:synthetic:`. Repeated hashes and IDs are shape placeholders, not
computed identities or verified content. No producer was called to generate these records. No
PubMed record, clinical input, evaluation question or held-out label was read.

`pins.json` binds each fixture's exact bytes and its accepted 1.0.0 schema. Fixtures are ordinary
JSON documents; references are not fetched. The shared gate checks structural/version boundaries,
required fields, allowed enums, unknown fields and applicable numeric/type/conditional rules.

The accepted schemas do not prove hashes, slice/offset semantics, corpus/ranking/count relationships,
clinical scope, rights provenance or metric arithmetic. Those remain retrieval runtime checks.
These records must not be supplied to real producers or offered as accepted runtime identities.
The `proposed_provisional_not_official` metric/context labels deliberately retain the existing
producer contract; D-344 policy acceptance does not authorize its migration or a real tokenizer.

Negative controls alter one named field after validating the corresponding positive. Missing rights
permissions, premature metric promotion, unsupported token counters and malformed numeric/offset
shapes must fail. Cross-record semantics and omitted real rights are not inferred from schema passes.
