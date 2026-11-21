# Questions that would close the remaining provenance gaps

Draft only. No message has been sent and no scan has been uploaded.

## STU-Net release maintainers

We are auditing the original Google Drive `base_ep4k.model` (file ID `1BHCp1Ort-OaVFwaZmvsG4qHiKiPeNb4h`, SHA256 `7232a6296d320da1d60debe873a1d3fcad74e9404272db8f7440e30d62c5997a`). Could you confirm:

1. That this is the original TotalSegmentator-only model, without downstream fine-tuning, and provide an authoritative checksum if available?
2. The exact original dataset release and pseudonymous case IDs used for gradient training, validation/model selection and any other checkpoint-selection decisions? The paper's 1,081/57/65 counts sum to 1,203; which reference cases were included or excluded for the released 4,000-epoch model?
3. Whether other initialization or training sources were inherited, and whether repeated studies from the same source patient were kept within one partition?
4. The complete original preprocessing/spacing/intensity plan, trainer version and checkpoint-specific usage/redistribution license? The small released plan does not encode a complete geometry/intensity recipe.

## PanTS maintainers

Our permitted portable development registry contains 75 PanTS pseudonyms drawn from the publisher training partition. The released metadata lists University Hospital Basel for cases `PanTS_00001389`, `PanTS_00001823`, `PanTS_00002935`, `PanTS_00006011`, `PanTS_00006115`.

Could you provide an authorized pseudonymous crosswalk to the original dataset/release/study identifiers, including any TotalSegmentator reuse, and identify whether different PanTS pseudonyms can represent repeat acquisitions or phases of one patient? We do not need names, dates of birth or other direct identifiers. A privacy-preserving adjudication of candidate pairs would also help.

For eventual external evaluation, can you confirm separation from the specific TotalSegmentator/STU-Net checkpoint's training and selection patients, the permitted submission process and whether results should remain a one-time locked assessment? We would supply only an explicitly authorized inference package, not upload local scans for this audit.

An image duplicate lookup cannot substitute for this patient-level information. A response that cases have different dataset names or pseudonyms would not close that gap.

## Original TotalSegmentator v1 integrity question

The original v1 ZIP exactly matches publisher MD5 `f0fbb3f91d9d99f2169863545f577b30` (local SHA256 `efbc7119d7da5ca3b0ef56687d19136b03842c3f027a104258f0eac77d902409`). Python and an independent ZIP utility both report a CRC failure for `Totalsegmentator_dataset/s0864/ct.nii.gz`: expected `08acde52`, observed `cca32844`. Could the publisher supply a valid original-v1 member plus its checksum or explain the mismatch? We have not repaired it, accepted failed bytes or substituted v2.

For STU-Net maintainers: was this case excluded, repaired from an original source, or used by the released pretraining run? The metadata's 1,082 train rows minus this one member would fit the paper's 1,081 count, but we do not treat that arithmetic as confirmation.
