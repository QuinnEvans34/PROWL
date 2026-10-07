# SUP-DEVICE-DIAG-01 — invented-only fake device observations

October6,2026. Quinton approved the proposed scope with “Great, start on that, and tell me how
close we are to training.” This implements/qualifies only the named invented diagnostic; B02
remains consumed/refused, and source acceptance/actual values/session/training remain separate.

Four-file implementation allowlist: scripts/diagnostics/probe_suprem_fake_device_v1.py,
tests/test_suprem_fake_device_probe_v1.py, this contract and the dated result. Routine
AGENTS/readiness/Week1/Trello/automation pointers are permitted. All287 prior pins remain fixed.
No reader/dispatcher guard or actual source/control/array access, model construction/forward/update,
acquisition, external writer, capacity change, Git publication or retrieval ownership change.

`probe_fixture(tag)` accepts only literal cpu, cuda:0, cuda:3 or mps:0. No path/domain/checkpoint
argument exists. It launches one isolated owned CPU worker. The worker generates one contiguous
float32 tensor shape[2,3]/24B from literal values; saves only {net:{weight:tensor}} in an exclusive
private prowl-source-invented-device-* temporary root/invented-device.pth. Save-only trusted
serialization tagger records the selected tag on CPU storage, without accelerator allocation.
Restore the package registry immediately after save. Each worker generates its own file; the
parent accepts no external fixture/control/source. Source≤64KiB, metadata≤128KiB, max8archive
members/max4storages/max1KiBstorage declared, one24B tensor. No model factory or optimizer.

Use unchanged reader2 descriptor source/archive/virtual-zero view for metered reads. Internally
generated descriptor identity/hash control has only invented domain, exact local reader pin,
full reviewed architecture/signature (for binding only; no83tensor compatibility claim), narrow
archive/read bounds and no actual approval. Hash the generated file once, then restricted
weights_only=True/FakeTensorMode(allow_fallback_kernels=False)/map_location=cpu/mmap=False
metadata load with cleared safe globals. Source storage reads after hash must be zero. Bound
shape/stride/dtype/size/storage-file-offset to the generated archive; do not read tensor values.

Observe serialized storage `_fake_device`, tensor device and storage device separately. Record
three named predicates: source_tag_is_cpu, tensor_is_cpu, storage_is_meta, and their conjunction
reader2_guard_would_pass. A non-CPU stored tag is a diagnostic observation, never permission to
relax reader2. Fixture expectation: report observed facts independently; tests assert expected
behavior using literal known tags rather than the production guard helper. Report does not
identify B02's failed tensor/conjunct or qualify its weights; any inference must be labeled.

Closed report: schema_version=fake-device-probe-report-1, evidence_domain=invented_fake_device,
status/reason, fixture_tag, observation|null, io|null, resources|null, execution_authority=none,
training_eligible=false, values_audited=false, actual_source_access=false. Observation fields:
shape,dtype,stride,logical_bytes,serialized_storage_tag,tensor_device,storage_device,is_fake_tensor,
storage_file_offset,storage_bytes,checks. No original source path/content or tensor values.
io is the unchanged reader2 bounded evidence dict. Successful diagnostic means observations
complete, including a false reader2 predicate; it never means checkpoint compatibility passed.

CPU/no-network worker under -I with trusted checkout imports only. Parent proves native ps
monitor before authorizing worker input/import/generation. Parent+owned child RSS≤3GiB sampled
50ms, wall≤15s per fixture; stdin≤256B/stdout≤8KiB/stderr≤4KiB counted before buffering.
Read only {tag} JSON input with exact allowlist; bounded canonical report checked in parent.
Terminate/reap only owned process group on timeout/output/monitor/RSS failure; preserve refusal.
Temporary cleanup is limited to the worker's generated fixture. No durable binary output writer.
The CLI accepts only `--invented-device-probe`, runs each of the four tags once, prints bounded
reports; no actual follow-on. Targeted new tests≤300s/3GiB owned pytest tree/50ms with retained
failure/output/counts. No completed suites repeated. Stop after handback.
