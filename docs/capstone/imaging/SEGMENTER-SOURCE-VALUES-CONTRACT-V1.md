# V01-I selective values preparation — closed invented-only contract

October6 iteration authority permits independent invented readiness engineering while B02/source
acceptance are pending. This four-file slice uses the planned V01 paths: source/test/contract/result.
Actual source-values boundary remains a later separately versioned/approved operation. No model
forward/update/real values or persistent raw weights. Old reader1/2/A/SUP-01 remain fixed.

`inspect_values(control, *, control_sha256, metadata_report, metadata_report_sha256,
acceptance=None, acceptance_sha256=None, approval=None, approval_sha256=None, receipt)` returns
typed ValuesAudit(state,report_json) or raises Refusal. Domain invented_source_values only; actual
accepted_suprem_source_values always refuses before source open. Real locator/SHA denied by pinned
reader2 invented boundary too. Closed control: schema_version=source-values-control-1,domain,
reader_control,metadata_report_sha256,reader_sha256,code_sha256,request,limits.
Request run_id/consumption_receipt_sha256; receipt exactly schema_version=invented-values-receipt-1,
run_id,domain,stateconsumed. Caller attests generated provenance/consumption; hashes establish
consistency, not an actual permit. No approval/acceptance accepted in invented domain.

Bind reader2 source69f81f52…full pin in code, its exact metadata control and passing current
invented metadata report/source/control/request/full83 inventory. Canonical snapshots prevent
mutable-control drift. Limits exact model18,805,696B,metadata8MiB,totalfilebytes+8MiB+18,805,696B,
working128MiB,worker120s,report1MiB,IPC22MiB,3GiB parent+child sampled50ms; tests300s/3GiB owned tree.

Clean isolated worker revalidates domain/pins/receipt before descriptors. Reuse reader2 descriptor,
archive/metered fake view/inventory by immutable pin. Its guard is never changed/monkeypatched.
Hash once, discover current archive/fake metadata, compare all83 model rows to supplied prior
metadata report. weights_only=True/map_locationcpu/mmapFalse/empty safe globals. No actual/source
optimizer values; require little-endian byteorder member, exact dense contiguous float32 spans,
offset0/storage length logical bytes,83unique model spans, no model↔auxiliary storage aliases.

A separate value-span method brackets pread with unchanged descriptor checks, meters each selected
model span once and all requested bytes including metadata/virtual. Reject bounds/packing/alias
before value reads/allocation. Read only83 selected storage spans18,805,696B, independently hash
each normalized tensor/all-state, reject nonfinite values including excluded32classhead. Auxiliary
storages are hashed only in file-identity pass and never materialized. No unrestricted load/mmap.

Worker output is non-pickle binary:8byte little-endian JSON-header length, canonical bounded JSON
report, then83 sorted raw dense float32 tensors. No raw output file. Parent meters IPC before
buffering, validates report/source/control/code/domain/noauthority and each tensor byte hash,
constructs owned CPU tensors and independently checks finiteness/state hashes. Typed audit is
cooperative lineage, not an unforgeable Python capability; downstream consumers rehash tensors
and validate complete report/code/signature to reject mutations/arbitrary caller state. Stop/reap
only owned worker; time/memory/transport/decode/identity failures raise bounded Refusal and no audit.

Report keys schema_version=source-values-report-1,domain,status,scope,execution_authority,
training_eligible,values_audited,source_sha256,source_bytes,control_sha256,metadata_report_sha256,
code_sha256,reader_sha256,model,state_sha256,io,allocation. Pass scopeinvented_values_only,
authoritynone/trainingfalse/valuesauditedtrue. Report contains hashes/metadata, never tensor values.
State private read-only mapping of mutable owned tensors; canonical immutable report bytes.
