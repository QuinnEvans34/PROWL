# Bounded alignment review: cases 3, 26, 31

September 28, 2026. Execution scope under Quinton's request to complete the remaining evidence.
Read exactly the CT and pancreas mask for each of these three original train-role cases, using
paths/hashes/stat identities in the pinned content job JSON (SHA-256 d1707a08c36a29980302294cba66b878ec3a819004605e2422def872a2acc1f8).
No lesion/test/validation inputs, original edits, new sampling or training.

Budget: one process, 300 seconds overall, 64 MiB compressed source bytes, 256 MiB expanded bytes
per file, 20 million voxels per image, 2 GiB peak RSS check, 64 MiB total evidence, 100 GiB internal
free floor. Source files are read once through no-follow descriptors, stat-checked and hash-checked
before decoding from memory. This diagnostic uses bounded arrays and RSS checks, not a new workflow
supervisor. A fixed wall alarm bounds the run. No automatic retry or scope expansion.

Use full NIfTI scaling and D-259 binary decoding; verify same-study shape/affine agreement before
applying the same canonical RAS orientation to CT and mask. Preserve numerical geometry; no spatial
resampling. Display physical aspect ratio with nearest-neighbor scaling. Retain an overview with
paired plain/overlay views in three axes and contact sheets of every mask-bearing axial plane.
Record original/canonical geometry, exact displayed indices, source/code/spec hashes and normalized
value counts. Limit mask-bearing slices to 96 per case; exceeding a cap fails rather than sampling
away an uninspected region. New exclusive evidence directory under ignored outputs/prowl.

Visual findings are engineering checks for gross displacement, coverage, orientation and target/input
correspondence. They are not a diagnosis, expert contour certification or proof of every boundary.
Uncertain correspondence stays held. Partial files have no successful completion receipt.
