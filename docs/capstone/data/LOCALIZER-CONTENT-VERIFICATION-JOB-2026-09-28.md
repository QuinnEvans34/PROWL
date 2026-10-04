# Next localizer job: exact content verification and qualification handoff

September 28, 2026. Codex specification under the requested four-step data sequence.
**Status: specified, not executed.** The [machine-readable job](LOCALIZER-CONTENT-VERIFICATION-JOB-2026-09-28.json)
pins the inputs, ten paths, expected hashes and resource limits. No source payload was read to prepare it.
This advances Step 2; it does not claim Step 3 qualification or Step 4 publication.

## Concrete next operation

Reverify the five CT/pancreas pairs already audited: PanTS cases **3, 26, 31, 78 and 266**.
Keep the entire previous pool, including the empty-target and unknown-unit cases. This is deliberate
reuse of an investigation sample, not a representative sample of PanTS. Its original selection used
source tumor flags and size flags; report that bias. No model outcome or visual ease selects this job.

The live metadata inventory gives **44,195,710 compressed bytes across ten files**. The retained
five-case receipt supplies their expected SHA-256 values; all 13 receipt-covered evidence files were
rechecked while preparing this specification. Source bytes have not been rechecked in this pass.
The previous voxel observations are reusable only when the new current hashes agree and their
measurement code/evidence remain appropriate for the claimed check.

Use the existing registered acquisition parent and receipt-derived extracted root, not a newly
activated scientific alias. Preserve every source and old evidence package. Read only these ten
compressed files; no decompression, other organ masks, validation/test payloads or archive scans.

## Execution budget and tested-runner requirements

| Constraint | Exact rule |
|---|---|
| Unique bytes | Exactly the ten pinned file sizes; total 44,195,710 bytes |
| Read cap | 64 MiB total source bytes, including any attempted reread; one attempt per file |
| Time | 300 seconds overall, 60 seconds per file; deadline covers setup and finalization |
| Memory | 1 MiB streaming chunks; 512 MiB process RSS ceiling with supervisor enforcement |
| Evidence | New exclusive `outputs/prowl/localizer-content-<UUID>/`, maximum 8 MiB; 100 GiB internal free floor |
| Parallelism | One reader, no training/download job started by this operation |
| Identity | Registered APFS volume UUID and device checked before reads and at least every 2 seconds; reject symlink components, nonregular files and changed roots |
| Mutation | Compare current stat identity to pinned inventory, open safely, compare descriptor/path identity before and after; changed bytes or identity stops the job |
| Completion | Persist request/spec/code pins before reads; per-file measured hash, byte count, time and status; complete receipt only after all ten pass |
| Interruption | Keep partial evidence without a success marker; new attempt gets a new package; no automatic restart, deletion, overwrite or substitution |

The cap has over 25% byte contingency, but contingency is not permission to add files. Measure total
elapsed time and per-file effective read rate; record caching as unknown. This small repeat-read sample
cannot establish cold-cache throughput for all 319 GB of current CT/pancreas files. It is enough to
budget the next similarly bounded candidate job; any bulk job needs its own measured scope.

Implementation belongs in a new narrow diagnostic runner and synthetic tests, reusing reviewed path,
mount and package helpers. Test changed/missing hashes, wrong role, altered spec, path escapes/symlinks,
mutation during read, timeout, read/output/RSS limits and absence of a completion marker on failure.
Do not change Plan 04 or the existing live inventory scope. Run the focused tests and native suite
before executing. This specification is not evidence that these protections are implemented yet.

## Assurance scope: what is required and what remains unproved

The approved Plan 02 G1 checklist requires protected identities, source/status evidence, quarantine,
frozen ancestry and a resolving consumer. It does not explicitly require rereading every acquired
voxel before a first subset; it explicitly defers expensive image fingerprints to Plan 03. D-268
allows staged qualification. No G1 amendment or waiver is introduced here.

