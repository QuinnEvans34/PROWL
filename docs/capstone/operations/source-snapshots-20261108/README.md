# Six frozen source files: byte reconciliation

November 8, 2026. **PASS: all six current files match the exact frozen readiness pins.** The live training files were not changed.

The files contain mixed CRLF and LF endings. That explains why neither an unmodified Git blob nor a uniform LF-to-CRLF conversion reproduced their hashes. Replacing CRLF with LF **in memory only** makes every runtime file byte-identical to its Git counterpart at commit `48ea7c5f2561010c7aa589f97fe682eb4cfddc40`. All six ASTs are equal; there is no code/version difference in these six files. This is a source-byte reconciliation, not a new training qualification.

| File | Runtime CRLF lines | Runtime LF lines | Frozen pin | AST |
| --- | ---: | ---: | --- | --- |
| src/data/segmenter_full_inputs_v1.py | 108 | 12 | Exact | Equal |
| src/data/segmenter_prepared_inputs_v1.py | 63 | 1 | Exact | Equal |
| src/training/experiment_config.py | 241 | 5 | Exact | Equal |
| src/training/segmenter_full_executor_v1.py | 66 | 21 | Exact | Equal |
| src/training/segmenter_full_resume_v1.py | 52 | 4 | Exact | Equal |
| src/training/segmenter_full_session_v1.py | 176 | 87 | Exact | Equal |

[six-frozen-source-files.json](six-frozen-source-files.json) includes both exact byte streams as base64, SHA256s, byte lengths, per-line ending maps and changes, empty normalized unified diffs, and AST-dump hashes. Reconstructing each runtime file from its Git bytes and the runtime ending map gives exact byte equality. The JSON was read back, all base64 values decoded with strict validation, hashes/AST comparisons rechecked, and all six current source files re-read unchanged afterward.

Ready SHA256: `d0a291420d0e1ee07e56f1007540797ebb97c9a08ff25cc82111d53f77c4d9f8`. Snapshot JSON SHA256: `750bc3db8a76d9e7f69cd3028eb1892515feab1bc2ea4a0ba0f2b2b612e77d2b`.

Only these six source files, the existing ready/pin reports and corresponding Git blobs were read. No source imports, model/data array reads, GPU calls, training stops/restarts, repinning, source normalization or merges. Original published pin report remains intact. The snapshots are evidence, not replacement producing files.
