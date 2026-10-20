# Fixed development measurement comparison — CP02 / CP03

## Follow-up

[CP04](MEASUREMENT-CP04-RESULTS-2026-10-20.md) resolves the annotation encoding and inspects
source-boundary contact without new inference. Five cases now score; the original CP03 outcomes
below remain unchanged. Measurement accuracy and whole-organ coverage are still unqualified.

## Outcome

The bounded comparison is complete with explicit missing results: six cases selected before quality
inspection, four scored (two positive, two annotation-empty), one excluded for size, and one completed
prediction whose annotation failed strict binary validation. No substitutions or inference retries.
The unchanged largest-union candidate passes the relative CP01 screen on only one of four scored
cases. It is **not qualified for reliable measurements or UI promotion**. A relative screen pass
also does not establish acceptable absolute error: the passing case still has 6.905mL of lesion
false positives. The original prediction and live UI measurement guard remain unchanged.

W03-04 and W03-05 are complete for their bounded literature scopes; Quinton explicitly accepted
both the review packet and UI walkthrough. The independent evaluation and AI-05 measurement
acceptance remain separate and open.

## Intake and controlled input amendment

The authorized training-owner handoff confirms 70 current development cases (36 positive,
34 annotation-empty), disjoint from 1,333 training cases. All six selected cases were exposed in
the completed raw step6000 development evaluation. Selection uses the first three sorted IDs in
each admitted annotation stratum, with no quality scores used. All18 local source hashes/sizes
match admitted identities. The handoff itself used retained metadata, not a new remote array audit.

CP02 header-only admission accepts case29. The five other cases have unspecified spatial units
on pancreas masks; case927's lesion mask also omits units. All masks have exactly matching CT
shapes and affine matrices; all six CTs explicitly use millimetres. Case139 independently exceeds
the original32M-voxel/128MiB decoded-image limits. CP02 retains these failures and performed no
new inference or array decoding.

The separately frozen [CP03 plan](MEASUREMENT-UNITS-CP03-PLAN-2026-10-20.md), committed in68355b9
before real preparation, permits explicit CT-linked unit inheritance on hash-bound, exact-grid
annotations. Seven synthetic tests verify preservation and reject conflicting units/grids/hashes
and overwrites. Five private derived masks were prepared for the four eligible new cases.
Independent streaming comparisons confirm byte123 is the only changed uncompressed byte in each;
voxel bytes and temporal-unit bits are unchanged. Originals, inference code, checkpoint, restoration,
component selector and screen criteria are unchanged. This is a recorded input interpretation,
not evidence that the original headers contained units. It is not enabled as a silent UI fallback.

## Per-case results

IDs below abbreviate PanTS_00000xxx. All volumes are mL, rounded for display; exact counts and
arithmetic are retained privately. Empty references are not verified healthy patients.

| Case | Stratum | Raw lesion | Candidate lesion | Reference lesion | Candidate lesion Dice | Original screen disposition |
|---|---|---:|---:|---:|---:|---|
| 29 | Positive; reused | 11.815 | 6.229 | 2.911 | 0.584 | Fail: parenchyma absolute-volume error worsens |
| 84 | Positive | 15.048 | 10.382 | 4.099 | 0.564 | Fail: parenchyma absolute-volume error worsens |
| 927 | Positive | — | — | — | — | Prediction succeeds; comparison fails strict binary reference validation |
| 139 | Annotation-empty | — | — | — | — | Excluded:42,339,780 voxels exceeds unchanged limits |
| 514 | Annotation-empty | 10.600 | 6.905 | 0 | 0 | Relative screen passes; absolute accuracy remains unqualified |
| 698 | Annotation-empty | 6.874 | 4.831 | 0 | 0 | Fail: crop and CT-face contact persist |

| Case | Extent reference | Extent raw → candidate | Extent absolute error raw → candidate | Parenchyma absolute error raw → candidate |
|---|---:|---:|---:|---:|
| 29 | 84.291 | 92.205 → 84.269 | 7.915 → 0.022 | 0.989 → 3.340 |
| 84 | 122.432 | 149.751 → 104.420 | 27.319 → 18.011 | 16.370 → 24.295 |
| 514 | 43.597 | 87.786 → 75.083 | 44.188 → 31.486 | 33.588 → 24.581 |
| 698 | 62.986 | 93.882 → 65.300 | 30.896 → 2.314 | 24.022 → 2.516 |

