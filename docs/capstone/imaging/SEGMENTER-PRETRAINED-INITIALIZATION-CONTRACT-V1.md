# V02-I typed values → exact fresh-head preparation

October6 iteration scope; four new files: source/test/this contract/result. Invented-only CPU
initialization, after V01-I qualification. Actual source acceptance/R05 remains incomplete.
Old SUP-01, readers, consumers and environment locks remain fixed. No forward, update, real
checkpoint, patient array or optimizer construction. No persistent raw weights or external write.

`initialize(audit, control, *, control_sha256)` requires V01-I's typed ValuesAudit, current immutable
code pins, complete83-source signature, finite owned CPU float32 tensors and unchanged report/state
hashes. Reject arbitrary caller mappings, mutated audits and actual domains before factory use.
Reject ambient non-CPU or non-float32 tensor defaults before constructing a model.
Closed control: schema_version=pretrained-initialization-control-1,domain=invented_pretrained_init,
values_report_sha256,values_code_sha256,initializer_sha256,factory_sha256,target_architecture,
seed,policy,limits. Seed exactly integer42; policyexact_backbone_fresh_head. Target architecture
SegResNet1→3/init16/group8/down[1,2,2,4]/up[1,1,1]/dropout0. Limits128MiB owned-buffer planning
ceiling/report1MiB; native tests300s/3GiB sampled pytest+owned descendants,50ms. No native-sized run.

Bind the unchanged repository factory by source hash. Build one fresh CPU three-class model in
torch.random.fork_rng(devices=[]), seed42; preserve caller RNG on success and failure. Fresh full
target83-tensor signature must match the independently fixed source signature with only the final
weight/bias first dimension changed32→3. Clone only after all input/policy/lineage guards. Transfer
exact81 backbone tensors, including conv_final.0 normalization. Exclude exactly conv_final.2.conv
weight/bias; retained32-class head is still finite-audited by V01-I but never transferred.

Strict load once; reject missing/unexpected keys or any final mismatch. Final head must be bitwise
equal to the fresh pre-transfer seed42 head; all81 backbone entries bitwise equal to the audited
source. Source remains unchanged and final state owns separate CPU storage. Source18,805,696B;
excluded head2,176B; backbone18,803,520B; fresh3-head204B; target18,803,724B.

Return InitializationAudit(state,report_json) with a read-only mapping and immutable canonical JSON;
mutable tensors are rehashed by `validate_initialization` before any future consumer use. Python
type/token is cooperative lineage, not cryptographic authorization. Report closed fields:
schema_version=pretrained-initialization-report-1,domain,status,scope,execution_authority,
training_eligible,control_sha256,code_sha256,values_code_sha256,values_report_sha256,factory_sha256,
source_sha256,source_state_sha256,source_backbone_sha256,fresh_head_sha256,target_state_sha256,
seed,target_architecture,policy,excluded_keys,model,bytes. Pass scopeinvented_initialization_only,
authoritynone/trainingfalse. No source separation assertion or actual training eligibility.
