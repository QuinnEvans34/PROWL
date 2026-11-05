# Matched KD error-review preparation

The Mac can now reconcile the paused/resumed KD lineage into a hash-bound,
read-only error-review packet while training continues. The new adapter reuses
the existing native report/component validation and error-summary math. It reads
JSON and complete journal-line prefixes only: no CT, mask, checkpoint, model or
MLflow write. Code is published in `2af98f7`.

## What is ready

- All twelve control validations (2k through 24k) and seven completed treatment
  validations (2k through 14k) were admitted from eight journal segments. The
  treatment still needs 16k, 18k, 20k, 22k and 24k at this snapshot.
- Each admitted report requires a completed validation journal event, the full
  ordered 70-case cohort, an identical independent backup and a report-bound
  component sidecar. Reference target/geometry/component identities match across
  validations and both arms. Only auxiliary KD weight differs between designs.
- Replay checkpoints must join at the same update. Conflicting same-step report
  copies, missing backups, altered reference semantics and mixed scopes fail.
  Live journals can append; their observed complete-line prefixes cannot change.
- The control's original cleanup-only failure remains explicitly recorded as
  failed historical supervision. Its separately reviewed completed optimization
  and bound result are not rewritten into a healthy original worker outcome.
- 49 CPU tests pass across the new adapter and existing native-review math. Tests
  include a full 70-case synthetic CLI contract, partial-horizon handling, source
  preservation, recipe drift, replay gaps, bad hashes and output reuse rejection.

## Current same-update diagnostic: 14k

| Measure | No-KD control | KD treatment |
| --- | ---: | ---: |
| Positive-case mean native lesion Dice | 0.294552 | 0.332939 |
| Positive-case mean voxel recall | 0.368768 | 0.533653 |
| Positive-case mean voxel precision | 0.337540 | 0.301739 |
| Positive cases with any overlap | 32/36 | 33/36 |
| Missed reference components | 8/45 | 8/45 |
| Reference-empty cases with predictions | 31/34 | 34/34 |
| Predicted lesion voxels in reference-empty cases | 103,008 | 239,211 |
| Predicted lesion volume in reference-empty cases | 78.076mL | 175.110mL |
| Total false-negative lesion voxels | 116,992 | 93,319 |
| Total false-positive lesion voxels | 241,993 | 436,828 |

At this matched checkpoint, better recall and overlap accompany lower precision
and greater false-positive burden. This is not a final KD result or acceptance
decision. The full [case-paired diagnostic](KD-MATCHED-ERROR-PREPARATION-20261104.json)
retains all 70 cases, including negatives and complete misses. No case was selected
or excluded based on these outcomes. Empty-case Dice is not used as a positive-
case quality measure. Native voxel counts and physical volumes stay separate.

These are supplied-pancreas-region results on 36 positive/34 reference-empty cases,
not the autonomous 63 completed/7 failed baseline. Those inference scopes and failure
denominators must not be mixed. Selected visual examples remain qualitative.

## Provenance follow-up: cases 6755 and 2889

Lenovo published a [17-record retained-metadata review](https://github.com/QuinnEvans34/PROWL/blob/467e19124d1a749bbe5f60e20d6e4e16224b950e/docs/capstone/operations/WEEK-05-TWO-CASE-PROVENANCE-20261104.md).
The files have distinct saved hashes/byte lengths and annotation files, but the
same native dimensions/spacing. Their saved affines differ by x/z flips and a
derived 300.800005 mm positive-axis z-origin shift. Those facts do not establish
independent patients or shared underlying anatomy. Retained `study_id` values
are case aliases, not verified patient/DICOM relationship identifiers.

No patient/study/series linkage was found in the reviewed records. The finding
does not assert that the dataset publisher lacks such information. Both cases
and the 70-case denominator remain unchanged. No scan, mask, new header, array,
inference or scoring reads occurred for this follow-up. Earlier interactive
review time was uninstrumented; only publication time was measured, so no measured
cumulative 10-minute compliance claim is made. The 17 records meet the 30-record cap.

Provenance JSON SHA256
`996be9c75ecc8c0dd0574d211cda8f2cd9ce0216774a95d5eba74b0f56b6bb15`
matches the publication. Mac also checked both cases' retained source hashes,
native shapes and affines against the already imported visual packet.

## What remains before final interpretation

1. Complete the treatment's full 24k horizon and all twelve native validations;
   verify independently selected and terminal endpoints, backups, actual worker
   cleanup and read-only MLflow closeout. Preserve the known control failure and
   its reviewed closeout separately.
2. Resolve the resampling-unit question before describing bootstrap intervals as
   verified independent-patient uncertainty. Case aliases do not establish patient
   independence. Patient grouping requires a verified mapping; no grouping or
   outcome-based exclusion was inferred here. This preparation emits point
   estimates only, no confidence intervals or H0/practical verdict.
3. Reuse the existing frozen comparison policy and component guards after full
   evidence review. The old Windows command expects a single completed root;
   it is not silently pointed at a resumed Mac directory or given relaxed gates.
   The new packet supplies the validated Mac report/sidecar inventory and
   continuation prefixes for that final platform-specific closeout.
4. Preserve spatial uncertainty: aggregate validation reports can quantify missed
   components, extra voxels and volume expansion, but cannot locate remote versus
   pancreas-adjacent false positives or isolate attached spillover. Those categories
   need separately bound predictions/visual evidence from the same inference scope.

No new filtering, crop, threshold, verifier training or experiment follows
automatically from these observations. KD's scientific recipe remains frozen.

## Reproduction and retained evidence

```sh
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
.venv312/bin/python scripts/diagnostics/prepare_mac_kd_error_review.py \
  --root /Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-treatment-resume-20261104-01 \
  --ready-sha256 7cf54250da7f109723f48678fcbfc3763b953170618a9f0215c3862a417bc3f7 \
  --output /absolute/path/to/a-fresh-preparation-directory
```

The successful local packet is at
`outputs/prowl/kd-error-review-preparation-20261104-02/preparation.json`, SHA256
`1bf3c6af5bf97fc1aa54b5cc543b426a076f5c8bdf77e34eba58723c1f176e46`.
It binds 82 metadata files and eight journal prefixes. The earlier01snapshot is
preserved. Output directories are never overwritten; active producer files are
not modified. Appended training progress can make a later fresh packet newer
without invalidating the recorded snapshot. No new scheduled task was created.
