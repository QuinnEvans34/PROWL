# Expanded candidate header job — preparation only

D-290: exact JSON job in this directory selects only the148 new candidates from D-289:
112 training and36 development-validation,296 CT/pancreas files. All28 old candidates remain in
selection; retained6350 is still held, not retried or replaced here. No headers have been read by this job.

JSON SHA-256 must be pinned by the executable request after its runner is tested. Reuse the bounded
NIfTI-1 gzip header reader from `localizer_candidate_headers.py` (348 decoded bytes, at most65536
compressed bytes/file). Total cap20MiB,15minutes,512MiB RSS,8MiB evidence,100GiB internal free floor.
Only header metadata is decoded, never voxel arrays. The compressed reader necessarily touches a
bounded gzip prefix, which may include compressed array bytes; it does not decompress those arrays.

Before opening files, validate the selection receipt, JSON job, exact unique296 input tuples, roles,
registry hash and registered volume UUID/mount. Each file must match retained inventory size/device/
inode/mtime/ctime, with safe relative paths and no symlink traversal. Recheck identity after reads.
Record source shape, datatype, physical units, qform/sform, affine, voxel count, expanded-byte estimate,
CT/target grid agreement and every issue. Header size/data-type estimates are not measured processing
RSS. Unknown units or unusual geometry become visible concerns, never silent exclusions.

Implement as a new versioned job consumer; do not modify the old28-case job's constants or receipts.
Test substituted selection/role/path/identity, duplicated files, truncation, unsupported formats and
read/resource limits before freezing its request. Preserve per-case failures. Stop on identity or
budget violations; any retry needs a new request and retains prior evidence.

The output sizes later qualification batches. It grants no target permission, no new executable
cohort and no training. Full content/geometry/decoding qualification and review remain required for
every consumed input, with resource budgets based on these header observations.
