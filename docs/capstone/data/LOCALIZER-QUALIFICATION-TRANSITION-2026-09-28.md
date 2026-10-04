# Localizer qualification: supported transition and exact remaining evidence

September 28, 2026. **Completed:** narrow pre-publication transition checker, synthetic tests and
retained-input review for cases 3/26/31. **Not completed:** real positive qualification, hold removal,
source activation, production publication/consumer integration or training.

## What the hold review established

Each candidate has three applicable historical generic holds:

| Historical rule | Supported route forward | Current result |
|---|---|---|
| IDENTITY_UNVERIFIED | D-022 already accepts study-as-subject with `unverified_unique`; preserve exact protected roles and reject known duplicate findings | No need to claim or prove biological uniqueness to use the approved fallback; no real hold removed yet |
| STUDY_QUALIFICATION_PENDING | Pin source readiness, existing physical geometry and target/coverage review to exact CT/mask bytes | Retained geometry and finite-array evidence available; visual alignment and source-readiness assessment pending |
| ANNOTATION_USE_PENDING | Approved mapping plus release-applicable provenance and affirmative purpose-specific allowed-use evidence | Complete counts support D-259 in all three; source/use decision and alignment evidence still pending |

Specific denials for case 78 and case 266 are outside the supported transition. They remain effective.
The old package's generic study-hold message mentions case 78 even on other study records; attachment
identity and rule govern applicability. That historical wording was not rewritten or treated as a
finding that every candidate has pelvic-only coverage.

Case 3's recorded spacing is approximately 0.818 × 0.818 × **7.5 mm**. Preserve this thick-slice
characteristic under D-267. It is not grounds for silently substituting an easier case. The proposed
first learning fixture remains a small, deliberately selected engineering check, not a representative
generalization evaluation.

## Implemented transition boundary

`src/data/qualification_transition.py` produces a reproducible certificate binding independently
reviewed old/new manifest hashes, the successor qualification hash and every superseded issue hash.
It requires:

- exactly the three supported generic quarantine holds, attached to their correct entities;
- original train role and identical protected membership/migration pins;
- unchanged source snapshot, CT/mask identities, geometry and complete encoding evidence;
- a new annotation identity with only pancreas `training_target` permission;
- `human_validated`, `source_asserted`, `publisher_protocol` provenance, not expert certification;
- fully revalidated positive qualification and all independently pinned check evidence;
- unchanged unrelated records/issues and preservation of non-pancreas target claims.

The old manifest and issues are never edited. A certificate records the exact supported successor
relationship; it does not itself publish a new manifest or change a production consumer. Missing
checks, specific purpose denials, unknown holds, changed geometry, wider permissions or unrelated
record deletion fail closed. The existing deny-only helper and manifest-v3 resolution rejection remain
unchanged. Future publication must explicitly verify this certificate with retained parent history;
merely constructing an eligible-looking record is not sufficient.

This checker deliberately accepts only an already valid v3 accounting context. The historical real
package remains v2; migration to v3 with complete protected accounting and reviewed source evidence
must occur before a real transition is issued. No unreviewed source migration is smuggled into this
single-case transition. This is a bounded implementation component, not completion of Step 3 or G1.

## Real retained-input review

Runner: `scripts/diagnostics/localizer_qualification_review.py`.
It verified the independently pinned old purpose-package receipt and all **55** covered files,
plus the current content-verification receipt and all **13** covered files. For the three candidates
it binds current CT/mask hashes, original records, complete retained audit counts, exact hold IDs and
approved binary-policy evidence. It then checks a mapping proposal in memory with the existing
D-259 lineage validator. It does not publish replacement annotations or decode arrays.

| Study | Retained pancreas foreground | Mapping evidence | Permission |
|---|---:|---|---|
| PanTS_00000003 | 14,894 voxels | Complete counts and D-259 lineage verified | Not granted |
| PanTS_00000026 | 45,095 voxels | Complete counts and D-259 lineage verified | Not granted |
| PanTS_00000031 | 37,344 voxels | Complete counts and D-259 lineage verified | Not granted |

New review package:
`outputs/prowl/localizer-qualification-review-8074e048-1340-44d7-8d60-51ab151641bd/`.
Verification SHA-256:
`d495032119c701e9ff3c709293426a110ccc5a2d07c5be004b973fe00d837b28`.
This is a partial evidence review with explicit pending fields, not five synthetic `pass` receipts
masquerading as a real qualification. Mapping proposals are not published annotation records or
resolved evidence-root bindings. The original annotation mappings remain null.

The first retained-review attempt stopped before creating an output package because its proposed
mapping object omitted required schema fields and included an unsupported field. The proposal was
corrected to the existing schema; the second attempt passed. The validator was not weakened.
No source-drive access, model result, legal clearance or clinical judgment was involved.

## Verification and next concrete work

`tests/test_qualification_transition.py`: **17 passed**.
Full native suite: **937 passed**, two existing upstream torch.jit warnings. The full suite ran with
native process access for the existing synthetic memory-supervision tests. The retained-review runner
was additionally executed successfully against pinned local evidence. No dependencies changed.

Next, prepare the remaining evidence for **these same three pairs**:

1. Finish the exact source/archive/extraction assurance and release-applicability review, with a
   purpose-specific local research use record. Separate public-release restrictions. Do not require
   Quinton to adjudicate legal applicability or infer that a publisher reply alone is the only route.
2. Generate and inspect a bounded CT-mask overlay package under a separately recorded read/memory/
   output budget; retain hashes, view coordinates and the engineering alignment assessment. No
   perfect-contour requirement and no expert certification by the assistant.
3. Complete v3 accounting migration and independently reviewed five-check receipts. Only after all
   requirements pass, apply the transition checker and preserve its certificate with the old/new
   records. Unsupported requirements stay held; do not fabricate positive receipts to advance.
4. Publish and resolve the frozen executable cohort before connecting real training inputs.
