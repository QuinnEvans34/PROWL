# V14 — plain-text writer boundary diagnostic

V13 does not qualify: revision often repeats the rejected claim, and the model's qualification
boolean incorrectly accepts an unqualified numerical example. Stronger review instructions alone
are not evidence of correctness. Preserve the whole run and its outputs; do not deploy it.

Test a different output boundary: ask the local8B model for ordinary prose, with source markers at
the end of each paragraph, instead of generating prose inside a constrained JSON schema. Put the
question after the source data and explicitly name a reader unfamiliar with specialist jargon.
Code parses only a strict terminal [P1, P2] marker group per paragraph, binds original passages,
and applies existing citation/number/qualifier checks. INSUFFICIENT is the sole empty-answer token.
No hand-authored answer or expected concept is supplied. Original canonical evidence stays fixed.

First diagnostic: exactly two exposed cases, head-size and published volume (quality01/03). One
non-thinking8B writer call each, publisher sampling/seed42/context16384/max1024tokens,60s deadline.
No JSON format constraint, no automatic repair/retry. Preserve raw output even if parser/validation
fails. At most2calls/3minutes. Inspect each factual statement and citation manually as engineering
review, not clinical acceptance. Both must be useful, supported, readable and appropriately qualified
before any separately recorded continuation. No deployment from this two-case diagnostic alone.
