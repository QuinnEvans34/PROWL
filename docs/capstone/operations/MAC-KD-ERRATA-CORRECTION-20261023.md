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

## Corrected target cache — subsequent integration step

`annotation-errata-cache-01/` now contains seven compressed region targets plus
metadata and an explicitly partial manifest. Manifest SHA256:
`77811d7b62a188d5644887b3ed52f7082ab95a6f576042ef87baac485e187c63`.
The additive `pants_errata_cache_v1.load_target` reader checks manifest/overlay,
role, case membership, member hashes, geometry shape, binary target values and
pancreas voxel count. It is a derivative reader, not the complete training provider.

All seven targets reopen byte-for-byte equal to their generated arrays. Their
pancreas counts equal the full original masks, lesion counts are zero, and rebuilt
coverage/component metadata exactly matches the preceding overlay preparation.
Changed lesion source hashes are explicit in the new metadata; original identities
are retained separately. No original provider or existing receipt was edited.

18 focused tests pass, covering policy and reader scope, stale identities, modified
members and rejection of a lesion-bearing target even with a refreshed file hash.
Real CPU preparation:9.80seconds,1,506,066,432B peak owned RSS,212,250B target/metadata
payload,322 producing pins verified before/after,exit0 and workers reaped. A separate
fresh process successfully read all seven files (`fresh-reader.json`); this is
artifact recovery, **not training checkpoint cold restore**. Initial command failed
on missing jsonschema before creating an output directory or worker; the subsequent
invocation used the existing isolated dependencies without changing the environment.

The complete 1333-member corrected provider/cache manifest remains unqualified.
Unaffected cache reuse, actual CT batches/augmentation, optimizer cold restore and
teacher acceptance are still required. The partial manifest explicitly declares
`complete:false`; neither comparison arm has been launched.

## Opt-in input provider and real-data replay

`src/data/pants_errata_inputs_v1.py` adds `ErrataInputs`, a separate VariedInputs
subclass. It verifies all seven cache members at initialization, binds their
manifest/overlay plus the original provider identity, and checks original source
provenance before loading corrected cases. Unaffected training cases and validation
use the original implementation. Existing providers and receipts stay unchanged.
This implementation is on-demand, **not the fast-prefetch input policy** in the
proposed experiment configuration; do not silently substitute it at launch.

Bounded evidence: `annotation-errata-inputs-01/`. Cases3059 (corrected) and691
(unchanged), already hash-bound training cases, passed actual CT normalization,
target alignment, reserved coverage/component focus/context sampling, and the
existing augmentation function. All six view hashes, traces and provider identity
matched exactly in a fresh process. Each process decoded two CTs. Neither loaded a
model nor performed an optimizer update. Full1333/70 membership is retained in the
control for schedule accounting, but only these two source rows were locally bound
for this probe; remaining paths retain their remote identities and are **not**
admitted as usable Mac data. No development images were opened.

Producer5.94s/2,217,852,928B peak owned RSS; fresh-process replay5.48s/
2,218,967,040B. Both exit0/reaped.83 tests passed covering existing physical geometry,
varied sampling, augmentation and new correction behavior. This is input replay,
not optimizer/checkpoint cold restore or full-cohort qualification.

Next decision point: teacher quality remains inadequate after correcting known
labels. Do not generate a full teacher cache or start KD merely because this
input check passed. Before launch, either qualify the teacher or explicitly revise
the experiment; then bind the full local cohort, reconcile the intended throughput
policy for both arms, and qualify actual optimizer recovery under a new receipt.
