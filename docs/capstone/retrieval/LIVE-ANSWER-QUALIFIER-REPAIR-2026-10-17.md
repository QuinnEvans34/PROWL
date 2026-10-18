# Live answer qualifier repair v6.1

Both v7 and v8 prompt candidates failed their development promotion criteria and remain unpromoted.
Stop prompt iteration in this checkpoint. Keep the v6 system/review/schema hashes, reasoning modes,
model, seed, context window, call limits, retrieval and corpus exactly unchanged.

The separate v6.1 repair adds only two mechanical backstops before semantic review: reject mandatory
wording absent from cited passages, and reject introduced healthy/normal-person/control-group
descriptors absent from cited text. These checks directly address observed unsupported statements;
they neither certify support nor decode group abbreviations. They may reject a legitimate paraphrase
and can miss other overstatements or unrelated matching words. Semantic review remains necessary
and demonstrably fallible. No claim of general answer-quality qualification follows.

Before local deployment, run focused Python and UI checks and validate both retained offending
drafts against their own evidence: the prior v6 “requiring comparison” response and v7 “healthy
control group” response must fail. Keep model failures distinct from insufficient evidence. The UI
will explain rejected source qualifications and scope insufficiency to the returned passages.

After this validation, restart only the verified owned literature API and run the two previously
selected live questions once each: “What does the pancreas do?” and “Could the size of the pancreas
head indicate any specific diseases?” Maximum four generation calls, no retries or further prompt
changes. Retain all outcomes; inspect source navigation. This is a development integration check,
not a new comparative benchmark or final evaluation. Core answer quality and retrieval coverage
remain open. Existing human review, protected evaluation and measurement-extension obligations remain.