| Coverage | Required evidence and remaining work |
|---|---|
| All 9,901 identities | Reuse pinned original controls, complete identity/role accounting and explicit study-as-subject fallback; production protected roots still need publication |
| Declared acquired CT/pancreas scope | Reuse pinned acquisition/extraction receipts and the 18,000-row live inventory; enumerate exact receipt integrity methods and gaps in the new source snapshot |
| Current selected bytes | This ten-file job establishes continuity with retained measured hashes, not an independent publisher per-file attestation |
| Source archive identity | Retain publisher-hash evidence where supplied; the label archive has a local digest and release-endpoint linkage, not a publisher SHA-256. Do not relabel either assurance |
| Archive-to-extracted equivalence | Report precisely which retained archive comparisons cover these paths. A retained local file hash alone is not an archive-member comparison. Missing mandatory evidence blocks the affected source-readiness assertion |
| Duplicate protection | Compare all available measured CT hashes across recorded roles and known findings. Report coverage; no proof of biological uniqueness or whole-source absence of duplicates |
| Annotation quality | Per-case target/geometry/coverage evidence and source provenance, independent of byte integrity |

The source snapshot must say accounting complete but integrity coverage partial where appropriate.
Unknown fields remain explicit. Rechecking this pool cannot make uninspected members payload-ready.

## Step 3: turn evidence into supported purpose decisions

The five required qualification checks remain `source_readiness`, `geometry`, `mapping_lineage`,
`target`, and `permitted_use`. Their receipts must bind the actual new source/subject/study/annotation/
issue records and independently reviewed evidence; filling in five `pass` strings is not qualification.

1. Review exact source/release/provenance applicability and the allowed-use evidence for **local
   noncommercial pancreas-localizer training**. The existing source-use review separates this from
   public release; it does not itself remove the recorded holds. Keep redistribution/model-release
   questions separate. No new legal clearance is claimed here.
2. Bind D-259 to the complete retained scaled-value counts. Require finite values within absolute
   1e-6 of 0/1, rtol zero; no truncation or generic positivity. Preserve original mask bytes.
3. Reuse verified header/voxel reports only for identical bytes. Physical units and valid transforms
   remain mandatory. Unknown-unit mask inference may use the existing `paired-explicit-mm-ct-v1`
   rule with clean explicitly-mm same-study CT; do not extend it to an unknown-unit CT. The current
   implementation specifies native grid atol 1e-5/rtol zero and coded-mask transform atol 1e-4/rtol
   zero. Bind its code hash and tests instead of creating a conflicting tolerance policy.
4. Record coverage/alignment inspection for each proposed consumed pair. Nonempty foreground alone
   does not establish anatomical correspondence; an overlay is engineering evidence, not expert
   certification of a perfect contour. Noise, anatomy and target size remain descriptors.
5. Publish new records only through an explicit append-only supersession path that enumerates each
   old hold, exact new evidence and affected purpose. The current pure qualification checker rejects
   unresolved issues and does not implement this path. Specify/test it before issuing positive records;
   never omit old issues to force a pass.

Expected dispositions remain provisional: cases 3/26/31 have promising retained geometry and nonempty
pancreas evidence, but **none is qualified yet**. Case 78 remains excluded for this pancreas-present
purpose; case 266 stays geometry-held. Case 2 remains held outside this job. Original membership stays.

## Step 4 and the actual training dependency

For the first two-case learning fixture, propose ascending study ID among positively qualified members
of this fixed five-case pool, exact count **2**. If fewer than two qualify, report shortage; do not
silently search for easier replacements. Expansion uses a new recorded pool and frozen cohort. This
small fixture tests learning/execution, not generalization or normal-versus-unusual robustness.

After reviewed positive records, publish the protected parents and executable child, verify the
completion inventory and deterministic rebuild, and make the consumer reject held/wrong-role/changed
inputs before array loading. Only then connect the separately planned preprocessing, synthetic training,
checkpoint/recovery and run-budget checks. No training starts from this document.

## Execution follow-up

The specified job subsequently [completed successfully](LOCALIZER-CONTENT-VERIFICATION-RESULTS-2026-09-28.md).
The original specification and JSON pins above remain historical run inputs; no eligibility was granted.
