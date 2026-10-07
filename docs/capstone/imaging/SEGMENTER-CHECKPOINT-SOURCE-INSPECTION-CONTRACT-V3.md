# P03-I — versioned recorded-device metadata policy

October6,2026. Quinton said “Great, continue with that” after the diagnostic handback and
P03-I recommendation. This approves the proposed four-file invented reader3 implementation/
qualification only. Preserve all290pins, reader2/dispatcher2 and consumed B02; no actual source/
control/stat/hash/decode/request or policy change to existing consumers. Stop after handback.

Allowlist: src/models/segmenter_checkpoint_source_inspection_v3.py,
tests/test_segmenter_checkpoint_source_inspection_v3.py, this contract and dated reader3 result.
Routine AGENTS/readiness/Week1/Trello/automation pointers permitted. Versioned copy of reader2
retains all descriptor/volume/archive/virtual-zero/restricted-decode/shape/dtype/auxiliary/alias/
span/identity/read/resource/approval protections. Control/report schemas end in -3; actual reader
approval schema checkpoint-metadata-approval-3. No old control/report accepted by schema substitution.

Control adds mandatory closed device_policy, exactly:
{name:recorded_source_tag_cpu_fake_meta_v1,serialized_tag_rule:cpu|cuda:N(0-1023)|mps:0,
loaded_tensor_device:cpu,storage_device:meta}. Policy fields/types/values are exact; caller cannot
override them. Existing architecture/full83signature/namespace/wrapper/limits/request/source/
identity/volume binding remains. Missing/stale/unknown policy refuses before source/worker.

Serialized tag grammar: literal cpu or mps:0; cuda:(0|[1-9][0-9]{0,3}) with integer≤1023.
ASCII only, no signs/leading zeros/spaces/extra separators/unknown device names. Record the
original tag, do not infer actual device hardware or source scientific acceptance from it.
Always require exact FakeTensor type, strided/unquantized supported dtype, loaded tensor.device
typecpu and storagedevicemeta; actual materialized/nonCPU/nonfake metadata refuses. All full83
float32 shape/stride/contiguous/no-grad/span/storage-offset/alias/unreferenced/auxiliary rules stay.
Pass rows retain source_device=originaltag and add tensor_device/storage_device stringscpu/meta.

Report retains reader2 fields and adds exact device_policy and device_failure|null. On a device
guard refusal, device_failure has exactly tensor_path,tensor_path_truncated,serialized_storage_tag,
serialized_tag_truncated,source_tag_allowed,tensor_device,tensor_is_cpu,storage_device,storage_is_meta.
Tensor path and printable original tag are bounded≤512UTF8 bytes; unsupported/nontext tag reports
null, not repr/source object content. Truncation explicit; no arbitrary object serialization.
Unknown/malformed tag reasonunsupported_serialized_device_tag; wrong tensor/storage placement
reasonnon_cpu_or_materialized_storage. Never return partial model inventory as compatible. For
type/format/shape failures before the device predicate, device_failure staysnull.

Restricted load remains weights_only=True/FakeTensorMode(allow_fallback_kernels=False)/
map_location=cpu/mmap=False, cleared safe globals, isolated trusted worker/no network. Hash once,
metered descriptor/virtual view reads, zero source-storage rereads, aggregate≤file+8MiB. Closed
CPU worker≤60s/3GiB sampled50ms; report≤1MiB, root/path/type/identity/volume guards unchanged.
Existing actual envelope remains defensive code for a future separately approved dispatcher;
all actual tests are denial-only before source/worker. No actual candidate checkpoint access here.

Qualification on fresh invented full83float32 CPU fixtures, both namespace modes, known serialized
tags including maximumindex1023 and auxiliary tensors, mixtures/aliases. Retain numerical/device
observations without decoded values. Reject unknown/malformed tags, fakeCPU/nonmeta and fakeCUDA/
meta placements, nonfake tensor, wrong offset/span/shapes/dtypes/aliases/control/source/volume.
Version existing tests into the new test file to qualify the changed reader, no old suite rerun.
Native≤300s/3GiB pytest+owned descendants50ms, retained failures/counts/resource/reap evidence.
No model forwards/updates, real arrays/values/source acquisition/external writes/Git/retrieval work.
After handback, dispatcher3/fresh actual metadata packet is proposed separately; no automatic B03.
