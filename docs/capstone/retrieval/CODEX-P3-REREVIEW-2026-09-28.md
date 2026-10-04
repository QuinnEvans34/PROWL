# Codex P3 re-review — accepted synthetic foundation

September 28, 2026. Reviewed Claude handback revision 2, exact SHA-256
`c6a072db9194c1d94b9f26fafec17eaf26db5c1a6d662cd2043923acefdb3c48`.
**Accepted for the dispatched P3 synthetic foundation scope.** R1–R5 from the first review are
closed by this revision. No remaining blocking finding identified in the reviewed scope.
This is not G6, live-corpus approval, database/dependency approval or production query safety.

## Native evidence

Both exact packet commands ran in the Mac checkout with the existing environment:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/retrieval -q -p no:cacheprovider
# 182 passed in 0.65s
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
# 813 passed, 2 existing torch.jit deprecation warnings in 5.75s
```

All 30 listed source/test/schema/design hashes match, and the handback's own hash matches its
RUNNING-LOG entry: 31 verified files in total. The original reproduction failures are now public-
entry-point assertion regressions in the suite; their changed-signature versions were inspected.
The old scratch script is not reused unchanged because the interfaces intentionally changed.
Claude's reported 33 reverted mutation checks were reviewed as handback evidence, not independently
rerun as a mutation campaign by Codex. No retrieval implementation or tests were changed by Codex.

## Findings closure

| Finding | Verified correction |
|---|---|
| R1 stale identities / duplicate records | Revision, rights and event verifiers run on loading paths. Rights permission changes under a stale ID fail. Duplicate logical records fail; distinct update events may reference one revision. |
| R2 evaluation bindings | Required accepted-query mapping, exact question/configuration/corpus checks, unique label questions and verified corpus passage/representation records. |
| R3 false delivered credit | Passages are selected through the verified ranking and corpus; exact slices feed counters. Rights are identity-checked and display permission is independently enforced. Forged offsets fail before scoring. |
| R4 source offsets | Original length/hash and map participate in representation identity; structural checks reject malformed maps. Original-paragraph reconstruction verifies semantic provenance when source text is available. |
| R5 pool exhaustion | All-corpus-member count is derived and persisted; constructor and verifier enforce min(50, count), including forged/reidentified records and strict integer checks. |

## Schema and interface decision

Confirm **1.0.0** for this first accepted synthetic baseline. The prior draft was not accepted;
repository search found no imports of these interfaces outside src/retrieval and tests/retrieval,
and the handback reports no persisted external consumers. The three revised schemas are identified
by their exact hashes in the accepted handback. Do not interpret the superseded draft as compatible
merely because its schema_version field was also 1.0.0. Future incompatible changes after this
acceptance require explicit version/migration review under the project contract policy.

The breaking function signatures are accepted as lane-local pre-acceptance corrections. The
handback interface table is the integration reference. Shared contract documentation/consumer
integration can be updated in its owning slice; no global validator migration is implied here.

## Required downstream boundaries

- At real ingestion, call verify_revision with the pinned source bytes and
  verify_representation_source with the original paragraphs before publishing a representation.
  Structural map validation alone cannot prove the original characters. This is a P5 parser
  acceptance requirement, not an undisclosed assertion that P3 already parses real sources.
- Corpus/ranking identities detect changes; hashes alone are not independent authorization.
  Production consumers must resolve approved/pinned builds through the later artifact boundary.
- Fixture query rules and self-labelled synthetic counters are not a production security sandbox,
  anonymizer, tokenizer or permission for external text transmission.
- New eligibility filters need a verifiable inventory/policy; all_corpus_members is the only
  currently accepted ranking pool rule.
- Span-hit and delivered-evidence metrics remain proposed/provisional, not official D-085 metrics.

P3's contract-review dependency is satisfied. P4b still requires P4a and separate psycopg 3 approval;
P4a installation/platform work has its own authorization. No new phase is dispatched by this
review. P2 seed-candidate review can remain a separate proposed next literature activity.
