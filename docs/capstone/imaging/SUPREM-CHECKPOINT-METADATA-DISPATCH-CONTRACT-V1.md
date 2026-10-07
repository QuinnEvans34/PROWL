# R04 checkpoint metadata dispatcher v1 — closed contract

Written before code, October6. Quinton approved the exact R01 result's four-file dispatcher and
single metadata attempt. R01 source/tests/contract remain fixed. This script imports only the
pinned R01 reader; it cannot grant source acceptance, value access, initialization or training.

## Preparation and authorization

Trusted `prepare(run_id, authorization)` accepts the recorded user instruction, not a inferred
permission from file presence. Actual run ID is exactly SUPREM_META_20261006_B01, locator/bytes/SHA,
uniform_module wrapper/full83 signature and reader limits exactly as proposed in R01 results.
Authorization fields: approved_by, date, instruction, scope. Values are Quinton Evans,2026-10-06,
“Yes, I approve. How close are we to training?”,R04_single_metadata_attempt. This is transcription
of the human instruction in the current chat, not a cryptographic identity/authentication system.
Caller must possess that instruction; matching JSON alone never proves human approval.

No-follow parent traversal/stat binds exact source/root identity, APFS volume/UUID and output
parent identity/volume. Source leaf is regular/singly linked/user owned; root user owned and not
group/world writable. No source leaf open/read during preflight. No alternate locator, repair,
permission change or writes outside the single new0700 internal output area. Require1GiB free
after reserving4MiB via f_bavail, current same pinned output volume and exclusive absent area.
Prep observes metadata; source hash is expected, not measured until after consumption.

`control.json` is a dispatcher envelope: schema_version, scope, reader_control, receipt, pins,
environment, output. Exact schema version checkpoint-metadata-dispatch-1. scope is the receipt's
scope hash preimage: run_id,domain,source,namespace,output,pins,environment,bounds. Receipt fields
schema_version,run_id,scope_sha256,state (checkpoint-metadata-consumption-1 / consumed).
Receipt is deterministic before consumption, preventing a circular control/receipt hash.
R01 control pins its SHA; atomic exclusive receipt creation is consumption, not receipt planning.
Pins bind delivered R01 reader/tests/contract, dispatcher source/tests/contract. Environment binds
Python version/executable and installed torch/MONAI versions. Bounds fixed64,889,231B actual total
read cap,4MiB diagnostics,1GiB floor,90s whole dispatch/60s child,3GiB aggregate sampled RSS/50ms.

`approval.json`: schema_version,authorization,request_sha256,reader_approval. Schema version
checkpoint-metadata-dispatch-approval-1. Reader approval retains R01 closed approval schema.
Actual CLI requires external --request-sha256 and --approval-sha256 pins supplied by the trusted
caller. Pure consistency is distinct from genuine human authority. Invented domain has a separate
literal invented authorization, reader approval absent and private temporary generated source.
Invented tests must never positively stat/open/hash the actual locator.

## Execution and outputs

`dispatch(run_id, request, approval, request_sha256, approval_sha256)` checks canonical pins,
closed schemas, code/environment/source/output scope, prepared directory/member identity and
free space. Reject before source payload access. Require exactly the two prepared files and no
receipt/report/log; another invocation cannot replay a consumed area. Atomically O_EXCL create
and fsync consumption-receipt.json before starting the reader. Never retry automatically.

Run the unchanged R01 public API in an owned isolated intermediary; R01 owns its isolated reader
child. Before worker input prove the ps monitor is available. Monitor aggregate RSS of the
dispatcher plus intermediary and reader descendants every50ms;90s dispatch,3GiB sampled stop.
Record intermediary post-exit ru_maxrss and nested reader peak too. Sampled stops are not OS hard
guarantees. Terminate/reap only owned process groups, including R01's separate group, on every stop.
Bound worker stdout1MiB/stderr64KiB; retain only generic log/counts, not source payload text.
Monitor absence/platform mismatch refuses; no bypass. Native tests:300s/3GiB pytest+owned children.

Only control.json,approval.json,consumption-receipt.json,report.json,attempt.log allowed; exclusive
regular0600 single-link writes via pinned directory descriptor. Combined≤4MiB. Files already
created stay on failure; no overwrites/deletion/extra evidence files. Output drift, capacity loss,
limits and worker faults preserve consumed receipt plus bounded refusal where writable. Full disk
or directory replacement can prevent the report; never claim guaranteed evidence publication.

Report schema_version checkpoint-metadata-dispatch-report-1;status,reason,scope,
execution_authority,training_eligible,values_audited,run_id,request_sha256,approval_sha256,
consumed,reader,resources. Scope checkpoint_metadata_only,authority none,both flags false.
Pass requires R01 pass/identity+metadata flags, exact control/source/request hashes,83 tensors,
64,889,231B aggregate cap and zero metadata source-storage reads. Recheck source/volume/output
after worker and before success. Report neither grants scientific source use nor verifies values.

Preparation output identity deliberately excludes directory mtime/ctime changed by own writes.
Control/approval canonical bytes are rechecked before and after worker. A failed preflight creates
no source byte authority; any partially created output area is retained and cannot be reused.

## Four-file scope and finish

New dispatcher, new invented tests, this contract, dated result. Routine queue/AGENTS/packet/Trello
pointers only. No old reader/test/consumer edits, real arrays/models/updates/external writes.
After invented qualification, one approved metadata preflight and attempt; stop with actual
outcome/pins/resources and exact next review point. Failed consumed attempt needs a fresh reviewed
scope; no automatic different namespace, unsafe load, alternate source or replay.
