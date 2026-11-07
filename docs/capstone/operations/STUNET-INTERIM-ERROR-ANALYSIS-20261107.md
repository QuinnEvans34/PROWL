# STU-Net interim error analysis — November 7

The new model is learning, but its remaining errors include both missed annotation
and excess predictions. The clearest subgroup weakness at 6k is the five cases
with less than 1 mL of total reference lesion volume. This review uses existing
development metadata only; it does not select a final checkpoint, diagnose spatial
causes, demonstrate patient independence or change the running experiment.

## Evidence admitted

Lenovo published `0da40f1ae66e59e7e6fa8a7debdfea4b4c277c2c`. Its
[native metadata export](../coordination/LENOVO-STUNET-NATIVE-METADATA-20261107.json)
is copied byte-for-byte, 295,079 bytes, SHA256
`9528af9e5817f74d3a813c096b261d1e80b4ac688773697c272cd4e1f0e971a9`.
Capture: November 7 at 20:49:21 UTC. It contains all 70 cases at 2k/4k/6k;
8k was incomplete and is excluded. Each report retains 36 positives, 34 empty
references and 45 reference components. Source report/checkpoint identities and
peer-verified backup equality are recorded; the Mac did not reopen checkpoint,
scan, mask or probability bytes or independently inspect the live worker.

The new reader verifies the explicit export hash, run/receipt/producer identities,
exact membership, unchanged reference counts, native geometry/volumes, Dice
arithmetic, component bounds and complete summary denominators. It derives
recall, precision, FP/FN voxels and missed-component counts from saved integers;
these fields were **not originally stored** and are labeled accordingly in the
[derived report](STUNET-INTERIM-ERROR-ANALYSIS-20261107.json). Empty/empty Dice stays
null. Precision is null for zero predictions, so the defined-positive precision
denominator is reported separately. No scan scoring or model call occurred.

## Learning and remaining errors

| Completed validation | 2k | 4k | 6k |
| --- | ---: | ---: | ---: |
| Positive-case macro lesion DICE, all 36 | .144179 | .222087 | .347182 |
| Positive-case macro recall, all 36 | .310745 | .320046 | .452044 |
| Positive-case macro precision, defined cases only | .118867 (36) | .216976 (35) | .380762 (35) |
| Positive cases with any overlap | 28/36 | 26/36 | 30/36 |
| Reference components with any overlap | 30/45 | 31/45 | 36/45 |
| Empty cases with any lesion prediction | 33/34 | 29/34 | 26/34 |
| False-negative voxels | 133,456 | 115,368 | 91,076 |
| False-positive voxels on positive cases | 496,220 | 177,641 | 148,483 |
| False-positive voxels on empty cases | 812,735 | 189,237 | 73,002 |

Recall and defined precision both improve; the higher DICE is not explained solely
by reducing prediction volume. However, at 6k, 20/36 positive cases still miss more
than half their annotation and 10/36 predict at least twice the reference lesion
volume. These statements can coexist because predictions can miss one area and
label another. Counts alone cannot distinguish remote errors, attached spillover
or boundary mistakes. Raw voxel sums are descriptive across differing voxel sizes;
the JSON also derives physical-volume totals under the inherited geometry policy.

From 4k to 6k, 25 positive cases improve, six worsen and five are unchanged. Case
7868 becomes a complete miss with no lesion prediction, while several other cases
recover overlap. Case-level learning is not uniformly monotonic.

## Small lesions and review queue

The exact pinned native metric producer uses 26-neighbor connectivity and total
reference lesion-volume bands: small <1,000 mm³; medium 1,000–10,000 mm³ inclusive;
large >10,000 mm³. These are case-total bands, not individual-component size bands.

| 6k band | Cases | Mean DICE | Mean recall |
| --- | ---: | ---: | ---: |
| Small | 5 | .047820 | .209303 |
| Medium | 24 | .383014 | .498325 |
| Large | 7 | .438158 | .466750 |

