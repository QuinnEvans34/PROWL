# D-305 — complete the bounded 144³ training transaction

Quinton requested “Great, continue on” after D-304. Implement the separate training session,
deterministic shuffled passes, native evaluation/export, progress checkpoints and completion-last
attempt journal. The readiness API stays inference-only. Own new training/diagnostic/test files and
shared status records; leave retrieval, qualified memberships, source data and prior evidence intact.

Acceptance: synthetic tests for identity/authorization, role drift, exact schedule, state corruption,
checkpoint/next-update replay, native reference binding, failed publication and consumed attempts.
Then run the actual SegResNet on MPS, float32, fallback disabled, threads2/workers0, with invented
variable-volume inputs including a 248×248×244 grid (15,007,744 voxels). Three producer updates,
checkpoints0/2/3 and full before/after native scoring; validation also at2. Independently restore
step2 and terminal checkpoints with primary reads blocked; replay the next update and inject an
interruption after optimizer mutation. An uncertain session must refuse both saving and continued use.

Synthetic supervisor: 600 seconds per producer/recovery process,16GiB RSS and driver caps,
256MiB local evidence per process, AC required,100GiB internal free floor. Existing independent
storage controls:20GiB backup ceiling,96MiB per artifact,1GiB new per physical domain, ceilings
frozen once across both processes. Record all failed attempts; never rerun a consumed directory.
No source CT/label reads, real updates, automatic recovery continuation, deletion or model promotion.

The planned real run remains300updates over113train/40development-validation at144³/2mm.
Use fresh baseline evaluation in the new transaction rather than adapting old initialization receipts:
this adds a measured full inference/reference pass but keeps every trajectory bound to one identity.
The stage-specific source plan is386 label reads (153+40+40+153), no CT reads; it needs a new capability
and exact request. The old D-304153-read capability remains consumed. A45minute total limit remains
proposed until the completed rehearsal and real launch-wrapper/resource checks support freezing it.