Extent means pancreas OR lesion; parenchyma means pancreas AND NOT lesion. These are distinct
reference targets and must not be interchanged when reporting an apparent volume improvement.

## Findings and manual arithmetic review

All removed components in the four scored cases have zero reference-pancreas/lesion overlap;
TP and FN are unchanged for every target. Yet positive-case parenchyma absolute-volume errors
worsen: existing false positives partly compensated for missed tissue in the raw scalar volume.
Removing false positives improves spatial overlap without recovering missing tissue. This is
why an apparently close volume alone is insufficient evidence of a correct outline.

For the two scored positives, mean lesion Dice rises0.39459→0.57409 and mean absolute lesion-volume
error falls9.927→4.801mL. Neither passes all original rules. Case84's surviving lesion component
has2,677 reference-overlap voxels and4,127 false-positive voxels: overprediction is within the
surviving lesion region, not just detached fragments. Case29 retains the previously documented
all-false-positive1,385-voxel lesion region plus another partly overlapping region.

For the two scored annotation-empty cases, mean false-positive lesion volume falls8.737→5.868mL,
but both still predict lesions. Case514 has one residual1,448-voxel false-positive lesion component;
case698 has seven totalling7,817 false-positive voxels. Undefined empty-reference recall remains
null. The sample does not support a population specificity or healthy-patient claim.

Case698 retains CT-face and crop contact even after component selection. This differs from case29's
removable detached edge fragments; inspect the native anatomy/reference contact before attributing
it to truncation or predicting that cleanup will resolve it.

Case927's pancreas reference is exactly0/1; its scaled lesion values are0 and1.0000000591389835
(11,301 nonzero voxels). The strict comparison correctly rejects this representation. Its failure
and successful inference are preserved. No tolerance, rounding or label threshold was introduced
after observing the outcome; no model rerun is needed for a separately qualified scoring adapter.

Reviewed all12 target pairs/24 variant rows, TP+FP and TP+FN counts, signed/absolute mL arithmetic,
removed-component sums, reference-lesion overlap preservation, residual component counts and empty
recall. Automated arithmetic checks agree with the manual review. No new anatomical visual-review
or clinical accuracy claim is made.

## Execution, provenance and limits

Four new supervised inferences succeed and are reaped:84 in24.94s,927 in12.65s,514 in9.99s,
698 in21.95s; total69.53s. Maximum sampled worker-process-group RSS1,711,095,808B (~1.59GiB).
The sequential preparation/inference/comparison block completes in77.35s; retained artifacts are
approximately89MB, below2GiB. Internal free space remained above100GiB. Ollama had no resident
model during the block. Case29's existing package/comparison hashes were verified and reused.
No training, protected test arrays, retries, alternate segmentation correction or service change.
Live literature health responds and UI5180 returnsHTTP200 after the work.

Private evidence:
- `outputs/prowl/measurement-subset-cp02-20261020/`: frozen selection, original header admission,
  executed remote selection command, transcribed metadata receipt and pinned CP03 orchestration.
- `/Volumes/PROWL-Data/PROWL/artifacts/measurement-subset-cp03-20261020/`: original/derived bindings,
  unit receipts, four job packages/execution receipts, three new successful comparisons, one failed
  comparison, component diagnostics, status and arithmetic review. Original CP01 evidence unchanged.

Selection SHA-256: `3da195adac01d1a12642ec78269acc7b3aed057df66603dfdcd952fd5bee1f9b`.
Local transcribed metadata receipt SHA-256:
`58d4bad7b9209c8891967896bfaca52bc0ada8e9eed9292915458827cb331802`.
It is a saved transcription of the completed remote command's JSON, not a byte-identical copy of
the separately saved Windows receipt. Current development and control pins remain those in CP02.

## Next decision

The requested bounded diagnosis is delivered; AI-05 is still In Progress. First qualify an explicit
near-binary annotation interpretation using source scaling evidence and synthetic rejection cases,
then score case927's retained prediction without inference. Separately audit case698's native
boundary/reference geometry. These address the two demonstrated data/coverage gaps before another
segmentation correction is chosen. Further improvement must address false-positive lesion tissue
inside retained components; another largest-component rule alone is not supported by these results.
Reliable measurements, anatomical review and independent acceptance remain required deliverables.
