# PanTS local errata correction — October23

**Seven derived masks prepared and checked; original files and frozen runs intact.
This is a local correction based on upstream confirmation, not a new upstream release.**

User authorized addressing the confirmed errata. Policy `pants-issue12-local-normal-mask-1`
retains all seven scans and their pancreas masks, replacing only their erroneous
lesion masks with zero-valued masks. It rejects unlisted cases, non-training roles,
changed source hashes, nonbinary input and unexpected voxel counts. No general
small-component removal rule was introduced.

Source: [PanTS maintainer/radiologist confirmation](https://github.com/MrGiovanni/PanTS/issues/12#issuecomment-4538401573).
See MAC-KD-UPSTREAM-ERRATA-20261023.md for the affected case list and source review.

## Materialized evidence

External artifact root:
`/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/annotation-errata-02/`.

- `overlay.json`: original/corrected hashes and paths, provenance, case counts and
  per-case sampling changes. SHA256 `033f8f5cb7533031412a04f8daff62e5f95786123d0a21fc3c32c711ef5b06bc`.
- `masks/<case>/pancreatic_lesion.nii.gz`: seven zero-valued derived masks.
- `masks/<case>/sampling.json`: regenerated pancreas-focused components and coverage
  banks using unchanged source pancreas masks, regions and physical geometry.
- `pilot-reassessment.json`: separate corrected-label view of existing predictions.
- `request.json`, `resources.json`: producing-code pins and bounded execution.

All14 original pancreas/lesion files matched the frozen metadata hashes before
and after processing. Each derived mask was reopened: all zero, identical shape,
affine, qform/sform matrices and codes. No CT voxels or models were read.

The corrected source is assembled from the original pancreas plus an empty lesion
mask. Do not blindly map combined class2 to background, because a spurious lesion
may previously have overwritten a legitimate pancreas voxel.

## Cohort and sampling reconciliation

| Item | Original | Corrected |
| --- | ---: | ---: |
| Training cases | 1333 | 1333 |
| Positive training cases | 671 | 664 |
| Negative training cases | 662 | 669 |
| Development cases | 70 | 70 |
| Positive development cases | 36 | 36 |

Membership and patient order stay unchanged. The24k permutation was replayed for
visit counts only; no optimizer ran. All seven coverage-bank sizes stay unchanged
(one or two windows). Component-focused sampling changes from lesion to pancreas
components; every planned focused-visit index was checked for valid coverage slots
and pancreas anchors. This checks label-derived sampling metadata, not actual
augmented image batches or full cold-restore equivalence.

## Matched designs and integration boundary

New `configs/experiments/mac-kd-errata-comparison-20261023/control.json` and
`treatment.json` bind the same overlay hash and differ only in KD weight. Original
comparison files remain unchanged. Both new designs explicitly reject old target
cache admission and keep scientific launch disabled.

These are prepared data/design artifacts, **not a change to a running loader**.
Before a future run, explicitly bind the overlay in its input manifest, regenerate
seven affected targets and the cache manifest, then qualify actual batches and
cold restore under the new receipt. Unaffected cache reuse must be hash-verified
under that manifest. Do not resume a frozen old run with these labels, silently
repin old receipts, or use corrected labels in just one comparison arm.

Teacher quality acceptance is still outstanding, so no scientific launch is ready.

## Pilot reassessment without new inference

All12 cases remain; case3059 becomes annotation-negative. Original report retained.

| Report | Positive cases | Positive macro Dice | Positive macro recall |
| --- | ---: | ---: | ---: |
| Original labels | 11 | 0.374683 | 0.471450 |
| Corrected labels | 10 | 0.412151 | 0.518595 |

The numbers changed because the label interpretation changed, not because the
model improved. Negative cases691 and3059 have8112 and10 predicted lesion voxels,
respectively. No population specificity claim from two cases. Large-lesion failure
remains; teacher still not accepted. Do not substitute this rescore for independent
evaluation or rewrite the original experiment history.

## Verification and preserved failure

Nine focused policy tests pass, including scope/hash/count failures and original
array preservation. Real preparation completed10.70seconds,1,881,980,928B peak
owned RSS,exit0/workers reaped under600second/12GiB bounds. First attempt stopped
before any masks were processed because it expected development members in a
training-only archive directory. Its source snapshot/log/resources remain in
`annotation-errata-01/`; version02 reads development counts from the verified
source manifest. No source dataset edits, exclusions, model runs, training,
checkpoint changes or Windows messages occurred.
