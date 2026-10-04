# D-292 — first expanded content-evidence pilot

Quinton requested the next step after D-291. Implement/test and run only frozen batch-01 from the
15-batch proposal:16 new training candidates,32 files. This does not activate the other batches or
96M-voxel singleton scope. Do not replace candidates. No model, cohort publication or qualification.

Pin candidate selection, full batch-plan digest and header receipt; the batch must exactly match
its16 selected candidates and headers. Bind source/environment, this plan and the derived exact
selection into a single-use request. Verify registered volume and source identity before reads;
recheck identity, gzip EOF/CRC and hashes. Compare decoded shape/type/units/affine to header evidence.

Use unchanged diagnostic limits:1GiB compressed/4GiB expanded total,128MiB/512MiB per file,
64M voxels,20minutes,16GiB RSS,256MiB evidence,100GiB internal free floor. Process one pair at a time.
Retain partial failure evidence and stop on identity/resource/integrity failures; no automatic retry.

Check finite CT, native CT/target geometry, explicit units, strict binary decoding and nonempty target.
Generate paired raw/overlay views at first/middle/last target axial positions and coronal/sagittal
median target coordinates. Review all16 sheets. These limited planes do not prove every boundary is
correct, clinical acceptability or whole-organ coverage. Preserve noise, partial coverage and unresolved
units; diagnostic evidence never directly grants training permission. Report duplicate CT content
within this batch; cross-batch/retained evidence reconciliation remains required before cohort freeze.

Freeze after synthetic tests for exact batch identity/role, candidate/header substitution, duplicate
members, inactive batches, resource scope and decoded-header mismatch; retain the existing bounded
reader/scaling/malformed-gzip/declared-size tests. Review measured cost before proposing continuation.
