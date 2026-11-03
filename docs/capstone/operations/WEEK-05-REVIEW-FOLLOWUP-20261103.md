# November 3 saved-evidence and reviewer follow-up

CPU-only work while Mac KD continuation03 runs. Reviewed the committed Windows
four-case report at origin/codex/week05-cuda-readiness (07f7efb), not new model
inference or a visual inspection of the remote CTs/contours.

## What the saved evidence supports

- Case4681 has zero lesion overlap in both arms despite complete annotated-field
  containment. Expanding the crop is not a demonstrated remedy.
- Case6755 overlaps only one of two reference components; autonomous lesion voxel
  recall0.211380 and provided-region0.255761. Any-voxel component detection is not
  adequate lesion delineation.
- Case909 has an empty reference and autonomous false-positive volume11.554mL
  versus1.105mL provided-region. Preserve undefined lesion Dice, not a fabricated
  zero or perfect score.
- Case2028 has high lesion recall but false-positive volume worsens under the
  provided region (10.419→20.144mL). A smaller region is not uniformly better.
- Whole-surface distances include remote false-positive components. They cannot
  be interpreted as boundary accuracy of correctly matched lesions.

Next useful imaging review: inspect retained native contours and component bounds
for4681 and6755, then false positives in909/2028. No new threshold, crop, cohort or
training recipe chosen from these four exposed cases.

## Reviewer identity and history

ReviewDecisionPanel now scopes its internal instance to base plus manifest hash.
Two tests first failed: a changed prediction retained the prior draft, and a late
save acknowledgment could populate the new prediction's history. Both now pass.
SavedPredictionView already supplies the corresponding key; this is component-level
hardening, not a claim that the present screen demonstrated cross-case corruption.
Old saves may complete server-side, but cannot populate a different panel instance.
Existing navigation confirmation and durable idempotent-save behavior remain.

Added successful revision2/save/reopen regression: both revisions are retained,
expected_latest_id binds the previous event, and the reopen link preserves the
same manifest identity. Six focused suites:28tests pass. Vite production build
passes with existing large-chunk warnings. No browser/GPU rendering benchmark or
live model answer test performed. Remote evaluation packages were not imported
into the application or represented as available there.

One-time class pause scheduled around09:32MST using the existing cooperative v3
pause protocol. A scheduled request is not proof of cleanup: verify checkpoint,
independent backup and worker exit before disconnecting. The hourly monitor and
one-time pause task must be paused after the safe stop.

## Afternoon: distinguish repeated live analyses

Found another identity collision: App's display time contains only hour/minute,
but summary drafts and literature context used that display time to identify a
live result. Added a per-response session UUID to both identities, retaining the
readable time label. This does not substitute for durable manifest provenance.
The same-minute regression failed before the fix and passes afterward;25focused
tests pass, production build passes with existing chunk warnings. Commit9b5c674.
No live inference was launched for UI validation.

## Afternoon actual native overlay review

Received and verified the separate5,048,320B image/score gallery archive SHA
3ebf4af3d2667bc9abe9eec3e11f9328df83d88f720ddcf62927bfdd4af0e0dd.
All28members verified before import. Visually inspected all six retained sheets on
the Mac: two missed-reference targets plus largest false-positive targets for each
arm of909/2028. Three planes, orientation/world coordinates and a common window
are shown; paired rows use the same slices within each sheet. Component-based
slice selection is representative rather than an exhaustive scan review.

- 4681: the circled0.20555mL reference component is visibly separate from predicted
lesion regions in both rows. Complete region containment did not yield overlap.
- 6755: the circled0.68154mL reference component is missed in both rows, while
predictions elsewhere are visible. The other reference component has partial
coverage; any-overlap detection alone overstates delineation quality.
- 909: the largest autonomous false-positive target is separated from the reference
pancreas outline on the selected coronal/sagittal views and absent there in the
provided-region row. A different false-positive target near the pancreas remains
in the provided-region arm. Empty lesion reference is not a clinical diagnosis.
- 2028: false-positive predicted regions away from the reference pancreas outline
appear in both arms and are larger in the provided-region row on the selected
slices, consistent with retained false-positive volumes. A smaller region alone
is not an established remedy.

These are observations of mask/annotation relationships, not medical interpretation
or proof of the failure mechanism. No prediction regenerated, threshold changed,
case excluded or new model trained. Preserve the fixed larger-baseline recipe;
report component misses and false-positive behavior separately from aggregateDice.
Private image manifest, per-image hashes and Mac inspection receipt retained under
outputs/prowl/week05-review-gallery-20261103-01. No CT/mask/image payload in Git.
