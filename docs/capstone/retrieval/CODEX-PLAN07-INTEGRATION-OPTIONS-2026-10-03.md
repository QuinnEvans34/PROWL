# Plan 07 open integration choices — October 3, 2026

L6 options only. No choice below is approved by this document, and no code, dependency, platform
trial or official metric changes here. R-01 and imaging availability take priority.

| Choice | Recommended option | Alternative / tradeoff |
|---|---|---|
| Retrieval1.0.0 schemas join shared contract checks? | Include all12 accepted P3 schemas in a separate retrieval section of the shared offline contract gate, with invented positives/negatives and explicit schema/fixture version pins. Keep the existing Plan01/02 name/path set stable; retain runtime identity/relationship tests in the retrieval suite | Leave them lane-local until P4b integration; less shared coverage, fewer immediate shared-test changes |
| D-085 proposed span/delivered metrics? | Approve them as additional, separately reported metrics while keeping official passage/source recall@1/3/5/10 and MRR. Require immutable representation hashes, half-open Unicode offsets, complete-containment credit, checked ranking/question/corpus binding, display-rights enforcement and pinned tokenizer/context budget before measured use. State development-only selection role separately; do not change release bars retroactively | Keep them explicitly provisional until P7/P9 evidence is available; current P3 implementations remain demonstrations, not official criteria |
| When request P4a install/trial authorization? | Prepare the concrete named-runtime/version/storage/resource trial after the immediate imaging/checkpoint queue is settled; schedule its actual trial when imaging is idle. P4a can proceed independently of P3 and Run S once its own permission exists | Request the concrete install packet now but defer execution to an idle window; or defer the whole request until S1/S2 are accepted, reducing parallel work but delaying platform evidence |

Schema inclusion is software checking, not acceptance of a real corpus, database schema or generator.
P3 was accepted synthetically in [Codex's rereview](CODEX-P3-REREVIEW-2026-09-28.md); the retrieval
contract README retains an older "pending re-review" status, which should be reconciled by its owner
in a future bounded update. This options task changes neither it nor the schemas.

The D-085 amendment remains pending in [DECISIONS](../DECISIONS.md). Approval should explicitly name
ranked span-hit recall and delivered-span recall/concept coverage/token count, their denominators,
rights and tokenization, and whether they affect development configuration selection. No unseen
evaluation labels should be exposed to implementers. Pure fixture token counting is insufficient
evidence of actual token-budget delivery.

P4a is an explicit install authorization for a named container runtime, pinned PostgreSQL image and
pgvector, followed by a bounded synthetic platform/storage/resource/recovery trial. First inventory
existing shared Docker settings and storage, identify exact downloads/versions and stop limits, and
obtain approval before changing global settings. No existing image, installation or native acceptance
is assumed. P4b separately needs accepted P3 contracts, P4a evidence and psycopg3 dependency approval.
No production literature or model downloads are bundled with the platform trial.

At the decision discussion, choose one option per row. This list does not request or grant a
follow-on dispatch; any selected implementation needs its own concrete scope.
