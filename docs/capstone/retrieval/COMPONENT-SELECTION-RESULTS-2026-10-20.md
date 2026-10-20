# CP01 results: filtering helps, measurements still unqualified

**Decision:** the frozen development screen **failed**. Do not promote the candidate or enable
size answers. The rule removes disconnected false predictions on this case, but substantial
lesion error remains inside the retained pancreas. The original live package is unchanged.

## Comparison

The [plan](COMPONENT-SELECTION-PLAN-2026-10-20.md) was committed as `d0d6686` before the lesion
annotation was opened. Implementation was committed as `b3b8ace` before the actual comparison.
One retained, previously exposed development case and fixed step6000 prediction were used;
no new inference, new checkpoint, training, protected data or extra case selection occurred.

The selector keeps the unique largest26-connected predicted union component, preserving the
original1/2 labels. It never receives references. It removed ten components totaling4,398 voxels:
1,303 pancreas-label and3,095 lesion-label voxels. **Every removed component has zero overlap
with either annotation.** No previously correct voxel or reference-lesion overlap was lost.
The candidate clears the crop and image boundaries.

| Target | Annotation volume | Original volume | Candidate volume | Original → candidate Dice | Candidate recall |
|---|---:|---:|---:|---:|---:|
| Pancreas extent, including lesion | 84.291 mL | 92.205 mL | 84.269 mL | 0.86567 → 0.90643 | 90.63% |
| Pancreas parenchyma, excluding lesion | 81.380 mL | 80.391 mL | 78.039 mL | 0.86781 → 0.88061 | 86.25% |
| Lesion total | 2.911 mL | 11.815 mL | 6.229 mL | 0.36250 → 0.58401 | 91.69% |

These numbers are **offline evaluation measurements**, not accepted UI size answers. The
annotation is a dataset reference, not a new radiologist certification. The provided pancreas
annotation also selected the inference region, so this is not an independent localization test.

Reference semantics: pancreas extent uses pancreas OR lesion; parenchyma uses pancreas AND NOT
lesion, matching lesion-priority target construction. This case has1,613 reference-lesion voxels,
all inside the46,709-voxel provided pancreas, and one26-connected reference lesion component.
Original and candidate both retain1,479 of its voxels and miss134. References aligned exactly
with the prediction's native shape/affine and declared mm units; no resampling was applied.

## Frozen decision rules

| Rule | Result |
|---|---|
| No crop/image contact or outside-region prediction | Pass |
| No correct voxel removed for any target | Pass |
| No reference lesion component loses overlap | Pass |
| Dice nonworsening for all targets | Pass |
| Absolute volume error nonworsening for all targets | **Fail: parenchyma error rises from0.989 to3.340 mL** |
| Strict false-positive reduction for at least one target | Pass |

The failed volume rule illustrates cancellation: the original parenchyma prediction's false
positives partly offset its missing reference voxels. Removing those false positives improves
spatial Dice but exposes more underestimation in its total volume. We retained the frozen result
and did not relax that rule after seeing it. Separately, candidate lesion volume remains114.0%
above the reference, so even a relaxed aggregate-volume screen would not demonstrate reliable
lesion measurement. A near-perfect pancreas total can likewise hide thousands of spatial errors.

## Residual lesion diagnosis

A separate descriptive audit of the saved candidate, without reselecting or modifying it, found:

| Retained predicted lesion region | Predicted voxels | Reference overlap | False-positive voxels | Interpretation against this annotation |
|---|---:|---:|---:|---|
| Region1 | 2,067 | 1,479 | 588 | Overlaps the one annotated lesion, but overextends and misses134 reference voxels |
| Region2 | 1,385 | 0 | 1,385 | Entirely false positive relative to this annotation |

Both survive because they belong to the same connected **pancreas union**, even though they
are separate lesion-label components. Region1 alone is3.730 mL versus2.911 mL, a28.15%
overestimate. Thus even retrospectively dropping Region2 would not yield an accurate outline.
No such second candidate was created or evaluated. The residual audit is diagnosis only and
cannot change the failed CP01 decision.

## Reproducibility and verification

Private artifacts are under `outputs/prowl/component-selection-cp01-20261020/`:

- `input-pins.json`: package/model/annotation identities and producing source/plan hashes.
- `candidate.nii.gz`: distinct derived labels; native geometry and decoded labels round-trip exactly.
- `comparison.json`: exact confusion counts, all three targets, each removed component,
  reference-lesion component recall, coverage and explicit rule results.
- `residual-lesion-diagnosis.json`: bound to the original comparison/candidate/reference hashes;
  records the later descriptive helper's separate source identity. No CP01 rerun.

| Artifact | SHA-256 |
|---|---|
| Original prediction | `75fcf8e07d9a8c2650ce842004ad160e4879912debfcd8df944c778416e2ca49` |
| Candidate prediction | `90c936bc4fc627284ad0005854c59bcfa822d098ce5dc55a015b675ed0ba0d56` |
| Local lesion annotation,68,437bytes | `f7bd672ee6c0528bdfa8f7c9597c43c076f541d1725ed5d5a47c13e234f71ead` |
| Comparison JSON | `8de41be100925be8a190047c81fad3bc8e1ac0772547ed7c53de3863e373839b` |

The new lesion hash was recorded before decode and rechecked afterward; its Windows copy's hash
was not independently matched. Original prediction and pancreas hashes also rechecked unchanged.
No CT array was decoded. Files stay private; only code and this summary are committed.

**27 distinct Python checks pass**:16 selector/comparison/diagnostic checks plus11 boundary and
package checks. Tests include a true disconnected lesion that is lost despite better aggregate
Dice, corner connectivity, ambiguity refusal, empty references, anisotropic/sheared volume,
label immutability, package geometry failure and distinct non-overwriting candidate export.
The first actual comparison completed successfully as an evaluation and returned `screen_pass=false`;
that is a failed candidate, not a program crash. No UI changes or broader test reruns were needed.

## Next checkpoint and live state

AI-05 remains In Progress. Keep CP01 as a documented exploratory result, not a deployed filter.
The existing `/saved` and on-demand viewers still use the original mask and retain their
measurement refusal. No service was restarted or configuration changed in this comparison.

Next, freeze a broader **lesion precision and measurement error** evaluation using deterministic
exposed development membership, including positive and reference-empty cases, with raw-versus-candidate
component recall, false positives and per-lesion volume/spatial errors. First verify source identities
and checkpoint parity. Study inference confidences or another explicitly versioned false-positive
control as a new candidate only after its method and loss limits are fixed. Do not select regions
using their annotation overlap or adopt “keep only the largest lesion” from this one outcome.

A separate broader accuracy packet and human outline review remain required before reliable
pancreas/individual-lesion sizes or normal-reference interpretation. This result identifies the
remaining failure; it does not complete REQ-X01 or prove that filtering generalizes.
