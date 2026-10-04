# Three-case localizer: source/use and engineering alignment assessment

September 28, 2026. Reviewer: Codex. Scope: PanTS cases 3, 26 and 31, their original CTs and
pancreas masks, for a private noncommercial two-case learning smoke. This review supplies evidence
for the forthcoming qualification records; it does not itself promote annotations or launch training.

## Source identity and integrity: accept the declared staged assurance

The pinned acquisition controls identify the first CT archive by publisher SHA-256
`c6a1e4e67617940a3e86da4362fc8c753d7bbc2e592181e347060dc3689af078`.
The retained extraction receipt records this same hash, 1,000 files and 34,180,879,311 expanded bytes.
The label extraction records local archive SHA-256
`2de0c363c73c8106b0456d49f3e5057641fefb5383a03f6cf13b4f300a672c83`.
That label digest is locally measured, not publisher-authenticated.

The receipt file `outputs/prowl/extraction-2026-09-22/pants.jsonl` is already pinned in
SOURCE-VERIFICATION-SCOPE JSON. Current 18,000-file metadata accounting matches the retained CT shard
sizes. The ten-file continuity job and this six-file render job independently checked the candidate
hashes against the earlier audit. Original 7,200/1,800/901 roles remain unchanged.

**Operational assessment:** this chain supports a source-readiness assessment for these exact local
smoke inputs under D-268's staged model: pinned release/acquisition, recorded extraction, complete
identity accounting, current consumed-file hashes and complete consumed-array checks. Keep source
integrity coverage **partial**. Do not assert independent archive-member equality for these six files,
fresh whole-archive verification, biological uniqueness, or qualification of all 9,901 studies.
Existing archive samples and scanner receipts remain separate evidence with their original coverage.
A new whole-source scan is not introduced as a prerequisite merely to make those stronger claims.
The v3 publisher must retain this explicit assurance scope and check all input pins before relying on it.

This accepts a bounded engineering assurance level; it does not weaken any recorded mismatch or
permit an unresolved known duplicate. The current candidate CT hashes are distinct. Wider exact-byte
and biological-identity duplicate coverage remains limited and must be stated in the source profile.

## Release applicability and pancreas provenance

The [pinned PanTSMini card](https://huggingface.co/datasets/BodyMaps/PanTSMini/blob/3b1cd61108116b58ea5c1ddb3512c1847d965f96/README.md)
links the released training/test collection to the PanTS paper and label archive. The
[pinned official downloader](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/download_PanTS_label.sh)
uses the same JHU label endpoint and identifies IDs 1–9000 as training-source labels.

The [paper's annotation protocol](https://arxiv.org/html/2507.01291v1#S3.SS3) describes model-initialized
non-tumor anatomy followed by human checking/correction. Applying that publisher protocol to this
linked release supports pancreas `method=human_validated`, `validation_status=source_asserted`,
`scope=publisher_protocol`, with release applicability confirmed at source level. It does not establish
who annotated each file or independently verify every boundary. Retain the original observed masks;
this review is not evidence that every file is flawless or manually drawn from scratch.

## Narrow local-use determination

The [pinned GitHub license](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/LICENSE)
states BY-NC-ND 4.0, while the card states BY-NC-SA 4.0. Both raw documents were re-fetched and matched
the earlier independently recorded hashes:

| Document | Bytes | SHA-256 |
|---|---:|---|
| Pinned HF card | 3,378 | 9ef102440ac6c6a0b4c63237f332380a6571c18cd19f1f60e7257d7e4e23e68f |
| Pinned GitHub license | 15,379 | 3581c0055b9652dd9e7a8e55755879fde7ab2ea511878ae268fd6fae3546ff81 |

The [NC-ND legal code, 2(a)(1)](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en)
permits private noncommercial production/reproduction of adapted material, withholding sharing of
adapted material. The [NC-SA legal code, 2(a)(1)](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
also permits noncommercial adaptation. Their differing distribution conditions remain unresolved.

**Operational determination within Quinton's authorized local academic project:** these three pancreas
masks may be considered for `training_target` use for the private pancreas-present smoke, subject to
all other qualification/cohort/run requirements. Preserve attribution, source notices, original files
and evidence. Do not allow commercial use, public data/overlay/derived-mask distribution, or model
release from this determination. It relies on publisher representations and does not certify underlying
contributors' rights or resolve how trained weights should be licensed. The publisher clarification
track remains open for release. No publisher was contacted or new terms accepted on Quinton's behalf.
This is an assessment for a narrow use, not a blanket legal clearance or a new owner policy decision.

## Alignment execution and observed result

The [preregistered job](LOCALIZER-ALIGNMENT-JOB-2026-09-28.md) read **six files, 33,056,488 compressed
bytes**, and completed in **8.60 seconds**. It verified bytes before decoding in memory, applied
NIfTI scaling and D-259, and retained original/canonical geometry and exact view indices. There was
no spatial resampling; display uses nearest-neighbor scaling with physical aspect ratio.

Package: `outputs/prowl/localizer-alignment-8ae22f7e-f845-4865-aa8f-8219662f46c4/`.
Eleven files, 4,102,222 bytes; ten covered file hashes independently verified.
Verification receipt SHA-256:
`bc66dafbfc7e72ec4a259bc42416c6bcb16bfc83008153687e7cc3f07efca04f`.
Six PNGs were inspected: overview plus every mask-bearing axial plane for each case. Overview sheets
include plain/overlay pairs at three axial levels and central coronal/sagittal mask views.

| Case | Mask-bearing canonical axial indices | Engineering assessment |
|---|---|---|
| 3 | 12–23 inclusive | Upper-abdominal coverage and mask/CT correspondence are plausible; no obvious gross shift or axis reversal in reviewed views. Coarse through-plane appearance is consistent with recorded 7.5 mm spacing; retained as variation |
| 26 | 50–64 inclusive | Foreground progresses coherently across the shown axial levels; paired views and orthogonal views show no obvious gross displacement or coverage mismatch |
| 31 | 8–29 inclusive | Foreground progresses coherently across axial levels; no obvious gross displacement or missing relevant coverage in displayed views |

**Result:** supports the limited engineering alignment/coverage check for localizer smoke inputs.
No claim that every source slice was visually reviewed, every pancreas boundary is correct, or that
this is an expert clinical contour acceptance. Fine-boundary uncertainty remains source-asserted.
The mask-bearing planes are exhaustive for the positive labels, not proof that the mask includes all
anatomy visible elsewhere. No diagnosis or lesion assessment was made.

## Implementation and handoff

New diagnostic: `scripts/diagnostics/localizer_alignment_review.py`; four tests cover physical display
aspect, localized overlay/array preservation, layout and changed-byte rejection. **941 native tests
passed**, two existing upstream warnings. Existing hash/decoder tests remain part of that suite.
The first web reads of the HF card/GitHub license failed; bounded native retrieval then verified the
exact known hashes. No corpus acquisition or Claude planning edits occurred.

Next: turn this pinned source/use/alignment assessment, D-259 evidence and protected identity controls
into the real v3 accounting context and five qualification checks. Apply the narrow transition checker
while preserving all old holds in history and all unrelated active holds. Then publish/resolve the
frozen two-case cohort. Keep case 78 excluded for this purpose and case 266 unit-held. No training
starts until the separate preprocessing, recovery and run-readiness requirements pass.
