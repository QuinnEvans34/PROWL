# Upstream teacher and PanTS review — October 23

**A confirmed upstream annotation correction affects our frozen training cohort.
No source masks, exclusions, scores or active training were changed.**

## Confirmed correction and local impact

A PanTS collaborator reports radiologist confirmation that nine tiny masks were
accidental drawing-tablet annotations on normal cases. Our pilot case3059 is on
that list. Its miss must no longer be interpreted as evidence of failure on a
verified tiny tumor. Source: [maintainer confirmation, May26](https://github.com/MrGiovanni/PanTS/issues/12#issuecomment-4538401573),
[affected IDs](https://github.com/MrGiovanni/PanTS/issues/12#issuecomment-4357449724).

Metadata-only intersection found seven affected training members, none in our70
local development members. Recorded counts match the upstream report:

| Training case | Recorded lesion voxels |
| --- | ---: |
| PanTS_00003059 | 12 |
| PanTS_00000044 | 16 |
| PanTS_00007933 | 16 |
| PanTS_00005693 | 20 |
| PanTS_00007947 | 32 |
| PanTS_00003548 | 36 |
| PanTS_00001819 | 45 |

The other two IDs are outside the local train/development lists; no protected
cases were opened. Source identity checks were valid but cannot establish
annotation correctness. Upstream errata should have been reviewed before treating
the tiny-mask pilot result as a teacher failure.

This correction does not establish that other small components are artifacts,
nor explain case2720's severe underprediction. Preserve historical results as
measurements against the original supplied labels, with this qualification.
Do not retrospectively remove cases to claim teacher acceptance.

## Other documented issues

[PanTS issue4](https://github.com/MrGiovanni/PanTS/issues/4) reports empty masks
versus tumor metadata, disagreement between pancreas and its subregions,
lesions outside the pancreas mask, and affine differences. A collaborator
acknowledges the report and promises fixes, without adjudicating every example.
Our five audited CT/mask pairs passed geometry checks; that does not resolve the
whole dataset or determine the intended lesion/gland overlap convention.

[Issue5](https://github.com/MrGiovanni/PanTS/issues/5) confirms contrast-phase
metadata errors for examples6/7 and describes a wider radiologist recheck. The
commenter's approximately25% model-predicted disagreement is not a confirmed
25% annotation-error rate. No phase relabeling or contrast inference was run here.

The [official label downloader](https://github.com/MrGiovanni/PanTS/blob/main/download_PanTS_label.sh)
still names a PanTSMini_Label archive. The reviewed pages do not establish that
a corrected archive has been published or that our extraction contains revisions.
Do not replace the frozen archive blindly or download a large dataset as a fix.

## Teacher instructions and documentation ambiguity

The [MedFormerPanTS model card](https://huggingface.co/AbdomenAtlas/MedFormerPanTS)
explicitly describes a PanTS segmentation baseline. Its26-channel list agrees
with our index19 pancreatic-lesion mapping. It is not documented as a guaranteed
high-quality teacher. Its example uses raw weights and predicted-organ masking;
our raw-weight experiment failed to rescue case2720. Organ masking can remove
predictions but cannot recover missed lesion voxels.

The [Merlin demo](https://github.com/MrGiovanni/R-Super/blob/main/rsuper_train/Merlin_demo.md)
labels a download as PanTS-pretrained but links to
[RSuperMaskPretrained](https://huggingface.co/AbdomenAtlas/RSuperMaskPretrained),
whose card instead describes an AbdomenAtlas-beta baseline and a42-label list.
These documentation paths are inconsistent. Do not switch weights or reuse the
26-channel map based only on that link. Our selected artifact matches its own
MedFormerPanTS card; this discrepancy is not proof we loaded the wrong weights.

No source reviewed establishes a verified CUDA/MPS-equivalence result for our
specific executor. Earlier numerical checks retain their limited scope.

## Next action

Before the next scientific run, prepare a versioned errata overlay for the seven
confirmed training cases, with source links, original hashes and explicit policy.
Prefer verified corrected upstream masks; if unavailable, an explicitly reviewed
local correction must be documented as such. Preserve original files and both
historical receipts. Reconcile affected sampling/positive counts and any future
matched-control recipe before launch. Do not modify the frozen Windows run.

Then reassess teacher usefulness on the remaining fixed pilot cases, reporting
original-label and corrected-label results separately. The large-lesion failure
still blocks teacher acceptance. No threshold tuning, automatic exclusions,
new teacher download, inference or training occurred in this research pass.

Evidence: external distillation-mac-20261023/upstream-errata-review-01 contains
GitHub API comment snapshots with stable comment URLs and a hashed metadata-only
intersection. Research date2026-10-23. Trello and the experiment log track the hold.
