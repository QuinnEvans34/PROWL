# Week 5 autonomous baseline: saved metadata review

The completed Lenovo baseline is ready for a focused visual error review. The
Mac admitted its hash-bound metadata and independently recomputed reported Dice,
recall, voxel/component totals and evaluation-region coverage. This was CPU-only
work while the resumed KD treatment continued; no images, model or live GPU
were used. The reviewer workflow and full G3 acceptance remain open.

## Results and denominator

| Measure | Saved baseline result |
| --- | --- |
| Requested development cases | 70 |
| Completed predictions/scores | 63: five reused, 58 new |
| Declared admission failures | Seven; retained, without imputed Dice |
| Mean lesion Dice, completed positive cases | 0.3712019132 on 32 cases |
| Positive cases with any lesion overlap | 30/32 |
| Reference-empty cases with lesion predictions | 31/31 |
| Reference lesion components with any overlap | 35/40 |
| Predicted components with no annotated lesion overlap | 394 |
| Expanded evaluation-region coverage | All pancreas annotation in 63/63; all lesion annotation in 32/32 positives |

The five component misses are in cases 4681, 8769, 6755, 2889 and 2235. Cases 4681
and 8769 have no lesion overlap; the other three retain some overlap elsewhere.
These are metadata findings, not spatial diagnoses or clinical detection results.
Full annotation coverage in the saved regions means region clipping does not
account for these misses. It does not establish why the segmenter missed them.

There are 81,211 false-negative and 316,768 false-positive lesion voxels across the
completed cases. Of the latter, 120,330 are in the 31 reference-empty cases. Counts
are descriptive; absence of an annotation does not independently establish health.

Failures remain separate from segmentation quality: cases 6011, 5780, 1823, 2935,
6901 and 6115 failed CT spatial-unit admission; 5592 exceeded the preflight
resampling resource limit. They were not silently excluded or assigned zero Dice.
These are results conditional on the 63 completed cases, not a 70-case Dice average.

## Next visual review

1. Inspect native CT/contours for the five missed-component cases above.
2. Inspect the largest raw false-positive counts:8769,8711,2889,6755 and4681.
3. Compare the observed error patterns with the existing four-case review;
   record evidence and limitations before proposing another model experiment.

The [complete review JSON](WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.json)
contains all63completed case records, seven failure identities, three ordered
review queues and original source-report hashes. Queues are suggestions for
inspection, not new acceptance thresholds. Raw voxel rankings span different
grids and do not rank physical volume or clinical severity. The58new saved
scores carry at least one unknown reference-unit assumption; those flags remain
visible. No reference units or saved predictions were repaired by this analysis.

All70cases are exposed development. Probability equivalence remains
**UNQUALIFIED** under the approved bounded exception; H0 is NOT TESTED and no
independent generalization or clinical acceptance is claimed. This autonomous
pipeline's Dice must not be directly compared with supplied-region KD Dice as
though the inference scopes were matched.

## Provenance and verification

- Reader/tool commit: `41ff9c7` (20 CPU tests pass, including invalid transfers,
  failure imputation, empty-reference Dice, contradictory counts and mixed units).
- Peer publication: [Lenovo d290d43](https://github.com/QuinnEvans34/PROWL/commit/d290d43cdcbc2a9dc541ac722977d98e3985ecc8).
- Immutable [source metadata](https://github.com/QuinnEvans34/PROWL/blob/d290d43cdcbc2a9dc541ac722977d98e3985ecc8/docs/capstone/operations/WEEK-05-AUTONOMOUS70-CLOSEOUT-20261104.json), SHA256
  `3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6`.
- RequestSHA `ed67a10ab6cd59a0cbf91ff42bb4cb8152882d06eafdaa879fbbb9e8a91a7d2e`;
  readySHA `19e6f8b1e981145281c35bfcbb7293dbe9ea99b5d07c2e1cea7447e65d1d2845`.
- CompletionSHA `1fa0794771efe461541c1d7cc200be7fb60e240cbce9aabffc36856eea2c5d9e`.
- Lenovo reports710output/backup pairs,12preparation backup pairs,294repository
  pins matching and successful worker cleanup. Mac verified the transferred
  JSON hash and its internal arithmetic, not Windows artifact bytes again.
- All139active Mac KD pins still matched after adding this separate tool. KD
  advanced through14123 with teacher access; MLflow and initial backups verified.

Initial local report admission stopped before output creation because the reader
incorrectly required both reference-unit fields to have the same spelling. The
frozen scorer permits either reference independently to be unknown. Inspection
found38unknown/mm,20unknown/unknown and five mm/mm pairs; an exact-policy reader
and synthetic mixed-unit regression fixed that reporting error. Failed-attempt
notes remain at `outputs/prowl/autonomous70-metadata-review-20261104-attempt01`;
successful analysis at `outputs/prowl/autonomous70-metadata-review-20261104-03`.
There was no inference/scoring rerun or producer change.

To reproduce after fetching the immutable source JSON to a local file:

```sh
.venv312/bin/python scripts/diagnostics/review_autonomous_baseline.py \
  --source /absolute/path/to/WEEK-05-AUTONOMOUS70-CLOSEOUT-20261104.json \
  --sha256 3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6 \
  --request-sha256 ed67a10ab6cd59a0cbf91ff42bb4cb8152882d06eafdaa879fbbb9e8a91a7d2e \
  --ready-sha256 19e6f8b1e981145281c35bfcbb7293dbe9ea99b5d07c2e1cea7447e65d1d2845 \
  --output /absolute/path/to/a-fresh-review-directory
```

An existing output directory is refused. The tool never imports model or image
libraries, writes MLflow, changes source records or starts a job.
