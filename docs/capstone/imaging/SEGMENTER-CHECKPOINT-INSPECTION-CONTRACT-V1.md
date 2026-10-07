# Invented checkpoint metadata inspection v1

SUP-02A only. Quinton approved the next bounded coding packet on October 6 after the board cleanup.
The reader accepts caller-attested invented fixtures in private temporary directories only. It
has no actual-file switch. It returns JSON metadata, never tensors or an initialized state.
Identity pins establish consistency, not scientific provenance or training permission.

## Closed control schema

`inspect_checkpoint(path, *, pinned_control, expected_control_sha256) -> dict`.
`control_sha256(control)` hashes UTF-8 sorted compact JSON plus a trailing newline, with finite
numbers, bounded depth/items and at most 1 MiB. All object fields below are required; extras refuse.

- `schema_version`: `segmenter-checkpoint-inspection-control-1`.
- `evidence_domain`: `invented_serialized_checkpoint`.
- `source`: exactly `root`, `path`, `bytes`, `sha256`. Root is an absolute canonical private
  temporary directory named `prowl-invented-checkpoint-*`, below the canonical system temporary
  root, owned by this user with mode 0700. Path is its single immediate regular-file child named
  `invented-*.pth`; it must equal the API path. Byte count and SHA bind that exact file.
  Symlinks, traversal, hardlinks, other roots and the recorded actual candidate hash are refused.
  The temporary-path restriction is an accidental-access guard; it cannot independently prove
  that a dishonest caller created invented bytes. The approved tests create every payload anew.
- `architecture`: one input,32 outputs,init_filters16,GroupNorm8,down[1,2,2,4],up[1,1,1],dropout0.
- `expected_signature`: every key maps to exactly `shape` and `dtype`; must match the complete
  fixed 83-key,float32 SegResNet signature (18,805,696 logical bytes), independently checked
  against a fresh factory-created model in the tests. Reader does not construct a model.
- `namespace`: `identity` or `uniform_module`; exactly one uniform leading `module.` may strip.
- `wrapper`: exactly `net_optimizer_scheduler_epoch`; outer keys are net,optimizer,scheduler,epoch.
- `limits`: every key returned by `limits()`, with positive bounds at most the hard maximum.
  Model/auxiliary and archive bounds are checked independently; limits cannot grant a new domain.
  `max_report_bytes` has a2048-byte minimum for bounded refusals; worker time has a50ms minimum.

## Closed report schema and interpretation

Every report contains `schema_version`, `status` (`pass` or `refused`), `reason`, `evidence_domain`,
`scope`, `execution_authority`, `training_eligible`, `identity_verified`, `metadata_compatible`,
`values_audited`, `control_sha256`, `source_sha256`, `source_bytes`, `archive`, `model`, `auxiliary`,
`io`, `worker`. Authority is always none; training eligibility and values_audited are always false.
Compatibility becomes true only after the complete container/signature/storage/view checks pass.
No rights or overlap acceptance is manufactured by this invented report.

Archive rows contain name,local-header offset,payload offset and declared bytes. Model rows contain
normalized key,shape,dtype,stride,storage offset in elements,logical bytes,storage bytes,source
device,storage-file offset and storage member. Storage aliases are reported by member and tensor
paths; no content hash or tensor value is emitted. Auxiliary fields are inventoried with bounded
primitive values and fake tensor metadata only; optimizer/scheduler state is never restored.
The model OrderedDict's optional `_metadata` version map is also inventoried, including its empty
root-module key. Unknown dictionary attributes refuse; no attached serialized data is silently
ignored. Empty primitive strings/keys are supported. Tuples remain outside this contract.
`io` reports hash bytes,metadata source bytes,virtual zero bytes,aggregate requested bytes and
metadata storage source bytes (must be zero). `worker` reports method,wall duration,sampling interval,
sampled peak RSS,child-reported peak RSS and termination reason. Resource observations can differ
between repetitions; semantic inventory and I/O evidence must be deterministic.

## Metadata-only view — recorded before implementation

The initial direct-file FakeTensorMode probe with installed PyTorch2.13.0 refused correctly:
18,138-byte invented archive, storage[832,17216), decoder requested[14042,18138). A 4KiB footer
buffer overlaps storage even though fake tensors do not allocate its contents. Probe:0.513774s,
273,219,584B process peak RSS. No actual artifact was touched and no unsafe fallback ran.

Revised approach within A: independently bound/parse EOCD,ZIP64 footer,central entries and local
headers first. Do not read storage payloads during this parsing. For PyTorch decoding, a seekable
descriptor-bound virtual view supplies zero placeholders wherever a requested buffer overlaps
declared storage. It reads only the remaining metadata intervals from the pinned descriptor.
All requested bytes, including repeated reads and virtual zeros, count against the aggregate cap.
The prior full-file SHA pass necessarily reads file bytes including storage, solely for identity;
the zero-storage-read guarantee applies to subsequent metadata parsing/decoding, not that hash pass.
No virtual view is written to disk and no weight content is returned or mmaped. Offset/layout
metadata remains byte-identical; placeholders are explicitly reported, not passed off as source.
FakeTensorMode plus weights_only=True,map_location=cpu,mmap=False remains mandatory. If this view
cannot qualify, refuse and stop; do not silently relax the boundary or proceed to actual inspection.

## Bounds, worker and refusal rules

Hard maxima:64MiB file; file-length hash plus8MiB metadata/virtual reads;1MiB central directory,
data.pkl,control and report;4096 members/distinct storages;128MiB declared storage;1024 model
tensors;64MiB logical model bytes;512 UTF-8 bytes/key/path;16 nesting levels;32768 visited items.
Worker maximum60s,3GiB sampled RSS,50ms polling. Whole qualification:5min/3GiB,CPU only.
Child is an isolated Python process with a minimal environment; clear ambient PyTorch safe globals
there, add none, and verify the set stays empty. No process-wide globals/RNG mutation in the caller.
Mac/Linux RSS monitoring uses the installed ps command; unavailable monitoring refuses before
source inspection. Wall/RSS/output stops terminate and reap the child, with no automatic retry.
Sampling is an operational stop, not an OS hard memory limit; retain interval and measured peaks.

Support only stored,unencrypted single-volume ZIP entries and bounded ZIP64 footer metadata;
reject legacy formats,unknown members,comments,duplicate/unsafe paths,compressed/encrypted members,
overlap/out-of-file offsets,local/central disagreements and storage excess before PyTorch decoding.
No extraction, unrestricted pickle, user safe-global additions, tensor subclass, sparse/quantized
layout, accelerator storage, model execution or historical loader. Model dtype isfloat32; auxiliary
supported dense CPU dtypes are explicitly inventoried. Validate logical/view byte bounds and
source-storage identity; reject unsupported views rather than materialize them.

Tests use temporary invented containers and independent zipfile offsets plus a factory inventory.
Exercise restrictive controls,descriptor mutation,archive/count/read/output caps,unsafe payload
side effects,namespace/signature/view/layout errors and child wall/RSS termination. Keep failed
approaches in the results. Existing tests/producers/locks and retrieval ownership stay untouched.

Actual-file SUP-02B needs a separately approved boundary and fresh exact request. This contract
cannot enable it. See [packet](../operations/SUPREM-CHECKPOINT-INSPECTION-PACKET-2026-10-06.md).
