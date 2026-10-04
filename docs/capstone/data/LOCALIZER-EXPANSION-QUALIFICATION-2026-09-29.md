# D-282 — bounded qualification and cohort publication

Quinton requested the next step after the complete D-281 audit. Codex will bind the existing
reviewed evidence to purpose decisions, preserve original membership and all unrelated holds,
and publish/replay separate train and validation cohorts. No raw-source read, source rewrite,
model execution, new download, literature work or global registry activation is required.

## Exact review scope and operational use

Candidate receipt `3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1` defines
16 train and 12 validation candidates. Content receipt
`224795f966a25733c7c1198e22dfa34fc525ef56be4e023ebdaa48ef8af0e3a9` and review receipt
`cb556a1086d665cb8584f9a8f404c89953445401bb9afc7c958f4e498560b8a4` supply file-specific evidence.
The [D-281 results](LOCALIZER-CANDIDATE-CONTENT-RESULTS-2026-09-29.md) describe its limits.

This record applies the retained [release/source assessment](LOCALIZER-SOURCE-AND-ALIGNMENT-REVIEW-2026-09-28.md)
to these exact PanTSMini CT/pancreas pairs from the same pinned extraction/inventory. The earlier
three-case allowed-use decision is not silently generalized. Under the existing authorized private,
noncommercial academic research scope, this successor assessment permits training_target only for
positively qualified train members, and evaluation_reference only for positively qualified validation
members. The latter grants no optimizer use. Publisher-protocol human validation remains
source_asserted, never independent expert acceptance. Attribution/source notices, the NC-ND/NC-SA
discrepancy and the prohibition on inferring public redistribution/model release permission remain.
No new legal clearance, publisher response, terms acceptance or biological uniqueness is asserted.

## Per-case decisions

The 27 pairs with a CT header declaring mm have matching CT/mask grids, finite CT arrays, nonempty
strict-binary targets and the reviewed limited alignment evidence. Interpret the original mask
coordinates in that matched CT grid; do not rewrite either source header. Case 6350 remains held
with no annotation allowed uses because both headers lack units. No visual inference resolves this.

Retain case 4965's limited visible pancreas coverage and case 3717's boundary contact as information
observations. Qualification is for a visible-pancreas development target, not guaranteed whole-organ
coverage. Later localization metrics must identify these cases and measure visible reference
containment separately from whole-organ claims. Retain observed noise and missing phase metadata.
No case is qualified or excluded based on model performance.

The proposed executable membership is exactly the original 16 train candidates and the 11 validation
candidates other than 6350. Keep all 12 validation candidates in the accounting report, including the
hold and its stratum; no replacement or silent shortage. Full protection parents remain 7200/1800/901.
All old issues survive; existing 3/26 annotation records are preserved in the predecessor artifact
and replaced by explicit successor versions here, without revoking their older scoped qualifications.

## Implementation and verification

Add an isolated expansion builder/validator and bounded publication CLI; reuse the existing shared
artifact store and D-269 cohorts-area capability. A bundle is frozen only after completion receipt
publication and independent readback. Consumers require independently retained bundle/manifest pins,
explicit optimizer/evaluator operation and unchanged candidate accounting. Source arrays remain a
separate loader responsibility. Keep the older fixed two-case registry unchanged.

Acceptance: reproduce from pinned inputs; validate all purpose checks and full ancestry; refuse held
or wrong-role members, changed evidence/current manifest, omitted candidates, altered permissions and
unrelated issue removal. Native synthetic tests plus actual fresh-process replay are required.
Metadata-only budget: 30 minutes per bounded invocation, 2 GiB RSS, 96 MiB artifact bytes, existing
artifact-store free-space floor; internal staging retains a 100 GiB free floor. No automatic retry
of publication conflicts or deletion of partial attempts.
