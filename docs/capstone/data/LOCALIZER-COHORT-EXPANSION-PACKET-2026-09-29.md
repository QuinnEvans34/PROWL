# Bounded cohort expansion implementation packet — D-280

Current state: descriptive candidate selection and header preflight complete; no new case permission,
validation execution or training. Read [measured result](../operations/LOCALIZATION-PROGRESSION-RESULTS-2026-09-29.md)
and [selection plan](LOCALIZER-EXPANSION-PLAN-2026-09-29.md). This packet is the next implementation
boundary, not an assertion that the work below has already passed.

## Exact evidence inputs

- Candidate receipt `3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1`:
  16 original-train and 12 original-validation candidates, CT + pancreas only.
- Header receipt `950a113e6d18d795b90fe1bce7f68555a5e302b48e88de8b97b8651b9e4e73ad`:
  all grids pairwise agree; case 6350 lacks a declared physical-unit anchor in both headers.
- Original membership hashes, source inventory, file identity observations and phase/spacing
  selection evidence are carried in the candidate package. Verify every pin before use.
- Preserve existing two-case qualification and experiment artifacts; their prior assessments remain
  scoped to their own exact inputs. Preserve candidate 6350 while its evidence is unresolved.

## A. Versioned purpose and consumer boundaries

Create an explicit validation-reference purpose and schema/identity version; never grant validation
annotations `training_target` just to reuse the existing training-only helper. Separate cohort role,
annotation permitted use and consumer operation. The optimizer accepts only qualified train cohorts;
evaluator accepts the registered validation-reference role. A validation cohort is disjoint from all
training ancestry in its protection family. Freeze requested members and report shortages/holds.

Retain the existing two-case v2 registry/loader untouched for historical replay. New generic package
replays reviewed per-case evidence and current manifest pins, not a fixed count of three historical
transitions. Reject stale, missing, changed or newly held evidence and duplicate CTs across roles.
Known/probable unresolved subject overlap also blocks the affected use; document the study-as-subject
fallback's biological-identity limitation. Role-safe tests precede real cohort publication.

## B. Exact full-content qualification job

Prepare a hashed machine-readable job for the same 56 inventory paths before execution. No lesions,
publisher-test payloads, new candidates or unbounded scans. Candidate totals: 693,588,981 compressed
bytes / 1,781,724,105 nominal array bytes. Sequential execution, one case at a time, at most 1 GiB
compressed input, 4 GiB cumulative decoded array bytes, 16 GiB RSS, 1,200 s, 256 MiB local evidence,
100 GiB internal free floor. Test caps/termination and exact metadata continuity before execution.

Hash every consumed file, verify full gzip completion and complete-array finite/encoding checks;
record CT range, original dtype/scaling, mask values, strict-binary policy lineage and empty/nonempty
status. Bound each declared array and reject malformed dimensions or payload overflow before allocation.
Compare new hashes with existing cases and selected cross-role peers. Preserve any mismatches as holds.
Do not infer eligibility from ranges alone. No source rewrites, resaved masks or unit-header repairs.

Review physical-unit evidence and alignment with bounded contact sheets (same fixed, documented
sampling rule for all candidates). Unknown units may be supported by an independently mm-declared
paired image with matching complete geometry and reviewed source/alignment evidence; header matching
alone is insufficient. Where no support exists, retain a hold instead of guessing. Read only the
selected CT/pancreas files, not hidden reports or unrelated source material.

## C. Publish and evaluate

Only after A/B evidence passes, create new immutable role-specific qualification/cohort packages and
exercise resolver refusal tests against altered permissions, membership and bytes. If some candidates
remain held, explicitly record the requested-versus-qualified counts and revise the executable subset
in a new frozen record; do not silently substitute or erase the held candidate. Validation result
coverage must subsequently include every member of the frozen executable evaluation cohort.

Preprocess each consumed member with verified geometry/resource bounds. Freeze a modest multi-case
run with resource estimates measured from these inputs. Evaluate full volumes on the separate
validation cohort; report per-case mask precision/recall/Dice, box coverage/volume and failures.
Do not select a production ROI policy or claim final cascade acceptance until complete Stage 2
mapping, lesion-reference permissions and effective-resolution/resource gates also pass.
