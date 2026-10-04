# D-297 — uniform2mm candidate qualification

Quinton: “Great find, continue on.” Scope: separately versioned candidate preprocessing for the exact
D-294113 train/40 development-validation members. Current3mm recipe and previous runtime remain
unchanged; no training,model forward,source modification,target inflation or cohort filtering.

V4 uses uniform2mm spacing,16M output ceiling,96M source ceiling and the existing16-slice restoration.
All other image/target operations match V3:RAS,HU[-100,300],bilinear image,nearest target,minimum96
padding,no target crop. Exact candidate JSON and source/environment snapshots are frozen per request.
A synthetic96M source with1.08mm spacing must produce at least15M output voxels and pass image-only
parity,nonempty binary target/source restoration under16GiB RSS/20minutes before any source reads.
Native tests must pass, including old8M refusal, versioned budget boundaries and slab/full parity.

New capability/request namespace and permanent single-use claims. Four-case pilot:6110/2727 tiny
boundary targets,5190 noisy/sparse target,7957 largest projected output. Review numerical evidence and
all pilot sheets before enabling continuation. Remaining membership is partitioned into nine16-case
standard batches plus five singleton large-source cases. The partition preserves exact153 identities
once each,113/40 roles and all prior limitations. No automatic refill or retry.

Every real request independently resolves/checks the pinned D-294 bundle, qualified source hashes,
roles/purposes,live binary policy and storage identity. Exactly306 CT/pancreas files overall:
5,152,089,856compressed /13,196,550,237expanded bytes. Per-file128MiB compressed/512MiB expanded;
per-job20minutes,16GiB RSS,256MiB output,100GiB internal-free floor. Whole qualification90minutes and
2GiB retained job outputs. Each batch enforces exact file/byte coverage, scoped URIs and no repeats.
Stop on supervisor breach or disappearing target,retain all evidence,do not delete consumed claims.

Verify actual CT image-only parity and restored source grids,record source/processed/restored target
counts,Dice,recall,size ratio and processed tensor payload. Compare every case against retained D-295;
report both improved and worse outcomes,including worst cases and partial/noisy references. Review
all153 limited three-plane sheets before declaring visual review complete. These are reference
resampling metrics,not model performance,whole-organ truth or expert contour certification.

Finer spacing may cost more memory and need not improve every individual overlap metric. Current
candidate qualification does not adopt it as a training recipe. At completion,record an explicit
recommendation based on full-cohort fidelity/resources,then proceed to role-safe cache/no-update MPS
profiling and independent checkpoint recovery under separately prepared requests. No training launch
request is authorized or prepared here;native evaluation truth and all23 prior holds remain unchanged.