Three of five small cases have zero overlap: 1823, 4681 and 7868. The other two,
4267 and 8339, have some overlap but very low precision (.105779 and .030261).
Thus this group has both missed-lesion and excess-prediction problems; merely
suppressing low-confidence predictions cannot recover its complete misses.

The complete 6k miss list is **1823, 2514, 2889, 4681, 6755, 7868**. Four cases
are missed at all three saved checks: 1823, 2514, 4681, 6755. These are aliases,
not verified independent patients. Other useful saved-count review examples:

- 2028 and 1347: recall .990958/.970362, precision .219156/.225817. Substantial
  excess prediction is a plausible target for a confidence-policy screen.
- 8711: recall .554447, precision .098465, about 56.39 mL false prediction under
  inherited native units. Spatial location/cause remains unreviewed for this model.
- Empty-reference cases 6454, 5363, 6115, 6901 and 6880 have the largest saved
  false-prediction volumes at 6k. They are a review queue, not a tuned exclusion list.

Keep all 70 cases and all failures. Do not crop references, discard inconvenient
cases or remove all but the largest predicted lesion to improve the score.

## Producer inspection and probability availability

[Source inspection receipt](STUNET-INTERIM-PRODUCER-INSPECTION-20261107.json) reconciles
all six recorded producer hashes against the peer Git commit. Four match exact
Git bytes; two match only the exact LF-to-CRLF serialization used on Windows.
The native metric and input producer match exact bytes. This is a specific
serialization observation, not a general tolerance or live-pin requalification.

Pinned `predict` reconstructs probabilities, takes argmax and returns metrics.
The inspected worker saves metrics and checkpoints, not per-case probability
volumes. The export therefore cannot support a retrospective threshold sweep.
No unrelated storage was searched to claim that no probabilities exist anywhere.
A confidence screen needs a separately qualified inference pass after training,
using one common probability reconstruction for raw and candidate policies.

## Next decision

Keep the current 12k/60h run and existing hourly monitor unchanged. Assess the full
six validations and selected/terminal errors after completion. No live schedule,
loss, sampler, horizon, source or producing pin was changed.

The next proposed experiment is a bounded confidence-policy screen, not another
multi-day training run. It tests whether some of the excess prediction can be
removed without sacrificing detected components, small-case recall or pancreas
quality. It cannot answer how to recover raw misses. If the final run retains
the small-lesion weakness, the subsequent training question is size-balanced
lesion sampling with coverage retained; that is deferred, not launched or frozen
from this interim snapshot. See [CAP-EXP-020 proposed design](CAP-EXP-020-PROPOSED-20261107.md).

Exact source/reference hashes match the retained November 2 selected-control
handoff, but equivalence with **both final KD arm bindings remains unverified**.
No cross-model deltas, independent-patient interval, formal hypothesis verdict
or promotion are produced. The higher-level G4/G5 requirements remain open.

## Verification and reproduction

Nineteen metadata tests pass: actual complete export/CLI, integer arithmetic,
undefined precision/empty Dice, newly missed/recovered cases, malformed/partial
cohorts, changed references, geometry, metrics, components, receipt/hash refusal,
size bands and preserved output. The actual analysis reproduces exactly into a
fresh output and the source bytes remain unchanged.

```sh
PYTHONPATH=. .venv312/bin/python scripts/diagnostics/review_stunet_interim_20261107.py \
  --export docs/capstone/coordination/LENOVO-STUNET-NATIVE-METADATA-20261107.json \
  --sha256 9528af9e5817f74d3a813c096b261d1e80b4ac688773697c272cd4e1f0e971a9 \
  --output outputs/prowl/testing/reviewer-flow-20261107-01/stunet-interim-reproduced.json
```

The reader accepts at most 1 MiB of metadata, opens no data paths from the JSON,
checks that the export stays unchanged and exclusively creates output. No new
training hours, RUNNING experiment, MLflow write, protected test access or GPU work.
