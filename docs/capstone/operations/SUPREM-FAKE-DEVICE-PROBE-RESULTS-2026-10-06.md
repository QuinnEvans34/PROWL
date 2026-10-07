# SUP-DEVICE-DIAG-01 — continuing invented diagnostic result

October6,2026. Quinton: “Great, start on that, and tell me how close we are to training.”
Approved exact four-file diagnostic from the B02 result; no actual retry/reader policy change.
[Closed contract](../imaging/SUPREM-FAKE-DEVICE-PROBE-CONTRACT-V1.md) recorded before code/tests.
Tracking: [W01-20](https://trello.com/c/TIWlmnJ3), parent[W01-12](https://trello.com/c/fiOfVdBz).

## Phone handback — complete

**36 new native checks pass**;5.568708s/323,223,552B sampled aggregate pytest+owned descendants,
78samples/50ms,exit0/no stops/all owned workers reaped. No full-suite claim or old-suite rerun.
CPU-, cuda:0-, cuda:3- and mps:0-tagged generated24B tensors all load as CPU FakeTensor with meta
storage through the unchanged restricted descriptor/virtual view. Only the source_tag_is_cpu
predicate is false for the three non-CPU serialized tags. Post-hash source-storage reads0 in
all four, with24virtual-zero bytes each. No accelerator allocation or actual source/control access.

This reproduces a plausible reason for B02's compound refusal: an original GPU serialization tag
can coexist with safe CPU fake metadata loading. **Inference only** for B02: its report did not
return which tensor/conjunct failed, so this diagnostic does not prove the actual cause or full83
compatibility. No accepted reader guard was changed and B02 remains consumed/refused.

**How close to SuPreM training:** source identity is verified and invented value/head code is
prepared, but five substantive gates remain:1metadata policy/fresh actual compatibility;
2candidate-bound rights/pretraining AND selection separation acceptance;3actual finite values/
exact initialization;4new session/learning/interruption/native/independent recovery qualification;
5current keeper/resource fit and frozen matched run/launch approval. No reliable hours/percentage
until source evidence and resource fit are known. D-335's scratch pipeline already trained;
this is readiness for a new SuPreM-initialized comparison, not inability to train any model.

Next recommended: review the concrete SUP-DEVICE-POLICY-03 proposal below. Proposed only; no
implementation or actual request dispatch follows this handback. Human hours unknown.

## Qualification and observations

One native qualification attempt:
`.venv-prowl/bin/python /tmp/prowl-device-diag-qualify.py 01`, pytest only the new test file.
Pytest reports36passed/5.23s; wrapper5.568708s. Four record_property/xunit2 format warnings retained;
all four full report properties were read back from XML successfully. No skips or unexpected
faults. Resource/authority/input/report/owned-worker refusals exercised on generated or mocked
inputs; no file-input API exists. Native timeout/output/stderr/nonzero-exit faults reap their
owned workers. CPU save tagging restores the package registry and does not advance caller RNG.

| Generated tag | Stored tag | Tensor device | Storage device | CPU tag check | CPU tensor / meta storage checks | Requested bytes | Fixture elapsed / sampled aggregate bytes |
|---|---|---|---|---|---|---:|---|
|cpu|cpu|cpu|meta|true|true / true|5427|1.181965s /320,634,880B|
|cuda:0|cuda:0|cpu|meta|false|true / true|5430|1.151315s /320,159,744B|
|cuda:3|cuda:3|cpu|meta|false|true / true|5430|1.060644s /322,469,888B|
|mps:0|mps:0|cpu|meta|false|true / true|5429|1.050964s /320,241,664B|

Each generated file1641B/one24Bstorage, recordedoffset768/shape[2,3]/stride[3,1]/float32.
Requested bytes include hash1641B once, metadata3762/3765/3765/3764B respectively and24virtual
zero bytes. No post-hash actual storage payload read. Diagnostic statuspass means observations
complete, including false predicates; it does not mean reader2 accepts these tags.

Local runtime primary evidence: torch/serialization.py load_tensor fake branch creates meta
storage and sets `_fake_device` from original location; torch/_utils.py `_restore_device_fake_mode`
maps the fake tensor device using map_location. These two fields have different meanings. This
diagnostic used the actual pinned local runtime with no network/download or package installation.

Retained logs /tmp/prowl-device-diag-attempt-01.log, SHA256
`892be388b67cffff18fa3f455590a59d739cdf9a9766942b59017f8359adcaa8`;
XML /tmp/prowl-device-diag-attempt-01.xml, SHA256
`7e7395716fb0ec69aab220b2429b1aaf249a73d9d29cfdd3760f591a013f775c`.
Qualification wrapper /tmp/prowl-device-diag-qualify.py has300s/3GiB/50ms/8MiB-output envelope.

## Produced files and preservation

| New file | SHA256 |
|---|---|
|scripts/diagnostics/probe_suprem_fake_device_v1.py|0cb040ab7f40702ae3ff672515f8845c56bb2b358c60186155a810169bd5ff23|
|tests/test_suprem_fake_device_probe_v1.py|2a266c974c237e1eef0a0dc0cb60818096bc163afcf18bafd536519bc3577760|
|docs/capstone/imaging/SUPREM-FAKE-DEVICE-PROBE-CONTRACT-V1.md|dc48a0ad5bb7ef3149eabec8f5372962999ae5f1813bab2878e6b24129bd5218|

This fourth dated result and routine AGENTS/queue/Trello/automation pointers updated too. No
old producer/reader/dispatcher/test/contract/lock changes. All287priorpins and historical notebook
tail exact. New290-pin ledger /tmp/prowl-device-diagnostic-preserved-pins.json, SHA256
`fa8e4d691971e61a72dff69027e550c25ef6e0f6fcd7fa8a931d4462785a5e50`.
No source acquisition, actual values/model/arrays/forward/update/training, external root writes,
capacity increase, Git publication or retrieval/N4 work. All prior roles/holds/failures retained.

## Proposed SUP-DEVICE-POLICY-03 — review before any guard change

Purpose: separate serialized provenance tags from loaded fake tensor/storage placement in a
new version. Preserve reader2/dispatcher2/B02 and all290pins. Explicitly accept only recorded
original tags cpu or canonical cuda:N (integer0–1023) or mps:0; reject unknown/ambiguous tags.
Always require exact FakeTensor type, loaded devicecpu and storagedevicemeta; nonmaterialized
storage/exact offset/span/float32/full83signature/auxiliary/alias/bounds checks remain mandatory.
Record the original tag per tensor; report separate failed predicates/tensor path on refusal.
This is a proposed policy change, not acceptance or confirmation of actual checkpoint tags.

PhaseP03-I: four NEW files src/models/segmenter_checkpoint_source_inspection_v3.py,
tests/test_segmenter_checkpoint_source_inspection_v3.py,
docs/capstone/imaging/SEGMENTER-CHECKPOINT-SOURCE-INSPECTION-CONTRACT-V3.md,
docs/capstone/operations/SEGMENTER-CHECKPOINT-SOURCE-INSPECTION-V3-RESULTS-2026-10-06.md.
Before code record the closed fields/tag grammar/report failure details. Invented full83CPU
fixtures with source/auxiliary device tags; strict reject nonfake/nonmeta/nonCPU/materialized/
unknown and malformed tags, alias/span/shape/dtype mismatches. Preserve original metadata read,
restricted loading/safe-global/ownership/resource rules. Native targeted qualification≤300s/3GiB
owned tree/50ms. No model forward/update, actual file/source/control or tensor values.

If P03-I is reviewed/passes, a separate dispatcher3/control packet is required for one fresh
actual metadata request (e.g.B03, proposed name only). Current dispatcher2 binds reader2 and B02;
do not patch it, replay B02 or substitute reader pins into spent controls. Any new actual packet
must bind frozen source/stat/volume/code/namespace/read/time/RSS/storage/receipt and require
Quinton's exact launch approval after preparation/qualification. No actual access is approved by
this diagnostic. Stop after P03-I if separately approved; no automatic dispatcher/native follow-on.

Exact next starting point: Quinton reviews the original-tag policy and four-file P03-I scope;
after explicit approval, implement/qualify only that versioned invented reader. Source scientific
acceptance and R05–R08 remain independent, unfinished gates. No launch ETA or automatic experiment.

## Final delivery checks

All290pins and the historical notebook tail verified after qualification;59local document links
resolve, scoped Markdown whitespace and git diff --check pass. No repeated successful tests.
W01-20 Done/complete and parentW01-12 To-Do/incomplete descriptions read back exactly; R04
checklist read back INCOMPLETE with actual B02 refusal and invented tag observation distinct.
All46existing board cards and unrelated content/list placements preserved; exactly one new
bounded task added,47total. No archive/delete or unrelated card update.
Existing hourly automation read back ACTIVE with the same schedule/notification intent, consumed
B02/no-replay state, completed36-check handback and proposed-only P03-I; configSHA256
`9802da991b78d8b98d3a74413a830eb94bf41f24bb9bb14c0d9671bf0cbeddd0`.
Human hours remain unknown; no machine runtime counted. Stop after this handback.

## Start

Authoritative pwd/Git root/status/workspace checker verified. All287 preserved source/test/lock/
contract pins exact, including qualified reader2/dispatcher2 and two CLI checks; four new paths
absent before creation. Existing dirty files/failed evidence preserved. No actual source/control
access in this diagnostic. B02 remains consumed/refused. No model/arrays/forward/update/training.

## Finish line

Generate tiny CPU tensor checkpoints with four explicit serialized device tags inside isolated
owned workers; observe each of the three guard predicates independently and prove post-hash
storage-payload reads zero. Native targeted qualification with retained output/resource stops,
Trello/queue readback and a phone handback. Source identity passed in B02; metadata compatibility,
scientific source-use evidence, actual finite values/initialization, session/recovery/current
storage budget and exact training launch remain open. No reliable launch ETA follows this packet.
