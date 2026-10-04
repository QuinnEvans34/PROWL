# D-293 — remaining content batches

Quinton explicitly requested the remaining nine standard batches/127 cases, then the five larger
cases separately. Complete batches02–07 and12–14 sequentially, each with an independent pinned
request and receipt; do not repeat consumed pilot01. Preserve all candidates, failures and holds.
No qualification, training, final-test use, source modification or Git publication.

Use the immutable D-291 batch plan and D-292 integrity/geometry/semantic/visual procedure. Standard
budgets remain20min/16GiB/1GiB compressed/4GiB expanded/256MiB output per invocation,64M voxels,
128MiB compressed/512MiB expanded per file,100GiB internal free floor. No parallel source jobs.
Freeze source/environment and controls separately for every job. Stop on resource/integrity failure;
no automatic retries. Review all available alignment sheets and preserve unresolved cases.

Before batches08–11 and15, run an array-only96M-voxel synthetic resource rehearsal through gzip
bounded decoding, float CT/target materialization, binary decoding and foreground-coordinate work.
Record source hash, time and peak RSS; require under20min/16GiB. Each larger case then has its own
96M-voxel diagnostic request with that receipt, all other budgets unchanged. This is not an extension
of the existing model loader/preprocessing64M limit. Stop after each if resources or integrity fail.

After execution, rehash all receipts, account for all148 new plus28 prior candidates, compare CT
content hashes across retained/new evidence, and inspect every generated sheet. Record inferior or
other boundary contact, unusual acquisition and noise as observations. Missing units remain unresolved
unless evidence establishes them; neither typical spacing nor visual appearance establishes mm.
Report actual resources, per-case holds and remaining qualification work. Five-plane visual review is
limited engineering evidence, not all-slice or expert boundary acceptance.
