# Time-boxed selector bottleneck triage

User authorized a30minute maximum investigation, not another pipeline redesign. Started
2026-10-14T22:31:42Z; ended early after two bounded3second native samples, small read-only
probes and a checkpoint comparison. Processing remained running in session46696/PID2142.
No production code, database schema, source identity, resource settings or locks changed.

## Findings

- First main-thread sample:2316/2331 samples in SQLite cursor reads, dominated by pread,
  including XML overflow payload and tree-page reads. Second sample:1614/2331 cursor reads,
  with another717 execute samples also predominantly disk reads (including insert paths).
  These are short observations, not a whole-run CPU profile.
- Native parent CPU was0.4%; observed workers mostly idle/lowCPU. More evaluation workers
  or GPU cannot address this measured I/O wait.
- iostat live intervals:~55–71operations/sec,~16KiB/operation,0.85–1.10MiB/s. Discarded
  the since-boot initial row. A separate contiguous16MiB database-file read took0.525s
  (~30.5MiB/s). Cache and concurrent workload confound this comparison; it supports an
  access-pattern bottleneck, not a guaranteed hardware specification or measured fragmentation.
- Source query EXPLAIN uses INTEGER PRIMARY KEY(rowid>?), no avoidable sort/full rescan.
-64record probes: keys0.051s; early XML421735bytes0.412s; recently processed XML491853bytes
  0.00043s after key probe. The latter is warm-cache behavior and is NOT a sustainable rate.
  No article text or identifiers displayed; only aggregate byte counts from already-processed
  source regions. No new relevance decisions or independent sampling.
- Recent committed window:994records/43.279seconds=22.97records/sec. Final observed
  checkpoint39,302,062 (~95.31%),1,934,772records remain. Diagnostic reads can compete with
  the live job, so this is not an isolated performance benchmark. Prior52minute rate~26/sec
  independently establishes slow throughput. Current errors remain absent.

## Decision

No small proven fix identified. Do not increase workers, weaken durability, rebuild/vacuum the
510GB source, or start copying the entire catalog as an unmeasured quick fix. No additional
large probe/scan is justified by this triage. Source/output random-page access on the external
storage is the observed limiting work; exact physical fragmentation and device health are not
proven. Faster random-access storage or a sequential/sharded staging architecture are plausible
future options, requiring migration cost and capacity measurement; neither is delivered here.

Stop spending capstone development time on this pipeline. Recommend prioritizing the guided
question -> evidence -> cited answer/refusal demonstration with approved fixtures, then a
bounded research collection. The full corpus can remain expansion work. Current job was NOT
paused by this diagnostic request; user can choose to retain slow background processing or
pause at a checkpoint. No completion ETA promised, no training/embeddings/human-hour credit.

Evidence: outputs/prowl/selection-bottleneck-20261014/ (two native samples, probe source/results,
contiguous-read result and end checkpoint). No production change requires tests or a run restart.
