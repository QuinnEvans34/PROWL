# Terminal 24k inference-policy experiment — November 10

Quinton requested autonomous hyperparameter and postprocessing experiments on the
completed current model, with the external drive connected. This is a new,
bounded inference experiment, not a restart of the completed November 8 budget.
Lenovo's 24k→36k training remains unchanged. No optimizer updates are authorized
or needed in this screen, and no policy is deployed automatically.

## Frozen scientific scope

- Primary: corrected terminal 24k checkpoint, SHA256
  `2cb9ff72c66b67f8bcdcb081c5d3f84735a83830f693ad2990fb8139933da92c`.
- Same 70 exposed development scans, 36 positive / 34 empty, 45 reference lesion
  components and five small positive cases. Provided-pancreas-region inference;
  this is neither autonomous localization nor an independent test.
- Unchanged model, normalization, physical reconstruction, 128 cube / 64 stride,
  source hashes and full native affines. Reconstruct once per case on MPS.
- Preserve a fresh same-device raw baseline and fixed 5 mm policy. Compare raw
  counts with original CUDA results; a per-positive-case absolute Dice difference
  exceeding .01 stops execution for diagnosis. This is a prospective gross-drift
  sanity check, not proof of numerical or spatial equivalence.
- Do not reselect the checkpoint. The selected 18k checkpoint is a contextual
  comparator in the existing report; a second native inference pass is outside
  this first screen. All development results are exploratory and selection-biased.

## Exactly 54 reference-free policies

1. Raw and four unfiltered lesion-margin biases: −1, −.5, +.5, +1.
2. Five margin biases (−1, −.5, 0, +.5, +1), crossed with proximity radii
   5 / 10 / 20 mm and minimum component volumes 0 / 10 / 25 mm³: 45 policies.
3. Four seed-and-grow policies: weak margin +.5 or +1, strong seed −.5,
   proximity 5 or 10 mm. Retain a weak 26-connected component only if it contains
   at least one strong voxel. This can recover weak connected tissue while
   rejecting unseeded weak blobs; attached false positives may still grow.

The bias multiplies reconstructed lesion probability by exp(bias), then compares
it strictly with the maximum of the two original non-lesion channels. Exact ties
use the original class order (background, pancreas, lesion). Scores are not
calibrated probabilities. This is a **post-reconstruction decision change**,
not a change to tile logits, training or softmax temperature.

All proximity tests use the **fixed raw predicted pancreas**, never a reference
mask. Full affine voxel-center distances and 26-connectivity are retained.
Missing predicted pancreas fails open for distance filtering and is recorded.
Suppressed candidate lesion components become background. Bias may reassign
pancreas voxels, so the pancreas Dice guard is necessary. Zero-bias / 5 mm /
zero-volume must reproduce the standing filter exactly.

Four-bit native codes retain all five bias masks exactly, including non-lesion
fallback. Store and independently reopen these codes; replay all 54 policies
from the backup and require identical scored dictionaries. No full floating-point
probability volumes are retained. References enter scoring only.

## Gates and limits

One new four-hour cumulative wall budget starts at creation of this experiment's
external root; transfer, preparation, pilot, scoring and inference share that
deadline. No automatic retry, successor or budget reset. Largest positive and
empty native cases (6837 / 6880) run first, once, then are reused. Continue only
if a conservative 1.5× tile-rate projection fits the remaining deadline.

Preserve the previously qualified cache-release allocation lifecycle, MPS fallback
disabled, exclusive repository MPS lock, AC, memory-pressure floor, 8 GiB MPS,
12 GiB combined RSS, 50,000,000,000 byte internal and 100 GiB external reserves.
This request uses the current user's new experiment authorization; the November 8
approval and spent budget are historical, not reused as launch authority.

Keep the **26 GiB total internal backup cap** and **4 GiB new external experiment
root cap**. Before launch, prove worst-case packed native codes, model-only
weights backup and 64 MiB metadata reserve fit. Full optimizer checkpoints stay
preserved on Lenovo and are transferred privately to the external drive. Back up
only the terminal model state needed for this inference, plus its exact full-source
checkpoint binding; independently reopen and compare every tensor. Do not delete
old attempts or backups to make room. A failed projection blocks launch.

Freeze producing hashes and package versions before launch; verify again at
closeout. Supervision owns the worker and guardian, enforces resource/deadline
limits and records reaping. Any failed gate preserves evidence and stops.

## Decision and reporting

Report the highest Dice policy even if it fails safeguards, clearly labeled as
ineligible. The usable exploratory candidate must satisfy all eight existing
guards against same-device raw: Dice gain ≥.02; no lost case or reference-component
identity; unchanged-or-better small-case recall; overall recall drop ≤.01;
pancreas Dice drop ≤.01; no increase in empty alarms or total false-positive mL.
Deterministic tie-break: greatest Dice, then lexical policy name. No qualifying
candidate means retain raw, not relax guards. Compare the candidate with fixed
5 mm as well, so the existing gain is not advertised as a new discovery.

Log as an MLflow inference-policy experiment, **excluded from training hours**.
Retain per-case results, raw/CUDA differences, policy definitions, checkpoint and
source identities, resource/reaping evidence, independent replay proofs and a
database snapshot. Full 70-case denominators are required for final conclusions;
pilot or partial results are never called a complete tuning result.
